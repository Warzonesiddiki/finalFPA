from app.engine.imports.profile_binding import (
    next_import_run_id,
    resolve_base_profile,
    verify_run_id_prediction,
)
from app.engine.store.db import DatabaseManager


def test_profile_binding_with_db(tmp_path):
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    rid = next_import_run_id(db_mgr)
    assert isinstance(rid, int)
    pred, max_id = verify_run_id_prediction(db_mgr)
    assert isinstance(pred, int)
    assert isinstance(max_id, int)
    prof = resolve_base_profile(db_mgr, ["Account", "Amount"], "trial_balance")
    assert prof is None or hasattr(prof, "profile_id")
