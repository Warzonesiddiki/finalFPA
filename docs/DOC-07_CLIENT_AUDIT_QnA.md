# DOC-07 — Client Audit Q&A: The Twenty Questions

**Document Reference**: `docs/DOC-07_CLIENT_AUDIT_QnA.md`
**Status**: Draft v0.1
**Last updated**: 2026-10-09
**Owning FRs/areas**: the questions a finance controller or auditor will ask about this tool, and the evidence that answers each one

---

## 1. Purpose

When a finance controller, internal auditor, or external reviewer asks about this tool, they do not ask
for a feature list. They ask about **trust, control, and accountability**. This document is the prepared
answer to the twenty questions that surface in every audit conversation, each with:

- **The question** — exactly as asked.
- **The short answer** — one paragraph, plain language.
- **The evidence** — the file, test, or record that proves the answer.
- **The limit** — what the answer does not cover (because an honest answer names its boundary).

This is not marketing. It is the audit trail from a question to a provable answer.

---

## 2. The Twenty Questions

### Q1. Where does the data live, and who can see it?

**Short answer**: On the analyst's machine, under their Windows user profile, in a local folder. Nothing
leaves the machine unless the analyst explicitly turns on the optional AI assistant, configures their own
AI provider key, and presses an AI button — in which case only a small redacted summary of the visible
screen is sent, and nothing else ever is. There is no cloud service, no telemetry, no backend, no account.

**Evidence**: `13_SECURITY_PRIVACY.md` §8.3 (privacy sentence, reused verbatim in `29` and `22`);
`SEC-039`; `09_TECHNICAL_ARCHITECTURE.md` §9 (loopback API bound to `127.0.0.1`).

**Limit**: This says where the data lives by design. It does not address what happens if the machine is
shared, lost, or stolen — that is a machine-security question (`13` §10 recommends BitLocker).

---

### Q2. How do we know the numbers are right?

**Short answer**: Every number is computed once by a deterministic Python engine using exact Decimal
arithmetic (no floating point, no rounding until display). The same input always produces the same output.
The tool proves this two ways: a planted-exception acceptance harness that checks the engine finds the
right exceptions on known data (32 plantings, 8 controls, 18 High-severity), and a cross-artifact equality
test that asserts the screen, the Excel pack, the PowerPoint deck, and the CSV all show the same number
at display precision.

**Evidence**: `14_TESTING_QA_PLAN.md` §5 (acceptance harness, 7 bars); `evidence/acceptance_report.json`
(current run: 32/32 recall, 0/8 controls fired, 18/18 High, 17 extras, 0 zero-coverage); `NFR-015` /
`14` §7 (cross-artifact equality); `05_CALCULATION_SPEC.md` §13 (exact Decimal, no epsilon).

**Limit**: "Right" means the engine computes what the spec says. It does not mean the source data was
correct when it left the ERP — the tool reads exports; it does not audit the source system.

---

### Q3. Can we trace a number back to the source transaction?

**Short answer**: Yes. Every figure on every screen can be drilled to the transactions that compose it.
The drill shows the source file, the import batch, and the voucher/line. The sum of the drilled
transactions equals the figure exactly (exact Decimal, no rounding drift). This is tested as a property
over the full sample dataset: zero violations.

**Evidence**: `FR-BVA-004`; `05` §4; `TST-BVA-02` (100% drill traceability); `TST-BVA-03` (≤ 5 clicks,
≤ 5 minutes on 250k rows).

**Limit**: This traces to the imported transaction, not to the original ERP entry beyond what the export
contains. If the export omits a field, the drill shows what the export contained.

---

### Q4. Does the tool change anything in our systems?

**Short answer**: No. The tool reads export files. It writes nothing back to any ERP, ledger, or bank
system. The only things it writes are its own local project files — databases, exports, backups — on the
analyst's machine. There is no "write back", no posting, no journal entry, no integration that alters a
record in another system.

**Evidence**: `01_PRD.md` §5 (out-of-scope: no ERP connection, no write-back); `02_FUNCTIONAL_SPEC.md`
§5 (FR boundary: import only); `13_SECURITY_PRIVACY.md` (local-only, no outbound except optional AI).

**Limit**: This is a design statement. If someone configures a file share or script that the tool writes
to, that is a configuration choice, not a tool behaviour.

---

### Q5. What happens if an import fails halfway — do we get half the data?

**Short answer**: No. Imports are atomic: either the whole file commits, or none of it does. If the app
crashes, is killed, or loses power during an import, the next launch detects the interrupted staging area
and reports it — no partial batch is committed. The batch is all-or-nothing.

