> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning areas:** the **single risk register** — every material risk with likelihood, impact, score,
> mitigation in force, early-warning trigger, owner and the document that owns the mitigation; reviewed at
> every phase gate (Addon 1 §C.1, kickoff §5; `RISK-nnn` namespace)
> **TL;DR (≤ 15 lines):**
> - **One register, one scoring scale** (§1): likelihood × impact, anchors tied to this product (launch
>   blocker, wrong numbers, data loss, trust damage), re-scored — never re-stated — at every gate.
> - **A risk without a trigger and an owner is a worry.** Every row names the early warning that says it is
>   happening and the role who acts on it.
> - **The top ten have full sheets** (§3): cause chain, contingency, residual risk, evidence that the
>   mitigation exists, and the decision it links to.
> - **Client-fact risks are seeded from `21`** (§4): `OQ-012`, `OQ-014`, `OQ-016` and the other unanswered
>   items, each with the date it starts to matter.
> - **Deliberate acceptances are written down** (§5): unsigned v1, no RBAC, plain-zip backups, sample data
>   never delivered — with the trigger that would reopen them.
> - **RISK-003 is the SmartScreen/Defender risk** on purpose: `09` `ADR-003` already points at it.
> - **Risk sources are named** (§6): `01` §13, `16` §12, the spike list, the parked items, incident
>   follow-ups from `23` §11 and any counter-evidence found in tests.
> - **A risk that materialises becomes a defect or an incident** — it is not left in the register as a
>   lesson.
> - **Mitigations are documents, not intentions**: every row links the doc that owns it.
> - **Never-cut items are not risks to be traded** (`02` §3.3); if one is threatened, scope is cut instead.
> - **Review cadence: at every gate**, plus whenever a trigger fires or a client answer lands
>   (`16` §5.1, `21` §5.1).
> - **Scores can fall**: a mitigation that is implemented and tested closes the risk with a date and the
>   evidence, kept in the register as history.
> - **The register is small on purpose** — 36 rows; a risk that cannot change a decision is deleted, not
>   annotated.
> - **Nothing here replaces `27`**: unknowns that are work become backlog entries with triggers; the
>   register keeps what could hurt the engagement.
> - **No product code exists yet**; this register is reviewed at `GATE-01`…`GATE-05` before any build.

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

## 2. The register (36 risks)

