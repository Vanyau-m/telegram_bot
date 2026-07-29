from __future__ import annotations

import logging
from typing import Any

from telegram import Message
from telegram.ext import ExtBot

from app.services.dialog_logs import DialogLogService


logger = logging.getLogger(__name__)


class DialogLoggingBot(ExtBot):
    """Telegram bot that stores every successfully sent text message."""

    def __init__(self, token: str, dialog_logs: DialogLogService) -> None:
        super().__init__(token=token)
        self._dialog_logs = dialog_logs

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        *args: Any,
        **kwargs: Any,
    ) -> Message:
        message = await super().send_message(chat_id, text, *args, **kwargs)
        try:
            chat = message.chat
            is_private = getattr(chat, "type", None) == "private"
            self._dialog_logs.log(
                direction="outgoing",
                telegram_user_id=chat.id if is_private else None,
                chat_id=chat.id,
                username=getattr(chat, "username", None),
                first_name=getattr(chat, "first_name", None),
                last_name=getattr(chat, "last_name", None),
                message_text=text,
                message_type="text",
                telegram_message_id=message.message_id,
                created_at=message.date,
            )
        except Exception:
            logger.exception("Не удалось сохранить исходящее сообщение в БД")
        return message

