# `TB-026` slice 1 — duplicate-definition survey and the `R12` guard

> **Date:** 2026-10-05 · **Author:** `buffy` (leader) · **Claim:** `TB-026` (forced past dep `TB-016`/mypy,
> logged: this slice delivers the guard + survey, not the `engine/common/` package, which does need the
> import-linter/mypy boundary first)
> **Artefact:** `tests/unit/test_engine_common.py` · **Result:** 6 tests, mutation-verified

## The question `TB-026` asked

> Create `engine/common/` and consolidate duplicated money/period/hash helpers into it; add the
> single-implementation test.

## What the measurement said

`TB-026`'s premise is **half already done**. An `ast` walk of `app/engine` (module- and class-level
definitions only) on 2026-10-05:

| Capability | Homes today | Verdict |
|---|---|---|
| `quantize_money` | `app/engine/calc/math.py:133` — **1** | already consolidated (`R8` money) |
| `period_end_from_id` | `app/engine/rules/rules_01_08.py:159` — **1** | already consolidated |
| `resolve_as_of_date` | `app/engine/rules/rules_01_08.py:182` — **1** | already consolidated |
| `normalise_invoice_no` | `app/engine/dedupe/normalize.py` — **1** | consolidated this session by `WC-1` |
| `_get_val` | `rules_01_08.py` (imported by the other rule modules) — **1** | already consolidated |
| hash/key digests | 12 modules call `hashlib.sha256` **ad hoc** (no shared helper) | **real gap** |
| `split_sentences` | `ai/guardrails.py:473`, `exports/ppt_fit.py:47` — 2 | **real duplicate** |
| `check_banned_phrases` | `ai/client.py:414`, `ai/guardrails.py:290` — 2 | **real duplicate** |

The 9 duplicate *names* in the tree are otherwise duplication **by nature**: `__init__` (24 classes),
`to_dict`/`__post_init__` (per-DTO), `_get_conn`/`_ensure_table` (per-`ai/`-module), `generate`
(different classes), `run_rules` (harness vs repository layer), `lock_version` (two different locks).

## What I built, and why not a package

The consolidation `TB-026` asks for is done for the money/period helpers. Creating `app/engine/common/`
now would mean it importing **backwards** — `common → calc`/`rules` — which is exactly the engine-boundary
violation `TB-014`/`TB-016` exist to prevent, and it is why `TB-026` carries the `TB-016` dependency. Forcing
that dependency to "finish" the task would have produced a worse architecture and a false ✅.

So slice 1 delivers the part that was genuinely missing: **the machine guard**, which is what stops the next
duplicate. `tests/unit/test_engine_common.py` walks the engine with `ast` and fails on any capability defined
twice that is not on a documented allowlist — and it fails with the file and line numbers.

Two design points worth keeping:

- **Module- and class-level definitions only.** The first version counted nested closures and reported
  `extract` as duplicated in `ai/client.py` — a false positive: those are two private local walkers inside
  two different static methods. Counting closures would have trained the team to ignore the guard.
- **The allowlist is itself asserted** (`test_allowlist_is_still_accurate`): an entry that stops being
  duplicated must be deleted, so the allowlist cannot quietly grow into a blanket excuse.

## Verification (mutation, not assertion)

| Check | Result |
|---|---|
| `pytest tests/unit/test_engine_common.py` | **6 passed** |
| Mutation: append a second `count_distinct` to `app/engine/dedupe/blocking.py` | **1 failed** — `count_distinct: blocking.py:86, blocking.py:98` (both locations named) |
| Restore the file | **6 passed** again (byte-checked: file ends at `return len(seen)`) |
| Non-vacuity | `test_engine_walk_is_not_vacuous` pins >150 function names, >40 modules, and the presence of `evaluate_exc_*` — a broken glob cannot make the guard pass silently |

## Owed (not hidden)

1. **`engine/common/` itself** — blocked on `TB-016` (mypy) + `TB-014` (import-linter) as designed. It should
   host the *new* shared digest helper, not re-export existing ones.
2. **One hashing helper for subject-key digests** — 12 ad-hoc `hashlib.sha256` call sites
   (`imports/`, `exports/stamps.py`, `rules/acceptance.py`, `store/period_repo.py`, `security/sanitizer.py`, …).
   That is the real consolidation `TB-026` wants; it needs an owner and a migration that touches import
   boundaries, so it is **not** started under this claim.
3. **`split_sentences` / `check_banned_phrases`** — genuine duplicates, listed on the test's allowlist with
   `FOLLOW-UP` in the reason so they cannot be forgotten. Suggested owner: `opencode` (ai lane).