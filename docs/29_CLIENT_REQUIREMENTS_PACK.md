> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** the **client-facing** statement of what is being built and what is being asked of
> the client (Addon 4 §E.1). Plain language, no requirement codes and no document numbers by design — the
> coded version lives in `20`; delivered as part of the handover pack (`23` §12).
> **TL;DR (≤ 15 lines):**
> - You are getting a **month-end analysis tool for one Windows laptop** that turns your three system
>   exports into a variance view, a triage list, a forecast refresh and a ready-to-issue Excel and
>   PowerPoint pack — **without** sending your data anywhere.
> - It **does not** touch your accounting system. It reads exports; it never posts, approves or changes a
>   single record.
> - **Nothing is calculated by AI.** The optional AI assistant writes *draft wording* from figures the
>   tool has already computed; you review, edit and approve every word. It is **off by default**.
> - **We need one sanitized real month as early as possible** — that single request unlocks the most.
> - **We need about a dozen decisions** (§7), each with a recommendation, so you can simply tick.
> - **Your files stay on your machine.** The tool runs offline; there is no server, no cloud account and
>   no usage tracking and nothing that reports back about how you work.
> - **Money is handled exactly**: whole rupees, no rounding drift, and every figure on a screen or a
>   slide ties back to the same transaction rows.
> - **Themes, not black boxes:** every exception rule is written down, threshold by threshold, in the
>   business terms you use today.
> - **You will be trained and supported**: a 60-minute session, a recorded walkthrough, a written guide
>   and a named person to call.
> - **We prove it works on your own month before go-live** — you reconcile the tool's output against your
>   current manual pack and sign the tie-out.
> - **You drive the acceptance test; we watch and fix.** No feature is "done" because we say so.
> - **Backups are plain zip files you own**; restore is tested with you on your machine before go-live.
> - **The advisory disclaimer** in §13 applies to every figure and every AI draft: this is an analysis
>   aid, and a qualified accountant reviews everything before it is used.
> - **What we ask you to sign now** is that your requirements are correctly understood (§14) — not that
>   the software is finished.
> - **Nothing changes silently.** After this pack is signed, any change to scope, wording or behaviour
>   comes to you first, with its cost and impact, for your decision.

# 29 — Client Requirements Pack

## 1. What this pack is (and what to do with it)

| Question | Answer |
|---|---|
| What is it? | A plain-English statement of what will be built for you, what it will not do, what we need from you and what you will be asked to sign — at three points, not once |
| Who should read it? | The finance owner who will use it or sponsor it; the person who prepares the month-end pack; whoever signs off on the finance side |
| How long is it? | About 20 minutes end to end; §7 and §8 are the two pages we need back |
| What do we need from you? | Your answers in §7 (many are a single tick), the items in §8, and the §14 sign-off block |
| What happens next? | Your answers are folded into the build plan; anything that changes scope gets an impact note back to you before any work starts |
| Where do the requirement codes live? | In the project's traceability and specification documents, deliberately not here — so this pack can be read without a decoder |
| Will this text change? | Only with a recorded reason; the version you sign is dated, and material changes re-open the sign-off |

## 2. Your month-end today, and what changes

| Your month-end today | With the tool |
|---|---|
| Three systems, three export shapes, hand-built workbooks | One import step per system, with a report that tells you what is wrong **before** any data is stored |
| Copy-paste and lookup formulas until the numbers tie | Every figure computed once by the analysis engine; every screen, workbook and slide reads the same numbers |
| Exceptions found late, if at all, because someone eyeballs a report | A written rule catalogue flags the usual problems (unusual spend, missing accruals, duplicate payments, budget pacing) with an owner and a status |
| A variance that looks wrong but takes an hour to trace | Click any variance and see the transactions behind it, down to the source file and row |
| The management pack rebuilt by hand every month | Excel and PowerPoint generated from the same analysis, in your house style, with a version number |
| A forecast rebuilt from scratch each cycle | A rolling forecast with the method, the overrides and the accuracy history kept together |
| "Which version did I send?" | An issuance register: every pack version, who received it and when |

