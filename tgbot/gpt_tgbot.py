import json
import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
import sqlite3
from datetime import datetime, timedelta

# --- Логирование ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
file_handler = logging.FileHandler('lashbot.log', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --- Конфиг ---
with open("C:\\Users\\Vanya\\Desktop\\myRepo\\data.json", "r", encoding='utf-8') as f:
    data = json.load(f)
    BOT_TOKEN = data["token"]
    logger.info("Загружен токен из файла конфигурации")

MASTER_TELEGRAM_ID = 127280410
FULLNAME, PHONE, CHOOSE_SLOT, ADD_DATE, ADD_START, ADD_END, CANCEL_CHOOSE, MOVE_CHOOSE, BULK_SLOTS = range(9)

# --- База данных ---
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS clients (
                telegram_id INTEGER PRIMARY KEY,
                full_name TEXT,
                phone TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                FOREIGN KEY(client_id) REFERENCES clients(telegram_id))''')
c.execute('''CREATE TABLE IF NOT EXISTS timeslots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                available INTEGER DEFAULT 1)''')
conn.commit()

# --- Клиентские обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Пользователь {update.effective_user.id} начал диалог")
    await update.message.reply_text("Привет! Введи своё ФИО:")
    return FULLNAME

async def get_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['full_name'] = update.message.text
    logger.info(f"ФИО: {update.message.text}")
    await update.message.reply_text("Теперь введи номер телефона:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    full_name = context.user_data['full_name']
    user_id = update.effective_user.id
    logger.info(f"Телефон: {phone}")
    c.execute("REPLACE INTO clients (telegram_id, full_name, phone) VALUES (?, ?, ?)", (user_id, full_name, phone))
    conn.commit()
    c.execute("SELECT id, start_time, end_time FROM timeslots WHERE available = 1")
    slots = c.fetchall()
    if not slots:
        await update.message.reply_text("Нет доступных слотов. Попробуйте позже.")
        return ConversationHandler.END
    keyboard = []
    for s in slots:
        start_dt = datetime.strptime(s[1], "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(s[2], "%Y-%m-%d %H:%M")
        display = f"{start_dt.strftime('%d %m %Y %H %M')}-{end_dt.strftime('%H %M')}|{s[0]}"
        keyboard.append([display])
    await update.message.reply_text("Выбери удобное время:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return CHOOSE_SLOT

async def choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    choice = update.message.text
    slot_id = int(choice.split('|')[-1])
    c.execute("SELECT start_time, end_time FROM timeslots WHERE id = ? AND available = 1", (slot_id,))
    slot = c.fetchone()
    if not slot:
        await update.message.reply_text("Слот недоступен")
        return ConversationHandler.END
    c.execute("SELECT COUNT(*) FROM appointments WHERE DATE(start_time) = ?", (slot[0][:10],))
    count = c.fetchone()[0]
    if count >= 6:
        await update.message.reply_text("На этот день уже слишком много записей. Попробуйте другой.")
        return ConversationHandler.END
    c.execute("INSERT INTO appointments (client_id, start_time, end_time) VALUES (?, ?, ?)", (user_id, slot[0], slot[1]))
    c.execute("UPDATE timeslots SET available = 0 WHERE id = ?", (slot_id,))
    conn.commit()
    c.execute("SELECT full_name FROM clients WHERE telegram_id = ?", (user_id,))
    client_name = c.fetchone()[0]
    await update.message.reply_text(f"Запись подтверждена: {slot[0]} - {slot[1]}")
    await context.bot.send_message(chat_id=MASTER_TELEGRAM_ID, text=f"Новая запись: {slot[0]} - {slot[1]} от {client_name}")
    delay = (datetime.strptime(slot[0], "%Y-%m-%d %H:%M") - timedelta(minutes=15) - datetime.now()).total_seconds()
    if delay > 0:
        asyncio.get_event_loop().call_later(delay, lambda: asyncio.create_task(
            context.bot.send_message(chat_id=MASTER_TELEGRAM_ID, text=f"Напоминание: через 15 минут запись {slot[0]} - {slot[1]}")
        ))
    return ConversationHandler.END

async def cancel_by_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() != "отменить запись":
        return
    user_id = update.effective_user.id
    c.execute("SELECT id FROM appointments WHERE client_id = ? ORDER BY start_time DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("У вас нет активных записей.")
        return
    app_id = row[0]
    c.execute("DELETE FROM appointments WHERE id = ?", (app_id,))
    c.execute("UPDATE timeslots SET available = 1 WHERE id = ?", (app_id,))
    conn.commit()
    c.execute("SELECT full_name FROM clients WHERE telegram_id = ?", (user_id,))
    client_name = c.fetchone()[0]
    await update.message.reply_text("Запись отменена.")
    await context.bot.send_message(chat_id=MASTER_TELEGRAM_ID, text=f"{client_name} отменил запись.")

# --- Мастер ---
async def add_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MASTER_TELEGRAM_ID:
        await update.message.reply_text("Недостаточно прав")
        return ConversationHandler.END
    await update.message.reply_text(
        "Введите слоты в формате: ДД ММ ГГГГ ЧЧ ММ-ЧЧ ММ\nОдин слот на строку.\nНапишите 'готово', чтобы завершить.")
    return BULK_SLOTS

async def handle_bulk_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.lower() == 'готово':
        await update.message.reply_text("Добавление слотов завершено.")
        return ConversationHandler.END
    try:
        date_part, start_part, end_part = text[:10], text[11:16], text[17:]
        dt = datetime.strptime(date_part, "%d %m %Y")
        start_time = datetime.strptime(start_part, "%H %M").time()
        end_time = datetime.strptime(end_part, "%H %M").time()
        start = datetime.combine(dt.date(), start_time).strftime("%Y-%m-%d %H:%M")
        end = datetime.combine(dt.date(), end_time).strftime("%Y-%m-%d %H:%M")
        c.execute("INSERT INTO timeslots (start_time, end_time) VALUES (?, ?)", (start, end))
        conn.commit()
        await update.message.reply_text(f"Добавлен слот: {start} - {end}")
    except Exception as e:
        logger.warning(f"Ошибка при разборе слота: {e}")
        await update.message.reply_text("Неверный формат. Используйте: ДД ММ ГГГГ ЧЧ ММ-ЧЧ ММ")
    return BULK_SLOTS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

logger.info("Запуск бота...")
app = ApplicationBuilder().token(BOT_TOKEN).build()

client_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT & filters.Regex("(?i)^привет$"), start)],
    states={
        FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fullname)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        CHOOSE_SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_slot)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

master_conv = ConversationHandler(
    entry_points=[CommandHandler("add_slot", add_slot)],
    states={
        BULK_SLOTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bulk_slots)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(client_conv)
app.add_handler(master_conv)
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^отменить запись$"), cancel_by_phrase))
app.run_polling()