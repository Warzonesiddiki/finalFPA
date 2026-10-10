# UX-19 — Field authority: board pack vs exceptions register

**Task**: `UX-19` [P0] — "Two truths is the failure mode of this product: the board pack and the
exceptions register must never disagree about the same finding, the same owner or the same status.
Write down the single source of truth for each field, then state the screen where a disagreement is
resolved."

**Acceptance**: a field-by-field table naming the authority for each field, and the reconciliation
rule for the ones that have none.

**Method**: every claim below is a `file:line` citation opened on 2026-10-10 and audited with
`python scripts/open_cited_lines.py evidence/ux19_field_authority.md --limit 0` (result recorded in
the handoff). Solo session — the team was dissolved 2026-10-10, so verification is command-evidence
within this session rather than a different-agent review; stated here so nobody later mistakes it
for one.

---

## 1. The three surfaces, as implemented today (measured)

| Surface | Read path | Where its exception rows actually come from |
|---|---|---|
| **Exceptions register (UI, live)** | fetch at `ui/src/components/exceptions/ExceptionsScreen.tsx:48`; route at `app/api/main.py:1242`; repository read at `app/engine/store/exceptions_repo.py:611` | The **live store** (`FactException`) |
| **Excel board pack, Sheet 5 "Exception Register"** | issuance function at `app/engine/store/reports_repo.py:79`; the issuance data source is the demo builder; CLI equivalent at `app/cli/main.py:184`; builder defined at `app/engine/exports/excel_pack.py:394`; literal demo rows at `app/engine/exports/excel_pack.py:888`, at `app/engine/exports/excel_pack.py:921`, and at `app/engine/exports/excel_pack.py:954` | **Hardcoded demo rows** inside `create_sample_pack_data` |
| **PowerPoint deck, Slide 5** | issuance function at `app/engine/store/reports_repo.py:150`, calling `generate_powerpoint_deck` at `app/engine/store/reports_repo.py:176`; CLI equivalent at `app/cli/main.py:199`; demo defaults at `app/engine/exports/ppt_pack.py:299` with the first literal row at `app/engine/exports/ppt_pack.py:301` | **A different set of hardcoded demo rows** (dataclass defaults) |

Neither export path reads the store. The Excel export also falls back to the demo builder whenever
no data is passed: `pack_data = data or create_sample_pack_data()` at
`app/engine/exports/excel_pack.py:2531`.

The Excel issuance data source is `pack_data = create_sample_pack_data()` at
`app/engine/store/reports_repo.py:101`.

## 2. The measured disagreement (this is not a risk, it is the current state)

The three surfaces do not merely *risk* disagreeing — they **cannot agree by construction**:

| | Register (live) | Excel Sheet 5 | Deck Slide 5 |
|---|---|---|---|
| Row count | whatever `FactException` holds | 3 literal rows (first at `app/engine/exports/excel_pack.py:888`) | 5 literal rows (defaults at `app/engine/exports/ppt_pack.py:299`) |
| Example finding ids | store ids | ids `101`/`102`/`103`, first row starting at `app/engine/exports/excel_pack.py:889` | voucher-style labels such as `V-00931 / INV-2026-88`, first at `app/engine/exports/ppt_pack.py:303` |
| Example owners | live `owner` column | `Rahul Mehta`, `Priya Sharma` (rows beginning at `app/engine/exports/excel_pack.py:888`) | `Rahul`, `Aarti`, `Unassigned` (defaults at `app/engine/exports/ppt_pack.py:305`) |
| Write path | `PATCH /api/v1/exceptions/{id}` at `app/api/main.py:1386`, repository write at `app/engine/store/exceptions_repo.py:893` | none (generated file) | none (generated file) |

The consequence for existing evidence: the UAT parity check compares pack against pack, both built
from sample data — `evidence/New-09_uat_verify.md:118` records that the parity test uses an
in-memory `sample_pack_data` generator. Demo-vs-demo parity can pass while the register (the screen
the analyst actually works in) disagrees with both. That is exactly why `TB-039` cross-artifact
("UI = Excel = PPT = CLI, exact equality") is still open.

