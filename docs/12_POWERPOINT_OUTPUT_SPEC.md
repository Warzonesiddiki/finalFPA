> **Status:** Draft v0.1
> **Last updated:** 2026-10-01
> **Owning FRs/areas:** `FR-PPT-001`…`FR-PPT-009` (deck), `FR-XC-001`/`FR-AI-011` (commentary approval gate), `FR-BVA-005` (bridge), `FR-EXC-*` (exception content), `FR-FC-008` (outlook + accuracy), `FR-XC-003` (pack version), `FR-XC-009` (offline); slide structure, placeholder geometry, character budgets, native-chart specification, base-deck handling, branding, stamping
> **TL;DR (≤ 15 lines):** The deck is **exactly six slides** (`PPT-001`…`PPT-006`) — cover · executive KPIs ·
> BvA bridge · top variances with drivers · exceptions and control risks · forecast and outlook — built from
> a purpose-made `.pptx` template so layout is deterministic, fast and testable. §3 is the universal
> contract: the inch grid and its scaling to any slide size, **native-and-editable only** (no screenshots),
> the theme shared with `11`, the **character-budget formula with per-placeholder budgets and the
> prioritized trimming order** that makes overlap impossible, deterministic element ordering and naming,
> stamping + the disclaimer, AI/rule-based labelling, not-available states, accessibility and the ≤ 15 s
> budget. §4 specifies every slide and placeholder; §5 the two native charts (including the
> waterfall decision `SPK-08`); §6 client base decks; §7 cross-artifact equality with the Excel pack; §8
> files and refresh; §9 the 24-item test contract; §10 failures (`ERR-EXP-012`…`018`); §11 open items;
> §12 change control. **A trimmed slide never loses a number, a signal or a disclaimer — only prose.**

---

# 12 — POWERPOINT OUTPUT SPECIFICATION

## 1. Purpose and ownership boundary

| Concern | Owner |
|---|---|
| Slide count, slide order, placeholder geometry, fonts/sizes, character budgets, trimming rules, chart types and styling, base-deck handling, deck stamping | **`12` (this document)** |
| Which numbers appear (graph/summary/exception/forecast content, bridge driver set) | `05`, `06`, `07` via `02` FRs |
| The `CF-` colour rules and their non-colour signals | `08` §14 (rendered here per §3.3) |
| Display formatting (₹, grouping, `dd-mm-yyyy`, negatives, `—`/`n/a`, scaling) | `08` §15; rendered in Excel per `11` §3.6 |
| Commentary text, drafts, approval, provenance | `10` (AI) + `02` `FR-XC-001`; the *approval gate* for this document is `FR-PPT-008` |
| Deck generation engine, job queue, cancellation | `09` (`engine/exports`, `ADR-006`, lazy import) |
| **Cross-artifact equality of every rendered value** | `11` §11 defines the contract; this document adds the deck-side comparison set (§7) |
| Template file as a build artefact | §12 obligation (packaging, `15`, `17`) |
| Tests | **§9** (`TST-PPT-01`…`TST-PPT-24`) |

**The one-sentence rule:** *the deck is a fixed six-slide narrative whose every number is the engine's value
produced from the same filter state as the Excel pack, whose every element is natively editable, and whose
text is guaranteed to fit because the fit is computed, not hoped for.*

## 2. The deck at a glance

### 2.1 The six slides (IDs are contract)

| ID | Slide | Purpose | Primary content | Native objects | FRs |
|---|---|---|---|---|---|
| `PPT-001` | **Cover** | Identify the pack, the period, the sources and the stamp | Project + pack title · period · window · scenario · entities · **source files + batch IDs** · stamp block · logo | 6 text boxes, 1 accent bar, 1 logo picture | `FR-PPT-001`, `FR-PPT-009` |
| `PPT-002` | **Executive summary** | What happened this period, and the headline numbers | 6 KPI cards · approved executive narrative · units/grain footnote | 6 card groups (rounded rectangle + 2 text boxes each), 1 narrative text box, 1 footnote | `FR-PPT-001`, `FR-XC-001`, `DEC-009` |
| `PPT-003` | **Budget vs Actual bridge** | How budget became actual | 1 native bridge chart · right-hand driver list · tie-out line | 1 chart, 2 text boxes | `FR-BVA-005`, `FR-PPT-001` |
| `PPT-004` | **Top variances with drivers** | The five variances that matter, with reasons | Native table (5 rows) · driver/commentary column · provenance + retrieval note | 1 table, 2 text boxes | `FR-BVA-007`, `FR-XC-001`, `FR-PPT-004` |
| `PPT-005` | **Exceptions and control risks** | What needs accounting review | Count chips (open/overdue/high/unassigned) · native table (5 exceptions) · risk line · approved exception summary | 4 chips, 1 table, 2 text boxes | `FR-EXC-002`, `FR-EXC-017`, `FR-PPT-001` |
| `PPT-006` | **Forecast and outlook** | Where the year lands, and how reliable the forecast has been | Scenario + version line · 3 outlook cards (landing estimate, vs budget, accuracy) · native forecast-vs-actual chart · outlook narrative · **full disclaimer band** | 3 cards, 1 chart, 2 text boxes, 1 small-print band | `FR-FC-008`, `FR-PPT-009` |

**Fixed-six rule (decision):** the deck always contains these six slides in this order. When a slide's
required input is missing:

1. The **default** is to generate the slide with a *"Not available"* state that names the reason and the
   action (e.g. *"No locked forecast version for FY26-P09 — lock a version in the Forecast workspace."*).
   Nothing is fabricated, nothing is blank, and the audience is never left guessing why a topic is absent.
2. The user may instead choose **"Omit this slide"** in the generate dialog; the deck then has five slides
   and the cover footer states `5 of 6 slides generated — forecast slide omitted: no locked forecast version`.
3. Neither path is silent. A slide is never omitted without the count and reason being written on the deck.

Rationale: `FR-PPT-001` requires exactly six slides, a management deck that silently loses a topic is
worse than one with a stated gap, and the "omit" escape hatch preserves the kickoff's 4–6-slide latitude
for an analyst who would rather send five slides than show a placeholder. This reconciles the `08` §11.1
example (*"the forecast slide will be omitted"*) with the fixed-six default — the example's behaviour is
now the *opt-in* path, and `08` records the pointer.

### 2.2 Inputs the deck consumes (all aggregate)

| Input | Source table / view | Grain | Used by |
|---|---|---|---|
| KPI set | `KPI-001…006` calculations (`05` §5) | period × KPI | `PPT-002` |
| BvA summary totals + drivers | `bva_drivers` / `bva_*` views (`05` §7) | driver × period | `PPT-003` |
| Top-N variances | `bva_topn` (`08` §13 `CHT-003/004`) | account/CC × period | `PPT-004` |
| Exception register aggregates + rows | `exception_stats`, `FactException` | rule/severity/owner, row | `PPT-005` |
| Forecast version, landing estimate, accuracy | `FactForecastVersion`, `forecast_accuracy` (`07` §12) | group × period | `PPT-006` |
| Commentary (per-line + executive) | `Commentary` / `CommentaryVersion` (`03` §5.7) | target | `PPT-002`, `PPT-004`, `PPT-005`, `PPT-006` |
| Stamp context | the same filter JSON the Excel pack used (`11` §3.9 `FactExport`) | — | `PPT-001`, footers |

**Aggregate-only guarantee:** deck generation never reads the transaction grain (`FactActual` row level).
The query budget is ≤ 12 aggregate queries and ≤ 24 chart points per series (§3.12). This is what keeps
`NFR-004` (≤ 15 s) reachable at 250,000 rows and what makes the deck's numbers provably identical to the
Excel summary (both derive from the same aggregates, `11` §11).

## 3. Universal contract (every slide)

### 3.1 Geometry model

The **contract is the inch grid for the built-in 16:9 deck** below; every position scales to any slide
size by one rule:

| Element | Built-in 16:9 (13.333″ × 7.5″) | Scaling rule for base decks |
|---|---|---|
| Left content margin | 0.45″ | `0.45 × (slide_width / 13.333)` |
| Right content margin | 0.45″ | same |
| Content width | 12.43″ | same |
| Title band | y = 0.35″, h = 0.60″ | y unchanged, h × (slide_height / 7.5) |
| Kicker/subtitle | y = 0.95″, h = 0.30″ | same rule |
| Body area | y = 1.45″ … 6.95″ | top y unchanged; bottom scales |
| Footer band | y = 7.04″, h = 0.28″ | `y = slide_height − 0.46`, h = 0.28″ |
| Accent bar | x = 0, y = 0, w = slide_width, h = 0.08″ | h unchanged |

- The built-in deck is **16:9** (`13.333″ × 7.5″` = 12,192,000 × 6,858,000 EMU at 914,400 EMU/inch).
- A base deck of any aspect ratio (4:3 = 10″ × 7.5″, or a custom corporate size) is supported by applying
  the scale rules above; **font sizes are never scaled** (a 12 pt body stays 12 pt), only the boxes move,
  and the character-budget formula recomputes from the box width (§3.4) so fit is preserved.
- All text frames: `word_wrap = True`, `auto_size = NONE`, `vertical_anchor = TOP`, zero internal
  margins where the box is a single line, 0.05″ internal margins elsewhere. **PowerPoint's "shrink text on
  overflow" is deliberately not used**: autofit reflows when the file is opened or edited, which makes the
  layout non-deterministic and could still overlap after a font substitution. Fit is guaranteed by the
  budget, not by PowerPoint's mercy.
