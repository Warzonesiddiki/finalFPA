> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **consultant-facing runbook** — rebuild the environment, ship a release, edit
> configuration/prompts/rules with the client, update dependencies, run the diagnostics workflow, and
> escalate support (Addon 1 §C.1/§I/§K, Addon 2 §H.2, Addon 4 §I.2; `Q-018`)
> **TL;DR (≤ 15 lines):**
> - This is the **successor's document**: someone who has never seen the project can rebuild it, ship a
>   release and support the client using only this file plus the docs it points to.
> - **Three loops:** the **dev loop** (`uv sync` → `npm ci` → run → `scripts/check`), the **release loop**
>   (`scripts/build` per `15` §3.2 → checksums → smoke test → evidence) and the **recovery loop**
>   (diagnostics zip → triage → restore/rollback).
> - **The build is owned by `15`**; this document is the operator's checklist — it never restates build
>   steps, it says when to run them and what evidence to keep.
> - **Everything client-facing that can be edited** is listed in §4: display, thresholds, master data,
>   mappings, branding, AI key. Each edit is versioned, reversible and has a traceability rule.
> - **Prompts are code** (`10` §4): a shipped version is immutable; an edit creates `v<N+1>`, updates
>   `10` §5, adds a `CHANGELOG` entry and re-runs the AI eval fixtures.
> - **Rules are tuned, never patched into data** (`06` §2.10/§10): thresholds change through Settings, and
>   every raise keeps the effective threshold that was used.
> - **Dependencies move on a schedule**, not on impulse: monthly audit, license allow-list, SBOM refresh;
>   a new dependency is an ADR (`09` `ADR-002`).
> - **Support runs on the diagnostics zip** — logs and settings, redacted by construction, no project data
>   and no key (`13` §7). The user never sends their project.
> - **Escalation is written, not remembered:** every incident gets an entry with a code, a cause, a fix and
>   whether a test now covers it.
> - **Never ask the client for a password, a key, or their whole project folder** (`15` §9.4).
> - Support/warranty **terms** are commercial (`OQ-016`); §11's response targets are the labelled defaults
>   in force until they are agreed.
> - **Handover pack** (§12) lists exactly what the client receives and what stays with the consultant.
> - **A successor is trained by doing §2 on their own machine** — that is the handover acceptance test.
> - **Nothing in this document replaces `15`/`24`**: when they change, this checklist is updated in the
>   same pass (it cites, it does not copy).
> - **No product code exists yet**; this runbook is written now so the first code session inherits it
>   (`19` §2, Addon 4 §L.12).

# 23 — Consultant Handover and Support

## 1. Purpose, audience and what this document owns

| Item | Detail |
|---|---|
| Reader | The consultant/support engineer who inherits the product, and the developer who rebuilds it |
| Owns | The rebuild runbook, the operator's release checklist, the configuration/prompt/rule edit procedures, the dependency cadence, the diagnostics workflow, the incident playbook, the support/handover contracts |
| Does not own | The build steps (`15` §3), release versioning/tagging (`24`), the support/warranty **terms** (`OQ-016`, `28`), the test suite (`14`), the code standards (`17`) |
| Success test | A successor rebuilds, releases and supports from this document plus `15`/`24`, with no undocumented step |

## 2. The dev loop: rebuild and run from a fresh clone

### 2.1 Preconditions (verify, do not assume)

| Check | Expected | Command / where |
|---|---|---|
| OS | Windows 11 x64 for anything release-related; other OSes only for docs and unit work | `winver` |
| Python | The pinned version from `09` `ADR-002` | `python --version` |
| Node | The pinned version from `09` `ADR-002` | `node --version` |
| Tooling | `uv`, `npm`, Inno Setup 6 (release only), Git | `uv --version`, `npm --version` |
| Disk | ~5 GB free (toolchain + build) | Explorer |

### 2.2 The fresh-clone bootstrap (Addon 4 §I.2) — the acceptance test for a new machine

```
git clone <repo> && cd <repo>
uv sync --frozen            # Python env from uv.lock — never install by hand
npm ci                      # UI deps from package-lock.json — never npm install
python -m app.cli doctor    # environment health (WebView2, permissions, disk)
scripts/check               # the gate command: format, lint, types, imports,
                            # tests, coverage, UI types, secret/license/docs checks
```

