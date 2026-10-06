# HO-nnn — <task id + short title>

> Copy this shape (or generate it: `python scripts/team.py handoff --claim <id> --summary … --changed … --tests … --docsync … --evidence … --next …`).
> `team.py check` fails a handoff missing any of the six sections below.

## Claim
- claim: `<agent>-<ts>-<hex>` · task: `TB-nnn` / `T-nnn` · author: `<agent>`
- scopes: `<path>`, `<path>`
- opened: `<utc>` · handed off: `<utc>`

## Changed
- `<path>` — what changed and why (one line each; real paths only)

## Verification
- `<exact command>` → `<raw result: N passed / exit 0 / measured number>`
- what was **not** verified and why (never leave this empty if something is open)

## Doc-sync
- Addon 6 §8 rows touched: `32` (`BD-nnn`/`ADP-nnn`) · `09` (ADR) · `18` (DEC/OQ) · `CHANGELOG` · `14`
  (coverage) · `33` (TB) · `STATE` · `SESSION_LOG` — or `docs-only: no behaviour change` / `no adoption:
  no notices owed`.

## Evidence
- `evidence/<slug>/<file>` (must exist on disk) — or `none (docs-only)`

## Next
- the single next action, and who should take it

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above, pastes the raw result, then
`python scripts/team.py verify --task <id> --by <agent> --handoff HO-nnn --note "<what was reproduced>"`)_