> The promise is not "fewer accountants". It is: **the repetitive part of the month-end shrinks, so the
> review part gets the time it deserves.**

## 3. What you will be able to do — screen by screen, in one line

| What you see | What it does for you |
|---|---|
| Home | Shows your open projects and the last one you worked in |
| New project | Creates a month-end workspace in a folder you choose, with a sample project ready to explore |
| Import — choose file | You pick this month's export from any of the three systems (Excel or CSV) |
| Import — read-ahead | Looks at the file before anything is touched and tells you the sheets, columns and rows it found |
| Import — map columns | Remembers the file's shape so next month is a one-click confirmation; you can adjust any column |
| Import — check | Runs the written checks (totals, duplicates, dates, missing values) and shows plain-language problems |
| Import — confirm | Stores the data only when you accept the check summary; a failed import changes nothing |
| Import report | A one-page summary per file: rows, controls, warnings, and a data-quality score |
| BvA view | Budget versus actual by account, cost centre and period, with the biggest movements first |
| Bridge | Explains a variance movement by movement instead of leaving you to guess |
| Trends and KPIs | The handful of trends you actually present: month-on-month, year-on-year, run-rate, margin |
| Click-through | Any number opens the transactions behind it, down to file and row |
| Exceptions | A triage list with severity, owner, age and status, ready to send to the accounting teams |
| Forecast | Refresh the remaining months with the method of your choice; add an override and a reason where you disagree |
| Forecast accuracy | How last cycle's forecast actually performed, by period |
| Generate pack | Excel workbook and PowerPoint deck produced together, in your template and house style |
| Issue a version | Records the pack version, date and recipients, so "which version" is answerable |
| Commentary | Write or edit the month's narrative; if the AI assistant is on, it drafts and you approve |
| Settings | Thresholds, mappings, master data, branding, display and the AI switch in one place |
| Backup and restore | Take a backup before you close; restore is tested and documented |
| About and diagnostics | Version, storage health and a one-click diagnostic bundle for support |

## 4. A month with the tool

| When | What happens | Time |
|---|---|---|
| Day 1 — data | Export from the three systems, drop the files in, read the check report, accept | 20–30 minutes |
| Day 1 — close | Your normal close process continues in your systems; the tool is read-only throughout | — |
| Day 2 — review | Open the variance view, drill the movements you do not believe, work the exception list | 60–90 minutes |
| Day 2 — forecast | Refresh the rolling forecast, review the drivers, record any overrides with reasons | 20 minutes |
| Day 3 — pack | Generate the Excel and PowerPoint pack, adjust the commentary, issue the version | 20 minutes |
| Month end +1 | Open the accuracy view: how the last forecast performed against the month you just closed | 10 minutes |

## 5. What the tool does not do

| Boundary | Why it matters to you |
|---|---|
| It does not connect to your ERP or write anything back | It reads exports; nothing it does can alter a record, a journal or a balance |
| It is not an accounting system | No posting, no approval workflow, no ledger of record |
| It does not consolidate companies or entities into one set of books | One project covers one entity's analysis; group consolidation stays in your existing process |
| It covers the profit-and-loss view; it is not a balance-sheet or cash-flow tool | The job it was asked to do is the month-end P&L review |
| It is a single-user desktop tool, not a shared server | One person works in a project at a time; the file lives on one machine by design |
| It does not send anything automatically | No emails, no uploads, no scheduled jobs; you issue the pack yourself |
| It does not render PDFs internally | Excel and PowerPoint are the outputs; printing and PDF export stay in Office |
| It is not an audit or fraud-detection system | It flags patterns worth a look; it does not certify that nothing is wrong |
| It does not replace professional judgement | See the disclaimer in §13 |

## 6. What the AI assistant does — and does not do

