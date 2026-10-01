> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the twenty zero-compromise principles (Kickoff §3, Addon 1 §B); the session protocol
> (Kickoff §14 + Addon 1 §M) — reading order, change order, the regression gate, the session log; the
> Definition of Done and its enforcement; **quote-before-code** and the paraphrase ban (Addon 4 §B);
> approval recording and the post-approval change impact rule (Addon 4 §E.2/E.3); blocking questions
> (`18` §4.3); demo recipes and walkthroughs; prompt-edit discipline and feedback intake (Addon 3 §I.4);
> and the anti-pattern list
> **TL;DR (≤ 15 lines):**
> - This is the **working protocol**: how a session starts, what order changes happen in, what must be
>   true before a session ends, and what "done" means. Code standards are `17`; gates are `14`/`16`.
> - **Docs before code, always:** no product code until the Phase-0 set passes its gates and the owner has
>   approved it (Addon 4 §L.12). The next open item is `16` §1.3, and nothing else is started.
> - **The change order is fixed:** spec → `CHANGELOG` → code → traceability (`20`) → demo recipe. Never
>   reversed, never skipped (Kickoff §14.2).
> - **Quote before code:** the exact FR/section text is pasted into the session plan before implementing;
>   paraphrasing from memory is banned, and a silent spec is a blocking question, not an improvisation.
> - **A red suite ends the session** if calculation, import, rule, export or migration code was touched;
>   golden files and `expected_exceptions.csv` are never edited to make a test pass.
> - **Never:** weaken a test, hardcode demo data, invent requirements silently, skip validation or error
>   handling "for now", add an unapproved library or pattern, or build ahead of the roadmap.
> - **Every feature ships as a bundle:** spec + tests + its `SCR`/error-catalog entries + traceability +
>   changelog + a 3–6 step demo recipe. An incomplete bundle does not close.
> - **Approvals are recorded, dated and explicit:** `Phase <n> gate APPROVED — <who> — <date>` in
>   `CHANGELOG` **and** `SESSION_LOG`. Silence is never approval.
> - **After approval, nothing is free:** every spec change gets an impact note (affected FRs, docs, tests,
>   size S/M/L) before any code (Addon 4 §E.3).
> - **Blocking questions stop the thread:** ask with ≤ 3 options + a recommendation + the default, keep
>   working on unrelated items, and record the answer as a `DEC` row when it arrives.
> - **The client sees only the installed product** — demo scripts run on sample data, never on real data,
>   never from a developer session.

# 19 — Vibe-Coding Playbook

## 1. Purpose, ownership and how this playbook is used

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| The twenty principles and their consequences | **`19` (this document)** |
| The session protocol (start, during, end) and the session-log format | **`19`**, with Addon 1 §M |
| Quote-before-code, the paraphrase ban and the reading plan's use | **`19`**, with Addon 4 §B and `00_INDEX` §2 |
| The Definition of Done's *enforcement* (the text's owners are `02` §3.5 and `14` §14.3) | **`19`** |
| Approval recording and the post-approval impact rule | **`19`**, with Addon 4 §E.2/E.3 |
| Blocking-question handling in a session | **`19`**, with `18` §4.2/§4.3 |
| Demo recipes, the tabletop and cold-start walkthroughs | **`19`**, with `16` §11 |
| Prompt-edit discipline and client-feedback intake | **`19`**, with `10` §4 |
| Code standards and the review checklist | `17` |
| Gate checklists and evidence formats | `14` §15, `16` §5 |
| The next open item | `16` §1.3 |
| Client facts, assumptions and decisions | `18` |

### 1.2 Supremacy in a session

Within a working session this playbook's **process** rules bind every other document's *convenience*: if a
shortcut conflicts with §3 (the session protocol), §5 (change order) or §6 (approvals), the playbook wins.
The playbook never overrides a **content** rule: behaviour belongs to `02`/`05`/`06`/`07`, structure to
`09`, standards to `17`, and the gate checklists to `14`/`16`.

### 1.3 Who reads what

| Reader | Reads first | Then |
|---|---|---|
| A new AI session | `00_INDEX` §2/§10, this document, `16` §1.3 | The docs the open item names |
| A new human developer | `00_INDEX` §2/§3, `17`, this document | `01` → `02` → `03` → `09` → task docs |
| The project owner | This document §6 (approvals), `16` | The gate evidence pack |
| The consultant running support | `23`, `13` §7, `15` §9 | The diagnostics bundle |

