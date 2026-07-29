from __future__ import annotations

import re
from datetime import datetime, timezone, tzinfo


UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC)


def to_database(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Дата должна содержать часовой пояс")
    return value.astimezone(UTC).isoformat(timespec="seconds")


def from_database(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def format_local(value: datetime, timezone_value: tzinfo) -> str:
    return value.astimezone(timezone_value).strftime("%d.%m.%Y %H:%M")


def parse_slot_input(text: str, timezone_value: tzinfo) -> tuple[datetime, datetime]:
    normalized = " ".join(text.strip().split())
    patterns = (
        (r"^(\d{2}\.\d{2}\.\d{4}) (\d{2}:\d{2})-(\d{2}:\d{2})$", "%d.%m.%Y %H:%M"),
        (r"^(\d{2} \d{2} \d{4}) (\d{2} \d{2})-(\d{2} \d{2})$", "%d %m %Y %H %M"),
    )

    for pattern, date_format in patterns:
        match = re.match(pattern, normalized)
        if not match:
            continue
        date_part, start_part, end_part = match.groups()
        start = datetime.strptime(
            f"{date_part} {start_part}", date_format
        ).replace(tzinfo=timezone_value)
        end = datetime.strptime(
            f"{date_part} {end_part}", date_format
        ).replace(tzinfo=timezone_value)
        if end <= start:
            raise ValueError("Время окончания должно быть позже времени начала")
        return start, end

    raise ValueError("Используйте формат ДД.ММ.ГГГГ ЧЧ:ММ-ЧЧ:ММ")