**Evidence**: `FR-IMP-020`; `04` §15; `TST-IMP-35` (atomicity: crash/cancel leaves 0% or 100%, never
partial); `TST-E2E-04` (crash recovery); `NFR-012` (crash never yields a raw traceback).

**Limit**: This covers the tool's own import. It does not cover a file that is being written to by
another process at the same time — the tool reads the file as it is at the moment of import.

---

### Q6. Can we undo an import if it was wrong?

**Short answer**: Yes. Every import is a batch with a status. A batch can be voided, which removes exactly
that batch's contribution from the analysis — all-or-nothing, audited, and blocked for closed periods.
Voiding does not delete the raw file (that is archived read-only with a checksum) or the history (that
stays). After a void, the analysis recalculates from the remaining batches.

**Evidence**: `FR-IMP-024`/`025`; `04` §13/§18; `TST-IMP-36` (re-import guard); `FR-PRJ-005` (period
close blocks void).

**Limit**: Voiding a batch that was used in an already-issued pack snapshot: the void is allowed, but the
snapshot is unchanged and a re-issue is required for any changed number (`FR-PRJ-010`).

---

### Q7. How do we know an exception is real and not a false alarm?

**Short answer**: Each exception is raised by a written rule with a defined threshold and severity. The
rule catalogue has 24 rules, each with a documented logic, threshold, severity, owner suggestion, and a
false-positive mitigation. The acceptance harness includes 8 precision controls — planted cases that must
**not** raise — and the bar is zero control raises. Every exception shows the rule that raised it, the
threshold used, the subject, the amount, and a drill path to the transactions.

**Evidence**: `06_EXCEPTION_RULES_CATALOG.md` (24 rules, each with logic/threshold/severity/owner/test
case); `14` §5.3 (control precision bar: 0 of 8); `evidence/acceptance_report.json` (0 controls fired);
`FR-EXC-014` (master-data dependencies degrade gracefully — no false positive, no silent skip).

**Limit**: A rule flags a pattern worth a human look. It does not certify that something is wrong. The
analyst's judgement is the last step, and the tool is explicit about that (`08` §16.1 wording: "Potential
exception — requires accounting review", never "error" or "wrong").

---

### Q8. What is the data-quality score, and can we trust a high one?

**Short answer**: It is a weighted 0–100 score over the import's validation checks, computed by formula —
not a hardcoded literal. A batch with any failed check cannot show a perfect score. The score is always
shown alongside the failed-check list, and the per-check breakdown is one click away. A high score means
the checks passed; it does not mean the data is correct in any broader sense.

**Evidence**: `CALC-050`; `04` §16; `DEF-021` (fixed the literal-100 bug); `TST-CALC-24` (asserts the
formula, weights, and "score never masks a failure" guarantee); `acceptance_report.json` → `corpus[]` →
`data_quality_score` per file (computed values: 93, 100, 100, 100, 100, 100, 92).

**Limit**: The score covers the checks the tool runs. It does not cover business logic the tool cannot
see (e.g. a correctly-formatted row that is factually wrong).

---

### Q9. How do we know the Excel and PowerPoint packs are accurate?

**Short answer**: The pack is generated from the same analysis the screen shows. The cross-artifact
equality test asserts that for one fixed filter state, the engine, the UI, the Excel pack, the PowerPoint
deck, and the CSV all show the same number at display precision — zero tolerance. This is tested
automatically. If any surface diverges, the test fails and the build is blocked.

**Evidence**: `NFR-015`; `14` §7; `TST-XL-*` + `TST-PPT-13` + `TST-API-14` under one harness;
`cross_artifact.json` (when generated); `FR-BVA-011` (export what you see).

**Limit**: This asserts the tool's outputs agree with each other. It does not assert the numbers are
correct in an absolute sense — that is the drill-through and trial-balance chain (Q2, Q3, Q5).

---

### Q10. Can we rely on the forecast numbers?

**Short answer**: The forecast is computed by four defined methods (run-rate, prior-year, budget,
driver-based), each with eligibility guards that refuse to run when there is not enough data. The methods
reproduce fixed fixtures exactly. Overrides require a reason and are audited. A locked forecast version is
immutable. The accuracy report compares closed-period forecasts to actuals using defined metrics.

**Evidence**: `07_FORECAST_METHODS_SPEC.md` §4; `05` §9; `TST-FC-01…14`; `TST-FC-10` (lock semantics);
`TST-FC-11` (accuracy metrics with worked examples); `07` §8 (accuracy feedback).