## 2. The twenty principles (canonical list)

Each principle is binding; the right-hand column says what violating it costs, so the rule is never
mistaken for a preference.

| ID | Principle | Violation looks like | Cost |
|---|---|---|---|
| `P1` | **Docs before code.** No product code until the Phase-0 set passes its gates and is approved | "I'll write it and document it after" | The spec set becomes a description of whatever was built |
| `P2` | **The spec is the source of truth.** Behaviour changes go into the spec + `CHANGELOG` first | Code drifting silently from a doc | Numbers and copy diverge; the client is told the wrong thing |
| `P3` | **Deterministic money maths.** AI never computes, approves, posts or decides | Letting a model produce a total | Trust destroyed by one wrong figure |
| `P4` | **Offline-first, local-only.** No cloud, no telemetry, no auto-upload | A "helpful" analytics ping | The confidentiality guarantee breaks |
| `P5` | **Traceability.** Every displayed number drills to transactions and to its source file | An orphan figure | The analysis cannot be defended |
| `P6` | **Scope discipline.** Only the approved phase's work; new ideas go to `27`/`18` | Building ahead or opportunistically | The phase gate slips and the cut line is meaningless |
| `P7` | **Non-technical UX.** Guided flow, plain-language errors, help, confirmations, sample project | Jargon and dead ends | The analyst abandons the tool |
| `P8` | **"Potential exception", never "error confirmed."** The tool flags; humans decide | An exception treated as an accusation | Vendor relationships and trust are damaged |
| `P9` | **Quality bars are numbers.** Every NFR is stated and measured | "It feels fast" | The bar quietly disappears |
| `P10` | **Boring, testable code.** No speculative abstraction, no unapproved frameworks | A plugin system nobody asked for | Complexity with no owner |
| `P11` | **The monthly rhythm is first-class.** The recurring cycle is designed, not assumed | One-month-thinking features | The tool breaks at the second month end |
| `P12` | **All-or-nothing imports.** Staging + atomic commit; a crash never leaves half a month loaded | A partially committed import | Every downstream number is suspect |
| `P13` | **Nothing is silently discarded.** Rejected/quarantined rows appear in the report with counts | A skipped sheet no one mentions | The client's numbers quietly lose rows |
| `P14` | **Versioned everything the user edits.** Mappings, thresholds, master data, assumptions, prompts | An in-place overwrite | The client cannot tell what changed or revert |
| `P15` | **Releases are upgradeable.** Migrations tested on a real prior-version project | "Reinstall and recreate the project" | The product is not a product |
| `P16` | **End-user documentation is a deliverable.** Guide + in-app help ship with the feature | Docs written at the end | The handover fails |
| `P17` | **Supply-chain hygiene.** Pinned deps, licence review, SBOM-lite, no secrets, no binaries without review | A convenient unvetted package | Licence or security exposure |
| `P18` | **Imported content is hostile data.** Descriptions and names are untrusted in validation, logs and prompts | Injecting a description into an AI prompt | Prompt injection or poisoned output |
| `P19` | **Colour is never the only signal.** Signs, symbols or text carry the meaning too | A red/green-only variance | Colour-blind users and prints lose the meaning |
| `P20` | **Tabletop walkthrough before approval.** Narrative a full month end using only the documents | Skipping to "it looks complete" | Gaps reach the client instead of the gate |

**How the principles are enforced, not admired:** `P1`/`P2`/`P6` by the session protocol (§3) and the
change order (§5); `P3` by the single-formula-owner rule and the AI boundaries in `10`; `P4`/`P17`/`P18`
by `13`'s statements and tests; `P5` by `20`'s chain and the drill tests; `P7` by `08` §16/§17 and the
wording audit; `P8` by `06`'s catalogued wording; `P9` by `14` §3 and the gate contract (`16` §5.1);
`P10`/`P12`/`P13`/`P14`/`P19` by `17`'s standards and `14`'s tests; `P11`/`P15` by `02`/`09` §13 and the
upgrade fixture; `P16` by `22`/`23`; `P20` by `16` §11.2.

## 3. The session protocol