| ID | Risk (cause → effect) | Cat | L | I | Exp | Mitigation in force | Early-warning trigger | Owner | Links |
|---|---|---|---|---|---|---|---|---|---|
| `RISK-001` | Messy real files (headers, encodings, accounting formats, merged cells) → the importer fails or silently mis-reads on the client's own exports | Data | 4 | 5 | 20 | `04` §7–§9 hardening rules (32 checks, handle-or-reject); 16-file malformed corpus in `14` §16; quarantine instead of drop; dry-run validate | First real file after go-live produces a check failure or a quarantine rate above the pilot's | Engineering | `04`, `14` §16, `IMP-*` |
| `RISK-002` | The sanitized real month never arrives (`Q-001`/`A29`) → the pilot and UAT cannot run on real shape | Client | 3 | 5 | 15 | Sample-data corpus is the testbed; the pilot gate (`GATE-13`) is explicitly dependent; the ask is first in the `21` §2.3 order | The needed-by date passes with no file | Project owner | `Q-001`, `A29`, `28` |
| `RISK-003` | Unsigned installer is blocked by SmartScreen/Defender → the client cannot install | Delivery | 4 | 4 | 16 | `ADR-003` mitigation ladder; verbatim non-technical walkthrough (`15` §8.3); SHA-256 verification; portable fallback (`15` §4.3); `SPK-01`/`SPK-02` spike | A client install attempt shows a dialog beyond the documented ones, or Defender quarantines the build | Engineering | `ADR-003`, `15` §8, `Q-015` |
| `RISK-004` | Rule precision disappoints (too many false positives or a visible miss) → the register is ignored | Quality | 4 | 4 | 16 | Precision targets (`06` §8.3), 8 precision plantings, effectiveness analytics (`06` §9), tuning via Settings with before/after counts | Precision below the target in the acceptance harness or ≥ 3 client complaints about the same rule | Engineering | `06` §8–§9 |
| `RISK-005` | The app's numbers differ from the client's manual pack → trust collapse at UAT | Quality | 3 | 5 | 15 | Real-data pilot tie-out with difference classification (`28`); drill-through to source lines; exact-Decimal money; round-trip fixtures | Any unexplained difference at the pilot tie-out | Engineering | `01` R5, `28` |
| `RISK-006` | Real volumes exceed the NFR envelope → unusable performance | Performance | 3 | 4 | 12 | `NFR-002`/`009` targets with baselines; `--scale 250000` perf suite; measurement at the pilot; 20 % regression block | Pilot measurement misses a baseline, or the client reports files "much bigger this month" | Engineering | `14` §3/§8, `09` §14 |
| `RISK-007` | Scope pressure at a gate pushes P1/P2 work into P0 time → a gate slips or quality drops | Scope | 4 | 3 | 12 | Cut-line policy and the **never-cut list** (`02` §3.3/§3.4, `16` §9); every cut is a recorded decision + `27` entry | A gate packet contains an undocumented scope change, or two consecutive gates use cut time | Project owner | `02` §3, `16` §9 |
| `RISK-008` | Windows-only evidence gap (dev environment is not Windows) → delivery fails on the client's machine | Delivery | 3 | 5 | 15 | `ADR-005`: real-Windows validation at every gate; 24-step clean-machine protocol (`15` §5.2); signed run sheets | A gate runs without a clean-Windows sheet, or a defect appears only on the client machine | Engineering | `ADR-005`, `15` §5 |
| `RISK-009` | Project lives in a synced folder (OneDrive/SharePoint) → database corruption or locks | Data | 3 | 5 | 15 | `%LOCALAPPDATA%` default (`ADR-004`); sync-folder tests (`TST-WIN-06`); a warning if the user chooses a synced folder | `doctor` reports a synced data folder, or cards on file locks | Engineering | `ADR-004`, `13` §4 |
| `RISK-010` | AI output drifts from engine numbers, or a payload leaks data → credibility/confidentiality damage | AI | 3 | 4 | 12 | AI never computes numbers (`10` §2); schema-validated outputs; redaction; caps; keyless default; usage log with prompt version | A draft contradicts a stored number, or a review finds a value that should have been redacted | Engineering | `10` §2/§6/§8, `13` §8 |
| `RISK-011` | Key-person dependency (one engineer) → delivery stalls if unavailable | Delivery | 3 | 4 | 12 | `23` written from Phase 1 (not at the end); demo scripts as knowledge transfer; trunk-based repo always buildable; fresh-clone test | More than one session lost to a single person's unavailability | Project owner | `16` §12, `23` |
| `RISK-012` | UAT participants unavailable at the planned time → go-live slips | Client | 3 | 3 | 9 | `28` names participants and a fallback week; UAT scripts runnable by one person (`14` §12.4) | The UAT window is confirmed with fewer than the required roles | Project owner | `A26`, `28` |
| `RISK-013` | Coverage or performance regresses unnoticed → a gate passes on weaker evidence | Quality | 3 | 3 | 9 | Coverage bars (engine ≥ 90 %, app ≥ 75 %); perf baselines; > 20 % regression blocks; waiver requires explicit approval | A coverage drop > 2 points with no explanation, or a baseline missing at a gate | Engineering | `14` §8.3/§13.2 |
| `RISK-014` | A document contradiction is found late → rework and a stale decision trail | Process | 3 | 3 | 9 | `00_INDEX` conflict rule; every doc has an owner; change order (`19` §5.1); `CHANGELOG` records corrections | The same fact is stated two ways in two docs, or a correction touches more than two docs | Doc owner | `00_INDEX` §6, `19` §5 |
| `RISK-015` | Master data (vendor categories, recurring costs, thresholds) is missing or stale → dependent rules degrade or fire wrongly | Data | 4 | 3 | 12 | Rules auto-disable with a visible notice (`FR-EXC-014`); master-data screens (`SCR-034`); the `Q-010`/`Q-011` asks are in the phase-3 set | A rule is disabled for two consecutive months, or the client reports repeated false positives from stale data | Client finance owner | `06` §2.9/§4, `Q-010`, `Q-011` |
| `RISK-016` | No signing certificate is procured in time (`OQ-012`) → the launch experience stays the unsigned one | Delivery | 4 | 2 | 8 | Default is a fully documented unsigned path with SHA-256 verification; signing checklist ready (`15` §8.5) | The install-day plan assumes signing, or the certificate budget is declined | Project owner | `OQ-012`, `A14`, `ADR-003` |
| `RISK-017` | The delivery channel cannot carry the ~500 MB installer + checksum (`Q-016`/`A23`) → distribution improvising at go-live | Delivery | 3 | 3 | 9 | Chunked delivery fallback; published SHA-256; portable zip as the alternative artefact | A test upload to the agreed channel fails or is blocked by policy | Project owner | `Q-016`, `A23`, `24` §7 |
| `RISK-018` | Client IT is unavailable on install day (`A24`) → install stalls on a SmartScreen prompt | Client | 3 | 2 | 6 | The written walkthrough stands alone (`15` §8.3); remote assistance offered; portable fallback | The install is scheduled without a named IT contact | Project owner | `A24`, `22` §2.1 |
| `RISK-019` | The performance reference machine is not representative (`A22`) → baselines look better than the client's reality | Performance | 2 | 3 | 6 | Baselines re-recorded on the client's machine at the pilot; comparisons annotated when the machine differs | Pilot runs on a machine outside the reference class | Engineering | `A22`, `14` §3 |
| `RISK-020` | A new security/privacy/compliance requirement emerges (`A28`) → design rework late | Compliance | 2 | 4 | 8 | The compliance stance is written and testable (`13`, 49 statements); a new requirement is a blocking question, not a silent change | A client questionnaire, IT policy or auditor asks for something outside `13` | Project owner | `A28`, `13` §1 |
| `RISK-021` | The client's current Excel/PPT samples never arrive (`Q-012`) → house-style matching happens blind and rework lands at UAT | Client | 3 | 3 | 9 | Default house style is complete and documented (`11`/`12`); house-style matching is a documented, bounded procedure (`11` §9) | UAT feedback is dominated by layout rather than numbers | Project owner | `Q-012`, `OQ-010`/`OQ-021` |
| `RISK-022` | Branding assets arrive late (`Q-019`) → deck/Excel branding rework after UAT | Client | 3 | 2 | 6 | Placeholder branding ships; brand settings are data (`SCR-037`) with a contrast guard; re-branding is a settings change, not code | Branding requested after the UAT build is frozen | Project owner | `Q-019`, `FR-SET-008` |
| `RISK-023` | Retention/deletion expectations differ from the design (`Q-020`) → a policy surprise after go-live | Client | 2 | 3 | 6 | Projects are local and user-deleted with typed confirmation and an offered pre-delete backup; retention is documented as user-owned (`13` §10.2) | The client asks for automatic purge or "secure erase" (parked, `BL-030`/`BL-032`) | Project owner | `Q-020`, `13` §10.2 |
| `RISK-024` | Headcount metrics are requested late (`Q-021`) → a parked scope re-opens mid-phase | Scope | 2 | 3 | 6 | The park is explicit (`BL-016`, no schema support); the question is asked before go-live so the answer is known early | A late request for cost-per-head in the pack | Project owner | `Q-021`, `BL-016` |
| `RISK-025` | Forecast accuracy expectations are unmet → the forecast is distrusted | Quality | 3 | 3 | 9 | Accuracy reporting per closed period (`07` §8.1); method guidance; scenarios; overrides with reasons; integrity guarantees (`07` §10) | The first accuracy report shows errors the client considers unacceptable, with no method alternative offered | Engineering | `07` §8, `16` §12 |
| `RISK-026` | Deck fidelity (fonts, chart styling, native waterfall) cannot be reproduced → layout rework | Delivery | 2 | 3 | 6 | `SPK-03`/`SPK-08` spikes before Phase 5 deck code; native-editable contract (`12` §3.2); documented "cannot match" list (`11` §9.2) | A spike shows the required chart or font cannot be produced, or the client template is unsupported | Engineering | `SPK-03`/`SPK-08`, `12` §11 |
| `RISK-027` | The client expects charts inside the Excel pack (`BL-026` is parked) → a pack that looks emptier than the manual one | Delivery | 3 | 2 | 6 | The pack's conditional formatting and bridge sheet are documented; the park is explicit and revisitable via `27` | The client asks for Excel charts during UAT or immediately after | Project owner | `BL-026`, `11` §14 |
| `RISK-028` | WebView2/DPI/printing issues in the packaged build → visual or print defects | Delivery | 2 | 3 | 6 | `SPK-04` spike; `doctor` reports WebView2; fallback path; print/PDF readiness tested per sheet (`11` §10) | A packaged-build check (150 % DPI, print preview, clipboard) fails | Engineering | `SPK-04`, `15` §6.3 |
| `RISK-029` | Antivirus quarantine or corporate policy blocks the build → install failure on the client's estate | Delivery | 3 | 3 | 9 | `SPK-02` spike; mitigation ladder; portable package; hash verification | Defender/policy quarantine observed at any client site | Engineering | `SPK-02`, `15` §8.4 |
| `RISK-030` | Backup/encryption expectations exceed the design (plain-zip backups, no secure erase) → a perceived security gap | Security | 2 | 3 | 6 | The plain-zip warning is shown in the UI (`13` §9.2); parked items have explicit triggers (`BL-030`/`BL-031`); BitLocker is the recommended control | The client's IT requires encrypted backups or attested erasure | Project owner | `BL-030`/`BL-031`, `13` §9 |
| `RISK-031` | Hostile input (prompt injection in a description field) influences an AI draft → wrong or unsafe commentary | AI | 2 | 3 | 6 | `13` §11 rule on instruction-bearing content; output validation; drafts are labelled and require approval; AI never acts | A draft contains instructions or content that did not come from the data | Engineering | `13` §11, `10` §7 |
| `RISK-032` | Support capacity after handover (one consultant, no ticket system) → slow response during month-end | Operations | 3 | 3 | 9 | The zip-only diagnostics path (`13` §7), the incident playbook (`23` §10), escalation ladder (`15` §9.3) and the month-end freeze windows (`16` §8.3) | Two incidents in the same month-end week both breach the response targets | Consultant | `23` §10/§11 |
| `RISK-033` | The upgrade fixture is unrepresentative → a migration surprise on a real project | Delivery | 2 | 4 | 8 | The fixture is a real project from the previous released build (`24` §6.3); `TST-E2E-05` hash-compares numbers | A migration behaves differently on a client project than on the fixture | Engineering | `24` §6, `TST-E2E-05` |
| `RISK-034` | The trained analyst leaves or changes role → knowledge loss at the client | Client | 3 | 3 | 9 | Written guide (`22`) with a first-hour checklist and training outline; recorded demo; help panel single-sourced with the guide; every task is doable without the author present (`TST-UAT-04`/`05`) | The primary user changes before go-live, or training is skipped | Project owner | `22` §10, `Q-017` |
| `RISK-035` | Single-user design conflicts with how the team shares work (`01` R10) → shadow copies and reconciliation | Product | 2 | 3 | 6 | Explicit single-user decision (`01` §10); backup/restore as the transfer path; the park is revisited post-pilot | Two people need the same project at the same time more than once | Project owner | `01` §10, `BL-004`/`BL-005` |
| `RISK-036` | The client expects the tool to email packs to recipients (`OQ-011`) → a scope surprise at UAT or an expectation of a send path the product does not have | Product | 3 | 2 | 6 | No send path by design (`13` §1); recipients are typed per issue in the issuance register (`FR-XC-003`); the manual hand-off is described in `22` (`FR-XC-014`); the answer is asked before go-live | The client asks, at UAT or go-live, for the pack to be emailed automatically | Project owner | `OQ-011`, `13` §1, `FR-XC-003` |

