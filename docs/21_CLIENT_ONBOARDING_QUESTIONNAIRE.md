> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **client-facing questionnaire** — every question the client must answer
> (`Q-001`…`Q-021`, five groups), why it matters, the **labelled default already implemented** if it goes
> unanswered, where that default lives, when the answer is needed, how an answer is recorded and propagated
> (`DEC-`/`OQ-`), and the delivery/IT confirmations registered as `A21`…`A28` (Addon 1 §C.1/§D, Addon 2 §H.3,
> Addon 4 §B)
> **TL;DR (≤ 15 lines):**
> - This is the **only** place the client is asked for facts. Q items are asked with **≤ 3 options + a
>   recommendation + the default** (`18` §4.3), one thread at a time, never as a bare open question.
> - **Nothing blocks.** Every one of the 21 items already has a labelled default implemented in an owning
>   doc; that is what makes `GATE-02-01` ("every questionnaire item has a decision or a labelled default")
>   provable without a live interview.
> - **Defaults are labelled "default, unconfirmed"** everywhere they are used and are never presented to the
>   client as settled facts (`01` §12 rule).
> - **An answer changes documents, not code paths:** it becomes a `DEC-nnn` row in `18` §5, closes or
>   rewrites the matching `OQ-nnn`, and lands in every owning doc in the same change (`19` §5.1).
> - Ask in **impact order** (§2.3): the highest-value answers come first; the rest can arrive over weeks
>   without stalling a phase.
> - **We do not re-open what is already ruled** (§4): consolidation, no RBAC, no in-app PDF, AI off by
>   default, sample data never delivered, the never-cut list. Those are decisions, not questions.
> - `Q-001` (one sanitized real month) is the **only item with a hard external dependency**; it gates the
>   real-data pilot (`GATE-13`, `28`), not development.
> - `Q-015` (code-signing certificate) has the longest lead time — ask it first; the unsigned-v1 ladder
>   (`09` `ADR-003`, `15` §8) is the fallback and is already documented.
> - Delivery/IT facts (`A21`–`A28`) are **confirmations**, not interviews: they are checked at install and
>   pilot time (§3.6).
> - §6.2 maps **Addon 1 §D's 20-item domain checklist** to the question, assumption or decision that
>   settles each one — no item is left undecided.
> - **Never guess a client fact.** If a phase needs an answer that touches money semantics, data loss, UX
>   flow or a client fact, it is a blocking question (`18` §4.2) — not an improvisation.

# 21 — Client Onboarding Questionnaire

