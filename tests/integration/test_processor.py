"""Полный путь от файлов к очищенному JSON."""

import json
import logging
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.exceptions import DataFormatError
from app.services.integration import integrate
from app.services.processor import Processor


def test_csv_one_good_two_bad(input_dir: Path, tmp_path: Path) -> None:
    # Arrange: ровно одна хорошая и две плохие строки.
    (input_dir / "mixed.csv").write_text(
        "id,amount,category,date\n"
        "good,0.01,sales,2026-10-01\n"
        "zero,0,sales,2026-10-01\n"
        "bad,garbage,sales,2026-10-01\n", encoding="utf-8",
    )
    output = tmp_path / "result.json"
    # Act: чтение → валидация → агрегация → экспорт.
    report = Processor().process(input_dir, output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    # Assert: проверяем сам JSON, а не только счётчик.
    assert len(payload["records"]) == 1
    assert payload["records"][0]["id"] == "good"
    assert payload["totals"] == {"sales": "0.01"}
    assert report.accepted == 1
    assert len(report.issues) == 2
    assert report.failed == 1


def test_duplicate_currency_and_partial_result(
    input_dir: Path, valid_record: dict[str, object],
) -> None:
    rows = [
        valid_record | {"amount": "bad"},
        valid_record,
        valid_record,
        valid_record | {"id": "usd", "currency": "USD"},
        valid_record | {"id": "second", "amount": "0.02"},
    ]
    (input_dir / "a.json").write_text(json.dumps(rows), encoding="utf-8")
    report = integrate(input_dir)
    assert [r.id for r in report.records] == ["transaction-1", "second"]
    assert report.totals == {"sales": Decimal("0.03")}
    assert len(report.issues) == 3
    assert "Повторный id" in report.issues[1].message
    assert "USD" in report.issues[2].message


def test_mixed_formats_and_broken_file(
    input_dir: Path, valid_record: dict[str, object],
    caplog: pytest.LogCaptureFixture,
) -> None:
    (input_dir / "a.json").write_text("{", encoding="utf-8")
    (input_dir / "b.JSON").write_text(
        json.dumps([valid_record]), encoding="utf-8"
    )
    (input_dir / "c.csv").write_text(
        "id,amount,category,date\n2,2,services,2026-10-01\n",
        encoding="utf-8",
    )
    (input_dir / "skip.txt").write_text("ignored", encoding="utf-8")
    (input_dir / "subfolder").mkdir()
    with caplog.at_level(logging.WARNING):
        report = integrate(input_dir)
    assert (report.processed, report.successful, report.failed) == (3, 2, 1)
    assert report.totals == {"sales": Decimal("0.01"), "services": Decimal(2)}
    assert "a.json" in caplog.text
    assert "skip.txt" in caplog.text


def test_large_amounts_do_not_lose_small_amount(
    input_dir: Path, valid_record: dict[str, object],
) -> None:
    rows = [valid_record | {"amount": "1e308"},
            valid_record | {"id": "small", "amount": "0.01"}]
    (input_dir / "large.json").write_text(json.dumps(rows), encoding="utf-8")
    report = integrate(input_dir)
    expected = Decimal("1" + "0" * 308 + ".01")
    assert report.totals["sales"] == expected


def test_empty_directory(input_dir: Path, tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    report = Processor().process(input_dir, output)
    assert report.processed == 0
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "currency": None, "records": [], "totals": {},
    }


def test_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(DataFormatError, match="директории"):
        integrate(tmp_path / "missing")


def test_directory_access_denied(input_dir: Path) -> None:
    with patch.object(Path, "iterdir", side_effect=PermissionError("locked")):
        with pytest.raises(DataFormatError, match="доступа"):
            integrate(input_dir)
