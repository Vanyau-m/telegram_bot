from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Client:
    telegram_id: int
    full_name: str
    phone: str
    created_at: datetime

