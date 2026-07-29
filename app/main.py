from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    TypeHandler,
)

from app.config import Settings
from app.database import Database
from app.handlers import (
    build_client_conversation,
    build_common_handlers,
    build_master_conversation,
    master_slots,
)
from app.handlers.dialog_logging import log_incoming_update
from app.runtime import Runtime
from app.services import (
    BookingService,
    ClientsService,
    DialogLogService,
    TimeslotsService,
)
from app.services.reminders import ReminderService
from app.telegram_bot import DialogLoggingBot


logger = logging.getLogger(__name__)


def build_application(settings: Settings) -> Application:
    database = Database(settings.database_path)
    database.initialize()

    clients = ClientsService(database)
    timeslots = TimeslotsService(database)
    dialog_logs = DialogLogService(database)
    bookings = BookingService(
        database,
        timezone=settings.timezone,
        max_appointments_per_day=settings.max_appointments_per_day,
    )
    reminders = ReminderService(
        bookings,
        master_telegram_id=settings.master_telegram_id,
        timezone=settings.timezone,
        reminder_minutes=settings.reminder_minutes,
    )
    runtime = Runtime(
        settings=settings,
        clients=clients,
        timeslots=timeslots,
        bookings=bookings,
        reminders=reminders,
        dialog_logs=dialog_logs,
    )
    bot = DialogLoggingBot(settings.bot_token, dialog_logs)

    application = (
        ApplicationBuilder()
        .bot(bot)
        .concurrent_updates(False)
        .post_init(_post_init)
        .build()
    )
    application.bot_data["runtime"] = runtime

    application.add_handler(
        TypeHandler(Update, log_incoming_update),
        group=-1,
    )
    application.add_handler(build_client_conversation())
    application.add_handler(build_master_conversation())
    application.add_handler(CommandHandler("slots", master_slots))
    for handler in build_common_handlers():
        application.add_handler(handler)
    application.add_error_handler(_error_handler)
    return application


async def _post_init(application: Application) -> None:
    runtime: Runtime = application.bot_data["runtime"]
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Записаться"),
            BotCommand("cancel_booking", "Отменить запись"),
            BotCommand("help", "Помощь"),
        ]
    )
    restored = runtime.reminders.restore(application)
    logger.info("Восстановлено напоминаний: %s", restored)


async def _error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    error = context.error
    logger.error(
        "Ошибка при обработке Telegram-события",
        exc_info=(type(error), error, error.__traceback__),
    )
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Попробуйте ещё раз позднее."
        )


def configure_logging(settings: Settings) -> None:
    settings.log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    file_handler = logging.FileHandler(settings.log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def run() -> None:
    settings = Settings.from_env()
    configure_logging(settings)
    logger.info("Бот запускается")
    application = build_application(settings)
    application.run_polling(allowed_updates=Update.ALL_TYPES)