**Limit**: A forecast is a projection, not a prediction. Its reliability depends on the method, the data,
and the overrides. The tool shows the method and the inputs; it does not certify the forecast will be
accurate.

---

### Q11. What is the audit trail, and can we get it out?

**Short answer**: Every change the tool makes is recorded: imports (batch, file, checksum, rows, status,
who/when), voids, period close/reopen, threshold and mapping changes, exception status changes, forecast
overrides, pack issuance. Each audit entry is timestamped and attributed. The audit trail is exportable —
the evidence bundle per exception contains the subject rows, the validation report, the mapping version,
the effective thresholds, and the audit trail.

**Evidence**: `FR-PRJ-007` (schema version check + migration audit); `FR-IMP-023` (import history);
`FR-EXC-008` (notes with history); `FR-EXC-016` (evidence bundle); `FR-PRJ-008`/`009` (backup/restore
with manifest); `13` §5 (provenance).

**Limit**: The audit trail records what the tool did. It does not record what someone did in the ERP, or
what the analyst decided offline. It is a record of the tool's actions, not a complete record of the
month-end process.

---

### Q12. Who can change the thresholds and rules?

**Short answer**: The finance owner (or whoever has access to the machine and the settings). Threshold and
rule changes are versioned, audited, and shown with the default for comparison. Every change marks derived
results as stale until re-run. There is no separate "admin" role — access control is the machine's access
control (whoever can open the app can change the settings).

**Evidence**: `FR-EXC-012` (per-project rule config, versioned, reset-to-default); `FR-EXC-013` (global
materiality, per-rule override wins, effective threshold recorded on every raise); `FR-SET-004` (settings
audit).

**Limit**: This is a single-user desktop tool. There is no multi-user permission model. If the machine is
shared, the machine's own access control is the only barrier. For a multi-user environment, this is a
limitation to be aware of (`29` §5: single-user desktop tool).

---

### Q13. What happens to the data if we stop using the tool?

**Short answer**: Everything stays on the machine, in the project folder, in open formats. The project can
be backed up to a plain zip at any time (one click), and restored on any machine that has the app. The raw
import files are archived read-only with checksums. The exports (Excel, PowerPoint, CSV) are standard files
that open in Office. Stopping use of the tool does not lock up the data.

**Evidence**: `FR-PRJ-008`/`009` (backup/restore); `FR-IMP-025` (immutable raw-file archive with
checksum); `15_PACKAGING_DEPLOYMENT_RUNBOOK.md` §7 (uninstall leaves user data); `29` §12 (care and
feeding).

**Limit**: The project databases are DuckDB and SQLite. They are open formats, but reading them outside
the tool requires a DuckDB/SQLite client. The tool's backup (zip) is the supported extraction path.

---

### Q14. Is the tool audited or certified?

**Short answer**: No. It is not an audited or certified accounting system, and it does not claim to be.
It is an analysis aid that flags patterns worth a human look. It is tested against a written specification
and a planted-exception corpus, and the test results are available. It does not replace professional
judgement, an audit, or a certification.

**Evidence**: `01_PRD.md` §15.1 (advisory disclaimer); `29` §13 (advisory disclaimer, verbatim);
`28_ACCEPTANCE_UAT_AND_GO_LIVE.md` §7.1 (signer certifies the artefacts and period, not a financial
opinion); `06` §1 (exception engine: flags, not certifies).

**Limit**: This is the honest answer. If the question is "will this satisfy our external auditor's
requirement for a reviewed system?", the answer is "bring your auditor to the trial month and let them see
the drill-down and the audit trail" — the tool's value in an audit is demonstrable behaviour, not a
certificate.

---

### Q15. Does the AI component change any numbers?

**Short answer**: No. The AI assistant, when enabled, writes draft commentary and observations from figures
the engine has already calculated. It has no calculator, no vote on any figure, and cannot change data,
set a threshold, approve an exception, close a period, or issue a pack. Every AI draft is labelled "AI
draft — not approved" until a person approves it, and the approved version is what appears in the pack.
With AI off (the default), every feature works identically.

**Evidence**: `10_AI_INTEGRATION_SPEC.md` §2.3 (AI policy: never computes, never decides, never sends);
`FR-AI-004`/`006`; `FR-EXC-003` (deterministic evaluation only — AI never raises or closes an exception);
`29` §6 (what the AI does and does not do).

**Limit**: This is the policy and the design. The AI provider is the client's own choice with their own
key. The tool sends only a redacted summary of the visible screen. The client should review the provider's
own data-handling terms (`10` §11).

---

### Q16. What happens if the AI gives a wrong suggestion?

