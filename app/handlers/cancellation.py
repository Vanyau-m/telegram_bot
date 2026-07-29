from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from app.handlers.helpers import get_runtime
from app.services.errors import AppointmentNotFoundError, BotServiceError
from app.utils.dates import format_local


async def cancel_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    runtime = get_runtime(context)
    try:
        details = runtime.bookings.cancel_next(update.effective_user.id)
    except AppointmentNotFoundError as exc:
        await update.effective_message.reply_text(
            str(exc), reply_markup=ReplyKeyboardRemove()
        )
        return
    except BotServiceError:
        await update.effective_message.reply_text(
            "Не удалось отменить запись. Попробуйте ещё раз.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    runtime.reminders.cancel(context.application, details.appointment.id)
    start_text = format_local(
        details.timeslot.start_time, runtime.settings.timezone
    )
    await update.effective_message.reply_text(
        f"Запись на {start_text} отменена.",
        reply_markup=ReplyKeyboardRemove(),
    )
    await context.bot.send_message(
        chat_id=runtime.settings.master_telegram_id,
        text=f"{details.client.full_name} отменил(а) запись на {start_text}.",
    )

