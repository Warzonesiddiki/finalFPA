> **Status:** Draft v0.2
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** owner control, session review, evidence and claims, red flags, Phase 0 review,
> spot-check sampling, stuck/rollback escalation, and independent money-oracle review (Addon 5 §§B–D, F–I).
> **TL;DR (≤ 15 lines):**
> - Pick the single next roadmap item before a session; after it, review evidence and approve or reject.
> - A session is not closed without the six-part report at the top of `SESSION_LOG.md`.
> - Every green, done, performance, UI, installer, or contract claim needs the exact evidence listed here.
> - Check the diff, citations, tests, evidence, and Coverage Matrix in five minutes before accepting work.
> - Phase 0 review takes about half a day and ends with an explicit approval or rejection, never silence.
> - Every phase gets at least two randomly selected FR demonstrations against their acceptance criteria.
> - Red flags stop work; severe or repeated evidence, data, test, or approval failures require full re-verification.
> - The independent oracle uses formula-visible spreadsheets derived from the specification, never engine code.

# 30 — OWNER OPERATING HANDBOOK

## 1. What this handbook is for

This is the project owner's operating guide. It explains what you need to do before, during and after a
session, and what evidence you should expect before approving work. It is not a technical build manual.
The engineering team owns implementation; you own priorities, approvals, scope decisions and client-facing
commitments.

| This handbook owns | It does not replace |
|---|---|
| Owner cadence, session reports, evidence standards, review checks, red flags, spot checks, stuck choices and independent hand checks | Product requirements (`01`/`02`), formulas (`05`), exception rules (`06`), architecture (`09`), tests (`14`), coding rules (`17`), release mechanics (`24`) |
| The evidence and red-flag rules for all project claims | The detailed source of each claim; that remains in its owning document or evidence artefact |
| The owner-facing Phase 0 review method | The formal approval record in `CHANGELOG.md` and `SESSION_LOG.md` (`19`) |

**One rule governs this handbook:** do not approve a claim because it sounds plausible. Approve it when its
evidence can be opened, understood and traced to the stated requirement.

## 2. Your session cadence

### 2.1 Before a session — choose one outcome

1. Read the **next open item** in `16_ROADMAP_PHASES.md` §1.3.
2. Confirm that it is the only item the session will pursue. New ideas go to the backlog or an open question;
they do not join the session by convenience.
3. If the item changes scope, money logic, data handling, client commitments, architecture or dependencies,
expect a written proposal before work starts.
4. If the item is a gate, ask for its evidence list before the session begins.

You do **not** need to prescribe technical implementation. The engineer must work inside the approved
specification and return evidence.

### 2.2 During a session — let the engineer work

During normal implementation, you do nothing. Interrupt only to answer a decision explicitly raised for
you, such as a scope cut, a client-facing promise, an Addon proposal, an `L`-sized change, or one of the
three stuck-protocol options in §9.

A status message is not an approval. Silence is not an approval.

### 2.3 After a session — review, then approve or reject

1. Read the newest session report at the top of `SESSION_LOG.md`.
2. Open the referenced evidence paths, beginning with failed or changed items.
3. Review the diff summary and confirm that files and dependencies are expected.
4. Approve, reject, or ask for correction in writing.
5. For a phase gate, record the exact approval in both `CHANGELOG.md` and `SESSION_LOG.md`:

```text
Phase <n> gate APPROVED — <your name> — YYYY-MM-DD
Conditions / notes: <optional>
```

For Phase 0, the exact form is:

```text
Phase 0 APPROVED — <your name> — YYYY-MM-DD
Conditions / notes: <optional>
```

No product code may begin before that Phase 0 record exists.

## 3. The required session report

Every session report is the newest entry at the top of `SESSION_LOG.md`. A session without this block is
**not closed**.