**Short answer**: The suggestion is a draft, labelled as such, and never applied without a human approving
it. A wrong suggestion that is not approved has no effect. A wrong suggestion that is approved and edited
is the human's edit. The tool does not learn from approvals in a way that changes future outputs without a
versioned mapping change.

**Evidence**: `10` §2.3; `FR-AI-004` (draft provenance label); `FR-IMP-008` (mapping review queue:
suggested → accepted | edited | rejected, never auto-applied in the same run).

**Limit**: The AI's output quality depends on the provider and the input. The tool's guard is the draft
label and the human approval gate, not a guarantee of AI output quality.

---

### Q17. How do we know the tool is the version we think it is?

**Short answer**: The installer is distributed with a SHA-256 checksum published separately. The recommended
install step is to verify the checksum before running the installer (`certutil -hashfile … SHA256`). The
app itself shows its version on the About screen, and the version is recorded in every generated pack's
stamp block. The portable package (no-install zip) carries the same checksum.

**Evidence**: `29` §2.1 (fingerprint check, verbatim walkthrough); `15` §8.3 (SmartScreen walkthrough,
reused verbatim); `11` §3.5 (machine-readable stamp, 30-field block with version); `24_RELEASE_AND_VERSIONING_RUNBOOK.md`
(semver, tags, checksum).

**Limit**: The checksum verifies the file arrived unchanged. It does not verify the file is "good" — that
is what the trial month and UAT are for. The signing certificate question is decision 14 in `29` §7
(certificate not purchased for v1; SmartScreen mitigation ladder applies).

---

### Q18. What is the backup and restore process, and has it been tested?

**Short answer**: One click creates a plain zip of the project folder (databases, archives, settings,
mappings, master data, no secrets). Restore is to a new empty folder, never over a live project, with a
typed confirmation if a folder already exists. Restore has been tested as part of the E2E suite: a backup
taken, restored to a clean location, and the numbers and workflow state compared — identical.

