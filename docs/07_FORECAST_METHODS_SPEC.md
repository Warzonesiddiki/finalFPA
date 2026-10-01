> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-FC-001`…`FR-FC-009`; forecast behaviour, method selection, scenarios, versions and locks, accuracy reporting, method-choice guidance
> **TL;DR (≤ 15 lines):** This document owns how the rolling forecast *behaves*: closed periods locked to
> actuals, four deterministic methods (remaining-budget spread, run-rate, 3-month average, manual
> override) resolved through a three-level resolver (line → account group → project default), three
> scenarios (Base/Best/Worst) as separate versioned outputs, the version lifecycle (draft → locked →
> superseded) with the rule that issued packs always reference a locked version, the accuracy report for
> closed periods, and the non-blocking method-choice guidance built from that accuracy history. All
> arithmetic is owned by `05` (`CALC-060`…`CALC-069`) and is never restated here. Forecasts never touch
> actuals or budget; every forecast row carries its method, version, driver reference and generation
> stamp so a number can be explained months later.

---

# 07 — FORECAST METHODS SPECIFICATION

## 1. Purpose and ownership boundary

| Concern | Owner |
|---|---|
| Forecast **behaviour**: eligibility, method resolution, scenarios, versions, locks, accuracy reporting, guidance | **`07` (this document)** |
| Forecast **arithmetic**: the four methods, scenario adjustment, accuracy metrics | `05` §9 (`CALC-060`…`CALC-069`) |
| Forecast row structure and provenance columns | `03` §4.3/§4.4 |
| Forecast screens, charts, copy | `08` (`SCR-`, `CHT-`) |
| Forecast-versus-actual columns in analysis views | `02` (`FR-BVA-008`) |

**Rule:** if a number appears in this document, it is a *reference* to a `CALC` ID in `05`. Restating a
formula here would violate the Source-of-Truth Matrix (`00` §5).

## 2. Why the forecast exists in this product

The client's monthly rhythm includes "builds budgets including rolling forecasts" (kickoff §2). The tool's
forecast is deliberately **narrow and explainable**: it answers *"given what has actually happened, where
does the year land?"* — it is not a driver-based planning engine. Every method is simple enough that a
finance director can reproduce it by hand, which is a feature, not a limitation (advanced methods such as
seasonality indices and driver regression are parked, `BL-018`).

## 3. Forecast lifecycle

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │  1. Period closes  →  2. Actuals locked  →  3. Generate forecast       │
   │      (new period)      (CALC-060)             (methods §5)             │
   │                                                                            │
   │  4. Review & override  →  5. Compare scenarios  →  6. Lock version     │
   │      (per line, with reason)                        (read-only)          │
   │                                                                            │
   │  7. Pack issued (references the locked version)  →  8. Next period:     │
   │      drafts, overrides and scenario choices carry                            │
   │      forward as *settings* — never as numbers                            │
   └────────────────────────────────────────────────────────────────────────┘
```

| Step | Behaviour | FR |
|---|---|---|
| 1–2 | When a period closes, its actuals are frozen; the forecast never writes to them | `FR-FC-001`, `FR-FC-005` |
| 3 | Generation covers only **forecast-eligible** periods (§4) and produces a **new draft version** per scenario | `FR-FC-002`, `FR-FC-009` |
| 4 | Any line may be overridden with a mandatory reason; overrides are listed, versioned and highlighted in exports | `FR-FC-006` |
| 5 | Scenarios are compared side by side; each scenario is its own version | `FR-FC-003` |
| 6 | Locking makes a version read-only; a pack may only reference a locked version | `FR-FC-009`, `FR-XC-003` |
| 7 | The issuance register records the version and snapshot behind every issued pack | `FR-XC-003` |
| 8 | Carry-forward is **configuration-only**: method choices, scenario adjustments, exclusions and overrides-as-settings carry forward; **amounts never do** (`FR-PRJ-004`) | `FR-PRJ-004` |

**Monthly-rhythm requirement (P11):** the forecast is a recurring monthly artefact, not a one-off. The
New Period wizard reminds the user that the forecast needs refreshing and shows when it was last generated.

## 4. Eligibility rules (what may be forecast)