- Nothing is placed closer than 0.12″ to another element (the separation constant used by the overlap
  test, §9 `TST-PPT-07`).

### 3.2 Native and editable — the shape-type whitelist

`FR-PPT-002`: a human must be able to click any number and edit it in PowerPoint. Allowed shape types:

| Allowed | Used for | Rule |
|---|---|---|
| Text box | Every piece of text | Real text frames, no images of text |
| Table (`GraphicFrame` with a table) | `PPT-004`, `PPT-005` | Native PowerPoint tables; header row marked; cell text editable |
| Chart (`GraphicFrame` with a chart part) | `PPT-003`, `PPT-006` | Native charts with an **embedded editable data workbook** (`python-pptx` `replace_data`) |
| Picture | **The configured logo only** | The single permitted image; `alt text` set; size cap 2.1″ × 0.9″ (aspect preserved) |
| Auto shape / rectangle | Accent bar, KPI card backgrounds, signal chips, count chips | Filled, no text inside unless the chip is a text box |
| Line | Title rule under the title band | Thin (0.75 pt–1 pt), theme colour |

**Forbidden, everywhere:** screenshots or any rasterised table/chart; ECharts/PNG/EMF/WMF renders; grouped
shapes; SmartArt; embedded OLE objects; video/audio; external links; hyperlinks (the deck is self-contained
and offline); macros (`.pptx` only, never `.pptm`); 3-D chart effects; theme fonts that are not installed
(missing-font check in §6).

Enforcement: `TST-PPT-02` walks `slide.shapes` and asserts every shape matches the whitelist, that exactly
one picture exists on `PPT-001` (the logo) and none elsewhere, and that every chart is a chart part with a
data workbook.

### 3.3 Theme — fonts, sizes, colours

One source: `ui/theme/tokens.ts` (validated against `08` §19), rendered into the deck exactly as it is into
Excel (`11` §3.7). The literal v1 values:

| Token | Value | Used by |
|---|---|---|
| `brand.primary` | `#1F3A5F` (Settings-overridable) | Accent bar, title text, card value text, chart series 3 |
| `brand.secondary` | `#B7791F` (Settings-overridable) | Signal chips for "needs attention", rule under titles, count chips |
| `text.primary` | `#1F2937` | Body text |
| `text.secondary` | `#6B7280` | Kickers, footnotes, stamp labels |
| `surface.card` | `#F7F8FA` | KPI/outlook card backgrounds |
| `semantic.favourable` | fill `#E8F5E9`, text `#1B5E20` | Favourable values, bridge favourable bars |
| `semantic.unfavourable` | fill `#FDECEA`, text `#B3261E` | Adverse values, bridge adverse bars |
| `semantic.neutral` | text `#6B7280` | `—` / `n/a` values |
| `semantic.warning` | fill `#FFF4E5`, text `#8A5300` | Overdue chips, not-available states |
| `severity.high/med/low` | `#7A1C16`, `#7A5200`, `#1F5C2C` on the `11` §3.7 badge fills | Severity column text |
| `font.heading` | Calibri (house-style override permitted) | Titles, card values |
| `font.body` | Calibri (house-style override permitted) | Everything else |

**Rules:** semantic colours are **non-negotiable** (a house style may change brand colours only, mirroring
`11` §9.2); every semantic colour is paired with a text signal (§3.9); any colour change is checked for AA
contrast against its background with a documented accessible substitute on failure (`01` §17); chart series
colours come from this table, never from the app's ECharts defaults.

### 3.4 Character budgets and the trimming order (the no-overlap guarantee)

Text cannot overflow because **the budget is computed** from box geometry and font size, and the engine
asserts the fit before writing.

**Formula (deterministic, implemented once in `app/engine/exports/ppt_fit.py`):**

```
chars_per_line = floor(box_width_inches * 72 / (AVG_ADVANCE * font_size_pt))     # AVG_ADVANCE = 0.50
line_height_in = 1.22 * font_size_pt / 72
lines_available = floor(box_height_inches / line_height_in)
design_max_lines = min(lines_available - 3, configured_max_for_placeholder)      # 3-line safety slack
budget_chars = chars_per_line * design_max_lines
```

**Slack rules:** a prose text box must fit at least `design_max_lines + 1` lines at its font size; a table cell or line-list entry must satisfy `cell_height ≥ design_max_lines × line_height + 0.20″`. Both are asserted by `TST-PPT-05`.

`AVG_ADVANCE = 0.50` is the conservative Calibri mixed-case average advance (measured values run
0.44–0.48; 0.50 builds in headroom). The constants and the per-placeholder budgets are **frozen in this
document**; the engine reads them from a table, never from a hard-coded number in a template.

**Budgets (built-in 16:9 deck; these are the numbers the tests assert):**

| Placeholder | Font | Box (w × h, in) | chars/line | design max lines | **Budget** |
|---|---|---|---|---|---|
| `PPT-001` title | 32 pt | 12.43 × 0.80 per line | 55 | 1 | **55** |
| `PPT-001` pack line | 20 pt | 12.43 × 0.50 per line | 89 | 1 | **89** |
| `PPT-001` period line | 14 pt | 12.43 × 0.35 per line | 127 | 1 | **127** |
| `PPT-001` source-file block (8 lines) | 10 pt | 7.50 × 1.60 | 108 | 8 | **864** |
| `PPT-001` stamp block (14 lines) | 9 pt | 4.50 × 2.40 | 72 | 14 | **1008** |
| `PPT-002` card label | 10 pt | 3.77 × 0.22 per line | 54 | 1 | **54** |
| `PPT-002` card value | 24 pt | 3.77 × 0.45 per line | 22 | 1 | **22** |
| `PPT-002` card comparison | 10 pt | 3.77 × 0.22 per line | 54 | 1 | **54** |
| `PPT-002` narrative | 12 pt | 12.43 × 1.88 per line | 149 | 6 | **894** |
| `PPT-002` footnote | 9 pt | 12.43 × 0.24 per line | 198 | 1 | **198** |
| `PPT-003` driver-list entry (×6) | 10 pt | 3.58 × 0.40 per line | 51 | 1 | **51** |
| `PPT-003` tie-out line | 9 pt | 12.43 × 0.28 per line | 198 | 1 | **198** |
| `PPT-004` table cell (account) | 10 pt | 3.04 × 0.60 | 43 | 2 | **86** |
| `PPT-004` table cell (driver) | 10 pt | 2.27 × 0.60 | 32 | 2 | **64** |
| `PPT-004` provenance strip | 9 pt | 12.43 × 0.30 per line | 198 | 1 | **198** |
| `PPT-004` notes block | 9 pt | 12.43 × 0.90 per line | 198 | 3 | **594** |
| `PPT-005` chip label | 10 pt | 2.68 × 0.28 per line | 38 | 1 | **38** |
| `PPT-005` chip value | 18 pt | 2.68 × 0.34 per line | 21 | 1 | **21** |
| `PPT-005` risk line | 9 pt | 12.43 × 0.22 per line | 198 | 1 | **198** |
| `PPT-005` table cell (subject) | 9 pt | 3.24 × 0.54 | 51 | 2 | **102** |
| `PPT-005` summary | 11 pt | 12.43 × 0.94 per line | 162 | 4 | **648** |
| `PPT-006` scenario line | 12 pt | 12.43 × 0.35 per line | 149 | 1 | **149** |
| `PPT-006` card label | 10 pt | 3.77 × 0.22 per line | 54 | 1 | **54** |
| `PPT-006` card value | 22 pt | 3.77 × 0.42 per line | 24 | 1 | **24** |
| `PPT-006` card comparison | 10 pt | 3.77 × 0.22 per line | 54 | 1 | **54** |
| `PPT-006` outlook narrative | 11 pt | 4.58 × 3.10 per line | 59 | 12 | **708** |
| `PPT-006` disclaimer band | 8 pt | 12.43 × 0.62 per line | 223 | 3 | **669** |
| Footer (every slide) | 8 pt | 9.30 × 0.28 per line | 167 | 1 | **167** |
| Page-number string | 8 pt | 2.60 × 0.28 per line | 46 | 1 | **46** |

**Trimming algorithm (priority order — `FR-PPT-004`):**

1. **Protected content is never trimmed or reordered:** every number and its unit, period labels, the
   signal words (`Fav ▲` / `Adv ▼` / `—` / `n/a`), severity words, the scenario/version name, the AI /
   rule-based provenance label, and the disclaimer. If protected content alone exceeds a budget, generation
   stops with `ERR-EXP-013` rather than hiding a signal — this is a defect to fix in the layout, not a
   silent degradation.
2. **Drop whole trailing sentences** while over budget. Sentence segmentation is deterministic: split on
   `. `, `; `, ` — ` and newline, keeping the delimiter with the preceding sentence.
3. If still over: drop the **least material remaining sentence**, where sentences containing a number whose
   absolute value is ≥ the row's materiality threshold (`CALC-080`) rank last to be dropped, then by the
   sentence's position (later first). Deterministic and explainable.
4. If still over (a single sentence larger than the budget): truncate at the last word boundary and append
   ` …`.