### 3.1 Start of a session (in this order)

| # | Step | Why |
|---|---|---|
| 1 | Read `00_INDEX` §2 (reading plans) and §10 (current phase status) | Context, and what "now" is |
| 2 | Read the `CHANGELOG` entries since the last session | What changed and why |
| 3 | Read the `SESSION_LOG` tail (the last entry, plus anything it points to) | The memory bridge; do not re-derive |
| 4 | Read **the next open item in `16` §1.3** — exactly one item | The whole session serves this item |
| 5 | Read **only the docs that item names**, plus this playbook | Reading everything is drift's friend |
| 6 | Write the **session plan**: the item, the quote(s), the files to touch, the tests to write, the evidence to produce | A plan that cannot be quoted is not a plan |
| 7 | Run `scripts/check` (or the recorded baseline) before changing anything | You cannot tell "green before, red after" without the before |

**Quote before code.** Paste the exact spec text being implemented (FR ID + the calc/rule section) into
the session plan. Every commit message and `SESSION_LOG` entry cites those IDs. If the spec is silent on a
behaviour question, stop and raise it (§7) — never improvise (Addon 4 §B.3/§B.5).

### 3.2 During the session

| Rule | Detail |
|---|---|
| Change order | spec → `CHANGELOG` → code → traceability (`20`) → demo recipe. A code commit without its spec/`CHANGELOG` sibling is out of order (§5) |
| One thing at a time | Finish the open item; unrelated discoveries go to `27`/`18` immediately (with an ID) and are not built |
| Small commits | Conventional Commits; docs and code separated; commit often enough that each commit tells one story (`17` §11.2) |
| Tests as you go | New behaviour arrives with its test in the same change (`17` §9.2); a test written later is a test that documented, not protected |
| Ask when blocked | The four blocking categories of `18` §4.2; ask early with the §7 format; keep working on unrelated parts |
| No silent surprises | A deviation, a discovered gap, a changed assumption: recorded in `SESSION_LOG` and the owning doc, not carried in someone's head |
| Keep the plan current | The plan is a living checklist; if the item grows beyond its intent, stop and re-scope through `16`/`18` |
| Sample data only | Never develop or test against client data; the corpus is synthetic (`14` §16) |

### 3.3 End of a session — the closing checklist

| # | Step | Evidence |
|---|---|---|
| 1 | The full test suite is green **if** calculation, import, rule, export or migration code was touched (the regression gate) | Transcript recorded in `SESSION_LOG` |
| 2 | Golden files, `expected_exceptions.csv` and thresholds are unchanged unless the spec changed (and then the `CHANGELOG` says so) | Diff review |
| 3 | `scripts/check` passes in the form the session needs (`--fast` while iterating; full before a gate) | Transcript |
| 4 | The `CHANGELOG` entries exist for every doc/behaviour change | `CHANGELOG` |
| 5 | The `SESSION_LOG` entry is written (§3.4) | `SESSION_LOG` |
| 6 | `20`'s traceability rows for touched FRs are updated | `20` |
| 7 | The demo recipe for the touched feature is recorded | `SESSION_LOG` |
| 8 | The next open item in `16` §1.3 is advanced **in the same commit** that closes it | `16` §1.3 |
| 9 | Deferred work has IDs (`27`) and questions have defaults (`18`) | `27`, `18` |
| 10 | Nothing is left uncommitted that the next session would have to guess about | `git status` |

### 3.4 The `SESSION_LOG` entry format

```
## Session <nnn> — <date>

### Objective
<the next open item, quoted from 16 §1.3>

### What changed
| File | Change |

### FRs / areas touched
- <FR IDs and areas>

### Spec sections integrated in this session
- <quotes or precise references>

### Test results
- <transcript summary; red items are never omitted>

### Decisions taken this session
- <DEC IDs, or "none">

### Blocking questions
- <with owner and date, or "none">

### Next step
<the new open item, in 16 §1.3's words>

### Deferred to backlog / open questions
- <BL/OQ IDs>
```

**Append-only.** A wrong past entry is corrected by a new entry that says so — history is evidence, not a
draft (Addon 1 §M.1).

### 3.5 What ends a session immediately

1. A **red suite** in the touched area (fix it or revert; do not continue building on red).
2. A newly discovered **blocking question** touching money semantics, data loss or a client fact (`18`
   §4.2) — stop that thread and ask.
