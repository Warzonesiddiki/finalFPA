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