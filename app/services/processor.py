"""Связывает обработку входной папки и запись результата."""

from pathlib import Path

from app.core.models import Report
from app.io.writer import save_report
from app.services.integration import integrate


class Processor:
    """Полный путь: прочитать → проверить → посчитать → сохранить."""

    def process(self, directory: Path, output: Path) -> Report:
        report = integrate(directory)
        save_report(report, output)
        return report
