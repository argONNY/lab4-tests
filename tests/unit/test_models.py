"""Модели не разделяют изменяемые данные между экземплярами."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.core.models import Issue, Report
from app.services.validation import validate_record


def test_report_collections_are_independent() -> None:
    first, second = Report(), Report()
    first.issues.append(Issue(Path("bad.csv"), 2, "bad"))
    assert second.issues == []
    assert first.totals is not second.totals
    assert first.records is not second.records


@pytest.mark.parametrize("row, expected", [
    (None, "bad.csv: bad"), (2, "bad.csv, запись 2: bad"),
])
def test_issue_description(row: int | None, expected: str) -> None:
    assert str(Issue(Path("bad.csv"), row, "bad")) == expected


def test_validated_record_is_frozen(valid_record: dict[str, object]) -> None:
    record = validate_record(valid_record)
    with pytest.raises(FrozenInstanceError):
        setattr(record, "id", "changed")
