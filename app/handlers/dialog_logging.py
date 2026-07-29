from __future__ import annotations

import logging

from telegram import Message, Update
from telegram.ext import ContextTypes

from app.handlers.helpers import get_runtime


logger = logging.getLogger(__name__)


async def log_incoming_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if message is None or chat is None:
        return

    message_text, message_type = _message_content(message)
    try:
        get_runtime(context).dialog_logs.log(
            direction="incoming",
            telegram_user_id=user.id if user else None,
            chat_id=chat.id,
            username=user.username if user else None,
            first_name=user.first_name if user else None,
            last_name=user.last_name if user else None,
            message_text=message_text,
            message_type=message_type,
            telegram_message_id=message.message_id,
            update_id=update.update_id,
            created_at=message.date,
        )
    except Exception:
        logger.exception("Не удалось сохранить входящее сообщение в БД")


def _message_content(message: Message) -> tuple[str | None, str]:
    if message.text is not None:
        return message.text, "text"
    if message.caption is not None:
        return message.caption, _attachment_type(message)
    return None, _attachment_type(message)


def _attachment_type(message: Message) -> str:
    for field_name in (
        "photo",
        "video",
        "voice",
        "audio",
        "document",
        "sticker",
        "animation",
        "video_note",
        "contact",
        "location",
        "venue",
        "poll",
    ):
        if getattr(message, field_name, None):
            return field_name
    return "other"

