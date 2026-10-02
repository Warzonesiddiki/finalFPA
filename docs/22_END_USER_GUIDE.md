> **Status:** Draft v0.1
> **Last updated:** 2026-10-02
> **Owning FRs/areas:** the **user-facing manual** — task-structured, plain language, keyed to `SCR-nnn`, and
> the **single source of help text** for the in-app Help panel (`FR-ONB-004`/`FR-ONB-007`); training outline
> and screenshot contract (Addon 1 §C.1/§K, `Q-017`)
> **TL;DR (≤ 15 lines):**
> - **User-centric manual:** Task-oriented documentation for finance analysts covering monthly close, variance triage, and reporting.
> - **Screen-by-screen walk:** Clear visual walkthroughs across all 43 user interface screens and guided workflows.
> - **Plain-language error help:** Diagnostic guide mapping error messages to immediate, actionable user remediation steps.
> - **Offline & privacy guidance:** Explains local-only storage, backup procedures, and optional AI privacy boundaries.
> - **First-run onboarding:** 15-minute tutorial guiding first-time users through the pre-loaded fictional sample project.

# 22 — End-User Guide

## 1. How to use this guide

### 1.1 Who it is for, and what it assumes

| Item | Detail |
|---|---|
| Reader | The FP&A analyst (primary), the accounting owner, and anyone who generates or reads the monthly pack |
| Assumes | Windows 11, Excel and PowerPoint installed, no technical knowledge, no training in the app |
| Does not assume | Any knowledge of databases, Python, APIs, FP&A tooling, or the documents in this repository |
| Language | Plain English, present tense; the same words as the screen (`08` §16.1 wording lint) |
| Length of the month-end flow | 30–60 minutes of app work for a normal month, after the first month is set up |

### 1.2 The five-minute version

1. **Open the app.** It reopens your last project (`FR-ONB-006`) and shows **Home** with the current
   period and its status.
2. **Start the new month** — Home → **New period**. The wizard lists the files it expects.
3. **Import** each file: Home → **Import**, or drag the file onto the window. Six short steps; nothing is
   saved until the final **Commit**.
4. **Check** — the score and the failed-check list tell you whether the data is fit to analyse.
5. **Analyse** — Budget vs Actual, bridge, trends, top variances. Click any figure to see the
   transactions behind it.
6. **Review the exceptions** the engine raised; each one tells you what it noticed and what to do next.
7. **Refresh the forecast** for the rest of the year and choose a scenario.
8. **Write the commentary** (optionally start from an AI draft, then edit and approve it).
9. **Generate the pack** — Excel and the management deck — then **Issue** it, which freezes the period's
   snapshot and records who received it.

> Screens are named in this guide the way the left-hand menu names them: **Home, Import, Check,
> Analyse, Exceptions, Forecast, Reports, Settings** (`08` §3.1). The order never changes.

### 1.3 Conventions used in this guide

| Convention | Meaning |
|---|---|
| **Bold text** | A button, menu item, field label or screen name you click or type into |
| `SCR-nnn` | The support name for the screen (e.g. `SCR-015` is *Analyse — BvA matrix*). Quote it in a support call |
| Steps | Numbered; each step is one action. If a step has a sub-choice, it is written as a bullet |
| ✓ Checkpoint | What you should see if the step worked — the place to stop if it did not |
| If it looks wrong | The most likely cause and the exact next action (§7 has the full list) |
| Read more | The document and section that owns the detail (for the consultant, not the user) |

### 1.4 Three ways to get help

| Way | When to use it | Where |
|---|---|---|
| **Help panel** | You are on a screen and want to know what it does | The **?** at the bottom of the left menu (`SCR-042`); it opens the topic for the screen you are on |
| **This guide** | You want to do a task from the beginning | §4 — find your task, follow the steps |
| **Support** | Something failed, or the numbers look wrong | §7.4 — send the diagnostics zip to your support contact |
| **What’s New** | You installed an update and want the short list of changes | Open `whats-new.md` delivered beside the installer; it is plain-language release guidance from `24` §10.1 |

## 2. Installing and first run

### 2.1 Installing (including the Windows warning)

1. Save `Setup-FPandAMonthEndCopilot-<version>.exe` and `SHA256SUMS-<version>.txt` from the link your
   contact sent you, into the same folder.
2. **Check the fingerprint (recommended).** Open a terminal in that folder and run
   `certutil -hashfile "Setup-FPandAMonthEndCopilot-<version>.exe" SHA256`. The long string must match
   the one in `SHA256SUMS-<version>.txt`. **If it does not match, stop and contact us — do not run the
   file.**
3. Double-click the installer. If Windows shows the blue **"Windows protected your PC"** box, follow
   the walkthrough below — it is expected for a new app and does not mean the file is harmful.
4. The installer asks for no administrator rights and no network; when it finishes, the app opens
   automatically and starts on the **sample project** (`FR-ONB-001`).

**The Windows warning, word for word** (`15` §8.3 — this text is reused verbatim in `29` and checked by
`TST-SEC-19`):

