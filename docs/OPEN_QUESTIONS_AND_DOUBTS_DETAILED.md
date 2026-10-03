# Open Questions & Doubts — Detailed Dossier (continue nonstop, zero compromises)

> Status: Living dossier supplementing `docs/18` OQ/DEC registers. Owning docs win on conflict (`00` §6).
> Last updated: 2026-10-03. Author: builder session. Contract: kickoff + Addons 1–5 + audit prompt.
> Purpose: every doubt with context, owning-doc quote, ≤3 options + trade-offs, recommendation, default if unanswered, owner, gate impact, reversibility, tier. No silent defaults on money/data-loss/scope.

## How to use this file
- Tier C items: STOP the thread, escalate, continue next non-blocking task (`Master Brief` §4).
- Tier B items: apply documented default, log `DEFAULT APPLIED`, owner reverses async.
- Tier A items: decide alone, log in SESSION_LOG.
- Closing an item = owning-doc update + CHANGELOG + test/evidence + `docs/20` traceability where FR-touched (`19` §5.1).

---

## D-01 — GL corpus balance fix (Option B rebuild vs plug vs defer) — DECIDED per delegation
- Context: `sample-data/d365_gl_actuals.csv` 250,037 rows, debit 24,626,607,267.80 / credit 6,682,091,688.47 / residual 17,944,515,579.33. All entities imbalanced (IN01 14.33B, IN02 2.17B, US01 1.45B). IMP-023 fails, 0 FactActual rows commit, harness BLOCKED.
- Owning quotes: `04:343` "Debit=credit at minor-unit precision per file, per entity, per period, overall"; `03:184-207` only 1010/1200/2000 offsets, no new account; `06:646-662` EXC-024 watches suspense with 100k floor; `CHANGELOG:167-177` plug ruled out.
- Options: (A) Single suspense plug to 1999 — 1-line, trivial; TRIED-AND-REJECTED: 17.9B/100k = 179,445x floor, corrupts P24 (1.24M → ~17.94B), violates per-entity rule, trips EXC-002 if new code. (B) Double-entry voucher rebuild — RECOMMENDED: balanced pairs per voucher/entity/period, routine 1999=0, plants stay unbalanced by design + harness whitelist. Cost: generator edit + trial-balance green + regression test. (C) Defer — harness stays BLOCKED, GATE-13 shut.
- Recommendation: B. Default if unanswered: B (spec-mandated; plug is spec violation, not a valid default).
- Owner: Data Lead. Gates: GATE-13 hard-block; harness exit 2 until landed. Tier: B (spec-settled). Reversible: yes (regenerable corpus).
- Status: FIX LANDED 2026-10-03 (generator verified, CHANGELOG entry, `tests/unit/test_def019_double_entry.py` 5 green, `docs/28` DEF-019 → Fixed-pending-confirmation). Committed corpus NOT yet regenerated (needs owner decision per seed provenance DEC-055). Crew dispatched.

## D-02 — DEF-010 sub-ledger gate (universal reject vs spec amendment) — DECIDED
- Context: `import_repo.py:40` `should_commit = is_balanced or source_type != actuals_d365` commits bank 499/499, payroll 399/399 while `04:314` IMP-023 + `04:330-333` demand unconditional reject. Audit metadata now honest (`committed`,0) but spec contradiction remains.
- Owning quotes: `04:314` "Scope=F, On failure: Reject"; `04:330-333` "Nothing is committed"; `19:249-251` spec wins, silent divergence = violation.
- Options: (A) Code-to-spec RECOMMENDED: `should_commit = bool(batch.is_balanced)` all types; update `test_def010...:161-178` + add TST-IMP-023-R1. (B) Spec amendment: IMP-023 → Warn for sub-ledgers + §11 table + weight change; needs owner approval + CHANGELOG. (C) Leave divergent — forbidden by 19 §5.5.
- Recommendation: A. Default: A. Owner: Backend + Owner (ruling recorded). Gates: GATE-13/14 S1 zero-bar. Tier: B. Crew dispatched.

