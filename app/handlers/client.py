from __future__ import annotations

import re
from enum import IntEnum

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.handlers.helpers import get_runtime
from app.keyboards import slots_keyboard
from app.services.errors import BotServiceError
from app.utils.dates import format_local
from app.utils.validators import normalize_full_name, normalize_phone


class ClientState(IntEnum):
    FULL_NAME = 1
    PHONE = 2
    CHOOSE_SLOT = 3


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Здравствуйте! Введите ваше ФИО:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ClientState.FULL_NAME


async def receive_full_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    try:
        full_name = normalize_full_name(update.effective_message.text or "")
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))
        return ClientState.FULL_NAME

    context.user_data["full_name"] = full_name
    await update.effective_message.reply_text(
        "Введите номер телефона, например: +7 999 123-45-67"
    )
    return ClientState.PHONE


async def receive_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    runtime = get_runtime(context)
    try:
        phone = normalize_phone(update.effective_message.text or "")
        runtime.clients.register(
            telegram_id=update.effective_user.id,
            full_name=context.user_data["full_name"],
            phone=phone,
        )
    except ValueError as exc:
        await update.effective_message.reply_text(str(exc))
        return ClientState.PHONE

    return await _show_slots(update, context)


async def choose_slot(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    runtime = get_runtime(context)
    text = update.effective_message.text or ""
    match = re.search(r"\|\s*ID:(\d+)\s*$", text)
    if match is None:
        await update.effective_message.reply_text(
            "Выберите время с клавиатуры или отправьте /cancel."
        )
        return ClientState.CHOOSE_SLOT

    try:
        details = runtime.bookings.create(
            client_id=update.effective_user.id,
            timeslot_id=int(match.group(1)),
        )
    except BotServiceError as exc:
        await update.effective_message.reply_text(str(exc))
        return await _show_slots(update, context)

    runtime.reminders.schedule(context.application, details)
    start_text = format_local(
        details.timeslot.start_time, runtime.settings.timezone
    )
    await update.effective_message.reply_text(
        f"Запись подтверждена: {start_text}.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await context.bot.send_message(
        chat_id=runtime.settings.master_telegram_id,
        text=(
            f"Новая запись: {details.client.full_name}, "
            f"{details.client.phone}, {start_text}."
        ),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_dialog(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    await update.effective_message.reply_text(
        "Диалог остановлен.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def _show_slots(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    runtime = get_runtime(context)
    timeslots = runtime.timeslots.list_available()
    if not timeslots:
        await update.effective_message.reply_text(
            "Сейчас нет свободных слотов. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "Выберите удобное время:",
        reply_markup=slots_keyboard(timeslots, runtime.settings.timezone),
    )
    return ClientState.CHOOSE_SLOT


def build_client_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex(r"(?i)^привет$"), start),
        ],
        states={
            ClientState.FULL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name)
            ],
            ClientState.PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)
            ],
            ClientState.CHOOSE_SLOT: [
                MessageHandler(filters.Regex(r"(?i)^отмена$"), cancel_dialog),
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_slot)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_dialog)],
        name="client_registration",
        persistent=False,
    )