**Every command above must pass before the first commit of a session.** `scripts/check --fast` skips
coverage and the docs link-check for the inner loop; gate and release runs use the full form (`14` §13.1).
A fresh clone that cannot pass this sequence is a **P0 defect**, not a setup problem.

### 2.3 Running it locally, and driving it headlessly

| Need | How |
|---|---|
| Run the app (dev) | Start the API (loopback, random port, per-launch token — `ADR-009`) and the Vite dev server; the packaged app is what the client sees, so anything visual is verified in the packaged build too |
| Reproduce a client issue without their data | `python -m app.cli <command> --project <path>` — `import`, `validate`, `bva`, `exceptions`, `forecast`, `export-xlsx`, `export-ppt`, `doctor`, `migrate`, `report` (`09` §5.2) |
| Inspect a project safely | Work on a **restored copy** (T-19 in `22`), never the client's live project |
| Environment triage | `python -m app.cli doctor --json` — DB integrity, disk, schema compatibility, WebView2, permissions, profile versions |

## 3. The release loop (the operator's checklist)

`15` owns the build; `24` owns versioning, tags and distribution. This is the order the operator runs them
in, with the evidence each step must leave behind.

| # | Step | Evidence to keep |
|---|---|---|
| 1 | Confirm the gate conditions for this release (`16` §5.1: green `scripts/check`, coverage bars, NFR baselines, cross-artefact test, clean-Windows run, demo script) | Gate transcript attached to the phase record |
| 2 | Set the version in **one** place (`15` §2.2) — app, schema and docs stamps derive from it | The version commit |
| 3 | Run `scripts/build` (`15` §3.2: UI build → PyInstaller onedir → payload staging → **payload audit** → Inno Setup → portable zip → checksums → smoke test → size/time report) | Build report, size vs `NFR-006` |
| 4 | Run the **clean-Windows 11 protocol** (`15` §5.2, 24 steps) on a machine that never saw the app | Signed run sheet + screenshots (SmartScreen, first run, sample project, one pack) |
| 5 | Compute and publish `SHA256SUMS-<version>.txt`; attach the SBOM snapshot | Checksums + SBOM in the release record |
| 6 | Write the release notes (what changed, what to re-test, any behaviour change) | `CHANGELOG` entry + release notes |
| 7 | Tag and publish per `24`; deliver through the **agreed channel** (`Q-016`) | Tag, publication record, delivery confirmation |
| 8 | Record the approval in `CHANGELOG` **and** `SESSION_LOG` (`19` §6) | `Phase <n> gate APPROVED — <who> — <date>` |

> **Never ship a build that has not been installed on a clean machine.** "It runs on the dev box" is not
> evidence (`ADR-005`). The packaging spike (`SPK-01`/`SPK-02`) exists precisely because this is where
> launches fail (`09` §15.1).

## 4. Editing configuration with the client

| What | Screen | Who decides | Procedure | Traceability |
|---|---|---|---|---|
| Currency label, units, decimals, negatives | `SCR-036` | Client finance owner | Change in Settings; ask the client to check one known number afterwards | Settings history; display-only, no data change |
| Thresholds, rule on/off, severity | `SCR-035` | Client finance owner | Change one rule at a time; re-run rules; compare the exception count before/after and state the change to the client | Versioned with history and revert; every raise records the effective threshold |
| Master data (vendor categories, recurring costs, approval thresholds, owners) | `SCR-034` | Client finance owner/analyst | Import or edit; rules that depend on missing data relax with a visible notice until loaded | Rows carry the source; changes are auditable |
| Mapping profiles | `SCR-033` | Consultant/analyst | Add or version a profile; **never edit a shipped version in place** | Profile versions with history and revert; each batch records the profile version used |
| Branding (name, logo, colours) | `SCR-037` | Client project owner | Apply and check contrast; capture a new deck cover | Recorded; the contrast guard refuses unreadable pairs |
| AI provider, model, caps, key | `SCR-038` | Whoever owns the AI decision | Provider + key, then **test connection**; caps and redaction stay at their documented defaults unless changed deliberately | Key stored with DPAPI; rotation/revocation per `13` §5.3; usage log records model and prompt version |

