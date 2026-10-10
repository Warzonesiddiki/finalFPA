# Pending-items analysis — 2026-10-10

Working note, not a deliverable. Compiled from the spec record (`docs/00`–`33`),
the acceptance evidence, and `scripts/team.py` status on this checkout.

Branches:
- `Branches: No branches to show.` was empty in the repo summary, so I treated the
  tree as a single main-line checkout and did not branch-hop.

All numbers below are recomputed on this checkout, not paraphrased from any artifact.

---

## Acceptance / corpus evidence layer (the hinge)

### Pending item A — acceptance evidence artifact is internally coherent but stale vs corpus

- `evidence/acceptance_report.json` `checksum_scope.sha256`: **56 paths**
- `sample-data/` files matching `.csv/.json/.xlsx`: **56**
- **matched: 33**
- **manifest != disk: 23**
- **in manifest but not on disk: 0**

Drift by role:
- primary: **6/6** mismatched — all top-level corpus files on disk differ from manifest
- import_history: **4/5** mismatched
- malformed: **4/16** mismatched (12/16 still match the manifest)
- templates: **0/4** mismatched
- test_scale: **9/25** mismatched

Why this is not “just recompute 23 checksums”:
- The manifest is **partially fresh**: templates match and most malformed files match.
- The artifact’s own run metadata does **not** match the M1 seal profile: `as_of` is
  `2026-11-12`, `elapsed_seconds` is `23.8`, `findings_total` is `50`. The board wants
  M1 to be a current-code, current-corpus, twice-run, identical-raise-set seal recorded in
  that same artifact (`docs/33` §5.2 `TB-012`).
- `docs/14` §5.2 (amended 2026-10-06) fingerprints `.csv/.xlsx/.json` by relative path
  with **no recognized data artifact excluded**, and explicitly says there is still **no
  committed golden corpus checksum**, so the manifest is a run fingerprint, not a golden
  constant. The literal §5.2 step 1 “regenerate + assert the generator’s own checksum” is
  still an explicit compliance gap.

So the pending item is **not** “update 23 checksums.” It is one of:
1. Refresh this artifact from the current corpus under the current harness and re-record it
   as the current acceptance evidence, with a current `as_of`/elapsed/findings profile; or
2. Mark the current artifact as superseded by a newer run and cite the newer one; or
3. Document that the existing artifact is authoritative for the verdict only and that its
   checksum scope is stale by design until a fresh re-run.

The right choice is a decision, not a checksum edit.

### Pending item B — two acceptance evidence artifacts agree with each other

Verified: `evidence/acceptance_report.md` corpus table and `evidence/acceptance_report.json`
corpus array agree on rows loaded, debits, credits, net imbalance, status, and DQ score for
all 7 files. The checksum drift is evidence-vs-corpus, not evidence-vs-evidence. This is
good — it means the evidence layer is not internally contradicted; it is just stale against
the current tree.

### Pending item C — test_scale/ is not a clean mirror on this checkout

20/25 `test_scale/` mirrors already differ from their primaries on disk. If `test_scale/`
is supposed to be a mirror layer, that is its own pending data-hygiene item. If it is not
supposed to be a mirror, the manifest and any report narrative that implies it is need
correction.

---

## GATE-13 approval path (M6 hinge)

- `docs/28_GATE13_PACKET.md`: assembled, 5 executive bars marked PASS, evidence links present.
- `evidence/gate13_decision_packet.md`: assembly note says DOC-08 complete and packet ready.
- `docs/28` §4.6.5: sign-off still **unsigned** (Client Finance Owner / Lead Consultant / Project
  Owner all blank).
- `docs/00` line 386: GATE-13 approval still **Pending**.
- `docs/33` §5.7: `TB-045` is **🚧 blocked on `TB-043`** (real-data pilot tie-out).

So the packet exists; the approval does not. The blocker is upstream: `TB-043` is blocked on a
sanitized real month (`OQ-014`/`A29`), and the fallback pilot exists but is explicitly a
limitation-notice rehearsal, not the approved pilot sign-off.

Pending: decide whether to advance the fallback-rehearsal record toward a documented limitation
state, or wait on real-data inputs. That is an owner decision, not an engineering edit.

---

## Quality infrastructure (M2)

Still open board items that keep `scripts/check` from being a green, complete gate:
- `TB-014` import-linter not configured
- `TB-015` ruff not wired
- `TB-016` mypy not wired
- `TB-017` eslint/tsc not verified in gate
- `TB-018` ADR-002 pins not fully landed
- `TB-019` `scripts/dev` and `scripts/release` not created
- `TB-020` perf/bar suite not green
- `TB-021` xlsx determinism normalization + pinned runtime still pending
- `TB-022` full green `scripts/check` transcript not attached

Plus the live P0 `GATE-FAST` card (in-progress): `scripts/check.py` is fail-fast and hides the
five `docs/14` §5.3 bars. The digest states this and measures it.

---

## Defect burn-down (M3)

Still open in `docs/28` §12 / defect log: `DEF-015` (float money paths), `DEF-016` (UAT
tautology), `DEF-017` (`tst` marker), `DEF-012`/`DEF-014` (traceability), `DEF-011` consequence
(installer rebuild with real assets). The `TB-030`–`TB-035` family is the closure path.

---

## Architecture alignment (M4)

Still open in `docs/33` §3 gap inventory: `app/jobs/` does not exist (`G-12`), CLI commands still
missing (`G-11`), `scripts/dev`/`scripts/release` still missing (`G-15`), code-health sweep still
open (`G-14`). `engine/common/` is accounted as closed in §5.8.

---

## Verification backlog (team layer)

Live on the board: `VERIFY-01/02/03` plus multiple review cards waiting on independent
verification with recomputed numbers. `scripts/team.py status` shows 1 active claim (`buffy` /
`UX-19`) and 2 stale `hermes` claims; working-tree edits not covered by an active claim: 287.

That 287 is its own pending hygiene item: before anything else lands, the checkout needs a claim
map that actually covers the paths being changed, or the changes need to be abandoned/backed out.

---

## Bottom line

The project is in the **“an acceptance artifact reads PASS and is internally coherent, but the live
gate is not sealed and the evidence layer is not reconciled with the current corpus”** state.

The smallest honest next move is not “start working on all pending.” It is:

1. **Decide the acceptance artifact question** (A above) — that unblocks the hinge for everything
   after it.
2. **Fix `GATE-FAST`** so the §5.3 bars are visible again — right now the gate can hide red bars.
3. **Decide the `test_scale/` mirror question** (C above) — otherwise any manifest refresh is
   rebuilding on top of a layer that is already inconsistent.
4. **Decide the GATE-13 path** (fallback-limited rehearsal vs wait-for-real-data) — the packet is
   written, the approval is not, and the blocker is upstream.
5. **Map or clear the 287 unclaimed working-tree edits** before any further integration work lands.

Numbers only; no adjectives.
