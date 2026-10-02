# Phase 0 tabletop walkthroughs — 2026-10-02

## Scope, method and limitation

This is a **documentation-only** tabletop performed against synthetic scenarios. It checks whether the
specified Phase 0 journey has a named owner, FR/specification, screen or artefact, and future test. It is
not a product demonstration: no product code, installer, client file, Windows machine, pilot or UAT exists
at Phase 0. Those executable checks remain gated after recorded approval.

The reviewer used the Phase 0 document set and the required path in `docs/16_ROADMAP_PHASES.md` §11.2.
No real client data, rows, screenshots or identifiers were used.

## Walk 1 — analyst month-end through pack issuance and re-issue

**Scenario:** an analyst works in a synthetic sample project for FY26-P09 and encounters both a normal
flow and one documented validation/recovery route. The pass condition is that every step has a home in the
specification, at least one requirement/control identifier, and a planned test or gate.

| # | Analyst action / expected outcome | Documentation trail inspected | Evidence / future test | Result |
|---:|---|---|---|---|
| 1 | Start in a local sample project; understand that it is not client data and is offline by default. | `22` T-01; `13` §3/§9; `02` `FR-PRJ-*` | `TST-E2E-01`, `TST-SEC-01` | PASS — purpose and boundary are explicit. |
| 2 | Select the D365-style export and begin the guided import. | `22` T-03; `04` §2/§7; `02` `FR-IMP-001`…`005` | `TST-IMP-*` | PASS — source selection and wizard ownership are named. |
| 3 | Confirm or correct the mapping profile before data can commit. | `04` §9–§11; `02` `FR-IMP-006`…`009`; `08` import screens | `TST-IMP-*`, mapping-review tests | PASS — profile/version path and human review are specified. |
| 4 | Exercise an invalid-file route: the app must show named recovery copy, not a traceback. | `04` hardening/validation catalogue; `02` §16; `14` §6.3 | `TST-IMP-33`, malformed corpus | PASS — documented handle/reject path and error-copy ownership found. |
| 5 | Review validation/control totals and either commit atomically or stop safely. | `04` §12–§14; `05` control-total rules; `02` import acceptance | `TST-IMP-*`, `TST-E2E-*` | PASS — atomicity and control-total decision are specified. |
| 6 | Open the BvA summary for MTD/YTD with sign/favourability rules visible. | `22` BvA task; `05` §2–§6; `08` BvA screens | `TST-BVA-*`, F1–F14 | PASS — deterministic number owner and display owner are separate and linked. |
| 7 | Drill from an adverse variance to transaction-level evidence and retain filters/breadcrumbs. | `02` `FR-BVA-*`; `08` drill-down inventory; `26` route contract | `TST-BVA-*`, `TST-API-*` | PASS — screen/API/test trail exists. |
| 8 | Inspect the data-quality score and any coverage/gap explanation. | `05` §8; `06` tie-out rules; `08` quality indicators | `TST-CALC-*`, data-quality worked example | PASS — formula and non-happy state are specified. |
| 9 | Run the exception catalogue, open an item, and see rule/evidence/severity rather than an accounting verdict. | `06` §1–§7; `02` `FR-EXC-*`; `22` exception task | `TST-EXC-*`, planted-exception harness | PASS — review-aid wording and workflow state are named. |
| 10 | Assign/triage an exception and preserve its identity on a re-run. | `06` identity/re-run semantics; `02` exception FRs; `03` model | `TST-EXC-*` | PASS — stable-key/history behavior has a canonical home. |
| 11 | Create or compare a forecast, including a manual-override reason where used. | `07`; `05` §9; `02` `FR-FC-*` | F14a–F14g, `TST-FC-*` | PASS — each specified method has an example and future test family. |
| 12 | Keep AI off by default; if later enabled, receive draft-only commentary with provenance and a human approval boundary. | `10` §2/§8–§12; `13`; `22` AI task | `TST-AI-*`, `TST-SEC-14` | PASS — no AI authority over numbers/data is specified. |
| 13 | Generate the values-only Excel pack with formatting/watermark rules. | `11`; `22` export task; `14` §7 | `TST-XL-*`, cross-artifact suite | PASS — workbook owner and output rules are named. |
| 14 | Generate the editable six-slide PowerPoint deck from the same numbers. | `12`; `22` export task; `14` §7 | `TST-PPT-*`, cross-artifact suite | PASS — slide/placeholder contract and source-of-truth path found. |
| 15 | Compare UI/Excel/PPT output to the deterministic engine and an independent synthetic hand-check. | `14` §5.7/§7; `tests/oracle/` | cross-artifact suite; formula-visible oracle | PASS — independent-oracle and machine-diff paths are specified. |
| 16 | Issue the approved pack, lock its version/recipient record, then make a re-issue rather than overwrite history. | `02` reporting FRs; `03` issuance tables; `11`/`12` issuance rules | `TST-XC-*`, issuance tests | PASS — issuance/re-issue sequence has named owners. |
| 17 | If a problem occurs, use metadata-only diagnostics and the support intake instead of sending data rows. | `13` §7; `23` diagnostics/support route; `22` support task | `TST-SEC-*` | PASS — safe support route and never-send list are documented. |
| 18 | Close the month with a versioned audit trail and local backup/restore expectation. | `13` §9–§10; `24`; `22` project tasks | `TST-E2E-*`, `TST-WIN-*` | PASS — lifecycle/recovery owners are named. |