## 3. Top-ten detail sheets

### 3.1 `RISK-001` — real files break the importer (Exposure 20)

| Aspect | Detail |
|---|---|
| Cause chain | Client exports vary by month (headers renamed, extra columns, localised numbers, merged cells, `.xlsm`/protected sheets) → a mapping or parse rule that passed on sample data fails on the client's file |
| Why it matters | The import is the front door; a failure here stops the whole month-end, and a silent mis-read is worse than a stop |
| Mitigation in force | Handle-or-reject catalogue (`04` §8/§9); every quirk has a named error and a hint; quarantine keeps unusable rows visible; validate-without-commit (`04` §3 step 5); mapping profiles are versioned so a new shape is an added profile, not a code change (`FR-IMP-026`) |
| Contingency if it fires | Capture the file, add the shape to the malformed corpus (`14` §16), fix the rule, add the regression test; the client imports via the corrected profile in the same session where possible |
| Residual risk | A brand-new quirk at go-live costs a day; mitigated by the dry-run and the profile mechanism |
| Evidence | `IMP-001`…`032` checks, 59 error slugs, corpus tests `TST-IMP-*` |

### 3.2 `RISK-002` — the real month never arrives (Exposure 15)

| Aspect | Detail |
|---|---|
| Cause chain | The client cannot sanitise or release one month's exports → the pilot (`GATE-13`) and the real-data tie-out cannot run |
| Why it matters | Without it, UAT runs on sample data and the numbers-vs-manual-pack risk (`RISK-005`) is unmeasured until after go-live |
| Mitigation in force | The ask is first in `21` §2.3's impact order; the sample corpus keeps development moving; the pilot gate is explicitly conditional |
| Contingency if it fires | Run UAT on sample data with a written limitation note; schedule the tie-out as the first post-go-live activity; keep `RISK-005` at `Monitoring` until the tie-out happens |
| Residual risk | A shape surprise discovered after go-live; covered by the profile mechanism and the corpus rule |
| Evidence | `Q-001`, `A29`, `28`'s pilot section |

