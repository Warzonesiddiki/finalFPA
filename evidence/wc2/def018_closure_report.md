# `DEF-018` closure report — Addon 6 v2 work card `WC-2`

> **Date:** 2026-10-05 · **Work card:** `WC-2` (`project prompt/ADDON_6_REUSE.md` §9, SHA-256 `81f5aaee…01d3`)
> **Defect:** `DEF-018` (S1) — `ppt_pack.py` built every slide from scratch, violating `12` §3.6.
> **Adoptions:** `ADP-001` (WS-02, Apache-2.0) · `ADP-002` (WS-10, CC0-1.0) · `ADP-003` (WS-03, MIT)
> **Records:** `DEC-061`, `DEC-063`, `DEC-064`, `DEC-065` · `ADR-011`, `ADR-012`, `ADR-013`
> **Artefact checksums:** `evidence/wc2/SHA256SUMS.txt`

---

## 1. The defect, restated

`12` §3.6: *"The engine never builds a layout from scratch: it copies the template and fills it."*

Before this work card, `generate_powerpoint_deck` opened the template only to satisfy `ERR-EXP-014`, then
built all six slides on `prs.slide_layouts[6]` using `add_textbox` / `add_shape` / `add_table` /
`add_chart`. The template's **103 named shapes** were never read.

| Consequence | Why it mattered |
|---|---|
| Template styling unused | Every font size, colour and typeface the template author set was re-authored in Python |
| Shape-name contract unenforceable | `12` §3.6 requires ERR-EXP-014 on a missing name, but names were *manufactured at runtime*, so nothing could be missing |
| Canonical write order impossible | `12` §3.6 names `ppt_spec.py` as the ordering source of truth; **the file did not exist** |
| §3.7 no-overlap guarantee unfounded | It rested on hand-tuned coordinates, not on a template contract |

## 2. The architecture decision that mattered

The template ships **0 slides and 0 placeholders** — seven layouts holding 103 named shapes. That makes
"copy the template and fill it" less obvious than it looks:

* Editing `slide.slide_layout.shapes` in place **does** persist through save/reopen (verified by probe:
  `scratch/_probe.pptx`, `scratch/_probe2.pptx`), but the resulting shapes are *inherited* layout content.
  PowerPoint does not let a user click inherited layout shapes, so the deck would no longer be natively
  editable — trading one §3.6 breach (`built from scratch`) for another (`not editable`).
* So layout shapes are **promoted**: each shape's element is deep-copied onto the slide's `spTree` in
  layout order, preserving geometry, styling and z-order.
* The catch is relationship ids. A promoted graphic frame still points at the chart or image part by the
  relationship id held by the **layout**, which the slide does not own — a dangling reference.
  `core._relocate_element_rels` re-relates every embedded part to the slide and rewrites the id in place.

Measured on a 6-slide deck containing both charts:

```
zip integrity: OK
chart parts:   ['ppt/charts/chart1.xml', 'ppt/charts/chart2.xml']   # one per slide, never shared
embeddings:    2 xlsx workbooks
slide2 rels -> ['../charts/chart1.xml']
slide3 rels -> ['../charts/chart2.xml']
chart content-type declared: True   xlsx: True   image: True
chart types preserved: COLUMN_STACKED (52), LINE_MARKERS (65)
```

## 3. The second load-bearing finding

**Assigning to `text_frame.text` destroys the template's run formatting.** python-pptx rebuilds the run and
drops its `rPr`:

| Write | Result |
|---|---|
| `shape.text_frame.text = "X"` | `sz=None`, `bold=None`, colour type `_NoneColor`, `<a:rPr><a:solidFill/></a:rPr>` |
| `shape.text_frame.paragraphs[0].runs[0].text = "X"` | `sz=304800` (24 pt), `bold=True`, `rgb=1F3A5F`, `Calibri` preserved |

Upstream WS-10 demonstrates `chart.chart_title.text_frame.text = …` and `table.cell(i,j).text = …` — both
would have silently discarded every format the template author set. Every fill verb therefore writes into an
**existing run**. This is pinned by `test_set_text_preserves_template_run_formatting`, which is the single
regression test this adoption exists to prevent.

## 4. Additional defects found and fixed