| Period state | Forecast behaviour |
|---|---|
| **Closed** | Locked to actuals. **No forecast rows are generated** (`CALC-060`). If a closed period has no actuals, it is treated as `0` **and** flagged in the forecast summary as "no actuals" — never silently zeroed |
| **Open, within the fiscal year** | Forecast-eligible: gets rows from the resolved method |
| **Open, before the year's first loaded actual** | Eligible only for manual override or remaining-budget spread (history-based methods are ineligible, below) |
| **Beyond the fiscal year** | Never forecast — out of the model |
| **Current period (not yet closed)** | Mixed: actuals already posted are shown as actual; the remainder of the period is forecast. The UI always labels the boundary date so the mix is never ambiguous |

### 4.1 Method eligibility (the guard table)

| Method | Eligible when | Otherwise |
|---|---|---|
| `remaining_budget` | A budget exists for the account and ≥1 open period remains in the year | Disabled for the line when the year is complete (`k = 0`) |
| `run_rate` | ≥ `N` loaded actual periods exist for the same key (`N` = the configured window, default 3) | Disabled with the hint *"Needs at least N loaded actual periods"* |
| `avg_3m` | ≥ 3 loaded actual periods exist for the same key | Same hint with `N = 3` |
| `manual` | Always eligible (the user supplies the value) | — |

**Never substitute a different method silently.** If the resolved method is ineligible, the line falls back
in a documented order — `manual` (if an override exists) → `remaining_budget` (if budget exists) →
**no forecast row, flagged as "not forecast — insufficient history"** in the forecast summary and on the
affected lines. The fallback used is recorded per line so the summary is reproducible.

## 5. Method resolution (which method applies to a line)

Resolution is a three-level, most-specific-wins cascade. The resolved method is stored on every generated
row (`03` §4.3 `method_id`) — no row is ever generated without its method recorded.

| Priority | Level | Configured where | Example |
|---|---|---|---|
| 1 | **Line-level** override | Forecast workspace, per line | Account 5450/CC-160 pinned to `manual` |
| 2 | **Account-group** setting | Settings → Forecast (groups defined by statement line or account range) | All marketing accounts → `avg_3m` |
| 3 | **Project default** | Settings → Forecast | `run_rate` with `N = 3` |
| 4 | **Fallback** (no configuration) | Built-in | `remaining_budget` |

| Additional rules | Detail |
|---|---|
| Pin vs suggest | Line-level settings are **pins** (they always win); guidance (§8) is a **suggestion** that requires an explicit user action to become a pin |
| Grouping | Account groups are data (name + account range or statement line), versioned like every other configuration |
| Exclusions | A line or account may be marked **"not forecast"** (e.g. a closed project); excluded lines generate no rows and appear in the forecast summary's exclusion list with the reason |
| Drivers | `run_rate`/`avg_3m` record which actual periods fed the average; `remaining_budget` records the annual budget and the consumed amount (`03` §4.3 `driver_ref`) |
| Seasonality | Not applied in v1 (parked, `BL-018`); the UI states plainly that methods are non-seasonal so nobody infers a seasonal model |

## 6. Scenarios

| Scenario | Purpose | Mechanism | Default adjustment |
|---|---|---|---|
| **Base** | The expected landing | The resolved method, unadjusted | `0%` |
| **Best** | Upside case | Base result × (1 + adjustment) per driver/account group, or per-line overrides | `+5%` on revenue, `−3%` on discretionary cost |
| **Worst** | Downside case | Same mechanism, negative direction | `−5%` on revenue, `+3%` on discretionary cost |

| Scenario rules | Detail |
|---|---|
| Adjustments are **data** | Stored per account group with the scenario, versioned with history and revert |
| Actuals never move | Scenarios change only forecast rows (§ `CALC-065`); budget and actuals are identical across scenarios |
| Per-scenario versions | Each scenario has its own version sequence, and can be locked independently |
| Identity | A scenario with no adjustments is **labelled as identical to Base** rather than presented as an independent view |
| Comparison | The comparison view shows Base/Best/Worst side by side with the variance between them, plus budget as a reference line |
| Deck usage | The deck shows the selected scenario (default Base) and states which scenario it shows on the slide and in the footer (`12`) |

**Scenario adjustment defaults are a documented starting point, not a client fact.** They are labelled
"default, unconfirmed" until the client confirms their own convention (`Q-008`).

