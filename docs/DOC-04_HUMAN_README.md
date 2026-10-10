# README — FP&A Month-End Copilot

**What it is**: A desktop tool for FP&A analysts that turns month-end export files into a variance analysis,
an exception list, a rolling forecast, and an Excel + PowerPoint pack — all from the same numbers, on your
machine, with no account, no cloud, and no internet required.

**What it is not**: An accounting system, an ERP connector, a multi-user server, a certified/audited
system, or a substitute for professional judgement. It reads exports; it writes nothing back to any system.

**Who it is for**: The FP&A analyst who spends a week each month copying numbers between exports, workbooks,
and slides, and who would rather spend that week reviewing variances and exceptions.

---

## In one paragraph

You export your GL and sub-ledgers as Excel or CSV at month-end. You drop the files into this tool. It
reads each file, checks it (totals, duplicates, dates, missing values), and shows you a data-quality score
and a list of problems in plain language — before it stores anything. You accept the check summary and it
commits the data atomically (all or nothing).

Then you open the Budget vs Actual view, sorted adverse, and click any variance to see the transactions
behind it — down to the source file and row. The bridge chart walks from budget to actual through the top
drivers. The exception list flags the things worth a human look: unusual spend, missing accruals, duplicate
payments, budget pacing — each with an owner, a severity, an age, and a status.

You refresh the rolling forecast (run-rate, prior-year, budget, or driver-based), add an override with a
reason where you disagree with the method, and write the commentary — optionally starting from an AI draft
that you must approve before it appears anywhere.

One click generates the Excel workbook and the PowerPoint deck in your house style, with a version number.
You issue the pack, which freezes the period's snapshot and records who received it.

The whole flow, on a normal month, is 30–60 minutes of app work after the first month is set up. The
numbers are deterministic: the same files always produce the same result. The screen, the workbook, and the
deck all show the same number.

---

## What you need to run it

- **Windows 11**, 64-bit, 4- or 8-core processor, 16 GB memory, an SSD.
- **Excel and PowerPoint** installed (to open the outputs — the tool does not render PDFs).
- **No administrator rights** required for install or use.
- **No internet** required (except optionally, if you choose to enable the AI assistant with your own key).

The installer is under 500 MB. Peak memory during a 250k-row import is under 1.5 GB.

---

## First launch

1. Run the installer (or unzip the portable package and run the app).
2. The app opens on a **sample project** — invented data, clearly marked "SAMPLE DATA" on every screen.
   Nothing you do here touches your own files.
3. Take the 6-step first-run tour (Home → Import → Check → Analyse → Exceptions → Reports), or dismiss it.
4. **Your first backup** (one time, takes a minute): Settings → Backup & restore → choose a folder. The
   backup is a plain zip of your project. Store it somewhere protected — it is not encrypted by the tool.

---

## A month-end, step by step

### 1. Start the new period

Home → **New period**. The wizard opens the next unopened period, shows the fiscal calendar, and lists the
files it expects this month (GL, payroll, procurement/bank — whatever your setup is). It carries forward
mappings, thresholds, and master data — never numbers. Click **Open period**.

### 2. Import each file

For each file: Import → **Choose file** (drag it in or browse). Six short steps:

1. **Choose file** — pick the file; the app guesses the source type.
2. **Pre-scan** — it reports rows, sheets, and an estimate before touching anything.
3. **Sheet & header** — pick the sheet and the header row; a preview shows real column names.
4. **Map columns** — check the suggested mapping; each field is green (matched) or asks you to choose.
5. **Validate** — wait for the checks; a list of pass/fail with a data-quality score; failures name the rows.
6. **Commit & confirm** — read the summary, click Commit. The whole file commits or none of it does.

Repeat for each file. The other two systems use the same six steps with a different source type.

### 3. Review quarantined rows (if any)

If a commit summary shows quarantined rows: Import history → the batch → **Quarantine review**. Each row
shows the reason in plain language with the source location. Fix the source file and re-import, or resolve
the row as excluded. Nothing was silently dropped.

### 4. Check the data

Click **Check** in the left menu. Read the data-quality score and the failed-check list. Each failed check
names what it compares and which files are missing or mismatched. Click a failed check to see the offending
rows. Do not proceed to analysis until the checks you care about pass.

### 5. Analyse

**Budget vs Actual** (sorted adverse) is the main view. The window selector switches between MTD, YTD, PY
MTD, PY YTD, and TTM (trailing 12 months). Click any variance to drill to the transactions behind it — the
sum of those transactions equals the variance exactly.

**Bridge** walks from budget to actual through the top-N drivers plus an "Other" bar.

**Trends** shows month-on-month and year-on-year lines. **KPIs** shows the headline ratios (gross margin %,
opex %, etc.) — each with its formula and a hover reason for `n/a` values.

**Three-way** shows Actual vs Budget vs Forecast in one view, with Forecast vs Actual signed error for closed
periods.

### 6. Review exceptions

**Exceptions** is a triage list with severity, owner, age, and status. Open one to see the rule that raised
it, the threshold used, the subject, the amount, the evidence, and the status history. Change a status (Open
→ In Review → Explained → Corrected → Closed), add a note (append-only, with history), assign an owner, or
export the evidence bundle.

### 7. Refresh the forecast

**Forecast** → refresh with the method of your choice. If the method is ineligible (no history, first
period, locked period), it shows a greyed line with the reason. Add an override with a reason where you
disagree. Switch scenarios (Base / Best / Worst). Open **Forecast comparison & accuracy** to see how last
cycle's forecast performed.

