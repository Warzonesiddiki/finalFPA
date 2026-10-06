# DOC-01 — Packaging notices audit (adopted-source licences reaching the payload)

**Date:** 2026-10-05 · **Author:** buffy (leader) · **Task:** `DOC-01` · **Claim:** `buffy-20261005T1210Z-0a58`

## Question

Does the file that actually ships — `THIRD_PARTY_LICENSES.txt` in the installer payload — carry a
licence notice for every third-party source whose **code** is inside the binary? `docs/15` step 4a says
it must, because copied source is not a distribution dependency: neither `pip freeze` nor an SBOM lists
it, so the notices file is the only place a user's obligation is discharged.

## What the audit found (measured, not assumed)

| # | Finding | Evidence |
|---|---|---|
| 1 | **The payload notices file carried no adopted-source notices at all.** It listed only Python/Node packages — no `WS-02`/`ADP-001`, no Apache-2.0 text — while `app/engine/pptx_fill/**` (Apache-2.0, CC0-1.0 and MIT sources) ships inside the binary. | `packaging/THIRD_PARTY_LICENSES.txt` before this change: 81 lines, zero `WS-`/`ADP-` matches; `build.build_licence_text` had only Part 1 (bundle `dist-info`) and Part 2 (`ui/package-lock.json`) |
| 2 | **The generator was the only source of the payload file**, so fixing the checked-in copy alone would have been undone by the next build. | `scripts/build.py:501` `licences.write_text(build_licence_text(root, payload), ...)` — the checked-in `packaging/…` copy is not what ships |
| 3 | **No gate would have caught it.** `license_gate.py` had five checks; none inspected the payload notices. | `scripts/license_gate.py` header, checks 1–5; `grep ADP- scripts/license_gate.py` → nothing before this change |
| 4 | Apache-2.0 §4(a)/(d) requires the licence copy and NOTICE to travel with the distribution, so this was a live compliance gap, not a documentation nicety. | licence text reproduced in `THIRD_PARTY_NOTICES.md` (WS-02 section) |

## The fix (three layers, all machine-checked)

1. **Generator** — `build.build_licence_text` appends *Part 3 — Adopted source (copy-edit) notices*,
   built by `_adopted_source_notices()` which copies the `## WS-nn` sections of
   `THIRD_PARTY_NOTICES.md` **verbatim**. If that file is missing the payload says so in words rather
   than silently shipping without a notice. Derived, never hand-written: the payload cannot drift.
2. **Gate** — new `CHECK 6` in `scripts/license_gate.py`. It runs the *real* generator into a temp
   payload, collects every `ADP-nnn` cited by an `Adapted from` header in `app/`, `ui/`, `packaging/`,
   and fails if any is missing from the generated text. Wired into `scripts/check.py` automatically
   (it is the same script).
3. **Records** — `docs/15` step 4a amended with the enforcement note; the checked-in
   `packaging/THIRD_PARTY_LICENSES.txt` gained a matching *4. Adopted Source (Copy-Edit) Notices*
   section with each upstream commit SHA, plus `BD-001` (built in-house — no notice required, and the
   gate correctly does not ask for one).

## Verification

```
python -m pytest tests/unit/test_gate_license.py -q -o addopts=""   ->  3 passed
python scripts/license_gate.py                                     ->  exit 0 (six checks)
python scripts/check_doc_integrity.py                              ->  exit 0
```

`tests/unit/test_gate_license.py` is written to falsify, not to pass:

- `test_check_6_passes_on_this_tree` — the real tree is clean;
- `test_check_6_fails_when_an_adopted_notice_is_missing` — a temp repo with a stripped notices file and
  one shipped `Adapted from … ADP-001` header makes CHECK 6 return 1 and name `ADP-001`;
- `test_gate_main_runs_six_checks` — `main()` actually executes all six.

## Boundaries

- No upstream code was copied for this task (nothing to gate); the notices text is mirrored from the
  repo's own registry, so `L2`/`L3` are satisfied by construction.
- The dev-only tool list in the checked-in file (pytest, ruff, mypy, PyInstaller) is deliberately left
  in place: `docs/15` step 4a forbids dev tools in the *runtime* section, and these sit in their own
  numbered section, while the shipped file is generated from bundle `dist-info` where they cannot
  appear at all. That was checked, not assumed (Part 1 is read from `_internal/*.dist-info`).