## D-03 — Finding.identity_hash basis (engine vs catalog IDs) — DECIDED
- Context: 8/24 rules diverge (`batch.py:60-71`, `rules_01_08.py:1-12`). Hash = SHA-256(rule_id|subject_key) (`rules_01_08.py:63-67`); catalog ID stored alongside, excluded. Switching re-hashes 8 rules, invalidates filed tie-out identity evidence.
- Owning quotes: `06:70`, `03:81,487` identity def; `STATE.md:53-54` default-keep rationale.
- Options: (A) Keep engine IDs through freeze RECOMMENDED — no churn, acceptance papers over via `_catalog_id()` (`acceptance.py:680-687`). (B) Switch now — catalog-stable but voids evidence, needs re-baselining + CHANGELOG + DimRule seed.
- Default: A. Owner: Owner (revisit post-handoff). Gates: none blocking now. Tier: B.

## D-04 — DimVendor + budget CSV loader (build vs spec-out) — DECIDED
- Context: vendor-keyed rules (EXC-014) + FactBudget need loader; STATE.md open decision 2.
- Options: (A) Minimal loader RECOMMENDED — parse/validate/atomic commit/audit; unblocks P0 rules; small. (B) Spec vendor-keyed rules + FactBudget out of v1 as documented-not-built — needs `02`/`06` amendment + `27` entries.
- Default: A (smaller honest scope than spec surgery). Owner: Backend. Gates: rule measurability. Tier: A/B. Crew dispatched.

## D-05 — Live DB residue purge (Tier C)
- Context: `28:448-455` — 62k bank-ledger rows + ~150 test rows mixed in live user dir, indistinguishable. No longer growing after isolation fix.
- Options: (A) Snapshot both files to timestamped backup, purge by batch threshold. (B) Leave residue, document as known contamination. (C) Selective void via Import History UI.
- Recommendation: A with backup-first, owner-confirmed batch list. Default: NONE (irreversible — must not auto). Owner: Owner + Data Lead. Gates: DEF-006 closure hygiene. Tier: C.

## D-06 — Signing certificate (Tier C)
- Context: `09 ADR-003`, `Q-015`. Unsigned PyInstaller → SmartScreen friction; `15 §8` ladder.
- Options: (A) Buy cert (cost/lead-time). (B) Ship unsigned + published SHA-256 + walkthrough. (C) Portable-zip only for pilot.
- Recommendation: B for pilot, A decision before go-live. Default: B (reversible). Owner: Owner. Tier: C (spend + client-visible).

## D-07 — Pilot inputs (Tier C)
- Context: `OQ-014` no default — sanitized real month (D365 + 2 systems), manual pack, tie-out session booking. Fallback per DEC-053/RISK-002 active.
- Options: (A) Client sends sanitized month by date X. (B) Run UAT on sample data with written limitation, tie-out as first post-go-live activity.
- Recommendation: push A, plan B as fallback week (`16 §12` row 10). Default: none (client fact). Owner: Client finance + Owner. Gates: GATE-13 entry 1/3/6. Tier: C.

## D-08 — EXC-011 cap + branding assets
- Context: volume-cap false positives on extreme batches (DEF-001); logo/banner missing (DEF-005 S3).
- Options: cap tune in `06` first (spec→config→tests) vs hide rule (forbidden); branding defaults from `01` until assets arrive.
- Recommendation: tune thresholds in `06`, keep rule enabled; branding defaults applied, assets when received. Owner: Engine + Client. Tier: A/B.

## D-09 — Support/UAT scheduling + OQ-016 targets (Tier C)
- Context: `23 §10/11` response targets unconfirmed; UAT ≤5 days needs analyst + accounting owner (`28 §5.1`).
- Options: confirm defaults vs replace numbers; schedule primary + fallback week.
- Default: labelled defaults stand until OQ-016 answered. Owner: Owner + Client. Tier: C (client commitment).

## D-10 — Installer delivery + rollback (Tier C)
- Context: secure channel + SHA-256 (`24 §7`); rollback restore-only (`24 §6.4`, `28 §6` item 11).
- Options: secure link vs in-person handoff; backup location agreed.
- Owner: Owner + Client IT. Tier: C (external delivery).

