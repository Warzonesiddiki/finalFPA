# Pilot request email — DRAFT for the lead's review

**Status:** proposal only. Not sent. Every claim below traces to a project document; nothing is invented.
Bracketed `[ ]` fields are for the lead to fill.

---

**To:** `[client finance contact]`
**Cc:** `[client IT contact, if any]`
**From:** `[consultant name / firm]`
**Subject:** FP&A Month-End Copilot — trial request and what we'd need from you

---

Dear `[name]`,

Thank you for the time you have given this so far. I am writing to ask whether you would like to go
ahead with a one-month trial of the FP&A Month-End Copilot on your own month-end data.

**What the tool is**

It runs entirely on your own PC. You import the files you already use for your month-end, and it
gives you back the checks and the comparison work you do by hand today — flagged items to review,
a budget-versus-actual view, a forecast for the periods still open, and an Excel pack and slide
deck you can circulate. It is an aid for review, not a decision-maker: it highlights **potential**
exceptions for a qualified person to look at, and it never posts, approves, or changes an
accounting record.

**Where your data goes: nowhere.**

> The app works completely offline. Nothing is sent anywhere unless you switch AI on, add your own
> key, and press an AI button — in that case, a small redacted summary goes to the AI service you
> chose. The app never sends your files, your data or your key anywhere else.

That is the whole of it. There is no account to create, no cloud copy, and no usage tracking. If
you never turn the AI features on, the app never connects to anything. You keep your data; we do
not receive it — not during the build, not during support.

If you do choose to try the AI features later, you add your own key from your own AI provider.
Nothing is sent anywhere until you press an AI button yourself.

**What I would need from you to start**

1. **A machine.** A Windows 11 laptop that is yours or your team's, not a shared or personal one.
2. **Permission to install**, for about ten minutes. It installs for your Windows user only — it
   does not need administrator rights, and it does not change anything system-wide.
3. **One month of real files** — actuals, budget, and whatever you use for master data — placed in a
   folder you choose. The app copies them into its own project folder and never writes back to your
   originals.
4. **One hour of your time**, near the end of the month, to review what it produced and tell me
   where it was wrong. That is the part that makes the trial useful.
5. **A named contact** for the install day, if your IT team wants to be present.

**One thing to decide early: BitLocker.**

The app's own files are ordinary, readable files on your machine. That is deliberate — there is no
password to manage and nothing to lose if someone forgets one. The protection for a laptop that
could be lost or stolen is Windows' own full-disk encryption, not the app. If BitLocker is not
already switched on for that laptop, please ask your IT team to enable it before we start. If that
is not possible, tell me, and we will talk about the trade-off rather than pretend it is not there.

**Two honest limitations you should know now**

- **Deleting a project is not a secure erase.** It removes the working files from that PC, but on
  modern drives, deleted data can sometimes be recovered. Backups and exported files are not
  affected at all — they stay where you put them.
- **The installer is unsigned**, because a code-signing certificate was not purchased for this
  version. Windows will therefore show a blue "Windows protected your PC" message the first time
  you run it. This is expected and does not mean the file is harmful. I will send you a separate
  one-page walkthrough, and a fingerprint (SHA-256) so you can confirm the file you received is
  exactly the file I sent.

**What this tool does not do**

> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and
> trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does
> **not** guarantee that every error, misstatement, or irregularity will be detected. All figures,
> flags, and AI-generated drafts must be reviewed by a qualified accountant before any business
> decision, filing, or external reporting. The tool never posts, approves, or alters accounting
> records, and it never replaces professional judgement.

**If you say yes**

I will send three things: the installer, the SHA-256 fingerprint file, and the one-page Windows
walkthrough. Then we pick a time for the install, and I will sit with you for the first run. After
the trial month we sit down together and go through what it found — the items it got right, the
items it got wrong, and the items it missed. You decide then whether it earns a place in your
process.

No obligation at any point, and deleting a project removes your working data with no involvement
from me.

With thanks,

`[name]`
`[role / firm]`
`[phone]`

---

## Source of every claim in this email

| Claim in the email | Verbatim or near-verbatim from |
|---|---|
| "runs entirely on your own PC" / "Nothing is sent anywhere unless you switch AI on…" | `docs/13_SECURITY_PRIVACY.md` §8.3 — quoted verbatim |
| "Advisory tool — not professional advice…" block | `docs/01_PRD.md` §15.1 — quoted verbatim, canonical wording |
| "highlights **potential** exceptions… never posts, approves, or alters accounting records" | `docs/01_PRD.md` §15.1 |
| installs per-user, no admin | `docs/15_PACKAGING_DEPLOYMENT_RUNBOOK.md` §1.2, §7 (installer contract: per-user, HKCU-only, no admin) |
| unsigned installer, blue dialog, SHA-256 | `docs/15` §8.1, §8.2, §8.3; `ADR-003` in `docs/09` |
| BitLocker is the correct control for a stolen device | `docs/13` §9.1, §10.3 — quoted verbatim ("ask IT to enable BitLocker if the laptop could be lost or stolen") |
| "Deleting a project … is not a secure erase" | `docs/13` §4.3 step 5 — quoted |
| backups/exports unaffected by delete | `docs/13` §4.3 steps 2 and 5 |
| source files copied into project folder, never written back | `docs/13` `SEC-005`, `SEC-006` |
| install takes about ten minutes | **NOT A DOCUMENTED CLAIM.** The lead must verify against the timed clean-VM run (`docs/15` §5.2, 24 steps) before sending, or delete the number. |
| "one month of real files" trial shape | `docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md` (trial month / UAT / go-live); the specific request structure is mine — lead to confirm. |

**Lead's checklist before sending:** confirm the recipient, confirm the version being offered, run
the timed install to replace the "ten minutes" estimate with a measured number, and confirm the
data-retention statements still match `docs/13` §10.2 at send time.