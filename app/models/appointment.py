from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Appointment:
    id: int
    client_id: int
    timeslot_id: int
    status: str
    created_at: datetime
    cancelled_at: datetime | None = None

