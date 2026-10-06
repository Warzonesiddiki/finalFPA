> **Status:** Draft v0.1
> **Last updated:** 2026-10-05
> **Owning FRs/areas:** the glossary of FP&A and product vocabulary; the **canonical assumption register**
> with defaults and owners (Kickoff §5, `01` §12); the **`OQ-` open-question register** with every
> unconfirmed client fact (Kickoff §5 gate item); the **`DEC-` Decided log** with dates, rationale and
> affected docs (Addon 3 §B.2/B.3); the blocking-question protocol (Addon 2 §H.3); and registry hygiene
> (`01` §14's `OQ-018`…`020` flag)
> **TL;DR (≤ 15 lines):**
> - **Single register of record:** Authoritative glossary of FP&A terminology, technical concepts, and business rules.
> - **Assumptions log:** 29 labeled assumptions (A1–A29) documenting operational, architectural, and data expectations.
> - **Open questions tracker:** 23 open questions (OQ-001 to OQ-029; `OQ-025`…`027` decided 2026-10-05 → `DEC-056`…`058`; `OQ-028` raised and decided 2026-10-05 → `DEC-066` — `WC-1`'s catalog source no longer exists; `OQ-029` raised 2026-10-05 — `ADR-002` pins Python 3.12.x while the tree runs 3.14.7), each with context, options, recommendations, and safe defaults.
> - **Decided log:** 67 binding architectural and product decisions (DEC-001 to DEC-067) with rationales and alternatives.
> - **Gate prerequisite:** Phase gates require zero unaddressed blocking questions; all changes update this register first.

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
| **Suspense account** | Chart of accounts code (default `1999`, `9999`, `SUSPENSE`) reserved for unallocated or temporary balances; monitored strictly by `EXC-024` for month-end close residual; prohibited from absorbing artificial trial-balance plugs | `03` §5.2, `06` EXC-024, `DEC-067` |
| **Tie-out** | Proving two numbers agree (control total vs GL, workbook vs engine) | `04` §12, `14` §7 |
| **Trial balance plug** | An artificial single-sided balancing entry inserted into a ledger to force debits = credits; strictly prohibited as it contaminates exception detection rules and violates double-entry integrity | `03` §5.2, `04` §12, `DEC-067` |
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
| **Deduplicated batch** | An import batch filtered for exact or composite key duplicates prior to staging | `04` §13 |
| **Comparability guard** | The rule that refuses to compare figures that are not comparable | `FR-BVA-013` |
| **Cross-artifact equality** | Engine, UI, Excel, deck and CSV must agree exactly at display precision | `NFR-015`, `14` §7 |
| **Data-quality score** | A weighted score over the import's checks; never shown alone, never hides a failure | `CALC-050`, `04` §16 |
| **Degradation** | A rule that cannot run (missing master data) says so; it never silently passes | `06` §2.9 |
| **Effective threshold** | The threshold actually applied, after overrides, recorded for traceability | `06` §2.10 |
| **False positive** | A raised exception the analyst judges wrong; managed by mitigation and precision controls | `06` §8 |
| **Golden fixture** | A frozen input/output pair with exact expected numbers | `05` §12, `14` §5 |
| **Identity hash** | `SHA-256(rule_id\|subject_key)` — the stable identity of an exception across re-runs | `06` §2.2 |
| **Idempotent** | Running twice changes nothing the second time | `06` §2.2 |
| **Mapping queue** | The staging queue where unmapped GL accounts and dimensions await analyst assignment | `04` §7 |
| **Materiality AND-test** | Both the amount and the percentage thresholds must be crossed | `CALC-080` |
| **Provenance** | The complete lineage trail tracing any aggregated figure back to its source import file and rows | `04` §15, `13` §5 |
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

| ID | Question | Why it matters | Default in force | Owner | Needed by | Blocking? | Assumption | `Q-` | Status |
|---|---|---|---|---|---|---|---|---|---|
| `OQ-001` | Which D365 edition/export produced the GL file? | Column set, dimension format and control totals | Generic D365-style template + documented dimension parsing | Client | Phase 1 (`GATE-07`) | No | `A1` | `Q-002` | Open |
| `OQ-002` | What are the exact column lists of the two other systems? | Mapping profiles and parsing rules | Two distinct sample shapes (payroll, procurement/bank ledger) | Client | Phase 1 (`GATE-07`) | No | `A2` | `Q-003` | Open |
| `OQ-003` | What is the fiscal calendar (year start, period structure)? | Period assignment, windows, comparisons | January start, 12 monthly periods, configurable | Client | Phase 1 (`GATE-07`) | No | `A3` | `Q-004` | Open |
| `OQ-004` | Is prior-year data available, and in what form? | PY views and comparisons | Build PY views; auto-hide when no PY batch exists | Client | Phase 1 (`GATE-07`) | No | `A5` | `Q-005` | Open |
| `OQ-005` | Single currency or multiple? | Money semantics and quarantine behaviour | INR only; mixed-currency rows quarantined (`DEC-007`) | Client | Phase 1 (`GATE-07`) | No | `A4` | `Q-006` | Open |
| `OQ-006` | How many budget versions exist, and how are revisions handled? | Budget import and version fields | One approved annual budget + `version` field | Client | Phase 1 (`GATE-07`) | No | `A6` | `Q-007` | Open |
| `OQ-007` | What approval thresholds apply (and where do they come from)? | `EXC-021` and the master-data seed | Editable table seeded with sensible defaults | Client | Phase 1 (`GATE-07`) | No | `A8` | `Q-009` | Open |
| `OQ-008` | What is the recurring-cost list? | `EXC-015` (missing recurring cost) quality | Editable master-data table the client maintains | Client | Phase 1 (`GATE-07`) | No | `A9` | `Q-010` | Open |
| `OQ-009` | Is a vendor master (with categories) available? | `EXC-014`/`EXC-015` precision and vendor analysis | Optional importable table; rules degrade gracefully | Client | Phase 1 (`GATE-07`) | No | `A10` | `Q-011` | Open |
| `OQ-010` | Can we see the current monthly Excel/PPT outputs? | House-style matching (`11` §9, `12` §6) | App house style until samples arrive | Client | Phase 3 (`GATE-09`) | No | `A11` | `Q-012` | Open |
| `OQ-011` | Who receives the pack, and in what form? | KPI strip, tone, distribution note | CFO / finance director | Client | Phase 3 (`GATE-09`) | No | `A12` | `Q-013` | Open |
| `OQ-012` | Is there budget/lead time for a code-signing certificate? | SmartScreen posture and the install experience | Not purchased; the mitigation ladder applies (`ADR-003`) | Project owner | Phase 2 (`GATE-06`) | No | `A14` | `Q-015` | Open |
| `OQ-013` | What file sizes are seen in practice? | `NFR-002`/`NFR-009` targets and performance work | 250k rows / ~100 MB upper bound | Client | Phase 2 (`GATE-08`) | No | `A13` | `Q-014` | Open |
| `OQ-014` | When can we get one sanitized real month (D365 + both systems)? | The real-data pilot gate (`GATE-13`) and UAT readiness | Default 'no date assumed'; ask-client-for-date action logged in doc 21 tracker. Schedule dependency, not design blocker. | Client | Pilot (`GATE-13`) | Schedule | — | `Q-001` | Open · default in force |
| `OQ-015` | Can we get the client's logo and two brand colours? | Branding defaults and the contrast guard | Generic professional default locked with Settings runtime hot-swap (`DEC-048`, `FR-SET-008`). Working name, neutral palette, no logo. | Client | Phase 3 (`GATE-09`) | No | `A18` | `Q-019` | Open · default in force |
| `OQ-016` | What support/warranty terms apply after go-live? | `23`/`28` support section and the sign-off | Consultant-first defaults (30-day S1/S2 warranty, 2-day SLA targets, backlog enhancements, no 24/7) as default-unconfirmed; diagnostics-zip workflow (`23`) | Project owner | Go-Live (`GATE-15`) | No | `A17` | `Q-018` | Open · default in force |
| `OQ-017` | Which delivery channel is approved for the installer? | Distribution and hash publication | Secure-link + out-of-band published SHA-256 (`15` §1.2, `24` §7); any approved channel must carry installer and checksum | Project owner | Phase 2 (`GATE-06`) | No | `A15` | `Q-016` | Open · default in force |
| `OQ-018` | *(never allocated — see §4.4)* | — | — | — | — | — | — | — | Reserved |
| `OQ-019` | *(never allocated — see §4.4)* | — | — | — | — | — | — | — | Reserved |
| `OQ-020` | *(retired tombstone — see §4.4)* | — | — | — | — | — | — | — | **Retired** |
| `OQ-021` | What format is the client's current report (`.xlsx` / `.xlsm` / protected / paper)? | Whether house-style matching can be automated or must be manual | Assume a modern `.xlsx` or a PDF/paper sample; matching degrades to manual guidance | Client | Phase 3 (`GATE-09`) | No | `A11` | `Q-012` | Open |
| `OQ-022` | Preferred default units in the pack (whole units vs lakhs)? | Display defaults in Excel/deck | Whole units with an optional lakhs display | Client | Phase 3 (`GATE-09`) | No | `A4` | `Q-006` | Open |
| `OQ-023` | What is the vendor-master CSV shape (name vs category columns)? | `DimVendor` requires `vendor_name NOT NULL` (`03` §3.4) but `04` §2.2 requires only "vendor code, category", no sample vendor file exists, and neither `MasterVendorCategory` nor the general `AuditLog` table exists in `schema_sqlite.sql` | Accept `vendor_code` + `vendor_name` headers; `vendor_name` defaults to `vendor_code`; `category*` columns accepted and recorded as ignored; audit = `FactImportBatch` + `FactValidationCheck` rows only (general `AuditLog` still owed per external audit R11) | Consultant | Phase 1 (`GATE-07`) | No | `A10` | n/a — loader-internal default, no client ask | Open |
| `OQ-024` | Quarantine or load-with-warning for budget lines with unknown dimensions? | `03` §7 I12 says unmapped values are quarantined; `04` IMP-013 says unknown accounts are a Warning (loaded + listed) | Quarantine: a `FactBudget` row cannot reference a nonexistent `account_id` without inventing a placeholder account (which would trip EXC-002), so the I12 reading is the only implementable one; the row is quarantined with `import.unknownDimensions` and listed in the report | Consultant | Phase 1 (`GATE-07`) | No | — | n/a — loader-internal default, no client ask | Open |
| `OQ-025` | Does `04` §12 / `IMP-023`'s unconditional debit=credit reject apply to **amount-style sub-ledger exports** (a bank statement is one-sided by nature; `04` §2.2 line 174 defines payroll/procurement as `amount`-style), or only to journal-style sources such as `actuals_d365`? | Decides whether the corpus's bank-ledger and payroll/procurement shapes can ever load, and therefore whether plantings the answer key assigns to them (`P1` — bank ledger under a ₹500 tolerance per `06` §8; `P9` — `batch_040` payroll/procurement) are reachable at all. Measured 2026-10-04: both files are rejected with 0 rows committed under the DEF-010 spec-wins rule | Keep the reject unconditional (DEF-010 status quo) and rebuild both fixtures as balanced where the shape allows, treating a bank statement as a control-total reconciliation source rather than a balanced journal — **default unsafe by definition** (money semantics) | Project owner | Acceptance gate (`14` §5.3) | **Yes** — recall cannot reach `≥ 29/32` while a planted source cannot load | — | **Decided `DEC-056` (2026-10-05)** |
| `OQ-026` | When `sample-data/expected_exceptions.csv` and `06` §4 disagree on a rule's **subject key or scope**, which wins for the acceptance join? | The harness joins on the answer key (`14` §5.1) and never reconciles. Four plantings are structurally unmatchable as written: `P6` (`entity\|IN02` vs EXC-006's default `scope_grain = entity_account`, 34 findings raised), `P8` (key omits cost centre while `06`'s key includes it, and the documented ₹500,000 floor suppresses the planted ₹12,500), `P2`/`P3`/`P9`/`P1` (batch-numbered keys `batch_037/039/040/041` the corpus never produces), `P20`/`P21`/`P24` (rule fires, key format differs) | Report divergences and change nothing (current harness behaviour) | Project owner | Acceptance gate (`14` §5.3) | **Yes** — key format alone caps recall below the `≥ 29/32` bar | — | **Decided `DEC-057` (2026-10-05)** |
| `OQ-027` | Does the sample project need an explicit **import-history fixture** — an earlier overlapping export for `P2` ("re-export overlaps batch 37"), a control-totals-supplied GL batch for `P3`, and the payroll/bank batches `040`/`041` — or should the answer key use the batch ids a three-file harness actually produces (1-3)? | `EXC-002` only fires against an *earlier committed* batch, and no earlier copy of `VCH-2026-0915-001/002` exists anywhere in `sample-data/`; the control-totals block exists only in the `.xlsx` template. Without a history fixture those plantings and the batch-numbered keys cannot both be satisfied | Build the history fixture (corpus files + a harness step that imports them in order) and keep the documented keys | Consultant (corpus) / Project owner if keys change | Acceptance gate (`14` §5.3) | **Yes** for `P2`/`P3` | — | **Decided `DEC-058` (2026-10-05)** |

| `OQ-028` | **`WC-1`'s catalog source `WS-01` no longer exists — adopt a replacement, build the capability ourselves, or re-scope the card?** | Addon 6 v2 §9 pre-approves `WC-1` as COPY-EDIT of `github.com/ricothanfx/invoice-dedupe` §3 catalog `WS-01` (MIT via `pyproject.toml`, "normalization, blocking, weighted-scoring modules only"). Measured 2026-10-05: `git clone --depth 1 … vendor/_upstream/WS-01` → `remote: Repository not found.` / `fatal: repository … not found`, **git exit 128** (captured twice, exit preserved); a web search finds no such repo and no renamed successor. So §6 "S2 — Fetch pinned upstream" cannot complete and the pinned SHA the `ADP` row must cite cannot be obtained. §6 S4 ("listed file missing → STOP → docs/18") and §14 (Tier C: proceed only with owner direction) both apply. **Aggravating finding from `S0`, which should inform the answer:** the capability `WC-1` targets is *already spec-complete* without any adoption — `06`'s duplicate rules are all Tier **`exact`** (`EXC-002` cross-batch rows, `EXC-007` duplicate invoice, `EXC-008` duplicate voucher line), so the normalisation clause (`EXC-007`: "trim, upper-case, strip leading zeros and non-alphanumeric separators") and the blocking/grouping are implemented and passing at `rules_01_08.py:221` (`_normalize_invoice_no`), `rules_01_08.py:evaluate_exc_001` and `rules_catalog_001_008.py:evaluate_exc_008`. `WS-01`'s headline capability, **weighted/fuzzy scoring, is not required by any `06` rule**: the eight `fuzzy`-Tier rules (`EXC-013`…`EXC-022`) are magnitude / pairing / completeness / budget-relationship / controls rules, none a text-similarity problem, and `06` deliberately keeps duplicate detection exact to protect precision (`EXC-007` mitigation: "Partial-amount duplicates … deliberately out of scope for v1 to keep precision high"). Adopting a fuzzy scorer into `EXC-007`/`EXC-008` would change their Tier and put the `14` §5.3 "0 of 8 controls may raise" bar at risk — i.e. `R1` (spec wins) forbids it | **(1)** *Recommended:* **BUILD path + `BD` row** — close `WC-1` as "no copyable source; capability already satisfied", record `BD-001` in `32` §2 with the search evidence, add a `TB` row to `33` for the one real gap (the normaliser and the two blockers live inline in rule modules rather than behind a shared `dedupe` interface), and implement that **interface extraction as our own code** so `R12` (one implementation per capability) is satisfied without importing anything. (2) *Intake a replacement source* per §10 (candidates seen: `dedupeio/dedupe` — MIT but a heavyweight ML stack (`numpy`/`scipy`/`affinegap`/`categorical`), i.e. `R9` + `R13` + it solves the fuzzy problem the spec does not have; `pimverschuuren/Deduplication` and `pmessan/duplicate_invoice_finder` — licences unverified). (3) *Skip `WC-1`* and proceed to `WC-5` (corpus) or `WC-1`'s `TB-020` sibling | Project owner | `WC-1` (`GATE-13` unaffected; `AC` gate **not** blocked — no rule changes) | **No** — no FR, rule or threshold moves under any option; only *where* the existing code lives changes | — | **Decided `DEC-066` (2026-10-05)** — option 1 (BUILD + `BD-001`); the shared interface is extracted as our own code and the duplicate rules rewired through it, acceptance measured identical to baseline |
| `OQ-029` | **`ADR-002` pins Python `3.12.x`, but the tree, the tests and the packaging all run **`3.14.7`** — amend the ADR, or downgrade the environment?** | Measured 2026-10-05 while landing `TB-018`'s pins: `pyproject.toml` declares `requires-python = ">=3.12"` (a floor, not a pin), the interpreter in use is **3.14.7** (`python --version`, and `platform.python_version()`), the full suite is green on it (**884 passed, 16 deselected**), and `09` §3.3 says *“Python `3.12.x` pinned (`pyproject.toml` + `.python-version`)”*. `.python-version` has been written as `3.14.7` — the version that is actually true — rather than the version the ADR names, because a pin file that lies is worse than no pin file. Per **R1** the ADR is *not* edited here. Node is consistent: `26.10.0` (an even/LTS major), recorded in `.nvmrc`, and `ui/package-lock.json` already exists (1,989 lines) | **(1)** *Recommended:* amend `ADR-002` §“Version pinning” to `3.14.x` and tighten `requires-python` to `>=3.14,<3.15`, so the spec, the pin and the machine agree; the deprecation warnings in the suite (`datetime.utcnow()`) are 3.12+ signals that the floor is stale. **(2)** Keep the ADR at 3.12.x and rebuild the environment on a 3.12 interpreter (costs a full re-verify of 884 tests and the packaging). **(3)** Leave both loose and treat `ADR-002` as advisory (weakest: the ADR exists precisely to stop framework/toolchain drift) | Project owner | `D3`/`D8` (`scripts/check` transcript, fresh-clone bootstrap) and `TB-018` closure | **No** — product work is unaffected; the environment already satisfies `>=3.12` | Pin `.python-version` to the real interpreter version now, `uv.lock` owed separately | Open |

**Register size:** 21 live questions (16 design/data + 2 formatting + 2 loader-internal + 1 reuse/process) plus 4 decided on 2026-10-05 (`OQ-025`…`028` → `DEC-056`…`058`, `DEC-066`), all non-blocking for Phase 0, plus
one schedule dependency (`OQ-014`) and three reserved/retired numbers. **`OQ-025`-`OQ-027` are the first questions to block
anything:** each one caps the doc 14 §5.3 planted-exception bars by construction, so the acceptance gate cannot go green until
they are answered (owner) or defaulted (recorded in `CHANGELOG`).

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

| ID | Date | Decision | Rationale (why) | Binds |
|---|---|---|---|---|
| `DEC-001` | 2026-10-01 | v1 scope = the 10 approved areas | Protects the phase plan; everything else is parked | `01` §6.1 |
| `DEC-002` | 2026-10-01 | P&L focus; balance sheet/cash flow out of v1 | The month-end job and the data available | `01` §6.3 |
| `DEC-003` | 2026-10-01 | Budgets are import-only | The client owns the budget process; authoring is a different product | `04`, `FR-IMP` |
| `DEC-004` | 2026-10-01 | Journal-category column optional via mapping | Systems differ; forcing it would break imports | `03`, `04` |
| `DEC-005` | 2026-10-01 | Cross-system tie-out = manual control totals in v1 | Automated matching needs data we do not have | `04` §12 |
| `DEC-006` | 2026-10-01 | One-off/exceptional tagging parked (`BL-024`) | No reliable signal in v1 data | `27` |
| `DEC-007` | 2026-10-01 | Single reporting currency; mixed-currency rows quarantined | Avoids invisible FX assumptions in money maths | `03`, `04` |
| `DEC-008` | 2026-10-01 | Per-entity reporting + simple grouped totals; no eliminations | Consolidation is a different problem | `05`, `08` |
| `DEC-009` | 2026-10-01 | Pack audience defaults to CFO/finance director; KPI strip configurable | Matches the brief's stated user | `12` |
| `DEC-010` | 2026-10-01 | Single user, no login, no RBAC; privacy boundary = OS account | The product is a personal analyst tool (`13` §2) | `13`, `08` |
| `DEC-011` | 2026-10-01 | Headcount/FTE metrics parked; no headcount field in the schema | No data available (`A20`) | `03`, `27` |
| `DEC-012` | 2026-10-01 | Prior prototypes are reference-only; no code reuse | Protect the clean start (and the licence position) | `09` |
| `DEC-013` | 2026-10-01 | Success metrics require measured baselines | No claimed improvement without evidence | `14` §8 |
| `DEC-014` | 2026-10-01 | Disclaimer wording is canonical in `01` §15.1 | One wording, enforced everywhere | `08`, `11`, `12`, `15`, `22`, `29` |
| `DEC-015` | 2026-10-01 | Data posture: local-only, no upload, AI opt-in + redacted | The client's confidentiality expectation | `13`, `10` |
| `DEC-016` | 2026-10-01 | Consultant retains app IP; client gets a perpetual usage licence | Commercial clarity | `23`, `29` |
| `DEC-017` | 2026-10-01 | Branding defaults until assets arrive; WCAG AA guard | Ships without assets, stays accessible | `08`, `12` |
| `DEC-018` | 2026-10-01 | Packaging spike immediately after Phase 0 approval | De-risks the delivery path first (`16` §4) | `16` |
| `DEC-019` | 2026-10-01 | Support/warranty terms flagged as a commercial question | Not ours to decide | `OQ-016`, `28` |
| `DEC-020` | 2026-10-01 | Cross-system tie-out: v1 = file-level control totals only | Same as `DEC-005`, made explicit for the rule family | `06` |
| `DEC-021` | 2026-10-01 | Cross-batch duplicate detection uses two keys (voucher+line; vendor+invoice+date+amount) | Neither key alone is sufficient; both have documented false-positive profiles | `06` |
| `DEC-022` | 2026-10-01 | Control-total variance fails the import by default, with a recorded-acceptance path | Silent acceptance would corrupt every downstream number | `04` §12 |
| `DEC-023` | 2026-10-01 | Cross-batch duplicates report and ask (skip / import anyway / cancel) | Never auto-skip, never auto-import — the analyst decides | `04` §13 |
| `DEC-024` | 2026-10-01 | Rules are registered and catalogued; an unregistered module cannot run | Prevents silent behaviour and untested rules | `06` §1 |
| `DEC-025` | 2026-10-01 | Forecast defaults: `remaining_budget`, `N = 3` run-rate, three scenarios with unconfirmed adjustment percentages | Sensible start, cheap to change, transparent | `07` |
| `DEC-026` | 2026-10-01 | AI number-mismatch: figures not in the payload are stripped and flagged | AI never becomes a source of numbers | `10` §8 |
| `DEC-027` | 2026-10-01 | AI redaction defaults: vendor names/descriptions masked; account/cost-centre/entity codes not masked (task-critical) and disclosed | Utility vs privacy, stated openly to the client | `10` §6, `13` |

### 5.2 Decisions `DEC-028`…`DEC-030` (later Phase 0 passes)

| ID | Date | Decision | Rationale (why) | Alternatives rejected | Binds |
|---|---|---|---|---|---|
| `DEC-028` | 2026-10-01 | **PDF is not rendered in-app.** v1 delivers tested print/PDF readiness plus an "Open for printing / Save as PDF" action using Excel / Microsoft Print to PDF | The architecture has no renderer and Office automation is forbidden; a bad PDF is worse than none | Bundling a renderer; LibreOffice automation; skipping print readiness | `11` §10.3 |
| `DEC-029` | 2026-10-01 | **Missing-input deck behaviour:** always the six slides, with a *not-available* state naming the reason and the action; omission only as an explicit, stated choice | Keeps the deck's structure predictable and the gap visible | Silent omission; blank slides | `12` §2.1, `FR-PPT-001` |
| `DEC-030` | 2026-10-01 | **Data at rest is plain local files.** No app-level encryption of the database or backups in v1; the only encrypted artefact is the AI key (DPAPI) | Honest and testable; application-level crypto would create a false sense of safety without OS-level protection | Encrypted project files; encrypted backups (parked `BL-029`…`BL-035`) | `13` §9 |

### 5.3 Decisions from later Phase-0 documents (registered as they are made)

| ID | Date | Decision | Rationale | Binds |
|---|---|---|---|---|
| `DEC-031` | 2026-10-01 | **The Phase-0 checklists are `GATE-01`…`GATE-05` plus provisional `GATE-05B` for Addon 5 deltas (66 checks); the build gates continue the numbering** — `GATE-06` packaging spike, `GATE-07`…`GATE-12` phases 1–6, `GATE-13`…`GATE-15` pilot/UAT/go-live (owned by `28`). `GATE-05B` is provisional until the Addon 5 contract confirms final numbering | One global gate namespace, no parallel vocabularies | `16` §2.1, `14` §15 |
| `DEC-032` | 2026-10-01 | **The next open item lives in `16` §1.3** and is the first thing a session reads after `00_INDEX`/`CHANGELOG`/`SESSION_LOG` | Kickoff §14.1 needs a single, unambiguous pointer | `16` §1.3, `19` |
| `DEC-033` | 2026-10-01 | **Estimates are ideal developer-days, re-estimated at every gate, with > 50 % variance reported immediately**; no dates are committed in the roadmap | Transparency without false precision; the client's calendar is not ours to promise | `16` §7 |
| `DEC-034` | 2026-10-01 | **Demo scripts are written at the start of each phase**, not before the gate | A phase is built to be demonstrable, which changes decisions early (and catches gaps cheaply) | `16` §11.1 |
| `DEC-035` | 2026-10-01 | **The never-cut list is absolute and cannot be waived at a gate** (`16` §9.2) | Nine properties carry the client's trust; a waiver is where trust breaks | `16` §5.3, `02` §3.3 |
| `DEC-036` | 2026-10-01 | **`ERR-ENG-*` is allocated as the environment/install/upgrade error family** (copy owned by `15` §12, catalogued by `26`) | The delivery path has failure modes of its own; they deserve plain-language codes like every other family | `15` §12, `00_INDEX` §8 |
| `DEC-037` | 2026-10-01 | **Code standards are machine-enforced wherever expressible** (format/lint/types/boundary/coverage), with the review checklist covering the rest | "We remembered" is not a control; automation is the deliverable | `17` §13/§14 |
| `DEC-038` | 2026-10-02 | **Drop Pandas dependency; use native Python / duckdb / sql analytics** | Eliminates massive external dependency footprint, reduces PyInstaller bundle size, and simplifies dependency tree without sacrificing analytical query performance | `09` §3, `15` §4 |
| `DEC-039` | 2026-10-02 | **Split performance test suite (`pytest -m perf`) from unit and integration tests** | Prevents heavy benchmark runs from slowing down standard CI/CD test gates while ensuring dedicated performance SLAs remain continuously monitored | `14` §4, `28` §5 |
| `DEC-040` | 2026-10-02 | **Defensive exclude auditing for PyInstaller builds** | Explicitly excludes unused binary modules and test packages to ensure clean, deterministic distribution artifacts and avoid inclusion of unauthorized runtime dependencies | `15` §6 |
| `DEC-041` | 2026-10-02 | **UAT-02 reconciliation basis established around trial balance control totals and variance tolerances** | Provides a verifiable, auditable basis for month-end sign-off matching client expectations | `28` §4, `04` §12 |
| `DEC-042` | 2026-10-02 | **Packaging output artifacts explicitly marked as non-authoritative draft/pilot until formal sign-off** | Protects governance boundaries and prevents unverified build distributions from being treated as final client-facing releases | `15` §2, `24` §3 |
| `DEC-043` | 2026-10-02 | **API contract-drift checks enforced as hard gate criteria** | Prevents undocumented schema divergence between FastAPI backend and React frontend during iterative feature development | `26` §2, `16` §5 |
| `DEC-044` | 2026-10-02 | **Requirements traceability matrix status flipped from Spec'd to Built upon completion of verification tests** | Reflects accurate implementation status across all core features and exception rules | `20` §2, `28` §2 |
| `DEC-045` | 2026-10-03 | **`EXC-011`'s subject key is `company_code\|voucher_no` (2 parts), matching `sample-data/expected_exceptions.csv` P11 — not the 3-part `company_code\|voucher_no\|posting_date` shown in `06`** | Where the catalog and the ground-truth fixture disagree on a subject key, **the fixture is authoritative**, following the `EXC-016` precedent (`IN01\|6100\|CC-120`, `DEC` recorded with the same reasoning). The key feeds `sha256(rule_id\|subject_key)`, which drives re-run identity matching and `flagged_again`; a key that differs from the fixture makes every planted case a non-match. The posting date remains a **grouping** input — two future dates for one voucher still yield two findings — it is only excluded from the **identity**. Verified zero vouchers with two future dates in the sample corpus; the shared-identity case is documented in code and pinned by `tests/unit/test_rules_09_16.py::test_exc_011_grouping_by_date_is_unchanged_by_the_key_change`. Raised by the `EXC-011` threshold-tuning review (2026-10-03), which found the rule at 100 % recall on P11 and the register flood caused by extract scope, not thresholds | `06` EXC-011, `14` §14.1, `03` §5.2 |
| `DEC-046` | 2026-10-03 | **DuckDB primary keys are allocated in Python and supplied explicitly on INSERT — DuckDB has no auto-increment column** | Measured against this project's own DuckDB 1.5.6: `INTEGER PRIMARY KEY` does **not** self-assign (omitting the column raises `NOT NULL constraint failed`), both `GENERATED ... AS IDENTITY` forms raise `NotImplementedException: Constraint not implemented!`, and `AUTOINCREMENT` is a `ParserException` because it is SQLite syntax. That is exactly why `MappingSuggestionAudit` (`schema_sqlite.sql:237`) works while the equivalent DuckDB tables did not, and why `PeriodRepository.open_period`/`close_period`/`reopen_period` were unreachable (`DEF-008`). The ruling generalises: any new DuckDB table must either supply its key at the INSERT or use an explicit `CREATE SEQUENCE` + `nextval`, and **`AUTOINCREMENT` copied from a SQLite DDL into a DuckDB DDL is a defect**. Existing convention already complies — `db.py:90` seeds `DimPeriod` with an explicit `period_id` and `ImportRepository.commit_budget_replace` computes `budget_id` in Python — so this records the rule rather than changing behaviour. Key allocation lives in `PeriodRepository._next_id()`; the read-then-write is safe under `ADR-004`'s single-user, one-writer-per-file model | `09` ADR-007 / ADR-004, `03` §2.1, `28` §12 (`DEF-008`) |
| `DEC-054` | 2026-10-03 | **Restore missing planted test cases via deterministic sample data regeneration** (`DEC-REQ-01`, renumbered from `DEC-046` per `DEF-014` duplicate collision fix) | Restores 100% recall across all 40 plantings while preserving ground-truth answer key `sample-data/expected_exceptions.csv` intact; conditional on zero answer key edits | `06` §7, `14` §15.4 |
| `DEC-047` | 2026-10-03 | **Mitigate EXC-011 future-dated finding volume via period-aware ranking and server-side pagination** (`DEC-REQ-02`) | Eliminates UI register flood without suppressing auditable rows; conditional on register volume perf verification under high row counts | `06` EXC-011, `14` §14.1 |
| `DEC-048` | 2026-10-03 | **Adopt neutral default application branding for pilot distribution** (`DEC-REQ-03`) | Unblocks pilot packaging without custom client styling dependencies; conditional on runtime branding customization via Settings screen | `08` SCR-034, `24` §3 |
| `DEC-049` | 2026-10-03 | **Distribute pilot as unsigned Windows executable with SHA-256 verification and SmartScreen walkthrough** (`DEC-REQ-04`) | Enables immediate pilot evaluation without code-signing certificate delays; conditional on formal Signing ADR (`ADR-004`) documenting OV/EV options, cost, lead time, and go-live plan | `15` §8.2, `25` RISK-007, `ADR-004` |
| `DEC-050` | 2026-10-03 | **Re-scope test coverage bars to 90% for domain engines and 75% for store layers (`DEC-REQ-05`) ratified as SELF-CERTIFIED — PENDING AUDIT** | Focuses rigorous 90% verification on core calculation/rules/forecast engines while unblocking pilot packaging. Ratified under audit-wave conditions: (1) money paths in 90% tier (`calc/`, `rules/`, `forecast/methods.py`, `ai/`), (2) store layers held to ≥75% floor, (3) automated split check enforced in `scripts/check.py`, (4) golden fixtures untouched. Gate reopens immediately on failed audit per fix-forward policy (`28` §2) | `14` NFR-014, `28` DEF-003, `16` |
| `DEC-051` | 2026-10-03 | **Enforce hard build failure on OpenAPI contract drift** (`DEC-REQ-06`) | Guarantees zero schema divergence between FastAPI backend and React frontend via automated drift gate in CI/build | `26` §2, `16` §5 |
| `DEC-052` | 2026-10-03 | **Purge provable test-origin batches from live project database with snapshot secured** (`purge-test-batches`) | Cleans non-production fixtures (`gl_api_seam.csv`, mapping fixtures) while preserving snapshot at `backups/snapshot_20261002_233619/`; conditional on live-DB root-cause isolation hardening (`BL-038`) | `04` §12, `27` BL-038 |
| `DEC-053` | 2026-10-03 | **Activate sample-data fallback pilot under `RISK-002` / `DEC-REQ-07` with mandatory limitation notice** | Scope check passed on all four criteria (switches to synthetic sample corpus; defers real client reconciliation; zero P0/never-cut impact; fully reversible when client data arrives; documented contingency armed). Pilot executed on sample data to validate software workflows, UAT familiarization, and tie-out mechanics with mandatory limitation notices | `28` §4.6, `25` (RISK-002), `GATE-13` |
| `DEC-055` | 2026-10-03 | **Seed `42` is canonical for the committed sample corpus; the acceptance harness fingerprints the CSV corpus only and records the `.xlsx` exclusion as a known limitation** | Doc 14 §5.2 step 1 previously read `sample-data --seed 20260101`. That seed was never used: the committed corpus was generated with the generator's default **`42`** ("default: 42, preserving baseline output"), and audit `New-06` reproduced it **byte-exactly** at seed 42. Regenerating the corpus two days from freeze to match an unused seed was judged the larger risk, so **doc 14 was amended** rather than the data. **Checksum scope is bounded deliberately:** the CSVs are byte-stable and are fingerprinted with SHA-256, but `generate_sample_data.py` emits **15 `.xlsx` files** (3 templates + 12 malformed) and `generate_tieout_template.py` a 16th, all written by `openpyxl`, which stamps a wall-clock `dcterms:created` into `docProps/core.xml` — so their hashes change on every run and **any SHA-256 manifest covering them fails by construction**. The harness therefore fingerprints CSVs only and **records the exclusion with its root cause instead of asserting a checksum that cannot hold**. Closing this properly means normalising `dcterms:created` in the generators, tracked as a follow-on. The step-1 requirement to "assert the generator's own checksum" remains unsatisfiable as literally written — no canonical checksum is committed anywhere — so checksums are recorded as a run-to-run fingerprint, not asserted against a constant. **Amended 2026-10-06:** the original XLSX exclusion is superseded: both workbook writers now use `sample-data/xlsx_deterministic.py`, the acceptance scope includes `.csv`, `.xlsx`, and `.json` artifacts with per-path SHA-256 values, and a targeted archive audit normalized the 17 legacy-timestamp workbooks without changing their member payloads. The same-seed generator test exists but was not run in the current sandbox; the official acceptance report remains stale/FAIL, and the missing canonical checksum constant is still an explicit limitation. | `14` §5.2 step 1, `28` §3.7, `app/engine/rules/acceptance.py`, `sample-data/xlsx_deterministic.py`, `evidence/acceptance_report.md` |
| `DEC-056` | 2026-10-05 | **Balance gate scoped by source type (`OQ-025`)** | Journal-style sources (`actuals_d365`, budget) keep the unconditional, exact debit=credit reject (`IMP-023`). Amount-style sub-ledger exports (`bank_ledger`, `payroll_procurement` per `04` §2.2) are one-sided by nature and are validated instead by **control totals / net-amount reconciliation with the ₹500 tolerance of `06` §8**; within tolerance the file loads and the variance is stated in the report, beyond tolerance it fails with the recorded-acceptance path. This harmonises `04` §12 with the catalog's own P1 sample case (a bank file unbalanced by ₹350 must be loadable) and makes P1/P9 reachable. Alternatives rejected: unconditional for all sources (contradicts `06` §8 by construction); unconditional + balanced fixtures only (re-homes documented plantings without fixing the spec contradiction). Money-semantics caveat carried: any non-zero tolerance must be stated in every report (already required by `04` §12) | `04` §11/§12, `06` §8, `14` §5.2, `app/engine/store/import_repo.py`, sample fixtures |
| `DEC-057` | 2026-10-05 | **The catalog `06` wins subject keys (`OQ-026`)** | Where `sample-data/expected_exceptions.csv` and `06` §4 disagree on a rule's subject key or scope, **`06` is authoritative** and the answer key is re-keyed to it — under strict spec-first order (this decision → `06` sample-case/key clarifications where a format is under-specified → fixture regeneration), per Addon 1 §M.5: expectations may change only when the spec changed first and is recorded. Covers P6 (scope: `entity_account`), P8 (key includes cost centre; the plant must satisfy the documented ₹500,000 floor), P20/P21/P24 (key formats), and the batch-numbered keys via `DEC-058`'s fixture. Alternative rejected: answer key wins (a test fixture may never govern rule logic — violates the `00` §5 source-of-truth matrix) | `06` §4/§7, `14` §5.1/§5.2, `sample-data/expected_exceptions.csv` (regenerated, not hand-edited) |
| `DEC-058` | 2026-10-05 | **Build the import-history fixture (`OQ-027`)** | The corpus gains history files — an earlier overlapping export for P2 ("re-export overlaps batch 37"), a control-totals-supplied GL batch for P3, and the batch files `040`/`041` — plus an **ordered-import step in the harness** (amended into `14` §5.2 step 2). Documented batch keys are unchanged. Rationale: `EXC-002`/`EXC-003` are cross-batch rules and cannot fire for *anyone* without an earlier committed batch, so the fixture is feature coverage, not test accommodation. The `18` row assigns fixture-building to the consultant (no key change ⇒ no owner dependency). Alternative rejected: re-key to runtime batch ids (leaves cross-batch semantics untested) | `14` §5.2, `03` §6, `04` §14, `sample-data/`, `app/engine/rules/acceptance.py` |
| `DEC-059` | 2026-10-05 | **`PROP-001` coherent corpus rebuild approved (bundled)** | The owner approved the coherent rebuild: actuals and budget are drawn from **one** coherent model instead of two independent random draws, in a single regeneration that also carries `DEC-056`/`057`/`058`'s fixture changes. Evidence for approval: 370 of today's 422 extras trace to corpus incoherence (`evidence/acceptance_remediation_2026-10-04.md`), making it the largest single extras lever; determinism (sha-stable CSVs) and `verify_trial_balance` are re-proven after regeneration (both already demonstrated 2026-10-05). Deferred alternative: the structural corpus model named as still-open in the proposal | `18_PROPOSAL_FOR_GENERATOR_REBUILD.md`, `sample-data/generate_sample_data.py`, `14` §5.2, `33` `TB-006` |
| `DEC-060` | 2026-10-05 | **Addon 6 assigned — reuse-first build; provenance registry takes `32`** | Addon 6 (`project prompt/ADDON_6_REUSE.md`, SHA-256 `f21c6bb86a5ab0f4deafc675a97659e6f5cdc20bbf58b83620c8888409387f9e`) is contract as of 2026-10-05: reuse before build, license gate, staging, provenance records, surgical-edit checklist. Its §8.4 mandates this DEC entry with the file hash. Addon 6 allocates `docs/32_REUSE_AND_PROVENANCE.md`; the execution taskboard created earlier the same day was renumbered **`32` → `33`** (a derived view yields to a contract-designated path; no contract doc changed). Scaffolding created same session: `THIRD_PARTY_NOTICES.md`, `vendor/_upstream/` in `.gitignore`, `README.md` §2 truthfulness correction | `00` §3/§5/§8, `09` (ADR-011 onward), `32`, `33`, `README.md`, `.gitignore` |
| `DEC-061` | 2026-10-05 | **Adopt WS-02 as `ADP-001` — template-fill engine (`WC-2`, `ADR-011`)** | Addon 6 §9 pre-approves WC-2 to close `DEF-018` (S1): `ppt_pack.py` builds every slide from scratch (`Presentation()` + `slide_layouts[6]`), violating `12` §3.6. Catalog WS-02 covers the capability, so §1's decision tree mandates REUSE. License gate **PASS** (Apache-2.0: `LICENSE` + `pyproject.toml`); upstream pinned `dc448cb1203443e503a558846dc1ce4c4b7ada3d`; take-list 8 files / 739 lines (package minus CLI); E9 audit clean — upstream deps (`python-pptx`, `pandas`, `openpyxl`) are all `ADR-001`-approved, **no new dependency, no R9**. Records written before any code edit per R5: `ADP-001` row (`32` §1), `ADR-011` (`09` §3.12), Apache text in `THIRD_PARTY_NOTICES.md`. R12 interface: the six from-scratch builders are replaced behind `build_ppt_pack`, not paralleled | `DEF-018`, `12` §3.6, `32` `ADP-001`, `09` `ADR-011`, `28` §3.2 |
| `DEC-062` | 2026-10-05 | **Addon 6 v2 assigned — supersedes v1; §11 machine license gate created and passing** | The owner replaced the v1 contract with **v2** at the same path (`project prompt/ADDON_6_REUSE.md`, SHA-256 `81f5aaee2461851f125e68c0bc7731de5fcf576e814f0beae1e0abfd6ee801d3`), which supersedes v1's hash from `DEC-060` (the v1 bytes remain in commit `cca75f6`). Deltas executed the same session: catalog adds COPY-EDIT for WS-03/WS-10 (+WS-05 optional), dev-only tools DT-01…03, golden-without-license WS-11/WS-12 (L2), `fschaeck/python-pptx-text-replacer` (GPL-3.0) into WS-X; two license gates (4A source / 4B dependency); rails L1–L3; checklist item E13; cards WC-6/WC-5; and the mandatory **`scripts/license_gate.py` (§11) wired as `scripts/check.py`'s final step — created, run, PASSING exit 0 on the current tree** (all five checks). Two Tier-B interpretations logged with the gate per §0.4: (a) CHECK 2's refusal-citation exception applies **by role** to `packaging/THIRD_PARTY_LICENSES.txt` (the Addon 1 §I payload notices file) as well as `THIRD_PARTY_NOTICES.md` — the literal exception named only a file outside the scan set, so as written it could never fire; (b) CHECK 4 classifies runtime licenses from expression + classifiers + full `License` text, because `polars` ships its entire MIT text in the `License` field (detection fix; the GO list itself is unchanged) | `project prompt/ADDON_6_REUSE.md`, `scripts/license_gate.py`, `scripts/check.py`, `00` §8, `32`, `15` |
| `DEC-063` | 2026-10-05 | **Adopt WS-10 as `ADP-002` — fill patterns for chart/table/text (`WC-2`, `ADR-012`)** | `WC-2`'s Done-When needs “WS-10 patterns for chart/table fills”: `ppt_pack.py` must push series into native charts (`chart.replace_data`), fill table cells and resolve placeholder text **by shape name** (`12` §3.6) — capability-level code once tests and adapters are counted, so Addon 6 §1's decision tree routes it to catalog `WS-10` (COPY-EDIT). License gate **4A PASS**: `keithmcnulty/ppt-generation`, `LICENSE` = “Creative Commons Legal Code / CC0 1.0 Universal”, on §4's GO list; CC0 needs no attribution, but the catalog says attribute anyway, so `THIRD_PARTY_NOTICES.md` carries the notice. One upstream file `edit_pres.py` (77 lines), pinned `062c4920da96c98574bad0c6cdfd4d10eaa21e02`, becomes `app/engine/pptx_fill/patterns.py`. E3/E9: the demo's pandas selection (`.squeeze()`, column indexing) and hardcoded slide indices are stripped — pandas is not an `ADR-001` dependency, so **no R9** — and `E13` is satisfied by new spec-derived tests (`tests/unit/test_pptx_fill_patterns.py`), since upstream ships none. The load-bearing divergence: upstream's `chart_title.text_frame.text = …` and `table.cell(i,j).text = …` assignments **rebuild the run and drop its `rPr`**, silently discarding the font size, weight, colour and typeface the template author set; the landed `set_text`/`set_cell_text` write into the existing run, pinned by `test_set_text_preserves_template_run_formatting`. **Recorded late (2026-10-05, WC-1 session):** this row was cited by `09` §3.13 (`ADR-012`), `STATE.md` and the `DEF-018` closure report, but the WC-2 append wrote the `DEC-064` row twice instead of appending this one; reconstructed from `ADR-012`, no decision changed | `12` §3.6, `32` `ADP-002`, `09` `ADR-012`/§3.13, `THIRD_PARTY_NOTICES.md`, `DEF-018` |
| `DEC-064` | 2026-10-05 | **WS-03 E12 escalation — amended take-list ruled Tier B; adopt the overflow cascade as `ADP-003`, flag-gated (`WC-2`, `ADR-013`)** | §10 six-field intake for the amended take-list: **(1) URL + capability** — `github.com/Whatsonyourmind/deckforge`, the font-shrink → reflow → slide-split overflow cascade, serving `12` §3.4's no-overlap guarantee and WC-2's “WS-03 overflow logic behind a flag”; **(2) license evidence** — `LICENSE` = “MIT License, Copyright (c) 2026 Luka Stanisljevic”, gate 4A **GO**; **(3) amended take-list** — `src/deckforge/layout/overflow.py` only (the catalog's “overflow handler, ≤4 files”), because post-clone E12 showed the handler coupled to `kiwisolver` (solver/types), `PIL` (text measurer) and deckforge's pydantic IR/themes — **none** in pyproject (E9), and whole-package copy would breach R13, so the original take-list proved wrong after cloning (§6 STOP → this entry); **(4) mode** — COPY-EDIT unchanged, cascade re-expressed against python-pptx shapes + our `ppt_fit` maths, no exotic imports land; **(5) risks** — R12 adjacency with `exports/ppt_fit.py` (mitigated: `§3.4` trim stays the canonical always-on path; cascade lands **default OFF** until a doc-12 amendment, per WC-2), no network, our IDs only; **(6) tier asked** — **Tier B**, which §10 grants same-session: license GO + 1 module (≤2) + no spec change + no API change. Pinned `ae71696f763f85b79f7f94d85484234f57f93f63`. Records before edit: `ADP-003` (`32` §1), `ADR-013` (`09` §3.14), MIT notice (`THIRD_PARTY_NOTICES.md`). Upstream `tests/unit/test_layout_adaptive.py` to be adapted (E13/R6) | `12` §3.4, `32` `ADP-003`, `09` `ADR-013`, `WC-2`, Addon 6 §10 |
| `DEC-065` | 2026-10-05 | **`12` §4.1 `PPT-004_table` row count — read “7 rows × 0.60″” as a typo for 6 (frame arithmetic + the never-blank-rows rule decide it)** | The §4.1 row declares a 3.60″ frame and “7 rows × 0.60″” in the same cell: 7 × 0.60 = 4.20″, which does not fit a 3.60″ frame, so the two halves of the cell contradict each other and the row count cannot be read off the geometry alone. Two clauses in the same row settle it: (a) “Rows = top 5 by ‖variance‖; **fewer rows only when fewer lines exist (never blank rows)**” caps the body at 5 data rows, giving 6 rows total; (b) 6 × 0.60 = 3.60″ matches the declared frame exactly. The sibling `PPT-005_table` row already reads “6 rows × 0.54″ (= 3.24″, consistent)”, so the `004` cell is the outlier. Per **R1** the spec is *interpreted*, never edited to fit code: the template generator, the shape contract and the tests all read **6**, and the contradiction is recorded here rather than silently resolved. `DEF-018` (S1) forced the question because filling a 7-row template with 6 rows of data would leave a blank row — exactly what §4.1 forbids | `12` §4.1, `DEF-018`, `TB-033`, `32` `ADP-001` |
| `DEC-066` | 2026-10-05 | **`WC-1` closed as BUILD (`BD-001`) — the pre-approved catalog source `WS-01` no longer exists, so the capability is extracted as our own code (`OQ-028`, `ADR-014`)** | Addon 6 §9 pre-approved `WC-1` as COPY-EDIT of catalog `WS-01` (`github.com/ricothanfx/invoice-dedupe`, MIT). Measured 2026-10-05: `git clone --depth 1 … vendor/_upstream/WS-01` → `remote: Repository not found.` / `fatal: repository … not found`, **git exit 128** (captured twice, exit preserved) — so §6 S2 cannot complete, no pinned SHA can be cited and the §5 R5 pre-edit record cannot exist. §6 S4 plus §14 **Tier C STOP** was raised with the owner (`evidence/wc1/ws01-escalation-packet.md`, three options, recommended default) and the owner chose **option 1: BUILD + `BD-` row**. `BD-001` (`32` §2) records the search so the question is answered once: the dead catalog URL plus the three successors found — `dedupeio/dedupe` (MIT, but a heavyweight ML stack: `numpy`/`scipy`/`affinegap`/`categorical` → R9 + R13, and it solves the fuzzy problem the spec deliberately does not have), `pimverschuuren/Deduplication` and `pmessan/duplicate_invoice_finder` (licences unverified → L2 default) — none fits. **No code was adopted, so no licence obligation and no `ADP-004`.** The `S0` aggravating finding is why BUILD is the correct outcome rather than a consolation: `06`'s duplicate rules are all Tier **`exact`** and `WS-01`'s headline weighted/fuzzy scorer is required by **no** `06` rule (the eight `fuzzy`-tier rules are magnitude/pairing/completeness/budget/controls rules), so wiring it into `EXC-007`/`EXC-008` would move them off `exact` and breach **R1**; `06` keeps duplicates exact on purpose (`EXC-007` mitigation: partial-amount duplicates are “deliberately out of scope for v1 to keep precision high”). The one real gap — the `EXC-007` normaliser and the two blockers lived inline in two rule modules with no shared interface (an **R12** symptom) — is closed as our own code: `app/engine/dedupe/` (`normalize.py`, `blocking.py`, `__init__.py`), **no `Adapted from` header** (nothing adapted; E8 governs adoptions), with `rules_01_08.evaluate_exc_001` and `rules_catalog_001_008.evaluate_catalog_exc_008` rewired through it and behaviour proven unchanged (acceptance bars measured **identical to baseline**: recall 11/32, control 1 fired P30, High 6/18, 422 extras, the same 14 zero-coverage rules — all pre-existing `14` §5.3 items under `TB-020`, none caused by this change). `normalise_invoice_no` is now the single implementation (`_normalize_invoice_no` is an alias, not a copy), and the `06` clause's limit (leading zeros collapse only at the start of the alphanumeric string, so `INV-00088213` does **not** block with `INV-88213`) is documented in the module rather than silently widened — widening it changes which rows `EXC-007` raises on, an `R1` spec question. Follow-on recorded as `TB-100` (`33` §5.8); the contract file `project prompt/ADDON_6_REUSE.md` is deliberately left byte-identical (SHA-256 still `81f5aaee…01d3`) so its recorded identity holds — the dead URL is flagged in `32` `BD-001`, not by mutating the hashed contract | Addon 6 §3/§6/§9/§14, `06` EXC-007/EXC-008, `32` `BD-001`, `33` `TB-100`, `OQ-028`, `evidence/wc1/ws01-escalation-packet.md`, `tests/unit/test_dedupe.py` |
| `DEC-067` | 2026-10-06 | **Prohibit Trial-Balance Plug to Account 1999 / Suspense — Double-Entry Generator Rebuild Mandatory** | Auditing of all 24 exception detection rules (`evidence/rule_audit_1999.md`) confirms `EXC-024` directly monitors Account 1999 for suspense/clearing residuals (planted P24 `VCH-2026-0930-040`, ₹1,240,000 debit). Inserting a single ₹17.9B balancing credit into Account 1999 would trigger a massive false-positive finding under `evaluate_exc_024` (amount at risk ₹17,944,515,579.33), masking genuine operational exceptions and corrupting the clean 100% recall / 0 extras baseline. Per `03` §5.2, chart-of-accounts suspense is not a balancing plug. The sample data generator must balance debits and credits via legitimate double-entry transactions in sample actuals (`d365_gl_actuals.csv`) | `03` §5.2, `06` EXC-024, `14` §5.2, `sample-data/generate_sample_data.py`, `evidence/rule_audit_1999.md`, `33` `TB-006` |

*New decisions are appended as Phase 0 continues; the table above grows, it never gets rewritten. D-12 (2026-10-03): `DEC-055` moved to the tail (after `DEC-053`) to restore append order; no `DEC-` ID was renumbered and all existing references still resolve.* *D-13 (2026-10-05, WC-1 session): register integrity repaired — `DEC-063` (WS-10 `ADP-002`; cited by `09` §3.13 `ADR-012`, `STATE.md` and the `DEF-018` closure report, but never appended) reconstructed from that ADR and placed in ID order, and the duplicated trailing `DEC-064` row removed. No decision changed; `DEC-` IDs are never reused or renumbered.* *D-14 (2026-10-06, Phase 0 remediation wave): DEC-067 appended per rule audit deliverable; trial-balance plug to Account 1999 prohibited, full double-entry generator rebuild mandated.*

	### 5.4 Pending Decisions & Awaiting-Owner Tracker

	Per doc 18 register rules (§1.3, §6), awaiting-owner items and pending policy decisions are tracked centrally below with date raised, options, recommendation, and impact of delay. Approvals recorded under authority 'owner auto-decide' on 2026-10-03 (with PEND-01 held pending scope delivery):

	| ID | Awaiting Decision / Topic | Date Raised | Options | Recommendation | Impact of Delay | Owner | Status / Resolution |
	|---|---|---|---|---|---|---|---|
	| `PEND-01` | **Real-data pilot inputs** (`OQ-014`, `A29`, `DEC-REQ-07`) | 2026-10-01 | A) Wait for client D365 GL export; B) Use generated sample data fallback | Fallback to sanitized sample data with written limitation note (`RISK-002`) | High (blocks GATE-13 pilot sign-off) | Client | **APPROVED** (2026-10-03, scope check passed on all 4 criteria; fallback pilot activated and executed per DEC-053) |
	| `PEND-02` | **Code-signing certificate acquisition** (`OQ-012`, `ADR-003`, `DEC-REQ-04`) | 2026-10-01 | A) Purchase paid OV/EV cert; B) Use unsigned executable + SmartScreen mitigation ladder | Use unsigned installer with written SmartScreen walkthrough guide (`15` §8.2) | Medium (SmartScreen prompt on first run) | Project owner | **APPROVED** (2026-10-03, owner auto-decide: unsigned pilot) |
	| `PEND-03` | **Client brand logo & palette customization** (`OQ-015`, `A18`, `DEC-REQ-03`) | 2026-10-01 | A) Use default neutral palette & working name; B) Inject client logo & brand colors | Use default neutral palette with hot-reload settings support in Settings screen | Low (purely aesthetic styling) | Client | **APPROVED** (2026-10-03, owner auto-decide: generic branding) |
	| `PEND-04` | **Regen vs manual re-run policy** (`OQ-004`, `A5`, `DEC-REQ-01`) | 2026-10-01 | A) Automatic background re-calculation; B) Stale warning banner + manual "Re-run Now" button | Stale warning banner with explicit manual "Re-run Now" button (`FR-SET-010`) | Low (analyst controls re-run timing) | Project owner | **APPROVED** (2026-10-03, owner auto-decide: regen to restore) |
	| `PEND-05` | **EXC-011 threshold cap / volume** (`RISK-039`, `DEC-REQ-02`) | 2026-10-01 | A) Strict hard financial cap; B) Variance ranking & materiality filtering | Variance ranking & materiality filtering (`CALC-080`) | Low (managed via rule thresholds) | Project owner | **APPROVED** (2026-10-03, owner auto-decide: ranking + pagination) |
	| `PEND-06` | **API contract-drift strictness** (`26` §2, `DEC-REQ-06`) | 2026-10-01 | A) Loose warnings on schema divergence; B) Hard build/test failure on drift | Hard build and test failure gate check (`DEC-043`) | Medium (prevents schema bugs) | Project owner | **APPROVED** (2026-10-03, owner auto-decide: strict drift) |
	| `PEND-07` | **Coverage bars vs feature completeness priority** (`DEC-REQ-05`) | 2026-10-02 | A) Hold at 90% full backend; B) Re-scope to 90% domain engines & 75% store | Re-scope coverage bars for pilot readiness | Medium (unblocks GATE-14) | Project owner | **RATIFIED (SELF-CERTIFIED — PENDING AUDIT)** (2026-10-03, owner ratified: money paths ≥90%, stores ≥75%, check-enforced, goldens untouched; gate reopens on audit failure) |
	| `PEND-08` | **Purge test-origin batches from live DB** (`purge-test-batches`) | 2026-10-02 | A) Retain all batches; B) Purge test-origin batches with snapshot secured | Purge provable test batches while securing full database snapshot | Low (hygiene and storage integrity) | Project owner | **APPROVED** (2026-10-03, owner auto-decide: purge-test-batches) |
	| `PEND-09` | **Trial balance residual remediation method (`d365_gl_actuals.csv`)** | 2026-10-06 | A) Single ₹17.9B balancing plug entry in Account 1999; B) Full double-entry generator rebuild | Full double-entry rebuild (Option B) per rule audit; plug to 1999 corrupts EXC-024 findings | High (blocks doc-04 file-level acceptance gate) | RuleAuditor / Project owner | **DECIDED** (2026-10-06, Option B selected per DEC-067; Option A rejected) |

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
| Decision dates for `DEC-031`…`DEC-037` | All `2026-10-01` (session 001); `DEC-038`…`DEC-044` recorded on `2026-10-02` (current wave); `DEC-045`…`DEC-055` recorded on `2026-10-03` (`DEC-055` appended at tail per D-12; no IDs renumbered); `DEC-056`…`DEC-060` recorded on `2026-10-05` |
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
resolution (§4.4) · the `DEC-001`…`DEC-060` log (§5) · the maintenance cadence and hygiene rules (§6).