| # | Defect | Evidence |
|---|---|---|
| a | **Footer name mismatch.** Code created `PPT-00N_footer_disclaimer` / `_footer_page`; the template ships `PPT-00N_footer_left` / `_footer_right`. The §3.7 footer could never have matched. | `verify_deck.py` output; `test_slide_1_cover_and_stamp` |
| b | **KPI chips** created as `PPT-002_kpiN_chip` against the template's `PPT-002_kpiN_signal`. | template inventory probe |
| c | **Phantom accent bars.** `_add_accent_bar` added `PPT-00N_accent` to slides 2–6; the template has an accent shape only on `PPT-001` and `PPT-00D`. | template inventory probe |
| d | **Fabricated bridge tie-out.** Drivers sum to **+₹375,000**; opening → closing moves **+₹875,000**. The slide printed `Opening + Σ drivers = Closing — OK` as a hard-coded string. | before: bar tops ended 16,145,000 against a 16,645,000 closing bar |
| e | **`set_value_axis` swallowed `0.0`.** The inherited `if minimum:` guard treats `0.0` as falsy, silently dropping a legitimate zero axis bound. | caught by `test_set_value_axis_pins_the_scale` |

**Fix for (d).** The §5.2 stacked-column fallback needs a computed base series, so the ₹500,000 shortfall
would have become a visible unexplained step in the chart. It is now surfaced as its own `Other
(unexplained)` step in both the chart and the driver list, and the tie-out line states the residual —
consistent with `12` §3.7's "the gap is visible and truthful, never interpolated".

Measured after — the bridge now ties out exactly:

```
categories: Opening (Budget), Opex other, Contractors, Materials, Repairs, Utilities,
            Other, Closing (Actual)
base:       [0, 15770000, 15950000, 16090000, 16168000, 16143000, 16145000, 0]
amount:     [15770000, 180000, 140000, 78000, -25000, 2000, 500000, 16645000]
bar tops:   [15770000, 15950000, 16090000, 16168000, 16143000, 16145000,
             16645000, 16645000]        <- closing bar == final step
```

## 5. Contract conformance (`12` §3.6)

Every name in `ppt_spec.SHAPE_CONTRACT` must resolve on its layout; a missing one aborts with ERR-EXP-014.

```
PPT-001 (FPA-PPT-001): contract=9  layout=9    PPT-004 (FPA-PPT-004): contract=7  layout=7
PPT-002 (FPA-PPT-002): contract=37 layout=37   PPT-005 (FPA-PPT-005): contract=19 layout=19
PPT-003 (FPA-PPT-003): contract=7  layout=7    PPT-006 (FPA-PPT-006): contract=16 layout=19
CONTRACT OK
```

`PPT-006_card1…3` are the three outlook-card backgrounds. They carry no data — their surface fill and border
are template-authored constants — so they are deliberately **not** in the contract. That is the only
difference between 16 and 19, and it is asserted rather than assumed (`test_contract_is_append_only_in_shape_count`).

