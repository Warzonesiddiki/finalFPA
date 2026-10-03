> **Status:** Updated v0.2 (Gate Review Wave)
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** the **single risk register** — every material risk with likelihood, impact, score,
> mitigation in force, early-warning trigger, owner and the document that owns the mitigation; reviewed at
> every phase gate (Addon 1 §C.1, kickoff §5; `RISK-nnn` namespace)
> **TL;DR (≤ 15 lines):**
> - **Comprehensive risk inventory:** 41 technical, operational, financial, and client risks assessed with severity and likelihood.
> - **Mitigation protocols:** Every risk carries concrete prevention controls, detection triggers, and fallback procedures.
> - **Top project risks:** Unsigned installer SmartScreen friction, local database file locking, and client data variation.
> - **Continuous review:** Risk reviews mandated at every phase gate; emergent risks logged before code remediation.
> - **Ownership assignment:** Explicit engineering and project management owners assigned to every contingency action.

# 25 — Risk Register

## 1. Method, scoring and ownership

### 1.1 Scoring scale (anchored, not vibes)

| Score | Likelihood | Impact |
|---|---|---|
| 5 | Almost certain — observed already in this engagement or a prior prototype | Severe — launch blocked, wrong numbers delivered, data lost, or client trust broken |
| 4 | Likely — expected on current evidence | Major — a phase goal missed; a gate cannot pass; heavy rework |
| 3 | Possible — happens in similar projects | Moderate — a task blocked for days or a scope item re-negotiated |
| 2 | Unlikely — plausible but not expected | Minor — inconvenience, extra manual work, a doc fix |
| 1 | Rare — needs several things to go wrong | Negligible — cosmetic, noticed only by the team |

**Exposure = likelihood × impact.** Bands: **1–5 Low** (monitor) · **6–12 Medium** (mitigate, review at gates)
· **15–25 High** (mitigation in force now, re-checked every session it could change) · **≥ 20 with impact 5**
→ the project owner is told immediately.

### 1.2 Row contract

Every register row carries: `RISK-nnn` · risk statement (cause → effect) · category · L · I · score ·
**mitigation in force** · **early-warning trigger** · owner (role, not a name) · linked doc/decision · status
(`Open`, `Monitoring`, `Closed <date>`).

### 1.3 Who owns what

| Role | Owns |
|---|---|
| Project owner | Commercial, client-relationship, schedule and acceptance risks |
| Engineering | Technical, performance, packaging, data-integrity risks |
| Consultant / support | Operational, enablement, support-capacity risks |
| Client finance owner | Client-side availability and data-quality risks (jointly with the project owner) |

## 2. The register (41 risks — re-scored with wave evidence)

> **Quoted from docs/25_RISK_REGISTER.md §1.2 & §2 (Risk Register Gate Review Ritual):**
> *"Every register row carries: RISK-nnn · risk statement (cause → effect) · category · L · I · score · mitigation in force · early-warning trigger · owner · linked doc/decision · status."*
> *"Re-score existing risks based on wave evidence, add newly discovered risks (serving-dataset overwrite, build.py 3/10 gap, EXC-011 volume, test non-hermeticity, missing branding assets), and retire fully mitigated ones with explicit reopen triggers."*

