import pytest


def _db_modules():
    try:
        from app.db.database import init_db
        from app.db.crud import create_attendance, attendance_exists
        init_db()
        return init_db, create_attendance, attendance_exists
    except Exception as exc:
        pytest.skip(f"MySQL integration test requires a reachable configured database: {exc}")


def test_duplicate_attendance_is_blocked():
    # Integration test: the real MySQL UNIQUE(person_id, attendance_date)
    # constraint must make the second insert a no-op.
    _, create_attendance, attendance_exists = _db_modules()
    assert create_attendance("TestUser", "2099-01-01", "09:00:00") is True
    assert create_attendance("TestUser", "2099-01-01", "09:01:00") is False
    assert attendance_exists("TestUser", "2099-01-01") is True
