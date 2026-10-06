# Prior-Art Review #1: `github.com/Warzonesiddiki/fpa`

> **Reviewer:** `hermes` (Analyst's Advocate)  
> **Task Reference:** `PA-01` (P2)  
> **Target Evidence Path:** `evidence/prior-art/prior-art-1.md`  
> **Target Review Path (for Handoff):** `team/reviews/prior-art-1.md`  
> **Date:** 2026-10-05  

---

## 1. License Gate 4A Verification

| Field | Detail |
|---|---|
| **Upstream Repository** | `https://github.com/Warzonesiddiki/fpa` |
| **Pinned SHA** | `6f6f72f5b681573414c6da74bce7dc538c79e565` (depth-1 HEAD, fetched 2026-10-05) |
| **License** | **MIT License — PASS (Gate 4A)** |
| **Copyright Holder** | Copyright (c) 2026 Warzonesiddiki |
| **License Status** | MIT is on the §4 GO list (`32` §3). Code patterns and requirements may be evaluated and adopted under strict `ADP-nnn` registration. |

---

## 2. Architectural Analysis & Overview

The repository represents an earlier attempt at a local-first FP&A desktop application using **Tauri 2 + Rust + React 19/TypeScript** with **SQLite in Rust** as the data store.

### Core Stack & Modules
* **Tauri 2 & Rust Core:** Rust backend handled database schema (`SQLite`), exact money types (`rust_decimal`), formula evaluation, and audit logging.
* **React 19 / TypeScript UI:** Rendered frontend screens via Specta-generated IPC contracts and Zod schema validation.
* **Domain Modules:** Import pipeline, financial modeling engine, period planning, variance analysis, board reporting, and governance rules.

---

## 3. What Worked Well (Patterns to Adapt)

1. **Strict Money Math Enforcement:**  
   The project enforced `i64` minor units / `rust_decimal` at the engine boundary (`MONEY-ROUNDING-SPEC.md`). `finalFPA` carries this over via `R8` (`Decimal` only in Python engine and `DECIMAL(18,2)` in DuckDB).
2. **Explicit 5-State UI Contracts:**  
   Every component specified 5 states: *Empty, Loading, Success, Warning, Error*. `finalFPA` adopts this in `docs/08_UI_UX_SPEC.md` §15 state matrix.
3. **Audited Mutation Log:**  
   All structural edits created an immutable audit event (`FR-PRJ-005` period lock & close snapshot).

---

## 4. What Failed / Architectural Bottlenecks

1. **Rust-IPC Serialization Overhead for Large Ingests:**  
   Passing 250,000+ row ERP exports across the Tauri IPC boundary row-by-row created significant latency.  
   *`finalFPA` Resolution:* Ingests are handled directly via Python + DuckDB bulk multi-row batch inserts (`DEF-030`), processing 250k rows in <75s.
2. **Maintenance Strain of Dual-Language Schema Binding:**  
   Synchronizing Rust serde structs $\rightarrow$ Specta $\rightarrow$ TypeScript Zod definitions led to schema drift.  
   *`finalFPA` Resolution:* Shared DuckDB analytical store with unified Python engine calculation helpers (`app/engine/`).

---

## 5. Summary of Lessons & Reuse Status

* **Direct Code Reuse:** Zero lines copied directly (no `ADP-nnn` row required for code).
* **Pattern Adoption:** Architecture reinforces `R8` exact money math, deterministic golden fixtures (`05` §12), and period-close immutability (`FR-PRJ-005`).

---

*Report prepared by `hermes` for handoff under task `PA-01`.*
