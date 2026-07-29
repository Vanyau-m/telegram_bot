from __future__ import annotations

import re


PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 ()-]{7,19}$")


def normalize_full_name(value: str) -> str:
    full_name = " ".join(value.strip().split())
    if len(full_name) < 3:
        raise ValueError("ФИО слишком короткое")
    if len(full_name) > 100:
        raise ValueError("ФИО не должно быть длиннее 100 символов")
    if any(char.isdigit() for char in full_name):
        raise ValueError("ФИО не должно содержать цифры")
    return full_name


def normalize_phone(value: str) -> str:
    phone = value.strip()
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValueError("Введите телефон, например: +7 999 123-45-67")
    digits = "".join(char for char in phone if char.isdigit())
    return f"+{digits}" if phone.startswith("+") else digits