### 3.3 `RISK-003` — SmartScreen/Defender blocks the installer (Exposure 16)

| Aspect | Detail |
|---|---|
| Cause chain | The v1 build is unsigned (`ADR-003`) → Windows shows the "protected your PC" box; some browser/Defender policies refuse the file outright |
| Why it matters | A blocked installer is a launch blocker and a first-impression failure with a non-technical user |
| Mitigation in force | Documented mitigation ladder (`15` §8.2); verbatim non-technical walkthrough (`15` §8.3) reused in `22`/`29`; SHA-256 published and verifiable; portable package fallback; `SPK-01`/`SPK-02` spike run before installer work |
| Contingency if it fires | Walk through the ladder live; if policy blocks both artefacts, escalate to client IT with the hash and the signed run sheet; a certificate (`Q-015`) becomes an immediate commercial decision |
| Residual risk | Client-IT policy may forbid unsigned binaries entirely; that would force the certificate path |
| Evidence | `ADR-003`, `15` §8, `TST-SEC-19` copy audit on the walkthrough |

### 3.4 `RISK-004` — rule precision disappoints (Exposure 16)

| Aspect | Detail |
|---|---|
| Cause chain | 24 rules on real data raise too much noise (or miss something obvious) → the register loses credibility and gets ignored |
| Why it matters | The exception engine is a headline feature; trust is binary and hard to rebuild |
| Mitigation in force | Recall **≥ 90 % of the 32 expected raises** including **18/18 High-severity** plantings, with **zero** raises on the **8 control plantings** (`06` §7.1/§7.2, `06` §8.3); effective-threshold traceability on every raise; effectiveness analytics (`06` §9); suppression mechanics ordered by preference (`06` §8.2) |
| Contingency if it fires | Tune the rule in `06` first (spec → defaults → tests), then settings; never hide a rule to pass a bar; report precision before/after to the client |
| Residual risk | Some client data will always produce judgement calls; the wording ("potential exception") keeps the frame honest |
| Evidence | Acceptance harness report, false-positive log, `TST-RUL-*` |

