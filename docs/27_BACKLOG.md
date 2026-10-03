> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **single backlog register** — every parked item with a one-line scope, the trigger
> that promotes it, a rough size, its source and a target phase; reviewed at every phase gate with the
> decision register (`18`) and the risk register (`25`) (Addon 3 §B.1/§H, Addon 1 §N)
> **TL;DR (≤ 15 lines):**
> - **Controlled scope reserve:** 34 explicitly parked backlog items (BL-001 to BL-034) with acceptance criteria and triggers.
> - **Zero accidental bloat:** Prevents opportunistic feature creep; new ideas logged to backlog rather than added mid-phase.
> - **Promotion gates:** Items promoted to active roadmap only with explicit project owner approval and impact analysis.
> - **Contract alignment:** Encompasses all deferrals from Kickoff and Addons 1–4 (multi-currency, cloud sync, direct ERP APIs).
> - **Regular pruning:** Backlog review ritual conducted at each phase gate to reassess priorities against client feedback.

# 27 — Backlog

## 1. Purpose, rules and the entry schema

### 1.1 What belongs here

| Belongs | Does not belong |
|---|---|
| A scope item consciously parked with a reason | Work in the current phase (that is `02` + `16`) |
| A deferred refinement of a shipped behaviour | A defect (that is `14`/`28` defect flow) |
| A client ask that cannot be answered "no" forever | A risk (that is `25`) — a park with a downside links there |
| A technical improvement with a named trigger | An implementation idea with no trigger and no size |
| A park created by a decision (`DEC-`) or an open question (`Q-`/`OQ-`) | A question still awaiting a client answer (that is `21`/`18`) |

### 1.2 The entry schema (Addon 3 §H, verbatim shape)

| Field | Rule |
|---|---|
| `BL-nnn` | Allocated here, stable forever, never reused (`00_INDEX` §8) |
| Item | A name a client could read without translation |
| One-line scope | What it would do, one line, no design |
| Trigger | The observable event that promotes it — a client answer, a phase boundary, a measured miss, an IT mandate |
| Size | `S` (≤ one session of work) · `M` (a slice of a phase) · `L` (its own phase) |
| Source | Where it was raised: a document section, a decision, a question, an addon section |
| Target phase | `Phase 6 candidate`, `Post-v1`, `On trigger`, or `Not planned` (with the reopen condition) |

### 1.3 The three rules

1. **Nothing lives in chat.** A deferral is registered the session it appears (Addon 3 §H).
2. **A park with a downside links a risk row** — consequences live in `25`, not in a parenthesis here.
3. **Promotion is a decision, not a mood**: the trigger fires → the gate records the promotion → the item
   becomes an FR (`02`), a decision (`18`) or a phase-plan change (`16`), and the register entry is updated
   with the pointer (never deleted).

## 2. The register (34 items)