| Aspect | Rule |
|---|---|
| Default state | **Off.** The tool is complete without it, and no key is required to use anything in §3 |
| If you turn it on | It writes **draft commentary and observations** from figures the tool has already calculated, and suggests which exceptions to look at first |
| It never computes | Every number comes from the deterministic analysis engine; the assistant has no calculator and no vote on any figure |
| It never decides | It cannot change data, set a threshold, approve an exception, close a period or issue a pack |
| It never sends | It cannot email or upload; drafts wait for a human to accept, edit or reject |
| Your data | Only the small extract you see on the drafting screen is sent to the provider **you** configure; nothing else, ever |
| You choose the provider | Any AI service you approve that uses the industry-standard interface (the same style as OpenAI), with your own account key; the key is stored protected on the machine and is never included in a backup |
| Review is mandatory | Every draft is marked as a draft until a person approves it, and the approved version is what appears in the pack |
| Turn it off later | One switch; the audit trail records that the feature was used, and nothing breaks when it is off |

## 7. Decisions we need from you

Each row is a decision, a recommendation and a space for your answer. If you agree with the
recommendation, write "agree" — that is enough.

| # | Decision | Why it matters | Our recommendation | Your answer / date |
|---|---|---|---|---|
| 1 | Which closed month is the trial "real month", and when can we have it sanitized? | It unlocks the closest-to-truth test and is the single biggest schedule dependency | The most recent closed month; files within two weeks of sign-off | |
| 2 | Which system each export comes from, and the exact columns it contains | The whole import path is built on these three files; a surprise mid-build is expensive | Send one sample file per system exactly as exported; we profile the columns and confirm the mapping with you in a one-hour walkthrough | |
| 3 | Fiscal calendar: year start, period count, period names | Every period label, window and comparison follows this | Calendar months with your existing period labels (for example 2026-P09) | |
| 4 | Prior-year data available, and in what form? | Enables prior-year comparisons and run-rate views | Provide the prior-year general-ledger extract if it exists; otherwise we ship without | |
| 5 | One reporting currency or several? And which units should the pack show? | Storage, mixed-currency handling and every displayed figure | One reporting currency per project; show whole rupees by default, switchable to lakhs | |
| 6 | How many budget versions exist, and how are revisions approved? | Import replaces, version labels and comparison views | One approved budget plus dated revisions, each kept as its own version | |
| 7 | Forecast cadence and the scenarios you actually use | Sets the default refresh cycle and the scenario set | Monthly refresh with base, best and worst cases | |
| 8 | Approval thresholds, and where the list comes from today | Sets the starting point for every amount-based exception rule | Start at ₹5,00,000 or 2 % of the budget line, whichever is greater, then tune after the trial month | |
| 9 | The recurring-cost list and the vendor master with categories | Drives the missing-cost and vendor-based rules, and owner assignment | Provide both; the tool maintains them from then on | |
| 10 | Who owns an exception by default? | Determines whether the triage list is worked or ignored | Auto-assign by vendor/cost category where possible; the analyst assigns the rest | |
| 11 | AI assistant: on or off for the first months? | A data-handling and support decision, not a technical one | Keep it off for v1; turn it on later with a written data-handling note | |
| 12 | Which Excel and PowerPoint examples define the house style? | Fonts, colours, slide order and the KPI set on the summary slide | Share one recent pack; we match what Excel and PowerPoint can reproduce reliably | |
| 13 | Product name, logo and two brand colours | App header, workbook cover and deck title slide | The finance function's own name and brand; provide the logo file and the colours | |
| 14 | Delivery channel for the installer, and whether to buy a signing certificate | Affects how the installer is distributed and whether an install-day security warning appears | Internal file share with a published fingerprint number; buy a certificate only if your policy blocks an unsigned installer | |
| 15 | Training format | Determines what is prepared and who attends | All three: a live 60-minute session, a recorded walkthrough and the written guide | |
| 16 | Support terms after go-live, and who is called first | Sets the response promise you can hold us to | The analyst calls the consultant directly for two month-ends; formal terms confirmed before go-live | |
| 17 | Retention and deletion expectations | Determines how long projects and backups stay, and what "delete" means | Keep 13 months of projects, delete means removed from disk, backups are yours to manage | |

## 8. What we need from you

