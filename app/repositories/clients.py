from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import Client
from app.utils.dates import from_database, to_database


class ClientsRepository:
    @staticmethod
    def upsert(
        connection: sqlite3.Connection,
        telegram_id: int,
        full_name: str,
        phone: str,
        created_at: datetime,
    ) -> Client:
        connection.execute(
            """
            INSERT INTO clients (telegram_id, full_name, phone, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                full_name = excluded.full_name,
                phone = excluded.phone
            """,
            (telegram_id, full_name, phone, to_database(created_at)),
        )
        return ClientsRepository.get(connection, telegram_id)  # type: ignore[return-value]

    @staticmethod
    def get(connection: sqlite3.Connection, telegram_id: int) -> Client | None:
        row = connection.execute(
            "SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if row is None:
            return None
        return Client(
            telegram_id=row["telegram_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            created_at=from_database(row["created_at"]),
        )