**Rule:** a configuration change that alters what the client sees is **told to the client in writing** the
same day (a one-paragraph note is enough), and any change that changes a delivered figure is a change-order
item (`19` §5.1, Addon 4 §E.3).

## 5. Editing prompts (AI features)

Prompts are versioned repository files, reviewed exactly like code (`10` §4). The procedure is fixed:

```
1. Copy app/engine/ai/prompts/<prompt_id>.v<N>.md  ->  <prompt_id>.v<N+1>.md and edit it
2. Update doc 10 §5 in the same commit        (the doc and the template may never diverge)
3. CHANGELOG entry: what changed, why, expected effect
4. Re-run the AI eval fixtures; record the output diff in SESSION_LOG
5. If the output character changes materially -> behaviour change: bump the version and record it in 18 §5
```

| Rule | Detail |
|---|---|
| Immutability | A shipped prompt version is never edited in place; history keeps the version that produced each draft |
| Stamping | Every call records `prompt_id + version` in the usage log and on the draft (`FR-AI-011`) |
| Client visibility | The active version per feature is readable in Settings → AI, full text, because the templates contain no secrets and no client data |
| No client data in prompts | Templates carry instructions and placeholders, never client values |

## 6. Tuning rules and thresholds

| Situation | Action | Never |
|---|---|---|
| A rule raises too much noise | Raise its threshold or narrow its scope in Settings; re-run; measure before/after | Disable the rule silently, or suppress in the data |
| A rule misses a class of issues | Note it, then extend the rule spec and plantings in `06` before any code (`06` §10) | Patch the client's file so the rule fires |
| Master data is missing | Leave the dependent rules relaxed with the visible notice, and chase the data (`Q-010`, `Q-011`) | Invent vendor categories or recurring costs |
| The client disagrees with a raise | Record the status and the reason on the exception; consider a tuning change for next month | Edit the exception out of the register |

All rule changes go through `06` §10's change control (spec, plantings, tests, then code) and are recorded in
the `CHANGELOG`; the effective threshold on each historical exception never changes retroactively.

## 7. Dependency updates and supply chain

| Cadence | Action | Evidence |
|---|---|---|
| Monthly | `pip-audit` on the frozen environment; review advisories for Python, UI and packaging dependencies | Audit output filed in the session log |
| Monthly | `scripts/check-licenses` — nothing outside the allow-list (`13` §12) | Check transcript |
| Per release | Regenerate the SBOM snapshot and `THIRD_PARTY_LICENSES.txt` (Python **and** UI dependencies) and ship it in the payload | Files present in the payload audit (`15` §3.2 step 5) |
| Per release | Re-verify the pinned Inno Setup major version and the pinned PyInstaller version with a smoke build | Build report |
| As needed | A dependency **update** follows the change order: `CHANGELOG` → tests → code; a dependency **addition** needs an ADR (`09` `ADR-002`) | ADR + `CHANGELOG` entry |

**Frozen-toolchain rule (`ADR-002`):** the Python version, framework, UI stack and packaging toolchain do
not change between releases without an ADR. A security update that would break a pin is an ADR with the
trade-off written down, not a quiet bump.

## 8. The diagnostics workflow (the only supported path)

### 8.1 What the user sends

1. **About / Diagnostics** (`SCR-040`) → **Create diagnostics zip** (`FR-XC-005`).
2. One line about what they were doing, with the screen's `SCR-nnn` if they have it.
3. The zip, to their support contact. **Nothing else** — not the project, not the databases.

### 8.2 What the zip contains — and what it never contains

| Included | Never included |
|---|---|
| App/build/schema versions, dependency lock hash, OS build, locale, DPI, free disk, RAM | The AI key or any secret; DuckDB/SQLite files; raw archives; exports; crash dumps (offered separately, with their own warning) |
| Provider/model names with the **host redacted**; theme; data directory as `%LOCALAPPDATA%` | Windows user name and machine name (masked to `%USER%`/`%MACHINE%`) |
| Project name **hashed** with a UI-visible alias; table names; column headers; row counts; batch IDs | Vendor names, descriptions, document numbers, amounts — unless the user opts in **and** the values are masked to `V-###` / magnitude buckets |
| Last 2 MB of the app log and the project log (tail-truncated) | Anything outside the project folder, or a path that identifies a person |