5. Whenever any trimming happened, the placeholder's surface gets the 8 pt footnote
   `Trimmed for space — full text in the Excel pack and the commentary editor.`
6. **The speaker notes always carry the full, untrimmed text** (this is the retrieval path `FR-PPT-004`
   requires), with the trim marker `[slide text trimmed to N characters]` where applicable.
7. Trimming never edits a digit, never reorders sentences, never inserts words.

**Overflow protection is structural:** because `design_max_lines = lines_available − 3`, a placeholder whose
budget is exceeded by an unforeseen font substitution still has three blank lines of room, and the overlap
test (`TST-PPT-07`) asserts that no two shape bounding boxes intersect on any slide, including the
long-commentary fixture (a 4,000-character narrative).

### 3.5 Fixed vs variable content

| Fixed (identical on every deck) | Variable (generated) |
|---|---|
| Slide sequence, shape order, shape names, positions, fonts, colours | Every number, period label, entity list, project name |
| Placeholder set per slide (a shape is never missing because data was missing) | KPI selection from the configured set (`DEC-009`) |
| Footer band layout, disclaimer placement | Narrative and commentary text (approved versions only) |
| Table column set, chart type | Row counts shown (5 variance rows, 6 exception rows — fewer only when the data set is smaller) |
| The six-slide contract | The optional logo (absent only with a stated warning) |

### 3.6 Deterministic ordering, naming and layouts

| Aspect | Rule |
|---|---|
| Template | A purpose-made template `packaging/templates/FPAMonthEndCopilot_v1.pptx` (16:9) with seven layouts: `FPA-PPT-001`…`FPA-PPT-006` + `FPA-PPT-DISCLAIMER`, each containing **named shapes** |
| Shape naming | `PPT-00N_<role>` (e.g. `PPT-002_kpi3_value`, `PPT-003_chart_bridge`). The engine resolves shapes **by name**; a missing name aborts with `ERR-EXP-014` (template damaged) rather than producing a half-blank slide |
| Add/edit order | The engine edits the template's shapes in a fixed order (documented in `ppt_spec.py` as the canonical order: title → kicker → body blocks top-to-bottom, left-to-right → charts → tables → cards → accent → logo → footer) so the XML order is stable |
| Z-order | Accent bar and card backgrounds are **behind** text (`shape.z_order` set explicitly by insertion order in the template, never re-ordered at runtime) |
| Unused placeholders | Removed from the layout by the template author (not at runtime), so the deck has no empty placeholders an editor would have to delete |
| Determinism test | Generating twice from the same context produces byte-identical slide XML after normalising the two timestamp fields (`TST-PPT-08`) |
| No runtime layout construction | The engine never builds a layout from scratch: it copies the template and fills it. Faster (helps `NFR-004`) and testable |

### 3.7 Stamping, footer band and the disclaimer

| Placement | Content |
|---|---|
| `PPT-001` stamp block (right column, 12 lines at 9 pt) | Project · Entity(ies) · Period(s) · Window · Scenario · Budget version · Forecast version + lock state · Pack version (`vN` or `unissued draft`) · Generated `dd-mm-yyyy hh:mm` · App version · Rule set version · Source batch IDs · Units/scale · AI content provenance (`none` / `AI draft approved by <name> at <ts>` / `rule-based narrative`) · House style profile · Sample-data flag |
| `PPT-001` source-files block | Up to 8 lines `File name · batch · N rows`, then `… (+N more files — full list in the Excel pack)`. This satisfies "source files" from Kickoff §11 |
| Footer band, **every slide** | Left: the short-form disclaimer verbatim (`01` §15.1, 134 characters). Right: `Slide N of 6 · Pack vN · FY26-P09`. Both 8 pt, `text.secondary` |
| `PPT-006` disclaimer band (8 pt small print) | The **full canonical disclaimer** verbatim (`01` §15.1) — the "back slide" requirement of `FR-PPT-009` is satisfied by the last slide carrying the full text; with a client base deck that has its own disclaimer layout, the text goes there instead (§6) |
| Speaker notes | Slide 1: the full disclaimer + the stamp as a JSON block (machine-readable, `TST-PPT-09`). Slide 6: the full disclaimer. Every slide: the filter context line and, where text was trimmed, the full untrimmed text |
| Document properties | `title` = `<Project> — <Period> — Month-end pack`, `author` = `FP&A Month-End Copilot <version>`, `comments` = `Pack vN · stamp hash <content hash>`, `subject` = the human filter context |
| Not-available slides | A `semantic.warning` chip with the reason and the action, plus the same text in the notes. Never a blank slide, never a fabricated value |
| Sample-data mode | When `Pack_Stamp_SampleData = Yes`: pale `#FFF9C4` title band, a `SAMPLE DATA — NOT CLIENT DATA` footnote on every slide, and the flag in the stamp |

**Speaker-notes stamp (slide 1) — the machine-readable block the tests read** (`TST-PPT-09`): the notes text
contains the full disclaimer and then exactly one JSON object, delimited by the lines
`--- FPA STAMP (JSON) ---` / `--- END FPA STAMP ---`:

```json
{
  "schema": "fpa.ppt.stamp.v1",
  "slide": "PPT-001",
  "generated_at": "2026-10-01T14:22:31+05:30",
  "project": "Acme Manufacturing",
  "entities": ["IN01", "IN02"],
  "periods": ["FY26-P09"],
  "window": "MTD",
  "scenario": "Base",
  "budget_version": "FY26-Approved",
  "forecast_version": "Base v3",
  "forecast_locked": true,
  "pack_version": 3,
  "issued": true,
  "file_version": 3,
  "app_version": "0.9.0",
  "schema_version": "1",
  "rule_set_version": "2026-09-30",
  "batch_ids": [1041, 1042, 1043],
  "filter_json": { "entity": ["IN01", "IN02"], "period": ["FY26-P09"], "window": "MTD", "scenario": "base" },
  "filter_human": "Entity=IN01, IN02 · Period=FY26-P09 · Window=MTD · Scenario=Base",
  "units": "₹ whole units",
  "grouping": "Indian (lakh/crore)",
  "ai_content": { "used": true, "prompt_ids": ["PROMPT-01"], "approved_by": "A. Sharma", "approved_at": "2026-10-01T13:40:00+05:30" },
  "sample_data": false,
  "stale": false,
  "omitted_slides": [],
  "content_hash": "sha256:9f2c...",
  "base_deck": { "file": "Acme_Management_Monthly.pptx", "required_shapes": 43, "mapped_shapes": 41, "unmapped": ["PPT-005_risknote"], "preserved_slides": 2 },
  "notes_full_text": { "PPT-002_narrative": 1180, "PPT-004_driver_5600": 240, "PPT-006_outlook": 890 }
}
```

`notes_full_text` records the character count of each full (untrimmed) text stored in the notes, so
`FR-PPT-004`'s "retrievable from the source" claim is itself measurable. An omitted slide appears in
`omitted_slides` with its reason; the field is `[]` in the normal six-slide case.


### 3.8 AI and rule-based labelling (`FR-PPT-008`, `10` §12)

| Case | Slide treatment | Notes treatment |
|---|---|---|
| Approved AI draft | The text is shown with the label **"AI draft — review before use."** in the placeholder's provenance strip (9 pt, `semantic.neutral`) + `Approved by <name> on <dd-mm-yyyy>` | Full provenance: prompt id + version, model, generation timestamp, approval actor and timestamp, evidence references |
| Rule-based narrative (no key configured) | Label **"Rule-based narrative"** — never the AI label (the app never blurs the two, `10` §2) | The generator name and the driver data used |
| Unapproved AI draft | **Not rendered at all.** The placeholder falls back to the rule-based narrative where one exists, or to the not-available state | Notes state why: `AI draft present but not approved — showing rule-based narrative` |
| No commentary at all | The placeholder is absent from the slide (it is a variable block, not a fixed placeholder) and the slide's footnote says `No commentary recorded for this period.` | — |
| AI disabled | Only rule-based text can appear; the label is always present | — |

Approval is an explicit user action in `SCR-031` (`10` §12); the deck never solicits, generates or applies
AI text during generation. Deck generation therefore works fully offline with AI disabled (`FR-XC-009`).

### 3.9 Number, label and signal conventions (identical to app and Excel)

1. Money: `₹` symbol, project grouping (Indian default: `₹ 1,08,00,000.00`), 2 dp, negatives in
   parentheses, unit/scale label wherever scaled (`₹ in lakhs`) — the same strings as `08` §15 and
   `11` §3.6.
2. Percentages: 1 dp (`8.0%`); percentage points: `+1.5 pp`; ratios: 2 dp.
3. Dates: `dd-mm-yyyy`; timestamps `dd-mm-yyyy hh:mm`.
4. `—` = nothing to compare; `n/a` = undefined (zero denominator); `₹ 0.00` = a real zero. Never
   interchangeable, never rendered as colour alone.
5. Every semantic colour carries its text signal (`Fav ▲`, `Adv ▼`, `High`, `Overdue 12 d`) — the deck is
   readable in greyscale and in a photocopy (`P19`).
6. Footnote line on `PPT-002`/`PPT-003`/`PPT-006` wherever more than one entity is in scope:
   `Simple sum — no eliminations`. Rounding footnote wherever displayed components may not sum
   (`CALC-031`).
7. Every chart axis label carries the unit and scale; the deck never shows an unlabelled axis.

