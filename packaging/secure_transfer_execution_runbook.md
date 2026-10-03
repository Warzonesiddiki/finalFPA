# SECURE TRANSFER EXECUTION RUNBOOK (`v0.1.0`)

**Project:** FP&A Month-End Copilot  
**Reference:** Doc 24 Section 7 (Distribution & Checksum Publication), Secure Transfer Rehearsal Report (`packaging/secure_transfer_rehearsal_report.md`)  
**Status:** Approved Operational Runbook (Pending Channel Approval)  
**Constraint:** *Do NOT send anything until formal channel approval is granted.*  

---

## 1. Quoted Distribution Rule (`Doc 24 §7`)
> *"Channel: The channel agreed with the client (`Q-016`); until agreed, a secure link — **never** an attachment in a public channel. Message contents: Artefact file name(s), the SHA-256 from `SHA256SUMS-<version>.txt`, one line on what changed, one line on what to re-test. Hash authority: The hash in the notes **and** the delivery message are identical to the file in the record; a mismatch is a failed release."* — `docs/24_RELEASE_AND_VERSIONING_RUNBOOK.md` §7.

---

## 2. Step-by-Step Execution Procedure

### Step 1: Bundle Assembly & Exclusion Audit
1. Run `python scripts/build.py` to compile production artefacts into `packaging/out/0.1.0/`.
2. Stage the delivery package manifest, checksums, user guide, and requirements pack into a clean staging folder per `packaging/secure_transfer_rehearsal_report.md`.
3. **Mandatory Exclusion Check:** Scan staging folder to ensure zero sample data (`*actuals.csv`, `*budget*.csv`) or internal engineering runbooks (`docs/00`–`20`, `25`, `26`) are present (`NFR-015` / `14` §16).

### Step 2: Cryptographic Hash Generation & Verification
1. Generate SHA-256 checksums for all staged artefacts and write to `SHA256SUMS-0.1.0.txt`:
   ```powershell
   certutil -hashfile Setup-FPandAMonthEndCopilot-0.1.0.exe SHA256
   certutil -hashfile FPandAMonthEndCopilot-0.1.0-portable.zip SHA256
   ```
2. Verify that local file hashes match `SHA256SUMS-0.1.0.txt` bit-for-bit.

### Step 3: Upload & Secure Transmission (`Q-016` Channel)
1. Upload the signed bundle (`Setup-FPandAMonthEndCopilot-0.1.0.exe`, `FPandAMonthEndCopilot-0.1.0-portable.zip`, `SHA256SUMS-0.1.0.txt`, and documentation) to the agreed secure client transfer portal.
2. Transmit notification message via secure out-of-band channel containing:
   - Artefact filenames.
   - Exact SHA-256 checksum hashes from `SHA256SUMS-0.1.0.txt`.
   - One line on what changed (`v0.1.0` initial pilot release).
   - One line on what to re-test (Installation, SHA-256 verification, and Sample Fallback).

### Step 4: Recipient Verification Instructions
Provide recipient with client verification command (`15` §8.3):
```powershell
certutil -hashfile Setup-FPandAMonthEndCopilot-0.1.0.exe SHA256
```
Instruct recipient to compare output hash against `SHA256SUMS-0.1.0.txt`.

### Step 5: Failure Recovery Protocol
- **Mismatch in Hash:** If recipient reports a hash mismatch, immediately invalidate the transfer, halt installation, inspect local build records, and re-upload a clean audited bundle.
- **Corrupt Download:** Re-initiate secure portal session and verify client disk space / network connectivity.

---
*End of Secure Transfer Execution Runbook.*
