"""Командный интерфейс: сводка и ожидаемые ошибки без traceback."""

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

import main as cli
from app.core.exceptions import DataFormatError


@pytest.fixture(autouse=True)
def isolated_logging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Журнал тестов не должен создаваться рядом с реальными данными.
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)


def test_cli_success(input_dir: Path, tmp_path: Path,
                     valid_record: dict[str, object],
                     capsys: pytest.CaptureFixture[str]) -> None:
    (input_dir / "valid.json").write_text(
        json.dumps([valid_record]), encoding="utf-8"
    )
    output = tmp_path / "result.json"
    assert cli.main([str(input_dir), "--output", str(output)]) == 0
    captured = capsys.readouterr()
    assert "Успешно: 1" in captured.out
    assert "Список ошибок" not in captured.out
    assert captured.err == ""
    assert output.exists()


def test_cli_partial_result(input_dir: Path, tmp_path: Path,
                            capsys: pytest.CaptureFixture[str]) -> None:
    (input_dir / "bad.json").write_text("{", encoding="utf-8")
    assert cli.main([str(input_dir)]) == 0
    captured = capsys.readouterr()
    assert "Список ошибок" in captured.out
    assert "bad.json" in captured.out
    assert "Traceback" not in captured.out + captured.err


def test_cli_missing_directory(tmp_path: Path,
                               capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([str(tmp_path / "missing")]) == 1
    captured = capsys.readouterr()
    assert "Ошибка:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_output_inside_input_rejected(input_dir: Path) -> None:
    assert cli.main([
        str(input_dir), "--output", str(input_dir / "result.json")
    ]) == 1


def test_cli_log_unavailable(input_dir: Path,
                             capsys: pytest.CaptureFixture[str]) -> None:
    with patch("main.logging.basicConfig", side_effect=PermissionError):
        assert cli.main([str(input_dir)]) == 1
    assert "журнал" in capsys.readouterr().err


def test_cli_reports_write_failure(input_dir: Path, tmp_path: Path,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    # Пустой input_dir: единственный open здесь — запись результата.
    output = tmp_path / "result.json"
    output.write_text("OLD REPORT", encoding="utf-8")
    with patch.object(Path, "open", side_effect=PermissionError("read only")):
        code = cli.main([str(input_dir), "--output", str(output)])
    captured = capsys.readouterr()
    assert code == 1
    assert "сохранить" in captured.err
    assert "Traceback" not in captured.err
    assert output.read_text(encoding="utf-8") == "OLD REPORT"


def test_processor_failure_is_reported(
    input_dir: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    with patch("main.Processor.process", side_effect=DataFormatError("bad")):
        assert cli.main([str(input_dir)]) == 1
    assert "bad" in capsys.readouterr().err