| Item | Format | When | Why |
|---|---|---|---|
| Sanitized exports from all three systems, one month | The files as you would export them today, with anything sensitive replaced | As early as possible, before any build | The trial month proves the mapping and the numbers |
| Two further months of the same exports (optional but valuable) | Same format | With or after the trial month | Proves the tool handles month-to-month variation |
| A one-hour mapping walkthrough with the person who knows the files | A diary slot, screen share | Early | Column meanings, tricky sheets, business rules that live in someone's head |
| The approved budget workbook | Excel | Early | Budget versus actual is the core view |
| Prior-year general-ledger extract (if it exists) | Same export style | Early | Prior-year comparisons |
| Recurring-cost list and vendor master with categories | Excel or CSV | Before the exceptions work starts | Missing-cost and vendor rules |
| One recent Excel pack and one recent management deck | The files themselves, even PDF | Early | House style and slide layout |
| Brand assets: logo, two colours, any usage rules | Image files and colour values | Before the pack work starts | Branding inside the app and in the outputs |
| Your current threshold/approval list | Excel, or a conversation | Before the exceptions work starts | Rules start from your reality |
| Access and timing: a 2-hour install window, a named analyst for one day per month-end, an IT contact for install day, one week for acceptance testing, one tie-out session | Diary commitments and a named person per role | Booked two weeks ahead of each stage | Nobody's time is wasted waiting |
| Decision turnaround: 48 hours on §7 items | Email or a short call | Throughout | Decisions are the only thing that stops the build |
| The accounting-owner representative for the acceptance test | A named person | Before acceptance testing | They check that the exception wording would not mislead the business |

## 9. Timeline, in plain terms

| Stage | What happens | What you see | What we need from you |
|---|---|---|---|
| Now — requirements sign-off | This pack and the questionnaire are agreed | The signed §14 block and your §7 answers | Your answers and the trial-month files |
| Delivery-path test | We prove an installer can be built, installed and launched on a clean Windows machine before writing features | Nothing to review; a note confirming the path works | — |
| Build, in six stages | Import and checks → variance and drill-through → exceptions → forecast → Excel/PowerPoint packs → AI and polish | A short demonstration at the end of each stage, on sample data | Two hours per stage for the demonstration, and answers when asked |
| Trial month | Your real month run end to end; you reconcile the numbers against your current manual pack | The tie-out worksheet and a difference list, each item explained | The analyst's time for one tie-out session |
| Acceptance test | Five working days at most; you run the scripts, we watch and record | A running list of what is found, and fixes | The analyst plus the accounting-owner representative |
| Go-live | Installed on your machine, trained, backed up, restored once to prove it | A signed go-live checklist | Install window, IT contact, trainees |
| First two month-ends | Priority support while the tool proves itself in live use | Response within the agreed targets | Feedback, and the first accuracy review |

**About the dates.** The build plan is expressed in *ideal working days* — about **96 days of build**
across the six stages (roughly five months if nothing ever waits), plus the delivery-path test, the trial
month, the acceptance test and go-live. The honest driver of elapsed time is not the coding: it is file
access, answers and diary slots, which is why §7's first row is the month's data. We will give you a dated
plan once your §7 answers are in, and we will flag any schedule risk as soon as we see it, not at the end.

## 10. How we will prove it works

| Proof | What it means in practice |
|---|---|
| The trial month | Your own closed month, run end to end, reconciled to your current manual pack line by line |
| Every difference explained | Nothing is written off as "rounding"; each difference is classified and signed off by the analyst |
| The mapping frozen | Once the trial month ties out, the file mapping for your systems is locked and versioned |
| Acceptance test (five days) | You follow the written guide on the installed build; if the guide is not enough, that is a defect in the guide, and we fix it |
| A first-timer test | Someone who has never seen the tool installs it and completes a month-end using the written guide alone |
| Go-live rehearsal | The installation, backup, restore and rollback steps are rehearsed with your IT contact before the real day |
| Accuracy review | After the first live month closes, we review how the forecast performed and agree any change to the method |

## 11. Your computer and how it gets installed