## D-11 — DEF-012 catalogue disposition (S1 docs)
- Context: 267 cited / 2 mechanically tagged (`test_rules_01_08.py:64,147`); 244 untagged. DEF-017 forbids mass re-tag (unearned ID = hidden lie).
- Options: (A) Re-label `14 §4` planned-vs-as-built + appendix + DEC-054 RECOMMENDED (~4h docs). (B) Back-tag 540 tests (1.5-2d, laundering risk). (C) Write 244 tests (5-8d, pre-freeze impossible).
- Default: A pending owner concurrence. Owner: QA Lead + Owner. Gates: `30 §2` step 4 join. Tier: B.

## D-12 — DEF-014 DEC hygiene
- Context: duplicate remediated (`18:386` DEC-046, `18:387` DEC-054); `20 §6.6` rows present; residual: `18:385` DEC-055 out-of-order, DEC-055 untraced in `20`, stale headers (`18:12`), stale FAIL texts.
- Recommendation: move DEC-055 to tail, add `20 §6.6` row, refresh counts, mark old reports superseded. Owner: Docs/QA. Tier: A.

## D-13 — DEF-016 UAT expectations
- Context: `test_uat_dry_run.py:71-78` self-seeded literals; real acct 4000 = 190,778,680.37 not 12.5M. Blocked behind DEF-019 (corpus imbalanced → BvA BLOCKED).
- Options: (A) Corpus-derived expectations via helper (recommended post-DEF-019). (B) Interim re-scope to pack-assembly-only + strip TST-UAT labels.
- Default: B until DEF-019 lands, then A. Owner: QA Lead. Gates: GATE-14. Tier: B.

## D-14 — DEF-018 PPT wiring
- Context: Slide 1 migrated (`ppt_pack.py:487-495`); slides 2-6 `slide_layouts[6]` + procedural; `ERR-EXP-014` 4 hits in app, 0 in tests; `ppt_spec.py` absent.
- Options: (A) Convert slides 2-6 to named-layout + `_resolve_shape` + guards + `ppt_spec.py` (full close). (B) Minimal: guards + 1 regression test pinning Slide 1 + document remainder as known gap.
- Recommendation: A (cross-artifact never-cut); B only if freeze forces phasing with waiver. Owner: Backend/Docs. Gates: parity evidence void until fixed. Tier: A (B needs waiver = C).

## D-15 — Coverage phantoms + domain gaps
- Context: evidence claims `formulas.py` 94.1%, `registry.py` 100% — files absent; `math.py` 87.0%, `guardrails.py` 84.2% below 90 bar.
- Options: (A) Fix evidence + `14` wording to as-built + close gaps with tests RECOMMENDED. (B) Restore phantom files (wrong direction).
- Owner: QA/Engine. Gates: NFR-014. Tier: A.

## D-16 — API contract drift (95 routes)
- Context: ~34/95 implemented (aliases violate `26:224`, envelope non-compliant, `X-Session-Token` vs `X-FPA-Token`, no 202-job, drift script narrow).
- Options: (A) Narrow v1 contract to as-built + freeze remainder as Later (needs `26` amendment + owner). (B) Implement missing 60 routes (large).
- Recommendation: A for v1 + `27` entries. Owner: Owner + Engine. Tier: B (A needs approval).

## D-17 — Security unbuilt (DPAPI/log/diagnostics/scans)
- Context: env-var key + `masked_key` fragment violates SEC-010; no scrub filter/rotation; diagnostics stub; no `check-secrets`/CI.
- Options: cheapest-first — (1) remove fragment + commit `.gitignore` + patterns, (2) `check-secrets` + pre-commit, (3) DPAPI envelope + purge test, (4) real diagnostics builder, (5) log filter + rotation.
- Owner: Backend/Security + Owner. Gates: UAT trust. Tier: A (code) / C (only if scope cut).

