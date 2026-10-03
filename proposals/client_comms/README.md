# Client comms pack — README for the lead

**Status:** proposals only. Nothing sent, nothing merged.
**Contents:** four client-facing documents in plain, non-technical language.
**Rule applied:** zero invented claims. Every factual statement is either quoted verbatim from a
project document or carries a "NOT A DOCUMENTED CLAIM" flag in its own source table.

---

## Files

| File | Purpose | Audience | Format |
|---|---|---|---|
| `01_pilot_request_email.md` | Asks the client to agree a one-month trial; sets the honest expectations up front | Finance contact + IT cc | Email |
| `02_transfer_instructions.md` | What we send, how to verify the fingerprints before running anything | Whoever receives the download | Instruction sheet |
| `03_smartscreen_walkthrough_printout.md` | One page, print-and-keep, for the person at the keyboard on install day | Analyst doing the install | Printout |
| `04_support_sheet.md` | Who to call, what to send, what we will never ask for | Everyone | Keep-beside-the-machine sheet |

---

## The design decisions behind the pack

**1. The privacy statement is quoted, never paraphrased.**
`docs/13` §8.3 owns one client-facing sentence about what leaves the machine. It is used verbatim
in file 01. `docs/13` §10.3 owns the longer privacy note and the "not a secure erase" caveat; both
appear in 01 in their own words, with the "ask IT to enable BitLocker" advice intact. `docs/15`
§8.3 owns the SmartScreen walkthrough; it is reproduced verbatim in files 02 and 03. `docs/01`
§15.1 owns the disclaimer; it is quoted verbatim in 01 and 04. Per `docs/15` §8.3 and `docs/22`,
these blocks are single-sourced and must not be reworded downstream — if the wording in these files
ever differs from the owner document, **the owner document wins**.

**2. The two scary things are said before they happen.**
The unsigned installer and the not-a-secure-erase deletion are both in the *first* email, before the
client has to ask. Both are documented limitations (`docs/15` §8.1; `docs/13` §4.3), not surprises.
Hiding them to make the pitch smoother would contradict `docs/13` §1's honesty rule.

**3. "Potential exception" is explained, not just used.**
`docs/01` §8 `P8` and `docs/06` require "potential exception" wording, never "error confirmed". A
finance reader needs to know a flag means *look at this*, so file 04 says it in one line.

**4. The support bundle section is written from the client's side.**
`docs/15` §9.1 describes the preview and the opt-in. File 04 restates it as: what is in it by
default, what is never in it, that you see a preview first, that the app never sends it, and that
turning on data rows is visible on screen. A client who cannot answer "what is in this zip?" in
one breath will not send it.

**5. "What we will never ask for" is a promise, not a courtesy.**
`docs/15` §9.4 is a written rule. It reads as a commitment here because it is one — and it doubles
as reassurance for someone being asked to hand over a finance team's data.

---

## Before any of this is sent — the lead's checklist

1. **Fill every bracketed field.** Names, numbers, version, date.
2. **Resolve the two "NOT A DOCUMENTED CLAIM" flags.**
   - *"install takes about ten minutes"* (file 01) — replace with a measured number from the timed
     clean-VM run in `docs/15` §5.2, or delete the estimate.
   - *"about two minutes"* for the hash check (file 02) — time it once, or delete the estimate.
   - The **Unblock** step in files 02 and 03 is standard Windows behaviour but is not written down
     in a project document. Confirm it against `TST-WIN-08` / `docs/15` §5.2 before it reaches a
     client.
3. **Re-check the security claims against the current build.** This matters more than usual right
   now — see the note below.
4. **Confirm the delivery channel in writing** with the client before sending file 02.
5. **Check nothing here contradicts `docs/22_END_USER_GUIDE.md` or `docs/29`.** Those are the
   shipped client-facing artefacts; these four files are new drafts, not replacements for them.

---

## ⚠ Important: do not send file 01 until the audit findings are resolved

`audit-external/TASK1_SECURITY_CONTRACT_AUDIT.md` found two places where the **application's own
screens** currently tell the user something untrue:

- The About & Diagnostics screen reports **"AI Key & Credential Redaction Guardrails — PASS —
  Zero unmasked secrets detected in state"**, and the diagnostics button reports a successful
  "redacted zip export" when no zip is produced. Those checks do not run.
- The Settings screen shows the **last four characters** of the AI key, which `docs/13` §5.2
  explicitly forbids ("No part of the key is ever displayed, including the last characters").

None of these are in the four documents above, and I have written nothing in them that repeats the
fabricated assurance. But the client will eventually read those screens, and the audit's R1/R3/R4
are exactly the kind of thing a finance team's auditor would find. **The honest fixes belong in
`app/`, which is not my folder to write to** — they are flagged for the lead in §4 of the audit
report.

The statements in files 01–04 are drawn from the *documented* contract (`docs/13`, `docs/15`,
`docs/01`), not from the current build. If the lead prefers to ship the client pack before those
defects are fixed, that is a reasonable call — but it should be a deliberate one, recorded in
`CHANGELOG`/`SESSION_LOG` per `docs/13` §16.2, and the client should not be shown the About screen's
doctor table in the meantime.

---

## What I did not write, and why

- **No invented features.** Every capability described here exists in `docs/13`/`15`/`01`. Where the
  current build does not yet implement something, the document does not claim it works.
- **No pricing, dates, SLAs beyond the documented L1 target, or commercial terms.** None of that is
  mine to draft and none of it is documented in the project.
- **No client name, brand, logo or contact details** anywhere in the pack.
- **No technical jargon without a plain-language gloss** on first use — "SHA-256" is introduced as
  "fingerprint", "BitLocker" as "Windows' own full-disk encryption", "SmartScreen" by what the box
  actually says on screen.
- **No changes to `docs/22` or `docs/29`.** If the lead decides any of this wording should replace
  what is in those documents, that is a `docs/` change with its own single-source obligations, and
  it needs to be made there rather than here.