### 3.10 Not-available and empty states per slide

| Slide | Required input | Not-available state (default path) |
|---|---|---|
| `PPT-001` | Filter context | Cannot occur (context always exists) |
| `PPT-002` | At least one KPI with data | Cards show `—` with the reason `No actuals loaded for this period`; the narrative is replaced by the rule-based statement |
| `PPT-003` | A single-period bridge | Not available when the filter spans periods: *"The bridge is a single-period view — apply a single period to see it."* Chart replaced by a text block of the same height (no empty chart frame) |
| `PPT-004` | Variance rows | *"No variances to report for this filter."* Table replaced by one centred text block |
| `PPT-005` | Rule run exists | *"No exception run has been completed for this period."* + action; a genuine empty register renders *"No open exceptions — nothing requires review."* |
| `PPT-006` | A forecast version | *"No forecast version for FY26-P09 — lock a version in the Forecast workspace."*; if a **draft** exists: *"Draft forecast v4 — not locked. This deck is marked unissued."* |
| Any slide | Stale derived results | A `semantic.warning` corner chip: *"Re-run required before issue — <what changed>."* (mirrors `CF-009`) |

### 3.11 Accessibility

| Requirement | Rule |
|---|---|
| Reading order | Title → kicker → cards/table/chart in document order → narrative → footer; asserted by test |
| Alt text | Every chart carries a generated alt text ≤ 250 characters stating the headline (e.g. *"Waterfall: budget ₹1,57,70,000 to actual ₹1,66,45,000; largest adverse driver materials ₹78,000"*); the logo alt text is the project name |
| Tables | Header row marked as a header row; no merged cells; one idea per column |
| Contrast | AA (4.5:1) for text on fills, checked for the v1 theme and re-checked when house styles or brand colours change |
| Colour independence | All semantic colours carry text signals (§3.9) and the greyscale check is part of the golden test |
| Fonts | Body text ≥ 9 pt (table cells) / ≥ 10 pt elsewhere; nothing below 8 pt except the two sanctioned 8 pt bands (footer, disclaimer) |
| Motion | No animation, no transitions, no auto-advance in generated decks |

### 3.12 Performance, cancellation and atomicity

| Aspect | Budget / rule |
|---|---|
| Generation | ≤ 15 s end-to-end on a 4-core laptop with a 250k-row project (`NFR-004`), progress + Cancel in the job drawer |
| Queries | ≤ 12 aggregate queries; never the transaction grain; ≤ 24 points per chart series |
| Template load | Template opened from disk (≤ 3 MB), never rebuilt at runtime |
| Embedded chart data | One small data workbook per chart (≤ 8 series × 24 points) — invisible in the deck, editable via "Edit Data" |
| Cancellation | Checked between slides and between queries; on cancel **no file is written** (temp path → atomic move on success), mirroring `11` §12 |
| Memory | Within `NFR-005` (≤ 1.5 GB during other workloads); deck generation itself stays far below |
| Output size | Typical ≤ 3 MB; hard guard at 25 MB with `ERR-EXP-018` and the suggestion to drop preserved base-deck slides |
| Offline | No network access at any point (`FR-XC-009`); AI text, if used, was generated earlier and is already stored |

### 3.13 Comment provenance objects rendered in the deck

| Content | Rendered where | Includes provenance strip? |
|---|---|---|
| Executive narrative | `PPT-002` narrative box | Yes (label + approver + date) |
| Per-line commentary (top rows) | `PPT-004` driver column | Yes, once in the slide's provenance line, not per cell (space) |
| Exception summary | `PPT-005` summary box | Yes |
| Outlook text | `PPT-006` narrative | Yes |
| Bridge driver notes | `PPT-003` right-hand list | No (engine-derived driver text, not commentary) |

When **any** rendered text is AI-derived, the deck's stamp (`PPT-001`) lists the approved drafts with their
prompt versions (`Pack_Stamp_AIContent` semantics, `11` §3.2 field 26).

## 4. Slide-by-slide specification

Every geometry below is `x, y, w, h` in inches **for the built-in 16:9 deck**; base decks scale per §3.1.
Wireframes are proportional, not literal. Shape names are the runtime contract (§3.6). Every slide carries
the footer band (§3.7); the footer is omitted from the tables below to avoid repetition.

### 4.1 `PPT-001` — Cover

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ accent bar ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ [logo]    │
│                                                                              │
│   Alpha Industries Pvt Ltd                                                   │
│   Month-end pack — September 2026                                            │
│   FY26-P09 · MTD · Base · Entities: IN01, IN02                               │
│                                                                              │
│   SOURCES                                        STAMP                       │
│   D365 GL Sep-26.xlsx · batch 1041 · 96,412 rows  Project    Alpha Indust…   │
│   Payroll Sep-26.csv · batch 1042 · 1,204 rows    Period     FY26-P09 (MTD)  │
│   Procurement Sep-26.xlsx · batch 1043 · 31,880…  Generated  01-10-2026 14:22│
│   … (+1 more file — full list in the Excel pack)  Pack       v3 …            │
│                                                  Units      ₹ whole units   │
│                                                  Sources    1041, 1042, …    │
├──────────────────────────────────────────────────────────────────────────────┤
│ Potential exceptions only — advisory tool, not professional advice.   Slide 1 of 6 │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry (x, y, w, h) | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-001_title` | Text box | 0.45, 2.20, 12.43, 0.80 | Calibri 32 pt bold, `brand.primary` | 55 | Project name (Settings) |
| `PPT-001_packline` | Text box | 0.45, 3.05, 12.43, 0.50 | Calibri 20 pt, `text.primary` | 85 | `Month-end pack — <Month YYYY>` (period label from `05` §2) |
| `PPT-001_periodline` | Text box | 0.45, 3.60, 12.43, 0.35 | Calibri 14 pt, `text.secondary` | 125 | `<Period(s)> · <Window> · <Scenario> · Entities: <codes>` |
| `PPT-001_sources` | Text box | 0.45, 4.15, 7.50, 1.60 | Calibri 10 pt, `text.primary`, 8 lines | 100 / line (800 total) | Header line `SOURCES` (10 pt bold, `text.secondary`) + one line per batch: `<file> · batch <id> · <N> rows`; overflow line `… (+N more files — full list in the Excel pack)` |
| `PPT-001_stamp` | Text box | 8.38, 4.15, 4.50, 2.40 | Calibri 9 pt, 14 lines (label `text.secondary`, value `text.primary`) | 70 / line | Header line `STAMP` + the 12 stamp fields (§3.7) |
| `PPT-001_logo` | Picture | 10.83, 0.35, ≤ 2.05 × ≤ 0.90 (aspect preserved) | — | — | Settings logo file; alt text = project name; absent with a stated warning (`ERR-EXP-016`) |
| `PPT-001_accent` | Rectangle | 0, 0, slide width, 0.08 | `brand.primary` fill, no border | — | Brand accent |

**Rules:** the title is the only 30 pt+ element in the deck (identity, not content); source lines beyond 8
collapse into the `… (+N more files)` line (never a ninth line); the stamp always prints all 12 fields even
when a value is `none`; a sample-data deck adds the pale title band and the `SAMPLE DATA — NOT CLIENT DATA`
footnote line (§3.7). Speaker notes: full disclaimer + the stamp JSON (§3.7).

### 4.2 `PPT-002` — Executive summary

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  │
│  Executive summary — FY26-P09                                                │
│  MTD · Base · Budget FY26-Approved · 2 entities                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                │
│  │ ACTUAL          │ │ BUDGET          │ │ VARIANCE        │                │
│  │ ₹ 1,66,45,000.00│ │ ₹ 1,57,70,000.00│ │ +₹ 8,75,000.00  │                │
│  │ vs PY +12.4%    │ │ as budgeted     │ │ +5.5% · Adv ▼   │                │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                │
│  │ GROSS MARGIN %  │ │ BUDGET BURN %   │ │ EXCEPTIONS OPEN │                │
│  │ 40.0%           │ │ 25.8%           │ │ 14 · 2 overdue  │                │
│  │ vs budget +1.2 pp│ │ YTD vs annual  │ │ 3 high          │                │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘                │
│  Executive narrative · approved by A. Sharma, 01-10-2026                     │
│  September landed 5.5% above budget, driven by repairs …                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ ₹ whole units · month × account × cost centre · Simple sum — no eliminations  │
│ Potential exceptions only — advisory tool, not professional advice.   Slide 2 of 6 │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-002_title` | Text box | 0.45, 0.35, 12.43, 0.60 | 24 pt bold, `brand.primary` | 70 | `Executive summary — <period>` |
| `PPT-002_kicker` | Text box | 0.45, 0.95, 12.43, 0.30 | 12 pt, `text.secondary` | 140 | `<Window> · <Scenario> · Budget <version> · N entities` |
| `PPT-002_kpi{1-6}_card` | Rounded rectangle | cards at y = 1.45 and 3.10; x = 0.45, 4.68, 8.91; w = 3.97, h = 1.45 | `surface.card` fill, no border | — | Card background + the left signal chip (0.06″ wide, `brand.secondary` or `semantic.unfavourable`) |
| `PPT-002_kpi{1-6}_label` | Text box | card x + 0.16, card y + 0.10, 3.77, 0.22 | 10 pt bold, `text.secondary`, letter-spaced | 54 | KPI label (`ACTUAL`, `BUDGET`, `VARIANCE`, + 3 configured) |
| `PPT-002_kpi{1-6}_value` | Text box | card x + 0.16, card y + 0.34, 3.77, 0.45 | 24 pt bold, `brand.primary` (or `semantic.*` for the variance card) | 22 | The KPI value at display precision |
| `PPT-002_kpi{1-6}_compare` | Text box | card x + 0.16, card y + 0.86, 3.77, 0.22 | 10 pt, `text.secondary`; signal words in `semantic.*` | 54 | Comparison line with its signal (`vs PY +12.4%`, `+5.5% · Adv ▼`) |
| `PPT-002_narrative_label` | Text box | 0.45, 4.30, 12.43, 0.22 | 9 pt, `text.secondary` | 198 | Provenance strip: `Executive narrative · approved by <name>, <date>` / `AI draft — review before use.` / `Rule-based narrative` / `No commentary recorded for this period.` |
| `PPT-002_narrative` | Text box | 0.45, 4.64, 12.43, 1.88 | 12 pt, `text.primary` | **894** | Approved executive narrative (`Commentary` scope `executive`) |
| `PPT-002_footnote` | Text box | 0.45, 6.64, 12.43, 0.24 | 9 pt, `text.secondary` | 198 | `<Units> · <grain> · Simple sum — no eliminations` (+ rounding note when it applies) |