### 3.5 `RISK-005` — numbers differ from the manual pack (Exposure 15)

| Aspect | Detail |
|---|---|
| Cause chain | Mapping, period assignment, sign conventions or rounding presentation differ from the client's current spreadsheet → a number mismatch at UAT |
| Why it matters | A single unexplained difference can discredit the whole tool |
| Mitigation in force | Real-data pilot tie-out with difference classification (`28`); drill-through to source lines; exact-Decimal money with display-only rounding; golden fixtures (`05` §12); cross-artifact equality test (`NFR-015`) |
| Contingency if it fires | Classify the difference (spec bug / mapping / genuine client error), fix the owner, re-run the tie-out; if the client's sheet is wrong, show the drill-through, not an argument |
| Residual risk | Legitimate methodology differences (timing, allocation) may remain; they are documented, not hidden |
| Evidence | `TST-UAT-01`/`02`, `TST-CALC-*`, F1–F14 fixtures |

### 3.6 `RISK-006` — performance misses the envelope (Exposure 12)

| Aspect | Detail |
|---|---|
| Cause chain | A 250k-row month with wide dimension sets, on a 4-core/16 GB machine, exceeds the import/UI budgets |
| Why it matters | The monthly rhythm's value is speed; a slow tool is abandoned |
| Mitigation in force | Canonical NFRs with measurement methods and fixtures (`14` §3); scale mode; architecture budgets (`09` §14); lazy/streaming processing; baselines re-measured at every gate |
| Contingency if it fires | Profile before optimising; partition/column-prune; if a bar cannot be met, re-scope with the client and record it — never redefine the NFR silently |
| Residual risk | Client hardware below the reference class is covered by `A22`/`RISK-019` |
| Evidence | `TST-PRF-01`…`TST-PRF-16`, baselines under `tests/perf/baselines/` |