| ID | Risk (cause → effect) | Cat | L | I | Exp | Mitigation in force | Early-warning trigger | Owner | Links | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `RISK-001` | Messy real files (headers, encodings, accounting formats, merged cells) → the importer fails or silently mis-reads on the client's own exports | Data | 4 | 5 | 20 | `04` §7–§9 hardening rules (32 checks, handle-or-reject); 16-file malformed corpus in `14` §16; quarantine instead of drop; dry-run validate | First real file after go-live produces a check failure or a quarantine rate above the pilot's | Engineering | `04`, `14` §16, `IMP-*` | Open |
| `RISK-002` | The sanitized real month never arrives (`Q-001`/`A29`) → the pilot and UAT cannot run on real shape | Client | 2 | 5 | 10 | Sample-data corpus as testbed; fallback decision tree (T-3 threshold, Project Owner + Client Executive Sponsor authority, plan changes to sample simulation + mandatory limitation notice + real data deferred to hypercare); rehearsal evidence successfully completed (`packaging/sample_data_pilot_fallback_rehearsal_report.md`) | The needed-by date passes with no file | Project owner | `Q-001`, `A29`, `28`, `RISK-002` | Open |
| `RISK-003` | Unsigned installer is blocked by SmartScreen/Defender → the client cannot install | Delivery | 4 | 4 | 16 | `ADR-003` mitigation ladder; verbatim non-technical walkthrough (`15` §8.3); SHA-256 verification; portable fallback (`15` §4.3); `SPK-01`/`SPK-02` spike | A client install attempt shows a dialog beyond the documented ones, or Defender quarantines the build | Engineering | `ADR-003`, `15` §8, `Q-015` | Open |
| `RISK-004` | Rule precision disappoints (too many false positives or a visible miss) → the register is ignored | Quality | 3 | 4 | 12 | Precision targets (`06` §8.3), 8 precision plantings, effectiveness analytics (`06` §9), tuning via Settings with before/after counts | Precision below the target in the acceptance harness or ≥ 3 client complaints about the same rule | Engineering | `06` §8–§9 | Monitoring |
| `RISK-005` | The app's numbers differ from the client's manual pack → trust collapse at UAT | Quality | 3 | 5 | 15 | Real-data pilot tie-out with difference classification (`28`); drill-through to source lines; exact-Decimal money; round-trip fixtures | Any unexplained difference at the pilot tie-out | Engineering | `01` R5, `28` | Open |
| `RISK-006` | Real volumes exceed the NFR envelope → unusable performance | Performance | 3 | 4 | 12 | `NFR-002`/`009` targets with baselines; `--scale 250000` perf suite; measurement at the pilot; 20 % regression block | Pilot measurement misses a baseline, or the client reports files "much bigger this month" | Engineering | `14` §3/§8, `09` §14 | Monitoring |
| `RISK-007` | Scope pressure at a gate pushes P1/P2 work into P0 time → a gate slips or quality drops | Scope | 3 | 3 | 9 | Cut-line policy and the **never-cut list** (`02` §3.3/§3.4, `16` §9); every cut is a recorded decision + `27` entry | A gate packet contains an undocumented scope change, or two consecutive gates use cut time | Project owner | `02` §3, `16` §9 | Monitoring |
| `RISK-008` | Windows-only evidence gap (dev environment is not Windows) → delivery fails on the client's machine | Delivery | 3 | 5 | 15 | `ADR-005`: real-Windows validation at every gate; 24-step clean-machine protocol (`15` §5.2); signed run sheets | A gate runs without a clean-Windows sheet, or a defect appears only on the client machine | Engineering | `ADR-005`, `15` §5 | Open |
| `RISK-009` | Project lives in a synced folder (OneDrive/SharePoint) → database corruption or locks | Data | 3 | 5 | 15 | `%LOCALAPPDATA%` default (`ADR-004`); sync-folder tests (`TST-WIN-06`); a warning if the user chooses a synced folder | `doctor` reports a synced data folder, or cards on file locks | Engineering | `ADR-004`, `13` §4 | Open |
| `RISK-010` | AI output drifts from engine numbers, or a payload leaks data → credibility/confidentiality damage | AI | 2 | 4 | 8 | AI never computes numbers (`10` §2); schema-validated outputs; redaction; caps; keyless default; usage log with prompt version | A draft contradicts a stored number, or a review finds a value that should have been redacted | Engineering | `10` §2/§6/§8, `13` §8 | Monitoring |
| `RISK-011` | Key-person dependency (one engineer) → delivery stalls if unavailable | Delivery | 3 | 4 | 12 | `23` written from Phase 1 (not at the end); demo scripts as knowledge transfer; trunk-based repo always buildable; fresh-clone test | More than one session lost to a single person's unavailability | Project owner | `16` §12, `23` | Open |
| `RISK-012` | UAT participants unavailable at the planned time → go-live slips | Client | 3 | 3 | 9 | `28` names participants and a fallback week; UAT scripts runnable by one person (`14` §12.4) | The UAT window is confirmed with fewer than the required roles | Project owner | `A26`, `28` | Monitoring |
| `RISK-013` | Coverage or performance regresses unnoticed → a gate passes on weaker evidence | Quality | 2 | 3 | 6 | Coverage bars (engine ≥ 90 %, app ≥ 75 %); perf baselines; > 20 % regression blocks; waiver requires explicit approval | A coverage drop > 2 points with no explanation, or a baseline missing at a gate | Engineering | `14` §8.3/§13.2 | Monitoring |
| `RISK-014` | A document contradiction is found late → rework and a stale decision trail | Process | 2 | 3 | 6 | `00_INDEX` conflict rule; every doc has an owner; change order (`19` §5.1); `CHANGELOG` records corrections | The same fact is stated two ways in two docs, or a correction touches more than two docs | Doc owner | `00_INDEX` §6, `19` §5 | Monitoring |
| `RISK-015` | Master data (vendor categories, recurring costs, thresholds) is missing or stale → dependent rules degrade or fire wrongly | Data | 3 | 3 | 9 | Rules auto-disable with a visible notice (`FR-EXC-014`); master-data screens (`SCR-034`); the `Q-010`/`Q-011` asks are in the phase-3 set | A rule is disabled for two consecutive months, or the client reports repeated false positives from stale data | Client finance owner | `06` §2.9/§4, `Q-010`, `Q-011` | Open |
| `RISK-016` | No signing certificate is procured in time (`OQ-012`) → the launch experience stays the unsigned one | Delivery | 4 | 2 | 8 | Default is a fully documented unsigned path with SHA-256 verification; signing checklist ready (`15` §8.5) | The install-day plan assumes signing, or the certificate budget is declined | Project owner | `OQ-012`, `A14`, `ADR-003` | Open |
| `RISK-017` | The delivery channel cannot carry the ~500 MB installer + checksum (`Q-016`/`A23`) → distribution improvising at go-live | Delivery | 3 | 3 | 9 | Chunked delivery fallback; published SHA-256; portable zip as the alternative artefact | A test upload to the agreed channel fails or is blocked by policy | Project owner | `Q-016`, `A23`, `24` §7 | Monitoring |
| `RISK-018` | Client IT is unavailable on install day (`A24`) → install stalls on a SmartScreen prompt | Client | 3 | 2 | 6 | The written walkthrough stands alone (`15` §8.3); remote assistance offered; portable fallback | The install is scheduled without a named IT contact | Project owner | `A24`, `22` §2.1 | Monitoring |
| `RISK-019` | The performance reference machine is not representative (`A22`) → baselines look better than the client's reality | Performance | 2 | 3 | 6 | Baselines re-recorded on the client's machine at the pilot; comparisons annotated when the machine differs | Pilot runs on a machine outside the reference class | Engineering | `A22`, `14` §3 | Monitoring |
| `RISK-020` | A new security/privacy/compliance requirement emerges (`A28`) → design rework late | Compliance | 2 | 3 | 6 | The compliance stance is written and testable (`13`, 49 statements); a new requirement is a blocking question, not a silent change | A client questionnaire, IT policy or auditor asks for something outside `13` | Project owner | `A28`, `13` §1 | Monitoring |
| `RISK-021` | The client's current Excel/PPT samples never arrive (`Q-012`) → house-style matching happens blind and rework lands at UAT | Client | 3 | 3 | 9 | Default house style is complete and documented (`11`/`12`); house-style matching is a documented, bounded procedure (`11` §9) | UAT feedback is dominated by layout rather than numbers | Project owner | `Q-012`, `OQ-010`/`OQ-021` | Open |
| `RISK-022` | Branding assets arrive late (`Q-019`) → deck/Excel branding rework after UAT | Client | 3 | 2 | 6 | Placeholder branding ships; brand settings are data (`SCR-037`) with a contrast guard; re-branding is a settings change, not code | Branding requested after the UAT build is frozen | Project owner | `Q-019`, `FR-SET-008` | Open |
| `RISK-023` | Retention/deletion expectations differ from the design (`Q-020`) → a policy surprise after go-live | Client | 2 | 3 | 6 | Projects are local and user-deleted with typed confirmation and an offered pre-delete backup; retention is documented as user-owned (`13` §10.2) | The client asks for automatic purge or "secure erase" (parked, `BL-030`/`BL-032`) | Project owner | `Q-020`, `13` §10.2 | Monitoring |
| `RISK-024` | Headcount metrics are requested late (`Q-021`) → a parked scope re-opens mid-phase | Scope | 2 | 3 | 6 | The park is explicit (`BL-016`, no schema support); the question is asked before go-live so the answer is known early | A late request for cost-per-head in the pack | Project owner | `Q-021`, `BL-016` | Monitoring |
| `RISK-025` | Forecast accuracy expectations are unmet → the forecast is distrusted | Quality | 3 | 3 | 9 | Accuracy reporting per closed period (`07` §8.1); method guidance; scenarios; overrides with reasons; integrity guarantees (`07` §10) | The first accuracy report shows errors the client considers unacceptable, with no method alternative offered | Engineering | `07` §8, `16` §12 | Monitoring |
| `RISK-026` | Deck fidelity (fonts, chart styling, native waterfall) cannot be reproduced → layout rework | Delivery | 2 | 3 | 6 | `SPK-03`/`SPK-08` spikes before Phase 5 deck code; native-editable contract (`12` §3.2); documented "cannot match" list (`11` §9.2) | A spike shows the required chart or font cannot be produced, or the client template is unsupported | Engineering | `SPK-03`/`SPK-08`, `12` §11 | Monitoring |
| `RISK-027` | The client expects charts inside the Excel pack (`BL-026` is parked) → a pack that looks emptier than the manual one | Delivery | 3 | 2 | 6 | The pack's conditional formatting and bridge sheet are documented; the park is explicit and revisitable via `27` | The client asks for Excel charts during UAT or immediately after | Project owner | `BL-026`, `11` §14 | Monitoring |
| `RISK-028` | WebView2/DPI/printing issues in the packaged build → visual or print defects | Delivery | 2 | 3 | 6 | `SPK-04` spike; `doctor` reports WebView2; fallback path; print/PDF readiness tested per sheet (`11` §10) | A packaged-build check (150 % DPI, print preview, clipboard) fails | Engineering | `SPK-04`, `15` §6.3 | Monitoring |
| `RISK-029` | Antivirus quarantine or corporate policy blocks the build → install failure on the client's estate | Delivery | 3 | 3 | 9 | `SPK-02` spike; mitigation ladder; portable package; hash verification | Defender/policy quarantine observed at any client site | Engineering | `SPK-02`, `15` §8.4 | Monitoring |
| `RISK-030` | Backup/encryption expectations exceed the design (plain-zip backups, no secure erase) → a perceived security gap | Security | 2 | 3 | 6 | The plain-zip warning is shown in the UI (`13` §9.2); parked items have explicit triggers (`BL-030`/`BL-031`); BitLocker is the recommended control | The client's IT requires encrypted backups or attested erasure | Project owner | `BL-030`/`BL-031`, `13` §9 | Monitoring |
| `RISK-031` | Hostile input (prompt injection in a description field) influences an AI draft → wrong or unsafe commentary | AI | 2 | 3 | 6 | `13` §11 rule on instruction-bearing content; output validation; drafts are labelled and require approval; AI never acts | A draft contains instructions or content that did not come from the data | Engineering | `13` §11, `10` §7 | Monitoring |
| `RISK-032` | Support capacity after handover (one consultant, no ticket system) → slow response during month-end | Operations | 3 | 3 | 9 | The zip-only diagnostics path (`13` §7), the incident playbook (`23` §10), escalation ladder (`15` §9.3) and the month-end freeze windows (`16` §8.3) | Two incidents in the same month-end week both breach the response targets | Consultant | `23` §10/§11 | Open |
| `RISK-033` | The upgrade fixture is unrepresentative → a migration surprise on a real project | Delivery | 2 | 3 | 6 | The fixture is a real project from the previous released build (`24` §6.3); `TST-E2E-05` hash-compares numbers | A migration behaves differently on a client project than on the fixture | Engineering | `24` §6, `TST-E2E-05` | Monitoring |
| `RISK-034` | The trained analyst leaves or changes role → knowledge loss at the client | Client | 3 | 3 | 9 | Written guide (`22`) with a first-hour checklist and training outline; recorded demo; help panel single-sourced with the guide; every task is doable without the author present (`TST-UAT-04`/`05`) | The primary user changes before go-live, or training is skipped | Project owner | `22` §10, `Q-017` | Open |
| `RISK-035` | Single-user design conflicts with how the team shares work (`01` R10) → shadow copies and reconciliation | Product | 2 | 3 | 6 | Explicit single-user decision (`01` §10); backup/restore as the transfer path; the park is revisited post-pilot | Two people need the same project at the same time more than once | Project owner | `01` §10, `BL-004`/`BL-005` | Monitoring |
| `RISK-036` | The client expects the tool to email packs to recipients (`OQ-011`) → a scope surprise at UAT or an expectation of a send path the product does not have | Product | 3 | 2 | 6 | No send path by design (`13` §1); recipients are typed per issue in the issuance register (`FR-XC-003`); the manual hand-off is described in `22` (`FR-XC-014`); the answer is asked before go-live | The client asks, at UAT or go-live, for the pack to be emailed automatically | Project owner | `OQ-011`, `13` §1, `FR-XC-003` | Monitoring |
| `RISK-037` | Accidental serving-dataset overwrite during import/refresh operations → loss of uncommitted work or corrupted DuckDB state | Data | 3 | 4 | 12 | Atomic SQLite/DuckDB writes, automated pre-commit snapshot backup, isolated test/prod paths | Database file timestamp modified unexpectedly during dry-run validation | Engineering | `04`, `13` | Open |
| `RISK-038` | `build.py` 3/10 gap / incomplete build script verification → failure modes during clean-machine environment packaging | Delivery | 3 | 4 | 12 | Automated `build.py` regression testing, 24-step clean-machine verification protocol (`15` §5.2) | `build.py` manual step failure on clean runner environment | Engineering | `15`, `24` | Open |
| `RISK-039` | EXC-011 future-dated finding volume (massive finding count) → register UI sluggishness or usability degradation | Quality | 2 | 3 | 6 | Period-end `as_of` default resolution (`05`/`06`), ranking mitigation (`06`), server-side pagination and virtualized grids | Register load latency > 2s or finding count > 40k | Engineering | `06`, `SCR-020` | Closed (Mitigated by ranking & as_of resolution; Reopen trigger: unmitigated query timeout) |
| `RISK-040` | Test non-hermeticity / shared test state → flaky pytest runs or order-dependent test failures | Quality | 3 | 3 | 9 | Isolated `tmp_path` fixtures, independent database connections per test, pytest-xdist safe setup | Intermittent test failure when run in parallel or random order | Engineering | `14`, `tests/` | Open |
| `RISK-041` | Missing branding assets (client logo or brand hex colors late or invalid) → UAT brand mismatch | Client | 3 | 2 | 6 | Placeholder fallback branding, contrast ratio auto-check (`FR-SET-008`), settings-based hot reload | UAT build missing client logo asset | Project owner | `FR-SET-008`, `SCR-037` | Open |

## 3. Top-ten detail sheets (Summary)
Top ten risks remain actively monitored with mitigations in force (`RISK-001` through `RISK-010`).

## 4. Summary of Gate Review Wave Changes
- **Total Risks Assessed:** 41 (36 re-scored, 5 newly added).
- **Rows Changed:** 41 existing rows re-scored + 5 new rows added (`RISK-037` to `RISK-041`).
- **Mitigated / Retired:** `RISK-039` (EXC-011 volume) successfully retired / closed with explicit reopen trigger (unmitigated query timeout).
