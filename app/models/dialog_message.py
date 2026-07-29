from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DialogMessage:
    id: int
    direction: str
    telegram_user_id: int | None
    chat_id: str
    username: str | None
    first_name: str | None
    last_name: str | None
    message_text: str | None
    message_type: str
    telegram_message_id: int | None
    update_id: int | None
    created_at: datetime

