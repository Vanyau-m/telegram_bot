from __future__ import annotations

import logging
from datetime import timedelta

from telegram.ext import Application, CallbackContext

from app.services.booking import BookingDetails, BookingService
from app.utils.dates import format_local, utc_now


logger = logging.getLogger(__name__)


class ReminderService:
    def __init__(
        self,
        booking_service: BookingService,
        master_telegram_id: int,
        timezone,
        reminder_minutes: int,
    ) -> None:
        self.booking_service = booking_service
        self.master_telegram_id = master_telegram_id
        self.timezone = timezone
        self.reminder_minutes = reminder_minutes

    def schedule(self, application: Application, details: BookingDetails) -> bool:
        job_queue = application.job_queue
        if job_queue is None:
            logger.error("JobQueue недоступна: установите extra [job-queue]")
            return False

        reminder_time = details.timeslot.start_time - timedelta(
            minutes=self.reminder_minutes
        )
        if reminder_time <= utc_now():
            return False

        self.cancel(application, details.appointment.id)
        job_queue.run_once(
            self._send,
            when=reminder_time,
            data=details.appointment.id,
            name=self._job_name(details.appointment.id),
        )
        return True

    def cancel(self, application: Application, appointment_id: int) -> None:
        if application.job_queue is None:
            return
        for job in application.job_queue.get_jobs_by_name(
            self._job_name(appointment_id)
        ):
            job.schedule_removal()

    def restore(self, application: Application) -> int:
        restored = 0
        for details in self.booking_service.list_future():
            if self.schedule(application, details):
                restored += 1
        return restored

    async def _send(self, context: CallbackContext) -> None:
        appointment_id = int(context.job.data)
        details = self.booking_service.get_details(appointment_id)
        if details is None or details.appointment.status != "active":
            return

        start = format_local(details.timeslot.start_time, self.timezone)
        client_text = (
            f"Напоминание: ваша запись начнётся через "
            f"{self.reminder_minutes} минут — {start}."
        )
        master_text = (
            f"Напоминание: через {self.reminder_minutes} минут запись "
            f"{details.client.full_name} ({details.client.phone}), {start}."
        )
        await context.bot.send_message(
            chat_id=details.client.telegram_id, text=client_text
        )
        await context.bot.send_message(
            chat_id=self.master_telegram_id, text=master_text
        )

    @staticmethod
    def _job_name(appointment_id: int) -> str:
        return f"appointment:{appointment_id}"

