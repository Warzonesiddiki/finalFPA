# Training narration pack — proposal for the lead

**Status:** proposals only. Not delivered, not merged.
**Format:** word-for-word presenter scripts for the 60-minute live session, against the
**sample project** only. No client data is used, referenced or required at any point.

---

## Files

| File | Covers | Minutes |
|---|---|---|
| `01_presenter_script_full_60min.md` | The whole session, word-for-word, in one document | 60 |
| `02_chapter_scripts_for_recording.md` | The six recorded-demo chapters, split out for filming | 6 × 3–5 |

`docs/22` §10.1 defines the seven time blocks; this pack follows them exactly. `docs/22` §10.2
defines the six recorded-demo chapters; `02_…` follows those exactly.

---

## How to use these scripts

**Read them as written the first time.** They are deliberately plain — short sentences, no jargon,
one idea per sentence. The audience is a finance analyst who has never seen the tool and who does
not care how it is built.

**The three rules the script enforces, which are the ones that matter:**

1. **A flag means "look at this", never "this is wrong."** The script says this in Block 1 and
   repeats it every time an exception is opened. It is the single most important sentence in the
   hour, because a finance team that misreads the output will stop trusting the tool.
2. **Never say the app is accurate, fast, or reliable.** The trainer says what the app *does* and
   what it *shows*. If someone asks "is it right?", the honest answer is the accuracy question in
   Block 6 — and it points at the acceptance evidence, not at a claim.
3. **Never promise a screen the build does not have.** Every click in these scripts is a click in
   the current UI. Where a documented screen is not built yet, the script says so out loud and
   offers the alternative — see the caveat below.

---

## ⚠ Read this before you deliver the session

**The screens exist, but two documented behaviours behind them do not yet.**

`docs/22` §9 defines **24 screenshot slots across 43 screens** (`SCR-001`…`SCR-043`). The current
shell (`ui/src/main.tsx:38`) registers **thirteen tabs** — `home`, `import`, `importhistory`,
`check`, `analyze`, `exceptions`, `forecast`, `reports`, `ai`, `settings`, `search`, `backup`,
`about` — plus a `GuidedTour` and a `HelpPanel`, wired at `main.tsx:262-317`. Every area Blocks 2–6
need is therefore reachable from the tab bar, and the scripts below click real tabs.

*Correction, recorded honestly:* I first wrote that the build was a four-tab app, taken from an
earlier `docs/SESSION_LOG.md` entry describing an intermediate state. Reading `main.tsx` directly
showed thirteen tabs. The earlier note was stale; this one is checked against the source.

**What the trainer must still handle** are two behaviours that are documented but not yet built,
both carried as `[BUILD NOTE]` lines in the scripts:

1. **Diagnostics export** (`app/api/main.py:1810`) returns a hard-coded filename and writes no
   file. Do not demonstrate it as a working feature. See `audit-external` finding R3.
2. **The AI key field** (`app/api/main.py:1431`) currently shows the last four characters of a
   stored key, which `docs/13` §5.2 forbids. Do not screen-share the Settings → AI area with a real
   key configured. See audit finding R1.

Neither is a reason to delay the session. Both are reasons to demo the **sample project** and a
**keyless** AI configuration, which is the documented default anyway (`docs/10` §3).

---

## What the trainer must have ready

| Item | Why | Source |
|---|---|---|
| The app installed and launched on the machine | You cannot train on a machine that needs a SmartScreen click-through in front of an audience | `proposals/client_comms/03_smartscreen_walkthrough_printout.md` |
| The **sample project** open and untouched | Every demo in this pack runs on sample data. Never on client data. | `docs/13` `SEC-007`; `docs/22` §9 |
| The user's guide printed, one per attendee | They will follow along in Blocks 2, 3 and 5 | `docs/22` |
| The support sheet printed | Hand it out in Block 1, not at the end — people lose it | `proposals/client_comms/04_support_sheet.md` |
| A timer you can see | Block 5 has a hard 10-minute stop; see the script | — |
| A way to reach support live during the session | Somebody will hit a real error in front of everyone | `docs/23` |

---

## Time is the constraint, and it is real

The documented outline fits 60 minutes exactly with **no slack**. In practice, the Blocks that
overrun are always the same two:

- **Block 2** — the import wizard has more steps than people expect, and the column-mapping step is
  where the questions come from.
- **Block 5** — the forecast override requires typing a reason, and someone will always ask whether
  the reason is checked.

**The script's cut-lines** (marked `[IF BEHIND]`) tell the trainer what to drop first. Dropping
the recorded-demo preview and the AI discussion is safe. Dropping the Block 6 accuracy explanation
is **not** safe — it is the answer to the hardest question in the room.

If the session starts late, cut Block 5's scenario comparison and the Block 7 real-month walkthrough
down to ten minutes rather than rushing Block 1. **The orientation is what stops the tool being
misread.**

---

## The one question you will be asked, and the answer to give

> *"How do we know it hasn't missed anything?"*

Do not answer "it checks everything." Answer:

> The rules are a list we have written down, and we have gone through that list with you line by
> line — which ones matter to your month, and which are deliberately off. The tool tells you which
> rules ran and what it saw. What it cannot tell you is that there is nothing outside those rules.
> That is why the acceptance test at the end of the trial month is you running your own month and
> telling us what it missed — not us telling you it is complete.

That answer is the honest one, it matches the advisory disclaimer, and it converts the trial into
the thing that will actually produce evidence. It is scripted in Block 6.

---

## Source of every claim

| Claim in the scripts | Source |
|---|---|
| The seven time blocks and their minutes | `docs/22` §10.1 — followed verbatim |
| The six recorded-demo chapters | `docs/22` §10.2 — followed verbatim |
| "Potential exception" means a person must judge it | `docs/06`; `docs/01` `P8`; `docs/22` §12 glossary |
| The advisory disclaimer wording | `docs/01` §15.1 — quoted verbatim in Block 1 |
| Where the data lives / what leaves the machine | `docs/13` §8.3, §10.3 — quoted verbatim in Block 1 |
| The five-step SmartScreen walkthrough | `docs/15` §8.3 — quoted verbatim in Block 1 |
| Delete-project is not a secure erase | `docs/13` §4.3 |
| AI is off by default; keyless fallback is rule-based | `docs/10` §3, `docs/13` §8.2 |
| "AI draft — review before use." | `docs/10` §12; `app/engine/ai/guardrails.py:31` |
| Aging targets 7/21/45 days by severity | `docs/22` §12 glossary |
| Support contact details | `docs/15` §9.3 — fill in before delivery |
| The thirteen current tabs | `ui/src/main.tsx:38` and `:262-317` — **corrected**: my first note said four tabs, taken from a stale `SESSION_LOG` entry describing an intermediate state; the source shows thirteen. |
| Diagnostics export is currently a stub | `app/api/main.py:1810-1819` — audit finding R3 |
| The AI key field currently shows the last four characters | `app/api/main.py:1431` — audit finding R1 |

**I have written no client name, no client data, no client brand, and no commercial claim anywhere
in this pack.**