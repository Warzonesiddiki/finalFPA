# HANDOFF — external contributor audit, FP&A Month-End Copilot

**From:** independent contributor-auditor (outside the main team)
**To:** project lead
**Date:** 2026-10-03
**Sessions:** 001 (static audit) + 002 (verification pass, after your `test-output-2026-10-03.md`)
**Write boundary honoured:** I wrote only under `audit-external/` and `proposals/`. Nothing of mine
was written into `app/`, `tests/`, `docs/`, `ui/`, `sample-data/`, `packaging/` or `scripts/`.
**No test, gate or threshold was weakened.**

---

## 1. Files I created

### `audit-external/` (reports — mine to own)

| File | What it is |
|---|---|
| `progress.md` | Session log, per the protocol. Session 001 + Session 002 entries, resume points, corrections. |
| `TASK1_SECURITY_CONTRACT_AUDIT.md` | The security & contract audit. 15 areas (A–O), 18 ranked risks, full file:line evidence. |
| `test-output-2026-10-03.md` | **Yours**, not mine — your pytest result, which I cite rather than reproduce. |
| `HANDOFF.md` | This file. |
| `sessions/` | *(Session 002 additions below, where relevant.)* |

### `proposals/` (new files only — nothing merged)

**`proposals/client_comms/`** — plain-language client pack, zero invented claims:
`README.md`, `01_pilot_request_email.md`, `02_transfer_instructions.md`,
`03_smartscreen_walkthrough_printout.md`, `04_support_sheet.md`.

**`proposals/branding/`** — neutral professional defaults, no client branding invented:
`README.md`, `logo-mark.svg`, `logo-lockup.svg`, `logo-lockup-stacked.svg`, `palette.md`,
`make_icons.py`.

**`proposals/training/`** — word-for-word presenter scripts against the sample project:
`README.md` (with one correction applied and left visible), `01_presenter_script_full_60min.md`
(seven blocks, eight `[BUILD NOTE]` lines, `[IF BEHIND]` cut-lines), `02_chapter_scripts_for_recording.md`
(six chapters + closing card).

**Total: 4 reports + 14 proposal files.**

---

## 2. Test status — now EXECUTED

Your run at `audit-external/test-output-2026-10-03.md`:

```
python -m pytest tests/unit/test_ai_defenses.py tests/unit/test_ai_key_rotation_drill.py \
  tests/unit/test_ai_pinning.py tests/integration/test_error_envelope.py \
  tests/integration/test_error_catalog.py -p no:cacheprovider -q
→ 18 passed, 0 failed
```

**18/18 green. My independently-read test counts matched exactly (5 + 1 + 7 + 4 + 1), which
corroborates that I read the right files.**

**One thing you should not take comfort from:** `test_error_envelope.py` and `test_error_catalog.py`
are green *against* a divergence from `docs/26`. See §4.6 and §4.7. A passing suite proves the code
does what the test says; where the test and the document disagree, that is a finding.

**Still unrun, and I recommend you run them next:**

```bash
python -m pytest tests/integration/test_api_contract.py tests/unit/test_ai_client.py \
  tests/unit/test_ai_prompts.py tests/unit/test_ai_guardrails.py tests/unit/test_ai_usage.py -v
```
These cover the AI contract surface (`docs/10` §8, §9, §10) that Task 1 leans on hardest.

---

## 3. Per-item verdicts

Verdict vocabulary, per your instruction: **PASS** · **DOCUMENTED-NOT-BUILT** (specified, owed,
expected at this phase — *not* a defect) · **DEFECT** (code claims a property it does not have, or
contract and code disagree observably).

