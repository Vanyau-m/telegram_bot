from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Timeslot:
    id: int
    start_time: datetime
    end_time: datetime
    status: str

