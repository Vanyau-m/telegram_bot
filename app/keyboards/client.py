from telegram import ReplyKeyboardMarkup

from app.models import Timeslot
from app.utils.dates import format_local


def slots_keyboard(timeslots: list[Timeslot], timezone) -> ReplyKeyboardMarkup:
    rows = [
        [
            (
                f"{format_local(slot.start_time, timezone)}–"
                f"{slot.end_time.astimezone(timezone).strftime('%H:%M')} "
                f"| ID:{slot.id}"
            )
        ]
        for slot in timeslots
    ]
    rows.append(["Отмена"])
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Выберите свободное время",
    )
