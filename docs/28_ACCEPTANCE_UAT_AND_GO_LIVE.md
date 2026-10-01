> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning areas:** the **acceptance path**: the project-level Definition of Done, the defect severity and
> workflow (`S1`–`S4`), the **real-data pilot (`GATE-13`)**, **UAT (`GATE-14`)**, the **go-live checklist
> (`GATE-15`)**, the client sign-off template and the per-phase demo-script standard (Addon 3 §B.1/§G,
> Addon 4 §F; the test-level detail stays in `14`, the release mechanics in `24`)
> **TL;DR (≤ 15 lines):**
> - **Done means demonstrated, not discussed.** The project DoD is the five quality gates plus coverage,
>   a clean-Windows E2E golden path, and the live Coverage Matrix — no partial credit (§2).
> - **The pilot is the credibility gate (`GATE-13`)**: one sanitized real month, end-to-end, **no sample
>   data allowed**, with every difference classified and signed off (§4).
> - **UAT is the analyst's own month, on the installed build**: one FP&A analyst plus at least one
>   accounting-owner representative, ≤ 5 business days, with a fallback week (§5).
> - **Six human scripts** (`TST-UAT-01`…`06`, `14` §12.4) carry the acceptance — including the cold-start
>   client pass with no author present and the go-live rehearsal.
> - **Defects are `S1`–`S4`** with `14` §14.1's meanings and `23` §10's response targets as labelled
>   defaults until `OQ-016` is answered (`OQ-016`); `S1` blocks any release.
> - **Every difference is classified**, never "explained away": spec bug / mapping error / client-data or
>   methodology difference / genuine client error (§4.3).
> - **The tie-out worksheet is a template, not a vibe**: totals, key accounts and the exception list
>   compared line by line, with the classification log and the analyst's signature (§4.4/§7).
> - **Go-live is a checklist of 22 items** (`GATE-15`) covering delivery, install, training, backup,
>   diagnostics, rollback and the sample-data assertion (§6).
> - **Rollback is restore-only** — the app never reverses a migration (`24` §6.4); the statement is part
>   of go-live, not a surprise.
> - **The client signs what they verified**: pilot, UAT and go-live each have a sign-off block naming the
>   evidence and the person (§7).
> - **Post-go-live has a home**: hypercare, the first accuracy report and the feedback intake that turns a
>   request into a `27` entry before any code (§8).
> - **Every phase gate brings a 3–5 minute demo script** on sample data with expected results (`16` §5.1
>   item 11); §9 fixes the template.
> - **The support/warranty terms are placeholders until the user sets them** (`OQ-016`, Addon 3 §E.4);
>   response targets are defaults, not promises.
> - **The real month is a schedule dependency, not a design one** (`OQ-014`): it has no default, it gates
>   `GATE-13`, and its only mitigation is `RISK-002`.
> - **No product code exists yet**; this document is the acceptance path Phase 1 onward must satisfy.

# 28 — Acceptance, UAT and Go-Live

## 1. Purpose, ownership and readers

| Owns | Does not own |
|---|---|
| The project-level Definition of Done (§2) | Per-FR acceptance criteria (`02`) |
| Defect severity meanings in workflow terms, the defect log and closure rules (§3) | The test-side response and severities (`14` §14.1) |
| The pilot (`GATE-13`), UAT (`GATE-14`) and go-live (`GATE-15`) mechanics (§4–§6) | The gate checklist itself (`16` §2.1/§5.1) |
| The acceptance evidence set and the sign-off template (§7) | The release record and rollback mechanics (`24`) |
| Post-go-live review and the feedback intake into `27` (§8) | Support model and incident playbook (`23` §10/§11) |
| The per-phase demo-script standard (§9) | Each phase's actual script (`16` §5.1 item 11) |

| Reader | Uses |
|---|---|
| Project owner | §2, §4–§7 (what to promise and what to sign) |
| Engineering | §3 (what blocks a release), §4.3 (difference classification) |
| Consultant / support | §5–§8 (running UAT, hypercare, intake) |
| Client finance owner | §4–§7 (what they will be asked to verify and sign) |

## 2. The project-level Definition of Done (Addon 3 §G.1)

### 2.1 The project is done when all of these are true