## 6. Verification

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest -m "not perf"` | **843 passed, 16 deselected**, 0 failed (317.67 s) |
| Coverage | `--cov=app` | **87.21 %** total (gate 75 % required) |
| New-code coverage (R6 ≥ 90 %) | `--cov=app.engine.pptx_fill` | **95.09 %** (`patterns.py` 98 %, `core.py` 94 %, `layout.py` 92 %, `ppt_spec.py` 100 %); `ppt_pack.py` itself **95 %** |
| Doc integrity | `python scripts/check_doc_integrity.py` | **PASS** — 88 markdown files, links + cross-doc IDs consistent |
| Licence & provenance (Addon 6 §11) | `python scripts/license_gate.py` | **PASS exit 0** — 5 `Adapted from` headers, all matching the E8 regex; 0 forbidden-license hits; `vendor/_upstream/` gitignored and untracked; 9/9 runtime deps on the GO list; 0 DT tools in runtime |
| Contract drift | `python scripts/check_contract_drift.py` | **PASS** |
| TST catalogue traceability | `python scripts/check_tst_catalogue.py` | **PASS** — 34 mapped IDs, 41 markers |
| CLI doctor | `python -m app.cli doctor --json` | `{"status":"healthy","version":"0.1.0","engine":"ready"}` |
| Determinism (`TST-PPT-08`) | `test_two_runs_from_the_same_context_produce_identical_slide_xml` | PASS |
| Bridge tie-out | `verify_deck.py` | closing bar == final step, exactly |
| Real user path | `python scripts/run_uat_dry_run.py` | **exit 0**, all six `TST-UAT-*` PASS; `Management_Deck_UAT_FY26-P09.pptx` generated with 6 slides through the same `generate_powerpoint_deck` call the API uses |

**New tests:** 82 (`test_pptx_fill_patterns.py` 49 + `test_pptx_fill_layout.py` 33).
The layout file is the adapted WS-03 `tests/unit/test_layout_adaptive.py` (11 upstream tests), re-expressed
against python-pptx shapes per `DEC-064` and `E13`/`R6`.

## 7. Tests changed rather than deleted (R7)

Two assertions in `tests/unit/test_ppt_pack.py` encoded the from-scratch behaviour `DEF-018` called a
defect, so they asserted the wrong thing. Both were rewritten to the `12` §3.6/§3.7 contract and are
**stronger** than what they replaced:

| Test | Before | After |
|---|---|---|
| `test_slide_1_cover_and_stamp` | footer shapes *exist* under code-invented names | names are the template's `footer_left`/`footer_right` **and** each shape's text is checked against `12` §3.7 verbatim |
| `test_shape_whitelist_no_raster_screenshots` | no `PICTURE` anywhere (would reject the template's own logo) | exactly one raster permitted — the template's `PPT-001_logo` — failing on any other picture anywhere in the deck |

## 8. Dependency and licence position

| Source | URL | SHA | Licence | Gate 4A |
|---|---|---|---|---|
| `m3dev/pptx-template` (`ADP-001`) | `https://github.com/m3dev/pptx-template` | `dc448cb1203443e503a558846dc1ce4c4b7ada3d` | Apache-2.0 | PASS |
| `keithmcnulty/ppt-generation` (`ADP-002`) | `https://github.com/keithmcnulty/ppt-generation` | `062c4920da96c98574bad0c6cdfd4d10eaa21e02` | CC0-1.0 | PASS |
| `Whatsonyourmind/deckforge` (`ADP-003`) | `https://github.com/Whatsonyourmind/deckforge` | `ae71696f763f85b79f7f94d85484234f57f93f63` | MIT | PASS |

**E9 audit result: clean.** The landed modules import only `python-pptx` plus the stdlib. Upstream's
`pandas`/`numpy` (CSV path) and `kiwisolver`/`PIL` (solver + text measurer) were dropped, so **no new
runtime dependency** and no R9 ADR/DEC cycle was required. Dev-only tools (`pip-licenses`, `faker`,
`hypothesis`) are absent from runtime, per Addon 6 v2 gate 4B.

**Take-list amended once under `E12`** (`DEC-064`): WS-03's overflow handler proved coupled to a
constraint solver, font files and a pydantic IR — none in `pyproject`, and a whole-package copy would
breach R13. Only `overflow.py` was taken.

## 9. Still red — and it is not this work card

`scripts/check.py` still exits 1. The cause is unchanged from the recorded baseline and blocked on M1:

```
5 failed, 11 passed, 841 deselected in 523.37s
  planted-exception recall   11/32 = 34.4 %   (bar: >= 29 of 32)
  control precision          1 fired           (bar: 0 of 8)
  High-severity recall       6/18              (bar: 18 of 18)
  extra findings             422               (bar: <= 3 unexplained per rule)
  no rule has zero coverage  14 rules          (bar: all 24 wired, none zero)
```

Blocked on the M1 corpus rebuild (`TB-020`). ruff/mypy remain unwired (`TB-015`/`TB-016`).
Neither is caused by, nor blocks, `WC-2`.

## 10. Owed

| Item | Why | Where |
|---|---|---|
| `12` §5.2 "template carries **both** bridge variants as two shapes" | The pinned `python-pptx` exposes no `XL_CHART_TYPE.WATERFALL` (verified against the installed enum: `False`), so the template ships only the stacked fallback. Fabricating a second shape would violate §3.6. | `TB-048` |
| `12` §4.1 row-count reading | "7 rows × 0.60″" contradicts the same row's 3.60″ frame and its own "never blank rows" rule. Interpreted as 6 (R1 — the spec was **not** edited to fit the code). | `DEC-065` |
| §3.4 amendment to enable the cascade | `app/engine/pptx_fill/layout.py` lands flag-gated **default OFF** (`FPA_PPT_OVERFLOW_CASCADE`). A default build is byte-identical with the flag on or off, so the module is neither dead nor behaviour-changing. | `ADR-013` |