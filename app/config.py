from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    master_telegram_id: int
    database_path: Path
    log_path: Path
    log_level: str
    timezone: tzinfo
    max_appointments_per_day: int
    reminder_minutes: int

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        _load_env_file(env_file or BASE_DIR / ".env")

        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise ValueError(
                "Не задан BOT_TOKEN. Скопируйте .env.example в .env и добавьте токен."
            )

        master_id = _positive_int("MASTER_TELEGRAM_ID")
        max_per_day = _positive_int("MAX_APPOINTMENTS_PER_DAY", default=6)
        reminder_minutes = _positive_int("REMINDER_MINUTES", default=15)

        timezone_name = os.getenv("TIMEZONE", "Europe/Moscow")
        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            if timezone_name == "Europe/Moscow":
                timezone = timezone_from_moscow_offset()
            else:
                raise ValueError(
                    f"Неизвестный часовой пояс: {timezone_name}"
                ) from exc

        database_path = _resolve_path(
            os.getenv("DATABASE_PATH", "data/database.db")
        )
        log_path = _resolve_path(os.getenv("LOG_PATH", "logs/bot.log"))

        return cls(
            bot_token=token,
            master_telegram_id=master_id,
            database_path=database_path,
            log_path=log_path,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            timezone=timezone,
            max_appointments_per_day=max_per_day,
            reminder_minutes=reminder_minutes,
        )


def _positive_int(name: str, default: int | None = None) -> int:
    raw_value = os.getenv(name)
    if raw_value is None and default is not None:
        return default
    try:
        value = int(raw_value or "")
    except ValueError as exc:
        raise ValueError(f"{name} должен быть целым числом") from exc
    if value <= 0:
        raise ValueError(f"{name} должен быть больше нуля")
    return value


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def _load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE settings without an external dependency."""
    if not path.exists():
        return

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            raise ValueError(
                f"Некорректная строка {line_number} в файле {path.name}"
            )

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            raise ValueError(
                f"Пустое имя настройки в строке {line_number} файла {path.name}"
            )
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(name, value)


def timezone_from_moscow_offset() -> timezone:
    """Windows fallback when the optional IANA timezone database is absent."""
    return timezone(timedelta(hours=3), name="Europe/Moscow")
