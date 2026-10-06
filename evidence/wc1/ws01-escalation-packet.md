# WC-1 escalation packet — the `WS-01` catalog source no longer exists

> **Date:** 2026-10-05 · **Work card:** `WC-1` (`project prompt/ADDON_6_REUSE.md` §9, SHA-256 `81f5aaee…01d3`)
> **Tier:** **C — STOP for owner** (§14). Nothing landed; `STATE.md` rolled back to the last green state.
> **Open question:** `OQ-028` (docs/18) · **Rollback:** clean (no `app/` file touched, no staging dir left behind)

---

## 1. What was measured

Addon 6 v2 §9 pre-approves `WC-1` as a COPY-EDIT of catalog entry `WS-01`:

```
| WS-01 | github.com/ricothanfx/invoice-dedupe | COPY-EDIT | from `src/invoice_dedupe/`:
  normalization, blocking, weighted-scoring modules only (≤6 files; exact list after clone) |
  `app/engine/dedupe/` | … | **MIT** — `pyproject.toml` line `license = { text = "MIT" }`
```

§6 S2 − "Fetch pinned upstream" cannot complete. Captured twice, with the exit status preserved (no pipe masking):

```
$ git clone --depth 1 https://github.com/ricothanfx/invoice-dedupe vendor/_upstream/WS-01
Cloning into 'vendor/_upstream/WS-01'...
remote: Repository not found.
fatal: repository 'https://github.com/ricothanfx/invoice-dedupe/' not found
REAL_GIT_EXIT=128
```

A web search for the repository returns no such project and **no renamed successor** — the closest public
projects are `dedupeio/dedupe`, `pimverschuuren/Deduplication` and `pmessan/duplicate_invoice_finder`, none of
which is the catalog's target.

**Consequence for the card:** `ADP-004` cannot be written, because its mandated `files copied` and `SHA`
fields have no values — S2 has to succeed before S3 (gate 4A) can even run. §6 S4's escape hatch ("listed file
missing → STOP → docs/18") and §14's Tier C both apply. Retrying cannot fix a 404, so the two-attempt loop in
§14 is satisfied in substance rather than by repetition.

## 2. The S0 finding that changes the shape of the decision

Before the fetch, §6 S0 requires grepping `app/` for the capability. It returned something the card's premise
does not anticipate: **the capability `WC-1` exists to improve is already implemented and already spec-complete.**

| `06` rule | Tier | Status | Where |
|---|---|---|---|
| `EXC-002` Cross-batch duplicate rows | `exact` | implemented, passing | `rules_catalog_001_008.py:223` |
| `EXC-007` Possible duplicate invoice | `exact` | implemented, passing | `rules_01_08.py:evaluate_exc_001` (+ `_normalize_invoice_no:221`) |
| `EXC-008` Possible duplicate voucher line | `exact` | implemented, passing | `rules_catalog_001_008.py:665` |

`EXC-007`'s normalisation clause — *"trim, upper-case, strip leading zeros and non-alphanumeric separators"* —
is implemented verbatim at `rules_01_08.py:221`:

```python
def _normalize_invoice_no(invoice_no: Optional[str]) -> str:
    """Normalise invoice number per §4 EXC-007: trim, upper-case, strip leading zeros and symbols."""
```

**All three duplicate rules are Tier `exact`.** `06` has eight `fuzzy`-Tier rules, and none of them is a
text-similarity problem:

```
EXC-013 spike vs trailing average      EXC-017 material unbudgeted spend
EXC-014 unusual vendor→account pairing EXC-018 material variance (amount AND %)
EXC-015 missing recurring cost         EXC-019 cumulative overrun vs annual budget
EXC-016 missing expected accrual       EXC-022 round-number manual journal
```

