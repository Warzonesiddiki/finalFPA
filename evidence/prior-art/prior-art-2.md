# Prior-Art Review #2: `github.com/Warzonesiddiki/fp-A-betterversion`

> **Reviewer:** `hermes` (Analyst's Advocate)  
> **Task Reference:** `PA-02` (P2)  
> **Target Evidence Path:** `evidence/prior-art/prior-art-2.md`  
> **Target Review Path (for Handoff):** `team/reviews/prior-art-2.md`  
> **Date:** 2026-10-05  

---

## 1. License Gate 4A Verification

| Field | Detail |
|---|---|
| **Upstream Repository** | `https://github.com/Warzonesiddiki/fp-A-betterversion` |
| **Pinned SHA** | `04c329e0678e34b712f77ee97e0d536050d18e6a` (depth-1 HEAD, fetched 2026-10-05) |
| **License** | **MIT License — PASS (Gate 4A)** |
| **Copyright Holder** | Copyright (c) 2026 Tahir |
| **License Status** | MIT is on the §4 GO list (`32` §3). Code patterns and requirements may be evaluated and adopted under strict `ADP-nnn` registration. |

---

## 2. Architectural Analysis & Overview

The repository represents a feature-rich, multi-engine FP&A web/desktop codebase built with **React 19 + TypeScript + Vite 8 + Tailwind 4 + Zustand / Immer + AG Grid + Recharts**.

### Core Structure
* **State Management:** 28+ domain Zustand stores (`src/store/`) using `subscribeWithSelector` + `persist` + `immer`.
* **Engine Library:** 180+ calculation engines (`src/engines/`) covering GL validation, FX rates, consolidation, variance, and forecast models.
* **Component Library:** 240+ atomic UI components (`src/components/ui/`) with AG Grid integration for high-density tabular data.

---

## 3. What Worked Well (UX & Data Patterns)

1. **Rich Tabular Grid Exploration (AG Grid):**  
   The application provided exceptional BvA matrix slice-and-dice, allowing users to expand account hierarchies, filter by cost center, and inspect line-item details. `finalFPA` carries this forward in `SCR-015` (BvA Matrix) and `SCR-021` (Drill-through).
2. **Explicit Favourable / Unfavourable Indicators:**  
   Enforced direction-aware variance formatting (#16A34A Favourable vs #DC2626 Unfavourable) paired with textual indicators (`Fav` / `Adv`). `finalFPA` mandates this in `05` CALC-012 and UI Principle 6 (P19: never colour-only).
3. **Dedicated Exception Triage UI:**  
   Provided specialized views for reviewing flagged GL anomalies with severity tags (High, Medium, Low). `finalFPA` codifies this in `SCR-023` (Exceptions Register) and `SCR-024` (Exception Detail).

---

## 4. What Failed / Over-Engineering Traps

1. **Fragmentation Across 180+ Engine Files:**  
   Dividing calculation logic into hundreds of small JS engine files led to duplicated formula logic and subtle rounding discrepancies across modules (`R12` violation).  
   *`finalFPA` Resolution:* `app/engine/` provides a single authoritative implementation of each calculation formula (`05` §1.4).
2. **Float Arithmetic Drift in Financial Engines:**  
   Using standard JavaScript `number` (binary float) inside client-side engine loops caused rounding errors on large monetary sums.  
   *`finalFPA` Resolution:* Strict Python `Decimal` in backend engine (`R8`) and exact equality comparisons (`05` §1.3).
3. **Excessive Framework Overhead:**  
   Adopting complex agent-coordination frameworks (BMAD v5.0) and multi-tier store middlewares created heavy build and test setup requirements.  
   *`finalFPA` Resolution:* Clean FastAPI / DuckDB backend + standard React frontend with strict spec-driven QA gates (`14`).

---

## 5. Summary of Lessons & Reuse Status

* **Direct Code Reuse:** Zero lines copied directly (no `ADP-nnn` row required for code).
* **Pattern Adoption:** Validates UI/UX contracts for high-density BvA grids (`SCR-015`), exception triage workflows (`SCR-023`), and direction-aware variance formatting (`05` CALC-012).

---

*Report prepared by `hermes` for handoff under task `PA-02`.*