3. A **security or data incident** (a secret committed, client data in the repo, an unexpected outbound
   call): stop, record it, and follow `13` §12 (`17` §8) before anything else.
4. A **spec contradiction** that changes behaviour: stop the implementation, fix the owning doc first
   (`00_INDEX` §6 conflict rule), then continue.

## 4. The Definition of Done and its enforcement

### 4.1 Per feature / FR

`02` §3.5 owns the text; `14` §14.3 owns the evidence formats. The enforcement rule is below, and it is
literal:

| Requirement | Enforcement |
|---|---|
| Spec updated | The change's doc diff exists before the code diff |
| Tests written | The test appears in the same change; coverage bars hold (`14` §13.2) |
| Works on the sample project | A demo recipe proves it in 3–6 steps on sample data |
| Error/empty/loading states handled | The screen's state-matrix rows exist (`08` §17) |
| Traceability updated | `20` rows filled (FR → spec → screen → API → test) |
| `CHANGELOG` entry | Present, with the reason |
| Demo recipe recorded | In `SESSION_LOG`, per Addon 2 §F.5 |

**An incomplete bundle does not close.** A feature without its error catalog entry, its `SCR-ID`, its demo
recipe or its tests is not "nearly done" — it is not done (Addon 3 §I.5).

### 4.2 Per phase

The Definition of Done for a phase is `16` §5.1's universal gate contract plus the phase-specific list in
`16` §6. The playbook adds one rule: **the phase's demo script is written at the start of the phase**, so
the phase is built to be demonstrable (`16` §11.1).

### 4.3 Demo recipes (Addon 2 §F.5)

- 3–6 numbered steps on **sample data**, each with the expected result.
- Short enough to run in a review, specific enough that a different person gets the same result.
- Recorded in `SESSION_LOG` when the feature closes and rehearsed before the gate.
- A demo recipe that needs a terminal, a database client or an Internet connection is not a demo recipe.

## 5. Change control and the post-approval impact rule

### 5.1 The order of a change (never reversed)

```
1. Quote the spec (FR ID + section text) into the session plan.
2. If behaviour changes: update the owning spec + CHANGELOG (docs first).
3. Write/adjust the tests.
4. Write the code.
5. Update traceability (20).
6. Record the demo recipe (SESSION_LOG).
```

### 5.2 The impact rule (Addon 4 §E.3)

After Phase 0 approval, **every** spec change gets an impact note **first**, recorded in the `CHANGELOG`
entry: affected FRs · affected docs · affected tests · size (`S`/`M`/`L`) · the reason. `L` changes are
escalated before any work starts. No impact note, no code.

### 5.3 What else needs a decision before code

| Situation | Before code |
|---|---|
| A behaviour question the spec does not answer | A blocking question (`18` §4.3) or a `DEC` row |
| A new dependency, pattern or top-level folder | An ADR (`09` §3, `17` §7.1) |
| A schema change | `03` updated, migration planned, version bump, backup prompt tested (Addon 1 §M.4) |
| A change to a promise (offline, disclaimer, never-cut list) | The owning doc + the owner's approval; never a quiet edit |
| A change to a prompt template | The prompt-edit discipline of `10` §4 (versioned, reviewed, tested) |
| A cut or deferral | The cut process (`02` §3.4) with a `27` entry and a trigger |

### 5.4 Client feedback intake (Addon 3 §I.4)

Relayed feedback is **logged before any code**: what was said, who said it, which doc/FR it touches, and
whether it is a defect, a change request or a question. Then it follows §5.3 like anything else. Feedback
does not enter the product through a chat message.

## 6. Approvals and gates

### 6.1 What an approval is

| Aspect | Rule |
|---|---|
| Explicit | An approval is a recorded line, never an inference. Silence, a thumbs-up emoji or "looks fine" in passing is **not** an approval |
| Recorded | `Phase <n> gate APPROVED — <who> — <date>` in `CHANGELOG.md` **and** `SESSION_LOG.md` (Addon 4 §E.2) |
| Scoped | It approves the state presented at that moment; material changes after it re-open the gate via §5.2 |
| Evidence-backed | Every approval references its evidence pack (`16` §5.2); an approval without evidence is a wish |
| Hard gates | Phase 0 (after `GATE-01`…`05`), the packaging spike (`GATE-06`), each phase gate (`GATE-07`…`12`), the real-data pilot (`GATE-13`), UAT (`GATE-14`), go-live (`GATE-15`) |
| The Phase-0 stop | **No product code before the recorded Phase-0 approval** (Addon 4 §L.12) — this is the one rule with no exception |

