# LEAD-03 control fixture — a DELIBERATELY FABRICATED citation

This file exists to prove that `scripts/open_cited_lines.py` can fail. It is
**not** an audit and must never be cited as evidence. Every row below asserts
something about a line that does not say it.

The rows are shaped exactly like the honest control in
`evidence/ops/lead-03-honest-control.md`, so that the only difference between a
false report and a true one is whether the claim is on the line.

| Fake Screen | Claimed on the cited line | Verdict | Component File & Line |
|---|---|---|---|
| `FAKE-001` | `role="main"` | Conforming | `ui/src/main.tsx:145` |
| `FAKE-002` | `role="dialog"` | Conforming | `ui/src/components/import/PreScanModal.tsx:1` || `FAKE-003` | `LOCK_TIMEOUT=999` | Conforming | `scripts/memory.py:83` |
| `FAKE-004` | `RENDER_LIMIT=999` | Conforming | `scripts/memory.py:87` |

Four rows, so the command's default `--limit 4` exercises the "open four citations" path on a
report that is false in every row.

`FAKE-003` is the row that matters. Its file is real, its line number is in range, and the line is not blank — it reads `LOCK_TIMEOUT = 60.0`. The claim is merely wrong. A checker that verified only "the file exists" and "the line is within the file" would pass it, and that is precisely the check `verify_audit_citations.py` performed when it reported PASS on three fabricated audits.

`FAKE-001` and `FAKE-002` are the real thing, lifted from the rejected HO-031
matrix, and they fail for the same reason: the cited line does not contain the
attribute the row asserts.

Citations in this file deliberately point at `scripts/memory.py` and `ui/src`
rather than at `scripts/open_cited_lines.py`, because a fixture that cites a
line number in a file under active development drifts the moment that file is
edited — and a fixture that silently drifts is a fixture that starts lying.
