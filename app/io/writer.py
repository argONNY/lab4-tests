"""Атомарная запись: старый отчёт сохраняется при сбое записи."""

import json
import os
from pathlib import Path

from app.core.exceptions import DataFormatError
from app.core.models import Report


def save_report(report: Report, destination: Path) -> None:
    """Сначала пишем соседний временный файл, затем заменяем итоговый."""
    temporary = destination.with_name(destination.name + ".tmp")
    payload = {
        "currency": report.currency,
        "records": [
            {
                "id": record.id,
                "amount": str(record.amount),
                "category": record.category,
                "date": record.date.isoformat(),
                "currency": record.currency,
            }
            for record in report.records
        ],
        # Строки сохраняют точные десятичные суммы без округления float.
        "totals": {
            key: str(value)
            for key, value in sorted(report.totals.items())
        },
    }
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(destination)
    except (OSError, ValueError) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise DataFormatError(f"Не удалось сохранить отчёт: {exc}") from exc