**Walk 1 result:** PASS as a Phase 0 documentation tabletop. All 18 steps map to a specification owner and
planned evidence path; no uncovered workflow hole was found. This result is deliberately not an assertion
that the screens, installer, exports, AI calls or tests have executed.

## Walk 2 — cold-start client using only docs 22 and 29

**Scenario:** a person who has not read the engineering specifications has only the end-user guide (`22`)
and client requirements pack (`29`). They ask the questions below while preparing for their first use. The
pass condition is that the documents answer the question without a developer explanation; where execution
is required later, the document must say so rather than fabricate a result.

| # | Cold-start question | Where the answer was found using only `22` / `29` | Result |
|---:|---|---|---|
| 1 | What does the product do, and what is it not promising? | `29` product overview, boundaries and advisory disclaimer | PASS — finance-language description and boundaries are available. |
| 2 | What data do we provide, and can we send real data to the project team or an online tool? | `29` client inputs/privacy wording; `22` privacy guidance | **Superseded by correction below.** The original PASS was made before final review identified ambiguous/unsafe copy in `29`. |
| 3 | How will we install it safely when Windows warns us? | `22` install/SmartScreen task; `29` machine/install section | PASS — the expected future installer route and warning guidance are documented. |
| 4 | What happens on the first run? | `22` first-run/sample-project task | PASS — guided start and sample context are documented. |
| 5 | How do we import the month and recover from a bad file? | `22` import task and error guidance | PASS — a plain-language workflow and recovery expectation are available. |
| 6 | How do we know the numbers are trustworthy? | `22` BvA/check tasks; `29` pilot/UAT explanation | PASS — deterministic/tie-out and human-review boundaries are explained without engineering jargon. |
| 7 | What does an exception mean, and who acts on it? | `22` exception task; `29` advisory boundary | PASS — it is clearly a lead for accounting review, not an automatic verdict. |
| 8 | What does AI do with our data and can it change a number? | `22` AI task; `29` AI boundaries | PASS — off-by-default, draft-only and no-number-authority statements are present. |
| 9 | How do we create Excel and PowerPoint outputs and share them? | `22` export tasks; `29` output explanation | PASS — intended outputs and user responsibility are clear. |
| 10 | Where do I learn the next task and the release changes? | `22` task/training sections and What's New route | PASS — help and installer companion route are documented. |
| 11 | Who supports us after go-live, and how do requests become improvements? | `22` support pointer; `29` support/change wording | PASS — client-facing route is clear; formal response targets remain owner approval work before go-live. |
| 12 | What must happen before this is accepted and goes live? | `29` pilot/UAT/go-live timeline and sign-off | PASS — acceptance stages and the client sign-off role are stated. |