> **When Windows shows a blue "Windows protected your PC" box**
> This happens because the app is new and not yet a "known" download; it does **not** mean the file is
> harmful. To continue:
> 1. Click **More info**.
> 2. Check that the app name is **FP&A Month-End Copilot** and that the version matches what you were told.
> 3. Click **Run anyway**.
> 4. If your browser warns that the file *"isn't commonly downloaded"*, choose **Keep** — then run the file.
> **Check the file's fingerprint first (recommended).** Right-click the downloaded file → **Properties** →
> *Digital signatures*/*File hashes* are not shown for unsigned files, so instead compare the SHA-256 we
> sent you using this command in a terminal:
> `certutil -hashfile "Setup-FPandAMonthEndCopilot-<version>.exe" SHA256`
> The long string that appears must match the one in `SHA256SUMS-<version>.txt`. If it does not match, stop
> and contact us — do not run the file.
> **Never** do these things: do not turn off Defender or SmartScreen, do not run the installer "as
> administrator" if Windows does not ask for it, and do not ignore a warning that names a **different**
> file or publisher than the ones above.

> If your organisation blocks the installer, use the **portable package** instead (`15` §4.3): unzip it
> anywhere and run the app; nothing is written outside your user folder. If WebView2 is missing, the app
> tells you and offers the documented fallback (`15` §6.3).

### 2.2 First launch: the sample project and the tour

| Step | What happens | What to do |
|---|---|---|
| 1 | The app opens on the **sample project** — invented data, clearly marked | Look around; nothing you do here touches your own files |
| 2 | A **SAMPLE DATA** banner stays visible on every screen (`FR-ONB-008`) | This is how you know you are not in a client project |
| 3 | The **first-run tour** (`SCR-043`) offers 6 steps (Home → Import → Check → Analyse → Exceptions → Reports) | Take it once; it is skippable and never reappears after you dismiss it (`FR-ONB-002`) |
| 4 | **Download blank template** is offered on Home and in Import | Use it if you are unsure what your file should look like (`FR-ONB-005`) |

**SAMPLE DATA can never mix with your data:** a sample project carries a project-type flag, is
watermarked in every export, and is refused entry to a client project (`FR-ONB-008`, `FR-XC-013`).

### 2.3 Where your data lives

*"The app works completely offline. Nothing is sent anywhere unless you switch AI on, add your own key,
and press an AI button — in that case, a small redacted summary goes to the AI service you chose. The app
never sends your files, your data or your key anywhere else."* (`13` §8.3, `SEC-039` — used verbatim in
`29`.)

| Fact | Detail |
|---|---|
| Location | Your projects live under `%LOCALAPPDATA%` by default — **never** inside OneDrive/SharePoint, which can corrupt open databases |
| How to see it | **Settings → Data & storage** (`SCR-032`) shows the exact folder; **About / Diagnostics** (`SCR-040`) repeats it |
| Moving it | You may choose another **local** folder; a synced folder is allowed only with a warning |
| Deleting | Deleting a project asks you to type its name and offers a pre-delete backup first (§4 T-19) |

### 2.4 Do this once: your first backup

1. Open **Settings → Backup & restore** (`SCR-039`) or Home → **Back up**.
2. Choose a destination folder (any local or network folder; a synced folder gets a warning).
3. The backup is a plain zip named `<Project>_<YYYY-MM-DD-HHMM>.zip`.

> **Plain-language warning shown in the app:** *"This backup is a normal zip file — anyone who can open
> the file can read the project. Store it somewhere protected, or let Windows protect the folder."*
> (`13` §9.2.) The app **never deletes a backup**; retention is yours.

## 3. The month-end rhythm

The nine steps below are the order the app is built around (`01` §4.1). The right column is the task in
§4 that walks you through it.

| # | Step | Screens | Task |
|---|---|---|---|
| 1 | Open the new period | `SCR-001`, `SCR-004` | T-02 |
| 2 | Import the month's files | `SCR-005`–`SCR-010` | T-03, T-04 |
| 3 | Validate and reconcile | `SCR-006`–`SCR-014` | T-05, T-06 |
| 4 | Analyse budget vs actual | `SCR-015`–`SCR-022` | T-07 |
| 5 | Investigate potential exceptions | `SCR-023`–`SCR-026` | T-08, T-09, T-10 |
| 6 | Refresh the rolling forecast | `SCR-027`, `SCR-028` | T-11, T-12, T-13 |
| 7 | Produce the pack | `SCR-029`, `SCR-031` | T-14, T-15, T-16 |
| 8 | Issue and archive the period | `SCR-030`, `SCR-004` | T-17, T-18 |
| 9 | *(before you close the laptop)* | `SCR-039` | T-19 |

> **Numbers never carry forward. Only setup does.** Mapping profiles, master data and settings carry to
> next month; last month's imported numbers are never reused (`01` §4.1 step 9).

## 7. When something goes wrong

### 7.1 The error dialog, explained

Every error path uses the same three-part shape (`08` §16.1), in this order:

| Part | What it tells you | Example |
|---|---|---|
| **What happened** | One sentence, naming the object — no jargon, no codes as the headline | *"Column 'Cost Center' wasn't found in sheet 'GL_Export'."* |
| **What was not lost** | The assurance, in plain words | *"Nothing was imported. Your project and previous months are unchanged."* |
| **One action** | The single recommended next step (plus optional secondary links) | *"Map it now, or download the current template."* |

A **Copy details** button copies the technical text (a code such as `ERR-IMP-011`, versions, and the log
location) — your data is never included beyond identifiers. Technical codes appear in the details area
only, never as the message.

### 7.2 The ten things that most often look like problems

| What you see | What it usually means | What to do |
|---|---|---|
| Windows warns about the installer | The app is new and unsigned | Follow §2.1; never disable Defender |
| "Another copy is already open" | A second window on the same project | Close the other window; your work is safe |
| A column wasn't found | The export's headers changed this month | Map the column in step 4; the new mapping is saved as a version |
| Rows appear under **Quarantine** | A few rows could not be read (date, number, missing key) | Review them (T-05); nothing was silently dropped |
| The score dropped | A source is missing, or a file is for the wrong period | Fix the import; the failed-check list names the source |
| A number differs from the old spreadsheet | Rounding/display differences, or a different date basis | Compare drill-through to source lines; see §5 |
| An exception looks wrong | The rule's threshold or the master data behind it | Note it, then report it; rules are tuned between months |
| The forecast shows grey lines | Those lines are ineligible (no history, first periods, locked period) | Read the note on the line; it names the reason |
| The pack took longer than usual | A very large period or a big exception list | Wait for the progress bar, or cancel and narrow the scope |
| The app closed unexpectedly | A crash — recovery is automatic | Reopen: the last committed work is there; uncommitted form edits are re-offered (`FR-XC-008`) |

### 7.3 Offline, autosave and recovery

- **Offline is normal.** The app needs no network. With the network off, every task in §4 works, including
  pack generation (`NFR-007`).
- **Autosave:** forms and grids save as you commit them; killing the app mid-edit never loses a
  **committed** change, and the app offers to restore an uncommitted form edit (`FR-ONB-006`).
- **After a crash or power loss:** reopen the app — long jobs are marked *interrupted* rather than left
  half-done, and imports are all-or-nothing (`FR-XC-008`).

### 7.4 Sending a problem to support

1. **Create the diagnostics zip** — About / Diagnostics (`SCR-040`) → **Create diagnostics zip**.
2. **Write one line about what you were doing** (the screen `SCR-nnn` helps).
3. **Send the zip to your support contact.** It contains logs, versions and settings — **no project data,
   no numbers, no key** (`13` §7.1/§7.2).

> **Support flow (default, `Q-018`):** the analyst contacts the consultant first; the consultant escalates
> if needed. The agreed warranty/support terms are confirmed with the client before go-live (`OQ-016`).

## 8. Settings a user may change

| Setting | Screen | Who should change it | Safe? |
|---|---|---|---|
| Display: currency label, units (whole/thousands/lakhs), negatives, decimals | `SCR-036` | Anyone — display only | Reversible; no numbers change |
| Thresholds and rule on/off | `SCR-035` | The finance owner | Changes what is flagged; every change is versioned and shown in the audit trail |
| Master data: vendor categories, recurring costs, approval thresholds | `SCR-034` | The finance owner or analyst | Rules that need the data relax with a visible notice until it is loaded |
| Mapping profiles | `SCR-033` | The analyst | Versioned with history and revert; never destroy an earlier version |
| Branding: product name, logo, two colours | `SCR-037` | The project owner | Contrast is checked; an unreadable colour pair is refused |
| AI provider and key | `SCR-038` | Whoever owns the AI decision | Off by default; the key is encrypted and never logged |
| Data folder, backups, archive-and-delete | `SCR-032` | Whoever owns the machine | Moving the folder does not move existing projects — the dialog says so |

## 9. Screenshots: the capture contract

The guide ships with screenshots of the **sample project** (Addon 1 §K). Screenshots are captured **after
the screens are built**, from the sample project only, and every slot below must be filled before UAT
(`TST-UAT-04`/`05` read the guide on a fresh machine — a slot that is still empty fails the pass).

| Rule | Detail |
|---|---|
| Source | The bundled sample project, at the state named in the slot — never a mock, never a design file |
| Never | Client data, real vendor names, real amounts, an unreleased build, a half-populated screen |
| Capture | 1366×768 minimum, 100 % scaling, English, the app maximised, the relevant panel focused |
| Annotation | At most three numbered call-outs per image, matching the step numbers in the task |
| Naming | `docs/help/img/<SCR-nnn>-<state>-<n>.png` (e.g. `SCR-008-mapped-1.png`) |
| Redaction | None needed: the sample project's data is invented; if a real name ever appears, re-capture |
| Freshness | A screenshot is re-captured when its screen's wording or layout changes (`FR-ONB-007` test) |

| Slot | Screen | State to capture | Must show | Used in |
|---|---|---|---|---|
| SS-01 | `SCR-001` | Home with a period open, partly imported | Period chip, file checklist, quick actions | T-01, T-02 |
| SS-02 | `SCR-004` | New Period wizard, step 1 | Period code and file checklist | T-02 |
| SS-03 | `SCR-005` | Choose file, file selected | Source-type guess and size | T-03 |
| SS-04 | `SCR-006` | Pre-scan finished | Rows, sheets, time estimate | T-03 |
| SS-05 | `SCR-008` | Map columns, greens and one amber | Matched/needs-choice states | T-03, T-04 |
| SS-06 | `SCR-009` | Validate, one failed check expanded | Score, check result, offending rows | T-03, T-06 |
| SS-07 | `SCR-010` | Commit summary | Row count, score, next actions | T-03 |
| SS-08 | `SCR-013` | Quarantine review with three rows | Reasons and Resolve action | T-05 |
| SS-09 | `SCR-011` | Import history, three batches | Statuses including a voided batch | T-05 |
| SS-10 | `SCR-014` | Check with score and failed checks | Score plus failures; coverage line | T-06 |
| SS-11 | `SCR-015` | BvA matrix sorted adverse | Window header, favourable/unfavourable words | T-07 |
| SS-12 | `SCR-021` | Drill-through from a figure | Source file, batch, voucher lines | T-07 |
| SS-13 | `SCR-016` | Bridge chart | Waterfall with a drilled bar highlighted | T-07 |
| SS-14 | `SCR-020` | KPI cards with one `n/a` | `n/a` with its reason on hover | T-07, §5 |
| SS-15 | `SCR-023` | Exception register filtered to High | Severity, owner, age, status | T-08 |
| SS-16 | `SCR-024` | Exception detail with history | Evidence, threshold used, status history | T-09 |
| SS-17 | `SCR-025` | Evidence bundle modal | Scope choices and expected file name | T-10 |
| SS-18 | `SCR-027` | Forecast workspace with an override | Computed vs override value and reason | T-11, T-12 |
| SS-19 | `SCR-028` | Scenario comparison | Two scenarios side by side, accuracy block | T-13 |
| SS-20 | `SCR-031` | Commentary with an AI draft | *AI draft — not approved* label and Approve action | T-14 |
| SS-21 | `SCR-029` | Generate pack | Artifact choices and scope | T-15, T-16 |
| SS-22 | `SCR-030` | Issuance register with one issued version | Version, recipients, file names | T-17 |
| SS-23 | `SCR-041` | An error dialog (a staged, harmless one) | The three parts and Copy details | §7.1 |
| SS-24 | `SCR-042` | Help panel open on a task | Topic text matching this guide | T-21, §11 |

## 10. Training outline (60 minutes, and the recorded demo)

### 10.1 The live session (default: 60 minutes, on the sample project — `Q-017`)

| Min | Block | What happens |
|---|---|---|
| 0–5 | Orientation | What the app is and is not (§6); the monthly rhythm (§3); where their data lives (§2.3) |
| 5–15 | Import and check | Live import of a sample GL file by the trainer; then **the user does one themselves** |
| 15–25 | Analyse and drill | Find the biggest variance, drill to transactions, read the bridge |
| 25–35 | Exceptions | Triage, open one, move a status, export evidence |
| 35–45 | Forecast and commentary | Refresh, override with a reason, write one comment, approve it |
| 45–55 | Pack and issue | Generate Excel and the deck, open both, issue a version on the sample project |
| 55–60 | Their real month | Walk the file checklist together; agree who does what on day one |

### 10.2 Recorded demo outline (for people who cannot attend)

Six chapters, one per screen area, 3–5 minutes each, recorded on the sample project: (1) Home and the
period, (2) Import and Check, (3) Analyse and drill, (4) Exceptions, (5) Forecast and commentary, (6) Pack,
issue and backup. Chapter titles match the §4 task titles so a viewer can jump straight to the guide.

### 10.3 The first-hour checklist (hand this to a new user)

- [ ] Installed and opened the app (§2.1) and seen the sample project
- [ ] Took the 6-step tour, or dismissed it knowingly
- [ ] Imported one file of their own (in a **new project**, not the sample)
- [ ] Read the data-quality score and explained one failed check out loud
- [ ] Found a variance and drilled to the transaction
- [ ] Opened an exception, changed a status, added a note
- [ ] Refreshed the forecast and typed one override with a reason
- [ ] Generated a pack and opened it in Excel
- [ ] Made a backup and found the folder it went to
- [ ] Knows the three ways to get help (§1.4)

## 11. In-app help and the single-source contract

| Rule | Detail |
|---|---|
| One source | The Help panel (`SCR-042`) and this guide render the **same topic text**, keyed by task and screen (`FR-ONB-007`) |
| Topic shape | Every topic has three parts: **What this is for** · **What to do here** (the steps) · **Where to go next** |
| Coverage | Every screen in the inventory (`08` §4, 43 screens) has a topic; a screen without one fails a test |
| Wording | The `08` §16.1 lint applies to help text exactly as to dialogs: no codes as headlines, no jargon, one action |
| Freshness | Changing a task's steps here updates the panel in the same change; a doc-hygiene test detects divergence |
| What it is not | The panel is not a bug tracker and holds no client facts; anything project-specific lives in this guide's §2–§4 |

## 12. Plain-language glossary of on-screen terms

| Term you see | What it means |
|---|---|
| **Period** | One month of the fiscal year (e.g. `FY26-P09`), which can be open or closed |
| **Batch** | One import of one file, with its own status and history |
| **Quarantine** | Rows the app could not use; they are kept and explained, never dropped |
| **Data-quality score** | A 0–100 summary of how well the imports passed their checks |
| **Variance** | Actual minus budget (with favourable/unfavourable shown), never a bare plus/minus |
| **Window** | The period range you are looking at: MTD, YTD, PY MTD, PY YTD or TTM |
| **Drill-through** | Clicking a figure to see the transactions behind it |
| **Potential exception** | Something a rule noticed that deserves a person's judgement — not a proven error |
| **Owner** | The person responsible for an exception |
| **Aging** | How long an exception has been open, compared with its target (7/21/45 days by severity) |
| **Provenance** | Where a number came from (file, batch, line) |
| **Snapshot** | The frozen picture of a period when the pack was issued |
| **Stale** | A result is out of date because something it depends on changed |
| **AI draft** | Text an AI wrote for you to edit — never approved, never printed until you approve it |
| **Diagnostics zip** | The one file support needs; contains logs and settings, not project data |

## 13. Obligations this document places elsewhere

| Owner | Obligation |
|---|---|
| `08` | Every screen keeps a help topic; wording changes to a screen update the topic and this guide in the same change |
| `10` | AI output stays labelled *draft — not approved* until a human approves, exactly as §4 T-14 describes |
| `11`/`12` | The units, rounding, favourable/unfavourable and disclaimer conventions in §5/§6 are rendered identically in the artefacts |
| `13` | The privacy sentence (§2.3) and the diagnostics contents (§7.4) stay verbatim-copyable |
| `15` | The SmartScreen walkthrough (§2.1) is reused verbatim; changes land here in the same pass |
| `23` | Owns the support detail behind §7.4 and the consultant-side procedures |
| `28` | UAT runs the guide-only test (`TST-UAT-04`/`05`) with the screenshot slots filled (§9) |
| `29` | Reuses §2.1, §2.3 and §6 verbatim so the client pack and this guide cannot disagree |
| `14` | Owns the divergence test between the help source and this document (`FR-ONB-007`) |

## 14. Change control for this document

1. **Task steps change only with the screen**: a UI change updates `08` and this guide in the same commit.
2. **Wording here is user-facing wording**: it obeys the `08` §16.1 lint and is copy-checked (`TST-SEC-19`
   for the reused blocks).
3. **Screenshots are evidence**, not illustration: a slot is filled only from a real capture (§9); a stale
   capture is a defect, not a nicety.
4. **The guide is completed as built** (Addon 1 §C.1): this outline is frozen now; every task gains its
   screenshots and its final screen names at UAT, and the divergence test keeps it aligned with the Help panel.
5. Additions are `CHANGELOG`-recorded; the task numbering (`T-nn`) is append-only.

## 15. Frozen constants and conventions in this document

| Constant | Value | Source |
|---|---|---|
| Task register | `T-01`…`T-21`, append-only, mapped to the nine rhythm steps | §3, §4; `01` §4.1 |
| Screens named | `SCR-nnn`, exactly as `08` §4 | §4 |
| Screenshot register | `SS-01`…`SS-24`, filled only from the sample project | §9 |
| Help topics | One per screen (43), under the single-source contract | §11, `FR-ONB-004`/`007` |
| Training default | 60-minute live session + six-chapter recorded demo | §10, `Q-017`, `18` `A16` |
| Support default | Analyst → consultant; diagnostics zip only | §7.4, `Q-018` |
| Reused verbatim | SmartScreen walkthrough (`15` §8.3), privacy sentence (`13` §8.3), disclaimer (`01` §15.1) | §2/§6 |
| Reading-the-numbers rules | Units, rounding, `n/a`, `—`, favourable, stale | §5, `05` §6/§11 |
| Wording lint | `08` §16.1 (no codes as headlines, one action per message) | §7.1, §11 |

### 4.0 Where each screen is covered (the 43-screen check)

Use this to find the task for a screen, or to confirm that a screen has no separate task because it is a
modal, an overlay or a settings surface. (Screen purposes: `08` §4.)

| Screen | Task(s) | Screen | Task(s) |
|---|---|---|---|
| `SCR-001` Home | T-01, T-02, T-18 | `SCR-023` Exceptions register | T-08 |
| `SCR-002` Project launcher | T-01 | `SCR-024` Exception detail | T-09 |
| `SCR-003` New Project wizard | T-01 | `SCR-025` Evidence bundle (modal) | T-10 |
| `SCR-004` New Period wizard | T-02, T-18 | `SCR-026` Rule effectiveness | T-08 |
| `SCR-005` Import 1 — Choose file | T-03, T-04 | `SCR-027` Forecast workspace | T-11, T-12 |
| `SCR-006` Import 2 — Pre-scan | T-03 | `SCR-028` Forecast comparison & accuracy | T-13 |
| `SCR-007` Import 3 — Sheet & header | T-03, T-04 | `SCR-029` Reports — Generate pack | T-15, T-16 |
| `SCR-008` Import 4 — Map columns | T-03, T-04 | `SCR-030` Pack issuance register | T-17 |
| `SCR-009` Import 5 — Validate | T-03, T-06 | `SCR-031` Commentary editor | T-14 |
| `SCR-010` Import 6 — Commit & confirm | T-03, T-04 | `SCR-032` Settings — Data & storage | §2.3, T-19 |
| `SCR-011` Import History | T-05 | `SCR-033` Settings — Mappings | T-04 (tip) |
| `SCR-012` Batch detail / validation report | T-05, T-06 | `SCR-034` Settings — Master data | T-08, §8 |
| `SCR-013` Quarantine review | T-05 | `SCR-035` Settings — Thresholds & rules | T-08, §8 |
| `SCR-014` Check | T-06 | `SCR-036` Settings — Display & locale | §5, §8 |
| `SCR-015` Analyse — BvA matrix | T-07 | `SCR-037` Settings — Branding | §8 |
| `SCR-016` Analyse — Bridge | T-07 | `SCR-038` Settings — AI | T-20, §8 |
| `SCR-017` Analyse — Trends | T-07 | `SCR-039` Backup & restore | §2.4, T-19 |
| `SCR-018` Analyse — Top-N | T-07 | `SCR-040` About / Diagnostics | T-21, §7.4 |
| `SCR-019` Analyse — Three-way | T-07 | `SCR-041` Error dialog (global) | §7.1 |
| `SCR-020` Analyse — KPIs | T-07 | `SCR-042` Help panel (global) | §1.4, T-21, §11 |
| `SCR-021` Drill-through | T-07 | `SCR-043` First-run tour overlay | §2.2 |
| `SCR-022` Search | T-07 | — | — |

## 4. Tasks

Each task is self-contained: when to do it, the steps, what you should see, what to do if it looks wrong,
and where the consultant-level detail lives. Tasks marked **(first month only)** are setup you do once.

### T-01 — Open the app and find your project (`SCR-001`, `SCR-002`)

**When:** any time you sit down to work.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Double-click the app. It reopens your **last project** automatically | **Home** appears with the period chip (e.g. *FY26-P09 — Open*) |
| 2 | To switch projects, click the project name (top-left) → **Project launcher** (`SCR-002`), or create one with **New project** (`SCR-003`) | Your recent projects are listed with their last-opened date |
| 3 | If the project is on another drive or was restored, choose **Open another project** | A folder picker appears; the project opens and is added to the recent list |

- **If it looks wrong:** if the app says another copy is already open (`FR-PRJ-006`), close the other
  window — this is a guard, not an error; nothing is lost.
- **Read more:** `FR-ONB-001`, `FR-ONB-006`, `FR-PRJ-001`/`002`; `08` §5–§6.

### T-02 — Start a new month (`SCR-001`, `SCR-004`)

**When:** once the previous month has been issued (or you are starting a period you have not opened yet).

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | On **Home**, click **New period** | The New Period wizard opens on the next unopened period |
| 2 | Confirm the period code and dates | The wizard shows the fiscal calendar you set up in T-01 (January start by default) |
| 3 | Read the **file checklist** the wizard shows | It lists the sources it expects this month, e.g. *D365 GL, Payroll summary, Procurement/bank ledger* |
| 4 | Choose whether to carry forward last month's mapping profiles and settings (recommended: yes) | The summary shows what will be carried; **nothing numeric is carried** |
| 5 | Click **Open period** | Home now shows the new period as **Open** with **0 of 3 files imported** |

- **If it looks wrong:** a source you do not recognise means a mapping profile names something your team
  does not produce — tell your support contact rather than working around it (the profile is a one-line fix).
- **Read more:** `FR-PRJ-004`/`005`, `FR-SET-005`; `08` §6.3.

### T-03 — Import a file (the six-step wizard) (`SCR-005`–`SCR-010`)

**When:** for every file, every month.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | **Import → Choose file.** Drag the file in, or use **Browse** | The file name and size appear; the app guesses the source type (GL, payroll, other) |
| 2 | **Pre-scan.** Wait a moment | Rows, sheets and an estimate of the time are shown; very large files ask for confirmation first |
| 3 | **Sheet & header** (`SCR-007`). Pick the sheet and the header row | A preview shows real column names as they will be read |
| 4 | **Map columns.** Check the suggested mapping | Each target field is green (matched) or asks you to choose a column; your last-used mapping is pre-filled |
| 5 | **Validate.** Wait for the checks to finish | A list of checks with pass/fail and a **data-quality score**; failures name the rows and the reason |
| 6 | **Commit & confirm.** Read the summary, then click **Commit** | The batch is saved atomically — either the whole file or none of it (`FR-IMP-016`); the summary offers the next actions |

**What good looks like:** every required field matched, no required check failed, quarantined rows shown as a
count you can review (T-05), and the commit summary states the row count and the score.

- **If it looks wrong:**
  - *A column is missing* → the app names the column and the sheet, and offers **Download blank template**.
  - *Numbers look like text* → values are still parsed (accounting formats, `1.234,56`, brackets for minus);
    check the **Validation** step's per-check results rather than the raw preview.
  - *Nothing is saved when you cancel* → correct: cancel and crash are safe; the batch is not committed.
- **Read more:** `04` §3/§6–§11, `FR-IMP-001`–`030`; `08` §7.

### T-04 — Import the other two systems (`SCR-005`–`SCR-010`)

**When:** straight after T-03, once per file.

Same six steps as T-03. The only difference is the **source type** you pick in step 1: *Payroll summary* or
*Procurement / bank ledger* (or whatever names your setup uses). These files are reconciled against the GL
automatically in the **Check** screen (T-06).

- **Tip:** if a file arrives with extra columns each month, import once more with the new column mapped —
  the profile is versioned, and last month's mapping is never destroyed (`FR-IMP-026`).
- **Read more:** `04` §2/§5, `FR-IMP-002`/`010`.

### T-05 — Review and resolve quarantined rows (`SCR-013`, `SCR-011`, `SCR-012`)

**When:** whenever a commit summary or the Import screen shows quarantined rows.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Import → Import history**, then the batch | The batch shows *staged*, *committed* or *voided*, with row counts |
| 2 | Click **Quarantine review** | Only the rows that could not be used are listed — **nothing was silently dropped** |
| 3 | Read the reason on a row (e.g. *booking date could not be read*) | Each reason is one sentence in plain language with the row's source location |
| 4 | Fix the source file, or accept the row as excluded | **Resolve** removes it from the list (and records the decision); the rest of the batch stays committed |
| 5 | Re-import the corrected file if you chose to fix it | A new batch appears; the old one stays in history with its counts |

- **If it looks wrong:** a whole import that is wrong can be **voided** from the Import History screen
  (`FR-IMP-025`); voiding keeps the audit trail and removes its numbers from analysis.
- **Read more:** `04` §11/§18, `FR-IMP-013`/`025`; `08` §7.8.

### T-06 — Check the data before you trust it (`SCR-014`)

**When:** after every import, before you analyse.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Click **Check** in the left menu | A single **data-quality score** (0–100) with its biggest contributors |
| 2 | Read the **failed checks** list | Each failed check names what it compares and which files are missing or mismatched |
| 3 | Click a failed check | The offending rows, batches or sources are listed; **Open in Import** jumps to the batch |
| 4 | Confirm the **coverage** line | It shows which accounts/entities have budget and actuals — gaps here become *coverage* exceptions (T-08) |

- **The score is never shown alone** (`05` §8.2): it always comes with the failed-check list, so a high
  score cannot hide a broken import.
- **If it looks wrong:** a low score right after a clean import usually means a missing source (one file
  not imported yet) or a stale file for the wrong period. Fix the input, not the score.
- **Read more:** `04` §16/§17, `05` §8, `FR-IMP-014`/`022`; `08` §8.

### T-07 — Explain a variance (`SCR-015`–`SCR-022`)

**When:** every month — this is the heart of the job.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Analyse → BvA matrix** (`SCR-015`) | Budget, actual, variance and variance % by account, with the window selector (MTD / YTD / PY MTD / PY YTD / TTM) |
| 2 | Choose the window and, if needed, an entity or cost centre | The header always states the window and its exact date range |
| 3 | Sort by the biggest **adverse** variance (or click **Top variances**, `SCR-018`) | The largest unfavourable movers are at the top with favourable/unfavourable labels, not just signs |
| 4 | **Click any figure** to drill through (`SCR-021`) | The transactions behind the number appear, with their source file and batch |
| 5 | Use **Bridge** (`SCR-016`) to see how budget becomes actual | The waterfall shows the movers in order; every bar drills through as well |
| 6 | Use **Trends** (`SCR-017`) for the shape over months, **KPIs** (`SCR-020`) for ratios and **Three-way** (`SCR-019`) to see actual, budget and forecast together | Ratios that cannot be computed show **n/a** (never a misleading zero) |
| 7 | Search (`SCR-022`) for a voucher, vendor, account or description | Results open the same drill-through view |

- **Why a number may differ from your old spreadsheet:** rounding is display-only (the stored value is exact),
  totals are the sum of stored values and may not equal the sum of the rounded figures — the footnote says
  so (§5).
- **Read more:** `05` §2–§7/§11–§13, `FR-BVA-001`–`016`; `08` §9.

### T-08 — Find and triage potential exceptions (`SCR-023`, `SCR-026`)

**When:** after T-06/T-07, before the forecast.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Exceptions** (`SCR-023`) | The register lists every potential exception with severity, owner, age and status |
| 2 | Filter by severity, owner, status or rule | Counts update live; **High** items are the ones with a 7-day target (§7 of `06`) |
| 3 | Read the **rule effectiveness** screen (`SCR-026`) if your team reviews rule quality | Per-rule stats and suggestions appear only when there is enough history; otherwise the screen says so |
| 4 | Select several rows and use **Bulk act** where the same verdict applies | One audit event is written per exception — bulk never hides individual decisions |
| 5 | Export what you see when a colleague needs the list | The exported file matches the screen exactly (`FR-XL-010`) |

- **Wording matters:** the app says *"Potential exception — requires accounting review."* It never claims an
  error (`06` §1.1).
- **Read more:** `06` §2, `FR-EXC-001`–`004`/`010`/`015`; `08` §10.1/§10.3.

### T-09 — Work an exception to closure (`SCR-024`)

**When:** when you are ready to judge a specific exception.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Click a row in the register | The detail opens with the evidence (amounts, voucher, dates, the rule and the threshold used) |
| 2 | Check the **history** panel | Every raise, flag-again and change is listed with who and when — nothing is overwritten |
| 3 | Move the status: **Open → In review → Explained → Corrected → Closed** (or **Not applicable** with a reason) | Each move asks for a note where the rules require one; the change is recorded |
| 4 | Add a note or attach the explanation | Notes appear in the history and travel into the pack's evidence bundle |
| 5 | If you disagree with the rule, note it and tell your support contact | Rule precision is tuned between months, never by editing the data |

- **The app cannot move a status by itself** (`06` §2.3): only a person changes a verdict, and a closed
  exception is never reopened silently.
- **Overdue is a target, not an alarm:** aging targets are 7/21/45 days by severity; the register highlights
  overdue items but takes no automatic action.
- **Read more:** `06` §2.3–§2.5, `FR-EXC-005`–`009`; `08` §10.2.

### T-10 — Export an evidence bundle (`SCR-025`, `SCR-024`)

**When:** when an auditor, the accounting owner or a colleague asks for the working.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | From the exception detail or the register, choose **Export evidence** | The evidence-bundle modal opens (`SCR-025`) |
| 2 | Choose the scope (this exception, the filtered list, or all open) | The dialog states the file it will produce and an estimated size |
| 3 | Click **Create** | A workbook (and a zip when attachments exist) is written to your Exports folder; the file name names the exception |

- **Read more:** `11` §6 (`XL-009`), `FR-EXC-016`, `FR-XL-007`.

### T-11 — Refresh the forecast (`SCR-027`)

**When:** after the actuals are settled.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Forecast** (`SCR-027`) | The workspace shows the forecast for the eligible lines with the method chosen for each |
| 2 | Read the **method guidance** panel | It explains, in one line per line-group, why that method was chosen; it is advice, not a block |
| 3 | Click **Refresh forecast** | The forecast is recomputed; a progress indicator appears for large projects and can be cancelled |
| 4 | Choose the **scenario** you need (Base / Best / Worst) | Switching scenarios never changes another scenario's numbers |

- **Forecast integrity:** actuals are never overwritten by a forecast; locked periods are never
  re-forecast (`07` §10, `FR-FC-005`).
- **If it looks wrong:** a greyed line with a note means the line is ineligible (no history, first periods,
  or a locked period) — the note says which.
- **Read more:** `07` §3–§7, `FR-FC-001`–`009`; `08` §10.4.
### T-12 — Override a forecast line, and lock a version (`SCR-027`)

**When:** your judgement differs from the mathematical method (a contract, a one-off, a known change).

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Find the line in the forecast grid and double-click the cell | The cell opens for editing, showing the computed value beside your override |
| 2 | Type the new value and a one-line reason | The reason is required — an override without a reason is not accepted |
| 3 | Press Enter | The cell shows the override marker; the computed value stays visible for comparison |
| 4 | Use **Lock version** when a scenario is agreed | Locking freezes that version; later refreshes create a new version instead of changing the locked one |

- **Every override is recorded** with who, when, the old value, the new value and the reason (`FR-FC-004`), and
  it appears in the forecast provenance export.
- **If it looks wrong:** if a cell refuses an edit, the period is closed or the version is locked —
  reopen the period with a reason (T-18) or create a new version.
- **Read more:** `07` §7/§9–§10, `FR-FC-004`–`006`; `08` §10.4.

### T-13 — Compare scenarios and read accuracy (`SCR-028`)

**When:** before you write the commentary, and each month when you review how good last month's forecast was.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Forecast → Comparison & accuracy** (`SCR-028`) | Scenarios sit side by side; the forecast version and date are stated |
| 2 | Switch between Base / Best / Worst | The comparison keeps the same lines and periods, so differences are like-for-like |
| 3 | Read the **accuracy report** for closed periods | It shows actual vs forecast by period and by method — the evidence for changing a method next month |

- **Read more:** `07` §8.1, `FR-FC-007`/`008`; `08` §10.5.

### T-14 — Write the commentary (`SCR-031`)

**When:** after the analysis is agreed and before generating the pack.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Reports → Commentary** (`SCR-031`) | The editor lists the lines that need a comment (the biggest movers first) and the executive summary |
| 2 | Write per-line comments in your own words | Each comment is saved with a version, so a rewrite never destroys an earlier draft |
| 3 | *(Optional)* press **Draft with AI** on a line or the summary | A draft appears clearly labelled **AI draft — not approved**; it cites the numbers it used |
| 4 | Edit the draft, or reject it | Your edit is the comment; an unapproved draft is never printed in the pack |
| 5 | Press **Approve** on each comment you will publish | Only approved comments appear in the Excel pack and the deck |

- **The AI never decides, computes, applies or sends anything** (§6, `10` §2). It cannot invent a number
  that is not in the pack data, and it never writes into an approved field.
- **If it looks wrong:** a draft that misreads the business is fixed by editing the input line, not by
  arguing with the model — tell your support contact if it repeats, and tune the prompt (`10` §4).
- **Read more:** `10` §2/§5/§12, `FR-AI-004`/`005`/`014`; `08` §11.3.

### T-15 — Generate the Excel pack (`SCR-029`)

**When:** once actuals and exceptions are reviewed and commentary is approved.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Reports → Generate pack** (`SCR-029`) | Artifact choices, the period, the entity scope and the scenario are on one screen |
| 2 | Choose **Excel pack** and the parts you need | The dialog states which sheets will be created and any cap that will split a sheet |
| 3 | Click **Generate** | Progress appears; on a normal project this takes seconds, not minutes |
| 4 | Click **Open** when it finishes | The workbook opens in Excel; the cover sheet carries the stamp block and the disclaimer footer |

- **Files are values only** — no formulas to break, and the file name follows
  `<Project>_<Entity>_<Period>_MonthEnd_<vN>.xlsx` (`11` §3.4).
- **Every regeneration makes a new version** (`v1`, `v2`, …); the previous draft is kept, never overwritten.
- **Read more:** `11` §3–§7, `FR-XL-001`–`009`; `08` §11.1.

### T-16 — Generate the management deck (`SCR-029`)

**When:** after the Excel pack is right, or when only the deck is wanted.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | In **Generate pack**, choose **PowerPoint deck** | The six-slide structure is listed (cover, executive summary, bridge, top variances, exceptions, forecast) |
| 2 | Confirm the period, entity and scenario | The same choices as the Excel run are pre-filled, so the two artefacts agree |
| 3 | Click **Generate** | The deck appears in the same `Exports\<project>\<period>\` folder as the workbook |
| 4 | Open it and edit freely in PowerPoint | Everything is native PowerPoint: text boxes, shapes and charts — no placeholders that break |

- **The deck is editable on purpose** (`12` §3.2): fix a wording, move a box, hide a slide — nothing
  breaks, and a later **Refresh** updates the numbers without destroying your edits it can map.
- **If it looks wrong:** a very large deck warns at 15 MB and fails at 25 MB with a suggestion (`12` §8).
- **Read more:** `12` §2–§8, `FR-PPT-001`–`009`; `08` §11.1.

### T-17 — Issue the pack (`SCR-030`)

**When:** when the pack has been reviewed and is ready to send.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Open **Reports → Issuance register** (`SCR-030`) | The pack's version and the period's status are shown |
| 2 | Click **Issue pack** | The app freezes the period snapshot, increments the pack version and locks the commentary |
| 3 | Type the **recipients** (names, as plain text) | Recipients are recorded in the register; the app itself **never sends anything** |
| 4 | Send the files the way your team normally does (email, Teams, shared folder) | The register now shows the issued version with its file names and the recipients you typed |

- **Issuing is the line in the sand:** the issued snapshot will not change, even if you import a correction
  later — you would issue a **new version** instead (`FR-XC-002`/`003`).
- **Read more:** `FR-PRJ-010`, `FR-XC-002`/`003`; `08` §11.2.

### T-18 — Close the period (`SCR-001`, `SCR-004`)

**When:** after the pack is issued.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Go to **Home** and click the period chip | The period panel opens with its status and history |
| 2 | Click **Close period** | A summary lists what was imported, what remains open (e.g. exceptions) and what closing changes |
| 3 | Confirm | The period shows **Closed**; imports, re-imports and edits now require an audited **reopen** |
| 4 | *(If you must change something)* Click **Reopen**, give a reason | The reason is recorded in the audit trail; the period returns to **Open** |

- **Closing is reversible, but visibly so.** Nothing is deleted; the reason for a reopen is part of the
  period's history (`FR-PRJ-005`).
- **Read more:** `FR-PRJ-005`, `FR-PRJ-010`; `08` §6.3.

### T-19 — Back up, restore, and free space (`SCR-039`, `SCR-032`)

**When:** back up at least once a month (before closing is a good habit); restore only when moving or recovering.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | **Settings → Backup & restore** (`SCR-039`) → **Back up now** | A zip is written to the folder you choose; the dialog states it is a plain zip |
| 2 | To move or recover, choose **Restore from backup** | The app validates the file's manifest and hashes, then restores into an **empty** folder — it never merges into an existing project |
| 3 | To reclaim space, open **Settings → Data & storage** (`SCR-032`) | Storage used is broken down (databases, raw files, snapshots); **archive raw files** can shrink a project while keeping the numbers |
| 4 | To delete a project, use **Delete project** | You must type the project name and a pre-delete backup is offered first (`FR-PRJ-012`) |

- **Read more:** `13` §4.3/§9.2, `15` §7, `FR-PRJ-008`/`009`/`011`/`012`.

### T-20 — The AI assistant: what it does and never does (`SCR-038`, `SCR-031`)

**When:** only if your organisation wants it. **It is off by default and stays off until someone switches
it on and adds a key.**

| Topic | The rule in plain language |
|---|---|
| What it can do | Draft commentary in the words of your data, suggest a column mapping, and answer "what does this screen do?" |
| What it never does | It never calculates a number, never changes data, never moves an exception's status, never approves anything, never sends anything |
| What leaves the machine | Only when you press an AI button: a small **redacted** summary (numbers and labels, no full rows, no vendor names unless allowed in Settings) |
| The key | Stored encrypted for your Windows account (`DPAPI`); it is never logged, never included in backups or diagnostics |
| If it is switched off | Every AI button disappears and the rule-based suggestions still work (`FR-AI-008`) |

- **Read more:** `10` §2–§4/§6/§14, `13` §8, `FR-AI-001`–`014`; `08` §12.

### T-21 — Get help, and report a problem (`SCR-042`, `SCR-041`, `SCR-040`)

**When:** any time.

| Step | What you do | ✓ Checkpoint |
|---|---|---|
| 1 | Press the **?** at the bottom of the left menu | The help panel opens on the topic for the screen you are on — the same text as this guide |
| 2 | If a red dialog appears, read its three parts | It says what happened, what was **not** lost, and the one recommended action (§7.1) |
| 3 | Click **Copy details** in the dialog if you will report it | Technical details are copied to the clipboard for support — they never include your data beyond identifiers |
| 4 | Still stuck? **About / Diagnostics** (`SCR-040`) → **Create diagnostics zip** | One file is created containing logs, versions and settings (no project data, no secrets); send that file to your support contact |

- **Support flow (agreed default, `Q-018`):** the analyst contacts the consultant first; the consultant
  escalates if needed. The diagnostics zip is the only file support needs (`23`).
- **Read more:** `13` §7, `15` §9, `FR-XC-005`/`012`, `FR-ONB-004`.

## 5. Reading the numbers

| What you see | What it means |
|---|---|
| **Favourable / unfavourable** | Colour and word — not just plus/minus. For revenue, above budget is favourable; for cost, above budget is unfavourable |
| **n/a** | The number cannot be computed (e.g. no budget to compare against) — it is never shown as 0 % |
| **—** | Nothing to show (e.g. zero budget and zero actual). It is not an error |
| **Units** | Whole rupees by default; thousands/lakhs are display-only choices and the unit is always labelled |
| **Rounding** | Stored amounts are exact; rounding happens only for display. Totals are the sum of stored values, so a total may differ from the sum of the rounded figures — the footnote says so (`05` §6.2) |
| **Data-quality score** | A 0–100 summary of the import checks, always shown with the failed-check list (T-06) |
| **Stale indicator** | A results area marked *stale* means something it depends on changed; run the suggested refresh |
| **Threshold in an exception** | The exact rule and threshold that raised it is always shown on the exception, even after settings change |

## 6. What the app never does

| Never | Because |
|---|---|
| Post, approve, alter or delete accounting records | It is an analysis aid, not a ledger tool (`01` §15.1) |
| Guarantee that every error is found | Rules find **potential** exceptions; judgement stays with people (`06` §1.1) |
| Send the pack, email anyone, or phone home | There is no send path; the update check is manual and off by default (`FR-XC-015`) |
| Render PDF itself | It prepares the workbook for printing and offers *Open for printing / Save as PDF* (`DEC-028`) |
| Net off entities or eliminate intercompany | Grouped totals are labelled *Simple sum — no eliminations* (`FR-BVA-014`) |
| Edit budgets | Budgets are imported; a re-import replaces a version atomically (`DEC-003`) |
| Use AI unless a person switches it on and presses an AI button | AI is optional and off by default (`10` §2) |
| Deliver sample data with the app's numbers as if real | Sample data is watermarked and never mixes with client data (`FR-XC-013`) |

**The disclaimer you will see on the pack, the deck and the About screen:**

> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and
> trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does
> **not** guarantee that every error, misstatement, or irregularity will be detected. All figures,
> flags, and AI-generated drafts must be reviewed by a qualified accountant before any business
> decision, filing, or external reporting. The tool never posts, approves, or alters accounting
> records, and it never replaces professional judgement. (`01` §15.1 — quoted verbatim everywhere)