So `WS-01`'s headline capability — **weighted / fuzzy scoring** — is not required by any rule in the catalog.
Worse, wiring it into `EXC-007`/`EXC-008` would be an `R1` violation: it would move those rules off Tier
`exact`, and `06` keeps them exact *on purpose* to protect precision (`EXC-007` mitigation: *"Partial-amount
duplicates … are deliberately **out of scope** for v1 to keep precision high"*). The `14` §5.3 bar *"0 of 8
controls may raise"* is currently already breached (1 fired), so a fuzzy scorer in a duplicate path would
attack the one bar the corpus can least afford.

**What is genuinely missing is smaller than the card assumes:** a shared `dedupe` interface. The normaliser
and the two blockers exist as inline logic inside two rule modules; nothing else can reuse them. The
`R12`-visible symptom is duplication of the *blocking idea*, not a missing matcher.

## 3. Exactly three options

### Option 1 — BUILD path + `BD` row (**recommended**)

Close `WC-1` as *"no copyable source; capability already satisfied"*:

- write **`BD-001`** in `32` §2 (the first build-decision row: capability, the `FR`/spec quote, sources
  searched **including the dead catalog URL**, why none fit, chosen approach) — this is the §1 decision tree's
  documented terminal state ("nothing copyable → BUILD path + BD row"), the same outcome `WC-5` is expected to
  reach for the corpus generator;
- add a `TB` row to `33` for the **one real gap**: extract the normaliser and the two blockers behind a shared
  `app/engine/dedupe/` interface **as our own code**, so `R12` is satisfied without importing anything;
- amend the `WS-01` catalog row to record that its URL is dead (so no future session repeats this fetch);
- tests: reuse the existing rule tests plus new interface tests, `≥90 %` coverage on the new module.

**Why recommended:** it is the only option that is `R1`-clean (no rule, tier, threshold or `FR` moves), costs
no new runtime dependency (`R9`), and turns a blocked reuse card into a real improvement. It also stops the
`repo → 404` from being rediscovered by the next session.

### Option 2 — Intake a replacement source (§10)

Search → shortlist ≤3 → one six-field `docs/18` entry. Candidates already visible:

| Candidate | Licence | Verdict |
|---|---|---|
| `dedupeio/dedupe` | MIT | Heavy ML stack (`numpy`/`scipy`/`affinegap`/`categorical`) → `R9` ADR + DEC + `pyproject` change, and it solves the fuzzy problem the spec does not have |
| `pimverschuuren/Deduplication` | unverified | Research/notebook-shaped; licence evidence not yet gathered |
| `pmessan/duplicate_invoice_finder` | unverified | Challenge submission; likely small, licence unknown |

§10 grants Tier B *only* when "licence GO + ≤2 modules + no spec change + no API change"; a heavyweight
dependency stack pushes this to Tier C and an owner signature.

### Option 3 — Skip `WC-1`, proceed elsewhere

Leave the catalog entry flagged dead and move the session to `WC-5` (corpus build, the parallel track) or to
the `TB-020`/acceptance-bar work that `scripts/check.py` is actually red on. Fastest route to a green gate;
leaves the `R12` interface gap open.

## 4. Recommended default, stated plainly

**Option 1.** The card's goal is met without the card's source: the spec's duplicate detection is `exact`-Tier
and already passing, the normaliser it asks for exists verbatim, and the only defensible improvement left is
extracting the shared interface as our own code — which `L2`/`R12` sanction and which needs no licence, no new
dependency and no spec change.

## 5. What was *not* done, deliberately

- No `ADP-004` row, no `ADR-014`, no notices entry — `R5` forbids records before an achievable fetch, and
  inventing an `SHA` for a repository that does not exist would be a fabricated provenance record.
- No staged files, no `app/engine/dedupe/` directory, no `pyproject.toml` change.
- `vendor/_upstream/WS-01` was never created (the failed clone left nothing); the empty parent directory
  created by `mkdir -p` was removed.

## 6. Acceptance-gate impact

**None, under every option.** No `FR`, rule, tier, threshold or subject key moves. `OQ-028` is recorded as
*not* blocking the `14` §5.3 bars, so it is a process decision, not an acceptance blocker — the corpus work
(`TB-020`, `OQ-025`…`027`) remains the only thing standing between `scripts/check.py` and green.