### 6.2 The stop-and-present pattern (every gate)

1. Freeze the work; run the gate checklist (`16` §5.1 + the phase list).
2. Assemble the evidence pack (`16` §5.2).
3. Write the gate summary: what the phase delivered, the estimate variance, the P1/P2 gaps with decisions,
   the new risks, the next phase's plan.
4. **Stop.** Present and wait for the recorded approval. Do not start the next phase's code.
5. On approval: record the line, advance `16` §1.3, and begin the next item.
6. On a gap: the gap list becomes the next open item; nothing downstream starts.

### 6.3 Non-gate approvals the owner gives

| Situation | Approval needed |
|---|---|
| A cut or deferral outside the never-cut list | Yes, with the impact note (`02` §3.4) |
| A never-cut item at risk | Yes — and the answer to "can we cut it?" is no (`16` §9.2) |
| A waiver of a blocking performance/coverage regression | Yes, recorded in the `CHANGELOG` with the reason (`14` §8.3) |
| A change to the canonical disclaimer or any client promise | Yes |
| An `L`-sized post-approval change | Yes, before code (§5.2) |
| Anything else in the docs' change-control sections | Per the owning doc |

## 7. Blocking questions and escalation

### 7.1 When to stop and ask (`18` §4.2)

Stop the **thread**, not the session, when the answer could change money semantics, data loss, UX flow or
a client fact. Write the question in the `18` §4.3 format: one paragraph of context, ≤ 3 options with
trade-offs, a recommendation and the default if unanswered.

### 7.2 What "continue with unrelated work" means

| Allowed while waiting | Not allowed |
|---|---|
| Work that does not depend on the answer, from the same open item | Guessing the answer and building on it |
| Tests/documentation that are true under every option | Writing code that hard-codes one option |
| Preparing both branches of the decision as a note | Presenting the guess as a decision |
| Raising the question at the next gate if it is not urgent | Letting the question go unrecorded |

### 7.3 Escalation ladder in a session

1. **The spec** — the first place to look; most questions are answered there (`00_INDEX` §6).
2. **The registers** — `18`'s `OQ`/`DEC` and the ADR index (`09` §3).
3. **The owning doc's change-control section** — whether the question is a change or a clarification.
4. **The project owner** — for anything that changes a promise, a scope line or a client fact.
5. **The consultant's judgement** — only for what stays inside an existing decision; recorded as a `DEC`
   row if it sets precedent.

### 7.4 Timeboxing a question

A question that remains unanswered past the gate that needs it becomes a **gate item** (owner + date), not
a silent default (`18` §4.2). A question that stays unanswered and stops a phase is escalated explicitly,
in writing, in the gate summary.

## 8. Walkthroughs, demos and evidence

### 8.1 The three levels

| Level | What it is | When |
|---|---|---|
| **Demo recipe** | 3–6 steps on sample data for one feature | Every feature close (§4.3) |
| **Phase demo script** | 3–5 minutes covering the phase's value end to end | Written at phase start, run at the gate (`16` §11.1) |
| **Tabletop + cold-start walks** | The whole month end narrated on paper, then a no-context person attempting the guided path | Closing Phase 0 (`16` §11.2), repeated at the pilot |

### 8.2 Evidence discipline

- Every gate number comes from an artefact: a transcript, a JSON report or a signed checklist. No "it felt
  fast" (`14` §1.2 item 4).
- Screenshots and logs are redacted by the same rules as the diagnostics bundle (`13` §7) before they leave
  the machine.
- Real data never appears in demos, screenshots, issues or the repo (`14` §16); the pilot is the only real
  data moment and it is governed by `28`.
- A failed check is recorded in the gate summary with its cause — never omitted, never softened.

## 9. Working with the AI session

### 9.1 How to brief a session