## D-18 — EULA + installer.iss gaps
- Context: `EULA.txt` has placeholder; `.iss` no LicenseFile page, hard-coded version/outdir, missing components/HKCU/metadata.
- Recommendation: legal text from `01 §15.1` owner-approved; fix `.iss` version derivation + components. Owner: Owner (legal) + Release Eng. Tier: B/C.

## D-19 — DEF-013/020 governance + pointer drift
- Context: DEF-013 guard green but no §12 row; DEF-020 process-only; `16 §1.3` GATE-07 vs `00 §10`/STATE pilot-blocked; `CHANGELOG` dual approval records; stale `501`/`73MB` figures.
- Recommendation: add/withdraw rows via `28` change control; advance/reaffirm `16 §1.3` in same commit as work; append-only corrections in SESSION_LOG (never rewrite). Owner: Docs/QA + Owner. Tier: A.

## D-20 — Console UTF-8 crash (new)
- Context: `scripts/acceptance.py:82` `print(render_markdown)` crashes cp1252 on ₹ (exit 1 vs designed 2). Verified twice.
- Recommendation: `PYTHONUTF8=1` guard or UTF-8-safe write in script (Tier A, small). Owner: QA. Tier: A.

---
---
## Ratifications 2026-10-03 (owner)
- D-01..D-04 ratified as decided (plug dead; universal reject; engine IDs + backlog trigger; minimal loader, nothing beyond).
- D-05: option A threshold-purge REJECTED. Sequence: verified snapshot (restore spot-check) → keep-list 62k by batch ID → proven-test deletes with manifest → remainder via Import History selective void (contract-native) → counts+manifest to evidence/ → root-cause stays open. No hard delete without proof.
- D-06: B pilot (unsigned + SHA-256 + walkthrough + ADR-003); cert at go-live; not C.
- D-07: pursue A (owner chases date), schedule on Stage A row-10 timeline regardless; real month = Stage B trigger.
- D-08: tune in 06 first within four rails + effectiveness evidence; hide-rule forbidden. Branding defaults now, Settings on arrival.
- D-09: labelled defaults stand till OQ-016 at go-live; participants per 28 §5.1; Stage A when gates green.
- D-10: expiring link + out-of-band SHA; restore-only rollback; backup/channel = owner+client IT action.
- D-11: approve re-label + appendix + DEC-054 WITH never-cut guard: list core 244 first; unwritten core gets built.
- D-12: approved (DEC-055 tail, 20 §6.6 row, refresh, supersede marks; never renumber refs).
- D-13: staging accepted, GATE-14 exit still requires corpus-derived A; strip partial TST-UAT labels now.
- D-14: full close, no waiver (slides 2-6 + ppt_spec.py + ERR-EXP-014 tests).
- D-15: split — (1) evidence integrity now (clean coverage, as-built wording, phantom finding); never restore files. (2) math.py 87.0% + guardrails.py 84.2% → tests to ≥90.
- D-16: owner approves active-34 contract + envelope/X-FPA-Token fix + drift on active set + 60 to backlog as planned-not-implemented; 26 amendment + CHANGELOG.
- D-17: all five pre-UAT in order; step 1 today (fragment = live exposure; history check; revoke/rotate + Tier C if real keys); AI-key path disabled till step 3.
- D-18: engineering now (.iss version/outdir/metadata/components); LicenseFile vs placeholder internal-only; client builds need owner EULA at go-live.
- D-19: register DEF-013; withdraw DEF-020 only with citation + DEC; 16 §1.3 advances only with evidence (else built-pending-certification); refresh 501/73MB; append-only log.
- D-20: approved (UTF-8 guard + exit-code reconcile + regression + ₹ helper).
- Owner queue unchanged: D-07 date chase, D-09 UAT dates at Stage A, D-10 backup/channel, D-18 EULA by go-live, D-06 cert at go-live, D-08 branding optionally for UAT.
- Process flag: fresh-clone scripts/check + D-01..D-04 evidence + session reports verification queued before next dossier.

*Teams: 60+ subagents used (30 pre-restart + 30 post + 3 fix crews). Evidence before synthesis; red items never omitted; no test weakening; docs-first per `19 §5`.*
