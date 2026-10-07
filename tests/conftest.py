"""Общие фикстуры. Все временные данные создаются через tmp_path."""

from pathlib import Path

import pytest


@pytest.fixture
def valid_record() -> dict[str, object]:
    """Каждый тест получает новую, независимую запись."""
    return {
        "id": "transaction-1",
        "amount": "0.01",
        "category": "sales",
        "date": "2026-10-01",
        "currency": "RUB",
    }


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "data"
    directory.mkdir()
    return directory