1. Give it **the open item**, not a wish list.
2. Point it at the reading plan (§3.1) and let it read; do not paste spec text out of context.
3. Require the quote in the plan before it writes code (§3.1).
4. Require the change order (§5.1) literally: docs first, then tests, then code.
5. Require the session to stop at a blocking question rather than guess.
6. Require the `SESSION_LOG` entry and the next-item advance before the session ends.

### 9.2 The rules that keep AI sessions honest

| Rule | Why |
|---|---|
| **Paraphrase ban** (Addon 4 §B.5) | Behaviour questions are answered by quoting the spec, never from memory |
| **No invented requirements** (Kickoff §14.5) | A discovered gap becomes an `OQ`/`DEC` row, never a silent feature |
| **No fabricated numbers** | Every number in code, tests and docs comes from the spec or a test artefact |
| **No test weakening** | Expectations change only through the spec path (`14` §1.2 item 3) |
| **Context discipline** | Summarise forward into `SESSION_LOG` instead of re-reading everything; the log is the memory bridge |
| **Told to be lazy about reading is not a licence to guess** | The reading plan is the minimum; the open item's docs are read in full |
| **Small commits, clear messages** | History is the audit trail of the process (`17` §11.2) |
| **Escalate, don't improvise** | §7 exists so that "I was unsure" never becomes a shipped behaviour |

### 9.3 Prompt templates as product artefacts (Addon 3 §I.4, `10` §4)

Prompt edits follow the same protocol as code: versioned, reviewed, tested against the fixtures, recorded
in the `CHANGELOG`, and never hand-edited in a running installation without the version bump.

## 10. Anti-patterns (the never list)

| # | Anti-pattern | Why it is fatal here |
|---|---|---|
| 1 | Building ahead of the roadmap | Breaks `P6`, invalidates the phase gate, wastes the estimate |
| 2 | Editing a test, golden file or `expected_exceptions.csv` to pass | The suite stops being evidence (`P9`, `14` §1.2) |
| 3 | Silent scope expansion ("while I'm here…") | Unapproved work with no traceability |
| 4 | Hardcoding demo numbers or client values | `P3`/`P9`; the demo lies |
| 5 | Skipping validation/error handling "for now" | The happy path is not the product (`P7`) |
| 6 | Adding a library or pattern without an ADR | `P10`/`P17`; the stack is closed |
| 7 | Docs written after the code | Breaks `P1`/`P2`; the client is told the wrong thing |
| 8 | Re-running until it randomly passes | Flakiness hidden, distrust earned |
| 9 | Hiding a failure behind a fallback without saying so | The fallback becomes the product's real behaviour |
| 10 | Letting AI output carry a number | `P3`; the single rule AI may never break |
| 11 | Treating a warning as a pass | The warning is the cheap warning |
| 12 | Leaving a gate red and starting the next phase | The evidence chain is broken |
| 13 | Committing a secret "temporarily" | `P17`; rotation is the only fix |
| 14 | Using real client data for development | `P4`/`14` §16 |
| 15 | Taking a question as answered because it is convenient | `19` §6.1: silence is not approval |
| 16 | Writing a spec to match the code | `P2` reversed — the most expensive form of drift |

**The test for any doubtful action:** if it would need a `CHANGELOG` entry to be honest and it does not
have one, it is an anti-pattern in progress.

## 11. Roles and who decides what

| Role | Decides | Does not decide |
|---|---|---|
| **Project owner** (the client-side sponsor / the user in this repo) | Scope, cuts, approvals, commercial terms, priorities | Implementation detail; formulas (`05`) |
| **Consultant / engineer** (builds) | Technical execution inside the approved spec | Behaviour changes without a spec change; scope |
| **FP&A analyst** (the primary user) | Workflow preferences, wording, thresholds, master data | Formulas; the product's rules |
| **Accounting owner** | Exception severity/wording judgement, tie-out acceptance | Scope; the roadmap |
| **Client IT** | Installation mechanics, environment constraints | The product's data behaviour |
| **AI session** | Nothing on its own: it proposes, quotes, implements and records | Anything a document does not authorise |

**One-writer rule:** a document has one owner (`00_INDEX` §5); a consensus edit is how contradictions
start.

## 12. Onboarding: a new session or a new human

### 12.1 The 30-minute ramp

