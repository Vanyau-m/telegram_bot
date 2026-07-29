from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.handlers.cancellation import cancel_booking


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.effective_message.reply_text(
        "/start — зарегистрироваться и выбрать время\n"
        "/cancel_booking — отменить будущую запись\n"
        "/help — показать эту справку"
    )


async def unknown_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.effective_message.reply_text(
        "Не понял сообщение. Используйте /start или /help."
    )


def build_common_handlers():
    return [
        CommandHandler("cancel_booking", cancel_booking),
        MessageHandler(
            filters.TEXT & filters.Regex(r"(?i)^отменить запись$"),
            cancel_booking,
        ),
        CommandHandler("help", help_command),
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text),
    ]