**Walk 2 result (as first recorded):** PASS as a cold-start **paper** walkthrough for the other 11 questions.
The original row 2 assessment is superseded by the correction below. This remains not a clean-machine
usability result; the real fresh-machine walkthrough remains a later `TST-UAT-05` / Windows-gate obligation
after a build exists.

## Correction and targeted re-test — development-time data-egress (2026-10-02)

During final owner-presentation review, the reviewer found that the original `29` §7/§8 wording could be
read as requesting sanitized exports, a budget workbook or a recent pack **before build**. That contradicted
Addon 5 §E and `13` §3.1. The original Walk 2 row 2 PASS was therefore not supportable. **No file, row,
amount, vendor name, screenshot or other client data was requested, received, uploaded, committed or used;
this was a documentation-copy defect, not a data-exposure incident.**

The copy was repaired before presentation in `29` (§1 data-sharing boundary, §7, §8–§10), `21` (§1.2 and
`Q-001`/`Q-002`/`Q-003`/`Q-012`), `18` (`A29`/`OQ-014`), `20`, `25`, `04`, `13`, `14`, `16`, `28`, `00`, `01`
and `PHASE0_SUMMARY`. The repaired rule is: development receives only metadata or style-only/blank material;
real client data is made available only in the isolated local pilot/UAT environment after a release candidate
exists, and no real data enters an agent, cloud/web service, repository or support evidence.

| Re-test | Documents opened | Result |
|---|---|---|
| A client asks whether to email/upload a real or sanitized export now | `29` §1 data-sharing boundary; `21` §1.2 and `Q-001` | PASS — explicit “do not email, upload or share” instruction; `Q-001` schedules isolated-local use only. |
| A client needs us to understand file shape before build | `29` §7–§8; `21` `Q-002`/`Q-003`; `13` §3.1 | PASS — only column/schema metadata, counts, sheet names and format facts are requested. |
| A client wants house-style matching | `29` §7–§8; `21` `Q-012` | PASS — only blank/redacted style layouts with no financial rows, names or amounts are requested. |
| The eventual real month and pilot evidence are handled | `28` §4–§5; `13` §3.1; `14` §5.7 | PASS — release-candidate, isolated-local pilot/UAT only; repository evidence is safe metadata/hash references only. |

**Corrected Walk 2 result:** PASS as a paper walkthrough after the targeted re-test. It verifies clarity of
the written egress boundary only; it does not demonstrate a product, delivery channel, client local setup,
pilot, UAT or real-data handling in operation.

## Follow-on decision-table sweep — development-time data-egress (2026-10-02)

A final full-cell review of `29` §7 found two residual recommendation cells after the first correction:
item 4 previously told the client to provide a prior-year GL extract, and item 9 previously told them to
provide recurring-cost/vendor records. Both could still invite a real-data transfer. They were corrected
before presentation to request only metadata now and to keep actual records in the installed local app after
a release candidate exists. **No actual extract, vendor list, payment record or other client data was
requested, received, uploaded, committed or used.**

| Follow-on re-test | Documents opened | Result |
|---|---|---|
| Prior-year decision (item 4) | `29` §7 item 4; `13` §3.1 | PASS — schema, coverage and volume are metadata-only; an actual extract stays local until installed-app use. |
| Recurring-cost/vendor decision (item 9) | `29` §7 item 9; `13` §3.1 | PASS — fields, categories and maintenance owner are metadata-only; actual vendor/payment records stay local. |
| Whole client-facing request surface | `29` §§1/7/8; `21` §1.2/`Q-001`–`Q-012`; `audit/phase0_reaudit.py` auxiliary check | PASS — no remaining pre-build request asks for a real export, workbook, extract, vendor/master record or amount; automated auxiliary safeguard now guards the specific legacy phrases. |

**Final corrected Walk 2 result:** PASS as a paper walkthrough after both targeted re-test passes. It
verifies only written egress clarity and documentation controls; it is not product, delivery-channel,
client-local-setup, pilot, UAT or real-data execution evidence.

## Follow-up disposition

- Walk 1 found no workflow gap. Walk 2's original data-egress row and subsequent two decision-table cells
  were corrected and re-tested before presentation; no product scope, FR or test behaviour changed.
- The execution limitation is retained as a future phase-gate obligation, not hidden as a pass claim.
