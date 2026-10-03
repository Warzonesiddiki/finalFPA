# Presenter script — 60-minute live session, word for word

**Audience:** the client's finance team. Non-technical. Never used before.
**Data:** the bundled **sample project** only. Never client data.
**Blocks:** exactly the seven in `docs/22` §10.1. Timings are the documented ones.

**Notation for the presenter:**
- `SAY:` — read this out, close to verbatim. Short sentences.
- `DO:` — an action in the app. Clicks are real tabs in `ui/src/main.tsx:38`.
- `[IF BEHIND]` — what to drop when you are running late. Read before the session.
- `[BUILD NOTE]` — something documented but not yet built. Read this line to yourself before you
  present. Do not improvise around it.
- `[ASK]` — stop and let the room answer before you continue.

---

## BEFORE YOU START — 5 minutes, before anyone arrives

- [ ] App installed and already launched once (do not make the audience sit through SmartScreen).
- [ ] Sample project open, untouched.
- [ ] User guide printed, one per attendee.
- [ ] Support sheet printed and **on the table**, not handed out at the end.
- [ ] Timer visible to you.
- [ ] Read the eight `[BUILD NOTE]` lines in this script. All eight.

---

# BLOCK 1 — Orientation (0–5 min)

### 1.1 What this is (1 min)

`DO:` Open the app. Home screen.

> `SAY:` "Good morning. In the next hour I'm going to show you what this tool does in your month-end
> — not the theory, the actual clicking. At the end you'll have done one import yourselves.
>
> One thing up front, before I show you anything. This tool **highlights** things for a person to
> look at. It does not decide anything. When you see a flag, that means *look at this* — it never
> means *this is wrong*. Somebody still has to make that call, and it stays with you."

`[ASK]` "Does that distinction make sense before I go further?" — Get a yes. If anyone is unsure,
repeat it. Everything downstream depends on it.

### 1.2 What it is not (1 min)

> `SAY:` "Three things it will not do.
>
> It will not post, approve or change an accounting record. Ever.
>
> It will not send your files anywhere. Everything stays on this PC. If you never turn on the AI
> features, it never connects to anything at all.
>
> And it is not professional advice. Let me read you the sentence the tool is built around."

`DO:` Nothing on screen. Read the disclaimer from your printed copy, or open `docs/01` §15.1.

> `SAY:` "*Advisory tool — not professional advice. FP&A Month-End Copilot is an analysis aid. It
> highlights **potential** exceptions, variances, and trends for review. It does **not** provide
> audit, accounting, tax, or legal advice, and it does **not** guarantee that every error,
> misstatement, or irregularity will be detected. All figures, flags, and AI-generated drafts must be
> reviewed by a qualified accountant before any business decision, filing, or external reporting.
> The tool never posts, approves, or alters accounting records, and it never replaces professional
> judgement.*"

> `SAY:` "That last sentence is the honest one. 'It does not guarantee that every error will be
> detected' — I'm telling you that now, at the start, so it's not a surprise later."

### 1.3 Where your data lives (1.5 min)

> `SAY:` "Everything you import, calculate and export stays on this PC, in your Windows user folder.
> There is no account, no cloud copy, and no usage tracking."

`DO:` Show the data-folder path on the About screen. **Do not click Export Diagnostics.**

`[BUILD NOTE]` **1.** `POST /api/v1/diagnostics/export` (`app/api/main.py:1810`) returns a hard-coded
filename and writes no file. If asked, say: *"That button isn't finished yet — when it is, you'll see
a preview of exactly what's in the bundle before anything is written."* **Never** say the export
succeeded and **never** demonstrate it.

> `SAY:` "If you ever do turn on AI, you add your own key from your own AI provider. Only when you
> press an AI button does a small redacted summary go to that provider. Never your files, never the
> whole database, never your key. If you never turn AI on, nothing ever connects anywhere."

### 1.4 Deleting a project (0.5 min)

