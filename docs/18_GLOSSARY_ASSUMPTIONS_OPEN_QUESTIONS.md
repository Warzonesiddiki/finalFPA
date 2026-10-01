> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the glossary of FP&A and product vocabulary; the **canonical assumption register**
> with defaults and owners (Kickoff §5, `01` §12); the **`OQ-` open-question register** with every
> unconfirmed client fact (Kickoff §5 gate item); the **`DEC-` Decided log** with dates, rationale and
> affected docs (Addon 3 §B.2/B.3); the blocking-question protocol (Addon 2 §H.3); and registry hygiene
> (`01` §14's `OQ-018`…`020` flag)
> **TL;DR (≤ 15 lines):**
> - This document is the **canonical register** of what we do not know (`OQ-`), what we assume in the
>   meantime (`A`), and what we have already ruled (`DEC-`) — with dates, rationale and owners.
> - **Nothing here is a fact about the client.** Every assumption is labelled *default, unconfirmed*
>   wherever it is used, and is never presented to the client as settled (`01` §12 rule).
> - **Every open question has a safe default** — that is why none blocks Phase 0; a question becomes
>   **blocking** only when it touches money semantics, data loss, UX flow or client facts (Addon 2 §H.3).
> - A blocking question is asked as **≤ 3 options + a recommendation + the default**, and work stops on
>   that thread until it is answered.
> - **Open questions never disappear:** when answered, they move to the **Decided** log with the date and
>   the rationale — never deleted, never renumbered (`00_INDEX` §8).
> - The `DEC-001`…`DEC-030` log consolidates every ruling made in `01`, `11`, `12` and `13` so far; the
>   index in `01` §21 stays an index, this document is the log of record.
> - The `OQ-020` phantom reference is resolved here (§4.4): `OQ-018`/`OQ-019` were never allocated and
>   `OQ-020` is retired as a tombstone, with the `01` §16 reference corrected to `OQ-016`.
> - The glossary exists so that a doc, a screen and a sentence to the client all use the same word for
>   the same thing — the owning document always wins over the glossary.
> - `21` seeds its questionnaire from §3/§4 and carries the same `Q-` IDs; `29` re-states the decisions
>   the client must confirm; `16`'s gate artefacts include the updated Decided log.
> - Review cadence: **every gate**, plus whenever a client answer arrives, an ADR is written, or a `Q-`
>   item is confirmed (`16` §5.1 item 10).

# 18 — Glossary, Assumptions & Open Questions

## 1. Purpose, ownership and the life of a question

### 1.1 What this document owns

| Fact | Owner |
|---|---|
| The glossary of domain and product terms, and the rule that the owning doc wins | **`18` (this document)** |
| The canonical **assumption register** (what we proceed on until the client says otherwise) | **`18`** |
| The canonical **`OQ-` open-question register** (every unconfirmed item, with owner and default) | **`18`** |
| The canonical **`DEC-` Decided log** (date, rationale, alternatives, affected docs) | **`18`** |
| The blocking-question protocol and the ask format | **`18`**, with Addon 2 §H.3 and `19` |
| Registry hygiene rules (no reuse, tombstones, no dangling references) | **`18`**, with `00_INDEX` §8 |
| The per-document assumption notes (a doc may add local context) | the owning doc |
| The questionnaire items and their wording (`Q-` IDs) | `21` |
| The client-facing statement of decisions | `29` |
| Risk implications of an unanswered question | `25` |
| What happens after a "no" decision (triggers) | `27` |

### 1.2 The life of a question

```
Raised (Q- in 21)  ──►  Open (OQ- here, default in force)  ──►  Answered  ──►  Decided (DEC- here)
                              │                                      │
                              └─ blocking? ──► stop and ask          └─ "no" ──► backlog (27) with a trigger
```

| State | Meaning | Where it lives |
|---|---|---|
| Raised | Someone (usually the client) has to answer something | `21` (`Q-` ID) with the recommended default |
| Open | We are proceeding on a **labelled default**; the question is tracked | `18` §4 (`OQ-` ID) |
| Blocking | The default is unsafe (money, data loss, UX flow, client facts) | `18` §4.3 — work on that thread stops |
| Answered | The client/owner has answered; the default becomes confirmed or changes | the answer is recorded in the `OQ` row and the affected docs |
| Decided | A ruling exists with a date and rationale; docs reference the `DEC-` ID | `18` §5 |
| Retired | A question that no longer applies (e.g. mooted by another decision) | `18` §4.4 as a tombstone — **never deleted** |
| "No" | The answer is "we will not do this in v1" | `27` with a trigger condition |

### 1.3 The rules that make the registers trustworthy

1. **One ID, one question, one decision.** IDs are allocated once, never renumbered, never reused
   (`00_INDEX` §8).
2. **Every open question has a default and an owner.** A question without either is not registered — it
   is an unfinished thought.
3. **Defaults are labelled everywhere they are used** — in code, copy, docs and any client-facing text
   (`01` §12 rule).
4. **Nothing is invented silently.** An implementation choice that changes behaviour is either traceable
   to an FR or becomes an `OQ`/`DEC` — Kickoff §14.5 makes this a protocol violation otherwise.
5. **A question never silently disappears.** Answered → Decided; moot → retired with the reason; not
   doing it → `27` with a trigger (`16` §9.3).
6. **The owning document always wins.** If the glossary, a register row and a spec disagree, the spec's
   text is authoritative and this document is corrected.
7. **No duplicates.** If two registers name the same thing (e.g. an assumption and a question), the row
   links them by ID instead of restating the content.

## 2. Glossary

### 2.1 Money, period and FP&A fundamentals (the client's vocabulary)

| Term | Meaning in this product | Authoritative detail |
|---|---|---|
| **Actual** | The posted, imported result for a period, from the GL export | `03`, `04` |
| **Accrual** | An expected cost not yet invoiced; the exception engine watches for missing ones | `EXC-016` |
| **Budget** | The approved annual plan, imported (never authored in-app), with a version field | `DEC-003`, `04` |
| **BvA (Budget vs Actual)** | The comparison at the heart of the product: actual minus budget, with variance % and favour*ability* | `05` §4 |
| **Bridge / waterfall** | The chart that walks from one figure to another through its drivers | `CHT-*`, `12` §5 |
| **Control total** | A file-level total (e.g. debit sum) used to prove an import landed intact | `04` §12 |
| **Cost centre** | The organisational unit a cost belongs to; a dimension on every row | `03` |
| **Cut-off** | Whether a transaction was posted in the right period; a classic month-end issue | `EXC-010` |
| **Document date** | The date on the underlying document | `05` §2 |
| **Posting date** | The date the system recorded it; period assignment follows this by default | `05` §2 |
| **Driver** | The quantity a forecast or a bridge is built from (e.g. headcount, volume) | `07` §4 |
| **Drill-through / drill-down** | Walking from a number to the transactions that compose it, ≤ 5 minutes end to end | `FR-BVA-004` |
| **Entity** | A legal/accounting unit within the project; v1 reports per entity with simple grouped totals | `DEC-008` |
| **Exception** | A rule-generated flag needing a human decision: owner, severity, SLA, evidence | `06` |
| **Favour*ability*** | Whether a variance is good or bad for the business — expense under budget is favourable | `05` §4.3 |
| **Fiscal calendar** | The period definition; default January start with 12 monthly periods, configurable | `A3`, `05` §2 |
| **GL (General Ledger)** | The accounting ledger; the primary source of actuals | `04` §2 |
| **GL account** | The chart-of-accounts code attributed to a row | `03` |
| **Issuance** | The moment a pack is finalised and recorded in the issuance register | `FR-XC-003` |
| **Lakh / crore** | The Indian grouping convention used in display (1,00,000 / 1,00,00,000) | `08` §15 |
| **Materiality** | The amount **and** percentage test that decides whether a variance is worth flagging | `05` §11 |
| **Month end / close** | The recurring monthly process the product serves: import → check → analyse → exceptions → forecast → pack | `01` §5 |
| **MTD / YTD / PY / TTM** | Month-to-date / year-to-date / prior year / trailing twelve months | `05` §2.3 |
| **n/a vs —** | `n/a` = undefined (÷0); `—` = genuinely zero (0/0); they never collapse | `05` §4 |
| **Pack** | The month-end deliverable set: the Excel pack and the six-slide deck | `11`, `12` |
| **Percentage point (pp)** | The arithmetic difference between two percentages — never called "%" | `CALC-013` |
| **Planting** | A deliberately-placed exception in sample data whose verdict is pre-recorded | `06` §7 |
| **Precision control** | A planted case that must **not** raise — the false-positive guard | `06` §7.2 |
| **Recurring cost** | A cost expected every period; its absence is an exception | `EXC-015` |
| **Run-rate** | A forecast method extrapolating the recent average | `07` §4 |
| **Scenario** | Base / Best / Worst variants of the forecast, versioned separately | `07` §6 |
| **SLA (exception)** | The target response window by severity (7 / 21 / 45 days) | `06` §2.5 |
| **Snapshot (close)** | The locked state of a period's figures at close | `FR-PRJ-*` |
| **Tie-out** | Proving two numbers agree (control total vs GL, workbook vs engine) | `04` §12, `14` §7 |
| **Variance** | `actual − budget` (sign convention is fixed) | `05` §3 |
| **Variance %** | Variance relative to the budget base, with defined divide-by-zero behaviour | `CALC-011` |
| **Vendor** | The supplier a cost is paid to; a dimension and a master-data table | `03`, `04` |
| **Watermark** | The visible "SAMPLE DATA" mark that makes synthetic data unmistakable | `FR-ONB-008`, `14` §16 |
| **Workbook (client's)** | The client's existing monthly Excel output, used only for house-style matching | `11` §9 |

### 2.2 Methods, quality and control vocabulary

| Term | Meaning in this product | Authoritative detail |
|---|---|---|
| **Acceptance harness** | The planted-corpus run that decides whether the rule engine is good enough | `14` §5 |
| **Accuracy (forecast)** | Closed-period comparison of forecast vs actual, per method | `07` §8 |
| **Aging** | How long an exception has been open, bucketed for attention | `06` §2.5 |
| **Atomic (import)** | All-or-nothing: a failed import leaves the previous state untouched | `04` §15 |
| **Batch** | One import run with its own lifecycle: staged → committed → voided | `03` §5.7 |
| **Comparability guard** | The rule that refuses to compare figures that are not comparable | `FR-BVA-013` |
| **Cross-artifact equality** | Engine, UI, Excel, deck and CSV must agree exactly at display precision | `NFR-015`, `14` §7 |
| **Data-quality score** | A weighted score over the import's checks; never shown alone, never hides a failure | `CALC-050`, `04` §16 |
| **Degradation** | A rule that cannot run (missing master data) says so; it never silently passes | `06` §2.9 |
| **Effective threshold** | The threshold actually applied, after overrides, recorded for traceability | `06` §2.10 |
| **False positive** | A raised exception the analyst judges wrong; managed by mitigation and precision controls | `06` §8 |
| **Golden fixture** | A frozen input/output pair with exact expected numbers | `05` §12, `14` §5 |
| **Identity hash** | `SHA-256(rule_id\|subject_key)` — the stable identity of an exception across re-runs | `06` §2.2 |
| **Idempotent** | Running twice changes nothing the second time | `06` §2.2 |
| **Materiality AND-test** | Both the amount and the percentage thresholds must be crossed | `CALC-080` |
| **Quarantine** | Rows held aside with a reason rather than rejected outright | `04` §11 |
| **Recall** | The share of planted exceptions the engine finds (bar: ≥ 90 %) | `14` §5.3 |
| **Reconciliation** | Proving the import agrees with the source's control totals | `04` §12 |
| **Stale (derived data)** | Figures invalidated by a mapping/threshold/master-data change, flagged until re-run | `FR-SET-010` |
| **Sum-of-rounded** | The rule that displayed components add to the displayed total | `CALC-031` |
| **Tolerance policy** | Exact Decimal internally; display rounding applied once; no epsilon in comparisons | `05` §13 |

### 2.3 Product, engineering and delivery vocabulary (internal)

| Term | Meaning in this product | Authoritative detail |
|---|---|---|
| **ADR** | Architecture Decision Record — a ruling with context, options and consequence | `09` §3 |
| **Coverage Matrix** | The mapping of every spec section to the docs that integrate it | `00_INDEX` §4 |
| **Diagnostics bundle** | The metadata-only support zip the user exports and sends themselves | `13` §7 |
| **Engine** | The pure-Python core that owns all arithmetic, rules, imports, forecasts and exports | `09` §4 |
| **Evidence bundle** | The workbook + zip with a hashed manifest shipped with the Excel pack | `11` §6 |
| **FR / NFR** | Functional requirement / non-functional target | `02` / `14` §3 |
| **Gate** | A quality checkpoint with a checklist and recorded evidence | `14` §15, `16` §5 |
| **Loopback API** | The local HTTP API the UI talks to, bound to `127.0.0.1` with a per-launch token | `09` §9 |
| **Machine-readable stamp** | The 30-field block in every generated workbook that identifies project, versions and filters | `11` §3.5 |
| **Message catalog** | The single list of user-visible strings with stable IDs | `08` §16, `26` |
| **Owner (of a doc)** | The document that decides a fact; other docs cite it | `00_INDEX` §5 |
| **Portable package** | The no-install zip variant of the app | `15` §4.3 |
| **Sample project** | The bundled, watermarked synthetic project loaded on first run | `FR-ONB-001` |
| **Seeded** | Generated from a fixed random seed so results are reproducible | `14` §16 |
| **Single-source rule** | A fact is stated once, in its owning document, and referenced elsewhere | `00_INDEX` §6 |
| **Spike** | A timeboxed investigation (≤ half a day) with a written outcome | `09` §15.1 |
| **Stakeholder roles** | Consultant (builds), project owner (decides), analyst (uses), accounting owner (reviews) | `01` §4 |
| **Traceability chain** | FR → spec section → screen → API endpoint → test | `20` |

### 2.4 Glossary usage rules

1. **The owning doc wins.** This glossary is a navigational aid; it never overrides `02`/`05`/`06`/`07`.
2. **UI copy follows `08` §16.** A term used on a screen must match this glossary *and* the message
   catalog; a screen never invents a synonym.
3. **Client documents follow `29`'s language.** A term explained to the client must be the plain-language
   version of the same concept.
4. **New terms** enter here only when a document defines them; this glossary does not create concepts.

## 3. The assumption register

### 3.1 The canonical register (`A1`…`A20`, from `01` §12)

Every row is **default, unconfirmed** until its `Q-` item is answered. "Cost to change" is the effort to
adopt the client's answer once it arrives.

| ID | Assumption | Default in force | If wrong | Cost to change | Question | Status |
|---|---|---|---|---|---|---|
| `A1` | D365 edition | Generic "D365-style GL export" template + documented dimension parsing | A different export shape needs a mapping profile (config, not code) | Low | `Q-002` | Open |
| `A2` | The two other systems | Two distinct sample shapes: payroll summary, procurement/bank ledger | Real shapes replace the samples as mapping profiles | Low | `Q-003` | Open |
| `A3` | Fiscal calendar | January start, 12 monthly periods, configurable | Period maths re-anchored (config + tests) | Medium | `Q-004` | Open |
| `A4` | Reporting currency | INR, whole units, optional ₹ thousands/lakhs display | Display/scale change; storage unaffected | Low | `Q-006` | Open |
| `A5` | Prior-year data | PY views built; auto-hidden when no PY batch exists | Nothing breaks; the view simply has data | Low | `Q-005` | Open |
| `A6` | Budget versions | One approved annual budget + a `version` field | Additional versions imported as separate batches | Low | `Q-007` | Open |
| `A7` | Forecast cadence | Monthly rolling forecast; Base/Best/Worst scenarios | Cadence is a workflow habit, not a schema change | Low | `Q-008` | Open |
| `A8` | Approval thresholds | Editable master-data table with seeded defaults | Defaults replaced by the client's values | Low | `Q-009` | Open |
| `A9` | Recurring-cost list | Editable master-data table the client maintains | List populated at onboarding; rules degrade until then | Low | `Q-010` | Open |
| `A10` | Vendor master/categories | Optional importable table; dependent rules degrade gracefully | Import once available | Low | `Q-011` | Open |
| `A11` | Current outputs to replicate | None yet; app house style until samples arrive | House-style profile built from the samples | Medium | `Q-012` | Open |
| `A12` | Pack audience | CFO / finance director | KPI strip and commentary tone configurable | Low | `Q-013` | Open |
| `A13` | File sizes in practice | 250k rows / ~100 MB upper bound | `NFR-002`/`NFR-009` re-measured; perf work re-planned | Medium | `Q-014` | Open |
| `A14` | Signing certificate | None; the SmartScreen mitigation ladder applies | Certificate purchased → signing ADR + `15` §8.5 | Medium | `Q-015` | Open |
| `A15` | Delivery channel | Secure link + published SHA-256 | Alternate channel needs the same hash step | Low | `Q-016` | Open |
| `A16` | Training | 60-minute guided session + recorded demo outline | Extra sessions are commercial (`01` §19) | Low | `Q-017` | Open |
| `A17` | Support model | Analyst calls the consultant first; diagnostics-zip workflow | Support terms are a commercial question (`OQ-016`) | Low | `Q-018` | Open |
| `A18` | Branding assets | Working name, neutral placeholder palette, no logo | Assets dropped in via settings; contrast guard applies | Low | `Q-019` | Open |
| `A19` | Data retention | Projects kept locally until the user deletes them | Retention policy documented in `22`/`29` | Low | `Q-020` | Open |
| `A20` | Headcount data | Not provided; headcount metrics parked (`BL-016`) | Re-opens a parked backlog item, not v1 scope | Low | `Q-021` | Open |

### 3.2 Assumptions introduced by later documents (`A21`…)

These are **engineering/delivery** assumptions: they are stated by the owning document and registered
here so that every gate can see the full set. The owning document remains the place where the assumption
is explained.

| ID | Assumption | Default in force | If wrong | Cost to change | Owner doc |
|---|---|---|---|---|---|
| `A21` | Client machines | Windows 11 x64, WebView2 present, standard (non-admin) user account | The WebView2 fallback or the portable package applies; per-machine install becomes a discussion | Low–Medium | `15` §13 |
| `A22` | Reference machine for performance | 4-core / 16 GB / SSD / Windows 11, per the measurement protocol | Baselines re-recorded; comparisons invalidated (annotated) | Low | `14` §3 |
| `A23` | Delivery channel capacity | The agreed channel can carry a ~500 MB file and a checksum | Split/chunked delivery or a different channel (both keep the hash step) | Low | `15` §13 |
| `A24` | Client IT availability | Available for the one-time install if SmartScreen requires it | The written walkthrough stands alone; the install is done together remotely | Low | `15` §13 |
| `A25` | Team shape for estimates | One senior engineer with AI assistance; ideal days exclude client waits | Estimates re-based at the next gate with the variance rule (`16` §7.1) | Low | `16` §13 |
| `A26` | Client analyst availability | Available for the pilot and UAT as planned | UAT scripts are runnable by one person; dates move, the bar does not | Low | `16` §13 |
| `A27` | Office availability | Excel and PowerPoint are available on the client machine to open the artefacts | The structural artefact tests still prove validity; the manual open-test cannot run | Medium | `14` §9.4, `15` §5.2 |
| `A28` | No new compliance regime | No security/privacy/compliance requirement outside `13` emerges | `13` and `25` are revised before the affected phase closes | High | `16` §13 |
| `A29` | Sanitized real data for the pilot | The client provides one sanitized real month (D365 + both other systems) | The pilot gate (`GATE-13`) cannot run; UAT cannot be entered | High | `28`, Addon 4 §F |

### 3.3 Rules for using an assumption

1. **Label it.** Any document, screen or message that depends on an assumption marks it *default,
   unconfirmed* where a reader would otherwise treat it as fact.
2. **Never sell it as truth.** Client-facing documents (`29`) list assumptions as questions with
   recommendations, not as agreed facts.
3. **Escalate when unsafe.** If the default turns out to affect money semantics, data loss, UX flow or a
   client fact, the question becomes **blocking** (§4.2) and work on that thread stops.
4. **Revisit at every gate.** The assumption register is an artefact of every gate (`16` §5.1 item 10);
   an answered question is moved to the Decided log in the same pass.
5. **Cheap-to-change is a design goal.** Where two defaults are equally plausible, choose the one that is
   cheapest to change when the client answers (mapping profiles, settings, brand config).

## 4. The open-question register (`OQ-`)

### 4.1 The register

Status values: **Open** (default in force) · **Answered** (client confirmed; decision pending record) ·
**Decided** (moved to §5, tombstone kept here for traceability) · **Retired** (§4.4).

| ID | Question | Why it matters | Default in force | Owner | Blocking? | Assumption | `Q-` | Status |
|---|---|---|---|---|---|---|---|---|
| `OQ-001` | Which D365 edition/export produced the GL file? | Column set, dimension format and control totals | Generic D365-style template + documented dimension parsing | Client | No | `A1` | `Q-002` | Open |
| `OQ-002` | What are the exact column lists of the two other systems? | Mapping profiles and parsing rules | Two distinct sample shapes (payroll, procurement/bank ledger) | Client | No | `A2` | `Q-003` | Open |
| `OQ-003` | What is the fiscal calendar (year start, period structure)? | Period assignment, windows, comparisons | January start, 12 monthly periods, configurable | Client | No | `A3` | `Q-004` | Open |
| `OQ-004` | Is prior-year data available, and in what form? | PY views and comparisons | Build PY views; auto-hide when no PY batch exists | Client | No | `A5` | `Q-005` | Open |
| `OQ-005` | Single currency or multiple? | Money semantics and quarantine behaviour | INR only; mixed-currency rows quarantined (`DEC-007`) | Client | No | `A4` | `Q-006` | Open |
| `OQ-006` | How many budget versions exist, and how are revisions handled? | Budget import and version fields | One approved annual budget + `version` field | Client | No | `A6` | `Q-007` | Open |
| `OQ-007` | What approval thresholds apply (and where do they come from)? | `EXC-021` and the master-data seed | Editable table seeded with sensible defaults | Client | No | `A8` | `Q-009` | Open |
| `OQ-008` | What is the recurring-cost list? | `EXC-015` (missing recurring cost) quality | Editable master-data table the client maintains | Client | No | `A9` | `Q-010` | Open |
| `OQ-009` | Is a vendor master (with categories) available? | `EXC-014`/`EXC-015` precision and vendor analysis | Optional importable table; rules degrade gracefully | Client | No | `A10` | `Q-011` | Open |
| `OQ-010` | Can we see the current monthly Excel/PPT outputs? | House-style matching (`11` §9, `12` §6) | App house style until samples arrive | Client | No | `A11` | `Q-012` | Open |
| `OQ-011` | Who receives the pack, and in what form? | KPI strip, tone, distribution note | CFO / finance director | Client | No | `A12` | `Q-013` | Open |
| `OQ-012` | Is there budget/lead time for a code-signing certificate? | SmartScreen posture and the install experience | Not purchased; the mitigation ladder applies (`ADR-003`) | Project owner | No | `A14` | `Q-015` | Open |
| `OQ-013` | What file sizes are seen in practice? | `NFR-002`/`NFR-009` targets and performance work | 250k rows / ~100 MB upper bound | Client | No | `A13` | `Q-014` | Open |
| `OQ-014` | When can we get one sanitized real month (D365 + both systems)? | The real-data pilot gate (`GATE-13`) and UAT readiness | None yet; the pilot cannot run without it — a **schedule** dependency, not a design blocker | Client | Schedule | — | `Q-001` | Open |
| `OQ-015` | Can we get the client's logo and two brand colours? | Branding defaults and the contrast guard | Working name, neutral palette, no logo | Client | No | `A18` | `Q-019` | Open |
| `OQ-016` | What support/warranty terms apply after go-live? | `23`/`28` support section and the sign-off | Consultant-first support; diagnostics-zip workflow | Project owner | No | `A17` | `Q-018` | Open |
| `OQ-017` | Which delivery channel is approved for the installer? | Distribution and hash publication | Secure link + published SHA-256 | Project owner | No | `A15` | `Q-016` | Open |
| `OQ-018` | *(never allocated — see §4.4)* | — | — | — | — | — | — | Reserved |
| `OQ-019` | *(never allocated — see §4.4)* | — | — | — | — | — | — | Reserved |
| `OQ-020` | *(retired tombstone — see §4.4)* | — | — | — | — | — | — | **Retired** |
| `OQ-021` | What format is the client's current report (`.xlsx` / `.xlsm` / protected / paper)? | Whether house-style matching can be automated or must be manual | Assume a modern `.xlsx` or a PDF/paper sample; matching degrades to manual guidance | Client | No | `A11` | `Q-012` | Open |
| `OQ-022` | Preferred default units in the pack (whole units vs lakhs)? | Display defaults in Excel/deck | Whole units with an optional lakhs display | Client | No | `A4` | `Q-006` | Open |

**Register size:** 19 live questions (17 design/data + 2 formatting), all non-blocking for Phase 0, plus
one schedule dependency (`OQ-014`) and three reserved/retired numbers.

### 4.2 When a question becomes blocking

A question blocks work when the answer could change **money semantics, data loss, UX flow or a client
fact** (Addon 2 §H.3). The default is then unsafe by definition, and the thread stops.

| Category | Example of a blocking question | Example that is **not** blocking |
|---|---|---|
| Money semantics | "Does 'budget' include reforecasts, and do we compare to the latest or the original?" | "Which currency symbol?" (display, defaulted in `A4`) |
| Data loss | "If two files contain the same period, replace or refuse?" | "What is the file's usual sheet name?" (mapping profile) |
| UX flow | "Does the analyst approve an exception or can the owner?" | "What colour is the flag?" (`08` owns it) |
| Client facts | "Is the fiscal year a calendar year?" — only if the client insists on something the default forbids | "Is the two other systems' shape exactly as sampled?" (mapping handles it) |

**Blocking procedure:** stop the affected thread → write the question in the §4.3 format → record it in
`SESSION_LOG` → continue with unrelated work → record the answer as a `DEC-` row in the same session it
arrives. A blocking question with no answer by the gate becomes a gate item (owner + date), never a
silent default.

### 4.3 The ask format (Addon 2 §H.3)

```
Q: <one sentence, in the client's language>
Why it matters: <one line — what changes depending on the answer>
Options:
  A) <option> — <trade-off> (recommended)
  B) <option> — <trade-off>
  C) <option> — <trade-off>
Recommendation: A, because <reason>.
If we don't hear back: we continue with <default>, which is safe because <reason>.
```

Rules: one question per ask · ≤ 3 options · always a recommendation · always a default · never a question
without a default (if no safe default exists, that is a blocking question and it is stated as such).

### 4.4 `OQ-018`…`OQ-020`: the hygiene flag, resolved

`01` §14 raised a hygiene flag: `OQ-020` was referenced in `01` §16 but defined nowhere, and `OQ-018`/
`OQ-019` were treated as reserved. Resolution (recorded here as the register of record, and applied to
`01` in the same pass):

| ID | Resolution | Rationale |
|---|---|---|
| `OQ-018` | **Never allocated.** Left as a reserved number, never reused | The `11` pass allocated `OQ-021`/`OQ-022` after discovering the phantom; honest numbering beats back-filling |
| `OQ-019` | **Never allocated.** Same treatment | — |
| `OQ-020` | **Retired tombstone.** The `01` §16 reference is corrected to `OQ-016` (support/warranty terms) | Inventing a question to justify a phantom reference would create a duplicate of `OQ-016`; deleting the reference silently would hide the history — a tombstone with a corrected reference is the only honest option |

**Rule going forward:** an ID referenced anywhere must exist in this register. The docs link-check
(`14` §13.1) plus the registry rules of `00_INDEX` §8 keep it true.

## 5. The Decided log (`DEC-`)

Every ruling with its date, rationale and the documents it binds. This table is the log of record;
`01` §21 remains the index of PRD-originated decisions, and `09` §3 holds the ADRs.

### 5.1 Decisions `DEC-001`…`DEC-027` (Phase 0, session 001)

| ID | Decision | Rationale (why) | Binds |
|---|---|---|---|
| `DEC-001` | v1 scope = the 10 approved areas | Protects the phase plan; everything else is parked | `01` §6.1 |
| `DEC-002` | P&L focus; balance sheet/cash flow out of v1 | The month-end job and the data available | `01` §6.3 |
| `DEC-003` | Budgets are import-only | The client owns the budget process; authoring is a different product | `04`, `FR-IMP` |
| `DEC-004` | Journal-category column optional via mapping | Systems differ; forcing it would break imports | `03`, `04` |
| `DEC-005` | Cross-system tie-out = manual control totals in v1 | Automated matching needs data we do not have | `04` §12 |
| `DEC-006` | One-off/exceptional tagging parked (`BL-024`) | No reliable signal in v1 data | `27` |
| `DEC-007` | Single reporting currency; mixed-currency rows quarantined | Avoids invisible FX assumptions in money maths | `03`, `04` |
| `DEC-008` | Per-entity reporting + simple grouped totals; no eliminations | Consolidation is a different problem | `05`, `08` |
| `DEC-009` | Pack audience defaults to CFO/finance director; KPI strip configurable | Matches the brief's stated user | `12` |
| `DEC-010` | Single user, no login, no RBAC; privacy boundary = OS account | The product is a personal analyst tool (`13` §2) | `13`, `08` |
| `DEC-011` | Headcount/FTE metrics parked; no headcount field in the schema | No data available (`A20`) | `03`, `27` |
| `DEC-012` | Prior prototypes are reference-only; no code reuse | Protect the clean start (and the licence position) | `09` |
| `DEC-013` | Success metrics require measured baselines | No claimed improvement without evidence | `14` §8 |
| `DEC-014` | Disclaimer wording is canonical in `01` §15.1 | One wording, enforced everywhere | `08`, `11`, `12`, `15`, `22`, `29` |
| `DEC-015` | Data posture: local-only, no upload, AI opt-in + redacted | The client's confidentiality expectation | `13`, `10` |
| `DEC-016` | Consultant retains app IP; client gets a perpetual usage licence | Commercial clarity | `23`, `29` |
| `DEC-017` | Branding defaults until assets arrive; WCAG AA guard | Ships without assets, stays accessible | `08`, `12` |
| `DEC-018` | Packaging spike immediately after Phase 0 approval | De-risks the delivery path first (`16` §4) | `16` |
| `DEC-019` | Support/warranty terms flagged as a commercial question | Not ours to decide | `OQ-016`, `28` |
| `DEC-020` | Cross-system tie-out: v1 = file-level control totals only | Same as `DEC-005`, made explicit for the rule family | `06` |
| `DEC-021` | Cross-batch duplicate detection uses two keys (voucher+line; vendor+invoice+date+amount) | Neither key alone is sufficient; both have documented false-positive profiles | `06` |
| `DEC-022` | Control-total variance fails the import by default, with a recorded-acceptance path | Silent acceptance would corrupt every downstream number | `04` §12 |
| `DEC-023` | Cross-batch duplicates report and ask (skip / import anyway / cancel) | Never auto-skip, never auto-import — the analyst decides | `04` §13 |
| `DEC-024` | Rules are registered and catalogued; an unregistered module cannot run | Prevents silent behaviour and untested rules | `06` §1 |
| `DEC-025` | Forecast defaults: `remaining_budget`, `N = 3` run-rate, three scenarios with unconfirmed adjustment percentages | Sensible start, cheap to change, transparent | `07` |
| `DEC-026` | AI number-mismatch: figures not in the payload are stripped and flagged | AI never becomes a source of numbers | `10` §8 |
| `DEC-027` | AI redaction defaults: vendor names/descriptions masked; account/cost-centre/entity codes not masked (task-critical) and disclosed | Utility vs privacy, stated openly to the client | `10` §6, `13` |

### 5.2 Decisions `DEC-028`…`DEC-030` (later Phase 0 passes)

| ID | Decision | Rationale (why) | Alternatives rejected | Binds |
|---|---|---|---|---|
| `DEC-028` | **PDF is not rendered in-app.** v1 delivers tested print/PDF readiness plus an "Open for printing / Save as PDF" action using Excel / Microsoft Print to PDF | The architecture has no renderer and Office automation is forbidden; a bad PDF is worse than none | Bundling a renderer; LibreOffice automation; skipping print readiness | `11` §10.3 |
| `DEC-029` | **Missing-input deck behaviour:** always the six slides, with a *not-available* state naming the reason and the action; omission only as an explicit, stated choice | Keeps the deck's structure predictable and the gap visible | Silent omission; blank slides | `12` §2.1, `FR-PPT-001` |
| `DEC-030` | **Data at rest is plain local files.** No app-level encryption of the database or backups in v1; the only encrypted artefact is the AI key (DPAPI) | Honest and testable; application-level crypto would create a false sense of safety without OS-level protection | Encrypted project files; encrypted backups (parked `BL-029`…`BL-035`) | `13` §9 |

### 5.3 Decisions from later Phase-0 documents (registered as they are made)

| ID | Decision | Rationale | Binds |
|---|---|---|---|
| `DEC-031` | **The five Phase-0 gates are `GATE-01`…`GATE-05` (58 checks); the build gates continue the numbering** — `GATE-06` packaging spike, `GATE-07`…`GATE-12` phases 1–6, `GATE-13`…`GATE-15` pilot/UAT/go-live (owned by `28`) | One global gate namespace, no parallel vocabularies | `16` §2.1, `14` §15 |
| `DEC-032` | **The next open item lives in `16` §1.3** and is the first thing a session reads after `00_INDEX`/`CHANGELOG`/`SESSION_LOG` | Kickoff §14.1 needs a single, unambiguous pointer | `16` §1.3, `19` |
| `DEC-033` | **Estimates are ideal developer-days, re-estimated at every gate, with > 50 % variance reported immediately**; no dates are committed in the roadmap | Transparency without false precision; the client's calendar is not ours to promise | `16` §7 |
| `DEC-034` | **Demo scripts are written at the start of each phase**, not before the gate | A phase is built to be demonstrable, which changes decisions early (and catches gaps cheaply) | `16` §11.1 |
| `DEC-035` | **The never-cut list is absolute and cannot be waived at a gate** (`16` §9.2) | Nine properties carry the client's trust; a waiver is where trust breaks | `16` §5.3, `02` §3.3 |
| `DEC-036` | **`ERR-ENG-*` is allocated as the environment/install/upgrade error family** (copy owned by `15` §12, catalogued by `26`) | The delivery path has failure modes of its own; they deserve plain-language codes like every other family | `15` §12, `00_INDEX` §8 |
| `DEC-037` | **Code standards are machine-enforced wherever expressible** (format/lint/types/boundary/coverage), with the review checklist covering the rest | "We remembered" is not a control; automation is the deliverable | `17` §13/§14 |

*New decisions are appended as Phase 0 continues; the table above grows, it never gets rewritten.*

## 6. Maintenance and hygiene of the registers

| Rule | Detail |
|---|---|
| Cadence | Reviewed at **every gate** (`16` §5.1 item 10) and updated whenever a client answer, an ADR or a `Q-` confirmation arrives |
| Who updates | The doc owner making the change updates `18` in the same pass; the `00_INDEX` link-check keeps IDs honest |
| Append-only | A decided row is never rewritten — a later decision supersedes it with a new `DEC-` row that says so |
| No dangling IDs | Every `OQ-`/`DEC-`/`A` ID referenced anywhere exists here; every ID here is referenced by at least one doc |
| No duplicates | A question asked twice is one row with two consumers; a decision made twice is a defect in the register |
| Tombstones | Retired IDs stay visible with their reason (§4.4); numbers are never reused |
| Client language | Rows destined for the client (`21`, `29`) are written in plain language; the register row keeps the technical trigger |
| Ownership of answers | `Client` = the client answers; `Project owner` = the commercial owner answers; `Consultant` = we decide and record |
| The gate artefact | The updated Decided log is part of every phase-gate evidence pack (Addon 3 §K) |

## 7. Open items, deferrals and assumptions about this document

| Item | Status |
|---|---|
| The full questionnaire wording (`Q-001`…`Q-0nn`) | Owned by `21`; seeded from §3/§4 with each item pre-filled with its default (Addon 1 §C.2) |
| Client-facing statement of decisions | Owned by `29`; lists what the client must confirm |
| Risk links for the high-impact questions (`OQ-014`, `OQ-012`, `OQ-016`) | Registered in `25` when it is written |
| Decision dates for `DEC-031`…`DEC-037` | All `2026-10-01` (session 001) — recorded here as the allocation date; later decisions carry their own |
| The `OQ-014` pilot date | Schedule dependency; tracked in `28` and reported at gates |

**Assumptions about the register itself.** (a) The client answers most questions before the Phase-1 gate;
(b) any unanswered question continues on its labelled default without blocking, unless it becomes blocking
by §4.2; (c) the project owner answers the commercial questions (`OQ-012`, `OQ-016`, `OQ-017`).

## 8. Change control and cross-document obligations

### 8.1 Obligations this document places elsewhere

| Obligation | Owner |
|---|---|
| The questionnaire seeds from §3/§4, keeps the same `Q-` IDs and shows each default | `21` |
| The client pack states the decisions the client must confirm and lists the open questions in plain language | `29` |
| Every gate's evidence pack includes the updated Decided log | `16` §5.1 item 10 |
| ADRs are indexed in `09` §3 and cross-referenced here when they settle a question | `09` |
| A "no" answer becomes a `27` entry with a trigger | `27` |
| High-impact questions appear in the risk register | `25` |
| Documents depending on an assumption label it *default, unconfirmed* | every doc (`01` §12 rule) |
| `01` §14's hygiene flag is closed: `OQ-018`/`019` reserved, `OQ-020` retired, the `01` §16 reference corrected to `OQ-016` | `01` (applied in the same pass) |
| Registry rules (no reuse, tombstones) stay identical in substance here and in `00_INDEX` §8 | `00_INDEX` |

### 8.2 Changes to this document

| Change | Requires |
|---|---|
| A new open question | An ID, an owner, a default and a `Q-` link (or a note that it is a schedule dependency); `CHANGELOG` entry |
| A question answered | The `OQ` row status updated **and** a `DEC-` row created with the date/rationale; affected docs updated in the same pass |
| A new decision | A `DEC-` row with rationale, alternatives (if any) and the docs it binds; `01` §21 index updated if PRD-originated |
| A retired question | A tombstone row with the reason (§4.4) |
| A glossary term | Only when a document defines it; the owning doc is cited |
| An assumption change | The owning doc's assumption note is updated first (or in the same pass) |

**Frozen constants owned by this document:** the question states and lifecycle (§1.2) · the register rules
(§1.3) · the glossary term definitions (§2.1–§2.3) · the `A1`…`A29` assumption register with defaults
(§3) · the `OQ-` register and the blocking rules (§4) · the ask format (§4.3) · the `OQ-018`…`020`
resolution (§4.4) · the `DEC-001`…`DEC-037` log (§5) · the maintenance cadence and hygiene rules (§6).