The manifest schema is `fpa.diagnostics.v1` (`13` §7); the redaction rules are the security document's,
not this one's. **A diagnostics zip is safe to forward; a project folder is not.**

### 8.3 What support does with it

| Step | Action | Output |
|---|---|---|
| 1 | Confirm versions and schema compatibility (`doctor`) | Whether the build matches the reported release |
| 2 | Read the last error records and failed checks | The failing operation and its code (`ERR-*`) |
| 3 | Reproduce on the sample project or a restored copy using the CLI (`09` §5.2) | A reproduction, or a ruled-out class of cause |
| 4 | Classify the defect (S1–S4 per `14` §14.1) and state the next action to the client **in writing** | Incident entry (§11) |
| 5 | If a fix is needed: spec → `CHANGELOG` → tests → code → release (`19` §5.1) | Fix released with a regression test that names the incident |

**Never ask for:** the project folder, a password, the AI key, administrator rights, or the client's
screen-share to "just look around" (`15` §9.4). If a project must be examined, the client makes a backup
themselves and shares it through their own protected channel — a backup is a plain zip, and that warning is
printed in the UI (`13` §9.2).

## 9. Upgrades, migrations and rollback

| Situation | Procedure | Guard |
|---|---|---|
| App upgrade, same schema | Install over the previous version (per-user install); projects open unchanged | `doctor` reports version/schema state |
| App upgrade, new schema | On first open, the app **backs up the project**, applies forward-only migrations, and reports what changed (`09` §13, `ADR-008`) | No migration runs without a backup; no downgrade path is offered |
| Rollback needed | Restore the pre-upgrade backup with the older build; the newer build's projects are **not** readable by it (documented in `24`) | Rollback is a restore, never a reverse migration |
| Client moves machine | Install, then restore projects from their backups; portable package is the fallback (`15` §4.3) | Restores go into empty folders only (`13` §9.2) |
| New Windows/Defender behaviour | Re-run the SmartScreen/Defender walkthrough steps and update `15` §8 if the dialogs differ | Walkthrough text is copy-audited (`TST-SEC-19`) |

## 10. Incident playbook

| Symptom | First checks | Likely cause | Action |
|---|---|---|---|
| App will not start | `doctor --json`; event log; WebView2 presence | WebView2 missing, permissions, antivirus quarantine | Documented fallback path (`15` §6.3/§8.4); never "run as administrator" blindly |
| Installer blocked | SmartScreen/Defender dialogs | Unsigned build, new download | Walk through `15` §8.3 with the user; verify SHA-256 first |
| Project will not open | `doctor`; schema version; file locks | Sync folder, second instance, interrupted migration | Follow `ADR-004` (move off sync folder), close the other instance, restore from backup |
| Import fails mid-file | Batch status; log tail; disk space | Corrupt source row, disk full, cancellation | Batch is atomic: re-import after fixing; nothing partial is committed |
| Numbers disagree with the manual pack | Drill-through vs source lines; window and date basis | Mapping, period assignment or rounding presentation | Diff via the CLI (`bva`/`report`); if the app is wrong it is an S1 with a test |
| Pack generation fails | Error code; size guard; template presence | Missing template asset, size limit, locked output file | Rebuild payload audit; regenerate per `11`/`12` failure modes |
| Slow behaviour | Baselines vs now; project size; storage on network drive | Local disk, project growth, antivirus scanning | Re-measure against `14` §3; storage health (`SCR-032`) |
| Data corruption suspected | Integrity check via `doctor` | Hardware/sync/antivirus | Stop writes, copy the project, restore the last good backup, record the incident |

**Severity and response:** severity classes are `14` §14.1's; the response targets below are the support
**defaults in force until `OQ-016` is agreed** (`28` owns the client-facing confirmation):

| Severity | Meaning | Ack | Workaround/fix |
|---|---|---|---|
| S1 | Data loss risk, wrong numbers, app unusable | Same business day | Workaround or fix plan within 2 business days |
| S2 | A major task blocked, workaround exists | 1 business day | 5 business days |
| S3 | Minor defect or wording | 3 business days | Next scheduled release |
| S4 | Cosmetic or request | 5 business days | Backlog (`27`) |

