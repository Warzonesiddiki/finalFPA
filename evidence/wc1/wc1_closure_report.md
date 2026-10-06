# `WC-1` closure report — Addon 6 v2 work card (`WS-01` → `app/engine/dedupe/`)

> **Date:** 2026-10-05 · **Work card:** `WC-1` (`project prompt/ADDON_6_REUSE.md` §9, SHA-256 `81f5aaee…01d3`)
> **Outcome:** **BUILD** — the pre-approved catalog source (`WS-01`) no longer exists; the capability was
> extracted from our own rule modules and rewired (`R12`). **No adoption, no `ADP-004`, no licence obligation.**
> **Records:** `BD-001` (`32` §2) · `ADR-014` (`09` §3.15) · `DEC-066` + `OQ-028` decided + `D-13` register repair
> (`18`) · `TB-100` (`33` §5.8) · `CHANGELOG` 2026-10-05 · `SESSION_LOG` 014
> **Artefacts:** `evidence/wc1/SHA256SUMS.txt`

---

## 1. Trigger — the catalog source is gone

`WC-1` was pre-approved as COPY-EDIT of catalog `WS-01`, `github.com/ricothanfx/invoice-dedupe`
(“normalization, blocking, weighted-scoring modules only”, MIT via `pyproject.toml`).

Measured 2026-10-05, twice, with the exit status preserved:

```
$ git clone --depth 1 https://github.com/ricothanfx/invoice-dedupe vendor/_upstream/WS-01
remote: Repository not found.
fatal: repository 'https://github.com/ricothanfx/invoice-dedupe/' not found
REAL_GIT_EXIT=128
```

A web search found no such repository and **no renamed successor**. Consequences, in contract terms:

| Rule | Why it fires |
|---|---|
| §6 S2 “fetch pinned upstream” | Cannot complete; there is nothing to fetch |
| `R5` records before code | An `ADP` row must cite a pinned SHA and the files copied — neither exists |
| §6 S4 “listed file missing → STOP” | The whole source is missing, not one file |
| §14 Tier C | Proceed only with owner direction |

**Rollback was clean and verified:** `vendor/_upstream/WS-01` was never created; `vendor/_staging/` and
`vendor/_upstream/` still hold only `WS-02`/`WS-03`/`WS-10`; no `app/` file was touched at that point.

## 2. `S0` finding — the capability is already spec-complete (and the scorer is required by nothing)

The preflight grep found every duplicate rule in `06` is Tier **`exact`**:

| Rule | Where it lived | Tier |
|---|---|---|
| `EXC-002` cross-batch rows | `rules_catalog_001_008.py:223` | `exact` |
| `EXC-007` duplicate invoice | `rules_01_08.py:evaluate_exc_001` (+ `_normalize_invoice_no:221`) | `exact` |
| `EXC-008` duplicate voucher line | `rules_catalog_001_008.py:665` | `exact` |

`EXC-007`’s normalisation clause (*“trim, upper-case, strip leading zeros and non-alphanumeric
separators”*) is implemented verbatim. The eight `fuzzy`-Tier rules in `06` (`EXC-013`…`EXC-019`,
`EXC-022`) are magnitude / pairing / completeness / budget-relationship / controls rules — **none is a
text-similarity problem**. `WS-01`’s headline capability (weighted/fuzzy scoring) is therefore required by
**no** `06` rule, and wiring it into `EXC-007`/`EXC-008` would move them off `exact` — an **`R1` breach**.
`06` keeps duplicates exact deliberately: `EXC-007`’s mitigation states partial-amount duplicates are
*“deliberately out of scope for v1 to keep precision high”*.

The one **real** gap was an `R12` symptom: the normaliser and the two blockers lived **inline in two rule
modules** — two copies of one capability, no shared interface.

## 3. The escalation and the owner’s ruling

`evidence/wc1/ws01-escalation-packet.md` carries the measured facts, the `S0` finding, exactly **three
options** with a recommended default, and the acceptance-gate impact (**none** under any option):

1. **BUILD + `BD` row** (recommended) — record the search once in `docs/32` §2, extract the interface as our
   own code.
2. Intake a replacement source per §10 (`dedupeio/dedupe` — MIT but a record-linkage ML stack:
   `numpy`/`scipy`/`affinegap`/`categorical`, i.e. `R9` + `R13`, and it solves the fuzzy problem the spec
   does not have; `pimverschuuren/Deduplication`, `pmessan/duplicate_invoice_finder` — licences unverified → `L2`).
3. Skip `WC-1`.