> `SAY:` "Last thing in this block. If you delete a project, that removes the working files from this
> PC. Backups you made yourself and files you exported are not affected — they stay where you put
> them.
>
> And I want to be straight with you: **deleting a project is not a secure erase.** Windows Delete is
> not a shredder. On modern drives deleted data can sometimes be recovered. The right control for a
> laptop that could be lost or stolen is BitLocker — Windows' own full-disk encryption. If that's not
> switched on for this laptop, please ask your IT team to enable it before we go live."

### 1.5 The rhythm (1 min)

> `SAY:` "The tool follows your month, not the software's month. Nine steps, roughly:
> set up the period, import, check quality, look at the variance, work the exceptions, forecast,
> write the commentary, produce the pack, issue it. We're going to walk most of that now."

### 1.6 Cut-line

`[IF BEHIND]` **Never cut 1.2 or 1.4.** They take 2.5 minutes total and they are what stops the tool
being misread.

---

# BLOCK 2 — Import and check (5–15 min)

### 2.1 Trainer demo (6 min)

`DO:` Click the **Import** tab.

> `SAY:` "I'm going to import one of the sample files. Watch what it does, then you do it yourself."

`DO:` Walk the wizard. Narrate each step as you click it.

> `SAY:` "Step one, choose the file. It looks at the file and guesses what kind it is. If it guesses
> wrong, you tell it — it's a suggestion, not a decision."

`DO:` File selected → pre-scan.

> `SAY:` "Before it reads a single row, it tells you what's in the file: how many rows, how many
> sheets, roughly how long it'll take. If a file is enormous, you find out now, not halfway through."

`DO:` Column mapping.

> `SAY:` "Here's the step that generates the most questions, so let me be slow. The tool is matching
> your column headings to the fields it needs. Green means it matched. **Amber means it did not
> match, and it needs you.**"

`[ASK]` "What would you do if it got a column wrong and you didn't notice?" — Let someone say
"the numbers would be wrong." Then:

> `SAY:` "Exactly. That's why amber is amber, and why this is the one step you never click through."

`DO:` Validate.

> `SAY:` "Now it validates. You get a score out of a hundred, and underneath, every check it ran —
> pass or fail — and for any failure, which rows caused it."

`DO:` Point at one failed check and expand it.

> `SAY:` "Here's one that failed. It names the rows. Nothing is hidden, nothing is silently dropped."

`DO:` Commit summary, then commit.

> `SAY:` "The summary before you commit: this many rows in, this many set aside, this score. If that's
> wrong, this is the moment to stop. After commit, it's a batch you can void — but it's cleaner to
> stop here."

### 2.2 Now you do one (4 min)

> `SAY:` "Your turn. Same steps, different file. I'll walk round."

Hand out the file list. Circulate. **Do not take over someone's mouse.** If they get stuck on amber,
ask: *"What does amber mean?"* — that is the only hint they need.

### 2.3 Where the rows went (2 min)

> `SAY:` "Two questions I get every time.
>
> **'What if some rows are wrong?'** They don't disappear. They go into what we call quarantine, with
> the reason. Nothing is ever dropped without telling you.
>
> **'Does it change my original file?'** Never. It copies your file into the project folder and reads
> the copy. Your source file is opened read-only and is never written to."

`DO:` Import history tab — show the three batches and one voided status.

### 2.4 Read the score (2 min)

> `SAY:` "The data-quality score. It's a summary, not a verdict. A low score doesn't mean your data is
> bad — it means some checks failed, and you should find out which before you rely on anything
> downstream. Can you read me the score, and tell me one check that failed?"

`[ASK]` Have an attendee read the score and name a failed check. **This is the competency check.**

### 2.5 Cut-line

`[IF BEHIND]` Drop 2.3 and demo the wizard faster. **Keep 2.2 and 2.4** — the hands-on import and
reading the score are the two things they must be able to do.

---

# BLOCK 3 — Analyse and drill (15–25 min)

### 3.1 Find the biggest variance (3 min)

`DO:` Click **Analyse**.

