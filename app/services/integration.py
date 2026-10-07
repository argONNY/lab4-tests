"""Обход файлов, накопление ошибок и подсчёт сумм."""

import logging
from decimal import Decimal, localcontext
from pathlib import Path

from app.core.exceptions import (
    BaseAppError,
    CurrencyMismatchError,
    DataFormatError,
    DuplicateIdError,
)
from app.core.models import Issue, Report
from app.io.readers import READERS
from app.services.validation import validate_record

LOGGER = logging.getLogger(__name__)


def add_issue(report: Report, path: Path, row: int | None,
              error: BaseAppError) -> None:
    """Сохраняем ошибку для сводки и записываем её в журнал."""
    issue = Issue(path, row, str(error))
    report.issues.append(issue)
    LOGGER.error("%s", issue)


def integrate(directory: Path) -> Report:
    """Ошибочная запись не мешает обработать остальные записи и файлы."""
    try:
        if not directory.is_dir():
            raise DataFormatError(f"Нет входной директории: {directory}")
        paths = sorted(directory.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise DataFormatError(f"Нет доступа к директории: {exc}") from exc

    report = Report()
    seen: set[str] = set()
    for path in paths:
        if path.is_dir():
            continue
        reader_class = READERS.get(path.suffix.lower())
        if reader_class is None:
            LOGGER.warning("Пропущен неподдерживаемый файл: %s", path.name)
            continue
        report.processed += 1
        errors_before = len(report.issues)
        try:
            rows = reader_class().read(path)
        except BaseAppError as exc:
            add_issue(report, path, None, exc)
        else:
            for number, raw in enumerate(rows, start=1):
                try:
                    record = validate_record(raw)
                    if record.id in seen:
                        raise DuplicateIdError(f"Повторный id: {record.id}")
                    if report.currency not in (None, record.currency):
                        raise CurrencyMismatchError(
                            f"Валюта {record.currency}, ожидается "
                            f"{report.currency}"
                        )
                    report.currency = record.currency
                    seen.add(record.id)
                    previous = report.totals.get(record.category, Decimal(0))
                    # Точная сумма даже при сильно разных порядках чисел.
                    with localcontext() as context:
                        low = min(
                            int(previous.as_tuple().exponent),
                            int(record.amount.as_tuple().exponent),
                        )
                        high = max(
                            previous.adjusted(), record.amount.adjusted()
                        )
                        context.prec = max(28, high - low + 2)
                        total = previous + record.amount
                    report.totals[record.category] = total
                    report.records.append(record)
                    report.accepted += 1
                except BaseAppError as exc:
                    add_issue(report, path, number, exc)
        if len(report.issues) == errors_before:
            report.successful += 1
        else:
            report.failed += 1
    return report
