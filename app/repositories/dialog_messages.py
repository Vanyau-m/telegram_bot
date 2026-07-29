from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import DialogMessage
from app.utils.dates import from_database, to_database


class DialogMessagesRepository:
    @staticmethod
    def create(
        connection: sqlite3.Connection,
        *,
        direction: str,
        telegram_user_id: int | None,
        chat_id: str,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        message_text: str | None,
        message_type: str,
        telegram_message_id: int | None,
        update_id: int | None,
        created_at: datetime,
    ) -> DialogMessage:
        cursor = connection.execute(
            """
            INSERT INTO dialog_messages (
                direction,
                telegram_user_id,
                chat_id,
                username,
                first_name,
                last_name,
                message_text,
                message_type,
                telegram_message_id,
                update_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                direction,
                telegram_user_id,
                chat_id,
                username,
                first_name,
                last_name,
                message_text,
                message_type,
                telegram_message_id,
                update_id,
                to_database(created_at),
            ),
        )
        row = connection.execute(
            "SELECT * FROM dialog_messages WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return _row_to_dialog_message(row)

    @staticmethod
    def list_for_user(
        connection: sqlite3.Connection,
        telegram_user_id: int,
        limit: int = 100,
    ) -> list[DialogMessage]:
        rows = connection.execute(
            """
            SELECT * FROM dialog_messages
            WHERE telegram_user_id = ?
            ORDER BY created_at, id
            LIMIT ?
            """,
            (telegram_user_id, limit),
        ).fetchall()
        return [_row_to_dialog_message(row) for row in rows]


def _row_to_dialog_message(row: sqlite3.Row) -> DialogMessage:
    return DialogMessage(
        id=row["id"],
        direction=row["direction"],
        telegram_user_id=row["telegram_user_id"],
        chat_id=row["chat_id"],
        username=row["username"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        message_text=row["message_text"],
        message_type=row["message_type"],
        telegram_message_id=row["telegram_message_id"],
        update_id=row["update_id"],
        created_at=from_database(row["created_at"]),
    )