## 7. Versions and locks

| State | Writable? | Referenced by packs? | Transitions |
|---|---|---|---|
| `draft` | Yes (generation, overrides, exclusions) | No | → `locked` once reviewed; → `superseded` if a newer draft replaces it |
| `locked` | **No** — read-only | **Yes** (only locked versions may be referenced) | → `superseded` when a newer version is locked for the same scenario |
| `superseded` | No | No (historical reference only) | Terminal; the version remains readable forever |

| Rule | Detail |
|---|---|
| Generation creates a draft | Never overwrites a locked version |
| Locking is explicit | A user action with a confirmation stating what will be frozen (scenario, periods, line count, total) |
| One locked version per scenario | Locking a new version supersedes the previous locked version; the superseded one remains readable and is never mutated |
| Issued packs pin a version | The issuance register stores `forecast_version_id`; a later generation cannot change what an issued pack said (`FR-PRJ-010`) |
| Deleting drafts | Allowed for drafts only, with confirmation; locked/superseded versions are never deleted |
| Provenance | `generated_at`, `generated_by`, `method_id`, `driver_ref` on every row (`03` §4.3) — a forecast number is explainable months later without re-deriving it |

## 8. Accuracy reporting and method-choice guidance

### 8.1 Accuracy report (closed periods)

For every **closed** period where a locked forecast version exists, compare forecast to actual using
`CALC-066`…`CALC-069`. Reported by period, entity, account group and method:

| Column | Source |
|---|---|
| Forecast (locked version) | `FactForecast` rows for that version |
| Actual | `FactActual` for the same key |
| Signed error | `CALC-066` |
| Absolute error | `CALC-067` |
| Signed bias | `CALC-068` (per group over multiple periods) |
| MAPE-lite | `CALC-069`, with the excluded zero-actual periods **counted and shown** |

| Rule | Detail |
|---|---|
| No forecast version for the period | The column shows *"not generated"* with a CTA — never a zero, never a blank that looks like a perfect forecast |
| Locked version missing (only drafts exist) | The report uses the draft and **marks it as "draft — not the issued basis"** |
| Zero actuals | Excluded from MAPE-lite per `CALC-069`; the count of excluded periods is displayed |
| Comparability | Accuracy is only computed where the forecast and actual are at the same grain; otherwise the row shows the grain disclosure (same rule as BvA) |

### 8.2 Method-choice guidance (non-blocking)

| Aspect | Behaviour |
|---|---|
| What it shows | Per account group, which method has historically produced the lowest absolute error and the smallest bias, with the number of periods compared and the data behind it |
| Where | Forecast workspace, "Guidance" panel |
| Action | **Suggestion only.** "Apply suggestion to these lines" requires a click; nothing changes automatically |
| Insufficient history | Fewer than `min_accuracy_periods` (default 3) closed periods → the panel shows *"Not enough closed periods yet"* and no suggestion |
| Transparency | Every suggestion states the evidence (periods compared, errors, bias) and the method it would replace |
| Governance | Applying a suggestion writes a configuration change (`VersionHistory`) and marks derived results stale; declining it changes nothing |
| AI role | AI may **explain** an accuracy pattern in words, but the ranking itself is engine arithmetic; AI never selects or applies a method |

## 9. Overrides

| Aspect | Behaviour |
|---|---|
| Who | Any user of the project (single-user app in v1) |
| Requirement | A **mandatory reason** (free text) per overridden line; enforced by the UI and by a data check |
| Scope | Per line (account × cost centre × period **or** the whole line across remaining periods, chosen explicitly) |
| Visibility | Overrides list (filterable), highlighted rows in the workspace, a dedicated column in the Excel pack, and a count on the forecast summary |
| Versioning | Overrides belong to the draft version; locking freezes them; a new draft starts from settings, not from the previous draft's overrides unless the user chooses "carry forward overrides" explicitly |
| Audit | Each override records author, timestamp and old→new value |

## 10. Forecast integrity guarantees (never-cut list items)