| # | Criterion | Evidence |
|---|---|---|
| 1 | All five quality gates green: kickoff, Addon 1 §O, Addon 2 §I, Addon 3 §J, Addon 4 §K | `14` §15 with every check ✅ |
| 2 | Coverage bars met: `app/engine` ≥ 90 %, `app` ≥ 75 % | `coverage.xml` (`14` §13.2) |
| 3 | E2E golden path green on a **clean Windows 11 install** of the built artefact | Playwright report + clean-machine run sheet (`15` §5.2) |
| 4 | Docs `00`–`29` complete, with the Addon Coverage Matrix live and every row integrated | `00_INDEX` §3/§4 |
| 5 | The never-cut list intact (Decimal money, atomic imports, versioned audit, offline/local-only, installer + real-Windows validation, disclaimer, backup/restore, golden tests, cross-artefact equality) | `02` §3.3 + the gate packet |
| 6 | The real-data pilot passed with a signed tie-out (`GATE-13`) | §4.4 evidence |
| 7 | UAT closed with no open `S1`/`S2` and all `S3` decisions recorded (`GATE-14`) | §5.5 exit record |
| 8 | Go-live checklist complete and signed (`GATE-15`) | §6, §7 |
| 9 | The release record for the delivered version is complete (`24` §5) | `packaging/out/<version>/` |
| 10 | The handover pack delivered (`23` §12) and the training completed (`22` §10) | Sign-off §7 |

### 2.2 Per-feature DoD additions (Addon 3 §I.5)

A feature is not "nearly done". It closes only with: its FR and demo recipe (Addon 2 §F.5), its `SCR-ID`,
its error messages present in the catalogue (`26` §5), its tests (including empty/loading/error/first-run
states), and its traceability row filled in `20`.

## 3. Defect severity, intake and workflow

### 3.1 Severities (meanings from `14` §14.1; `S4` goes to `27`)

| Severity | Meaning | Release effect | Response target (default, `23` §10) | Resolution target |
|---|---|---|---|---|
| **S1** | Wrong numbers, crash, data loss, cross-artefact mismatch, secret exposure | **Blocks any release**; fix immediately, regression test first | Same business day | Workaround or fix plan within 2 business days |
| **S2** | A documented feature is broken; a workaround exists | Fix before release | 1 business day | 5 business days |
| **S3** | Cosmetic or wording | Fix or defer with a recorded rationale | 3 business days | Next scheduled release |
| **S4** | Enhancement or request | Not a defect: registered in `27` with a trigger | 5 business days (acknowledgement) | Backlog (`27`) |

> These targets are the labelled defaults from `23` §10. `OQ-016` (support/warranty terms) must confirm or
> replace them before go-live; the confirmed numbers are recorded in `23` §11 and here in the same change.

### 3.2 Intake and the defect log

| Field | Rule |
|---|---|
| Intake paths | UAT session notes, the support log (`23` §11), the pilot tie-out, any internal test |
| Minimum report | What they did, what they saw, the screen (`SCR-`), the code if shown (`ERR-*`), and the artefact (screenshot or diagnostics zip, `13` §7) |
| Log fields | `id` (`DEF-nnn`, allocated here, never reused — `00_INDEX` §8), date, reporter, severity, screen/FR, symptom, expected, evidence, owner, status, fix version, regression test id |
| Triage | Agree the severity within the response target; disagreement escalates one level (`15` §9.3 ladder) |
| Fix rule | `S1`/`S2` require a regression test that fails before the fix (`14` §14.1); the test id goes in the log |
| Closure | Closes when the fix is verified on a real Windows build **and** the reporter confirms; `S1` closures are also reviewed at the next gate (`23` §11) |
| Deferral | `S3` may be deferred with a recorded rationale; `S4` becomes a `27` entry in the same change |
| Themes | A defect theme appearing three times becomes a spec change or a `27` entry, never a standing workaround (`23` §11) |

## 4. The real-data pilot (`GATE-13`, Addon 4 §F)

### 4.1 Preconditions

