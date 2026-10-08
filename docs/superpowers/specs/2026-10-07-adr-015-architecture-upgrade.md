> **Status:** Accepted · **Date:** 2026-10-07 · **Source:** this session's architecture-upgrade brainstorming (owner + Buffy); embodies the "offline-first spine, governed AI add-on, MNC-later" decision and the recommendation to keep the existing stack sharpened rather than replaced unless measurement forces it.

> **Owning FRs/areas:** architecture upgrade direction; offline-core performance and correctness; governed cloud-AI boundary; MNC-later data-model shape; flawless-result bar.
> **TL;DR (≤ 15 lines):** This ADR decides the architecture-upgrade direction for the project: keep the existing
> stack (Python/FastAPI/DuckDB/Polars/pywebview/React) and sharpen it rather than replace it, unless profiling
> later shows Python is the actual ceiling; treat the deterministic engine as the trusted core and invest the
> performance/correctness budget there first; build the cloud-AI path as a bound, flag-gated, provider-neutral
> adapter designed now with consent/redaction/minimum-data/labelling/audit, implemented behind a default-off
> flag on top of the existing keyless rule-based fallback; shape the data model now for the later MNC phases
> (multi-currency as a real concept, multi-entity/consolidation-ready dimensions, per-project residency
> contract, permissions/auth placeholder) without paying the full MNC cost now; and govern everything by the
> "flawless result" bar — ties-out + cross-artifact equality + no unvalidated AI number + auditability. MNC and
> any language rewrite (Rust) are explicitly later, separately justified decisions. Full design, alternatives
> and consequences are below.

**Design scope (what this ADR owns and does not own):**

This ADR owns the *direction* and the *cross-cutting shape* of the upgrade. It does not restate the existing stack (that is ADR-001), the existing AI policy (that is doc `10` §2), or the existing data model in full (that is doc `03`). It only states the changes to those things and the new cross-cutting concerns. The implementation plan (`docs/superpowers/plans/2026-10-07-architecture-upgrade.md`) is where the tasks live.

**Context.** The product is a single-company, offline-first desktop app whose deterministic engine, exception catalogue, Excel/PPT packs and packaging path are already built and measured. The owner's broader vision is that **one trusted offline core plus a governed cloud-AI add-on should eventually do the repetitive work of an FP&A analyst team and produce what the product calls a *flawless result*** — where "flawless" is defined as: every figure ties out to source, every artefact matches the engine exactly, AI never computes or silently changes a number, and every output is auditable. MNC/multi-country/multi-sector scale is explicitly **later**, not v1.

The upgrade question is not "pick a new language." It is: make the offline core fast and correct enough to be the trusted asset, and make the AI path a clean governed layer that can be added (and later scaled) without compromising that core. Three candidate approaches were examined:

| # | Approach | What it buys | What it costs | Verdict |
|---|---|---|---|---|
| A | Keep Python/FastAPI/DuckDB/Polars/pywebview/React; sharpen the architecture (profile, safe parallelism, finish engine boundary, formalise `engine/common/`, governed AI module, MNC-shaped data model) | Lowest risk to existing spec debt, acceptance harness, packaging story and rule engine; "fast" delivered by DuckDB/Polars/parallelism/profiling; "ready for AI" delivered by a bounded module; simplest single-language core | Python is the ceiling on raw single-thread speed if profiling later shows it is the actual bottleneck | **Recommended for v1** |
| B | Port the deterministic engine into a systems language (Rust) and keep or drop the rest | Real single-thread speed ceiling; stronger type-level guarantees for money paths | Real rewrite of the core: loses existing rule modules, harness, import-linter story, ADR-007 DuckDB/SQLite hand-written-SQL shape unless re-expressed; risks the correctness evidence currently held; "productive like Python" takes a hit during the port | **Only if measurement shows Python is the actual ceiling** |
| C | Offline desktop core (A) + a designed-now service boundary for cloud AI (provider-neutral adapter, consent/redaction/minimisation/labelling/audit), with MNC shape designed into the data model and the AI contract | Most honest match to "offline-first now, cloud AI later, MNC later"; when scaling to MNC you scale a well-shaped contract, not bolt AI onto a desktop app | Up-front design cost for the boundary and the consent/redaction/audit contract; risk of over-building the AI layer before the offline core is proven | **Folded into A, not a separate track** |

**Decision.** Adopt **A** as the v1 architecture direction, with **C's AI-boundary design folded in** as a governed module behind a flag, and **B held as a measurement-triggered contingency**. Concretely:

1. Keep the existing stack (this ADR does not change ADR-001's stack list; it sharpens how it is used).
2. Treat the deterministic engine (imports, calc, rules, forecast, exports) as the **trusted core** and invest the performance/correctness budget there first: profile hot paths under a 250krow load, introduce safe parallelism only where the engine boundary and the one-writer-per-store rule (ADR-006) make it safe, and finish the headless-engine boundary enforcement (`TB-014`/`TB-025`/`TB-026`) so "AI changed a number" stays structurally impossible.
3. Build the cloud-AI path as a **bound, flag-gated, provider-neutral adapter** with consent, redaction, minimum-data, labelling and a local audit log **designed now**, implemented behind a default-off flag and the existing keyless rule-based fallback (doc `10` §11). AI still never computes, decides, applies or sends (doc `10` §2.3). No change to that policy; this ADR only governs the *architecture* around it.
4. Shape the data model **now** for the later MNC phases as first-class concerns that cost nothing controversial in v1: multi-currency as a real concept (not just display), multi-entity/consolidation-ready dimensions, a per-project storage-isolation/residency contract, and a permissions/auth placeholder boundary. Implement v1 scope only where it strengthens the offline core or the AI contract.
5. Use "flawless result" as the governing outcome: ties-out + cross-artifact equality + no unvalidated AI number + auditability. Measure, don't assert.

**Alternatives considered.** B alone (rejected for v1: it trades the existing correctness evidence and packaging story for an abstract speed ceiling, before any measurement says the ceiling is real). C alone as a separate service track (rejected: it splits focus and risks over-building the AI layer before the offline core is proven; the governed-AI design is worth doing, but as a module inside the desktop core with a clean boundary, not as a parallel service project in v1). A without C's boundary design (rejected: the vision includes cloud AI and you want it governed from the start; a bolt-on later would compromise the "flawless" bar).

**Consequences.** Positive: v1 stays a stronger offline app with the least risk to correctness/traceability/packaging; the AI path is designed as a clean boundary so later scaling touches a contract, not a retrofit; MNC shape is designed without paying the full MNC implementation cost now; "simpler than all three" is preserved because the core stays one language and the changes are structural, not a rewrite. Negative/owed: the performance gains are measurement-dependent (profile first; parallelism only where safe); the AI-boundary design adds design cost up front; B remains available but is a later, separately-justified decision, not part of this upgrade.

**Reversibility.** A is cheap to revert in pieces (the AI module is flag-gated; the boundary enforcement is config; the MNC-shaped fields are additive). B, if ever chosen, is costly (core rewrite) and would be its own ADR superseding portions of this one.

**Affected docs.** `01` (PRD scope/consequences), `03` (data dictionary — multi-currency/entity/residency/permissions shape), `09` (this ADR index + §4/§6/§7/§14), `10` (AI path: the governed boundary, consent/redaction/labelling/audit — no policy change, architectural hardening), `16` (roadmap: upgrade work as a first-class block, MNC-later phasing), `26` (API contract: AI endpoint boundary + MNC-shaped contract), `29` (client pack: the "trusted core + governed AI" story and the later-scaling statement), `33` (execution blueprint + taskboard for the upgrade).
