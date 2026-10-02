# ADDON 5 — OWNER CONTROL, EVIDENCE & DATA-EGRESS EXTENSION
_Extension to the FP&A Month-End Copilot kickoff prompt and Addons 1–4. All six documents together are the contract; where they overlap, later addons add requirements and never remove them. Further gaps become proposals for Addon 6 via `docs/18_…OPEN_QUESTIONS.md` — never silent scope expansion._

---

## SECTION A — HOW THIS ADDON WORKS & CONVERGENCE

1. Kickoff + Addons 1–5 = the **spec of record**. Implement all six.
2. Integrate every item below into existing Phase 0 documents (or new doc `30`) with a `CHANGELOG.md` entry — no parallel documentation.
3. Extend the **Addon Coverage Matrix** in `docs/00_INDEX.md` with Addon 5 rows; the quality gate fails if any row is not "integrated".
4. **Convergence notice:** with this addon the prompt set is complete for Phase 0 and v1. After integration, treat the six documents as a **frozen contract** — new needs route through OPEN_QUESTIONS → my explicit approval → a numbered addon. Do not self-generate Addon 6.
5. Re-run all quality gates (kickoff + Addon 1 O + Addon 2 I + Addon 3 J + Addon 4 K + Section M below) before requesting approval.

---

## SECTION B — NEW DOCUMENT: `30_OWNER_OPERATING_HANDBOOK.md`

Written **for me, the project owner** — plain language, no jargon. Contents:

1. **Session cadence:** what I do before a session (pick the next roadmap item), during (nothing — you work), and after (review the session report + evidence, approve or reject).
2. **Session-report format** (top of SESSION_LOG, newest first): `Done (with FR IDs) | Evidence refs | Tests status (with transcript path) | Decisions needed from me | Next session plan | Risks/blocked`. A session without this block is not closed.
3. **My 5-minute review checklist per session:** evidence present? FR citations valid? git diff sane (no surprise files/deps)? `scripts/check` transcript green? spec changes recorded before code? Coverage Matrix updated?
4. **My Phase 0 review guide:** reading order with time budget — read fully: `01_PRD`, `05_CALCULATION_SPEC`, `06_EXCEPTION_RULES_CATALOG`, `29_CLIENT_REQUIREMENTS_PACK`, `PHASE0_SUMMARY`; skim: gates + matrix; trust-but-verify: everything else via link-check + spot samples. Total budget ≈ half a day.
5. **Spot-check sampling:** each phase I pick ≥2 FRs at random from the traceability table and demand a live demo against their acceptance criteria (uses existing demo recipes).
6. **Red-flag list** (Section D) and what to do when I see one.
7. **Stuck-protocol escalation** (Section I): the three options I'll be offered and how to choose.
8. **Hand-check oracle procedure** (Section G): how I verify money independently of the engine's own tests.

---

## SECTION C — EVIDENCE & CLAIMS PROTOCOL (doc 30 owns; doc 19 cross-references)

**No claim without evidence.** Every status claim in SESSION_LOG, gates, or reports must reference an artifact:

| Claim type | Required evidence |
|---|---|
| "Tests green" | command + exit code + last ~20 lines of transcript, saved under `evidence/<date>-<task>/` |
| "Feature done" | FR IDs + commit hash + demo recipe run with observed output |
| "UI works" | screenshot (sample data only) at `evidence/` path |
| "Installer builds" | artifact path + SHA-256 + machine/OS used |
| "Perf target met" | perf script output with numbers vs NFR table |
| "Docs integrated" | Coverage Matrix row + CHANGELOG entry hash |
| "Contract/API consistent" | contract-test transcript |