### 8. Write commentary and generate the pack

**Commentary** → write the month's narrative. If AI is on, start from a draft (labelled "AI draft — not
approved"); edit it; approve it. Then **Reports → Generate pack** → choose Excel, PowerPoint, or both → click
Generate. Open both in Office. Check the numbers match the screen (they will — the cross-artifact equality
test asserts it).

### 9. Issue and back up

**Pack issuance register** → issue the version: it records the version, date, recipients, and the file
names, and freezes the period's snapshot. Then **Backup & restore** → back up the project. Done.

---

## Where your data lives

By default, your projects live under `%LOCALAPPDATA%` — never inside OneDrive or a synced folder (which can
corrupt open databases). You can see the exact folder in Settings → Data & storage. You can move it to
another local folder. You can back it up to any local or network folder.

Deleting a project asks you to type its name and offers a pre-delete backup. The tool never deletes a
backup — retention is yours.

---

## When something looks wrong

| What you see | What it usually means | What to do |
|---|---|---|
| A column wasn't found | The export's headers changed | Map the column; the new mapping is saved as a version |
| Rows under Quarantine | A few rows could not be read | Review them; nothing was silently dropped |
| The score dropped | A source is missing or a file is for the wrong period | Fix the import; the failed-check list names the source |
| A number differs from the old spreadsheet | Rounding/display, or a different date basis | Drill to the source rows; compare to the source file |
| An exception looks wrong | The threshold or master data behind it | Note it, then report it; rules are tuned between months |
| The forecast shows grey lines | Those lines are ineligible | Read the note on the line |
| The app closed unexpectedly | A crash — recovery is automatic | Reopen; the last committed work is there |
| Windows warns about the installer | The app is new and unsigned | Follow the walkthrough; never disable Defender |

The full list is in `docs/DOC-07_CLIENT_AUDIT_QnA.md` (the twenty questions a controller will ask) and
`docs/22_END_USER_GUIDE.md` (the full user guide, with screenshots).

---

## How it works (briefly, for the curious)

- **Numbers are exact.** The engine uses Python's `Decimal` for all money arithmetic — no floating point,
  no rounding until display. The same input always produces the same output.
- **Imports are atomic.** A file is staged, validated, and only committed when you accept the check summary.
  A crash or cancel never leaves a partial batch.
- **Exceptions are rules.** 24 written rules, each with a defined logic, threshold, and severity. The tool
  tests itself against 32 planted exceptions and 8 precision controls (cases that must not raise) on
  generated sample data. The current run finds all 32, fires 0 controls, finds all 18 High-severity cases,
  and has 17 extra findings (none from a rule with more than 3).
- **The pack is the analysis.** Excel and PowerPoint are generated from the same in-memory analysis the
  screen shows. A test asserts they all agree at display precision.
- **The AI is optional and off by default.** When on, it drafts commentary from figures the engine already
  calculated. It has no calculator, no vote on any figure, and cannot change data. Every draft is labelled
  and must be approved.
- **Nothing leaves your machine.** No telemetry, no cloud, no account. The only outbound connection is the
  optional AI provider you configure with your own key, and then only a redacted summary of the visible screen.

---

## Sample data and templates

The sample project is bundled with the app and is the safest way to learn the flow. It is watermarked on
every screen and in every export, and it cannot mix with your data.

Blank import templates (Excel) are available from inside the app: Import → **Download blank template**, or
Home → **Download blank template**. Templates are available for: actuals, budget, forecast, and master data
(vendor categories, recurring costs, approval thresholds). The downloaded file is the same as the shipped
template, including the template version stamp.

---

## Getting help

Three ways:

1. **Help panel** — the **?** at the bottom of the left menu opens the topic for the screen you are on.
2. **This README** and **docs/22_END_USER_GUIDE.md** — the full task-by-task guide.
3. **Support** — create the diagnostics zip (About / Diagnostics → Create diagnostics zip) and send it to
   your support contact with one sentence on what happened. The zip contains logs, versions, and settings —
   no project data, no numbers, no key.

---

## Upgrading

The app checks your project's schema version on open and migrates if needed (with a backup prompt first).
If the project is newer than the app, it refuses to open with a message. The upgrade-over-previous-version
path is tested as part of the E2E suite.

Updates in v1 are manual: you are told a new version exists and given the file plus a checksum so you can
verify it arrived unchanged. Nothing updates itself.

---

## Uninstalling

The uninstaller removes the application. Your project folders, backups, and exports stay where they are.
If you want to remove everything, delete the project folder (after a final backup, typed confirmation
required).

---

## The honest limits (read this once)

- **Single user, one machine.** No multi-user, no server, no shared access. If the machine is shared, the
  machine's own access control is the only barrier.
- **Reads exports, writes nothing back.** No ERP connection, no posting, no journal entry. If a number in
  the export is wrong, the tool's output is wrong in the same way.
- **Analysis aid, not a certified system.** The tool flags patterns worth a human look. It does not audit,
  certify, or replace judgement. The advisory disclaimer appears in the app, the packs, and the client pack.
- **The AI is a drafter, not a calculator.** It writes text from numbers the engine already has. It does not
  produce numbers.
- **Forecast is a projection, not a prediction.** Its reliability depends on the method, the data, and the
  overrides. The tool shows the method and inputs; it does not certify the forecast.

These limits are not shortcomings to fix quietly — they are the boundaries that make the tool's promises
honest. If a limit matters to you, say so; it may be a decision to record, a backlog item to schedule, or a
boundary to accept.
