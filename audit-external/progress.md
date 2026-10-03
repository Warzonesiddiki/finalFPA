# Audit-external progress log

Auditor: independent contributor-auditor (outside the main team).
Writes only under `audit-external/` and `proposals/`.
Project: FP&A Month-End Copilot, `C:\Users\Tahir\Documents\GitHub\finalFPA`.

---

## Session 001 — 2026-10-03

### Environment blocker

**No shell is available on this host.** `run_terminal_command` fails with:

```
Bash is required but was not found on this Windows system.
```

Searched for a Git Bash install; none found at:
- `C:/Program Files/Git/**/bash.exe` → 0 matches
- `C:/Users/Tahir/AppData/Local/Programs/Git/**/bash.exe` → 0 matches
- `C:/Program Files*/Git*/**/bash.exe` → 0 matches

**RESOLVED for tests in Session 002** — see below. **Still unresolved** for `git` (I could not
confirm whether `dist/` is tracked) and for running an image encoder (see Task 3 `app.ico`).

### Work completed

1. Read `docs/13_SECURITY_PRIVACY.md` in full (602 lines) — the 49 `SEC-nnn` statements,
   the `TST-SEC-01…22` test contract, `ERR-SEC-001…008`.
2. Read `docs/26_API_CONTRACT.md` §1–§5.4.
3. Static verification against `app/`, `ui/src/`, `tests/` for the security-relevant claims.
4. Wrote `audit-external/TASK1_SECURITY_CONTRACT_AUDIT.md` (areas A–L).
5. Wrote the client comms pack, the branding pack and the training narration pack under
   `proposals/`.

### Session 001 errors, recorded

- Marked the diagnostics bundle, `security.log` and DPAPI key storage as **FAIL**. These are
  documented-not-built. Corrected in Session 002 at the lead's instruction — I should have made
  that call myself.
- `proposals/training/README.md` claimed the UI was a "four-tab app", taken from a stale
  `docs/SESSION_LOG.md` entry. Corrected in Session 002 against `ui/src/main.tsx`.
- Reported the `docs/26` severity vocabulary as a code-vs-doc mismatch. It is a doc-internal
  contradiction (§5.2 vs §5.5). Reclassified.

---

## Session 002 — 2026-10-03 (verification pass)

### Resumed from

Session 001's "Work NOT completed" list:
- `docs/26` §5/§6 vs `errors.py` / `openapi.json`
- `docs/10` in full
- the `ui/src` copy audit

### Lead's input received this session

`audit-external/test-output-2026-10-03.md` — **18 passed, 0 failed**, executed by the lead across
the five named suites. Two instructions:

1. *"Shell gap: keep working static; the lead runs pytest here and pastes output."* → All 18 test
   claims **upgraded from static to EXECUTED** and cited by path, not restated as my own result.
2. *"Unbuilt surfaces (diagnostics bundle, security.log, DPAPI): record as documented-not-built with
   phase note, NOT as FAIL."* → Introduced a three-value verdict vocabulary
   (`PASS` / `DOCUMENTED-NOT-BUILT` / `DEFECT`) and reclassified every affected row in the report.

### Work completed

1. **`docs/26` §5 error catalogue vs `app/engine/errors.py`** — all seven implemented families
   verified row-by-row against §5.4/§5.5 (message, hint, httpStatus, slug all faithful). Found:
   - 4 of 11 registered families (`EXP`, `SEC`, `ENG`, `API`) not yet aggregated → documented-not-built.
   - **`docs/26` contradicts itself on severity**: §5.2 says `info/attention/blocking`, §5.5's own
     table says `High/Medium/Low`, and the code follows §5.5 → a `docs/26` decision, not a code fix.
   - The runtime catalogue emits an 8th key (`family`) the documented 7-field projection omits.
   - `test_error_catalog.py:44` asserts 7 of the 11 families; it executed green and is presence-only,
     so it cannot catch a family going missing. Left unchanged (strengthening belongs with the
     aggregation work).
