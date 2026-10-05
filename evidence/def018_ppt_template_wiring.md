# DEF-018: PPT Template Contract Wiring

## 1. Description
The PowerPoint export engine now loads the validated template file (`packaging/templates/FPAMonthEndCopilot_v1.pptx`) instead of starting from a blank `Presentation()`. Shape resolution operates by name traversing `slide.shapes` and then falling back to `slide.slide_layout.shapes`. If a shape is missing, `ERR-EXP-014` is raised.

## 2. Scope of Migration 
- **Fully Migrated**: Slide 1 `PPT-001` (Cover & Metadata). It retrieves the `FPA-PPT-001` layout, resolves shapes (`PPT-001_title`, `PPT-001_packline`, `PPT-001_periodline`, `PPT-001_sources`, `PPT-001_stamp`) and injects the context data properties exactly.
- **Still Procedural (Not Conformant)**: Slide 2 (`PPT-002`), Slide 3 (`PPT-003`), Slide 4 (`PPT-004`), Slide 5 (`PPT-005`), Slide 6 (`PPT-006`). They use the procedural path `prs.slide_layouts[6]` and are marked explicitly with `# not-yet-doc-12-conformant: using procedural path`.
- **Atomic Failure Guarantee**: If shape resolution fails in any migrated slide builder, `generate_powerpoint_deck` guarantees no partial file is produced by writing to `output.tmp` and unlinking it in the `except` block. No `.pptx` remains on disk if `ERR-EXP-014` fires.

## 3. Error Codes Added
Added all the missing `ERR-EXP` family codes to `app/engine/errors.py`:
- `ERR-EXP-002, 003, 006, 007, 009` (General export conditions).
- `ERR-EXP-012..018` (PowerPoint specific exceptions).

## 4. Evidence of Output & Double Direction Gate
A Python verification was run showing the bidirectional gate behavior:

1. **Success path**: `generate_powerpoint_deck` successfully wrote 6 slides and finished without exception.
2. **Failure path**: Loading a modified template (with one shape deleted) caused it to raise `ExportTemplateError: ERR-EXP-014`. The `.tmp` file and `.pptx` were completely cleared from the disk, leaving nothing.

All test debris from the repository root has been cleared.

---

## 5. CORRECTION — 2026-10-05 (Addon 6 v2 work card `WC-2`): `DEF-018` is now fully closed

> Sections 1–4 above are the **original, partial** fix and are left unedited so the record stays honest.
> Read this section before acting on anything above it.

§2's "**Still Procedural (Not Conformant)**: Slide 2 … Slide 6" is **no longer true**. All six builders now
fill the template's named shapes; the `# not-yet-doc-12-conformant: using procedural path` marker and the
`prs.slide_layouts[6]` path are both gone from `app/engine/exports/ppt_pack.py`.

Closure work, full measurements and evidence: **`evidence/wc2/def018_closure_report.md`**
(checksums in `evidence/wc2/SHA256SUMS.txt`). Summary of what changed since §4:

| Item | Status now |
|---|---|
| Slides 1–6 template-fill by name (`12` §3.6) | **done** — 103/103 contract names resolve per slide |
| `ppt_spec.py` (canonical write order named by §3.6) | **created** — `app/engine/pptx_fill/ppt_spec.py` |
| `ERR-EXP-014` on a missing name | **real** — raised by `pptx_fill.core.TemplateShapeError`, now a single implementation (`ExportTemplateError` is an alias) |
| Fill engine | **`app/engine/pptx_fill/`** (`ADP-001`/`002`/`003`), 95 % coverage, 82 new tests |
| Footer band | **corrected** — §4 above predates the discovery that code invented `PPT-00N_footer_disclaimer`/`_footer_page` while the template ships `PPT-00N_footer_left`/`_footer_right` |
| KPI chips / accent bars | **corrected** — `*_chip` → `*_signal`; the phantom `PPT-00N_accent` bars on slides 2–6 removed |
| Bridge tie-out | **corrected** — the "— OK" tie-out line was a hard-coded string hiding a ₹500,000 gap; it is now an explicit `Other (unexplained)` step and the residual is stated |
| Verification | **843 passed, 16 deselected**; `check_doc_integrity.py` PASS; `license_gate.py` PASS (exit 0) |

Owed, and deliberately not fabricated: `12` §5.2's "both bridge variants as two shapes" until `python-pptx`
gains `XL_CHART_TYPE.WATERFALL` (`TB-048`); `12` §4.1's row count read as 6 per `DEC-065` (R1 — the spec was
interpreted, not edited).