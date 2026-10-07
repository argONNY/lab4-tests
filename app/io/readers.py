"""Чтение форматов без проверки финансовой логики."""

import csv
import json
from pathlib import Path
from typing import Any, Protocol

from app.core.exceptions import DataFormatError


class Reader(Protocol):
    """Общий интерфейс обработчиков."""

    def read(self, path: Path) -> list[Any]:
        ...


class CsvReader:
    """CSV с заголовком и разделителем-запятой."""

    def read(self, path: Path) -> list[Any]:
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                headers = reader.fieldnames
                if not headers:
                    raise DataFormatError("Пустой CSV или нет заголовка")
                if len(headers) != len(set(headers)):
                    raise DataFormatError("Повторяющиеся колонки CSV")
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise DataFormatError(f"Не удалось прочитать CSV: {exc}") from exc
        if not rows:
            raise DataFormatError("CSV не содержит записей")
        return rows


class JsonReader:
    """JSON должен содержать массив записей."""

    def read(self, path: Path) -> list[Any]:
        try:
            with path.open(encoding="utf-8-sig") as stream:
                data = json.load(stream)
        except (OSError, UnicodeError, ValueError, RecursionError) as exc:
            raise DataFormatError(f"Не удалось прочитать JSON: {exc}") from exc
        if not isinstance(data, list) or not data:
            raise DataFormatError("Ожидается непустой JSON-массив записей")
        return data


# Новый формат подключается добавлением класса в этот реестр.
READERS: dict[str, type[Reader]] = {
    ".csv": CsvReader,
    ".json": JsonReader,
}
