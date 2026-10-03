# Support sheet — KEEP THIS NEXT TO YOUR MACHINE

**FP&A Month-End Copilot · `[version]` · Prepared `[date]`**

---

## Who to call

| | |
|---|---|
| **First point of contact** | `[consultant name]` — `[phone]` · `[email]` |
| **Response target** | Same business day (`docs/15` §9.3, level L1) |
| **After hours** | `[name / number]` |
| **Your IT contact** | `[name / number]` |

---

## What to send us

**Write what happened in your own words.** That is the single most useful thing you can send us.
A screenshot helps if there is one, but plain description beats a screenshot every time.

Please tell us:

1. What you were trying to do.
2. What you expected to happen.
3. What happened instead.
4. The **error code** shown at the top of the message, if there is one (it looks like `ERR-…`).

---

## If the app offers to send a support bundle

You may send it. Before you do, this is what is in it:

| | |
|---|---|
| **By default it contains** | Version and build information, your Windows and hardware details, the last part of the app's log files, and the *names of columns* and the *number of rows* in your tables. |
| **By default it does NOT contain** | Any amounts. Any vendor names. Any of your data rows. Your AI key. Your database files. |
| **You will see a preview first** | The exact list of files, before anything is written. |
| **You control it** | The app never sends the bundle. You attach it yourself from your own mail. |
| **If you tick "include data rows"** | It will say so on the screen, and you should look at it before you send it. |

---

## Things we will never ask you for

This is a written rule on our side, not a courtesy.

- **Your AI key**, or a photo of it. There is no reason for anyone to see it.
- **A copy of your database**, or a full data dump. The support bundle is metadata-only by default.
- **Remote access**, screen sharing of a live project, or an administrator account. The app is
  local-only by design; there is no remote support and there is no need for any.
- **Your Windows password.** Never.
- **For you to turn off Defender or SmartScreen**, or to add an exclusion. If a security tool
  objects to the app, that is handled with Microsoft, not by weakening your protection.

---

## The five questions we get most

**"It says Windows protected your PC."**
Expected for an unsigned first release. The fingerprint check on your install sheet confirms the
file is the one we sent. Then: **More info** → check the app name and version → **Run anyway**.

**"It asks me for a folder — can I use OneDrive / Dropbox / Google Drive?"**
Not for the project itself. Those folders can corrupt a live working project. Use a normal local
folder such as `C:\FP&A Projects\`. **Exporting** the finished pack to a synced folder is fine —
you will get a one-line notice, and the upload will happen by your own cloud provider as usual.

**"Where are my files?"**
Everything stays on this PC, in your Windows user folder. Nothing is uploaded and there is no
cloud copy.

**"I deleted a project. Is that permanent?"**
It removes the working files from this PC, but on modern drives deleted data can sometimes still
be recovered — Windows' Delete is not a shredder. Backups and exported files are not affected;
they stay exactly where you put them. For a laptop that could be lost or stolen, ask your IT team
to enable BitLocker.

**"The AI button did nothing."**
That is the app working as designed. If no AI key is configured, the app writes the text itself
using rules instead of an AI service, and labels it differently. Nothing was lost and nothing was
sent anywhere.

---

## What this tool does not do

> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and
> trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does
> **not** guarantee that every error, misstatement, or irregularity will be detected. All figures,
> flags, and AI-generated drafts must be reviewed by a qualified accountant before any business
> decision, filing, or external reporting. The tool never posts, approves, or alters accounting
> records, and it never replaces professional judgement.

Two things worth saying out loud, because they are the ones people get wrong:

- A flag means **"look at this"**, not **"this is wrong"**. Nobody has decided anything yet.
- An AI-written paragraph is a **draft**. It starts with the label *"AI draft — review before use."*
  A person has to read it and approve it before it can go into anything you circulate.

---

## When you have a problem, in one line

**Describe it in your own words → send the error code if you can see one → send the support bundle
if the app offers it → call `[phone]`.**

---

*This sheet matches the project's support procedure (`docs/15` §9, `docs/23`) and the security
contract (`docs/13`). Prepared `[date]`.*