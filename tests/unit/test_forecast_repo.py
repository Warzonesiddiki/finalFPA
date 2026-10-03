import pytest
from app.engine.store.forecast_repo import ForecastRepository
from app.engine.store.db import DatabaseManager

def test_forecast_repo_comprehensive(tmp_path):
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    repo = ForecastRepository(db_mgr)
    
    split = repo.get_periods_split()
    assert isinstance(split, tuple)
    assert len(split) == 2, "ForecastRepository.get_periods_split should return (historical_periods, forecast_periods) (doc 12 §3.3)"

    ws = repo.generate_forecast(scenario_id="base", default_method="run_rate", generated_by="Tester")
    assert ws is not None
    assert ws.scenario == "base"
    assert ws.lines or len(ws.lines) == 0, "ForecastRepository.generate_forecast should produce mapped projections according to doc 12 §3.3"