- Gates **reject unevidenced claims** — "should be green" is a violation, not a status.
- Evidence is committed (small text/paths; screenshots via repo-appropriate storage) so any later dispute is resolvable from the repo alone.
- Lying about evidence (claiming a run that didn't happen) is the single most severe violation — treat as stop-work and full re-verification of the session's work.

---

## SECTION D — VIOLATION / RED-FLAG LIST (doc 30 owns; consolidates enforcement across all six docs)

| # | Red flag | Detection |
|---|---|---|
| 1 | Product code before recorded Phase 0 approval | git history timestamps vs approval entry |
| 2 | Tests edited/weakened to pass; golden files changed without blessed regeneration | git diff on `tests/` + golden paths; Section F rules |
| 3 | Spec changed after approval without impact note / approval for `L` | CHANGELOG vs code commit order |
| 4 | Dependency added outside ADR-001/002 | lockfile diff vs ADR list |
| 5 | Coverage Matrix row marked "integrated" without corresponding doc edits | spot audit: row → doc section exists |
| 6 | Green claims without Section C evidence | SESSION_LOG/gate review |
| 7 | Client data, secrets, installers, or large binaries committed | `.gitignore` + pre-commit secret/binary scan (Addon 1 I) |
| 8 | Scope built outside FRs (no citation possible) | quote-before-code rule (Addon 4 B.3) |
| 9 | Silent under-delivery (P0 gaps at gate without proposal) | gate checklist vs priorities |
| 10 | `main` red, or long-lived branches | repo state at each session end |
| 11 | Raw exceptions/tracebacks shown as UX; error messages not in catalog (doc 26) | message-catalog audit |
| 12 | AI features making decisions/auto-applying mappings (never-cut behavior) | code review + mapping-queue tests |
| 13 | Sample data delivered to client / watermark removed | go-live checklist item (Addon 4 H) |

**Response ladder:** 1st violation → stop work, written explanation in SESSION_LOG, remediation plan; repeated or severe (1, 2, 6, 7) → re-verify that session's entire output before any further progress.

---

## SECTION E — DEVELOPMENT-TIME DATA-EGRESS RULES (docs 13/19 — governs the *development process*, not just the app)

1. **Real client data never enters any cloud agent, LLM, web form, or third-party service** — including this development session. Development, tests, demos, and screenshots use **sample/synthetic data only**.
2. If structure of a real file is needed during development, share **metadata only** (column names, row counts, data types) — never data rows, vendor names, or amounts.
3. The installed app processes real data only in **local-only mode** on an isolated environment (consultant's or client's machine) per Addon 1/2 security rules; the **Real-Data Pilot** (Addon 4 F) runs there — not in any cloud-hosted dev sandbox.
4. AI-in-app calls with real data follow the redaction policy (Addon 1 I) — and remain disabled unless explicitly enabled for that session.
5. Violating E.1 is severity-1: stop everything, assess exposure, log the incident in doc 13 and SESSION_LOG.

---

## SECTION F — GOLDEN MONTH BLESSED-REFERENCE WORKFLOW (doc 14)

1. Select one sample-data month as the **Golden Month** (e.g., FY26-P09) covering actuals + budget + forecast + exceptions.
2. At the first complete build, generate its **full artifact set**: engine JSON outputs, UI API responses, exported Excel, generated PPT, exception register, forecast table, validation report — and the owner **blesses** them once (approval recorded per Addon 4 E.2).
3. From then on, **every build** produces a machine diff vs the Golden set; any difference is either (a) an intended spec change → regenerate golden **with approval + impact note first**, or (b) an unintended regression → fix before proceeding.
4. Golden Month files live under `tests/golden/`, regenerated only by `scripts/regen-golden` (whose use logs the approver + date).
5. This is the strongest single guard against slow, silent drift across 30 docs and many sessions.

---

## SECTION G — INDEPENDENT ORACLE SPOT-CHECKS (docs 14/28)

The engine's own tests only prove it agrees with itself. Add an **independent oracle**:

1. At every phase gate, produce a **hand-check worksheet**: one cost centre × one account × one period, recomputed from the raw sample export in a plain spreadsheet, formula-visible.
2. The app's numbers must match the worksheet **to the minor unit**; the worksheet (as `.xlsx` with live formulas) is committed under `tests/oracle/`.
3. At the Real-Data Pilot, the same procedure runs against the client's own manual figure for one account — reinforcing the tie-out (Addon 4 F).
4. The oracle worksheet is authored from the spec's formulas (doc 05), not copied from engine code — otherwise it proves nothing.

---

## SECTION H — REPO, RELEASE & COMMUNICATION HYGIENE (docs 17/01/24)

1. **Never in git:** installers/build artifacts, client data (real), secrets, large binaries. Sample data is **generated by script**, not committed as blobs. Releases are tagged; artifacts distributed outside the repo with SHA-256 (doc 24).
2. **Repo survivability:** a second remote or weekly archive copy of the repository (with history) — the project must survive losing the primary dev machine (pairs with fresh-clone test, Addon 4 I.2).
3. **"What's New" note per release:** short client-facing summary generated from the CHANGELOG (plain language, no FR IDs), delivered with each installer (doc 24 owns template; doc 22 links).
4. **Licensing mechanism decision** (doc 01): default = **none** (perpetual build, no activation — scope discipline); if you want usage control (expiry/key), record it as an explicit PRD decision with backlog entry — never improvised mid-build.

---

## SECTION I — STUCK / ROLLBACK PROTOCOL (doc 19)

When a task fails repeatedly or blows past its estimate:

1. **Stop after the 2nd failed attempt** (or 2× estimate) — no third blind attempt. Log symptoms + what was tried.
2. Roll back to the last green tag/commit; `main` never stays red while "thinking".
3. Offer me exactly three options: **(a)** simpler approach within spec, **(b)** spike per Addon 4 I.1 to de-risk, **(c)** descope proposal via the cut process (Addon 2/4 D) — with your recommendation.
4. Only my choice proceeds; the decision lands in `18` Decided (or `27_BACKLOG`) before new code.

---

## SECTION J — QUESTIONNAIRE ADMINISTRATION (doc 21)

- Doc 21 doubles as a **sendable form**: each question formatted so it can be copied to an email/Teams message as-is (question | why it matters | our default if unanswered).
- Add a **response tracker table** (question | sent date | answer | source person | default still active?); answers update the owning doc + move items in doc 18 to Decided.
- Defaults are time-limited: flagged items older than N days before go-live get a final "confirm or we ship with default" sweep (record in doc 28).

---

## SECTION K — POST-GO-LIVE OPERATIONS LOOP (docs 23/24/27)

1. **Intake:** client reports issue → diagnostics zip (Addon 1) → classify S1–S4 (doc 28 severities apply post-go-live too) → log in doc 28 defects list.
2. **Response expectations:** stated by me in doc 23 (E.4 of Addon 3) — placeholder until I define them.
3. **Fixes:** normal spec-first flow; released via doc 24 checklist + What's New note (H.3).
4. **Requests/enhancements:** always → `27_BACKLOG` with trigger; never direct-to-code from client conversations (feedback intake rule, Addon 3 B.2/19).

---

## SECTION L — DOCUMENT UPDATES

| Doc | Add |
|---|---|
| `00_INDEX` | Source-of-truth row: "Owner control, evidence, red flags → `30`"; Addon 5 Coverage Matrix rows |
| `01_PRD` | Licensing mechanism decision (H.4) |
| `13_SECURITY_PRIVACY` | Dev-time egress rules (Section E) as first-class policy; incident procedure |
| `14_TESTING_QA_PLAN` | Golden Month workflow (F); oracle spot-checks (G) |
| `17_CODING_STANDARDS` | Repo exclusions (H.1), second-remote policy (H.2) |
| `19_VIBE_CODING_PLAYBOOK` | Evidence obligation (C), red-flag response ladder (D), stuck protocol (I); cross-ref doc 30 |
| `21_CLIENT_ONBOARDING_QUESTIONNAIRE` | Sendable-form format + response tracker (J) |
| `23/24/27` | Post-go-live loop (K); What's New template (H.3) |
| `28_ACCEPTANCE_…` | Oracle worksheet attached at gates (G.3) |
| `SESSION_LOG` (root) | Session-report header format per doc 30 (B.2) |

---

## SECTION M — PHASE 0 QUALITY GATE DELTAS (run IN ADDITION to all previous gates)

- [ ] Coverage Matrix has Addon 5 rows; all "integrated".
- [ ] `30_OWNER_OPERATING_HANDBOOK.md` complete: cadence, session-report format, 5-minute checklist, Phase 0 review guide, spot-check sampling, red flags, stuck options, oracle procedure.
- [ ] Evidence matrix (C) recorded in doc 30 + cross-referenced in 19; `evidence/` directory convention defined.
- [ ] Red-flag list (D) present with response ladder.
- [ ] Dev-time egress rules (E) in doc 13 with incident procedure.
- [ ] Golden Month workflow + blessing mechanics (F) in doc 14; `scripts/regen-golden` planned.
- [ ] Oracle spot-check procedure + worksheet template (G) in docs 14/28.
- [ ] Repo exclusions, second-remote policy, What's New template, licensing decision (H) resolved.
- [ ] Stuck protocol (I) in doc 19 with the three-option escalation.
- [ ] Questionnaire sendable-form + response tracker (J) present.
- [ ] Post-go-live loop (K) documented with my placeholders for response times.
- [ ] Convergence/freeze notice (A.4) recorded in `00_INDEX` + doc 19.

---

## SECTION N — UPDATED IMMEDIATE NEXT ACTIONS (supersedes Addon 4 Section L)

1. Create the repo skeleton (folders + `.gitkeep` + root README + empty `evidence/`) — nothing else.
2. Write original Phase 0 docs `00 → 20` + `CHANGELOG.md`.
3. Integrate Addon 1 (docs `21–25`), Addon 2 (doc `26` + ADR-002), Addon 3 (docs `27–28` + prompt texts + inventories), Addon 4 (doc `29` + matrices + priorities) — each with its additions.
4. Integrate **this addon**: doc `30_OWNER_OPERATING_HANDBOOK`, Section L rows, egress rules, Golden Month + oracle plans.
5. Build `sample-data/` — D365-style export + two non-D365 shapes + `.xlsx` templates + ~40 planted exceptions + `expected_exceptions.csv` + `malformed/` corpus + `--scale 250000` mode — watermarked, project-typed, generated (not committed as blobs).
6. Refresh the **Addon Coverage Matrix** (all six documents) in `00_INDEX.md`.
7. Self-audit against **all six** quality gates (kickoff, 1-O, 2-I, 3-J, 4-K, M); fix every gap; run the link-check.
8. Run the **two tabletop walkthroughs** (analyst month-end through pack issuance; cold-start client via docs 22/29) using only the docs; fix every uncovered step.
9. Write `docs/PHASE0_SUMMARY.md` + session report per doc 30 (B.2).
10. **STOP. Present to me — PHASE0_SUMMARY + doc 29 + doc 30 — and wait for recorded approval (Addon 4 E.2). No product code before approval.**
11. After approval: **packaging spike first** (hello-world through `scripts/build` → PyInstaller → Inno Setup → installed launch on real Windows 11 exercising the SmartScreen path; evidence per Section C), then roadmap Phase 1 per doc 16 — beginning with the headless engine skeleton + CLI + `scripts/check`. Golden Month blesses at first full build (Section F); oracle worksheet ships with the first gate.
