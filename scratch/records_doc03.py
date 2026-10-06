"""Record DOC-03 in memory, CHANGELOG, STATE and SESSION_LOG."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def memory(args: list[str]) -> int:
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "memory.py"), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


ENTRIES: list[list[str]] = [
    ["add", "--kind", "state", "--ref", "evidence/release-readiness-dossier.md",
     "--text",
     "DOC-03 done: release-readiness dossier, generated from live gate runs. 3 of 9 gates red "
     "(RUFF-LINT, RUFF-FORMAT, ACCEPTANCE); full unit suite green. Handoff HO-050, record TB-108."],
]

CHANGELOG = (
    "- **Release-readiness dossier, generated from live gate runs (`scripts/release_dossier.py`, "
    "`TB-108`/`DOC-03`):** the page the owner reads to decide ship or not — every gate with its real "
    "exit status, open decisions with their blast radius, licence posture with the git SHA, known "
    "limits as numbers, every line traceable to the command printed beside it. It is a generator "
    "rather than a document because a hand-written readiness dossier is the most dangerous file in "
    "the repo: it is read at ship time, gets composed while the answer is “not yet”, and then sits "
    "unchanged for weeks after the answer moves. **Measured: 3 of 9 gates red** (`RUFF-LINT`, "
    "`RUFF-FORMAT`, `ACCEPTANCE`) against green `LICENCE`, `DOC-INTEGRITY`, `MEMORY`, "
    "`EVID-REGISTER`, `TEAM-CHECK` and the **full unit suite**; both ruff reds are pre-existing and "
    "every file added this session is ruff-clean. **The finding worth more than the document:** "
    "`scripts/check.py` line 12 calls `sys.exit(res.returncode)` on the **first** failed bar, so it "
    "is fail-fast — measured, it exits 1 at Ruff Format and reports nothing after it, which means "
    "the five `docs/14` §5.3 bars are currently **invisible**. They are not passing; nobody can "
    "tell, because the gate stopped. A fail-fast gate answers *which* bar failed first while a ship "
    "decision needs *how many* are red, so the dossier never short-circuits and says so in its own "
    "output — the same shape as the fabricated audits in `TB-104`. It also records that "
    "`evidence/open_decisions.md` declares 18 tracked decisions and lists 2. 11 tests, the "
    "load-bearing one proving a red first gate does not hide the three behind it.\n"
)

STATE_TASK = (
    "RELEASE-READINESS DOSSIER LANDED (TB-108 / DOC-03): evidence/release-readiness-dossier.md, "
    "GENERATED from live gate runs rather than written, because a hand-written readiness dossier is "
    "read at ship time, composed while the answer is 'not yet', and then sits unchanged for weeks "
    "after the answer moves. python scripts/release_dossier.py --slow regenerates; --check fails "
    "when it stops matching the machine. MEASURED: 3 OF 9 GATES RED - RUFF-LINT exit 1, RUFF-FORMAT "
    "exit 1, ACCEPTANCE exit 1 - against green LICENCE, DOC-INTEGRITY, MEMORY, EVID-REGISTER, "
    "TEAM-CHECK and the FULL UNIT SUITE (472.6s). Both ruff reds are pre-existing and repo-wide "
    "(1850 lint errors, 173 files unformatted); every file added this session is ruff-clean and was "
    "checked individually. THE FINDING THAT MATTERS MORE THAN THE DOSSIER: scripts/check.py line 12 "
    "calls sys.exit(res.returncode) on the FIRST failed bar, so it is FAIL-FAST. Measured, it exits "
    "1 at Ruff Format Check and reports nothing after it - so the five docs/14 section 5.3 bars "
    "(recall 11/32, control 1 fired, High 6/18, 422 extras, 14 zero-coverage rules) are currently "
    "INVISIBLE. They are not passing; nobody can tell, because the gate stopped. A fail-fast gate "
    "answers 'which bar failed first'; a ship decision needs 'how many are red'. The dossier "
    "therefore never short-circuits and says so in its own output - the same shape as the fabricated "
    "audits in TB-104, where one uniform verdict stood in for a population nobody examined. Also "
    "measured: evidence/open_decisions.md declares 18 tracked open decisions and lists 2, so the "
    "register does not deliver its own count. 11 tests. docs/33 gains TB-108. "
)

STATE_GATE = (
    "- DOC-03: `python -m pytest tests/unit/test_release_dossier.py -q` -> 11 passed; "
    "`ruff check scripts/release_dossier.py tests/unit/test_release_dossier.py` -> All checks "
    "passed; `mypy scripts/release_dossier.py` -> 0 errors in that file; "
    "`python scripts/release_dossier.py --check` -> current, exit 0; full `pytest tests/unit -q` "
    "-> green (472.6s, measured inside the dossier's own UNIT gate) "
)

SESSION_ADDENDUM = """
## Addendum 9 — DOC-03: the acceptance gate is fail-fast, and it is hiding five bars

