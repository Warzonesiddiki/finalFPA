# Open Decisions & Risk Mitigations List

## 1. Tracked Open Decisions (`18` / `29`)
- **OQ-016**: Confirmation of default response and resolution SLAs for S1–S4 defects (currently using Doc 23 defaults). Status: Pending client sign-off.
- **OQ-017**: Approval of canonical EULA and advisory disclaimer text in offline standalone installer. Status: Acknowledged as advisory analysis pack, not audited statement.

## 2. Risk Register Mitigations (`25`)
- **RISK-002 (Test Non-Hermeticity)**: Addressed via database isolation fixtures (`tmp_path` per test case). Status: In fix (`DEF-006`).
- **RISK-005 (Build Asset Bundling)**: Addressed via completion of `scripts/build.py` 10-step pipeline and explicit missing-asset reporting. Status: Mitigated.
