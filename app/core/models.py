"""Типы данных, которые передаются между слоями."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Record:
    """Проверенная финансовая запись."""

    id: str
    amount: Decimal
    category: str
    date: date
    currency: str


@dataclass(frozen=True)
class Issue:
    """Одна накопленная ошибка файла или записи."""

    path: Path
    row: int | None
    message: str

    def __str__(self) -> str:
        location = self.path.name
        if self.row is not None:
            location += f", запись {self.row}"
        return f"{location}: {self.message}"


@dataclass
class Report:
    """Результаты обработки; счётчики относятся к файлам."""

    processed: int = 0
    successful: int = 0
    failed: int = 0
    accepted: int = 0
    currency: str | None = None
    totals: dict[str, Decimal] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    records: list[Record] = field(default_factory=list)