### 3.7 `RISK-007` — scope pressure at a gate (Exposure 12)

| Aspect | Detail |
|---|---|
| Cause chain | Good ideas arrive mid-phase; the sprint-like push to close a gate tempts silent scope changes |
| Why it matters | The prior prototypes failed on scope sprawl (`01` §2.4, R3) |
| Mitigation in force | Cut-line policy with approval (`02` §3.4); never-cut list (`02` §3.3, `16` §9.2); every deferral becomes a `27` entry with a trigger; gate item 12 checks for silent scope change |
| Contingency if it fires | Stop, write the impact note (`Addon 4 §E.3`), decide cut-or-defer with the owner, record it; the gate does not pass on an undocumented change |
| Residual risk | Commercial pressure near go-live; the never-cut list is the hard floor |
| Evidence | Gate checklists, `CHANGELOG` scope rows, `27` |

### 3.8 `RISK-008` — Windows-only evidence gap (Exposure 15)

| Aspect | Detail |
|---|---|
| Cause chain | Development and CI are not the client's environment; installer, DPI, printing and Defender behaviour differ |
| Why it matters | The deliverable is a Windows desktop app; "works on the dev box" is not evidence (`ADR-005`) |
| Mitigation in force | Real-Windows validation at every gate (`15` §5.2 protocol); packaging spike first; `doctor` command; signed run sheets with screenshots |
| Contingency if it fires | Stop the gate; reproduce on the clean machine; fix and re-run the affected protocol steps; no waivers on Windows evidence |
| Residual risk | Client-specific Group Policy differences surface only at their site; the fallback paths exist |
| Evidence | Clean-Windows run sheets, `TST-WIN-01`…`TST-WIN-14` |

### 3.9 `RISK-009` — synced-folder corruption (Exposure 15)

| Aspect | Detail |
|---|---|
| Cause chain | A user moves the data folder into OneDrive/SharePoint → live databases get synced/locked and corrupt |
| Why it matters | Silent corruption is the worst outcome for a finance tool |
| Mitigation in force | `%LOCALAPPDATA%` default with `ADR-004`; project creation is blocked on a synced path with the documented message and export warns (`TST-WIN-06`); `doctor` reports the folder; backups are snapshots and are allowed in synced folders with a warning (`13` §9.2) |
| Contingency if it fires | Stop writes, copy the project, restore the last good backup, move the folder local; add the incident to `23` §10 |
| Residual risk | A user can still ignore the warning; backups and the integrity check limit the damage |
| Evidence | `TST-WIN-06`, `ADR-004`, `doctor` output |

### 3.10 `RISK-010` — AI drift or leakage (Exposure 12)

| Aspect | Detail |
|---|---|
| Cause chain | A model drafts commentary that contradicts the numbers, or a payload includes data that should have been redacted |
| Why it matters | Either one destroys credibility or confidentiality — the two things the client cares about most |
| Mitigation in force | AI never computes or decides (`10` §2); outputs schema-validated and number-checked; redaction rules (`10` §6); caps; keyless default; usage log with prompt version; drafts labelled and human-approved |
| Contingency if it fires | Disable the feature in Settings (keyless mode), regenerate the affected commentary by hand, fix the prompt/redaction, re-run the AI eval fixtures, record the incident |
| Residual risk | Provider-side model changes; handled by model pinning and the keyless fallback (`10` §10/§11) |
| Evidence | `TST-AI-01`…`TST-AI-14`, redaction tests, eval fixtures |

## 4. Client-fact and open-question risks (from `21`)

