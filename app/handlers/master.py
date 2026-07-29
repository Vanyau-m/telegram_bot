from __future__ import annotations

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
from app.keyboards import cancel_keyboard
from app.services.errors import BotServiceError
from app.utils.dates import format_local, parse_slot_input


class MasterState(IntEnum):
    ADD_SLOTS = 100


async def add_slots_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    runtime = get_runtime(context)
    if update.effective_user.id != runtime.settings.master_telegram_id:
        await update.effective_message.reply_text("Недостаточно прав.")
        return ConversationHandler.END

    await update.effective_message.reply_text(
        "Отправьте один или несколько слотов, каждый с новой строки:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ-ЧЧ:ММ\n\n"
        "Пример: 15.08.2026 10:00-11:30\n"
        "Когда закончите, нажмите «Готово».",
        reply_markup=cancel_keyboard(),
    )
    return MasterState.ADD_SLOTS


async def receive_slots(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    runtime = get_runtime(context)
    text = (update.effective_message.text or "").strip()
    if text.casefold() == "готово":
        await update.effective_message.reply_text(
            "Добавление слотов завершено.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    messages: list[str] = []
    for line in filter(None, (part.strip() for part in text.splitlines())):
        try:
            start, end = parse_slot_input(line, runtime.settings.timezone)
            timeslot = runtime.timeslots.create(start, end)
            messages.append(
                f"✓ {format_local(timeslot.start_time, runtime.settings.timezone)}"
                f"–{timeslot.end_time.astimezone(runtime.settings.timezone).strftime('%H:%M')}"
            )
        except (ValueError, BotServiceError) as exc:
            messages.append(f"✗ {line}: {exc}")

    await update.effective_message.reply_text(
        "\n".join(messages) if messages else "Не найдено ни одной строки."
    )
    return MasterState.ADD_SLOTS


async def master_slots(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    runtime = get_runtime(context)
    if update.effective_user.id != runtime.settings.master_telegram_id:
        await update.effective_message.reply_text("Недостаточно прав.")
        return

    slots = runtime.timeslots.list_future()
    if not slots:
        await update.effective_message.reply_text("Будущих слотов нет.")
        return

    status_names = {
        "available": "свободен",
        "booked": "занят",
        "blocked": "закрыт",
    }
    lines = [
        (
            f"ID {slot.id}: "
            f"{format_local(slot.start_time, runtime.settings.timezone)}"
            f"–{slot.end_time.astimezone(runtime.settings.timezone).strftime('%H:%M')}"
            f" — {status_names[slot.status]}"
        )
        for slot in slots
    ]
    await update.effective_message.reply_text("\n".join(lines))


async def cancel_master_dialog(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.effective_message.reply_text(
        "Операция отменена.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def build_master_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add_slot", add_slots_start)],
        states={
            MasterState.ADD_SLOTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_slots)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_master_dialog)],
        name="master_slots",
        persistent=False,
    )

