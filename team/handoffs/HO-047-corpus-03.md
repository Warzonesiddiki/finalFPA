# HO-047 — Fault injection: a command that corrupts the corpus in a named, documented way (drop a planted finding, duplicate a batch, unbalance a control total) and asserts the tool catches each one. This is what separates a rule that fires from a rule that happens to fire on this fixture. Acceptance: the injected defect name, the expected detection, and the exit code, for each

## Claim
- claim: `freebuff2-20261005T1531Z-f02e` · task: `CORPUS-03` · author: `freebuff2`
- scopes: `scripts/inject_fault.py`
- opened: 2026-10-05T15:31:03Z · handed off: 2026-10-05T19:29:48Z

## Changed
scripts/inject_fault.py

## Verification
python scripts/inject_fault.py --fault p18-below-absolute-floor -> CAUGHT (findings 45->44, misses 11->12, P18/EXC-018 newly missed); --fault p8-duplicate-line-floor-above-amount -> CAUGHT (findings 45->45, misses 11->12, P8/EXC-008 newly missed); sample-data/ SHA-256 verified byte-identical after every run

## Doc-sync
none - new tool, no spec change

## Evidence
Fault injection for the planted-exception corpus. A rule that fires on a fixture is not the same as a rule that fires because it is right; this command corrupts the corpus in NAMED ways and asserts each corruption costs exactly the detection it was predicted to cost.

scripts/inject_fault.py --fault <name> (repeatable; default all six) [--json PATH] [--sample-dir DIR] [--period] [--as-of]
Exit 0 when every fault behaved as predicted, 1 when any did not, 1 on an unusable run. The real sample-data/ is copied per fault into a temp dir and never written to.

## Fault table (doc 14 §5.2 / CORPUS-03 acceptance: defect name, expected detection, exit code)

FAULT                                      EXPECTED DETECTION                          EXIT
p18-below-absolute-floor                   P18 stops being recalled                     0
p8-duplicate-line-floor-above-amount       P8 stops being recalled                      0
p21-drop-dual-approval-voucher             P21 stops being recalled                     -
p6-budget-the-unbudgeted-entity            P6 stops being recalled                      -
p29-control-over-absolute-floor            control P29 starts firing                    -
p30-control-over-percentage-leg            control P30 starts firing                    -

MEASURED end-to-end this session (2 of 6; see the caveat below - I am not claiming the rest):
  BASELINE on the clean corpus: 45 findings, 11 misses, verdict FAIL
  [CAUGHT] p18-below-absolute-floor
      budget FY26-P09/IN01/CC-100/5200 -> 10700000.00 (actual 10540000.00, var +160000.00 = +1.50%)
      observed: findings 45 -> 44; misses 11 -> 12; newly missed P18/EXC-018
  [CAUGHT] p8-duplicate-line-floor-above-amount
      budget FY26-P09/IN01/CC-110/5300 -> 30000000.00 (EXC-008 min_amount becomes 7200000.00)
      observed: findings 45 -> 45; misses 11 -> 12; newly missed P8/EXC-008

Both are balance-neutral single-field budget edits, so each changes exactly one number and nothing else. Each one costs its planting and nothing else - a false-positive storm or a BLOCKED run would have shown up as extra misses, and neither did.

## The design lesson that mattered, and the safeguard it forced

My first P8 fault edited the GL amounts (500000.00 -> 499999.00). It reported CAUGHT - and for completely the wrong reason. P8's vouchers are single-sided (they are part of the planted residual the FIX legs balance at month level), so the edit unbalanced the whole file, the batch was rejected, the run went BLOCKED, and EVERYTHING became missed. The assertion "P8 must stop being recalled" was satisfied by a broken corpus rather than by a rule doing its job.

So the harness now treats an unusable run as a hard failure, never a pass: if the run is BLOCKED or not measurable the fault is INVALID, the blocked reasons are printed, and it counts toward failure. That case was observed and rejected as INVALID before the fault was redesigned.

And the faults were redesigned to be balance-neutral: the P8 test is now a BUDGET edit that lifts EXC-008's max(500000, 2% x account budget) threshold above P8's amount, which tests the documented floor instead of unbalancing the ledger.

p29/p30 are the mirror pair and are the most informative of the six: they are the two precision controls on the SAME rule, and they isolate EXC-018's AND-test into its two gates. Lowering CC-105's budget so the variance clears 500000 (820000, +12.42%) must make the P29 control FIRE. Lowering CC-110's budget so the variance clears 5% (2900000, +7.63%) must make the P30 control FIRE. A control that cannot be made to fail is not a control, so these assert the opposite direction of the raise-faults.

## Caveat - stated plainly rather than buried

The remaining four faults are implemented and registered but I did NOT get them to complete end-to-end this session. Each fault re-runs the full acceptance harness; on an idle box that was ~90s per fault, but with four agents working the same checkout it measured 9m30s for a SINGLE fault plus baseline, and my command timeout is 10 minutes. So 2 of 6 are measured, 4 are unmeasured. --fault makes them individually runnable; they should be run before anyone cites this as a 6/6 result. I would rather hand over 2 measured than 6 asserted.

Cost note for whoever schedules this: fault injection is inherently expensive because it re-imports and re-runs every rule per fault. The obvious optimisation, reusing one loaded context and re-running rules only over the changed key, is NOT safe - EXC-017/018/019 aggregate across the whole corpus, so the change is not local. A cheaper harness needs a narrower fault surface, not a lazier one.

## Next
qual-05 (determinism: byte-identical findings/hashes/board pack over two runs + a test that fails on non-determinism). Then remaining four inject_fault faults need a quiet box.

## Verification by reviewer
_(required before `done`: a different agent re-runs the commands above and pastes the raw result, then
`team.py verify --task <id> --by <agent> --handoff HO-047 --note "<what was reproduced>"`)_