**KPI selection (`DEC-009`):** three fixed cards — Actual, Budget, Variance (money + % + signal) — plus
three configurable cards from the KPI library (`05` §5): defaults **Gross margin %**, **Budget burn %**,
**Exceptions open**; the user may swap any of the three in Settings → Branding/Reporting. Each card's
comparison line is defined per KPI (`vs PY`, `vs budget`, `YTD vs annual`, `count · overdue · high`).
**Rules:** the variance card carries `Δ` money, `%` and its signal word — the three-token pattern from
`08` §15; no card shows a bare number without its period/comparison; a KPI with `n/a` shows `n/a` and the
reason in the comparison line (never `0.0%`).

### 4.3 `PPT-003` — Budget vs Actual bridge

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BvA bridge — FY26-P09                                                       │
│  MTD · Base · drivers ordered by materiality                                 │
│  ┌────────────────────────────────────────────┐  TOP DRIVERS                │
│  │  1,57,70,000 ────────────────────┐         │  ▼ Materials       +78,000   │
│  │      ▼ Materials  +78,000        │         │  ▼ Contractors   +1,40,000   │
│  │      ▼ Contractors +1,40,000     │         │  ▲ Repairs        −25,000    │
│  │      ▲ Repairs    −25,000        │         │  ▼ Utilities       +2,000    │
│  │      ▼ Utilities  +2,000         │         │  ▼ Opex other     +1,80,000  │
│  │           └──────── 1,66,45,000  │         │                             │
│  └────────────────────────────────────────────┘  Opening + Σ drivers = Closing — OK │
│  ₹ whole units · month × account × cost centre                              │
│  Potential exceptions only — advisory tool, not professional advice.  Slide 3 of 6 │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-003_title` | Text box | 0.45, 0.35, 12.43, 0.60 | 24 pt bold, `brand.primary` | 70 | `BvA bridge — <period>` |
| `PPT-003_kicker` | Text box | 0.45, 0.95, 12.43, 0.30 | 12 pt, `text.secondary` | 140 | `<Window> · <Scenario> · drivers ordered by materiality` |
| `PPT-003_chart_bridge` | Chart | 0.45, 1.45, 8.60, 4.95 | §5.2 | — | Native bridge chart from the `BvA Bridge` data (`11` §4.3) |
| `PPT-003_drivers` | Text box | 9.30, 1.45, 3.58, 4.95 | Header 10 pt bold; entries 10 pt on a 0.40″ line pitch (6 entries = 2.64″) | 51 / entry (306) | Header `TOP DRIVERS` + exactly the 6 drivers the chart plots: `<▲/▼> <driver> <signed amount>`, ordered by ‖amount‖ descending; the list order and the chart order are identical by construction |
| `PPT-003_tieout` | Text box | 0.45, 6.54, 12.43, 0.28 | 9 pt, `text.secondary` | 190 | `Opening + Σ drivers = Closing — OK` (or the named difference) · `<Units> · <grain>` |

**Rules:** the chart and the driver list read from the **same** driver set in the same order (the chart's
step order equals the list order — a test asserts it); the closing value must equal the `BvA Summary`
actual total and the opening the budget total for the same filter (§7); when the bridge is not available
(§3.10) both the chart shape and the driver list are replaced by one text block occupying the chart's
rectangle, so the slide never has an empty chart frame.

### 4.4 `PPT-004` — Top variances with drivers

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Top variances — FY26-P09                                                    │
│  MTD · Base · 5 largest absolute variances of 41 lines                       │
│  ┌──────────────┬────────────┬────────────┬───────────┬──────┬──────┬───────────────┐
│  │ Account      │ Actual     │ Budget     │ Variance  │ Var %│ Sig. │ Driver        │
│  ├──────────────┼────────────┼────────────┼───────────┼──────┼──────┼───────────────┤
│  │ 5600 Contr.  │9,60,000.00 │8,20,000.00 │+1,40,000  │+17.1%│Adv ▼ │Third-party …  │
│  │ 5300 Material│6,18,000.00 │5,40,000.00 │+78,000    │+14.4%│Adv ▼ │Steel price …  │
│  │ 5200 Repairs │3,55,000.00 │3,80,000.00 │−25,000    │ −6.6%│Fav ▲ │Two jobs moved…│
│  └──────────────┴────────────┴────────────┴───────────┴──────┴──────┴───────────────┘
│  Commentary: approved by A. Sharma, 01-10-2026 · Full commentary for the top 10 lines in the notes   │
│  Potential exceptions only — advisory tool, not professional advice.        Slide 4 of 6             │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-004_title` | Text box | 0.45, 0.35, 12.43, 0.60 | 24 pt bold, `brand.primary` | 70 | `Top variances — <period>` |
| `PPT-004_kicker` | Text box | 0.45, 0.95, 12.43, 0.30 | 12 pt, `text.secondary` | 140 | `<Window> · <Scenario> · 5 largest absolute variances of <N> lines` (+ `· sorted adverse-first` when applicable) |
| `PPT-004_table` | Table | 0.45, 1.45, 12.43, 3.60 (7 rows × 0.60″) | Header 10 pt bold white on `brand.primary`; body 10 pt; numbers right-aligned | 86 (account), 64 (driver) | Columns **Account** (3.20″) · **Actual** (1.50″) · **Budget** (1.50″) · **Variance** (1.65″) · **Var %** (1.15″) · **Sig.** (1.00″) · **Driver** (2.43″) = 12.43″. Rows = top 5 by ‖variance‖; fewer rows only when fewer lines exist (never blank rows) |
| `PPT-004_provenance` | Text box | 0.45, 5.20, 12.43, 0.30 | 9 pt, `text.secondary` | 198 | `Commentary: approved by <name>, <date>` / `AI draft — review before use.` / `Rule-based narrative` / `No commentary recorded for this period.` |
| `PPT-004_notes_line` | Text box | 0.45, 5.62, 12.43, 0.90 | 9 pt, `text.secondary` | 594 | The one-line driver summary for rows 6–10 (engine-derived), the retrieval line `Full commentary for the top 10 lines: speaker notes, the Excel pack and the commentary editor.`, and the materiality note when `<N>` lines exist but fewer than 5 are material |

**Rules:** the driver cell shows the **approved commentary** for that line when one exists, otherwise the
engine-derived driver sentence (a deterministic one-liner from the variance's largest contributing
accounts). The row set is *always* the top 5 by absolute variance — a materiality threshold never removes
rows from this slide (the threshold is a consideration for the reader, not a filter here); the kicker
states the count of lines considered so the audience knows the slide is a selection. Signal words are
always present. Speaker notes list the top-10 rows with full numbers and full commentary.

