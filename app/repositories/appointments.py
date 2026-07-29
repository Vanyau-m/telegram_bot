from __future__ import annotations

import sqlite3
from datetime import datetime

from app.models import Appointment
from app.utils.dates import from_database, to_database


class AppointmentsRepository:
    @staticmethod
    def create(
        connection: sqlite3.Connection,
        client_id: int,
        timeslot_id: int,
        created_at: datetime,
    ) -> Appointment:
        cursor = connection.execute(
            """
            INSERT INTO appointments
                (client_id, timeslot_id, status, created_at)
            VALUES (?, ?, 'active', ?)
            """,
            (client_id, timeslot_id, to_database(created_at)),
        )
        return AppointmentsRepository.get(connection, cursor.lastrowid)  # type: ignore[return-value]

    @staticmethod
    def get(
        connection: sqlite3.Connection, appointment_id: int
    ) -> Appointment | None:
        row = connection.execute(
            "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
        return _row_to_appointment(row) if row else None

    @staticmethod
    def count_active_between(
        connection: sqlite3.Connection,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        row = connection.execute(
            """
            SELECT COUNT(*) AS amount
            FROM appointments AS a
            JOIN timeslots AS t ON t.id = a.timeslot_id
            WHERE a.status = 'active'
              AND t.start_time >= ?
              AND t.start_time < ?
            """,
            (to_database(start_time), to_database(end_time)),
        ).fetchone()
        return int(row["amount"])

    @staticmethod
    def next_active_for_client(
        connection: sqlite3.Connection,
        client_id: int,
        after: datetime,
    ) -> Appointment | None:
        row = connection.execute(
            """
            SELECT a.*
            FROM appointments AS a
            JOIN timeslots AS t ON t.id = a.timeslot_id
            WHERE a.client_id = ?
              AND a.status = 'active'
              AND t.start_time > ?
            ORDER BY t.start_time
            LIMIT 1
            """,
            (client_id, to_database(after)),
        ).fetchone()
        return _row_to_appointment(row) if row else None

    @staticmethod
    def cancel(
        connection: sqlite3.Connection,
        appointment_id: int,
        cancelled_at: datetime,
    ) -> bool:
        cursor = connection.execute(
            """
            UPDATE appointments
            SET status = 'cancelled', cancelled_at = ?
            WHERE id = ? AND status = 'active'
            """,
            (to_database(cancelled_at), appointment_id),
        )
        return cursor.rowcount == 1

    @staticmethod
    def list_future_active(
        connection: sqlite3.Connection,
        after: datetime,
    ) -> list[Appointment]:
        rows = connection.execute(
            """
            SELECT a.*
            FROM appointments AS a
            JOIN timeslots AS t ON t.id = a.timeslot_id
            WHERE a.status = 'active' AND t.start_time > ?
            ORDER BY t.start_time
            """,
            (to_database(after),),
        ).fetchall()
        return [_row_to_appointment(row) for row in rows]


def _row_to_appointment(row: sqlite3.Row) -> Appointment:
    cancelled = row["cancelled_at"]
    return Appointment(
        id=row["id"],
        client_id=row["client_id"],
        timeslot_id=row["timeslot_id"],
        status=row["status"],
        created_at=from_database(row["created_at"]),
        cancelled_at=from_database(cancelled) if cancelled else None,
    )
