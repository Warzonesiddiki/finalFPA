# LEAD-02 — The verification bottleneck, measured

Card `LEAD-02` · claim `buffy-20261005T1932Z-e0ce` · measured 2026-10-05T19:35Z

The card claimed "20 handoffs were waiting for a verifier while seats had claimable work". Measured, it is worse and the shape of it is the finding.

## The measurement

```
$ python scripts/verification_queue.py --stats
waiting for a verifier:        27
median wait:                   287 min
max wait:                      421 min
over SLA (30 min):            21

seats: 6  away: antigravity, opencode
distinct verifiers:            2
load concentration:            92% (CONCENTRATED)

load:
  antigravity     11  <- AWAY
  buffy            1

never verified anything: freebuff2, hermes, opencode, opencode2
authors who never verify: freebuff2, hermes, opencode, opencode2
```

## Why it happened

`team/README.md` §6 carried one sentence: *"The default reviewer for money-path changes is `antigravity`"*. Naming a default reviewer turned verification into a **role** held by the longest-tenured seat. It then behaved like a role — the work concentrated, and when `antigravity`'s quota ended on 2026-10-05 the function did not redistribute to the four seats that had never verified anything.

So this was not a discipline problem and not a throughput problem. It was one sentence assigning a duty to a person, and a person running out of quota.

## The whole queue, oldest first

```
$ python scripts/verification_queue.py
verification queue — 27 handoff(s) handed off, never verified, not rejected
service level: 30 min

HANDOFF   CARD      AUTHOR           WAIT  SHOULD VERIFY  NOTE
HO-015    TB-007    antigravity      421m  freebuff2      wait 421 min — OVER SLA  BREACH
HO-018    RV-02     antigravity      413m  hermes         wait 413 min — OVER SLA  BREACH
HO-019    RV-03     antigravity      410m  opencode2      wait 410 min — OVER SLA  BREACH
HO-020    PERF-01   antigravity      399m  buffy          wait 399 min — OVER SLA  BREACH
HO-021    ENG-01    opencode         399m  freebuff2      wait 399 min — OVER SLA  BREACH
HO-022    PA-01     hermes           398m  opencode2      wait 398 min — OVER SLA  BREACH
HO-023    PA-02     hermes           397m  buffy          wait 397 min — OVER SLA  BREACH
HO-024    INT-01    buffy            380m  hermes         wait 380 min — OVER SLA  BREACH
HO-026    TB-027    opencode2        350m  freebuff2      wait 350 min — OVER SLA  BREACH
HO-027    TB-029    opencode2        329m  buffy          wait 329 min — OVER SLA  BREACH
HO-028    TB-031    opencode2        325m  hermes         wait 325 min — OVER SLA  BREACH
HO-029    TB-032    opencode2        323m  freebuff2      wait 323 min — OVER SLA  BREACH
HO-030    UX-05     hermes           322m  opencode2      wait 322 min — OVER SLA  BREACH
HO-032    ENG-02    opencode2        287m  buffy          wait 287 min — OVER SLA  BREACH
HO-034    ENG-03    opencode2        281m  hermes         wait 281 min — OVER SLA  BREACH
HO-036    TB-006    freebuff2        280m  opencode2      wait 280 min — OVER SLA  BREACH
HO-037    UX-02     hermes           253m  freebuff2      wait 253 min — OVER SLA  BREACH
HO-038    TB-011    freebuff2        246m  buffy          wait 246 min — OVER SLA  BREACH
HO-039    UX-22     hermes            46m  opencode2      wait 46 min — OVER SLA  BREACH
HO-040    ENG-05    opencode2         41m  hermes         wait 41 min — OVER SLA  BREACH
HO-041    ENG-07    opencode2         33m  freebuff2      wait 33 min — OVER SLA  BREACH
HO-042    UX-08     hermes            29m  buffy          wait 29 min
HO-043    LEAD-03   buffy             19m  opencode2      wait 19 min
HO-044    QUAL-01   opencode2         18m  hermes         wait 18 min
HO-045    QUAL-02   opencode2         13m  freebuff2      wait 13 min
HO-046    LEAD-01   buffy             11m  opencode2      wait 11 min
HO-047    CORPUS-03 freebuff2          4m  buffy          wait 4 min

seats: 6  away: antigravity, opencode
```

Every row past the service level is a BREACH. The oldest items are `antigravity`'s, which nobody can verify now — they are permanently stuck behind a seat with no quota, and they are the queue's longest tail.

## What the rotation proposes instead

Same 26 handoffs, same backlog, same moment — assigned by least-recently-verified-first:

| Seat | Proposed | Currently verified |
|---|---|---|
| `freebuff2` | **7** | 0 |
| `opencode2` | **7** | 0 |
| `buffy` | **7** | 1 |
| `hermes` | **6** | 0 |

From **92% on two seats** to a spread across **4 active seats**. Both `AWAY` seats are excluded by rule, and no handoff is ever assigned to its author.

## The honest part: this is a proposal, not a result

The mechanism landed minutes before this measurement. The distribution above is what the queue *proposes*, not a wait time that has been realised. The median wait only falls once seats actually drain the queue.

Re-measure and record the real figure:

```
$ python scripts/verification_queue.py --stats
```

Reporting an improvement here before it is observed would be exactly the habit `TB-105` (a citation is not evidence until the line is opened) and `TB-106` (a register that lies because it was written rather than measured) exist to prevent. The mechanism is the deliverable; the wait time is the follow-up measurement.

## The four refusals

Each exists because breaking it produced a real failure here:

| Rule | Why |
|---|---|
| Never assign to an `AWAY` seat | assigning to `antigravity` looks like fair rotation and produces nothing |
| Never assign to the author | `team.py verify` requires a different agent; the queue must not propose what the tool forbids |
| Least-recently-verified first | oldest-first FIFO keeps the concentration exactly where it is — it hands work to whoever is idle as a *verifier*, not to whoever has verified least |
| A service level, not a hope | `--sla` (default 30 min, matching the watchdog threshold) turns "late" into a number |

And one exclusion: a **rejected** handoff is not in the queue. It is waiting for its author to re-do the work, not for a verifier. Counting those would have inflated this bottleneck from 26 to 36 and hidden the real one.

