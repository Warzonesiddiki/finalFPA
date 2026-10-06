"""Record the out-of-scope write guard + the UX-03 verification + hermes' expanded lane."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)

# ---------------------------------------------------------------- CHANGELOG
c = pathlib.Path("CHANGELOG.md")
ct = c.read_text(encoding="utf-8")
anchor = "### Added" + NL
item = (
    "- **Writes outside a claim are now detectable (`team.py check`):** a file modified inside a claim"
    " window but outside that claim's scopes is reported, filtered down to files no other live claim covers and"
    " not a leader-only path, with tool caches excluded. Motivation: `hermes`' `UX-03` handoff created two"
    " `scripts/` files under a claim scoped to `evidence/` - invisible to the undeclared-file rule, because that"
    " rule only looked *inside* the claim. \"One writer per path\" is meaningless if paths outside your claim are"
    " unpoliced."
    + NL + NL
)
if "Writes outside a claim are now detectable" not in ct:
    ct = ct.replace(anchor, anchor + item, 1)
    c.write_text(ct, encoding="utf-8", newline="")
    print("CHANGELOG updated")

# ---------------------------------------------------------------- STATE.md
s = pathlib.Path("STATE.md")
st = s.read_text(encoding="utf-8")
i = st.index("TASK: ")
new_task = (
    "TASK: `UX-03` verified on substance and returned on form (hermes' 43-screen conformance matrix: matrix"
    " generator exit 0 with 43 screens, citation checker exit 0, team.py check 0 errors) - the handoff declared"
    " 1 of the 3 files written, wrote two scripts outside the claimed scope, and its citation count (242) does not"
    " match the checker's 146. That last one exposed a real hole, now closed: team.py check reports files written"
    " inside a claim window but OUTSIDE the claimed scopes, filtered to files no other live claim covers and not"
    " leader-only, with tool caches excluded. hermes' lane is now six new cards built for 30+ subagents: UX-08"
    " (a11y/keyboard audit of all 43 screens, P0), UX-09 (the twelve numbers an analyst must never get wrong, P0),"
    " UX-10 (error-message catalogue), UX-06 (board narrative), SPEC-05 (executable-ready test specs for the 14"
    " zero-coverage rules - the acceptance-gate critical path), UX-11 (first-run journey), RV-06 (adversarial code"
    " review of import commit, finding persistence, board-pack export). Watchdog loop running on the 20-minute"
    " cadence and now self-reloads when its own code or config changes"
)
s.write_text(st[:i] + new_task + st[i + len("TASK: "):], encoding="utf-8", newline="")
print("STATE.md updated")

# ---------------------------------------------------------------- SESSION_LOG
p = pathlib.Path("docs/SESSION_LOG.md")
t = p.read_text(encoding="utf-8")
add = [
    "",
    "### Addendum 4 - verifying `UX-03` found a hole in my own guard, not just in the handoff",
    "",
    "`hermes` handed off `UX-03` (screen-by-screen conformance for all 43 screens in `08`). I reproduced its own",
    "commands: `scripts/generate_screen_conformance_matrix.py` -> exit 0, 43 screens; `scripts/verify_audit_citations.py`",
    "-> exit 0, all citations resolve; `team.py check` -> 0 errors. The artefact is real and the matrix is the thing I",
    "wanted. Two formal problems, both mine to enforce: the handoff declared one file while three were written, and",
    "**two of those files were written outside the claim's own scope** - which my undeclared-file rule could not see,",
    "because it only looked inside the claim.",
    "",
    "**The hole, closed at the root.** `team.py check` now also reports files written inside a claim window but",
    "*outside* the claimed scopes, narrowed to files no other live claim covers and not leader-only paths, with tool",
    "caches (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `.coverage`, `dist/`) excluded so the signal is not noise.",
    "R14 - one writer per path - means nothing if the paths outside your claim are unpoliced. Two bugs of my own were",
    "found while building it and fixed: a variable named `covered` shadowed the existing `covered()` helper (crash on",
    "every `check`), and the first filter flagged 21 cases, nearly all legitimate.",
    "",
    "Third item: the handoff claims 242 citations across five evidence files; the checker reports 146. Unexplained, so",
    "it is in the rejection.",
    "",
    "`UX-03` was therefore **rejected on form, accepted on substance** - and hermes' stream grew by six cards, all",
    "shaped for a 30+ subagent fan-out: one subagent per screen group (`UX-08`, keyboard/focus/ARIA against WCAG 2.2",
    "AA), one per number (`UX-09`, the twelve an FP&A analyst must never get wrong, traced import to export), one per",
    "error family (`UX-10`), plus the board narrative (`UX-06`), the first-run journey (`UX-11`), the adversarial code",
    "review (`RV-06`), and `SPEC-05` - executable-ready test specs for the 14 zero-coverage exception rules, which is",
    "the acceptance gate's critical path and the single highest-leverage thing a subagent fleet can produce this week.",
    "",
    "Measured: `team.py check` -> **PASS, 0 fail**; `tests/unit/test_team_watchdog.py` -> **14 passed**;",
    "`check_doc_integrity.py` -> **exit 0**; `license_gate.py` six checks -> **exit 0**.",
    "",
]
i = t.index("## Session 014")
t = t[:i] + NL.join(add) + t[i:]
p.write_text(t, encoding="utf-8", newline="")
print("SESSION_LOG addendum 4 written")