```markdown
### Session <number> — YYYY-MM-DD — <focus>

| Done (with FR IDs) | Evidence refs | Tests status (with transcript path) | Decisions needed from me | Next session plan | Risks / blocked |
|---|---|---|---|---|---|
| <completed outcome and FR IDs, or “governance only — no FR”> | <repo-relative evidence paths, commands, commit hash, observed output> | <green / red / not applicable, command, exit code, transcript path> | <decision, options, recommendation, or “none”> | <single roadmap item> | <risk IDs, blocker IDs, or “none”> |
```

The report may have supporting detail below the table, but it must answer all six columns. A phrase such as
“tests should be green,” “works locally,” or “ready” is not a valid test or completion status.

## 4. Your five-minute review checklist

Use this for every completed session before you accept it.

| Check | What to inspect | Pass condition |
|---|---|---|
| 1. Evidence exists | Open every path in the session-report Evidence refs column | Each material claim has an artefact, command transcript, screenshot, hash or demo observation |
| 2. Requirements are cited | Open the referenced FR or specification section | The work can be traced to an approved requirement; there is no invented feature |
| 3. The diff is sane | `git diff --stat`, then the changed files | No surprise dependency, binary, client file, secret, installer, generated build output or unrelated refactor |
| 4. Checks are honest | Read the transcript path and its exit code | The stated command actually ran, its exit code is `0`, and the final lines support the claim; failures are named, not hidden |
| 5. Specs preceded code | Compare the `CHANGELOG`, spec diff and code diff | Behaviour changes were specified and recorded before implementation; test expectations were not weakened |
| 6. Coverage is current | Open the row in `00_INDEX.md` §4 | Any affected Coverage Matrix row points to the completed owning document and is not marked integrated without content |

If a check fails, reject the claim. The engineer either corrects it or records it as a risk, blocker or
backlog item. Do not approve partial evidence as a future promise.

## 5. Your Phase 0 review guide — about half a day

Phase 0 is approved only after the six-document contract is integrated, the six documentation gates pass,
and you have reviewed the required material. The suggested budget is approximately four hours.

| Order | What to read or verify | Budget | What you are checking |
|---|---|---:|---|
| 1 | `29_CLIENT_REQUIREMENTS_PACK.md` — read fully | 25 min | The client promise, boundaries, decisions, timeline, privacy wording and sign-off are what you intend to offer |
| 2 | `01_PRD.md` — read fully | 40 min | Scope, exclusions, success measures, constraints, assumptions, risks and licensing stance are acceptable |
| 3 | `05_CALCULATION_SPEC.md` — read fully | 50 min | Money rules, rounding, fiscal periods, materiality and the worked examples reflect the intended finance treatment |
| 4 | `06_EXCEPTION_RULES_CATALOG.md` — read fully | 50 min | Each potential exception is a review aid, not an accusation; thresholds and escalation ownership are acceptable |
| 5 | `PHASE0_SUMMARY.md` — read fully | 20 min | Gate state, risks, unresolved questions and the approval ask accurately reflect the repository |
| 6 | `00_INDEX.md` §4 and `14_TESTING_QA_PLAN.md` §15 — skim | 25 min | Every contract row is integrated and all six gate checklists have cited evidence |
| 7 | `20_REQUIREMENTS_TRACEABILITY.md` plus two sampled chains — trust but verify | 25 min | An FR leads to a specification, screen, API contract and test without guessing |
| 8 | Link-check and evidence spot sample — trust but verify | 25 min | Links resolve; reported evidence physically exists; no claim relies only on prose |

**Decision rule:** reject approval if a requirement is vague, a calculation cannot be hand-checked, an
evidence path is missing, a claim is unevidenced, or a red flag in §8 appears. Ask for a targeted repair,
then re-review only the affected material plus its evidence.

## 6. Spot-check sampling at every phase gate

At each phase gate, choose **at least two FRs at random** from `20_REQUIREMENTS_TRACEABILITY.md`. Ask for a
live demonstration against the FR’s documented acceptance criteria and its existing demo recipe.