| Minute | What to read |
|---|---|
| 0–5 | `00_INDEX` §2 (reading plans) and §10 (current status) |
| 5–10 | The last two `CHANGELOG` entries and the `SESSION_LOG` tail |
| 10–15 | `16` §1.3 (the next open item) and §2 (the phase model) |
| 15–25 | This playbook §2, §3, §5, §6 |
| 25–30 | The docs the open item names, with the quote in hand |

### 12.2 What surprises newcomers (stated up front)

1. **No code before approval** — the most likely mistake in this repo.
2. **The registers are the truth, not the chat** — decisions live in `18`, not in a message thread.
3. **Docs and code are separate commits**, docs first.
4. **The never-cut list is literal** — nine properties with no waiver path.
5. **Every demo runs on sample data**, and every number comes from an artefact.
6. **Failures are recorded, not hidden** — a red item in `SESSION_LOG` is normal; an omitted one is not.

### 12.3 Where the current state lives

| Question | Answer lives in |
|---|---|
| What are we doing now? | `16` §1.3 |
| What changed lately? | `CHANGELOG`, `SESSION_LOG` |
| What is decided? | `18` §5; ADRs in `09` §3 |
| What is unknown? | `18` §4 |
| What is deferred? | `27` |
| What proves it works? | `14` §15/§16, the gate evidence packs |

## 13. Open items, deferrals and assumptions

| Item | Status |
|---|---|
| The exact approval phrase for non-gate changes | Follows the same pattern: `<change> APPROVED — <who> — <date>` in `CHANGELOG` + `SESSION_LOG` |
| Session numbering | Continuous across the project (`Session 001` …); a new day is not a new number unless a new session starts |
| The human-readable summary for the client at each gate | Owned by `16` §10 (client-visible checkpoints) and `28` (UAT/go-live) |
| Tooling for the reading plan enforcement | None: the protocol relies on the recorded plan and the log (to be revisited if a session drifts) |
| Feedback-intake template | Will be finalised with `23`'s support flow |

**Assumptions.** (a) Sessions are run with an AI assistant against this documentation set; (b) the project
owner is reachable for approvals and blocking questions within the gate window; (c) the sample-data corpus
exists before Phase 1 work (Addon 4 §L.7); (d) the registers in `18` stay current because they are gate
artefacts.

## 14. Change control and cross-document obligations

### 14.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| The gate checklists and evidence formats stay authoritative in `14`/`16`; this document only enforces them | `14` §15, `16` §5 |
| The DoD text stays in `02` §3.5; this document enforces it and never restates the criteria differently | `02` |
| The next open item is updated in the same commit that closes it, and the pointer stays in `16` §1.3 | `16` |
| Approvals are recorded in `CHANGELOG` + `SESSION_LOG` with the §6.1 pattern | `CHANGELOG`, `SESSION_LOG` |
| Blocking questions use the `18` §4.3 format; answers become `DEC` rows | `18` |
| Prompt edits follow `10` §4; feedback intake is logged before code | `10`, `23` |
| Demo recipes are recorded per feature; phase demo scripts are written at phase start | `16` §11.1, `SESSION_LOG` |
| `.session-plan` artefacts (if any) are working files, never committed | `17` §11.3 |

### 14.2 Changes to this document

| Change | Requires |
|---|---|
| A new principle | An explicit owner decision, a `CHANGELOG` entry and a consequence row (§2) — principles are added, never quietly edited |
| A session-protocol change | Addon 1 §M and Addon 4 §B still bind; the change is recorded here and in `00_INDEX` §2 if reading order changes |
| An approval-mechanics change | Addon 4 §E.2/E.3 still bind; `CHANGELOG` entry |
| A gate-mechanics change | `14`/`16` first (they own the checklists), then this document |
| Any change here | `CHANGELOG` + `SESSION_LOG`; the next gate re-runs the checklists in full |

**Frozen constants owned by this document:** the twenty principles and their consequences (§2) · the
session start/during/end protocol and the log format (§3) · the enforcement of the Definition of Done
(§4) · the change order, the impact note and what needs a decision before code (§5) · the approval pattern
and the stop-and-present rule (§6) · the blocking-question handling (§7) · the walkthrough and evidence
levels (§8) · the AI-session rules and the paraphrase ban (§9) · the anti-pattern list (§10) · the roles
(§11) · the 30-minute ramp (§12).
