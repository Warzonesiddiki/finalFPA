# Recorded demo — six chapter scripts, word for word

**Format:** six chapters, 3–5 minutes each, per `docs/22` §10.2. Recorded on the **sample project**
only.
**Chapter titles match the `docs/22` §4 task titles** so a viewer can jump straight to the guide.
**Audience:** someone who could not attend the live session, or who wants to rewatch one part.

---

## Recording rules — read before you press record

1. **Sample project only.** Never client data. Never an unreleased build. `SEC-007`.
2. **Real app, real clicks.** No slides. No mock-ups. The viewer must be able to follow along in
   their own copy.
3. **Narration is complete.** Every click gets a sentence. A viewer should be able to pause, rewind
   and copy down what they saw.
4. **Say the honest thing out loud.** Where a feature is unfinished, say so. A recording that
   promises more than the build delivers is worse than no recording.
5. **No music, no transitions.** This goes into a finance team's induction pack, not a launch reel.
6. **Show the disclaimer.** Every chapter ends on the same two sentences (see the sign-off below).

**Total runtime target: 22–28 minutes.**

---

# CHAPTER 1 — Home and the period (3 min)

`docs/22` §4 T-01/T-02 · tab: **home** (`ui/src/main.tsx:262`)

### Narration

> "This is the opening screen. Two things to orient yourself.
>
> Up top: which period you're in. **Periods can be open or closed.** An open period still takes
> changes. A closed one doesn't — and if something needs to change in a closed period, that's a
> deliberate, recorded action, not something you do by accident.
>
> Down below: recent import activity. Each row is one import — which file, how many rows loaded, how
> many were set aside, and whether the file balanced.
>
> **Balance check.** Debits equal credits. If it doesn't balance, that file is wrong and everything
> downstream of it is suspect. That's why it's flagged right here at the point of import, rather
> than discovered in a pack three weeks later.
>
> This is a 60-second tour. Everything you just saw has a task in the guide if you want it later."

### Sign-off (all chapters)

> "And to repeat — these are **potential** exceptions for a person to review. The tool never decides
> anything, and it never posts or changes an accounting record."

---

# CHAPTER 2 — Import and Check (5 min)

`docs/22` §4 T-03…T-06 · tabs: **import**, **check**

### Narration — part 1: the wizard

> "Import is four steps, and the third one is the one that needs you.
>
> **Choose the file.** It guesses the type from the structure. A guess, not a decision.
>
> **Pre-scan.** Before it reads a single row: how many rows, how many sheets, how long. A file that
> is going to hurt finds out now.
>
> **Map columns.** Green means matched. **Amber means it did not match and needs you.** This is the
> step where care is cheap and carelessness is expensive — if a column is mapped to the wrong field,
> every number below it is wrong, and the tool will not know. That is why amber is amber.
>
> **Validate.** A score out of a hundred, every check that ran, and for each failure, the rows that
> caused it."

### Narration — part 2: quarantine and commit

> "Two things before you commit.
>
> Rows the app could not use are not dropped. They go into **quarantine**, with the reason. You can
> open them, see them, and resolve them.
>
> And the commit summary: rows in, rows set aside, score. This is your last clean stop. After this
> it's a batch, and a batch can be voided — but it's tidier to stop here."

### Narration — part 3: the Check screen

> "The Check screen is the quality view. The score at the top is a summary, not a verdict. Below it,
> every check that failed and what caused it.
>
> Read it as: *how much do I trust what's underneath?* A high score doesn't mean the numbers are
> right — it means the checks passed. The judgement is still yours.
>
> One more thing, and it's important: **the app never writes to your source file.** It copies the
> file into the project folder and reads the copy. Your original is opened read-only."

---

# CHAPTER 3 — Analyse and drill (4 min)

`docs/22` §4 T-07 · tab: **analyse**

### Narration

> "This is budget versus actual, and there's one thing to notice before anything else.
>
> **It never shows a bare plus or minus.** It says *favourable* or *unfavourable*. A negative number
> on an expense line is good news; on a revenue line it's bad news. The tool knows which, so you
> don't have to carry that in your head at eleven at night.
>
> Sort by biggest adverse. And let me say the unhelpful but true thing: **biggest is not most
> important.** A large favourable variance on a line you expected is boring. A small one you cannot
> explain is worth a coffee.
>
> Now — click any figure.
>
> This is the drill-through. Source file, which import, which voucher lines. **Every number this tool
> shows you can be traced back to the rows it came from.** That is the property I'd argue for most,
> and it's the one a summary report can't give you.
>
> The bridge is the same story as a picture, for a pack that goes to someone who won't read the
> table. And where a ratio can't be computed — usually no prior period — you get `n/a`, not zero.
> Zero would be a lie you'd carry into a pack."

---

# CHAPTER 4 — Exceptions (4 min)

`docs/22` §4 T-08…T-10 · tab: **exceptions**

### Narration