| ID | Item | One-line scope | Trigger that promotes it | Size | Source | Target phase |
|---|---|---|---|---|---|---|
| `BL-001` | Write-back / posting to D365 or any ERP | Post approved journals back to the ledger | A signed phase-2 scope with D365 write credentials and a posting-approval design | L | `01` §6.2 | Post-v1 (statement of work) |
| `BL-002` | Replacing the ERP / ledger-of-record functions | Keep books, close the ledger, produce statutory statements | Only if the product changes category (a new ADR, not a feature) | L | `01` §6.2 | Not planned (recorded non-goal) |
| `BL-003` | Journal approval workflows | Route reclass journals for approval inside the tool | The client's close process requires in-tool approvals before posting | M | `01` §6.2 | Post-v1 |
| `BL-004` | Multi-user, cloud, collaboration, RBAC | Shared projects, roles and concurrent editing | Two people need the same project at once more than once (`RISK-035`), or a server deployment is agreed | L | `01` §6.2 | Post-v1 |
| `BL-005` | In-app login / authentication | Accounts, sessions, per-user permissions | Same trigger as `BL-004`; today the OS account is the privacy boundary (`DEC-010`) | M | `01` §6.2 | Post-v1 |
| `BL-006` | Mobile / web-hosted UI | Access the analysis outside the one desktop | The client requires access away from the project PC | L | `01` §6.2 | Not planned |
| `BL-007` | Auto-update framework | Silent/assisted updates across machines | More than a handful of installed machines, or the delivery channel forces staged updates | M | `01` §6.2 | Phase 6 candidate |
| `BL-008` | Direct D365 / API connectors | Pull data without manual exports | The client grants API access and manual exports become the bottleneck | L | `01` §6.2 | Phase 6 candidate |
| `BL-009` | Auto-generated Power BI files / `.pbip` | Author Power BI artefacts from the model | A client standard mandates `.pbip`; the documented star-schema CSV export is the intermediate step | M | `01` §6.2 | Phase 6 candidate |
| `BL-010` | Balance sheet & cash-flow statements | Extend beyond the P&L focus | The client's close scope formally extends beyond P&L (a cut-line decision) | L | `01` §6.2 | Post-v1 |
| `BL-011` | Price / volume / mix revenue decomposition | Decompose revenue variance into drivers | A CFO-level request for margin analysis appears in the month-end pack requirements | M | `01` §6.2 | Post-v1 |
| `BL-012` | Purchase-commitment / PO data | Include commitments in the variance story | The client adds commitment data to the monthly source set | M | `01` §6.2 | Post-v1 |
| `BL-013` | Cost allocation / recharging | Allocate shared costs across entities/CCs | The client defines allocation rules (they do not exist today) | L | `01` §6.2 | Post-v1 |
| `BL-014` | Automated cross-system tie-out | Machine-verified ties across the three systems | Tie-out volume outgrows manual control totals (`06` §2.7's v1 default) | M | `01` §6.2 | Phase 6 candidate |
| `BL-015` | In-app budget authoring | Create/edit budgets in the tool | The client stops maintaining budgets in Excel and asks for authoring | L | `01` §6.2 | Post-v1 |
| `BL-016` | Headcount / FTE metrics (incl. cost per head) | Headcount KPI and cost-per-head analysis | The `Q-021` answer is yes, or a later phase funds the headcount schema | M | `01` §6.2, `Q-021`, `RISK-024` | Phase 6 candidate |
| `BL-017` | Intercompany eliminations & consolidation netting | Eliminate and net across entities | A consolidation requirement appears (today v1 shows per-entity + simple grouped totals) | L | `01` §6.2 | Post-v1 |
| `BL-018` | Advanced forecast methods (seasonality, driver-based) | Statistical and driver-based forecasting | Accuracy reports show the deterministic methods are insufficient (`RISK-025`) | M | `01` §6.2, `07` | Phase 6 candidate |
| `BL-019` | Email / Teams distribution of packs | Send packs from inside the tool | The client asks the tool to distribute packs (`RISK-036`); issued packs are otherwise delivered by the user | M | `01` §6.2, `OQ-011` | Post-v1 |
| `BL-020` | Budget version-compare view | Side-by-side comparison of two budget versions | A second budget version exists in a real project month | S | `01` §6.2 | Phase 6 candidate (small win) |
| `BL-021` | Commentary carry-forward between periods | Seed this month's narrative from last month's | Clients report rewriting the same narrative every month | S | `01` §6.2 | Phase 6 candidate (small win) |
| `BL-022` | Localisation beyond English | Additional UI/output languages | A non-English user joins the rollout | L | `01` §6.2 | Post-v1 |
| `BL-023` | Multi-client licence management | Multiple clients, builds and licences | A second client engagement is signed | L | `01` §6.2 | Post-v1 |
| `BL-024` | One-off / exceptional item tagging | Tag actual lines as one-off; adjusted views | After the first real month-end the client asks for adjusted views (parked by `DEC-006`) | M | `01` §6.2, `DEC-006` | Phase 6 candidate (revisit post-pilot) |
| `BL-025` | Partial-amount duplicate detection | Catch split/staged duplicate payments | A real duplicate miss involves a partial amount in a live month | M | `01` §6.2 | Phase 6 candidate |
| `BL-026` | Charts inside the Excel pack | Charts in the workbook rather than tables only | The client asks for charts in the workbook at UAT or after (`RISK-027`) | M | `11` §14 (`XL-CHART-DEFER`) | Phase 6 candidate |
| `BL-029` | Corporate proxy / custom CA support for AI calls | Trust a corporate TLS-inspecting proxy | Client IT mandates TLS interception support (today it fails closed with `ERR-SEC-004`) | M | `13` §15 | On trigger |
| `BL-030` | "Secure erase" of a project | Attested deletion of project data | A client policy demands attested erasure (BitLocker is the recommended control today) | M | `13` §15 | On trigger |
| `BL-031` | Password-protected (encrypted) project backups | Encrypt backup zips | Client IT requires encrypted backups (the plain-zip warning is documented today) | M | `13` §15 | On trigger |
| `BL-032` | Data-retention automation | Auto-archive/purge after N years | A client retention policy requires automatic action (today retention is user-owned) | M | `13` §15 | On trigger |
| `BL-033` | Windows Hello / TPM-bound key unlock | Bind the AI key to the device/user | Client IT mandates hardware-bound unlock | S | `13` §15 | On trigger (small win) |
| `BL-034` | AI endpoint allow-list | Restrict AI calls to specific hosts | Multi-provider support lands (the endpoint is already a single configured value) | S | `13` §15 | On trigger (small win) |
| `BL-035` | In-app authentication, RBAC, multi-user | Server-dependent accounts and roles | The product gains a shared/server mode (explicitly out today, `DEC-010`; duplicates `BL-004`/`BL-005` intent) | L | `13` §15 | Post-v1 (with `BL-004`) |
| `BL-036` | In-app PDF export of dashboards and packs | Render the dashboard views and a pack summary as a PDF without Office | A client workflow needs PDFs without Excel (or print/PDF readiness proves insufficient in practice, superseding `DEC-028`) | M | Addon 1 §N | Post-v1 |
| `BL-037` | Gradual refactor of existing UI payload DTOs | Migrate legacy inline component DTOs to import directly from `ui/src/api/types.ts` | Refactor sprint or strict contract-enforcement gate | S | `26`, `17` | Phase 6 candidate / On trigger |
| `BL-038` | Live-DB root-cause isolation hardening | Dedicated session tripwire & process sandboxing preventing background dev scripts from writing to default user DB | Post-pilot root cause investigation into batch-340 writer anomaly (`DEC-052`) | S | `14`, `17` | Phase 6 candidate / Post-pilot |
| `BL-039` | Rejected-batch audit history manual pruning | Admin-initiated purge of rejected import batch metadata and validation checks older than N days with explicit audit logging | Admin/compliance demand for history cleanup or project storage optimization | S | `04` §11/§15, Task `#01a100d6` | Phase 6 candidate / On trigger |

### 2.1 Counts at first issue

| View | Counts |
|---|---|
| By size | S 7 · M 18 · L 12 |
| By target | Not planned 2 · On trigger 6 · Phase 6 candidate 14 · Post-v1 15 |
| Registered | 37 (`BL-001`…`BL-026`, `BL-029`…`BL-039`); `BL-027`/`BL-028` unallocated |

## 3. Views

### 3.1 Small wins (S) that could ride a phase slice

| ID | Item | Why it is small | Suggested home |
|---|---|---|---|
| `BL-020` | Budget version-compare view | A read-only second version column over an existing query | Phase 6, or earlier if a second budget version lands |
| `BL-021` | Commentary carry-forward | Copy last period's text as a draft seed with a version note | Phase 6 |
| `BL-033` | Windows Hello / TPM unlock | DPAPI already wraps the key; an unlock prompt is the variable | On trigger (client IT mandate) |
| `BL-034` | AI endpoint allow-list | The endpoint is already a single configured value | On trigger (multi-provider) |
| `BL-039` | Rejected-batch audit prune | Simple parameterized SQL delete on rejected status + date cutoff with audit event write | Phase 6 candidate / Settings maintenance slice |

### 3.2 By source of the park

| Source | Items |
|---|---|
| `01` §6.2 (explicitly out of scope for v1) | `BL-001`…`BL-025` |
| `11` §14 (`XL-CHART-DEFER`) | `BL-026` |
| `13` §15 (security/privacy parks with triggers) | `BL-029`…`BL-035` |
| Addon 1 §N (the list `01` §6.2 mirrors) — the one item with no `01` twin | `BL-036` |
| Client questions that can promote an item | `Q-021` → `BL-016`; `OQ-011` → `BL-019`; `OQ-014` → the pilot gate, not a backlog item |

### 3.3 Trigger families

| Family | Trigger shape | Items |
|---|---|---|
| Client answer | A `Q-`/`OQ-` answer or a stated workflow need that changes scope | `BL-016`, `BL-019`, `BL-036` |
| Roadmap phase | A funding decision at a gate (Phase 6 candidate) | `BL-007`…`BL-009`, `BL-014`, `BL-018`, `BL-020`, `BL-021`, `BL-024`…`BL-026` |
| Measured miss | A real month shows the v1 behaviour is insufficient | `BL-018` (accuracy), `BL-025` (duplicate miss) |
| Client IT mandate | A policy requirement lands | `BL-029`…`BL-035` |
| Scale/engagement change | A second client, more machines, a server | `BL-002`…`BL-006`, `BL-022`, `BL-023` |

## 4. Promotion, review and change control

### 4.1 The gate ritual (every gate, `16` §5.1)

1. **Read the triggers aloud**: which fired since the last gate?
2. **Promote** what the evidence supports: FR added (`02`), decision recorded (`18`), phase plan updated (`16`).
3. **Re-size** any item whose trigger is close (a rough size that stays wrong for three gates is a bad entry).
4. **Add** new parks created during the phase (including anything deferred in review).
5. **Record** the review in the gate packet (`16` §5.1) and in `SESSION_LOG`.

### 4.2 Promotion and retirement

| Event | Register action |
|---|---|
| Promoted | Set target to the phase and add the FR/ADR pointer; the row stays for history |
| Implemented | Mark `Implemented <version>` with the FR and the release (`24`) |
| Rejected by the client or the owner | Mark `Declined <date> — <reason>`; the id is never reused |
| Superseded | Point to the item that replaced it and close with one line |
| Unallocated (`BL-027`, `BL-028`) | Reserved; not shown as rows because they were never raised |

### 4.3 What the backlog is not

| Not | Because |
|---|---|
| A wish list | Every row has a trigger and a size |
| A second roadmap | `16` owns phases; this register feeds it |
| A risk register | `25` owns consequences and owners |
| A defect list | `28` owns defect severity and workflow |

## 5. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `01` | §6.2 keeps the product-level park list; this register is the operational detail |
| `02` | A promoted item becomes an FR before any code (spec-first) |
| `16` | Phase gates read this register; a phase plan change points at the `BL-` rows it consumes |
| `18` | A park created by a decision links the `DEC-` row; a promotion records a new decision |
| `19` | The change protocol requires a `BL-` row for any deferral made in review |
| `25` | A park with a downside carries a `RISK-` row and vice versa |
| `28` | Post-go-live feedback that becomes a park lands here through the intake rule (`19` §5.4) |
| `24` | A promoted item that ships is named in the release notes |

## 6. Change control and frozen constants

| Constant | Value |
|---|---|
| ID format | `BL-nnn`, allocated here, never reused (`00_INDEX` §8) |
| Registered at first issue | 34 rows (`BL-001`…`BL-026`, `BL-029`…`BL-036`) |
| Unallocated | `BL-027`, `BL-028` (reserved) |
| Sizes | `S` ≤ one session · `M` a phase slice · `L` its own phase |
| Target phases | `Phase 6 candidate` · `Post-v1` · `On trigger` · `Not planned` |
| Review | Every phase gate, recorded in the gate packet |
| Promotion rule | Trigger → decision → FR/phase change; the row stays |
| Sources | `01` §6.2, `11` §14, `13` §15, Addon 1 §N, decisions, questions, review deferrals |
