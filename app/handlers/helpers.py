from telegram.ext import CallbackContext

from app.runtime import Runtime


def get_runtime(context: CallbackContext) -> Runtime:
    return context.application.bot_data["runtime"]