| Aspect | Detail |
|---|---|
| Machine | Windows 11, 64-bit, 4- or 8-core processor, 16 GB memory, an SSD, and roughly 1.5 GB of disk space for the application (plus room for your projects and backups) |
| Install | Double-click the installer, click through; per-user install with no administrator rights required |
| What a security warning means | The installer is not code-signed for v1, so Windows may show a "Windows protected your PC" prompt; the steps to proceed safely and verify the file are in the written guide, and a signing certificate is decision 13 in §7 |
| Network | Not required to use the tool; you may keep the machine offline |
| Where your data lives | On that machine, under your Windows user profile — never in a cloud folder by default, never on our systems |
| Updates | Manual in v1: you are told a new version exists and given the file plus a fingerprint number so you can check it arrived unchanged; nothing updates itself |
| Uninstalling | Removes the application; your project folders and backups are yours and stay where you put them |

## 12. Care and feeding: backups, retention and support

| Topic | Plain statement |
|---|---|
| Backups | One click creates a **normal zip file** of the project. Anyone who can open the zip can read it, so store it somewhere protected — for example on an encrypted drive |
| Restore | Tested with you before go-live; a backup restores into a **new empty folder**, never over the top of a live project |
| Retention | You own the retention decision; the tool never deletes a backup, and a project is deleted only when a person confirms it |
| Support — first line | Your analyst contacts the consultant directly, with the diagnostic bundle the tool produces and one sentence on what happened |
| What you get back | A written answer: what happened, what to do now, and what will change and when |
| Response expectations | A same-day response for anything that blocks the month-end, and a written plan within two working days; the other levels are agreed in decision 15 of §7 |
| Escalation | Anything that is not resolved at first line goes to the engineer who built it; you are told who is on point and by when |
| Learning loop | A problem that appears three times becomes a change to the product or a written decision — never a workaround you have to remember |

## 13. Advisory disclaimer

This wording appears in the application, in the generated packs and here, and it is the wording that
governs how the outputs may be used:

> **Advisory tool — not professional advice.**
> FP&A Month-End Copilot is an analysis aid. It highlights **potential** exceptions, variances, and
> trends for review. It does **not** provide audit, accounting, tax, or legal advice, and it does
> **not** guarantee that every error, misstatement, or irregularity will be detected. All figures,
> flags, and AI-generated drafts must be reviewed by a qualified accountant before any business
> decision, filing, or external reporting. The tool never posts, approves, or alters accounting
> records, and it never replaces professional judgement.

## 14. Sign-off — requirements understood and agreed

Signing this page means: the description in §1–§13 matches what you expect, the decisions and asks in §7
and §8 are the right ones, and the boundaries in §5–§6 are acceptable. It does **not** mean the software
is accepted — that happens at the trial month, the acceptance test and go-live.

```
CLIENT REQUIREMENTS — SIGN-OFF
Client: <organisation>          Project: <project name>
This pack version: v<version>   Date presented: <date>
We confirm that the requirements described in this pack are understood and agreed, subject to
the open decisions listed in §7 and the change process in §15.
Open decisions at signature: <ids or "none">            Target response date: <date>
Signed: <client sponsor, role> ...................... Date: <date>
Signed: <finance owner, role>  ...................... Date: <date>
For the project: <consultant, role> ................. Date: <date>
```

## 15. Feedback and changes after sign-off

| Rule | What it means for you |
|---|---|
| Nothing changes silently | Any change to scope, wording, a rule, a screen or a behaviour is described to you first, with what it affects and how big it is |
| Small changes | Made with a note in the change log; no ceremony |
| Large changes | Come to you with an impact note — what it affects, what it costs in time, and what would have to move — for your decision before any work starts |
| New ideas | Welcome, and always given a written entry with the trigger that would bring them into a future version; they do not silently enter this one |
| Scope is protected on purpose | The tool you agreed to is the tool that gets built; ideas are not lost, they are scheduled |
| Your data and branding stay yours | Your files, logo and colours are used inside your installed build only, and your data never leaves your machine |