**Evidence**: `FR-PRJ-008`/`009`; `TST-E2E-06` (backup → restore round trip on a clean VM: every table,
setting, workflow state identical; secrets absent); `13` §9.2 (backup plain-language warning: "This backup
is a normal zip file — anyone who can open the file can read the project").

**Limit**: The backup is a point-in-time snapshot. It does not replace a broader disaster-recovery plan
for the machine. The tool's backup is the project, not the machine.

---

### Q19. What is the response time if something goes wrong at month-end?

**Short answer**: The default support flow (until the client confirms different terms): the analyst contacts
the consultant directly, with the diagnostics zip the tool produces and one sentence on what happened. The
diagnostics zip contains logs, versions, and settings — no project data, no numbers, no key. The agreed
response targets (same-day for anything blocking the month-end; written plan within two working days) are
confirmed before go-live.

**Evidence**: `29` §12 (support, plain language); `23_CONSULTANT_HANDOVER_AND_SUPPORT.md` §10/§11 (support
model, response targets, escalation); `28` §3.1 (default response targets, pending `OQ-016` confirmation);
`SCR-040` (About / Diagnostics → create zip).

**Limit**: These are defaults until `OQ-016` confirms the support/warranty terms with the client. The
actual terms are a commercial decision, recorded in `18` and `23` §11.

---

### Q20. Can we trust this tool for external reporting or audit purposes?

**Short answer**: The tool is an analysis aid, not an audited system and not a substitute for professional
judgement. It can produce numbers you can trace, drill, and cross-check, and it can produce an audit trail
of what it did. Whether those numbers are suitable for external reporting or audit is a judgement for your
auditor, made with the tool's evidence in front of them. The tool's job is to make that judgement easier
to make by making the numbers traceable and the process auditable — not to certify the numbers itself.

**Evidence**: `01` §15.1 (advisory disclaimer); `29` §13 (verbatim disclaimer); `28` §7.1 (signer
certifies artefacts and period, not a financial opinion); `14` §5 (acceptance harness — the tool proves
its own behaviour against a planted corpus); `FR-BVA-004` (drill-through — the analyst can see the source
of any number).

**Limit**: This is the honest boundary. The tool is evidence-of-process, not a certified system. The
auditor's question is best answered by walking them through a drill-down on a number they choose, showing
the source file and batch, and letting them see the audit trail — not by showing them a certificate that
does not exist.

---

## 3. The Evidence Index

| Question | Primary evidence | Secondary evidence |
|---|---|---|
| Q1 data location | `13` §8.3; `SEC-039` | `09` §9 |
| Q2 number correctness | `evidence/acceptance_report.json`; `14` §5; `NFR-015` | `05` §13 |
| Q3 drill-through | `FR-BVA-004`; `TST-BVA-02`/`03` | `05` §4 |
| Q4 no write-back | `01` §5; `02` §5; `13` | — |
| Q5 atomic import | `FR-IMP-020`; `TST-IMP-35`; `TST-E2E-04` | `NFR-012` |
| Q6 void import | `FR-IMP-024`/`025`; `TST-IMP-36`; `FR-PRJ-005` | — |
| Q7 exception trust | `06`; `14` §5.3; `evidence/acceptance_report.json` | `FR-EXC-014` |
| Q8 DQ score | `CALC-050`; `DEF-021`; `TST-CALC-24`; `acceptance_report.json` corpus[] | `04` §16 |
| Q9 pack accuracy | `NFR-015`; `14` §7; `cross_artifact.json` | `FR-BVA-011` |
| Q10 forecast | `07` §4; `TST-FC-01…14`; `07` §8 | `05` §9 |
| Q11 audit trail | `FR-PRJ-007`/`008`/`009`; `FR-IMP-023`; `FR-EXC-016`; `13` §5 | — |
| Q12 thresholds | `FR-EXC-012`/`013`; `FR-SET-004` | — |
| Q13 exit data | `FR-PRJ-008`/`009`; `FR-IMP-025`; `15` §7; `29` §12 | — |
| Q14 audited/certified | `01` §15.1; `29` §13; `28` §7.1; `06` §1 | — |
| Q15 AI numbers | `10` §2.3; `FR-AI-004`/`006`; `FR-EXC-003`; `29` §6 | — |
| Q16 AI wrong | `10` §2.3; `FR-AI-004`; `FR-IMP-008` | — |
| Q17 version trust | `29` §2.1; `15` §8.3; `11` §3.5; `24` | — |
| Q18 backup/restore | `FR-PRJ-008`/`009`; `TST-E2E-06`; `13` §9.2 | — |
| Q19 response time | `29` §12; `23` §10/§11; `28` §3.1 | — |
| Q20 external reporting | `01` §15.1; `29` §13; `28` §7.1; `14` §5; `FR-BVA-004` | — |

---

## 4. The Honest Limits

These are the questions the tool **cannot** answer, and the honest response to each:

| Question | Honest response |
|---|---|
| "Is this system SOX-compliant?" | The tool is not a certified system. SOX compliance is an assertion about the control environment, of which this tool may be one component. Bring your auditor to the trial month. |
| "Will this satisfy our external auditor?" | The tool produces traceable, drillable numbers and an auditable trail. Whether that satisfies your auditor is your auditor's call. The trial month is the best evidence. |
| "Can we use this for regulatory filing?" | The tool is an analysis aid with an advisory disclaimer. It does not certify numbers for filing. Any number used for filing must be reviewed by a qualified accountant. |
| "Is the AI accurate?" | The AI is a drafting aid with a provenance label and a human approval gate. Its output quality depends on the provider and the input. The tool does not guarantee AI output quality. |
| "Can multiple people use it at once?" | No. It is a single-user desktop tool by design. There is no multi-user permission model. |
| "Can we host it on a server?" | Not in v1. It is a local-only desktop tool. A server-hosted version is a different product. |

These limits are not weaknesses to hide. They are the boundaries that make the tool's promises honest.
An auditor who hears "it does X, and here is the evidence, and it does not do Y, and here is why" is
getting a more useful answer than one who hears "it does everything."

---

## 5. Relationship to Other Docs

| Doc | Relationship |
|---|---|
| `29_CLIENT_REQUIREMENTS_PACK.md` | The client-facing requirements; this doc is the audit-specific companion |
| `28_ACCEPTANCE_UAT_AND_GO_LIVE.md` | The acceptance and UAT mechanics; this doc answers the questions UAT raises |
| `13_SECURITY_PRIVACY.md` | Owns the privacy and security assertions |
| `14_TESTING_QA_PLAN.md` | Owns the test evidence |
| `05` / `06` / `07` | Own the calculation, exception, and forecast definitions |
| `card_acceptance_standard.md` | Owns the acceptance standard the evidence must meet |
| `SPEC-08_ACCEPTANCE_STANDARD.md` | Owns the project-level acceptance standard |

---

## 6. Living Note

This document is updated when a new question surfaces in a real audit conversation, not in advance. The
twenty questions above are the ones that have surfaced. If a controller or auditor asks a question not
listed here, the answer is recorded as a new row and the evidence path is attached — the same way every
other row was built.