2. **`docs/26` §6 OpenAPI/types vs `app/api/openapi.json` + `ui/src/api/types.ts`** — new section M.
   6 findings: no `securitySchemes`/`security` in the spec; header is `X-Session-Token` and marked
   `required:false` against a spec that says `X-FPA-Token` required everywhere; operation ids are
   FastAPI auto-generated, not `area_verb_object`; no `tags`; `types.ts` is a 19-line hand-written
   `Record<string, any>` stub whose header claims it is auto-generated; the documented generator
   command `--write` does not exist; `GET /meta/error-catalog` is the unversioned alias §6.4 calls
   forbidden. `scripts/check_contract_drift.py` exists and works, but checks only the JSON.
3. **`docs/10_AI_INTEGRATION_SPEC.md` read in full** (1,068 lines) — new section N. Redaction PASS,
   §8.1 ten-step output validation PASS, §11 keyless fallback PASS, §10 pinning PASS (executed),
   §2.3 "never computes/decides/applies/sends" PASS architecturally (`engine/ai/` holds no DB handle).
   Three defects: §6.1 payload caps unenforced; §6.2 owner-name masking absent (`PROMPT-04` carries
   the real name); §9.1 caps implemented and unit-tested but never called from the request path.
4. **`ui/src` copy audit** (`SEC-022/024/034/036/039/040/043`, `TST-SEC-19`) — new section O, 5
   defects. Biggest: the canonical advisory disclaimer appears **nowhere** in `ui/src`, though
   `docs/01` §15.2 requires it on `SCR-040`. Then "securely"/"Masked" for an unencrypted key;
   fabricated `doctor` rows as the UI's *default state*; "encrypted-ready" backups and a delete flow
   missing the mandatory "not a secure erase" + BitLocker sentences; "Zero-Leakage Policy" and a
   false cap claim. Positive findings recorded too: rule-based labelling is present, no client data
   in `ui/src` (`SEC-007` holds).
5. Rewrote the verdict summary, the 18-risk table and §4/§5 of the audit report to carry the new
   material and the reclassification.
6. Wrote `audit-external/HANDOFF.md`.
7. Wrote `proposals/training/01_presenter_script_full_60min.md` and
   `proposals/training/02_chapter_scripts_for_recording.md`, which the training README referenced but
   which did not exist at the time it was written. **Self-consistency failure, now closed** — a README
   that points at missing files is exactly the kind of drift this audit reports elsewhere.

### Test status

**EXECUTED, 18/18 green** — cited from `audit-external/test-output-2026-10-03.md`.
Still unrun, recommended next: `test_api_contract.py`, `test_ai_client.py`, `test_ai_prompts.py`,
`test_ai_guardrails.py`, `test_ai_usage.py`.

---

## Open items for the next session

1. Run the second test batch above and upgrade those claims to executed.
2. Re-verify §O (copy) and §K (envelope) once fixes land — both bounded and fast.
3. `SEC-044`: the payload-shaped-text detector decision (build vs amend the claim). **Do not edit
   `test_ai_defenses.py:29`** — that assertion is correct for what the code does.
4. Confirm whether `dist/` is tracked (needs `git`; still no shell here).
5. Task 3 `app.ico`: `make_icons.py` is written but **unrun** — the binary cannot be produced without
   a shell. Run `pip install cairosvg pillow && python make_icons.py` in `proposals/branding/`.
6. The lead's eight decisions in `HANDOFF.md` §5 — several block re-verification.

## Status of the task menu

| Task | Status |
|---|---|
| 1. Security & contract audit | **Complete.** `audit-external/TASK1_SECURITY_CONTRACT_AUDIT.md`, 15 areas, 18 risks. |
| 2. Client comms pack | **Complete.** 5 files under `proposals/client_comms/`. |
| 3. Branding assets | **Complete as sources; `app.ico` binary unrun** (no shell). 6 files under `proposals/branding/`. |
| 4. Training narration | **Complete.** 3 files under `proposals/training/` — README, full 60-min script, six recorded-demo chapters. |
| 5. Handoff report | **Complete.** `audit-external/HANDOFF.md`. |

**Boundary check:** every file written by me is under `audit-external/` or `proposals/`. No test,
gate or threshold was weakened. No file in `app/`, `tests/`, `docs/`, `ui/`, `sample-data/`,
`packaging/` or `scripts/` was created, modified or deleted.