from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

from app.database import Database
from app.models import Appointment, Client, Timeslot
from app.repositories import (
    AppointmentsRepository,
    ClientsRepository,
    TimeslotsRepository,
)
from app.services.errors import (
    AlreadyBookedError,
    AppointmentNotFoundError,
    ClientNotFoundError,
    DailyLimitReachedError,
    SlotNotFoundError,
    SlotUnavailableError,
)
from app.utils.dates import utc_now


@dataclass(frozen=True, slots=True)
class BookingDetails:
    appointment: Appointment
    client: Client
    timeslot: Timeslot


class BookingService:
    def __init__(
        self,
        database: Database,
        timezone: tzinfo,
        max_appointments_per_day: int,
    ) -> None:
        self.database = database
        self.timezone = timezone
        self.max_appointments_per_day = max_appointments_per_day

    def create(self, client_id: int, timeslot_id: int) -> BookingDetails:
        now = utc_now()
        with self.database.transaction(immediate=True) as connection:
            client = ClientsRepository.get(connection, client_id)
            if client is None:
                raise ClientNotFoundError("Сначала зарегистрируйтесь через /start")

            existing = AppointmentsRepository.next_active_for_client(
                connection, client_id, now
            )
            if existing is not None:
                raise AlreadyBookedError(
                    "У вас уже есть будущая запись. Сначала отмените её."
                )

            timeslot = TimeslotsRepository.get(connection, timeslot_id)
            if timeslot is None:
                raise SlotNotFoundError("Слот не найден")
            if timeslot.status != "available" or timeslot.start_time <= now:
                raise SlotUnavailableError("Этот слот уже недоступен")

            day_start_local = timeslot.start_time.astimezone(self.timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end_local = day_start_local + timedelta(days=1)
            amount = AppointmentsRepository.count_active_between(
                connection, day_start_local, day_end_local
            )
            if amount >= self.max_appointments_per_day:
                raise DailyLimitReachedError(
                    "На этот день достигнут лимит записей"
                )

            reserved = TimeslotsRepository.change_status(
                connection,
                timeslot_id,
                expected_status="available",
                new_status="booked",
            )
            if not reserved:
                raise SlotUnavailableError("Этот слот только что заняли")

            appointment = AppointmentsRepository.create(
                connection, client_id, timeslot_id, now
            )
            return BookingDetails(appointment, client, timeslot)

    def cancel_next(self, client_id: int) -> BookingDetails:
        now = utc_now()
        with self.database.transaction(immediate=True) as connection:
            appointment = AppointmentsRepository.next_active_for_client(
                connection, client_id, now
            )
            if appointment is None:
                raise AppointmentNotFoundError("У вас нет будущих записей")

            client = ClientsRepository.get(connection, client_id)
            timeslot = TimeslotsRepository.get(connection, appointment.timeslot_id)
            if client is None or timeslot is None:
                raise AppointmentNotFoundError("Данные записи повреждены")

            if not AppointmentsRepository.cancel(
                connection, appointment.id, now
            ):
                raise AppointmentNotFoundError("Запись уже отменена")

            released = TimeslotsRepository.change_status(
                connection,
                timeslot.id,
                expected_status="booked",
                new_status="available",
            )
            if not released:
                raise SlotUnavailableError("Не удалось освободить слот")

            cancelled = Appointment(
                id=appointment.id,
                client_id=appointment.client_id,
                timeslot_id=appointment.timeslot_id,
                status="cancelled",
                created_at=appointment.created_at,
                cancelled_at=now,
            )
            return BookingDetails(cancelled, client, timeslot)

    def get_details(self, appointment_id: int) -> BookingDetails | None:
        with self.database.transaction() as connection:
            appointment = AppointmentsRepository.get(connection, appointment_id)
            if appointment is None:
                return None
            client = ClientsRepository.get(connection, appointment.client_id)
            timeslot = TimeslotsRepository.get(connection, appointment.timeslot_id)
            if client is None or timeslot is None:
                return None
            return BookingDetails(appointment, client, timeslot)

    def list_future(self, after: datetime | None = None) -> list[BookingDetails]:
        with self.database.transaction() as connection:
            appointments = AppointmentsRepository.list_future_active(
                connection, after or utc_now()
            )
            result: list[BookingDetails] = []
            for appointment in appointments:
                client = ClientsRepository.get(connection, appointment.client_id)
                timeslot = TimeslotsRepository.get(
                    connection, appointment.timeslot_id
                )
                if client and timeslot:
                    result.append(BookingDetails(appointment, client, timeslot))
            return result
