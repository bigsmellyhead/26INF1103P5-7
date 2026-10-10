# data_manager.py
import json
import os

DB_FILE = "audit_history.json"

def initialize_database():
    """Ensures the JSON file exists with a basic structure and won't crash if cleared."""
    if not os.path.exists(DB_FILE):
        create_default_db()
    else:
        try:
            with open(DB_FILE, "r") as file:
                data = json.load(file)
                if not isinstance(data, dict) or "users" not in data or "audit_logs" not in data:
                    create_default_db()
        except (json.JSONDecodeError, ValueError):
            create_default_db()

def create_default_db():
    initial_data = {
        "users": {},
        "audit_logs": []
    }
    save_database(initial_data)

def load_database():
    initialize_database()
    with open(DB_FILE, "r") as file:
        return json.load(file)

def save_database(data):
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

def get_user_profile(username):
    db = load_database()
    return db["users"].get(username.lower())

def save_user_profile(username, restrictions):
    db = load_database()
    db["users"][username.lower()] = {
        "username": username,
        "restrictions": restrictions
    }
    save_database(db)

def append_audit_log(audit_record):
    db = load_database()
    db["audit_logs"].append(audit_record)
    save_database(db)