| Area | Verdict | One-line reason |
|---|---|---|
| **A** Loopback/token/CORS | PARTIAL — 1 DEFECT | Binds `127.0.0.1` correctly; `/meta/error-catalog` and `/api/v1/health` carry no token dependency; header is `X-Session-Token`, spec says `X-FPA-Token`. |
| **B** Outbound inventory | **PASS** | Exactly three call sites, all in `engine/ai` or a loopback bind probe. No telemetry anywhere. |
| **C** TLS verification | **PASS** | `httpx.Client(timeout=…)` with no `verify=` override anywhere; no toggle in Settings. |
| **D** AI key storage | 2 DEFECTS + DN-B | Last 4 chars returned to the UI; "Securely/Masked" claimed for an unencrypted key. DPAPI itself is owed. |
| **E** Injection + redaction | PASS, 2 DEFECTS | Delimiters, stripping, schemas, number-strip and provenance all correct. `SEC-044` detector absent; owner-name masking absent. |
| **F** Caps | **DEFECT** | Four caps implemented and unit-tested; **none called from the request path**. |
| **G** Logging policy | DN-B | No logging configuration exists in the repo at all. |
| **H** Diagnostics bundle | 1 DEFECT + DN-B | Endpoint writes nothing; the UI reports a successful "redacted zip". |
| **I** Audit/security events | DN-B | `security.log`, general `AuditLog`, synced-folder guard all owed. |
| **J** `docs/26` §5 catalogue | DN-B + 2 DEFECTS | 7 of 11 families aggregated; **the document contradicts itself** on severity (§5.2 vs §5.5); runtime carries an extra `family` key. |
| **K** `docs/26` §2 envelope | 2 DEFECTS | Success responses omit `warnings`/`errors`; error shape diverges from the §2.3 contract. |
| **L** Supply chain | DN-B + 1 DEFECT | `httpx>=0.27.0` is a range, not a pin; no lockfile; `.gitignore` omissions. Scan/bootstrap/SBOM owed. |
| **M** `docs/26` §6 OpenAPI/types | 3 DEFECTS | `types.ts` is a hand-written `Record<string, any>` stub claiming to be generated; the generator command does not exist; no `securitySchemes`; unversioned route alias. |
| **N** `docs/10` AI spec | PASS, 3 DEFECTS, 3 DN-B | Redaction, output validation, pinning and keyless fallback all solid. Payload caps, owner-name masking and cap enforcement not done. |
| **O** `ui/src` copy audit | 5 DEFECTS | Disclaimer absent entirely; "securely", "encrypted-ready", "Zero-Leakage Policy" and a false cap claim all ship in the UI. |

**Tally:** 5 areas PASS outright · 6 areas mostly PASS with named defects · 5 areas largely
DOCUMENTED-NOT-BUILT · **17 distinct DEFECTs**.

---

## 4. Top 5 risks

### Risk 1 — The advisory disclaimer is not in the application at all
**`docs/01` §15.1/§15.2 · `SEC-043` · `docs/28` go-live item 13**
Searching `ui/src` for `Advisory|professional advice|qualified accountant|not professional` returns
**zero matches**. `AboutDiagnosticsScreen.tsx` (read in full) has no disclaimer. This is the one
paragraph an auditor and a client are told to look for, and §15.2 requires it *with a Copy button*
on the About screen. Cheapest high-impact fix in this report.

### Risk 2 — The last four characters of the AI key are returned by the API, and the UI calls it "secure"
**`SEC-010`, `SEC-036`**
`app/api/main.py:1431` returns `api_key[:6] + "..." + api_key[-4:]`. `docs/13` §5.2: *"No part of
the key is ever displayed, including the last characters."* Worse, `SettingsScreen.tsx:152` tells the
user `API Key configured securely (Write-only, Masked)` — false on both counts, because the key is a
plain env var and a masked substring is returned. Two one-line fixes.

### Risk 3 — The `doctor` screen asserts credential controls that do not exist, as its default state
**honesty rule (`docs/13` §1), `SEC-024`**
`AboutDiagnosticsScreen.tsx:37-45` and `main.py:1799-1806` both carry
`DOC-04 "AI Key & Credential Redaction Guardrails — PASS — Zero unmasked secrets detected in state"`
as **hard-coded default state**. No check runs. This is the string an auditor reads.

### Risk 4 — The UI promises an AI spend cap the engine does not enforce
**`FR-AI-009`, `SEC-021`, honesty rule**
`AiUsageDashboard.tsx:133`: *"When cumulative monthly tokens exceed this limit, outbound AI calls
automatically divert to rule-based fallback."* `AiUsageMeter.tsx:47`: *"🔒 Zero-Leakage Policy…"*.
Neither is true: `check_caps` (`guardrails.py:799`) and `check_cap_exceeded` (`usage.py:126`) exist
and are unit-tested, but `AIClient.generate()` never calls them. A user relying on that sentence has
a false belief about their spend, and `RISK-031`'s mitigation is inert.

### Risk 5 — Seven UI copy defects are unguarded because `TST-SEC-19` does not exist
**`SEC-022/024/034/036/039/040/043`**
`docs/13` §13.2 specifies a UI-copy audit asserting *"'encrypted'/'secure' never appear for
unimplemented properties"*. It is not in `tests/`. One test — grep `ui/src` for
`encrypted|secure|zero-leakage` against an allow-list, plus assert the disclaimer is present —
would prevent this entire class from recurring. **This is the single highest-leverage test in the
report**, because every one of the Session 002 copy findings would have been caught by it.