| Client fact (join of record: `20` §6.1) | `OQ-` | `Q-` | Risk | Consequence if unanswered |
|---|---|---|---|---|
| D365 edition / export column set | `OQ-001` | `Q-002` | `RISK-001` | Handled-or-rejected per `04` §8; a new quirk becomes a profile, not a mis-read |
| The two other systems' column lists | `OQ-002` | `Q-003` | `RISK-001` | Two shapes are already modelled (`04` §2) |
| Fiscal calendar | `OQ-003` | `Q-004` | `RISK-005` | Configurable periods (`FR-SET-005`); wrong periods would mis-date MTD/YTD |
| Prior-year data availability | `OQ-004` | `Q-005` | `RISK-005` | PY views are built and hidden with a note when no PY batch exists (`02` §16 E1) |
| Single vs multiple currency | `OQ-005` | `Q-006` | `RISK-001`, `RISK-005` | Single reporting currency; mixed-currency rows quarantine (`02` §16 E10) |
| Budget versions and revisions | `OQ-006` | `Q-007` | `RISK-005` | One version per period; a re-import replaces atomically (`04` §14) |
| Approval thresholds | `OQ-007` | `Q-009` | `RISK-015`, `RISK-004` | Global materiality default (`05` §11); rules stay configurable |
| Recurring-cost list | `OQ-008` | `Q-010` | `RISK-015` | The rule auto-disables with a visible notice (`06` §4 `EXC-015`) |
| Vendor master and categories | `OQ-009` | `Q-011` | `RISK-015` | Category rules auto-disable; owner assignment falls back to manual (`03` §5.6) |
| Current Excel/PPT outputs | `OQ-010`, `OQ-021` | `Q-012` | `RISK-021` | Documented default house style; matching is a bounded procedure (`11` §9) |
| Pack recipients | `OQ-011` | `Q-013` | `RISK-036` | Recipients typed per issue; no send path exists by design (`13` §1) |
| Code-signing certificate | `OQ-012` | `Q-015` | `RISK-003`, `RISK-016` | Unsigned v1 + documented SmartScreen path (`ADR-003`) |
| Real file sizes seen in practice | `OQ-013` | `Q-014` | `RISK-006`, `RISK-019` | Limits per `NFR-002` with explicit over-limit confirmation |
| One sanitized real month | `OQ-014` | `Q-001` | `RISK-002` | **No default exists** — the pilot gate (`GATE-13`) depends on it |
| Logo and brand colours | `OQ-015` | `Q-019` | `RISK-022` | Placeholder branding is settings-driven; re-branding is a data change |
| Support/warranty terms | `OQ-016` | `Q-018` | `RISK-032` | Support flow documented in `23`; response targets are labelled defaults |
| Installer delivery channel | `OQ-017` | `Q-016` | `RISK-017` | Manual download with published SHA-256; update check off by default |
| Preferred default units | `OQ-022` | `Q-006` | `RISK-005` | Whole rupees with the unit label always shown (`05` §6.3) |

> `OQ-014` is the only question in the set with **no labelled default** — it is a schedule dependency
> (`18`), owned by `28`'s pilot section and carried here by `RISK-002` alone.

## 5. Deliberate acceptances (written down, with reopen triggers)

| Accepted | Why it is acceptable | Reopen trigger |
|---|---|---|
| Unsigned v1 installer | The mitigation ladder + hash verification are documented and tested; signing is a commercial decision (`OQ-012`) | A client policy blocks unsigned binaries, or the certificate is procured |
| No login, no RBAC (`DEC-010`) | Single-user local tool; a permission model adds cost with no benefit | The product gains a shared/server mode (`BL-035`) |
| Plain-zip backups, no encryption | A non-technical user must be able to restore; the warning is explicit; BitLocker is the right control | Client IT requires encrypted backups (`BL-031`) |
| No secure erase | SSD wear-levelling makes app-level shredding a false promise | Client policy demands attested erasure (`BL-030`) |
| Sample data never delivered to the client | Delivery hygiene and contamination safety (`FR-XC-013`) | Never — this is policy, not a trade-off |
| AI off by default, keyless | Data-leak and support risk; the rule-based path is complete without it | The client asks for AI and accepts the key handling |
| No in-app PDF rendering (`DEC-028`) | Print/PDF readiness is tested; a renderer adds size and failure modes | A client workflow requires PDFs without Excel |
| P&L focus only | The stated job; balance-sheet scope is a different product | Scope change approved through the cut-line process |

## 6. Sources, review protocol and closure

### 6.1 Where risks come from (and go)