> `SAY:` "This is budget versus actual. Notice it never shows a bare plus or minus — it says
> *favourable* or *unfavourable*. A negative number isn't bad news on its own; whether it's good or
> bad depends on which line it's on. The tool knows that, so you don't have to."

`DO:` Sort adverse.

> `SAY:` "Let me sort by the biggest adverse variance. And I'm going to say the boring thing that
> matters: **biggest is not most important.** A large favourable variance on a line you expect is
> boring. A small one you can't explain is interesting. Sort by size to find things; use your
> judgement about which matter."

### 3.2 Drill to the transactions (4 min)

`DO:` Click a figure. Drill-through opens.

> `SAY:` "Click any number and it shows you what's behind it — source file, which import, which
> voucher lines. This is the part I'd argue for most. Every figure the tool shows you can be traced
> back to the rows it came from. That's the difference between this and a summary."

`[ASK]` "What would you do if a figure didn't tie back to anything?" — This is the answer you want:
*"Then we don't use it."*

### 3.3 The bridge (2 min)

> `SAY:` "The bridge is the same story in one picture — what moved the variance. It's useful in a pack
> for someone who won't read the table. For your own review, the drill-through is the more useful of
> the two."

### 3.4 The `n/a` (1 min)

`DO:` Find a KPI card showing `n/a`, hover it.

> `SAY:` "When a ratio can't be computed — usually no prior period to divide by — it says `n/a`. It
> does not show you zero, and it does not show you `Infinity`. Zero would be a lie and you'd carry
> it into a pack."

### 3.5 Cut-line

`[IF BEHIND]` Cut 3.3. The bridge is presentational; the drill-through is the audit trail.

---

# BLOCK 4 — Exceptions (25–35 min)

`[BUILD NOTE]` **2.** The Exceptions tab is wired at `ui/src/main.tsx:262-268` and the screen exists at
`ui/src/components/exceptions/`. If it renders, run this block. If a sub-feature (evidence bundle,
effectiveness analytics) is not reachable, **say so** — do not describe a screen you are not showing.

### 4.1 What an exception is (2 min)

`DO:` Click **Exceptions**.

> `SAY:` "Same principle as before, and I'll keep saying it. A **potential** exception. The tool applied
> a rule you agreed to, and the rule matched. That is all it means. It is not an error. It is not a
> finding. It is 'a person should look at this'.
>
> Which means the most valuable thing you do in this screen is decide what you are *not* looking at."

### 4.2 Triage (4 min)

> `SAY:` "Filter to High. Look at owner, age, status. Ageing is against a target — seven days for
> High, twenty-one for Medium, forty-five for Low. If something is sitting at forty days and it's
> High, that's the conversation to have."

`DO:` Sort by age. Change one filter.

### 4.3 Open one (3 min)

`DO:` Click a row. Open the detail drawer.

> `SAY:` "Here's the evidence: which rule, what threshold it used, what the history is. If you're going
> to challenge a flag — and you will, that's healthy — this is where you check whether the rule
> matched what you think it matched."

`DO:` Change the status. Add a note.

> `SAY:` "Add a note. **Whatever you write here is permanent and it exports with the pack.** So write
> it for the person who reads this in six months with no memory of today. 'Checked with supplier,
> invoice valid, recurring' — not 'ok'."

### 4.4 Export evidence (1 min)

`DO:` Open the evidence bundle modal. **Show the scope choices. Do not generate.**

> `SAY:` "This builds a bundle for one exception, so you can hand it to whoever needs to answer the
> question. You choose what goes in."

### 4.5 The cut that matters (2 min)

> `SAY:` "If a rule keeps raising things that aren't worth looking at, tell us. That's not you working
> around the tool — that's the tool telling us the rule needs tuning. There's a place for that. It
> goes in the backlog as a rule change, with a reason. I'd rather tune ten rules honestly than have
> you filter around fifty."

### 4.6 Cut-line

`[IF BEHIND]` Cut 4.4. **Keep 4.1 and 4.3.** The "potential, not error" framing and the permanent
note are the two things that must land.

---

# BLOCK 5 — Forecast and commentary (35–45 min)