## 3. Field-by-field authority table

Legend — **Authority** = the single source of truth a reader must treat as current; **Reconciliation
rule** = what to do when two surfaces disagree, and where it is resolved.

| # | Field(s) | Register source (live) | Pack/deck source (today) | Authority | Reconciliation rule + resolution screen |
|---|---|---|---|---|---|
| 1 | **Finding identity**: `exception_id`, `rule_id`, `subject_key` (identity hash `sha256(rule_id\|subject_key)`, FR-EXC-004) | `FactException` row via `app/engine/store/exceptions_repo.py:611` | hardcoded literals (`app/engine/exports/excel_pack.py:888`, `app/engine/exports/ppt_pack.py:301`) | **Store.** Identity is created once at raise time and never re-derived by any surface | Register wins. A pack row whose identity does not exist in the store is a stale/fabricated pack → regenerate the pack; `SCR-023` Exceptions Register is the reference read |
| 2 | **Rule facts**: `rule_name`, `rule_version`, `family`, `severity`, `mark`, `effective_threshold` | persisted at raise time by the engine, read back via `app/engine/store/exceptions_repo.py:611` | hardcoded literals | **Store (raise-time values).** The engine computes them once; surfaces display, never recompute | Register wins; regenerate pack |
| 3 | **Subject facts**: `subject`, `entity`, `account_code/name`, `cost_centre`, `vendor`, `period`, `first_seen` | store | hardcoded literals | **Store** | As #1 |
| 4 | **`amount_at_risk`** (Decimal) | store | hardcoded literals | **Store**, raise-time Decimal | As #1; no surface ever edits it |
| 5 | **`status`** | `PATCH /api/v1/exceptions/{id}` at `app/api/main.py:1386` is the **only** write path; repository write at `app/engine/store/exceptions_repo.py:893`; transition table at `app/engine/store/exceptions_repo.py:62`; evidence-required set at `app/engine/store/exceptions_repo.py:72` | not written (pack is a file) | **Store via `update_exception`.** Nothing else may change status | The **register screen (`SCR-023`, detail drawer `SCR-024`)** is the only surface where status changes, and therefore the screen where a status disagreement is resolved. A pack showing a different status is a stale snapshot → regenerate |
| 6 | **`owner`** | same PATCH path `app/api/main.py:1386` with the same transition/evidence validation | hardcoded literals | **Store via `update_exception`** | As #5: resolved on `SCR-023`/`SCR-024`; a pack never wins |
| 7 | **Notes / evidence refs / events** (`notes_count`, `last_note`, `evidence_refs`) | append-only store history via detail read at `app/api/main.py:1273`; sheet builder for the pack's notes columns at `app/engine/exports/excel_pack.py:1970` | hardcoded literals | **Store, append-only** | Register wins; notes are never edited in place, so a pack note count can only be older, never different → regenerate |
| 8 | **Time-derived fields**: `age_days`, `overdue`, SLA due, aging bucket | derived at read from `first_seen` + status + SLA windows (doc `06` §2.5) | derived from pack rows at generation, frozen | **No single stored authority — basis-stamped derivation.** Both surfaces must derive from the same stored inputs with the same rule; the pack additionally carries its generation stamp | Disagreement is *always* an age question: the pack is correct **as of its stamp**, the register is correct **now**. If the pack's stamp predates the current state, the pack is stale → regenerate. Never edit either side to match the other |
| 9 | **Aggregate chips**: total / open / overdue / high / unassigned counts | computed client-side from the live API row set at `ui/src/components/exceptions/ExceptionsScreen.tsx:287` | computed from pack rows at `app/engine/exports/excel_pack.py:2101` | **No independent authority — structural.** A count is a function of the row set; the authority rows are #1's | Counts must never be compared directly. On disagreement, compare the **row sets** (register's vs pack's): the register's row set is authoritative, then regenerate the pack. A count that matches while row sets differ is coincidence, not agreement |
| 10 | **Provenance**: `run_id`, `correlation_id`, `claim_id`, `raised_at`, `last_seen_at`, `closed_at`, `flagged_again` | store audit columns via `app/engine/store/exceptions_repo.py:611` | hardcoded literals; pack stamp block carries context (pack_version, scenario, periods) | **Store** for finding provenance; **`FactExport`** (insert at `app/engine/store/reports_repo.py:114`) for pack issuance fields | As #1 for finding provenance. Pack issuance facts (`pack_version`, `generated_at`, `generated_by`) exist only in the pack world — the register never shows them, so they cannot disagree |
| 11 | **Pack-only issuance fields**: file name, size, status `ready` | not shown in register | `FactExport` row written at `app/engine/store/reports_repo.py:114` | **`FactExport`** | No reconciliation needed — single-surface fields by definition |

