"""Границы сумм и некорректные данные: Arrange → Act → Assert."""

from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import InvalidTransactionError, ValidationError
from app.services.validation import validate_record


@pytest.mark.parametrize("amount, expected", [
    ("0.01", Decimal("0.01")),
    (0.01, Decimal("0.01")),
    (1, Decimal("1")),
    ("100.50", Decimal("100.50")),
    ("1e308", Decimal("1e308")),
    (0, None), ("0", None), (-1, None), (-0.01, None),
    ("abc", None), (None, None), (True, None), (False, None),
    ("NaN", None), ("sNaN", None), ("Infinity", None),
    ("-Infinity", None), ("1e309", None), ("1e-400", None),
    ([], None), ({}, None),
])
def test_amount_boundaries(
    valid_record: dict[str, object], amount: object,
    expected: Decimal | None,
) -> None:
    # Arrange: меняем только сумму, остальные поля корректны.
    valid_record["amount"] = amount
    if expected is None:
        # Act + Assert: именно доменная ошибка, а не случайный сбой.
        with pytest.raises(ValidationError):
            validate_record(valid_record)
    else:
        record = validate_record(valid_record)
        assert record.amount == expected


@pytest.mark.parametrize("field, value", [
    ("id", ""), ("id", "  "), ("id", None), ("id", True),
    ("id", 1.5), ("id", []), ("category", ""), ("category", 2),
    ("date", "2026-02-30"), ("date", "2026-13-01"),
    ("date", "01.10.2026"), ("date", "20261001"), ("date", None),
    ("currency", "rub"), ("currency", "RU"), ("currency", 1),
])
def test_invalid_fields(valid_record: dict[str, object],
                        field: str, value: object) -> None:
    valid_record[field] = value
    with pytest.raises(InvalidTransactionError):
        validate_record(valid_record)


@pytest.mark.parametrize("garbage", [None, [], [1], 12, "garbage", {}])
def test_garbage_raises_domain_error_not_index_error(garbage: object) -> None:
    with pytest.raises(InvalidTransactionError) as captured:
        validate_record(garbage)
    assert type(captured.value) is InvalidTransactionError
    assert isinstance(captured.value, ValidationError)


@pytest.mark.parametrize("field", ["id", "amount", "category", "date"])
def test_missing_field(valid_record: dict[str, object], field: str) -> None:
    del valid_record[field]
    with pytest.raises(InvalidTransactionError, match=field):
        validate_record(valid_record)


def test_extra_csv_values(valid_record: dict[str, object]) -> None:
    raw: dict[object, object] = {
        key: value for key, value in valid_record.items()
    }
    raw[None] = ["extra"]
    with pytest.raises(InvalidTransactionError, match="колонок"):
        validate_record(raw)


def test_normalization_and_default_currency(
    valid_record: dict[str, object],
) -> None:
    valid_record.update(id=7, category=" services ", date="2024-02-29")
    del valid_record["currency"]
    record = validate_record(valid_record)
    assert record.id == "7"
    assert record.category == "services"
    assert record.currency == "RUB"
    assert record.date == date(2024, 2, 29)
