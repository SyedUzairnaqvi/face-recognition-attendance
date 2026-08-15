from app.db.database import init_db
from app.db.crud import create_attendance, attendance_exists


def test_duplicate_attendance_is_blocked(tmp_path, monkeypatch):
    # This test targets the UNIQUE(name, date) rule in the real schema.
    init_db()
    assert create_attendance("TestUser", "2099-01-01", "09:00:00") is True
    assert create_attendance("TestUser", "2099-01-01", "09:01:00") is False
    assert attendance_exists("TestUser", "2099-01-01") is True
