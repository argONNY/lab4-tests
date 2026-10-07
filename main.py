"""Точка входа: аргументы, журнал, обработка и итоговая сводка."""

import argparse
import logging
import sys
from pathlib import Path

from app.core.exceptions import BaseAppError
from app.services.processor import Processor

ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    """0 — обработка завершена, 1 — неустранимая ошибка."""
    parser = argparse.ArgumentParser(description="Интеграция CSV и JSON")
    parser.add_argument(
        "directory", nargs="?", type=Path, default=ROOT / "data"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "result.json")
    args = parser.parse_args(argv)
    try:
        logging.basicConfig(
            filename=ROOT / "app.log",
            encoding="utf-8",
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    except OSError as exc:
        print(f"Не удалось открыть журнал: {exc}", file=sys.stderr)
        return 1

    if args.output.resolve().parent == args.directory.resolve():
        print("Сохраняйте отчёт вне входной папки.", file=sys.stderr)
        return 1
    try:
        logging.info("Начало обработки %s", args.directory)
        report = Processor().process(args.directory, args.output)
    except (BaseAppError, OSError) as exc:
        logging.error("Неустранимая ошибка: %s", exc)
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(
        f"Обработано файлов: {report.processed}. "
        f"Успешно: {report.successful}. С ошибками: {report.failed}."
    )
    print(f"Принято записей: {report.accepted}. Ошибок: {len(report.issues)}.")
    if report.issues:
        print("Список ошибок:")
        for issue in report.issues:
            print(f"- {issue}")
    print(f"Результат: {args.output.resolve()}")
    logging.info("Завершено. Принято записей: %s", report.accepted)
    return 0


if __name__ == "__main__":
    sys.exit(main())
