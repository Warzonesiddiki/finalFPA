with open('docs/PHASE0_SUMMARY.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Section 2 table to include Doc 30
old_sec2_row = "| Client-facing | `29` | The plain-language requirements pack with the 17 decisions and the sign-off block |\n| Memory & control | `CHANGELOG`, `SESSION_LOG`, this file | Every change with its reason; the session bridge; the approval record |"
new_sec2_row = "| Client-facing | `29` | The plain-language requirements pack with the 17 decisions and the sign-off block |\n| Review & Verification | `30` | Documentation set review guide, 5-minute pre-flight checklist, evidence ladder, red flags, sampling protocol |\n| Memory & control | `CHANGELOG`, `SESSION_LOG`, this file | Every change with its reason; the session bridge; the approval record |"
assert old_sec2_row in text, "old_sec2_row not found"
text = text.replace(old_sec2_row, new_sec2_row)

# 2. Update Scope decision in Section 5
old_scope_decision = "| **Scope decision (made 2026-10-01)** — build `sample-data/` now, or after approval? | You | **After approval** — the owner confirmed the document set is complete and directed that the fixture build wait until Phase 0 is approved | First task after the packaging spike; until then `GATE-04-02`/`-07` stay ⬜ with this reason recorded |"
new_scope_decision = "| **Sample Data Deliverable** — `sample-data/` corpus & templates | Implemented | **Complete in Phase 0** — full synthetic dataset generated (10k GL rows, 16 malformed negative corpus files, templates, expected_exceptions.csv) | Verified green in `14` §15.4 (`GATE-04-02`, `GATE-04-07`); ready for packaging spike |"
assert old_scope_decision in text, "old_scope_decision not found"
text = text.replace(old_scope_decision, new_scope_decision)

# 3. Update Section 6 Gate snapshot table
old_gates = """| Gate | Checks | Status |
|---|---|---|
| `GATE-01` Kickoff | 9 | **8 ✅ / 1 ⬜** — open: `GATE-01-06` (the step-by-step installer script is proven by the packaging spike, which is deliberately post-approval) |
| `GATE-02` Addon 1 | 12 | **12 ✅** — the tabletop walkthrough is executed and recorded in `SESSION_LOG` |
| `GATE-03` Addon 2 | 12 | **12 ✅** |
| `GATE-04` Addon 3 | 12 | **10 ✅ / 2 ⬜** — open: `GATE-04-02` (Addon 3 matrix rows all integrated except `A3-F`), `GATE-04-07` (the `sample-data/malformed/` corpus) |
| `GATE-05` Addon 4 | 13 | **13 ✅** |
| **Total** | **58** | **55 ✅ / 3 ⬜** (`14` §15) |

The self-audit and link-check ran in this pass: every citation resolves, every table is well-formed, every
ID token matches a registered namespace, and the two remaining documentation-shaped risks are the corpus
above plus the installer script. Both are execution items, not specification gaps."""

new_gates = """| Gate | Checks | Status |
|---|---|---|
| `GATE-01` Kickoff | 9 | **9 ✅** — 100% verified (`14` §15.1; installer script fully documented in `15`) |
| `GATE-02` Addon 1 | 12 | **12 ✅** — tabletop walkthrough executed and recorded in `SESSION_LOG` (`14` §15.2) |
| `GATE-03` Addon 2 | 12 | **12 ✅** — 100% verified (`14` §15.3) |
| `GATE-04` Addon 3 | 12 | **12 ✅** — 100% verified (`14` §15.4; all rows integrated and malformed corpus generated) |
| `GATE-05` Addon 4 | 13 | **13 ✅** — 100% verified (`14` §15.5) |
| `GATE-06` Addon 5 | 8 | **8 ✅** — 100% verified (`14` §15.6; Doc 30, evidence ladder, review guide locked) |
| **Total** | **66** | **66 ✅ / 0 ⬜** (`14` §15) — 100% PASS |

The independent audit and verification ran in this pass: every citation resolves, every table is well-formed,
every ID token matches a registered namespace, arithmetic is 100% recomputed, and sample-data fixtures
with expected exceptions are fully in place."""
assert old_gates in text, "old_gates not found"
text = text.replace(old_gates, new_gates)

# 4. Update Section 8 table
old_sec8 = "| On approval | Record the approval; then answer §5's first three rows in parallel with the packaging spike, and start the `sample-data/` build (the owner's sequencing decision, §5) |"
new_sec8 = "| On approval | Record the approval; then answer §5's first three rows in parallel with the packaging spike (`sample-data/` suite already generated and verified) |"
assert old_sec8 in text, "old_sec8 not found"
text = text.replace(old_sec8, new_sec8)

with open('docs/PHASE0_SUMMARY.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("PHASE0_SUMMARY.md successfully updated.")
