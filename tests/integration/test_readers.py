"""Чтение реальных временных файлов разных форматов."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.exceptions import DataFormatError
from app.io.readers import READERS, CsvReader, JsonReader, Reader


@pytest.mark.parametrize("reader, suffix, content", [
    (CsvReader(), ".csv", ""),
    (CsvReader(), ".csv", "id,id\n1,2\n"),
    (CsvReader(), ".csv", "id,amount,category,date\n"),
    (CsvReader(), ".csv", 'id,amount\n1,"unterminated'),
    (JsonReader(), ".json", ""),
    (JsonReader(), ".json", "[{"),
    (JsonReader(), ".json", "[]"),
    (JsonReader(), ".json", "{}"),
])
def test_malformed_files(tmp_path: Path, reader: Reader,
                         suffix: str, content: str) -> None:
    path = tmp_path / f"bad{suffix}"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataFormatError):
        reader.read(path)


@pytest.mark.parametrize("suffix", [".csv", ".json"])
def test_binary_disguised_as_text(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"image{suffix}"
    path.write_bytes(b"\x89PNG\r\n\x1a\n")
    with pytest.raises(DataFormatError):
        READERS[suffix]().read(path)


@pytest.mark.parametrize("suffix", [".csv", ".json"])
def test_permission_denied_is_wrapped(tmp_path: Path, suffix: str) -> None:
    with patch.object(Path, "open", side_effect=PermissionError("locked")):
        with pytest.raises(DataFormatError) as captured:
            READERS[suffix]().read(tmp_path / f"locked{suffix}")
    assert isinstance(captured.value.__cause__, PermissionError)


def test_csv_bom_and_quoted_category(tmp_path: Path) -> None:
    path = tmp_path / "valid.csv"
    path.write_text(
        'id,amount,category,date\n1,1.25,"sales, online",2026-10-01\n',
        encoding="utf-8-sig",
    )
    rows = CsvReader().read(path)
    assert len(rows) == 1
    assert rows[0]["category"] == "sales, online"


def test_json_reader(tmp_path: Path, valid_record: dict[str, object]) -> None:
    path = tmp_path / "valid.json"
    path.write_text(json.dumps([valid_record]), encoding="utf-8-sig")
    assert JsonReader().read(path) == [valid_record]
