from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import Timeslot
from app.utils.dates import from_database, to_database


class TimeslotsRepository:
    @staticmethod
    def create(
        connection: sqlite3.Connection,
        start_time: datetime,
        end_time: datetime,
    ) -> Timeslot:
        cursor = connection.execute(
            """
            INSERT INTO timeslots (start_time, end_time, status)
            VALUES (?, ?, 'available')
            """,
            (to_database(start_time), to_database(end_time)),
        )
        return TimeslotsRepository.get(connection, cursor.lastrowid)  # type: ignore[return-value]

    @staticmethod
    def get(connection: sqlite3.Connection, timeslot_id: int) -> Timeslot | None:
        row = connection.execute(
            "SELECT * FROM timeslots WHERE id = ?", (timeslot_id,)
        ).fetchone()
        return _row_to_timeslot(row) if row else None

    @staticmethod
    def list_available(
        connection: sqlite3.Connection,
        after: datetime,
        limit: int = 30,
    ) -> list[Timeslot]:
        rows = connection.execute(
            """
            SELECT * FROM timeslots
            WHERE status = 'available' AND start_time > ?
            ORDER BY start_time
            LIMIT ?
            """,
            (to_database(after), limit),
        ).fetchall()
        return [_row_to_timeslot(row) for row in rows]

    @staticmethod
    def list_future(
        connection: sqlite3.Connection,
        after: datetime,
        limit: int = 50,
    ) -> list[Timeslot]:
        rows = connection.execute(
            """
            SELECT * FROM timeslots
            WHERE start_time > ?
            ORDER BY start_time
            LIMIT ?
            """,
            (to_database(after), limit),
        ).fetchall()
        return [_row_to_timeslot(row) for row in rows]

    @staticmethod
    def change_status(
        connection: sqlite3.Connection,
        timeslot_id: int,
        expected_status: str,
        new_status: str,
    ) -> bool:
        cursor = connection.execute(
            """
            UPDATE timeslots SET status = ?
            WHERE id = ? AND status = ?
            """,
            (new_status, timeslot_id, expected_status),
        )
        return cursor.rowcount == 1


def _row_to_timeslot(row: sqlite3.Row) -> Timeslot:
    return Timeslot(
        id=row["id"],
        start_time=from_database(row["start_time"]),
        end_time=from_database(row["end_time"]),
        status=row["status"],
    )