| # | Precondition | Owner |
|---|---|---|
| 1 | One **sanitized real month** covering D365 + both other systems (`Q-001`/`OQ-014`; `A29`) | Client finance owner |
| 2 | The build under test is the release candidate from `24` §4's checklist (not a dev build) | Engineering |
| 3 | The client's current manual pack for the same month is available for comparison | Client finance owner |
| 4 | Mapping profiles for the real shapes are created and versioned (`FR-IMP-026`) | Consultant + client analyst |
| 5 | The pilot runs in a **real project**, never the sample project (`14` §16; sample data is banned in this gate) | Both |
| 6 | Time is booked with the analyst for the tie-out session | Project owner |

> `OQ-014` has **no labelled default** — the only mitigations are scheduling discipline and `RISK-002`'s
> contingency (run UAT on sample data with a written limitation note, then treat the tie-out as the first
> post-go-live activity).

### 4.2 The run

1. Import each sanitized file through the normal wizard (pre-scan → mapping → validate → commit), recording
   the validation report and data-quality score for each.
2. Close the period only if the imports are accepted; otherwise fix the mapping/profile first.
3. Run the rule set and the forecast; generate the Excel pack and the deck.
4. Present the pack to the analyst and walk the BvA → drill-through → exception register path.

### 4.3 Tie-out and difference classification

Every difference between the app's output and the client's manual pack is classified — never averaged away:

| Class | Meaning | Owner of the fix | Recorded as |
|---|---|---|---|
| **(a) Spec bug** | The app is wrong against its own specification | Engineering | `S1`/`S2` defect per §3 |
| **(b) Mapping error** | The app is right, the mapping/profile is wrong | Consultant + analyst | Mapping-profile version + note |
| **(c) Client-data or methodology difference** | Timing, allocation, sign convention, roundings or a genuine error in the manual pack | Client finance owner (decision) | Classification log with the evidence (drill-through rows) |
| **(d) Expected difference** | A documented v1 behaviour (e.g. `n/a` for ÷0, display rounding) | — | Classification log citing the spec section |

### 4.4 Tie-out worksheet (template — the completed copy is appended to this document)

| Field | Example |
|---|---|
| Client / project | `Northwind Industries — FY26` |
| Period covered | `2026-P09` |
| Build under test | `v0.1.0 — SHA-256 <hash>` |
| Files imported | three rows: file, source type, batch id, rows, score |
| BvA totals | app vs manual, per window (MTD/YTD), variance explained |
| Key account balances | account list with deltas and class (a–d) |
| Exception list comparison | app raises vs manually known issues; precision notes |
| Difference log | one row per difference: `class`, amount, cause, owner, action, status |
| Sign-off | analyst + project owner, date (see §7) |

### 4.5 Exit criteria (`GATE-13`)

1. Every difference classified and signed off by the analyst.
2. Mapping profiles **frozen** for the client (further changes are versioned, `FR-IMP-026`).
3. No open `S1`; `S2` has an agreed fix date before UAT.
4. New gaps routed as an impact note (`19` §5.1) — never patched into code directly.
5. The signed tie-out worksheet, classification log and validation reports attached to this document.

## 5. UAT (`GATE-14`, Addon 3 §G.2)

### 5.1 Environment, participants and timing

| Aspect | Rule |
|---|---|
| Build | The installed release candidate on a client-representative Windows 11 machine (`15` §5.2 protocol already run) |
| Data | The sample project **plus** the sanitized real month from the pilot (a real project) |
| Participants | One FP&A analyst (primary) **and** at least one accounting-owner representative (`A26`) |
| Duration | ≤ 5 business days, in one window |
| Fallback | A named fallback week in the same month (`16` §12 row 10); the scripts are runnable by one person |
| Facilitation | The consultant observes and records; they do **not** drive the keyboard during the analyst's scripts |
| Capture | Session notes with timestamps, screenshots, defect ids; recordings only with consent |

### 5.2 The six scripts and their pass criteria (`14` §12.4)

| Script | Pass criterion |
|---|---|
| `TST-UAT-01` Analyst reproduces one month's manual BvA | Their own numbers match the app's, or every difference is classified per §4.3 |
| `TST-UAT-02` Tie-out worksheet | Totals, key balances and the exception list signed off with the classification log |
| `TST-UAT-03` Accounting-owner review of exception wording and verdicts | No "this would mislead us" finding stands unresolved (any is `S2` or worse) |
| `TST-UAT-04` First-time user completes month-end from `22` alone | The guide is sufficient with no author present; every gap becomes a doc fix |
| `TST-UAT-05` Cold-start client pass (fresh machine, only `22`/`29`) | Install → first project → sample → real import without verbal help |
| `TST-UAT-06` Go-live rehearsal | §6's checklist executed end-to-end with the client's IT contact |

