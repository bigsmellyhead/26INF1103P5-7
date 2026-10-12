import json
import pytest
import data_manager as dm


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    """Use a temporary JSON database for each test."""
    db_file = tmp_path / "audit_history.json"
    monkeypatch.setattr(dm, "DB_FILE", str(db_file))
    return db_file


def test_initialize_database_creates_missing_file(temp_database):
    dm.initialize_database()

    assert temp_database.exists()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == {
        "users": {},
        "audit_logs": []
    }

def test_initialize_database_keeps_valid_database(temp_database):
    original_data = {
        "users": {"alex": {"username": "Alex", "restrictions": ["halal"]}},
        "audit_logs": [{"dish": "Chicken Rice"}]
    }

    with open(temp_database, "w") as file:
        json.dump(original_data, file)

    dm.initialize_database()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == original_data


def test_initialize_database_resets_invalid_json(temp_database):
    temp_database.write_text("{invalid json")

    dm.initialize_database()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == {"users": {}, "audit_logs": []}



def test_initialize_database_resets_non_dictionary_json(temp_database):
    temp_database.write_text(json.dumps(["not", "a", "dictionary"]))

    dm.initialize_database()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == {"users": {}, "audit_logs": []}


@pytest.mark.parametrize(
    "invalid_data",
    [
        {},
        {"users": {}},
        {"audit_logs": []},
        {"users": [], "audit_logs": []},
    ]
)
def test_initialize_database_resets_missing_or_invalid_structure(
    temp_database, invalid_data
):
    with open(temp_database, "w") as file:
        json.dump(invalid_data, file)

    dm.initialize_database()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == {"users": {}, "audit_logs": []}


# -------------------------
# create_default_db()
# -------------------------

def test_create_default_db_writes_default_structure(temp_database):
    dm.create_default_db()

    with open(temp_database, "r") as file:
        data = json.load(file)

    assert data == {"users": {}, "audit_logs": []}