> "Same principle, and I'll keep saying it: these are **potential** exceptions. A rule you agreed to
> matched. That is the entire claim. Not an error — a thing for a person to look at.
>
> Which makes the most valuable thing you do here a decision about what you're **not** looking at.
>
> The register filters by severity, owner, status and age. Ageing runs against a target — seven days
> for High, twenty-one for Medium, forty-five for Low. Something sitting at forty days and High is
> the conversation to have today.
>
> Open one and you get the evidence: which rule, what threshold, what the history is. **If you're
> going to challenge a flag — and you should — this is where you check whether the rule matched what
> you think it matched.**
>
> Change the status, and add a note. The note is permanent and it exports with the pack. So write it
> for the person reading it in six months with no memory of today. 'Checked with supplier, invoice
> valid, recurring.' Not 'ok.'
>
> And if a rule keeps raising things that aren't worth your time, tell us. That's the tool telling us
> the rule needs tuning. I'd rather tune ten rules honestly than have you filter around fifty."

---

# CHAPTER 5 — Forecast and commentary (5 min)

`docs/22` §4 T-11…T-14 · tabs: **forecast**, **ai**

### Narration

> "Forecasting. Actuals that are closed, periods still open. The tool picks a method per line and
> shows you which one it used and why. Lines that aren't eligible say so.
>
> You can override any cell. When you do, it asks for a reason, and it's mandatory.
>
> Now, honestly: **nobody checks that reason at the time you type it.** It exists so that three
> months later, when someone asks why this line looks different from what the method would have
> produced, there is an answer. Write the real reason. 'Q4 blackout, customer confirmed.' Not
> 'override.'
>
> Lock the version when you're happy. Locked means read-only, and it's what the issued pack points at.
>
> Then the commentary — the words that go on the slide.
>
> **The AI features are off by default.** In this sample there's no key, so what you're seeing is the
> app writing the text itself using rules. If you never add a key, that's what you get forever, at
> no cost and with no internet.
>
> If you do add one, anything AI-written arrives labelled **'AI draft — review before use.'** A
> draft. Not approved. It cannot go into anything you circulate until a person reads it and approves
> it. And there is **no send button anywhere in this tool** — you copy or download, and the sending
> is yours.
>
> Rule-written text is labelled differently again: **'Rule-based summary.'** The tool will never
> pretend a paragraph came from somewhere it didn't."

---

# CHAPTER 6 — Pack, issue and backup (4 min)

`docs/22` §4 T-15…T-20 · tabs: **reports**, **backup**

### Narration

> "Generate a pack and you get an Excel workbook and a slide deck — from the same numbers, so they
> can't disagree with each other.
>
> Two things to notice.
>
> **There are no formulas in the workbook.** It's values. Every number is fixed at issue, so it can't
> recalculate differently on your machine than on mine.
>
> **The disclaimer is on every sheet footer and on the deck.** It travels with the document. If you
> forward this to someone who's never met us, they still see it.
>
> Issuing freezes the numbers, the commentary and the statuses. The next version is version two;
> version one stays exactly as it was. When someone asks 'what did we send on the 3rd?', you have a
> frozen artefact, not a recollection.
>
> Finally, backup. It writes a plain zip — databases, archive, settings — with a manifest listing
> every file and its fingerprint.
>
> **It is not encrypted.** Anyone who can open that file can read the project. Store it somewhere
> protected, or let Windows encryption protect the disk.
>
> And **deleting a project does not delete your backups.** They're yours; the app never touches them.
> Deleting a project also isn't a secure erase — Windows Delete isn't a shredder. For a laptop that
> could be lost or stolen, ask your IT team for BitLocker."

---

# Closing card (hold on screen for the last 20 seconds)

> "This tool highlights **potential** exceptions, variances and trends for review. It does not
> provide audit, accounting, tax or legal advice, and it does not guarantee that every error,
> misstatement or irregularity will be detected. Every figure, flag and AI-generated draft must be
> reviewed by a qualified accountant before any business decision, filing or external reporting.
> The tool never posts, approves or alters accounting records.
>
> The trial works one way: **you run your own month, and you tell us what it missed.** Not us telling
> you it's complete."

---

## Production checklist

- [ ] Recorded on the sample project, at the state named in each chapter
- [ ] Every chapter's on-screen state matches the narration above
- [ ] No client data, no client name, no client branding anywhere in frame
- [ ] Disclaimer card captured (§15.2 requires it on the About screen — the recording carries it too)
- [ ] Runtime checked against the 22–28 minute target
- [ ] Chapter titles match the `docs/22` §4 task titles exactly, so the guide cross-references work
- [ ] `[BUILD NOTE]` items from `01_presenter_script_full_60min.md` re-checked against the build on
      the day of recording — **especially**: do not show the Diagnostics export button succeeding,
      and do not screen-share Settings → AI with a key configured

---

*Chapter structure and titles follow `docs/22` §10.2. Disclaimer text is `docs/01` §15.1, quoted
verbatim. No claim in these scripts was invented.*