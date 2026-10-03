# SECURE TRANSFER CHANNEL PROPOSAL (`v0.1.0`)

**Project:** FP&A Month-End Copilot  
**Reference:** Doc 24 Section 7 (Distribution and Checksum Publication), Doc 28 Go-Live  
**Status:** Submitted for Owner Approval  

---

## 1. Quoted Distribution Rule (`Doc 24 §7`)
> *"Channel: The channel agreed with the client (`Q-016`); until agreed, a secure link — **never** an attachment in a public channel. Message contents: Artefact file name(s), the SHA-256 from `SHA256SUMS-<version>.txt`, one line on what changed, one line on what to re-test. Hash authority: The hash in the notes **and** the delivery message are identical to the file in the record; a mismatch is a failed release."* — `docs/24_RELEASE_AND_VERSIONING_RUNBOOK.md` §7.

---

## 2. Transfer Channel Options ($\le 3$)

### Option A: Secure Client-Provisioned Enterprise File Share (Recommended)
- **Mechanism:** Client-provided secure portal (e.g., SharePoint, OneDrive for Business, or encrypted SFTP) managed under client IT governance.
- **Sizing Capacity:** ~500 MB (accommodates installer ~295 MB, portable zip, checksums, and documentation bundle).
- **Access Control & Expiry:** Restricted to authorised client signers; download link expiry set to 7 days post-delivery.
- **Pros/Cons:** Aligned with client security policies; zero external third-party dependency; auditable access logs.

### Option B: Encrypted Cloud Storage Link (Password-Protected)
- **Mechanism:** Encrypted transfer link (e.g., Proton Drive / secure enterprise file transfer) with a 256-bit AES password communicated via secure out-of-band channel (Signal/Teams voice).
- **Sizing Capacity:** ~500 MB limit.
- **Access Control & Expiry:** Password-protected, auto-expiring after 48 hours / 3 download attempts.
- **Pros/Cons:** Rapid deployment; good fallback if client portal provisioning is delayed.

### Option C: Secure Physical Media (Encrypted USB Thumb Drive)
- **Mechanism:** BitLocker-encrypted USB drive delivered by courier with password communicated out-of-band.
- **Sizing Capacity:** 32 GB+.
- **Access Control & Expiry:** Physical chain of custody.
- **Pros/Cons:** Maximum air-gapped security; avoids network egress constraints; higher lead time (1–2 days).

---

## 3. Recommendation & Action Plan
- **Recommended Option:** **Option A (Secure Client-Provisioned Enterprise File Share)**, with **Option B** as an immediate fallback if enterprise portal provisioning is delayed.
- **Publication Protocol:**
  1. Upload `Setup-FPandAMonthEndCopilot-0.1.0.exe`, `FPandAMonthEndCopilot-0.1.0-portable.zip`, and `SHA256SUMS-0.1.0.txt`.
  2. Transmit notification message containing exact SHA-256 checksums, what changed, and client verification instructions (`certutil -hashfile ...` per `15` §8.3).
- **Approval Requested:** Owner sign-off to finalize the transfer channel method.
