import pytest
from decimal import Decimal
from app.engine.store.db import DatabaseManager
from app.engine.store.exceptions_repo import ExceptionsRepository

def test_owner_distribution_and_evidence_bundle(tmp_path):
    """Test FR-EXC-016 (evidence bundle) and FR-EXC-017 (owner-wise distribution)."""
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    repo = ExceptionsRepository(db_mgr)

    # Test owner distribution
    dist = repo.get_owner_distribution(period_code="FY26-P09")
    assert isinstance(dist, dict)
    assert "ownerSummaries" in dist
    assert "csvContent" in dist
    assert "teamsSummary" in dist
    assert "Owner,RuleID" in dist["csvContent"]
    assert "Exception Ownership Distribution Report" in dist["teamsSummary"]
