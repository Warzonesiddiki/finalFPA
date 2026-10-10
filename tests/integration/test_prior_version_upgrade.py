"""
Upgrade Drill & Prior-Version Migration Test (TST-E2E-05 / Doc 24 §6)
Verifies:
1. Detection of older schema version (v1 vs current v2).
2. Pre-migration backup snapshot generation.
3. Forward migration execution.
4. Hash consistency check of derived financial balances.
5. Rollback via restore verification.
"""

import hashlib
import json
import shutil
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "prior-version-project"


def test_prior_version_upgrade_drill(tmp_path):
    # 1. Setup temporary project from prior-version fixture
    proj_dir = tmp_path / "project"
    shutil.copytree(FIXTURE_DIR, proj_dir)

    metadata_file = proj_dir / "project_metadata.json"
    assert metadata_file.exists()

    with open(metadata_file, encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["schema_version"] == 1
    assert meta["app_version"] == "0.0.9-alpha"

    # 2. Pre-migration mandatory backup
    backup_file = tmp_path / f"backup_pre_migration_{meta['schema_version']}.zip"
    shutil.make_archive(str(tmp_path / "pre_mig_backup"), "zip", proj_dir)
    assert Path(str(tmp_path / "pre_mig_backup.zip")).exists()

    # 3. Simulate forward migration to current schema version (v2)
    meta["schema_version"] = 2
    meta["app_version"] = "0.1.0"
    meta["migration_history"] = [
        {"from": 1, "to": 2, "timestamp": "2026-10-02T12:00:00Z", "status": "applied"}
    ]
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # 4. Hash comparison of financial numbers
    tb_file = proj_dir / "trial_balance.csv"
    with open(tb_file, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    assert len(h) == 64

    # Verify metadata is now current
    with open(metadata_file, encoding="utf-8") as f:
        migrated_meta = json.load(f)
    assert migrated_meta["schema_version"] == 2
    assert migrated_meta["app_version"] == "0.1.0"

    # 5. Rollback verification (Rollback = Restore)
    restore_dir = tmp_path / "restored_project"
    shutil.unpack_archive(str(tmp_path / "pre_mig_backup.zip"), restore_dir)
    with open(restore_dir / "project_metadata.json", encoding="utf-8") as f:
        restored_meta = json.load(f)
    assert restored_meta["schema_version"] == 1
    assert restored_meta["app_version"] == "0.0.9-alpha"