| Source | How it enters |
|---|---|
| `01` §13 (R1–R10) | Seeded here in full — R1→`RISK-003`, R2→`RISK-001`, R3→`RISK-007`, R4→`RISK-004`/`RISK-005` (advisory wording, `01` §15.1), R5→`RISK-005`, R6→`RISK-009`, R7→`RISK-008`, R8→`RISK-010`, R9→`RISK-006`, R10→`RISK-035` |
| `16` §12 (roadmap risks) | Seeded here in full — rows 1–10 → `RISK-002`, `RISK-003`, `RISK-006`, `RISK-004`, `RISK-010`, `RISK-007`, `RISK-013`, `RISK-014`, `RISK-011`, `RISK-012` in row order; `16` keeps the roadmap view and points back here |
| Spike findings (`SPK-01`…`08`) | A spike result becomes a risk row, an ADR, or a `27` entry |
| Parked items (`13` §15, `BL-*`) | A park with a real downside gets a row with the same trigger |
| Client answers (`21` §5.1) | Answered questions re-score or close rows; unanswered ones keep their dates |
| Incidents (`23` §10/§11) | Every S1/S2 incident adds or re-scores a row, and a materialised risk is converted to a defect |
| Test counter-evidence | A failing or flaky check that was assumed safe becomes a row |

### 6.2 Review protocol (the gate ritual)

1. **At every gate** (`16` §5.1): re-score the open and monitoring rows; close what has evidence; add what
   the phase revealed; list any row whose trigger fired since the last gate.
2. **A score of 20+ with impact 5** is told to the project owner the day it is scored, with the contingency.
3. **Closures need evidence**: a row moves to `Closed <date>` only with the artefact that shows the
   mitigation worked (a test, a spike output, a client confirmation).
4. **No silent deletions**: a row removed for being irrelevant is recorded as `Closed — not applicable`
   with one line of reasoning.
5. **The register never becomes a diary**: rows that cannot change a decision are closed or converted to
   `27` entries.

### 6.3 Current summary (at the time of writing)

| Band | Count | IDs |
|---|---|---|
| High (15–20) | 7 | `RISK-001`–`RISK-005`, `RISK-008`, `RISK-009` |
| Medium (6–12) | 29 | `RISK-006`, `RISK-007`, `RISK-010`–`RISK-036` |
| Low (1–5) | 0 | — |
| **Open total** | **36** | `RISK-001`–`RISK-036` |
| Closed | 0 | — |

> **Note:** the counts are by score at first issue; the register is re-scored at `GATE-01` and these counts
> are updated there (the only place in the Phase-0 set where a count is expected to change before approval).

## 7. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `01` | §13's R1–R10 stay the product-level summary; this register is the operational detail |
| `16` | §12 keeps the roadmap contingency view; a change there is mirrored here in the same pass |
| `21` | Registers the questions; this document registers the consequences of unanswered ones |
| `20` | §6.1 stays the question ↔ FR join; §4 above is the question ↔ risk join and never restates the FR list |
| `23` | Converts materialised risks into incident entries and feeds new rows back here |
| `24` | Reads §5's acceptances when a release changes a mitigation (e.g. signing) |
| `28` | Uses §3's tie-out and UAT contingencies in the pilot/UAT plan |
| `27` | Receives anything from §5 that reopens as work, with a trigger |

## 8. Change control for this document

1. **Adding a risk** requires a trigger, an owner and a linked mitigation doc — otherwise it is a note, not
   a risk.
2. **Re-scoring** is a change with a reason line (`CHANGELOG` + the row's status history in this file).
3. **Closing** requires the evidence artefact; the row stays visible with its closure date.
4. **The scale (§1.1) does not drift**: new anchors are added only if a real case shows a gap, and the
   change is recorded.

## 9. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| ID format | `RISK-nnn`, allocated here, never reused | `00_INDEX` §8 |
| Scoring | Likelihood 1–5 × Impact 1–5; bands 1–5 / 6–12 / 15–25 | §1.1 |
| Row contract | Cause → effect, mitigation, trigger, owner, link, status | §1.2 |
| `RISK-003` | SmartScreen/Defender blocked installer | `ADR-003`, §3.3 |
| Top sheets | `RISK-001`…`RISK-010` | §3 |
| Gate review | Every gate, re-scored, evidence-based closure | §6.2, `16` §5.1 |
| Acceptances | Eight deliberate acceptances, each with a reopen trigger | §5 |
| Sources | `01` §13, `16` §12, spikes, parks, answers, incidents, tests | §6.1 |
| Client-fact join | `20` §6.1 is the join of record | §4 |