### 4.5 `PPT-005` — Exceptions and control risks

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Exceptions and control risks — FY26-P09                                     │
│  Rule set 2026-09-30 · run 118 · 01-10-2026 14:05                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │ OPEN  14   │ │OVERDUE  2  │ │ HIGH   3   │ │UNASSIGNED 2│                 │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘                 │
│  ┌──────────────┬───────────────┬──────────┬──────┬────────┬──────────────┐  │
│  │ Rule         │ Subject       │ At risk  │ Sev. │ Owner  │ Status/Age   │  │
│  │ Dup. invoice │ V-00931/INV-… │ 45,000   │ High │ Rahul  │ Open · 4 d   │  │
│  │ Cut-off      │ V-00412/29-Sep│3,20,000  │ High │ Aarti  │ In rev · 6 d │  │
│  └──────────────┴───────────────┴──────────┴──────┴────────┴──────────────┘  │
│  Exception summary: three duplicate-invoice pairs …                          │
│  Potential exceptions only — requires accounting review.      Slide 5 of 6    │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-005_title` | Text box | 0.45, 0.35, 12.43, 0.60 | 24 pt bold, `brand.primary` | 70 | `Exceptions and control risks — <period>` |
| `PPT-005_kicker` | Text box | 0.45, 0.95, 12.43, 0.30 | 12 pt, `text.secondary` | 140 | `Rule set <version> · run <id> · <timestamp>` (+ `· rules disabled: <n>` when any rule is disabled) |
| `PPT-005_risknote` | Text box | 0.45, 2.24, 12.43, 0.22 | 9 pt, `text.secondary` | 198 | `Potential exception — requires accounting review. These are leads, not verdicts.` + `Σ amount at risk ₹… (indicator only)` |
| `PPT-005_chip{1-4}` | Rectangle | x = 0.45, 3.59, 6.73, 9.87; y = 1.45; w = 3.00, h = 0.75 | `surface.card`; the overdue chip uses `semantic.warning` fill | — | Chip background; label + value text boxes inside |
| `PPT-005_chip{1-4}_label` | Text box | chip x + 0.16, 1.55, 2.68, 0.28 | 10 pt bold, `text.secondary` | 38 | `OPEN` · `OVERDUE` · `HIGH` · `UNASSIGNED` |
| `PPT-005_chip{1-4}_value` | Text box | chip x + 0.16, 1.80, 2.68, 0.34 | 18 pt bold, `text.primary` (`semantic.warning` on the overdue chip) | 20 | The count (`14`, `2`, `3`, `2`) |
| `PPT-005_table` | Table | 0.45, 2.58, 12.43, 3.24 (6 rows × 0.54″) | Header 9 pt bold white on `brand.primary`; body 9 pt | 102 (subject) | Columns **Rule** (2.30″) · **Subject** (3.40″) · **At risk** (1.50″) · **Sev.** (1.00″) · **Owner** (1.40″) · **Status / Age** (2.83″) = 12.43″. Rows = top 5 by severity then amount at risk; fewer only when fewer exist (never blank rows) |
| `PPT-005_summary` | Text box | 0.45, 5.94, 12.43, 0.94 | 11 pt, `text.primary` | **648** | Approved exception summary (`PROMPT-03` output or rule-based equivalent), with its provenance strip on the first line at 9 pt |

**Rules:** severity is always rendered as a word (`High` / `Med` / `Low`) plus its mark; `Overdue` rows
carry the age text; the amount-at-risk total is labelled an **indicator**, never a control total (the same
caveat as `11` §4.5); the risk line sits above the table so the caveat is read first; when the register is
empty the table is replaced by one centred text block
*"No open exceptions — nothing requires review."* and the chips show zeros (a visible zero is
information).

### 4.6 `PPT-006` — Forecast and outlook

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Forecast and outlook — FY26-P09                                             │
│  Scenario Base · version v3 (locked 30-09-2026) · method mix: remaining budget 62% / run rate 38% │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                    │
│  │ LANDING EST.   │ │ VS ANNUAL BUDG.│ │ ACCURACY (MAPE)│                    │
│  │ ₹ 12,84,00,000 │ │ +₹ 34,00,000   │ │ 1.5% · bias +8k│                    │
│  └────────────────┘ └────────────────┘ └────────────────┘                    │
│  ┌──────────────────────────────┐   Outlook                                  │
│  │  actual ── forecast ┈┈ budget│   The forecast assumes …                   │
│  └──────────────────────────────┘                                            │
│  Full advisory disclaimer text …                                             │
│  Potential exceptions only — advisory tool, not professional advice. Slide 6 of 6 │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Shape name | Type | Geometry | Font / size / colour | Budget | Content / source |
|---|---|---|---|---|---|
| `PPT-006_title` | Text box | 0.45, 0.35, 12.43, 0.60 | 24 pt bold, `brand.primary` | 70 | `Forecast and outlook — <period>` |
| `PPT-006_scenario` | Text box | 0.45, 0.95, 12.43, 0.35 | 12 pt, `text.secondary` | 125 | `Scenario <name> · version <vN> (<locked/draft> <date>) · method mix: <method> <%> / …` (mandatory scenario + version naming, `07` §) |
| `PPT-006_card{1-3}` | Rounded rectangle | x = 0.45, 4.68, 8.91; y = 1.45; w = 3.97, h = 1.35 | `surface.card` | — | Card background |
| `PPT-006_card{1-3}_label` | Text box | card x + 0.16, 1.55, 3.77, 0.22 | 10 pt bold, `text.secondary` | 50 | `LANDING ESTIMATE (FY)` · `VS ANNUAL BUDGET` · `ACCURACY (MAPE-lite)` |
| `PPT-006_card{1-3}_value` | Text box | card x + 0.16, 1.79, 3.77, 0.42 | 22 pt bold, `brand.primary` | 22 | Landing estimate · variance vs budget (money + %) · MAPE-lite `%` |
| `PPT-006_card{1-3}_compare` | Text box | card x + 0.16, 2.27, 3.77, 0.22 | 10 pt, `text.secondary` | 50 | `YTD actual + forecast remaining` · `as at <period>` · `signed bias <±₹> · <N> periods compared · <E> excluded (zero actual)` |
| `PPT-006_chart_forecast` | Chart | 0.45, 2.98, 7.60, 3.10 | §5.3 | — | Native line chart: actual, forecast, budget over the loaded periods |
| `PPT-006_outlook` | Text box | 8.30, 2.98, 4.58, 3.10 | 11 pt, `text.primary` (first line 9 pt) | **708** for the narrative (the 9 pt method-mix line is not counted; the box holds 16 lines at 11 pt) | First line: `Methods: <method> <n> lines · <method> <n> lines · overrides: <n>`; then the 9 pt provenance strip; then the approved outlook narrative (or rule-based) |
| `PPT-006_disclaimer` | Text box | 0.45, 6.26, 12.43, 0.62 | 8 pt, `text.secondary` | 669 | **The full canonical advisory disclaimer, verbatim** (`01` §15.1) — the back-slide requirement |

**Rules:** the scenario and version are named on the slide (never implied); a draft forecast adds
`· NOT LOCKED — this deck is unissued` to the scenario line and the `semantic.warning` chip; accuracy
figures are shown only when a locked forecast existed for the compared closed periods, with the excluded
period count always visible (`07` §`CALC-069`); the landing estimate is labelled with its basis
(`YTD actual + forecast remaining`) and the method mix is stated in the outlook box's first line. Speaker
notes: full disclaimer, the method mix per account group, and the accuracy table behind the card.

## 5. Charts — native, styled, and identical to the workbook

### 5.1 Chart rules (both charts)

| Aspect | Rule |
|---|---|
| Construction | The template carries a **pre-styled chart** per chart placeholder; the engine replaces its data (`chart.replace_data`) and never re-styles at runtime. Formatting therefore comes from the template, is reviewed once by a human in PowerPoint, and cannot drift |
| Series cap | ≤ 8 series, ≤ 24 category points (§3.12) |
| Values | The **same display values** as the Excel pack and the app (`05` §6.3 scaling is display-only and applied identically in all three artefacts, so the chart and the `BvA Bridge` sheet can never disagree). Values land in the chart's embedded data workbook as numbers at display precision |
| Axis | Vertical axis number format matches the project (money format, `XLS-FMT-001/002/003` semantics), axis title carries the unit and scale (`₹ in lakhs`); horizontal axis shows period labels (`P09`) or driver names at ≤ 12 characters |
| Gridlines | Light horizontal only (`#E5E7EB`, 0.5 pt); no vertical gridlines; no chart border; no shadow; no 3-D; no gradient fills; no pie charts; no secondary axis |
| Legend | Bottom, text only (no colour swatches alone), present only when ≥ 2 series |
| Data labels | Bridge: on the opening, closing and the four largest steps (≤ 6 labels), formatted with the number format, positioned outside end. Forecast chart: none (the tooltip and the table carry the values) |
| Signals | Favourable steps/bars `semantic.favourable`, adverse `semantic.unfavourable`, totals `brand.primary`; each label carries `▲`/`▼` so greyscale printing survives |
| Alt text | Generated per chart, ≤ 250 characters, stating the headline (§3.11) |
| Title | Chart title `Bridge: <period>` / `Forecast vs actual: <scenario> <version>` + the unit label in a subtitle line inside the chart |
| Determinism | Category order, series order and colours are fixed by the data order (§4.3 rule); regenerating reproduces identical chart XML (`TST-PPT-08`) |

### 5.2 `PPT-003` bridge chart — the waterfall decision (`SPK-08`)

**Primary:** a native **waterfall** chart (`XL_CHART_TYPE.WATERFALL`) if the pinned `python-pptx` version
supports it and PowerPoint renders it from the generated XML (verified by spike `SPK-08`, which is added to
`09` §spike policy; the outcome is recorded as an ADR note or a one-line deviation in this document —
never left implicit in code).

**Fallback (documented, equally native and editable):** a **stacked column chart** with an invisible base
series — the classic waterfall construction:

| Series | Visible | Values |
|---|---|---|
| `base` (invisible) | No fill, no border, no legend entry | Running cumulative base: `bᵢ = Σ(previous visible steps)` minus the negative steps' absorption, computed so the visible series starts at the right height |
| `delta` (visible) | Per-point colour by favourability (`18B`/`E8F5E9` fills, text labels) | The step amounts (`CALC-010` signs) |
| `opening` / `closing` (visible) | `brand.primary` | Budget total as the first column, actual total as the last |

