"""Преобразование сырых данных в проверенную модель."""

import math
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.exceptions import InvalidTransactionError
from app.core.models import Record


def validate_record(raw: Any) -> Record:
    """Проверяем обязательные поля, сумму, дату и валюту."""
    if not isinstance(raw, dict):
        raise InvalidTransactionError("Запись должна быть объектом")
    required = {"id", "amount", "category", "date"}
    missing = required - raw.keys()
    if missing:
        raise InvalidTransactionError(
            "Нет полей: " + ", ".join(sorted(missing))
        )
    if None in raw:
        raise InvalidTransactionError("В CSV больше значений, чем колонок")

    identifier = raw["id"]
    if isinstance(identifier, bool) or not isinstance(identifier, (str, int)):
        raise InvalidTransactionError(
            "id должен быть строкой или целым числом"
        )
    identifier = str(identifier).strip()
    if not identifier:
        raise InvalidTransactionError("id не может быть пустым")

    category = raw["category"]
    if not isinstance(category, str) or not category.strip():
        raise InvalidTransactionError("category должна быть непустой строкой")

    try:
        amount = Decimal(str(raw["amount"]))
    except InvalidOperation as exc:
        raise InvalidTransactionError(
            "amount невозможно преобразовать в число"
        ) from exc
    if not amount.is_finite() or amount <= 0:
        raise InvalidTransactionError("amount должна быть конечным числом > 0")
    # ТЗ требует возможность представления amount как float.
    converted = float(amount)
    if not math.isfinite(converted) or converted == 0:
        raise InvalidTransactionError("amount выходит за диапазон float")

    raw_date = raw["date"]
    if not isinstance(raw_date, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", raw_date
    ):
        raise InvalidTransactionError(
            "date должна иметь формат YYYY-MM-DD"
        )
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError as exc:
        raise InvalidTransactionError(
            "Несуществующая календарная дата"
        ) from exc

    currency = raw.get("currency", "RUB")
    if not isinstance(currency, str) or not re.fullmatch(
        r"[A-Z]{3}", currency
    ):
        raise InvalidTransactionError(
            "currency должна состоять из трёх букв A-Z"
        )
    return Record(identifier, amount, category.strip(), parsed_date, currency)