**The owner chose option 1**, recorded in `DEC-066`.

## 4. What landed (BUILD — our code in our words, `L2`/`L3`)

| Path | Contents |
|---|---|
| `app/engine/dedupe/normalize.py` | `normalise_alnum_upper`, `normalise_invoice_no`. The `06` clause’s limit is **documented, not silently widened**: *strip leading zeros* collapses zeros only at the start of the alphanumeric string, so `INV-00088213` → `INV00088213` and does **not** block with `INV-88213`. Widening it changes which rows `EXC-007` raises on — an `R1` spec question. Three edge cases preserved from the inline implementation and pinned by tests: absent/falsy → `""`; separators-only (`"---"`) → `"0"` (a number *was* present); all-zeros returned unchanged. |
| `app/engine/dedupe/blocking.py` | `group_by_key`, `iter_candidate_groups` (optional `order_by` for deterministic finding order), `count_distinct`, plus `Group`/`CandidatePredicate` types. Boundary documented: grouping/candidate/order only — thresholds and subject keys stay in the rules. |
| `app/engine/dedupe/__init__.py` | Exports + the `BD-001`/`OQ-028` rationale, including why **no** fuzzy scorer exists. |
| `rules_01_08.py` | `R12`: `_normalize_invoice_no` is now an **alias** of `normalise_invoice_no`; `evaluate_exc_001` blocks through `iter_candidate_groups`. |
| `rules_catalog_001_008.py` | `R12`: `evaluate_catalog_exc_008` blocks through `iter_candidate_groups` + `count_distinct`. |
| `tests/unit/test_dedupe.py` | **New**, 41 tests: the `EXC-007` clause, blocking/order guarantees, `EXC-008`’s “different voucher” predicate, and two `R12` guards (the rules delegate; no weighted scorer was added). |

**No file carries an `Adapted from` header and no notices entry is owed** — nothing was adapted. `E8` governs
adoptions; there is no adoption here.

## 5. Verification (measured this session)

| Check | Result |
|---|---|
| `python -m pytest tests/unit/test_dedupe.py --cov=app.engine.dedupe` | **41 passed**; `app/engine/dedupe` **100 % statements, 100 % branches** (45 stmts / 16 branches) |
| `test_rules_01_08` + `test_rules_catalog_001_008` + `test_rules_batch` + 2 import suites | **54 passed** |
| `python -m pytest tests/rules/test_acceptance.py -o addopts=""` (277 s) | **26 passed, 5 failed — the five pre-existing `14` §5.3 bars, byte-identical to baseline**: recall 11/32, control 1 fired (`P30`), High 6/18, 422 extras, the same 14 zero-coverage rules. Behaviour-preservation proof for the rewiring. |
| `scripts/team.py check` | PASS (0 fail) — 1 active claim, 47 tasks |
| Guard falsification | overlapping claim → refused; leader-only path by non-leader → refused; WIP limit 2; released claims free their paths (found & fixed a bug where released claims kept blocking) |

## 6. Register repair (`D-13`) — found during the doc-sync sweep

The `docs/18` DEC register held **65 rows but only 64 unique IDs**: `DEC-064` was appended **twice** and
`DEC-063` — the WS-10 `ADP-002` adoption, cited by `09` §3.13 (`ADR-012`), `STATE.md` and the `DEF-018`
closure report — **had never been appended**. Repaired line-wise by script (CRLF preserved; verified after:
66 rows, 66 unique, `DEC-001`…`DEC-066`): `DEC-063` reconstructed from `ADR-012` and placed in ID order, the
duplicate removed, a dated note (`D-13`) added under the table. **No decision changed; no ID reused.** The
register’s only remaining non-numeric step is the pre-existing, documented `DEC-054` renumber (`DEF-014` fix).

## 7. Deliberately not done

- **The contract file was not edited.** `project prompt/ADDON_6_REUSE.md` still hashes to
  `81f5aaee2461851f125e68c0bc7731de5fcf576e814f0beae1e0abfd6ee801d3` (re-verified), the identity `DEC-062`
  records. Annotating the stale `WS-01` row would have broken that hash; the dead URL is flagged in
  `BD-001`/`DEC-066` instead. The contract is the owner’s document; the registry is where we record.
- **No fuzzy scorer, no `rapidfuzz`, no new dependency** (`R9` not triggered).
- **No commit** — the request was not made; all work is in the working tree.
- The five red acceptance bars are untouched (`TB-020` corpus rebuild, M1) — the card could not affect them
  and the measurement proves it did not.
