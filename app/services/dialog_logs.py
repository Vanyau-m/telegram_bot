from __future__ import annotations

from datetime import datetime

from app.database import Database
from app.models import DialogMessage
from app.repositories import DialogMessagesRepository
from app.utils.dates import utc_now


class DialogLogService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def log(
        self,
        *,
        direction: str,
        chat_id: int | str,
        telegram_user_id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        message_text: str | None = None,
        message_type: str = "text",
        telegram_message_id: int | None = None,
        update_id: int | None = None,
        created_at: datetime | None = None,
    ) -> DialogMessage:
        with self.database.transaction(immediate=True) as connection:
            return DialogMessagesRepository.create(
                connection,
                direction=direction,
                telegram_user_id=telegram_user_id,
                chat_id=str(chat_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
                message_text=message_text,
                message_type=message_type,
                telegram_message_id=telegram_message_id,
                update_id=update_id,
                created_at=created_at or utc_now(),
            )

    def list_for_user(
        self, telegram_user_id: int, limit: int = 100
    ) -> list[DialogMessage]:
        with self.database.transaction() as connection:
            return DialogMessagesRepository.list_for_user(
                connection, telegram_user_id, limit
            )

