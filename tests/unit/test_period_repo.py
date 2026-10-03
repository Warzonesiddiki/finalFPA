import pytest
from app.engine.store.period_repo import PeriodRepository
from app.engine.store.db import DatabaseManager

def test_period_repo_operations(tmp_path):
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    repo = PeriodRepository(db_mgr)
    periods = repo.list_periods()
    assert isinstance(periods, list)
    if periods:
        p = repo.get_period(periods[0].period_id)
        assert p is not None