**The rule in one sentence**: every field the register and the pack share has exactly one authority —
the store (`FactException`, written only through the validated PATCH path) — except time-derived
fields and their aggregate counts, which have *no* stored authority and are governed by
**basis-stamped derivation**: same inputs, same rule, pack stamped with its generation time, and any
disagreement resolved by regenerating the pack, never by editing either truth.

## 4. Where a disagreement is resolved

**The Exceptions Register screen (`SCR-023`), with the detail drawer (`SCR-024`), is the single
resolution surface.** It is the only surface that both reads the store live and can write to it
(status/owner/notes through the validated PATCH path at `app/api/main.py:1386`). The pack and deck
are read-only outputs; the correct action on any disagreement is to regenerate the pack after the
register reflects the desired state — never to reconcile by editing a generated file or by
loosening the register.

## 5. Compliance status of each surface (honest)

| Surface | Compliant with the authority rule? | Evidence |
|---|---|---|
| Exceptions register (API + UI) | **Yes** — all reads live from store, all writes via the validated PATCH path | `app/api/main.py:1242`, `app/api/main.py:1386`, `app/engine/store/exceptions_repo.py:611`, `app/engine/store/exceptions_repo.py:893` |
| Excel pack Sheet 5 | **No — violates by construction.** Production issuance wires the hardcoded demo builder, not the store | `app/engine/store/reports_repo.py:101`, `app/cli/main.py:184` |
| Deck Slide 5 | **No — violates by construction.** Production issuance uses dataclass defaults of hardcoded demo rows | `app/engine/store/reports_repo.py:176`, `app/engine/exports/ppt_pack.py:299` |

The code fix is **out of scope for this card** (UX-19's acceptance is the authority table and the
reconciliation rules, both delivered above) and is recorded on the board as `TB-110` in `docs/33`
§5.6, feeding the open `TB-039` cross-artifact bar.

## 6. What this table does not cover

- Commentary/issuance narrative (`CommentaryRowDTO` and `save_commentary` in
  `app/engine/store/reports_repo.py`) is a pack-world field set; the register does not display it,
  so it cannot create a two-truths disagreement today. If it ever surfaces in the register, it
  enters this table with the commentary register as authority.
- This card does not change any code, spec threshold, or test expectation (docs/evidence only).

## 7. Checkable claims (each paired with exactly one citation)

- Excel issuance data source: `pack_data = create_sample_pack_data()` — `app/engine/store/reports_repo.py:101`
- Export fallback: `pack_data = data or create_sample_pack_data()` — `app/engine/exports/excel_pack.py:2531`
- Workflow transition table: `EXCEPTION_STATUS_TRANSITIONS = {` — `app/engine/store/exceptions_repo.py:62`
- Evidence-required statuses: `STATUS_EVIDENCE_REQUIRED = frozenset({"corrected", "reopened", "not_applicable"})` — `app/engine/store/exceptions_repo.py:72`

## 8. Verification command

`python scripts/open_cited_lines.py evidence/ux19_field_authority.md --limit 0` — exit status and
raw output are pasted into the handoff for this claim.
