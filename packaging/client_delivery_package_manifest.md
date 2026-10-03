# CLIENT DELIVERY PACKAGE MANIFEST (`v0.1.0`)

**Project:** FP&A Month-End Copilot  
**Reference:** Doc 24 §7 (Distribution & Checksum) & Doc 28 §6 (Go-Live Deliverables)  
**Status:** Assembly Complete & Ready for Channel Transfer  

---

## 1. Quoted Source Rules
- **Doc 24 §7 (Distribution):** *"Distribution: installer (`Setup-FPandAMonthEndCopilot-<version>.exe`) and portable zip delivered via secured client channel with published `SHA256SUMS-<version>.txt`. Zero sample-data inclusion (`14` §16)."*
- **Doc 28 §6 (Go-Live Deliverables):** *"Installer + SHA-256 delivered through agreed channel; user guide (`22`), client requirements pack (`29`), training outline (`22` §10), support contacts (`23`), tie-out worksheet template (`28`), and first-month ops checklist delivered."*

---

## 2. Delivery Package Manifest Table

| # | Item Name & Artefact File | Content Description | Readiness State | Delivery Channel | Sample Data Excluded? |
|---|---|---|---|---|---|
| **1** | `Setup-FPandAMonthEndCopilot-0.1.0.exe` | Windows installer (Inno Setup, per-user install, unsigned release candidate) | **Ready** | Secure Client Transfer Channel | **YES** (Strictly excluded per `14` §16) |
| **2** | `FPandAMonthEndCopilot-0.1.0-portable.zip` | Portable package bundle with `portable.flag.README.txt` | **Ready** | Secure Client Transfer Channel | **YES** (Strictly excluded per `14` §16) |
| **3** | `SHA256SUMS-0.1.0.txt` | Cryptographic SHA-256 checksums for installer and portable zip | **Ready** | Secure Client Transfer Channel | **N/A** (Checksum text) |
| **4** | `22_END_USER_GUIDE.md` (PDF / Clean MD) | End-user functional walkthrough tasks (`T-01`..`T-21`) | **Ready** | Handover Pack (`23`) | **YES** (Internal documentation excluded) |
| **5** | `29_CLIENT_REQUIREMENTS_PACK.md` | Client decisions, architectural rules, and acceptance scope | **Ready** | Handover Pack (`23`) | **YES** (Internal documentation excluded) |
| **6** | Training Outline & Recorded Demo Scripts | 60-minute training curriculum and 6-chapter video presenter scripts | **Ready** | Handover Pack (`23`) | **YES** (Internal documentation excluded) |
| **7** | Support Escalation & Contact Pack | L1–L3 contacts, S1–S4 response targets, and support log template (`23` §11) | **Ready** | Handover Pack (`23`) | **YES** (Internal documentation excluded) |
| **8** | Pilot Tie-Out Worksheet Template (`.xlsx`) | Four-class difference classification log and sign-off sheets (`28`) | **Ready** | Handover Pack (`23`) | **YES** (Template only, no raw data) |
| **9** | First-Month Operations Checklist | Weekly close cadence, ingestion rules, and sign-off points (`28` §6 item 20) | **Ready** | Handover Pack (`23`) | **YES** (Operations checklist) |

---

## 3. Exclusion Policy & Compliance Note
- **Sample Data Exclusion:** In strict accordance with `NFR-015` and `14` §16, **zero sample data files** (`d365_gl_actuals.csv`, `budget_fy26.csv`, etc.) or internal engineering runbooks (`docs/00`–`20`, `25`, `26`) are included in client-facing installer packages or handover zips.
- **Integrity Verification:** Every binary artifact is accompanied by its corresponding SHA-256 checksum hash.

---
*End of Client Delivery Package Manifest.*