`[BUILD NOTE]` **3.** Forecast tab is wired at `ui/src/main.tsx:271-275`. **Use the Base Case and
avoid the scenario comparison** if it does not render.

`[BUILD NOTE]` **4.** The AI draft label appears at `ui/src/components/ai/FollowUpMessageComposer.tsx:159`.
It renders as title case (`AI Draft — Review Before Use`) rather than the specified
`AI draft — review before use.` **Do not stop to explain a casing difference to the room** — but do
not quote it as verbatim either.

### 5.1 What forecasting means here (2 min)

> `SAY:` "Actuals that are closed, periods still open. The tool picks a method per line — a trailing
> run-rate, the remaining budget spread, a three-month average — and shows you what it used. Lines
> that aren't eligible say so, and why."

### 5.2 Override, with a reason (4 min)

`DO:` Click an override. Type a reason. Save.

> `SAY:` "You can override any cell. When you do, it asks for a reason, and it is mandatory.
>
> Now — the honest question. **Is anyone checking that reason?** No. Nobody reads it at the time you
> type it. It exists so that three months later, when someone asks why this forecast line looks
> different from what the method would have produced, there is an answer.
>
> So write the real reason. 'Q4 blackout, customer confirmed' — not 'override'."

`[ASK]` "What's a good reason?" — Get a real one from the room, not 'override'.

### 5.3 Lock the version (2 min)

> `SAY:` "Lock the version when you're happy. Locked means read-only, and it means the pack you
> issue points at exactly these numbers."

### 5.4 Write a comment (3 min)

`DO:` Commentary. Type something. Save.

> `SAY:` "This is the narrative that goes on the slide and in the pack. You can write it yourself —
> which I'd encourage for anything a person outside the finance team will read."

### 5.5 AI, and what it is (4 min)

> `SAY:` "The AI features are **off by default**, and in this sample project there's no key
> configured, so what you're about to see is the app writing the text itself using rules.
>
> If you never add a key, that's what you get forever, and it costs nothing and needs no internet."

`DO:` Press an AI action. It returns a rule-based summary.

> `SAY:` "See the label? **Rule-based summary.** That's the app being honest about where the words
> came from. It will never present a rule-written paragraph as if a person or a model wrote it.
>
> If you do add a key later, anything an AI writes arrives labelled **'AI draft — review before
> use.'** A draft. It is not approved. It cannot go into anything you circulate until a person reads
> it and approves it. There is no send button anywhere in this tool — you copy or download, and the
> sending is yours."

`[BUILD NOTE]` **5.** Do **not** open Settings → AI with a real key configured and screen-share it.
`main.py:1431` currently shows the last four characters of a stored key. If you demo Settings at all,
keep the AI key empty.

### 5.6 Cut-line

`[IF BEHIND]` Cut 5.3 and the scenario comparison. **Keep 5.2 and 5.5.** The override-reason
discipline and the AI labelling are the two behaviours that change how people work.

---

# BLOCK 6 — Pack and issue (45–55 min)

### 6.1 Generate (3 min)

`DO:` Click **Reports**. Generate a pack.

> `SAY:` "This produces the Excel workbook and the slide deck. Both are generated from the same
> numbers, so they can't disagree with each other — there's a test that checks exactly that."

### 6.2 Open both (4 min)

`DO:` Open the workbook. Walk one sheet. Open the deck. Show the last slide.

> `SAY:` "Two things to look for.
>
> **First**, there's no formulas in the workbook. It's values, not a spreadsheet that recalculates
> differently on your machine than on mine. Every number is fixed at issue.
>
> **Second**, the disclaimer is on the footer of every sheet and on the deck. It travels with the
> document. If you forward this to someone who hasn't met us, they still see it."

### 6.3 Issue (3 min)

`DO:` Issue a version. Enter recipients.

> `SAY:` "Issuing freezes everything: the numbers, the commentary, the exception statuses. The version
> after this is version two, and version one stays exactly as it was. If someone asks 'what did we
> send on the 3rd?', the answer is a frozen artefact, not a recollection."

