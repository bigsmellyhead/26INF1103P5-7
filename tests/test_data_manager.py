import json
import pytest
import data_manager as dm


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    """Use a temporary JSON database for each test."""
    db_file = tmp_path / "audit_history.json"
    monkeypatch.setattr(dm, "DB_FILE", str(db_file))
    return db_file