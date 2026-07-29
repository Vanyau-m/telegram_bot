import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from app.database import Database
from app.services import BookingService, ClientsService, TimeslotsService
from app.services.errors import (
    AlreadyBookedError,
    DailyLimitReachedError,
    SlotUnavailableError,
)
from app.utils.dates import utc_now


class BookingServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        database = Database(Path(self.temp_directory.name) / "test.db")
        database.initialize()
        self.database = database
        self.clients = ClientsService(database)
        self.timeslots = TimeslotsService(database)
        self.bookings = BookingService(database, ZoneInfo("UTC"), 6)
        self.clients.register(1, "Иван Иванов", "+79991234567")
        self.clients.register(2, "Анна Петрова", "+79997654321")

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_booking_and_cancellation_release_exact_slot(self):
        start = utc_now() + timedelta(days=2)
        first = self.timeslots.create(start, start + timedelta(hours=1))
        second = self.timeslots.create(
            start + timedelta(hours=2), start + timedelta(hours=3)
        )

        details = self.bookings.create(1, first.id)
        self.assertEqual(details.timeslot.id, first.id)

        with self.assertRaises(AlreadyBookedError):
            self.bookings.create(1, second.id)

        cancelled = self.bookings.cancel_next(1)
        self.assertEqual(cancelled.timeslot.id, first.id)
        self.assertEqual(self.timeslots.get(first.id).status, "available")
        self.assertEqual(self.timeslots.get(second.id).status, "available")

    def test_same_slot_cannot_be_booked_twice(self):
        start = utc_now() + timedelta(days=2)
        slot = self.timeslots.create(start, start + timedelta(hours=1))
        self.bookings.create(1, slot.id)

        with self.assertRaises(SlotUnavailableError):
            self.bookings.create(2, slot.id)

    def test_daily_limit(self):
        limited = BookingService(self.database, ZoneInfo("UTC"), 1)
        start = (utc_now() + timedelta(days=2)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        first = self.timeslots.create(start, start + timedelta(hours=1))
        second = self.timeslots.create(
            start + timedelta(hours=2), start + timedelta(hours=3)
        )
        limited.create(1, first.id)

        with self.assertRaises(DailyLimitReachedError):
            limited.create(2, second.id)

    def test_database_enables_foreign_keys(self):
        with self.database.transaction() as connection:
            enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(enabled, 1)


if __name__ == "__main__":
    unittest.main()