For each selected FR, require all of the following:

1. The engineer reads the FR and acceptance criteria before the demonstration.
2. The feature runs on synthetic/sample data only.
3. The expected result is observed, including one relevant error, empty or recovery state where the FR
   requires it.
4. The engineer shows the test identifier and the transcript or report that proves it.
5. The number, export or screen can be traced back to the source data or specified formula.

If either selected FR cannot be shown, the gate does not pass. Sampling does not replace the full test suite;
it detects false confidence and broken traceability quickly.

## 7. Evidence and claims protocol

### 7.1 The non-negotiable rule

**No claim without evidence.** Every status in `SESSION_LOG.md`, a gate table, a report or a release record
must name a repository-relative artefact.

| Claim | Required evidence |
|---|---|
| “Tests green” | Exact command, exit code, and the final approximately 20 transcript lines under `evidence/YYYY-MM-DD-<task>/` |
| “Feature done” | FR IDs, commit hash, demo recipe run, and observed result |
| “UI works” | Screenshot using sample data only, stored at the stated evidence path |
| “Installer builds” | Artefact path, SHA-256, build machine and operating-system version |
| “Performance target met” | Performance command output with observed numbers compared with the named NFR |
| “Docs integrated” | Coverage Matrix row, owning document section, `CHANGELOG` entry and validation output |
| “Contract/API consistent” | Contract-test transcript and its output path |

### 7.2 Evidence storage and retention

Use one directory per activity:

```text
evidence/YYYY-MM-DD-<short-task-name>/
  command.txt              # command, environment, exit code and final transcript lines
  verification.md          # what was checked and the observed result
  screenshots/             # sample-data screenshots only, where appropriate
  hashes.txt               # SHA-256 values for generated, distributable artefacts
```

- Commit small text evidence and safe screenshots. Use the project’s approved artefact storage for larger
  files, then commit the immutable path and SHA-256.
- Never commit client data, secrets, installers, build output or large binaries as evidence.
- Evidence is retained so a later reviewer can reconstruct why a claim was accepted.
- A claimed run that did not happen is the most serious process violation: stop work and re-verify that
  session’s entire output before doing anything else.

## 8. Red flags and the response ladder

| # | Red flag | How you detect it |
|---:|---|---|
| 1 | Product code existed before recorded Phase 0 approval | Compare Git history with the Phase 0 approval record |
| 2 | Tests or golden files were weakened to pass | Review changes under `tests/` and golden paths against the spec change and approval |
| 3 | A specification changed after approval without an impact note or required approval | Compare `CHANGELOG` order, approval record and code commit order |
| 4 | A dependency was added outside ADR-001/ADR-002 | Inspect lockfile and dependency changes against the ADRs |
| 5 | A Coverage Matrix row says “integrated” but the owner document lacks the content | Open the cited section and compare it with the matrix claim |
| 6 | A green or done claim has no evidence | Read the session report or gate evidence paths |
| 7 | Client data, secrets, installers or large binaries were committed | Inspect the diff, `.gitignore` and secret/binary scan output |
| 8 | Work was built outside approved FRs | Ask for the quoted FR or specification section; no citation means no scope authority |
| 9 | P0 work is missing at a gate without an approved proposal | Compare priorities, gate checklist and backlog/cut records |
| 10 | `main` is red or branches live too long | Check repository status and branch history at session close |
| 11 | Users see raw exceptions or uncatalogued error messages | Run the message-catalog audit and inspect error screens |
| 12 | AI decides, changes data or auto-applies mappings | Inspect the mapping-queue tests and demo the human review step |
| 13 | Sample data was delivered to a client or its watermark was removed | Check the go-live checklist and output watermark evidence |

**Response ladder**

- **First violation:** stop the affected work, write an explanation and remediation plan in `SESSION_LOG.md`,
  then repair and verify it.
