"""Имитируем системные ошибки без изменения прав реального диска."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.exceptions import DataFormatError
from app.core.models import Report
from app.io.writer import save_report


def test_write_protected_disk(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text("OLD REPORT", encoding="utf-8")
    with patch.object(Path, "open", side_effect=PermissionError("read only")):
        with pytest.raises(DataFormatError, match="сохранить") as captured:
            save_report(Report(), output)
    assert isinstance(captured.value.__cause__, PermissionError)
    assert output.read_text(encoding="utf-8") == "OLD REPORT"


def test_replace_failure_preserves_old_report(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text("OLD REPORT", encoding="utf-8")
    with patch.object(Path, "replace", side_effect=PermissionError("locked")):
        with pytest.raises(DataFormatError):
            save_report(Report(), output)
    assert output.read_text(encoding="utf-8") == "OLD REPORT"
    assert not (tmp_path / "result.json.tmp").exists()


def test_disk_full_preserves_old_report(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text("OLD REPORT", encoding="utf-8")
    with patch("app.io.writer.os.fsync", side_effect=OSError("disk full")):
        with pytest.raises(DataFormatError, match="disk full"):
            save_report(Report(), output)
    assert output.read_text(encoding="utf-8") == "OLD REPORT"
    assert not (tmp_path / "result.json.tmp").exists()


def test_cleanup_failure_keeps_original_error(tmp_path: Path) -> None:
    with patch.object(Path, "open", side_effect=PermissionError("read only")):
        with patch.object(Path, "unlink", side_effect=PermissionError):
            with pytest.raises(DataFormatError, match="read only"):
                save_report(Report(), tmp_path / "result.json")
