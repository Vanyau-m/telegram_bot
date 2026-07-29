from dataclasses import dataclass

from app.config import Settings
from app.services import (
    BookingService,
    ClientsService,
    DialogLogService,
    TimeslotsService,
)
from app.services.reminders import ReminderService


@dataclass(slots=True)
class Runtime:
    settings: Settings
    clients: ClientsService
    timeslots: TimeslotsService
    bookings: BookingService
    reminders: ReminderService
    dialog_logs: DialogLogService
