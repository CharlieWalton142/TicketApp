# tests/conftest.py
import os
import sys
import pytest

# Ensure project root (where db.py lives) is on the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import db 
import auth


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path, monkeypatch):
    """
    For every test run, point DB_PATH at a temporary sqlite file
    and initialise schema there. This avoids touching your real DB.
    """
    test_db_path = tmp_path / "test_ticketapp.db"

    # override DB_PATH in the db module
    monkeypatch.setattr(db, "DB_PATH", str(test_db_path))
    monkeypatch.setattr(auth, "DB_PATH", str(test_db_path))

    # create tables in that temp file
    db.init_db()

    yield