**Card:** `DOC-03` (P1, docs lane) · **claim:** `buffy-20261005T2004Z-217d` ·
**handoff:** `HO-050` · **records:** `TB-108`

### Measured: 3 of 9 gates red

```
green  LICENCE 0 (8.2s)   DOC-INTEGRITY 0 (0.6s)   MEMORY 0 (0.2s)   EVID-REGISTER 0 (1.0s)
green  TEAM-CHECK 0 (301.8s)   UNIT 0 (472.6s)
RED    RUFF-LINT 1   RUFF-FORMAT 1   ACCEPTANCE 1
```

The full unit suite is green. Both ruff reds are pre-existing and repo-wide — 1850 lint errors,
173 files unformatted — and every file added this session is ruff-clean and was checked individually.

### What I found while building it

`scripts/check.py` line 12:

```python
print(f"FAILED: {desc} exited with code {res.returncode}")
sys.exit(res.returncode)
```

The gate exits on the **first** failed bar. Measured this pass it exits 1 at Ruff Format Check and
reports nothing after it — so the five `docs/14` §5.3 bars (recall 11/32, control 1 fired, High
6/18, 422 extras, 14 zero-coverage rules) are currently **invisible**.

They are not passing. Nobody can tell, because the gate stopped. And the stop *looks* like a clean
result: a reader sees "1 of 9 red" when the truth is "unknown, with at least 6".

A fail-fast gate answers *which bar failed first*. A ship decision needs *how many* are red. Those
are different questions, and only the second one is decision-relevant. So `release_dossier.py`
deliberately **never short-circuits**, and prints that fact in its own output.

This is the same shape as the fabricated audits in `TB-104`: one uniform verdict standing in for a
population nobody examined. It took three rejected audits to learn it for evidence; the acceptance
gate has been doing it silently all along.

### Two more measured facts

- `evidence/open_decisions.md` declares **18** tracked open decisions and lists **2**. The register
  does not deliver its own count.
- 8 handoffs authored by `antigravity` are unreachable by any rotation: the seat is AWAY and cannot
  verify its own work.

### What the dossier deliberately does not do

It reports gate **exit status**, not gate **adequacy**. A gate that exits 0 proves only that it ran,
and three audits this session exited 0 on fabrications. Section 7 of the dossier says so rather than
implying full coverage, and skipped gates are labelled as not-passing rather than quietly omitted.

### Gates

```
pytest tests/unit/test_release_dossier.py -q   -> 11 passed
ruff check (script + tests)                     -> All checks passed
mypy scripts/release_dossier.py                 -> 0 errors in that file
pytest tests/unit -q                            -> green (472.6s)
python scripts/release_dossier.py --check       -> current, exit 0
```
"""


def main() -> int:
    rc = 0
    for e in ENTRIES:
        rc |= memory(e)
    print("--- render ---")
    rc |= memory(["render"])
    print("--- verify ---")
    rc |= memory(["verify"])

    log = ROOT / "CHANGELOG.md"
    text = log.read_text(encoding="utf-8")
    anchor = "- **Verification is a rotating duty"
    assert anchor in text, "CHANGELOG anchor missing"
    log.write_text(text.replace(anchor, CHANGELOG + anchor, 1), encoding="utf-8")

    state = ROOT / "STATE.md"
    out = []
    for line in state.read_text(encoding="utf-8").split("\n"):
        if line.startswith("TASK: "):
            out.append("TASK: " + STATE_TASK + line[len("TASK: "):])
        elif line.startswith("LAST_GATE: "):
            out.append("LAST_GATE: " + STATE_GATE + line[len("LAST_GATE: "):])
        else:
            out.append(line)
    state.write_text("\n".join(out), encoding="utf-8")

    slog = ROOT / "docs" / "SESSION_LOG.md"
    s = slog.read_text(encoding="utf-8").rstrip("\n")
    if "Addendum 9" not in s:
        slog.write_text(s + "\n" + SESSION_ADDENDUM, encoding="utf-8")
    print("CHANGELOG.md, STATE.md, docs/SESSION_LOG.md updated")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