Escalation **levels** (L1–L3) and their targets are owned by `15` §9.3; the table above is the client-facing
response target by severity. Both are defaults until `OQ-016` is agreed.

## 11. Support model, escalation and the support log

| Aspect | Rule |
|---|---|
| First line | The client analyst contacts the consultant directly (`Q-018` default; no ticket system in v1) |
| What support needs | The diagnostics zip + one sentence + the screen ID; nothing else |
| What the client gets back | A written answer: what happened, what to do now, what will change and when |
| Escalation | `15` §9.3's ladder: **L1** consultant (install/upgrade, how-to, wording, mapping; same business day) → **L2** engineer (reproducible defects, data issues, packaging; first assessment ≤ 2 business days) → **L3** change control (spec gaps → `27` / impact note, decided at the next gate). Every escalation states impact, workaround and the decision needed |
| The support log | One entry per contact: date, severity, symptom, code (`ERR-*`), cause, action, follow-up, test added (Y/N) |
| Recurring themes | A theme appearing three times becomes a `27` backlog entry or a spec change — never a standing workaround |
| Closure | An incident closes when the client confirms the workaround/fix, and the regression test (if any) is green |

## 12. The handover pack

| Item | Where it lives | Given to the client? |
|---|---|---|
| Installer + `SHA256SUMS-<version>.txt` | Release record (`15`/`24`) | Yes |
| The user guide | `22` (shipped as PDF/help panel at UAT) | Yes |
| The client requirements pack (decisions, open questions, what to confirm) | `29` | Yes |
| Support flow + diagnostics instructions | §8, §11 and `22` §7.4 | Yes |
| Release/versioning notes they need for their own IT record | `24` (summary only) | Yes, summary |
| This document | Repository | Optional: the support-flow and escalation parts, on request |
| Source, docs `00`–`21`, tests | Repository | **No** — internal delivery assets |
| AI key, any credential | The client's own custody | Never handled by the consultant (`13` §5) |

## 13. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `24` | Owns tags, release checklist mechanics, distribution and the upgrade fixture; this document's §3 order must match it |
| `15` | Keeps §3/§5/§8/§9 current; a change there lands here in the same pass |
| `13` | Owns the diagnostics manifest and redaction rules; a change there updates §8.2 |
| `10` | Owns the prompt registry; the §5 procedure is binding on prompt edits |
| `06` | Owns rule change control; §6 cites it and never restates a rule |
| `14` | Owns the fresh-clone bootstrap test and the check composition referenced in §2.2 |
| `28` | Owns the UAT/go-live support mechanics and the client-facing confirmation of §11's targets |
| `29` | Restates the support flow and the diagnostics promise to the client in plain language |
| `18` | Registers an ADR or a `DEC` for anything in §4–§7 that becomes a standing policy |

## 14. Change control for this document

1. **A procedure change is a spec change:** it updates the owning doc (`15`/`24`/`13`/`10`/`06`) first,
   then this checklist, in the same pass — never the other way round.
2. **Every incident adds a row** to §10's playbook or a `27` entry; a playbook row without a real incident
   behind it is removed at the next review.
3. **SLA figures in §10 are defaults** until `OQ-016` is answered; the answer replaces them here and in
   `28`.
4. Reviews at every phase gate (`16` §5.1) and after every S1 incident.

## 15. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| Bootstrap sequence | `uv sync --frozen` → `npm ci` → `doctor` → `scripts/check` | §2.2, `14` §13.1 |
| Release order | Gate → version → build → clean-Windows protocol → checksums/SBOM → notes → tag → approval | §3, `15` §3, `24` |
| Config surfaces | Six (`SCR-033`…`SCR-038`), each versioned and reversible | §4 |
| Prompt edit steps | Five, with the template and `10` §5 changing together | §5, `10` §4.2 |
| Diagnostics safety rule | Zip only; project folder is never requested | §8.2, `15` §9.4 |
| Severity scale | S1–S4 (`14` §14.1) with the default response targets in §10 | §10, `OQ-016` |
| Support log fields | Date, severity, symptom, code, cause, action, follow-up, test (Y/N) | §11 |
| Handover pack | Eight rows; four go to the client, the rest are internal | §12 |