**Data mapping (both variants):** categories = `Opening (Budget)` · up to 6 drivers ordered by absolute
amount descending · `Closing (Actual)`; the driver set and order come from the `BvA Bridge` rows
(`11` §4.3) so the chart, the driver list and the Excel sheet are one source. Data labels show the step
amounts; the chart subtitle carries `<Units> · MTD · Base`.

**Template rule:** the template contains **both** variants as two shapes; the engine keeps the selected one
and deletes the other before writing, so the slide always has exactly one chart (asserted by
`TST-PPT-02`) and the spike outcome needs no template rewrite.

### 5.3 `PPT-006` forecast chart

| Aspect | Rule |
|---|---|
| Type | Native line chart with markers |
| Series | `Actual` (solid, `brand.primary`), `Forecast` (solid, `brand.secondary`), `Budget` (dotted `#9CA3AF`) — in that order |
| Categories | Loaded periods, oldest → newest, ≤ 24 points; labels `P01`…`P12` with the fiscal-year prefix in the chart subtitle |
| Data | Actuals from closed periods; forecast from the named locked version (draft shown with the dashed marker pattern and the `NOT LOCKED` note); budget from the budget version named on `PPT-001` |
| Gap handling | The forecast series starts at the first forecast period (no synthetic bridge point); the actual series ends at the last closed period — the gap between them is **visible and truthful**, never interpolated |
| Accuracy note | The accuracy card carries the figures, with `<N> periods compared · <E> excluded (zero actual)` always visible on the card's comparison line |
| Empty/not-available | When no forecast exists, the chart is replaced by the same-footprint text block (§3.10) — no empty chart frame |

## 6. Client base decks and house style (`FR-PPT-005`, `SPK-03`)

### 6.1 What a base deck must provide