### 6.4 Backup (2 min)

`DO:` Click **Backup**.

> `SAY:` "Backup writes a zip: your databases, your archive, your settings, with a manifest listing
> every file and its fingerprint.
>
> Two things to know about it.
>
> **It is a normal zip.** It is **not encrypted.** Anyone who can open the file can read the project.
> Store it somewhere protected, or let Windows encryption protect the disk.
>
> **And deleting a project does not delete your backups** — they're yours, the app never touches
> them."

`[BUILD NOTE]` **6.** `BackupRestoreScreen.tsx:175` currently describes the archive as
*"encrypted-ready"*. **Do not repeat that wording** — say what is true: a plain zip with a manifest.
If asked why the screen says "encrypted-ready", say it is wording we are correcting.

### 6.5 The accuracy question (3 min)

> `SAY:` "This is the question you'll be asked, so let me answer it properly now.
>
> We do not say this tool finds everything. We say it checks the things we have written down — and we
> have gone through that list with you, line by line: which rules matter to your month, and which
> are deliberately switched off.
>
> What the tool cannot tell you is that there is nothing outside those rules. That's the limit of any
> checklist, including one you wrote yourself.
>
> Which is why the trial ends the way it does: **you run your own month, and you tell us what it
> missed.** Not us telling you it's complete. If it misses things, that's the evidence that makes
> the next version better, and I would much rather have that conversation in month one than in year
> two."

### 6.6 Cut-line

`[IF BEHIND]` **Do not cut 6.5.** Cut 6.2 to one sheet and one slide. Cut 6.4 to the "it's a plain zip"
sentence alone.

---

# BLOCK 7 — Your real month (55–60 min)

### 7.1 The file checklist (3 min)

`DO:` Open the checklist on your printed guide.

> `SAY:` "Let's do the practical bit. For your first real month, you'll need:"

Walk the list. **Do not invent file names** — use the checklist in `docs/22`.

> `SAY:` "One folder rule that matters more than the rest: **do not put the project in OneDrive,
> Dropbox or Google Drive.** Those sync folders can corrupt a live working project — that's threat
> number six in our security review, and it's a real one for finance laptops. Use a normal local
> folder, `C:\` something. Exporting the finished pack to a synced folder is fine — you'll get a
> notice that it's going to upload, and that's expected, because sharing the pack is the point of
> the pack."

### 7.2 Who does what (1 min)

> `SAY:` "So — who imports, and when? Who reviews the exceptions? Who issues the pack? Let's write
> the names down now, not later."

`[ASK]` Get actual names and dates. Write them on the handout.

### 7.3 Help (1 min)

> `SAY:` "Three ways to get help, all on the sheet in front of you. Call me. Use the support sheet.
> And if the app offers you a support bundle, you can send it — but read it first: by default it
> contains no amounts and no vendor names, and you'll see exactly what's in it before anything is
> written.
>
> And what we will never ask you for: your AI key, a copy of your database, remote access to your
> machine, or your Windows password."

---

## CLOSING LINE

> `SAY:` "One last thing. If something in this hour didn't make sense, or you saw something you don't
> believe — I want to hear it today, not in three months. Especially the second kind. If a flag comes
> up that you think is wrong, tell me; if a number looks odd, tell me. The trial only works if you're
> arguing with it.
>
> Thank you."

---

## THE FIVE THINGS THEY MUST BE ABLE TO DO

Hand this to yourself. If someone can do these five, the session worked.

- [ ] Explain what a "potential exception" means — *look at this*, not *this is wrong*.
- [ ] Read the data-quality score and name one failed check.
- [ ] Find a variance and drill to the transactions behind it.
- [ ] Open an exception, change a status, and write a note worth reading in six months.
- [ ] State that backups are plain zips and deleting a project is not a secure erase.

---

*Structure and timings follow `docs/22` §10.1. Every claim traces to a project document; the source
table is in `proposals/training/README.md`. Nothing in this script was invented, and no client data
appears anywhere in it.*