## 1. Purpose, ownership and rules

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| The **question register** `Q-001`…`Q-021` (wording, grouping, order, status) | **here** |
| The **default in force** for each question, and where that default is implemented | **here** (the assumption's own row lives in `18` §3.1 `A1`…`A20` / §3.2 `A21`…) |
| The **answer log** (answered date, `DEC-` id, docs updated) | **here** §5.2 |
| Assumption register (`A1`…`A29`) and the change-if-answered consequences | `18` §3 |
| Open questions (`OQ-`), blocking protocol and the ask format | `18` §4 |
| Recorded decisions (`DEC-`) | `18` §5 |
| The client-facing, jargon-free version | `29` |
| Risks arising from unanswered items | `25` |

### 1.2 The four rules

1. **Nothing blocks.** Every item has a default that is already implemented in an owning doc. An
   unanswered question changes detail, never the promise (`18` §4.2).
2. **Ask in the `18` §4.3 format:** ≤ 3 options + a recommendation + the default that applies if nobody
   answers. A bare "what do you want?" is not an acceptable question.
3. **Labelled defaults only.** Until answered, every dependent statement is marked *default,
   unconfirmed*; it is never repeated to the client as a fact (`01` §12).
4. **Answers are recorded, dated and propagated** (§5): `DEC-nnn` in `18`, the `OQ-` row closed or
   rewritten, the owning docs updated in the same change, `CHANGELOG` + `SESSION_LOG` updated.

### 1.3 Who asks, who answers

| Role | Responsibility |
|---|---|
| Consultant (product owner side) | Runs the session, asks in §2.3 order, records answers in §5.2, updates the docs |
| Client finance owner (CFO or finance manager) | Answers the finance-model and outputs questions (groups B and D) |
| Client analyst | Answers data/file questions, provides the pilot month, runs the tie-out |
| Client IT contact | Confirms install-day facts (§3.6) and the delivery channel (`Q-016`) |

## 2. How the interview runs

### 2.1 Shape and timing

| Aspect | Rule |
|---|---|
| Session 1 (60–90 min) | Groups A, C and D — access, systems, outputs (`Q-001`…`Q-003`, `Q-012`…`Q-014`, `Q-019`, `Q-021`) |
| Session 2 (30–45 min) | Groups B and E — finance model, delivery, enablement, support (`Q-004`…`Q-011`, `Q-015`…`Q-018`, `Q-020`) |
| Follow-ups | Email-friendly: send the relevant table rows, not the whole document |
| Recording | Every answer goes into §5.2 the same day, with the docs it changes |
| No-answer default | Any item not answered by its "needed by" date stays at its default and is listed as an open question recovery item in `18` §4 |

### 2.2 What we do **not** ask

Nothing in §4. Asking a ruled question re-opens scope; the §4 list is shown to the client instead.

### 2.3 Ask in impact order (highest unblocking value first)

| Order | Item | Unblocks |
|---|---|---|
| 1 | `Q-015` signing certificate | Longest lead time (procurement); SmartScreen plan for install day |
| 2 | `Q-001` one sanitized real month | The pilot/tie-out (`GATE-13`) and real-world shape validation |
| 3 | `Q-002`, `Q-003` system shapes | The mapping profiles and parsing rules actually used in month 1 |
| 4 | `Q-004`, `Q-006` calendar and currency | Period maths and every displayed number |
| 5 | `Q-009`, `Q-010`, `Q-011` thresholds/master data | Which exception rules can be enabled on day one |
| 6 | `Q-012`, `Q-013`, `Q-019` outputs, audience, branding | The pack the client actually recognises |
| 7 | `Q-005`, `Q-007`, `Q-008` comparatives, budget versions, cadence | Analysis depth and forecast defaults |
| 8 | `Q-014`, `Q-016`…`Q-021` volumes, delivery, training, support, retention, headcount | Operational readiness, no code-path risk |

## 3. The questionnaire (21 items)

**Status of every row at the time of writing: `Open · default in force`** — tracked in §5.2.

### 3.1 Group A — Data access and volumes

| Q | Question to the client | Why it matters | Default in force (labelled, implemented) | Owning docs / FRs | Needed by |
|---|---|---|---|---|---|
| `Q-001` | Can you provide **one sanitized real month** — the D365 GL export plus both other system exports — as early as possible? | The pilot and tie-out prove the app against real numbers and real shapes; it is the only item with a hard external dependency | None yet: the synthetic `sample-data/` corpus (watermarked, never delivered) is used for development and demos | `28` (pilot), `14` §16, `18` `A29`/`OQ-014` | Start of Phase 6 / `GATE-13` |
| `Q-014` | What are the **largest file sizes and row counts** you actually see — per file and per month? | Validates `NFR-002`/`NFR-009` (250k rows / ~100 MB) and the import limits, estimates and UX | 250k rows / ~100 MB upper bound with an explicit over-limit confirmation | `04` §3, `14` §3, `FR-IMP-003/030`, `FR-XC-010`, `18` `A13`/`OQ-013` | Phase 1 gate (re-confirmed at the pilot) |
| `Q-021` | Should v1 report **headcount-based metrics** (cost/revenue per head)? If yes, what headcount data exists, and where? | Decides whether a parked KPI set re-opens; headcount is the only metric family with no data today | Not provided: headcount metrics stay parked (`BL-016`) and the KPI library ships without them | `05` §5.2, `FR-BVA-010`, `27` (`BL-016`), `18` `A20` | Before go-live (no code impact while parked) |

### 3.2 Group B — Finance model and calendar

| Q | Question to the client | Why it matters | Default in force (labelled, implemented) | Owning docs / FRs | Needed by |
|---|---|---|---|---|---|
| `Q-004` | What is the **fiscal calendar** — year start, period count and codes, 4-4-5 or calendar months? | Every period assignment, window (MTD/YTD/TTM), comparison and close boundary derives from it | January year-start, 12 calendar months, codes editable; configurable per project | `05` §2 (`CALC-001`/`002`), `03` §3.6, `FR-SET-005`, `FR-PRJ-004/005`, `FR-BVA-002`, `18` `A3`/`OQ-003` | Phase 1 gate |
| `Q-005` | Is **prior-year data** available, and in what form (system, file, level of detail)? | PY views, PY variance and run-rate/TTM eligibility | Build PY views; hide them with a note when no PY batch exists | `02` §16 E1, `05` §12 F8, `FR-BVA-002`, `18` `A5`/`OQ-004` | Phase 2 gate |
| `Q-006` | **Single reporting currency or several?** And which units should the pack show by default (whole, thousands, lakhs)? | Storage, mixed-currency quarantine, unit labels and every displayed total | INR, whole units, optional thousands/lakhs display; no FX table in v1 | `03` §3.7, `05` §6.3, `08` §15, `FR-SET-006/007`, `FR-IMP-011`, `FR-XL-002`, `18` `A4`, `OQ-005`/`OQ-022` | Phase 1 gate |
| `Q-007` | **How many budget versions** exist, and how are revisions approved and reloaded? | Import replace semantics, version comparison, and which budget the forecast anchors to | One approved annual budget per period with a `version` field; a re-import replaces that version atomically | `04` §14, `11` §8, `FR-IMP-027/028`, `FR-BVA-003`, `18` `A6` | Phase 1 gate |
| `Q-008` | What **forecast cadence and scenarios** do you actually use (monthly/quarterly; base/best/worst)? | Forecast defaults, scenario set, accuracy reporting and reforecast discipline | Monthly rolling forecast with Base/Best/Worst scenarios | `07` §3/§6, `FR-FC-002/003/009`, `18` `A7` | Phase 4 gate |
| `Q-009` | What **approval thresholds** apply, and where does that list come from today? | The default thresholds of every amount-based rule and the global materiality floor | Editable master-data table seeded with `max(₹500,000, 2 % × \|budget\|)` | `06` §2.10/§4 (`EXC-021`), `05` §11, `FR-EXC-013`, `FR-SET-003`, `18` `A8`/`OQ-007` | Phase 3 gate |
| `Q-010` | What is the **recurring-cost list** (subscriptions, retainer fees, regular payments), and who maintains it? | The "missing recurring cost" rule cannot run without it; a stale list creates false positives | Editable master-data table the client maintains; the dependent rule auto-disables with a visible notice until it is loaded | `06` §4 (`EXC-015`)/§2.9, `FR-EXC-014`, `FR-SET-003`, `18` `A9`/`OQ-008` | Phase 3 gate (rule stays disabled otherwise) |
| `Q-011` | Is a **vendor master with categories** available? In what file and with which columns? | Vendor-category rules and owner auto-assignment; absent data must degrade, not guess | Optional importable table; dependent rules degrade gracefully with a notice | `03` §3.4/§5.6, `06` §4 (`EXC-014`)/§2.6, `FR-EXC-007/014`, `18` `A10`/`OQ-009` | Phase 3 gate |
| `Q-020` | What are your **retention and deletion expectations** — how long must projects and backups exist, and what must "delete" mean? | Retention defaults, backup policy, deletion guarantees and the support story | Projects are kept locally until the user deletes them; delete requires typed confirmation and offers a pre-delete backup; no cloud copy exists | `13` §10.2, `FR-PRJ-011/012`, `18` `A19` | Before go-live |

### 3.3 Group C — Systems and file shapes

| Q | Question to the client | Why it matters | Default in force (labelled, implemented) | Owning docs / FRs | Needed by |
|---|---|---|---|---|---|
| `Q-002` | Which **D365 edition and export** produces the GL file (Finance & Operations, Business Central, other), and can we see one file's column layout? | Column set, dimension-string format, control totals and the profile that parses them | Generic "D365-style GL export" template with documented dimension parsing; a per-edition profile is added when confirmed | `04` §2/§7/§10, `FR-IMP-002/004/005/011`, `18` `A1`, `OQ-001` | Phase 1 gate |
| `Q-003` | What are the **two other systems**, and what are their exact column lists (including which sheets/rows hold the data)? | Proves mapping flexibility; the two non-D365 shapes are needed for month-1 imports and the sample corpus | Two distinct sample shapes ship (payroll summary; procurement/bank ledger) and both are documented end to end | `04` §2, `14` §16, `FR-IMP-002/005/010/011`, `18` `A2`, `OQ-002` | Phase 1 gate |

### 3.4 Group D — Outputs, audience and branding

| Q | Question to the client | Why it matters | Default in force (labelled, implemented) | Owning docs / FRs | Needed by |
|---|---|---|---|---|---|
| `Q-012` | Can you share **one recent BvA Excel** and the **management PPT** you send today (any format, even PDF/print)? | House style, slide structure and layout replication; also whether `.xlsm`/protected files are in scope | The app's own house style (`11`/`12`) until samples arrive; protected/`.xlsm` inputs are handled or explicitly rejected per `04` §8 | `11` §3/§9, `12` §6, `04` §8, `FR-XL-001/002`, `FR-PPT-001`, `18` `A11`, `OQ-010`/`OQ-021` | Phase 5 gate |
| `Q-013` | **Who reads the pack** (CFO, finance director, management team), and who should receive each issued version? | Drives slide-2 KPI selection, commentary tone and the issuance-register recipient list | CFO/finance director; recipients are typed per issue; the product itself never sends anything | `01` §9, `12` §4.2, `08` §11.2, `FR-XC-003`, `18` `A12`/`OQ-011` | Phase 5 gate |
| `Q-019` | What are the **product name, logo and two brand colours** (plus any rules about their use)? | Deck, Excel header and app branding; the WCAG-AA contrast guard applies to any colour supplied | Working name, neutral placeholder palette, no logo | `01` §17, `08` §19, `12` §3.3, `FR-SET-008`, `FR-PPT-006`, `18` `A18` | Phase 5 gate |

### 3.5 Group E — Delivery, IT, enablement and support

| Q | Question to the client | Why it matters | Default in force (labelled, implemented) | Owning docs / FRs | Needed by |
|---|---|---|---|---|---|
| `Q-015` | Is there **budget and lead time for a code-signing certificate** (EV or OV)? | Determines whether install day shows a SmartScreen warning, and which mitigation path is printed | None: unsigned v1 ships with the documented SmartScreen mitigation ladder and the verbatim user walkthrough | `09` `ADR-003`, `15` §8, `18` `A14`, `OQ-012` | Packaging spike (before Phase 1 completes) |
| `Q-016` | **Which delivery channel** is approved for the installer, and can it carry a ~500 MB file plus a checksum? | How the artefact and its published SHA-256 reach the client, and whether chunking is needed | Secure link + published SHA-256; any approved channel must carry the file and the checksum | `15` §1.2/§8, `18` `A15`/`A23`, `OQ-017` | Phase 6 (before go-live) |
| `Q-017` | What **training** does the team want (live session, recorded walkthrough, written guide, or all three)? | Training outline, UAT script and user-guide depth | 60-minute guided session + recorded demo outline inside `22` | `22`, `23`, `14` `TST-UAT-04`, `18` `A16` | Before UAT |
| `Q-018` | **Who does the client call first**, and what support/warranty terms apply after go-live? | Support flow, escalation path and the diagnostics-zip workflow | The analyst calls the consultant first; the diagnostics workflow is documented in `23`; terms are tracked in `OQ-016` | `15` §9, `13` §7, `FR-XC-014`, `18` `A17`/`OQ-016` | Before go-live |

### 3.6 Delivery and IT confirmations (`A21`–`A28`)

These are **confirmations of environment facts**, not interview questions: they are checked at install and
pilot time, and each already has a documented fallback. They carry no `Q-` ids because they are not client
decisions; the authoritative rows are `18` §3.2.

| Ref | Confirmation | Default in force | Where it is handled | Checked when |
|---|---|---|---|---|
| `A21` | Client machines run Windows 11 x64, have WebView2, and staff use standard (non-admin) accounts | Assumed true; the WebView2 fallback and the portable package are documented | `15` §4.1/§13, `09` §3.2 (`ADR-001`) / `ADR-005` spike list, `14` `TST-WIN-11` | Install day (`TST-WIN-01`, `TST-WIN-11`) |
| `A22` | A reference-class machine is available for the performance runs (4-core / 16 GB / SSD / Win 11) | Measured per the `14` §3 protocol; if the client machine differs, baselines are re-recorded and comparisons annotated | `14` §3 | Real-data pilot |
| `A23` | The agreed channel can carry a ~500 MB installer and a checksum | As stated; chunking is the fallback (`15` §13) | `15` §1.2/§13 | Before go-live |
| `A24` | Client IT is reachable for the one-time install if SmartScreen requires a prompt | The written walkthrough stands alone; the install proceeds together remotely | `15` §8.3/§13 | Install day |
| `A25` | Team shape behind the estimates (one senior engineer with AI assistance; ideal days) | As stated; re-estimated at every gate (`> 50 %` variance reported immediately) | `16` §7.1/§13 | Every gate (internal) |
| `A26` | The client analyst is available for the pilot and UAT as planned | As planned; a slip is reported, not absorbed silently | `16` §13, `28`, `14` §12.4 | Pilot/UAT scheduling |
| `A27` | Excel and PowerPoint are available on the client machine to open the artefacts | Assumed present; artefacts are always native/editable and never depend on in-app rendering | `14` §9.4 (`TST-WIN-10`), `15` §5.2, `12` §3.2 | Install day |
| `A28` | No security/privacy/compliance regime beyond `13` emerges during the engagement | As stated; any change is a blocking question immediately | `16` §13, `13` §1, `18` §4.2, `25` | Continuous |

## 4. Already ruled — do **not** ask the client to re-open these

Each is a recorded decision with an owning doc. Showing this list is how the session stays inside scope.

| Ruling | Owner | Why it is not a question |
|---|---|---|
| No eliminations or intercompany netting in v1; per-entity reporting plus simple grouped totals labelled "Simple sum — no eliminations" | `01` §8, `FR-BVA-014` | A consolidation engine is a different product; grouped totals are enough for the stated job |
| Single-user, no login, no RBAC | `01` §6.3/§10 | The app is a local single-user tool; a permission model would add cost with no benefit here |
| The app does not render PDF; it provides tested print readiness and "Open for printing / Save as PDF" | `DEC-028`, `11` §10.3 | Bundling a renderer or driving Excel was rejected on size/reliability grounds |
| AI is optional, off by default, and never computes, decides, applies or sends | `10` §2, `01` §15 | A policy decision, not a client preference |
| Sample data is never delivered to the client and never mixes with client data | `14` §16, `FR-XC-013` | Delivery hygiene; watermarks and the project-type flag enforce it |
| The canonical advisory disclaimer appears as specified (pack, Excel, deck, screens) | `01` §15.1 | Legal/advisory stance; wording is not negotiable per surface |
| The nine never-cut items (exact Decimal money, atomic imports, versioned audit, offline/local-only, installer + real-Windows validation, disclaimer, backup/restore, golden tests, cross-artifact test) | `02` §3.3, `16` §9.2 | These are the product's promises; a cut request goes through the cut process, not the questionnaire |
| Import-only budgets (no in-app budget editing) | `01` §6.3 | Keeps the app a single source of truth for budget data |

## 5. Recording, propagating and tracking answers

### 5.1 The six-step answer flow (mandatory)

1. **Capture the answer verbatim** in the session notes (the client's words), with date and who said it.
2. **Convert it to a decision row:** append `DEC-nnn` to `18` §5 (decision, date, rationale, source).
3. **Close or rewrite the open question:** the matching `OQ-nnn` in `18` §4 moves to its resolved state, or
   is rewritten to the narrower question that remains.
4. **Update every owning doc** listed in the question's row (default flag removed where it applied).
5. **Update this document:** the answer log row (§5.2) records date, `DEC-` id and the docs updated.
6. **Record the change:** `CHANGELOG` entry + `SESSION_LOG` row (`19` §5.1 change order — docs first).

**No answer may exist only in this document.** If step 4 did not happen, the answer is not integrated.

### 5.2 Answer log (status of record)

| Q | Status | Answered on | `DEC-` | Docs updated |
|---|---|---|---|---|
| `Q-001` | Open · default in force | — | — | — |
| `Q-002` | Open · default in force | — | — | — |
| `Q-003` | Open · default in force | — | — | — |
| `Q-004` | Open · default in force | — | — | — |
| `Q-005` | Open · default in force | — | — | — |
| `Q-006` | Open · default in force | — | — | — |
| `Q-007` | Open · default in force | — | — | — |
| `Q-008` | Open · default in force | — | — | — |
| `Q-009` | Open · default in force | — | — | — |
| `Q-010` | Open · default in force | — | — | — |
| `Q-011` | Open · default in force | — | — | — |
| `Q-012` | Open · default in force | — | — | — |
| `Q-013` | Open · default in force | — | — | — |
| `Q-014` | Open · default in force | — | — | — |
| `Q-015` | Open · default in force | — | — | — |
| `Q-016` | Open · default in force | — | — | — |
| `Q-017` | Open · default in force | — | — | — |
| `Q-018` | Open · default in force | — | — | — |
| `Q-019` | Open · default in force | — | — | — |
| `Q-020` | Open · default in force | — | — | — |
| `Q-021` | Open · default in force | — | — | — |

Status vocabulary: **`Open · default in force`** (the only state today) · **`Answered`** (a `DEC-` row exists and
the owning docs are updated) · **`Withdrawn`** (the client confirms the default is correct — still a `DEC-` row).

## 6. Why nothing is blocked

### 6.1 The proof

1. **Every item has a default** (§3.1–§3.5, "Default in force" column) and each default is implemented in an
   owning document — verifiable by opening the cited section.
2. **Every item has an owner and a needed-by date** (the same rows), so a missing answer is a scheduling
   fact, not an ambiguity.
3. **Every dependent statement is labelled** *default, unconfirmed* until answered (`01` §12 rule).
4. **A missing answer cannot silently change behaviour:** if a phase needs an answer on money semantics,
   data loss, UX flow or a client fact, the blocking protocol fires (`18` §4.2) and the thread stops.

This is what makes `GATE-02-01` ("every questionnaire item has a decision or a labelled default")
provable from the documents alone.

### 6.2 Addon 1 §D — the 20-item domain checklist, mapped

| # | §D item | Settled by |
|---|---|---|
| 1 | Fiscal calendar | `Q-004` → `18` `A3`; configurable in Settings (`FR-SET-005`) |
| 2 | D365 edition | `Q-002` → `18` `A1` (`OQ-001`) |
| 3 | The two other systems | `Q-003` → `18` `A2` (`OQ-002`) |
| 4 | Consolidation stance | **Ruled** — no eliminations in v1 (`01` §8, §4 here) |
| 5 | Prior-year comparatives | `Q-005` → `18` `A5` (`OQ-004`) |
| 6 | Reporting currency & units | `Q-006` → `18` `A4` (`OQ-005`, `OQ-022`) |
| 7 | Budget versions | `Q-007` → `18` `A6` (`OQ-006`) |
| 8 | Forecast cadence | `Q-008` → `18` `A7` |
| 9 | Approval-threshold source | `Q-009` → `18` `A8` (`OQ-007`) |
| 10 | Recurring-cost list source | `Q-010` → `18` `A9` (`OQ-008`) |
| 11 | Vendor master / categories | `Q-011` → `18` `A10` (`OQ-009`) |
| 12 | Current outputs to replicate | `Q-012` → `18` `A11` (`OQ-010`, `OQ-021`) |
| 13 | Who reads the pack | `Q-013` → `18` `A12` (`OQ-011`) |
| 14 | File sizes / row volumes | `Q-014` → `18` `A13` (`OQ-013`) |
| 15 | Signing certificate | `Q-015` → `18` `A14` (`OQ-012`) |
| 16 | Delivery channel | `Q-016` → `18` `A15`/`A23` (`OQ-017`) |
| 17 | Training | `Q-017` → `18` `A16` |
| 18 | Support model | `Q-018` → `18` `A17` (`OQ-016`) |
| 19 | Branding | `Q-019` → `18` `A18` (`OQ-015`) |
| 20 | Data retention | `Q-020` → `18` `A19` |

Two further items sit outside §D's list but are asked anyway: **`Q-001`** (the sanitized pilot month →
`18` `A29`/`OQ-014`) and **`Q-021`** (headcount metrics → `18` `A20`/`BL-016`).

## 7. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `18` | Every answered question lands as a `DEC-` row and closes/rewrites its `OQ-`; the assumption rows are updated, never duplicated here |
| Owning docs | Remove the "default, unconfirmed" label where an answer lands; the default text stays only as history in `18` §5 |
| `25` | Register a risk for every high-impact unanswered item whose needed-by date is approaching (`OQ-012`, `OQ-014`, `OQ-016`) |
| `29` | Present these questions to the client in plain language, without FR/`Q-` jargon, with the same defaults |
| `23` | Own the support-flow detail behind `Q-018`, and the support-side key rotation/revocation steps (`FR-AI-003`; mechanics in `10` §14, `13` §5.3) |
| `22` | Own the training material behind `Q-017` (`TST-UAT-04` uses only `22`) |
| `16` | At each phase gate, check that the items marked "needed by" that phase are answered or explicitly default-accepted |
| `28` | Schedule the pilot/UAT around `Q-001` and `A26` (analyst availability), not the other way round |

## 8. Change control for this document

1. A **new question** requires: a `Q-nnn` id (append-only, never reused), a default implemented in an owning
   doc, an owner, a needed-by date, and a `CHANGELOG` entry. A question without a default is not asked.
2. A **question is never deleted**: it is marked `Withdrawn` with the `DEC-` that settled it.
3. Answers propagate per §5.1 — the questionnaire is never the only place an answer lives.
4. The status column in §5.2 changes only together with the `DEC-` row and the owning-doc update.
5. Client-facing wording changes are `CHANGELOG`-recorded; the defaults they reference stay owned by `18`/the
   owning doc.

## 9. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| Question register | `Q-001`…`Q-021` (21 items), owned here, append-only | `01` §12, `18` §4; registry `00_INDEX` §8 |
| Groups | A data access · B finance model · C systems · D outputs/branding · E delivery/support | §3 |
| Ask format | ≤ 3 options + recommendation + default | `18` §4.3 |
| Status vocabulary | `Open · default in force` · `Answered` · `Withdrawn` | §5.2 |
| Answer flow | Six steps, docs before code | §5.1, `19` §5.1 |
| §D checklist coverage | 20 of 20 mapped (plus `Q-001`, `Q-021`) | §6.2 |
| Delivery confirmations | `A21`–`A28`, no `Q-` ids | §3.6, `18` §3.2 |
| Never-ask list | 8 rulings | §4 |
| Blocking rule | Money semantics / data loss / UX flow / client fact → stop the thread | `18` §4.2 |