- **Repeated or severe violation:** for flags 1, 2, 6 or 7, stop all progress and re-verify the entire
  session output before any further work.
- **Data exposure:** follow the security incident procedure immediately; do not wait for a gate or a normal
  session report.

## 9. When work is stuck or a plan is failing

Stop after the **second failed attempt** or when work exceeds **twice its estimate**. Do not make a third
blind attempt. The session report records symptoms, evidence, attempts and the last green commit.

The engineer then gives you exactly these three choices:

| Choice | What it means | Choose it when |
|---|---|---|
| **A — Simpler approach within the specification** | Meet the same approved requirement with a less risky implementation | The original method is overcomplicated but the requirement is clear |
| **B — Timeboxed spike** | Run the documented short investigation to remove a specific technical uncertainty | The requirement is clear but feasibility or packaging risk is unknown |
| **C — Descope proposal** | Move non-never-cut work through the formal cut process and backlog, with impact stated | The value is lower than the delay and the item is not P0 or never-cut |

The recommendation must state which choice is safest and why. Only your explicit choice permits a new
attempt. The resulting decision goes into `18` or `27` before new code begins. `main` is returned to the
last green commit; it never stays red while the team is deciding.

## 10. Independent hand-check oracle for money

The engine’s tests are necessary, but an engine must also agree with a calculation made independently from
its source data and the written formula.

### 10.1 What happens at every phase gate

1. Pick one cost centre, one account and one period from the synthetic Golden Month.
2. Copy the required raw sample-export rows into the formula-visible workbook under `tests/oracle/`.
3. Use the formulas in `05_CALCULATION_SPEC.md`, not engine code, to calculate actual, budget, variance,
   variance percentage and any relevant forecast or exception result.
4. Compare every result with the app to the minor unit. A mismatch blocks the gate until it is classified and
   corrected.
5. Commit the worksheet and attach its path to the gate evidence.

The template is `tests/oracle/golden_month_hand_check_template.xlsx`. Its formulas remain visible so a
finance reviewer can inspect the calculation without running Python.

### 10.2 Real-data pilot check

At the Real-Data Pilot, repeat the same one-account check against the client’s own manual figure. The client
keeps their data in the isolated local environment; it never enters a cloud development session or this
repository.

### 10.3 What makes the oracle independent

- The source rows are from the raw sample export, not an engine API response.
- The formula comes from `05`, not copied from engine code.
- The workbook exposes its formulas, inputs and rounding.
- The reviewer compares minor-unit values, not screenshots or rounded headlines.

## 11. Convergence and change control

The official Addon 5 source is retained at
`project prompt/ADDON_5_OWNER_CONTROL_EVIDENCE_DATA_EGRESS_EXTENSION.md` with SHA-256
`cfbb69411d586194d2ad8ef6034a74e19bcb0ae976b466485adda75a97372b11`.

Kickoff plus Addons 1–5 are the frozen Phase 0 and v1 contract. A newly discovered need is an open question
first. It becomes a change only after your explicit approval and a numbered future addon. The team must
never invent an Addon 6, silently expand scope, or edit a requirement merely to match code.

## 12. Gate M — owner checks before Phase 0 approval

All twelve Addon 5 Section M checks must be evidenced before you approve Phase 0:

1. Coverage Matrix rows are integrated.
2. This handbook is complete.
3. Evidence rules and directory convention are in place.
4. The red-flag ladder is in place.
5. Development-time data-egress rules and the incident procedure are in place.
6. Golden Month blessing and regeneration rules are in the test plan.
7. Oracle procedure and worksheet template are in the acceptance path.
8. Repository, survivability, release-note and licensing controls are resolved.
9. The stuck protocol is in the session playbook.
10. The questionnaire is sendable and tracks answers.
11. The post-go-live loop uses the documented support placeholders.
12. The convergence/freeze notice is recorded.

The detailed checklist and evidence references are owned by `14_TESTING_QA_PLAN.md` §15.6.