### 5.3 Exit criteria (`GATE-14`)

1. All P0 FRs of the delivered scope verified by the analyst (traceability + the session record).
2. No open `S1`; `S2` closed or with a written date before go-live; `S3` decisions recorded.
3. The guide (`22`) and client pack (`29`) corrected where UAT exposed gaps.
4. Training completed (`22` §10) and attendance recorded.
5. UAT sign-off (§7) with the evidence list.

## 6. Go-live checklist (`GATE-15`, Addon 3 §G.5)

| # | Item | Owner | Evidence |
|---|---|---|---|
| 1 | Release record complete for the delivered version (`24` §5) | Engineering | The 12-file record |
| 2 | Installer + SHA-256 delivered through the agreed channel (`Q-016`, `24` §7) | Project owner | Delivery message + hash |
| 3 | Install executed on the client machine; SmartScreen/Defender path handled per `15` §8.3 | Client IT + consultant | Signed checklist |
| 4 | Smoke test on the installed build (open → sample → real project → light import) | Consultant | Run sheet |
| 5 | Real project created at the agreed path (not synced, `ADR-004`) with the pilot's mapping profiles imported | Consultant | Project created + profile versions |
| 6 | Backup executed and **restore verified** on the client machine (`13` §9.2) | Consultant | Restore log |
| 7 | Diagnostics flow tested (zip generated, redaction spot-checked, `13` §7) | Consultant | Sample zip reference |
| 8 | Training session delivered (`22` §10) and the recorded demo handed over | Consultant | Attendance + file |
| 9 | User guide + client requirements pack delivered (`22`, `29`) | Project owner | Delivery message |
| 10 | Support contact, first-line flow and response targets confirmed with the client (`23` §11, `OQ-016`) | Project owner | Written confirmation |
| 11 | Rollback plan stated: **restore-only** (`24` §6.4) with the backup location and steps | Engineering | Rollback note |
| 12 | Update policy stated (manual check only in v1, `BL-007`) | Consultant | Note |
| 13 | Disclaimer present in About, EULA and the pack cover/footer (`01` §15.1) | Engineering | Screenshots |
| 14 | **Sample-data assertion:** no sample-data file appears in any client deliverable (`14` §16) | Project owner | Checklist signature |
| 15 | Retention/permissions briefing (local data, user-deleted projects, BitLocker recommendation, `13` §10) | Consultant | Note |
| 16 | Period status confirmed (the real month's period closed correctly and locked) | Client analyst | App screenshot |
| 17 | Exception ownership and severity defaults confirmed (owner auto-assign vs manual, `06` §2.6) | Client analyst | Settings record |
| 18 | Master data loaded (vendor categories, recurring costs, thresholds) or explicitly deferred with a notice | Client finance owner | Settings record |
| 19 | AI decision recorded: off (default) or configured with the key and endpoint | Client finance owner | Settings record |
| 20 | First-month plan agreed: who imports, when, and who runs the pack | Both | Written plan |
| 21 | Hypercare window agreed (§8) and the escalation path (`15` §9.3) shared | Project owner | Written note |
| 22 | Go-live sign-off (§7) recorded in `CHANGELOG` + `SESSION_LOG` (`19` §5.2) | Project owner | Signed record |

## 7. Acceptance evidence and sign-off

### 7.1 What is signed

| Stage | Signer | Certifies | Does not certify |
|---|---|---|---|
| Pilot (`GATE-13`) | Client analyst + project owner | The tie-out worksheet and classification log represent the month tested | That every future month will tie out automatically |
| UAT (`GATE-14`) | Client analyst + accounting owner + project owner | The scripts ran, the listed defects are the complete known set, the guide is usable | That no further defect will be found |
| Go-live (`GATE-15`) | Client finance owner + project owner | The §6 checklist is complete and the delivered artefacts are as described | Any financial statement or filing (the advisory disclaimer, `01` §15.1) |

### 7.2 Sign-off template (copy into the handover pack, `23` §12)

```
ACCEPTANCE — <stage: pilot | UAT | go-live>
Client: <name>            Project: <name>          Build: v<version> (SHA-256 <hash>)
Period tested: <YYYY-Pnn>  Date(s): <dates>         Evidence list: <files/ids>
Statement: We have reviewed the evidence listed above and confirm the results for the scope
tested. This acceptance covers the artefacts and the period named here; it is not a financial
opinion and does not certify future periods (advisory disclaimer, 01 §15.1).
Open items at this stage: <ids or "none">           Owner + date: <...>
Signed: <client, role> ____________________  Date: ________
Signed: <project owner> ____________________  Date: ________
```

### 7.3 Where the evidence lives

The signed records and their attachments are part of the **handover pack** (`23` §12); the delivery
reference (record name + SHA-256) is recorded in the release record's evidence list (`24` §5), and the
`CHANGELOG`/`SESSION_LOG` carry the approval line (`19` §5.2).

## 8. After go-live

| Aspect | Rule |
|---|---|
| Hypercare | The first **two month-ends** are supported at `S1`/`S2` response targets with a named contact (`23` §11) |
| First accuracy report | After the first closed period under the tool: forecast-vs-actual accuracy reviewed with the analyst (`07` §8) and any method change agreed |
| First month-end review | 30-minute review: what took time, which exceptions repeated, which settings to tune (`06` §10) |
| Feedback intake | Every request is logged as a `27` entry or a decision (`19` §5.4) **before** any code; `S4` items ride the same path |
| Support capacity | The support log (`23` §11) is reviewed monthly; recurring themes become spec changes, never workarounds |
| Re-entry | A later phase or a new scope starts again at `16` §5.1 with a fresh gate packet |

## 9. Per-phase demo scripts (standard)

| Rule | Detail |
|---|---|
| Length | 3–5 minutes, runnable on sample data with no preparation |
| Shape | Numbered steps; each step states the screen, the action and the **expected result** (a number, a state, a file) |
| Evidence | The script and its outcome are recorded in `SESSION_LOG` and attached to the gate packet (`16` §5.1 item 11) |
| Content | Only FRs whose phase is claimed done; at least one error/empty state and one drill-through |
| Rule of thumb | If a step needs explaining to the client, either the feature or the guide is not done |

## 10. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `14` | Owns the severities, test response and the six UAT scripts; a change here is mirrored there |
| `16` | Owns the gate checklists; `GATE-13`…`GATE-15` mechanics come from §4–§6 |
| `23` | Owns the support model, response targets and the support log (§10/§11) that §3 and §8 reference |
| `24` | Owns the release record, distribution and rollback that §6 asserts |
| `22` / `29` | Own the guides the client passes (`TST-UAT-04`/`05`) use |
| `27` | Receives every `S4` and every deferral created here, with a trigger |
| `18` | Records the decisions taken at pilot/UAT/go-live, including confirmed response targets (`OQ-016`) |
| `19` | Owns the impact-note protocol used for gaps found in the pilot (§4.5) and the approval recording (§7) |
| `25` | Carries the risks that these gates measure (`RISK-002`, `RISK-005`, `RISK-012`, `RISK-034`) |

## 11. Change control and frozen constants

| Constant | Value | Source |
|---|---|---|
| Severities | `S1`–`S4` as defined by `14` §14.1; `S1` blocks release | §3.1 |
| Defect ids | `DEF-nnn`, allocated in the UAT/pilot defect log, never reused | §3.2, `00_INDEX` §8 |
| Response targets | `23` §10 defaults until `OQ-016` confirms them | §3.1 |
| Pilot gate | `GATE-13`: one sanitized real month, no sample data | §4, Addon 4 §F |
| UAT gate | `GATE-14`: installed build, ≤ 5 business days, six scripts | §5 |
| Go-live gate | `GATE-15`: the 22-item checklist | §6 |
| Difference classes | `(a)` spec bug · `(b)` mapping error · `(c)` client-data/methodology · `(d)` expected | §4.3 |
| Sign-off stages | Pilot, UAT, go-live — each with the §7.1 statement | §7 |
| Rollback stance | Restore-only, never a reverse migration | §6 item 11, `24` §6.4 |
| Hypercare | Two month-ends at `S1`/`S2` targets | §8 |
| Demo script | 3–5 minutes, steps + expected results, in the gate packet | §9, `16` §5.1 |