*Honourable mentions, also high:* **R13** (unversioned `/meta/error-catalog` and `/api/v1/health`
without a token, `SEC-008`); **R9** (two green tests asserting an envelope that diverges from
`docs/26` §2.3); **R14** (backups described as *"encrypted-ready"*, and the delete flow lacking the
mandatory *"this is not a secure erase"* and BitLocker sentences).

---

## 5. What needs your eye — decisions only you can make

| # | Decision | Why it is yours |
|---|---|---|
| 1 | **Envelope shape.** Bring the API to `docs/26` §2.3, or amend `docs/26` and add a `BL-` entry? | It breaks the UI and two currently-green tests either way. Silence is the only indefensible option. |
| 2 | **Severity vocabulary.** `docs/26` §5.2 (`info/attention/blocking`) vs §5.5 + code (`High/Medium/Low`). | The **document contradicts itself**; the code follows §5.5. Needs a doc fix, not a code fix. |
| 3 | **Honesty-rule copy (R3/R4/R18).** Build, or make the copy true? | Per `docs/13` §16.2, *any weakening of a control* needs written rationale + a `docs/25` risk entry + sign-off in `CHANGELOG`/`SESSION_LOG`. |
| 4 | **Caps (R4 in §4 above).** Wire them, or stop claiming them? | A product-cost control versus a UI copy decision. |
| 5 | **OpenAPI pipeline (M-2/M-3).** Build the generator + `openapi-typescript`, or amend §6? | `ui/src/api/types.ts` is a 19-line stub whose header claims it is auto-generated. Right now the TypeScript contract is unenforced. |
| 6 | **`SEC-044`.** Build the payload-shaped-text detector, or amend the claim? | **Do not edit `test_ai_defenses.py:29`** — that assertion is correct for what the code does, and it executed green. |
| 7 | **`dist/` tracked?** | I could not run `git` (`SEC-045`, R10). Please confirm. |
| 8 | **Cost model.** `usage.py` prices in USD (`$5/$15 per 1M`); `guardrails.py` prices in INR (`₹0.15/₹0.77 per 1k`). | Money math is out of my scope, but `TST-AI-*` fixtures will pin one. Pick before they land. |

---

## 6. What I did **not** do, and why

- **I did not fix anything.** Every finding names a file and line; none of them is a patch.
  `app/`, `tests/`, `docs/`, `ui/` are not my folders.
- **I did not touch the tests.** `test_error_catalog.py:44` asserts 7 of the 11 documented families.
  Tightening it is a **strengthening**, but it should land *with* the aggregation work so the suite
  does not go red in between. That is the team's call.
- **I did not claim any test result I did not have.** Session 001 claimed none; Session 002 cites
  yours by path.
- **I did not mine `audit/`** — the team's own prior audit — for findings to claim as mine.
- **I did not create `app.ico` as a binary.** This host has no shell, so I cannot run an image
  encoder, and I will not paste an unverifiable base64 blob. I wrote `make_icons.py`, the build step
  that produces it from the reviewable SVG master. **A committed binary icon would also sit badly
  with `SEC-045` (no unreviewed binaries); a committed generator does not.**
- **I invented no client branding, no client data, and no commercial terms** anywhere.

---

## 7. My own errors, on the record

Per the protocol that honest partial beats confident complete, here are the corrections I made to
my own Session 001 work:

1. **18 tests recorded as unrun.** They are now executed, 18/18 green (yours).
2. **Three unbuilt surfaces recorded as FAIL.** Reclassified DOCUMENTED-NOT-BUILT at your
   instruction. That was the correct call and I should have made it without being told.
3. **`proposals/training/README.md` said the UI was a "four-tab app."** I took that from a stale
   `docs/SESSION_LOG.md` entry. `ui/src/main.tsx:38` registers **thirteen** tabs. Corrected in the
   file, with the correction left visible.
4. **`docs/26` severity reported as a code-vs-doc mismatch.** Re-reading §5.5, the **doc contradicts
   itself**. The code follows §5.5. Reclassified as a `docs/26` decision.

---

## 8. Recommended next session

1. Run the second test batch (§2) so the AI contract surface has executed evidence too.
2. Implement `TST-SEC-19` **before** fixing the copy defects it would catch — the test is the
   durable output, the fixes are one-off.
3. Triage the 17 defects into a `docs/27_BACKLOG.md` entry with severity, so Risk 1 and Risk 2 do
   not get lost behind feature work.
4. Re-run this audit against the fixes for §O (copy) and §K (envelope) only — both are bounded and
   fast to re-verify.

---

*Prepared by the independent contributor-auditor. Nothing here lands in the project without your
verification. Appropriate work should be carried into the repository by the team with attribution;
the rest stays here as reference.*