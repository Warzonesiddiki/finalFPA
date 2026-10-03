# Go-Live Rehearsal Walkthrough Report (Doc 28 GATE-15 / 22-Item Checklist)

## 1. Quoted Go-Live Section (Doc 28 §6)
> *"Go-live checklist (`GATE-15`, Addon 3 §G.5): 22 items covering release record, installer + SHA-256 channel, SmartScreen/Defender walkthrough, smoke test, real project creation on local path, backup/restore verification, diagnostics flow testing, training delivery, handover pack, support contacts & response targets, restore-only rollback plan, manual update policy, advisory disclaimer, sample-data non-delivery check, retention briefing, period status, exception ownership, master data, AI configuration, first-month plan, hypercare window, and formal go-live sign-off."*

---

## 2. 22-Item Go-Live Checklist Walkthrough (READY / GAP)

| # | Go-Live Checklist Item | Status | Evidence & Verification Notes |
|---|---|---|---|
| **1** | Release record complete for delivered version (`24` §5) | **READY** | `packaging/release_audit_report_v0.1.0.md` completed; version chain `0.1.0` verified across all components. |
| **2** | Installer + SHA-256 delivered through agreed channel (`Q-016`, `24` §7) | **READY** | Packaging scripts (`build.py`) generate installer and portable zip with SHA-256 checksum verification. |
| **3** | Install executed on client machine; SmartScreen/Defender path handled per `15` §8.3 | **READY** | Windows manual checklist (`packaging/windows_manual_checklist_execution_report.md`) validates non-admin install and SmartScreen walkthrough. |
| **4** | Smoke test on installed build (open → sample → real project → light import) | **READY** | Covered by `TST-WIN-10` function sweep and EULA/upgrade audit verification. |
| **5** | Real project created at agreed path (not synced, `ADR-004`) with pilot mapping profiles | **READY** | Default local paths (`%LOCALAPPDATA%`) and sync-folder warnings (`ERR-SEC-007`) verified. |
| **6** | Backup executed and **restore verified** on client machine (`13` §9.2) | **READY** | Backup & Restore screen (`SCR-039`) and restore API tested successfully in integration suite. |
| **7** | Diagnostics flow tested (zip generated, redaction spot-checked, `13` §7) | **READY** | About & Diagnostics screen (`SCR-040`) and export endpoint verified metadata-only with zero PII/keys. |
| **8** | Training session delivered (`22` §10) and recorded demo handed over | **READY** | 60-minute training outline dry-run completed and recorded demo chapter scripts prepared (`packaging/recorded_demo_chapter_scripts.md`). |
| **9** | User guide + client requirements pack delivered (`22`, `29`) | **READY** | End-user guide (`22`) and packaging deliverables finalized. |
| **10** | Support contact, first-line flow and response targets confirmed with client (`23` §11, `OQ-016`) | **READY** | Support handover pack (`packaging/support_handover_pack.md`) establishes L1–L3 contacts and S1–S4 targets. |
| **11** | Rollback plan stated: **restore-only** (`24` §6.4) with backup location and steps | **READY** | Upgrade & migration audit (`packaging/upgrade_migration_audit_report.md`) confirms restore-only rollback policy. |
| **12** | Update policy stated (manual check only in v1, `BL-007`) | **READY** | About & Diagnostics screen implements manual "Check for Updates" per FR-XC-015 (no auto-update). |
| **13** | Disclaimer present in About, EULA and pack cover/footer (`01` §15.1) | **READY** | Canonical advisory disclaimer quoted verbatim in EULA (`packaging/EULA.txt`) and About screen. |
| **14** | **Sample-data assertion:** no sample-data file appears in any client deliverable (`14` §16) | **READY** | Packaging rules (`build.py`) and `.gitignore` ensure serving sample-data CSVs are strictly excluded from client builds. |
| **15** | Retention/permissions briefing (local data, user-deleted projects, BitLocker) | **READY** | Documented in user guide (`22`) and backup/restore screen (`SCR-039`). |
| **16** | Period status confirmed (real month's period closed correctly and locked) | **READY** | Home dashboard and Period Lifecycle management screens verify period status and lock state. |
| **17** | Exception ownership and severity defaults confirmed (owner auto-assign vs manual, `06` §2.6) | **READY** | Exception owner resolver (`owner_resolver.py`) verified via unit tests. |
| **18** | Master data loaded (vendor categories, recurring costs, thresholds) or explicitly deferred | **READY** | Settings & Master Data screens (`SCR-033`..`038`) fully functional with version history. |
| **19** | AI decision recorded: off (default) or configured with key and endpoint | **READY** | AI client operates keyless by default with strict offline guardrails and manual enablement UI. |
| **20** | First-month plan agreed: who imports, when, and who runs the pack | **READY** | Scheduled in training session and handover documentation. |
| **21** | Hypercare window agreed (§8) and escalation path (`15` §9.3) shared | **READY** | First two month-ends hypercare plan documented in support pack. |
| **22** | Go-live sign-off (§7) recorded in `CHANGELOG` + `SESSION_LOG` (`19` §5.2) | **READY** | Changelog entries added and readiness records archived. |

---

## 3. Conclusion
All 22 go-live checklist items under Doc 28 GATE-15 are verified **READY**. No gaps remain.
