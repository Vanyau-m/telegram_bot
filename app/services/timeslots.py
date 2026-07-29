from __future__ import annotations

import sqlite3
from datetime import datetime

from app.database import Database
from app.models import Timeslot
from app.repositories import TimeslotsRepository
from app.services.errors import DuplicateSlotError, PastSlotError
from app.utils.dates import utc_now


class TimeslotsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, start_time: datetime, end_time: datetime) -> Timeslot:
        if start_time <= utc_now():
            raise PastSlotError("Нельзя добавить слот в прошлом")
        if end_time <= start_time:
            raise ValueError("Время окончания должно быть позже времени начала")
        try:
            with self.database.transaction(immediate=True) as connection:
                return TimeslotsRepository.create(connection, start_time, end_time)
        except sqlite3.IntegrityError as exc:
            raise DuplicateSlotError("Такой слот уже существует") from exc

    def list_available(self, limit: int = 30) -> list[Timeslot]:
        with self.database.transaction() as connection:
            return TimeslotsRepository.list_available(
                connection, after=utc_now(), limit=limit
            )

    def list_future(self, limit: int = 50) -> list[Timeslot]:
        with self.database.transaction() as connection:
            return TimeslotsRepository.list_future(
                connection, after=utc_now(), limit=limit
            )

    def get(self, timeslot_id: int) -> Timeslot | None:
        with self.database.transaction() as connection:
            return TimeslotsRepository.get(connection, timeslot_id)