| Requirement | Rule |
|---|---|
| Format | `.pptx` only (no `.ppt`, `.ppsx`, `.pptm`, no password, no IRM). Refused with a plain-language reason and the built-in fallback offered |
| Size | ≤ 50 MB; more than 50 MB is refused with `ERR-EXP-018` |
| Layouts | Six layouts whose names match `FPA-PPT-001`…`006` (case-insensitive, trimmed) **or** layouts the user maps by hand in the mapping dialog |
| Placeholders | Each layout must expose the named shapes of §4 (the client's template author adds them by name; the import dialog lists every required name with found/missing status) |
| Fonts | The base deck's theme fonts are adopted for **body and headings**; a missing installed font falls back to Calibri with a stated warning on the cover stamp and in the generation summary |
| Colours | Brand colours are adopted; every `CF-`/semantic colour stays as specified in §3.3 (a house style never changes what red/green mean) |
| Masters | The client's masters and slide size are used as-is (any aspect ratio, §3.1) |
| Extra slides | Client slides beyond the six are **preserved** (appendix/boilerplate) and the cover footer states the total: `6 generated · N preserved (client deck)`. The six-slide acceptance (`FR-PPT-001`) is asserted on the **generated** slides in base-deck mode and on the whole deck in built-in mode (§2.1) |
| Editing | The client's file is never modified in place: the app always writes a new file with the naming convention of §8 |

### 6.2 Mapping and mismatch reporting

1. **Automatic:** match by layout name, then by shape name, then by placeholder type (`title`, `body`,
   `picture`, `table`, `chart`) in document order.
2. **Manual:** for anything unmatched, the dialog shows a two-column table (`Required shape` →
   `Client shape` dropdown) with a live preview note.
3. **Reporting:** the generation summary and the deck's speaker notes (slide 1) record
   `Base deck: <file> · mapped 41 of 43 shapes · unmapped: PPT-006_methodline, PPT-005_footnote`.
4. **Failure:** if a *required* shape cannot be mapped and the user does not choose a substitute, the
   dialog offers **Use the built-in deck for this slide** or **Use the built-in deck for the whole deck**
   — never a silently broken slide (`ERR-EXP-012`).
5. **Verification:** after writing, the engine re-opens the output and asserts that every required shape
   name exists exactly once (`TST-PPT-19`).

### 6.3 What house-style matching may not change

Slide count and order, the six slide purposes, the footnote/retrieval lines, the provenance strips, the
signal words, the semantic colours, the full disclaimer, the stamp, alt text, the character budgets (they
recompute from the client's box geometry but never grow without a corresponding box), and the trimming
rules. House style is **appearance**: fonts, brand colours, logo, master layouts, and the client's own
boilerplate slides.

## 7. Cross-artifact consistency (the deck's half of `11` §11)

| Rule | Detail |
|---|---|
| Same filter state | The deck is generated from the `FactExport`/`Pack_Stamp_FilterJSON` context of the same generation event as the Excel pack; if the user generates only the deck, the context is still recorded the same way and the deck's own `FactExport` row is written (§8) |
| Comparison set (deck side) | The six KPI card values · bridge opening/closing/step amounts · the chart series values in the embedded data workbook · top-5 variance rows (account, actual, budget, variance, %, signal) · exception counts (open/overdue/high/unassigned) · the six exception rows · landing estimate · vs-budget variance · MAPE-lite · signed bias · excluded-period count · `Σ amount at risk` · units label and grouping · every `—`/`n/a` token position · the applied filter string in the footer/notes |
| Method | `python-pptx` reads the deck back: text frames by shape name, table cells by row/column, chart series values from the chart's data, and the notes JSON for the stamp. Values are compared to the engine and to the same cells in the Excel pack with **zero tolerance** at display precision |
| Unit label | Both artefacts state the same `<Units>` string; a scaled chart axis title must match the Excel header block |
| Conflict resolution | The engine is authoritative; the deck is fixed, never the numbers (`11` §11) |
| Failure class | S1 — a deck that disagrees with the pack issued alongside it destroys trust; release blocked (`28` defect list) |

## 8. Output files, refresh and issuance

| Aspect | Rule |
|---|---|
| Name | `<Project>_<Entity>_<Period>_Deck_<vN>.pptx` (same token rules, sanitisation, reserved-name handling and 240-character path cap as `11` §3.4) |
| Folder | `…\Exports\<project>\<period>\` beside the Excel pack |
| Collision | Identical policy to `11` §3.4: modal prompt with **Keep both (recommended)** → next `vN`, **Overwrite** → previous file moved to `.recycle\` (kept 30 days), **Choose another folder**; a file open in PowerPoint disables Overwrite with the reason; never a silent overwrite |
| Version semantics | `vN` is the file sequence and equals the pack version when issued (`11` §3.4); the stamp states both explicitly |
| Regeneration policy (`FR-XL-003` analogue, Addon 2 §C) | Re-generating creates a **new draft file version**; the previous draft stays on disk and in the register; the approved commentary versions it used remain in `CommentaryVersion` history — nothing is overwritten to make a re-run look clean |
| Issuance | "Issue pack" freezes the snapshot, increments the pack version, records recipients and locks commentary (`FR-XC-003`, `FR-XC-002`); the deck's cover then states `Pack vN (issued <date>)` instead of `unissued draft`. Issued decks are immutable; a re-issue creates a new version and the generation summary states what changed |
| Document properties | §3.7; also `core_properties.revision` = the pack version, `last_modified_by` = `FP&A Month-End Copilot <version>` (never a person's name — the human actor is in the audit trail) |
| Export register | One `FactExport` row per generated deck (`pack_token = Deck`), the same as the Excel pack (`03` §5.7) — the source of `vN`, the collision decision and the refresh context |
| Size guard | Warn > 15 MB, fail at 25 MB (`ERR-EXP-018`) with the preserved-slides suggestion |

## 9. Test contract (`TST-PPT-01`…`TST-PPT-24`)

| ID | Asserts | Fixture | Type |
|---|---|---|---|
| `TST-PPT-01` | The deck opens in PowerPoint with no repair prompt and re-opens through `python-pptx` with no shape loss | Golden deck (real Windows) | Manual + structural |
| `TST-PPT-02` | Shape whitelist (§3.2): no screenshots/groups/SmartArt/OLE/video; exactly one picture on `PPT-001` and none elsewhere; **exactly one chart** on `PPT-003` and `PPT-006` | Golden deck | Structural |
| `TST-PPT-03` | Exactly six slides in the contract order with the contract titles (built-in mode); base-deck mode asserts six generated + the counted preserved slides | Both modes | Structural |
| `TST-PPT-04` | Every placeholder exists by name with the §4 geometry, font, size, weight and colour (within 0.01″) | Golden deck + template | Structural |
| `TST-PPT-05` | `len(text) ≤ budget` for every placeholder on the golden fixture, using the §3.4 formula recomputed in the test | Golden deck | Structural |
| `TST-PPT-06` | Trimming order §3.4: trailing sentences dropped first, then least-material, then word-boundary ellipsis; protected content (numbers, signals, labels, disclaimer) never altered; the trim footnote appears; notes carry the full text | 4,000-character narrative fixture | Structural |
| `TST-PPT-07` | No two shape bounding boxes intersect on any slide, and no element is within 0.12″ of the footer band | Golden + oversize fixtures | Structural |
| `TST-PPT-08` | Two generations from the same context produce identical slide and chart XML after normalising the two timestamp fields | Golden deck ×2 | Structural |
| `TST-PPT-09` | Stamp completeness (12 fields), notes JSON parses, the short-form disclaimer appears in every slide's footer, the full disclaimer appears verbatim on `PPT-006` and in slide 1's notes | Golden deck | Structural |
| `TST-PPT-10` | Brand colours/logo from Settings are applied; semantic colours are unchanged by a house style; AA contrast holds for every text/fill pair present | Two brand profiles | Structural |
| `TST-PPT-11` | AI labelling: approved AI draft → label + `Approved by`; unapproved draft → absent with the rule-based fallback; AI disabled → rule-based only, never the AI label; rule-based text never carries the AI label | Three AI states | Structural |
| `TST-PPT-12` | Not-available states per slide name the reason and the action; no blank frame, no fabricated value, no empty chart | Five missing-input fixtures | Structural |
| `TST-PPT-13` | Chart data equals the `BvA Bridge` sheet and the forecast values exactly (series read back from the chart's embedded workbook) | Fixed filter state | Structural (cross-artifact) |
| `TST-PPT-14` | Bridge chart step order = driver-list order; opening = `BvA Summary` budget total; closing = actual total; `Opening + Σ steps = Closing` | Golden deck | Structural |
| `TST-PPT-15` | Row selection rules: top 5 variances / top 6 exceptions; fewer rows when fewer exist; never a blank row; kicker counts match the data | Small and large fixtures | Structural |
| `TST-PPT-16` | Alt text present on every chart (≤ 250 chars); reading order title → body → footer; table header rows marked | Golden deck | Structural |
| `TST-PPT-17` | Performance: ≤ 15 s at `--scale 250000`; ≤ 12 aggregate queries; no transaction-grain query issued (query counter assertion) | Perf fixture | Performance |
| `TST-PPT-18` | Cancel mid-generation leaves no file at the target path and no `.tmp` residue | UI test | UI + unit |
| `TST-PPT-19` | Base deck: the client's masters/slide size are used; the mapping report is written to notes; unmapped required shapes are reported and fall back per choice; the post-write re-open finds every required shape exactly once | Client base deck fixture (16:9 and 4:3) | Structural |
| `TST-PPT-20` | House style: fonts/colours adopted from the base deck; a missing font falls back to Calibri and is stated; budgets recomputed for the client's geometry | Base deck with an unusual font | Structural |
| `TST-PPT-21` | Sample-data watermark/footnote and the stale-results chip behave per §3.7/§3.10 | Sample + stale fixtures | Structural |
| `TST-PPT-22` | Filename tokens, sanitisation and the collision prompt behave per §8 (including the locked-file case) | Name/collision fixtures | Unit + UI |
| `TST-PPT-23` | One `FactExport` row per generation with `pack_token = Deck`, the filter JSON, the content hash and `file_version`; refresh reuses the stored context | Export register | Unit |
| `TST-PPT-24` | Greyscale legibility and AA contrast of the rendered deck (PowerPoint print-to-PDF in the real-Windows validation): every semantic colour still distinguishable by its text signal | Golden deck → PDF | Manual (VM) |

## 10. Failure modes (continuing the `ERR-EXP` family)

Deck failures extend the export error family owned by `11` §12; shared conditions reuse their codes
(`ERR-EXP-002` file locked, `ERR-EXP-003` disk full, `ERR-EXP-006` cancelled, `ERR-EXP-007` data changed
during generation, `ERR-EXP-009` synced path).

| ID | Trigger | Message (headline) | What was not lost | Next action |
|---|---|---|---|---|
| `ERR-EXP-012` | Base-deck layouts or required shapes missing/ambiguous | *"Some slides in your deck don't have a place for the required content."* | *"Your deck file is unchanged. Nothing was written."* | Map the shapes, or use the built-in deck for the affected slides |
| `ERR-EXP-013` | A budget cannot hold protected content (numbers/signals/disclaimer) | *"A slide can't fit its required figures — this is a layout problem, not a data problem."* | *"Nothing was written. No number was hidden or rounded away."* | Copy details and report it; the layout/template must change (`12` §3.4 rule 1) |
| `ERR-EXP-014` | Built-in template missing, unreadable, or a named shape is absent | *"The deck template is missing or damaged."* | *"Nothing was written."* | Reinstall/repair the app (the template ships with it); report if it recurs |
| `ERR-EXP-015` | Waterfall chart type unavailable in the pinned chart writer | *"The bridge is being drawn with the alternate (stacked) method."* (informational) | *"The chart shows the same data."* | None — the fallback is automatic and recorded (`SPK-08`); report only if it appears in a release build |
| `ERR-EXP-016` | Logo file missing, unreadable, or > 5 MB | *"Your logo couldn't be added to the deck."* | *"The deck is complete; it just has no logo."* | Re-select the logo in Settings → Branding |
| `ERR-EXP-017` | Chart data workbook could not be written into the deck | *"A chart's data couldn't be embedded, so the deck was not written."* | *"Nothing was written."* | Retry; if it recurs, report it (charts must stay editable — an image chart is never a substitute) |
| `ERR-EXP-018` | Deck size (incl. preserved client slides) exceeds 25 MB, or the base deck exceeds 50 MB | *"This deck is too large to generate (<size>)."* | *"Nothing was written."* | Drop the preserved appendix slides, or use the built-in deck |

## 11. Open items, deferrals and assumptions

| ID | Item | Status |
|---|---|---|
| `SPK-08` | Waterfall chart support in the pinned `python-pptx` version, and how PowerPoint renders the generated XML | Spike before Phase 5 code (`09` spike table; outcome recorded per §5.2) |
| `PPT-KPI-DEFAULT` | The three configurable KPI cards default to Gross margin %, Budget burn %, Exceptions open. Client confirmation via the questionnaire (`21`, `Q-` items) | Default set; changeable in Settings |
| Template authoring | `packaging/templates/FPAMonthEndCopilot_v1.pptx` must be authored (layouts, named shapes, both bridge chart variants, pre-styled tables/charts) and committed before Phase 5 code | Obligation (§12) |
| Assumption A | The client's PowerPoint is 2016+ or Microsoft 365 (native charts, theme colours, alt text all supported) | Assumption, validated in the real-Windows run |
| Assumption B | The client's base deck is a normal `.pptx` without protection; `SPK-03` verifies fidelity | Assumption, spike-gated |
| Assumption C | Six slides are the whole management narrative; anything more is an appendix the client owns, which is why preserved base-deck slides are counted and never generated | Assumption |
| `DEC-009` link | KPI selection is PRD-governed; the deck renders it, it does not decide it | Cross-reference |
| Reconciliations made this pass | `08` §11.1's omission example now points at the §2.1 default/opt-in rule; `05` §6.3's scale example now matches the display-formatting owner (`08` §15) | Done (`CHANGELOG`) |

## 12. Change control and obligations

| Obligation | Owner |
|---|---|
| Template file with the seven layouts, named shapes and both bridge chart variants, versioned with the app | `packaging/`, `15`, `17` |
| Spike `SPK-08` added to the spike table; outcome recorded here and in `09` | `09`, this document |
| `ERR-EXP-012`…`ERR-EXP-018` added to the message catalog with plain-language wording | `26` |
| `TST-PPT-01`…`TST-PPT-24` implemented, including the greyscale/PDF and base-deck cases | `14` |
| Deck screens/actions (`SCR-029` generate, `SCR-030` issue, `SCR-031` commentary) reference the budgets and labels specified here | `08` |
| API endpoints for generate/issue with the deck options (omit-slide choice, base deck, logo) | `26` |
| User-guide instructions: generating the deck, the omit-slide choice, editing in PowerPoint, why a number is never rounded away | `22` |
| Promotion/consultant handover notes: house-style and base-deck mapping walkthrough | `23` |
| `FR-PPT-001` acceptance clarified for base-deck mode (generated vs preserved slides) | `02` (done) |

| Change | Requires |
|---|---|
| Adding/removing/reordering a slide | Update §2/§4, the footer `Slide N of 6` strings, `TST-PPT-03`, `08`'s generate-pack copy, and the kickoff's 4–6-slide latitude check |
| Changing a placeholder's geometry or font | Update §4, recompute the budget from §3.4's formula, update §3.4's table and `TST-PPT-04/05`, and re-check the 0.12″ separation |
| Changing a budget or the trimming order | Update §3.4 and `TST-PPT-05/06`; the trimming order is a user-visible behaviour, so the user guide (`22`) changes too |
| Changing a chart type or series set | Update §5, the template, `TST-PPT-13/14`, and the cross-artifact comparison set (§7) |
| Changing colours/fonts | `08` §14/§19 own the tokens — change them there first, then mirror in §3.3 and the template; re-run the contrast test |
| Adding a fixed label or note (e.g. a new footnote line) | Treat as a budget change **and** a spec change; never add text that consumes a budget without recalculating it |
| Any change here | `CHANGELOG.md` entry + `SESSION_LOG.md` row; structural tests re-run before commit |

**Frozen constants owned by this document:** the six slide IDs, titles and order (§2.1) · the scaling rules
(§3.1) · the shape-type whitelist (§3.2) · the theme values (§3.3) · `AVG_ADVANCE = 0.50`, the budget
formula and the per-placeholder budgets (§3.4) · the trimming order (§3.4) · shape-naming scheme (§3.6) ·
footer/page strings and the disclaimer placement (§3.7) · the AI/rule-based labels (§3.8) · the deck's
display conventions (§3.9) · not-available copy per slide (§3.10) · chart rules and the bridge fallback
(§5) · the filename token `Deck` (§8).


