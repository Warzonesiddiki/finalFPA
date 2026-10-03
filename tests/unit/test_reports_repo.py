import pytest
from app.engine.store.reports_repo import ReportsRepository
from app.engine.store.db import DatabaseManager

def test_reports_repo_comprehensive(tmp_path):
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    repo = ReportsRepository(db_mgr)
    
    pack1 = repo.generate_excel_pack_file(period_code="2025-P03", scenario="base", generated_by="Tester")
    assert pack1 is not None

    deck1 = repo.generate_deck_file(period_code="2025-P03", scenario="base", generated_by="Tester")
    assert deck1 is not None

    packs = repo.get_packs(period_code="2025-P03")
    assert len(packs) >= 2

    all_packs = repo.get_packs()
    assert len(all_packs) >= 2

    listed_packs = repo.list_packs(period_code="2025-P03")
    assert len(listed_packs) == len(packs)

    all_listed_packs = repo.list_packs()
    assert len(all_listed_packs) == len(all_packs)

    issuances = repo.get_issuance_register(period_id=1)
    assert isinstance(issuances, list)

    comms = repo.get_commentaries(period_id=1)
    assert isinstance(comms, list)
