# Shared lessons (append-only)

Every entry is a trap that cost at least one agent real time. Add a dated line when you find one; never
delete an entry — if it stops being true, add a new line that says so (same discipline as `docs/18`).

Format: `- **YYYY-MM-DD** — <lesson> (evidence: <where it bit>)`

## Environment (Windows, this machine)
- **2026-10-05** — Console output in scripts must be UTF-8: `sys.stdout.reconfigure(encoding="utf-8")`,
  otherwise the project's unicode (₹, →, ⬜) raises `UnicodeEncodeError` on the cp1252 console.
- **2026-10-05** — `code_search` (the vendored ripgrep binary) can be missing in this Freebuff build; use
  `grep -rn` / `git grep` from the terminal instead of assuming search is available. (evidence: `ENOENT …
  rg.exe` on first use this session)
- **2026-10-05** — The repo mixes line endings: `docs/32`, `docs/09` are LF; `docs/18`, `docs/33`,
  `CHANGELOG.md`, `docs/14`, `docs/SESSION_LOG.md`, `STATE.md` are CRLF. Match the file's style when
  inserting lines, or scripts that compare bytes will drift.
- **2026-10-05** — Long heredocs passed through the shell tool can be truncated (a ~7 kB `python - <<EOF`
  died mid-string). For edits longer than a few kB, write a script file, run it, delete it; or use the
  file-edit tools.
- **2026-10-05** — A BACKGROUND `scripts/check.py` died with its parent shell once; for long jobs write to
  `scratch/*.log`, and verify the process is still alive before trusting the log.

## Shared-checkout traps (five agents, one working tree)
- **2026-10-05** — **`app/api/openapi.json` carries the owner's own uncommitted edit**, present before the
  team layer existed. Do not claim it, do not regenerate it, and do not “tidy” it: `git status` shows it
  modified and it is the human's, not ours. (evidence: `git status --porcelain` at session start)
- **2026-10-05** — Most of this tree is **uncommitted from earlier sessions** (77 untracked paths at the team
  layer's launch). `team.py check` warns about edits no claim covers — that warning is expected until the
  owner authorises a commit; do not “clean it up” to silence it.
- **2026-10-05** — `git grep` escapes non-ASCII paths unless `core.quotePath=false` (`preflight` was fixed to
  pass it); the same class of bug bites any script that reads `git status` output on Windows.

## Project traps worth never rediscovering
- **2026-10-05** — `text_frame.text = …` **destroys the run's `rPr`** (font size/weight/colour/typeface).
  Fill into an existing run (`pptx_fill.patterns.set_text` / `set_cell_text`). (evidence: `ADP-002` row,
  `test_set_text_preserves_template_run_formatting`)
- **2026-10-05** — Layout shapes on a template with 0 slides are **inherited**, not clickable; promote them
  onto the slide and re-point `r:embed`/`r:link`/`r:id` at the slide part. (evidence: `ADR-011`, `DEF-018`)
- **2026-10-05** — DuckDB has **no auto-increment**: supply primary keys explicitly or use a
  `CREATE SEQUENCE` + `nextval`; `AUTOINCREMENT` copied from SQLite DDL is a defect. (`DEC-046`)
- **2026-10-05** — `06`'s duplicate rules are Tier **`exact`** on purpose; the normalisation clause strips
  leading zeros only at the start of the alphanumeric string (`INV-00088213` ≠ `INV-88213`). Widening it is
  an `R1` question, not a tweak. (`WC-1`, `DEC-066`)
- **2026-10-05** — The acceptance gate is red on five **pre-existing** `14` §5.3 bars (recall 11/32, 1
  control fired, High 6/18, 422 extras, 14 zero-coverage rules) with the corpus as it stands. Do not "fix"
  these by relaxing the bar; the corpus rebuild (`TB-006`, `DEC-059`) is the lever.
- **2026-10-05** — Registry hygiene is a real failure mode: a cited `DEC`/`TB` id must exist. The `WC-2`
  session cited `DEC-063` everywhere while the register never received the row (and duplicated `DEC-064`
  instead). `team.py check` now warns when a claim references a `TB-nnn` that is not in `docs/33`.