| # | Guarantee | How it is enforced |
|---|---|---|
| G1 | **Actuals are never overwritten or blended** | Separate tables; forecast writes are restricted to `FactForecast`; a write-path test asserts no forecast operation mutates `FactActual` (`FR-FC-005`) |
| G2 | **Budget is never modified by forecasting** | Same separation; scenario adjustments apply only to forecast rows (`CALC-065`) |
| G3 | **Every forecast row is explainable** | `method_id` + `forecast_version_id` + `driver_ref` + `generated_at` + `generated_by` (`FR-FC-004`) |
| G4 | **Closed periods are immutable** | Period lock (`FR-PRJ-005`) + snapshot immutability (`FR-PRJ-010`) |
| G5 | **Issued packs cannot be rewritten** | Issuance pins a locked version and a snapshot (`FR-XC-003`) |
| G6 | **Deleting a draft cannot alter a locked version** | Supersession is one-way; locked rows are read-only |
| G7 | **Re-generating is idempotent for the same inputs** | Same data + same settings + same version inputs ⇒ identical rows (tested) |
| G8 | **A line with insufficient history is never invented** | §4.1 fallback order; "not forecast" is an explicit, visible state |

## 11. Worked end-to-end example (uses `05` fixtures)

Inputs: FY26, periods P01–P09 loaded with actuals, P10–P12 open. Budget for account 4000
(Revenue) = `12,000,000.00`.

| Step | Result | Fixture in `05` |
|---|---|---|
| P01–P09 actuals total | `9,300,000.00` | — |
| Remaining-budget spread over P10–P12 | `(12,000,000.00 − 9,300,000.00) / 3 = 900,000.00` per period | F14a |
| Run-rate on the last 3 actuals (`1,080,000.00 + 1,020,500.55 + 995,300.45`) | `1,031,933.67` per period (displayed) | F14b |
| Base scenario, run-rate method, project default | P10–P12 = `1,031,933.67` each | F14b |
| Best scenario (+5% revenue) | `1,083,530.35` per period | F14c |
| Locked version at P09 close; P07–P09 later compared | Signed bias `+8,000.00`, MAPE-lite `1.5%` | F14d |
| Guidance panel | If `avg_3m` had produced a smaller absolute error over the compared periods, it is suggested for the revenue group — with the evidence — and applied only if the user clicks | §8.2 |

## 12. Screen and export touchpoints (informative)

| Surface | Requirement |
|---|---|
| Forecast workspace (`SCR-` in `08`) | Method per line visible, overrides highlighted, scenario switcher, guidance panel, "last generated" stamp |
| Three-way view (`FR-BVA-008`) | Actual / Budget / Forecast with forecast-accuracy columns for closed periods |
| Excel pack (`11`) | Forecast summary sheet with method, scenario, version and generation stamp per line; overrides column |
| PowerPoint deck (`12`) | "Forecast & outlook" slide shows the selected scenario, the landing estimate and the accuracy track record, with the scenario and version named on the slide |
| CLI (`09`) | `python -m app.cli forecast --project <path> [--scenario base] [--lock]` for automation and testing |

## 13. Configuration reference

| Setting | Default | Scope | Notes |
|---|---|---|---|
| Project default method | `remaining_budget` | Project | Most explainable starting point; client may change (`DEC-025`) |
| Run-rate window `N` | `3` | Project | Clamped to loaded periods with a visible notice (`CALC-062`) |
| Account-group methods | none | Project | Optional; most-specific-wins (§5) |
| Scenario adjustments | Best `+5% rev / −3% cost`; Worst `−5% / +3%` | Project | **Default, unconfirmed** (`Q-008`) |
| `min_accuracy_periods` | `3` | Project | Guidance requires this many closed periods |
| Exclusions ("not forecast") | none | Project | Requires a reason; shown in the summary |
| Carry-forward overrides | `false` | Project | Opt-in per generation |

## 14. Change control

1. A change to method **behaviour** (eligibility, resolution, scenarios, locks, guidance) updates this
   document first, then `CHANGELOG`, then tests, then code.
2. A change to method **arithmetic** updates `05` §9 first (with a fixture), then this document's
   references.
3. A new method requires: a `CALC` entry + fixture in `05`, a full behaviour block here (eligibility,
   resolution, driver reference), a golden test, and a `CHANGELOG` entry. Until all exist, the method is
   not selectable in the UI.
4. Scenario-adjustment default changes are recorded in `18` §Decided with the reason.
