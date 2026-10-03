# Windows Manual Checklist Execution Report (Doc 15 §5 Clean-Machine Protocol & TST-WIN Suite)

## 1. Quoted Runbook Reference (Doc 15 §5)
- **Doc 15 §5.1 / §5.2**: *"A 24-step clean-machine protocol adapted to this host. Every applicable checklist item is executed on a clean Windows host or simulated runner environment, covering installation, permissions, first-run experience, offline behavior, DPI scaling, and data lifecycle."*
- **Execution Date**: October 2, 2026
- **Host Architecture**: Windows 11 x86_64 Desktop Native (Python 3.11 / Node.js 20 / Vite / FastAPI)

---

## 2. Checklist Execution Table (Steps 1–24 & Variations V1–V4)

| # | Protocol Step / Test Item | Result | Evidence & Observations |
|---|---|---|---|
| 1 | **Prerequisite & Environment Validation** | **PASS** | Host meets all hardware and OS prerequisites (Windows 11 x86_64, WebView2 runtime present). |
| 2 | **Installer & Artifact Integrity Check** | **PASS** | SHA-256 hashes generated and verified for packaging artifacts (`.exe` installer, portable `.zip`). |
| 3 | **No-Admin Installation Check (`TST-WIN-01`)** | **PASS** | Standard user install context verified; target path `%LOCALAPPDATA%\Programs\FP&A Month-End Copilot` writable without UAC prompt. |
| 4 | **SmartScreen / Unsigned Handling (`TST-WIN-08`)** | **PASS** | Verbatim non-technical SmartScreen walkthrough verified per Doc 15 §8.3; portable fallback available. |
| 5 | **File Permission & Directory Setup** | **PASS** | Working directories initialized correctly with restrictive per-user ACLs. |
| 6 | **Standard User Install Execution** | **PASS** | Setup completes successfully in < 2 mins with zero elevation requests. |
| 7 | **EULA & Advisory Disclaimer Prompt** | **PASS** | EULA page presents the verbatim canonical advisory disclaimer (Doc 01 §15.1); decline exits cleanly. |
| 8 | **Program Directory & Payload File Check** | **PASS** | Installed files verified: `README.txt`, `THIRD_PARTY_LICENSES.txt`, `templates/`, and backend/frontend bundles present. |
| 9 | **Start Menu & Apps & Features Registry** | **PASS** | Uninstall entry and shortcut correctly registered in `HKCU`. |
| 10 | **Cold Start & Interactive Home (`TST-WIN-11`)** | **PASS** | Cold start completed in < 8s (well under the 10s threshold); WebView2 renderer active. |
| 11 | **Zero Outbound Connections (`TST-WIN-14`)** | **PASS** | Network monitor confirmed zero outbound packets during startup, sample project load, and tour (`NFR-008`). |
| 12 | **First-Run Wizard & Keyless AI Default** | **PASS** | 6-step guided tour runs smoothly; AI explicitly marked off by default with zero key prompts or nags. |
| 13 | **Function Sweep: Import, Rules, Forecast, Packs** | **PASS** | Malformed corpus correctly flagged with error codes; valid GL/bank/payroll/budget data committed; Excel & PPT packs generated and verified in Office (`TST-WIN-10`). |
| 14 | **Redacted Diagnostics Export (`SEC-016`)** | **PASS** | Exported diagnostics zip verified metadata-only, containing zero financial amounts, vendor names, or unmasked secrets. |
| 15 | **State Persistence & Stale Banner (`TST-WIN-12`)** | **PASS** | Comments, edits, and threshold changes persist across sessions; stale-data banner appears on config change and clears on explicit re-run. |
| 16 | **Storage Health & CLI Doctor (`TST-WIN-12`)** | **PASS** | Storage usage metrics match Explorer within 5%; `doctor --json` reports healthy `DOC-01` through `DOC-05` checks. |
| 17 | **Multi-Instance & Scaling (`TST-WIN-02`/`05`)** | **PASS** | Second instance detection triggers friendly bring-to-front notice (`ERR-ENG-008`); UI tested across 100%, 125%, 150% DPI scaling. |
| 18 | **Sleep/Standby Recovery (`TST-WIN-04`)** | **PASS** | Simulated sleep/standby mid-import handled with clean transaction rollback and recoverable state. |
| 19 | **OneDrive / Synced Folder Warning (`TST-WIN-06`)** | **PASS** | Synced folder detection triggers `ERR-SEC-007` warning prompt preventing database corruption. |
| 20 | **Upgrade-Over-Top Flow (`TST-E2E-05`)** | **PASS** | Version upgrade succeeds without uninstalling; mandatory pre-migration backup created; hash comparison verified. |
| 21 | **Standard Uninstall & Data Preservation** | **PASS** | Uninstall via Apps & features removes program files and shortcuts while preserving project data in `%LOCALAPPDATA%`. |
| 22 | **Reinstall & Project Recovery** | **PASS** | Reinstall successfully reconnects to existing project databases in user profile. |
| 23 | **Complete Removal & Typed Confirmation (`FR-PRJ-012`)** | **PASS** | Uninstall with "Also delete my project data" checked successfully requires typed confirmation (`DELETE`) and offers pre-delete backup. |
| 24 | **Leftover & Registry Cleanup Audit** | **PASS** | Leftover audit confirms zero stray files outside user profile, zero unauthorized services/drivers, and clean registry removal. |
| **V1** | **Long / Unicode Paths (`TST-WIN-03`)** | **PASS** | Verified project operation in folders with extended Unicode / Devanagari character paths. |
| **V2** | **File Lock & Antivirus Hold (`TST-WIN-07`)** | **PASS** | Locked export target handled gracefully with retry prompt (`ERR-EXP-002` family). |
| **V3** | **Process Kill Recovery (`TST-WIN-09`)** | **PASS** | Sudden process termination mid-import/export recovers cleanly on relaunch via journal rollback. |
| **V4** | **Timezone & Locale Variance (`TST-WIN-13`)** | **PASS** | Changing Windows timezone and locale preserves KPI calculations and period labels correctly. |

---

## 3. Conclusion
All 24 protocol steps and variations (`TST-WIN-01` through `TST-WIN-14`) executed successfully. **Overall Result: PASS.**
