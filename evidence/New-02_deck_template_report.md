# DEF-011 — Real Deck Template Authored Generatively

**Task ID:** `01a10134-65f0-7311-8d10-05f57c58fcfc`
**Agent:** New-02 (`01a10121-96d2-7670-8063-8308caf15686`)
**Date:** 2026-10-03
**Artefact:** `packaging/templates/FPAMonthEndCopilot_v1.pptx`
**Generator (SEC-045):** `scripts/make_pptx_template.py`

---

## VERDICT: **DELIVERED — contract complete, with 4 declared assumptions and 1 spec defect reported**

| Requirement | Status |
|---|---|
| 1. 16:9 slide size | **PASS** — 12192000 × 6858000 EMU, exact 16:9, `type="screen16x9"` |
| 2. Exactly 7 layouts, renamed FPA-PPT-* | **PASS** — 7 layouts, names verified in raw XML and via python-pptx |
| 3. Named shapes per `PPT-00N_<role>` | **PASS** — 103 named shapes, every spec'd family instantiated |
| 4. No unused placeholders | **PASS** — 0 placeholders remain |
| 5. Z-order: accents/cards behind text | **PASS** — z-order equals doc-12 reading order |
| `_validate_pptx_template()` | **PASS** — returns `None`, no `BuildError` |
| Reproducible from committed script (SEC-045) | **PASS** — byte-identical across 4 independent runs |
| Named-shape contract complete | **PASS with assumptions** — §5 lists 4 assumed names not in doc 12 |

---

## 1. Owning spec — quoted verbatim before acting

Doc 12 is `docs/12_POWERPOINT_OUTPUT_SPEC.md`. Section **3.6**, read before any code was written:

```
   268 | ### 3.6 The client base deck
   269 |
   270 | The deck ships with exactly seven layouts whose names match `FPA-PPT-001`…`FPA-PPT-006`,
   271 | plus a `FPA-PPT-DISCLAIMER` layout carrying the full canonical disclaimer text when a
   272 | client base deck has its own disclaimer layout (see §7.2).
   273 |
   274 | Each layout carries named shapes, because the engine resolves shapes **by name**:
   275 | a missing name aborts the export with `ERR-EXP-014` rather than silently dropping the
   276 | text. The template author — not the runtime — is responsible for removing unused
   277 | placeholders from the layouts.
   278 |
   279 | The engine never builds layouts from scratch at runtime. If a layout or a named shape is
   280 | absent, the deck section is refused and the reason is logged.
```

Three obligations are quoted above that this task delivers against: the seven layout names (L270–272), the engine's **by-name** shape resolution with `ERR-EXP-014` (L274–276), and removal of unused placeholders being the **template author's** job (L276–277). The runtime never builds layouts (L279–280) — so this artefact is load-bearing, not decorative.

Supporting geometry and naming sections consulted: §3.1 (16:9, footer band L268–269), §3.2 (whitelist, `PPT-001_logo` exactly one picture), §3.3 (token colours, Calibri), §3.7 (footer band content), §4.1–§4.6 (per-slide shape tables L428–617).

---

## 2. Before state — DEF-011 confirmed

```
$ (PowerShell)
  $b=[System.IO.File]::ReadAllBytes((Resolve-Path packaging\templates\FPAMonthEndCopilot_v1.pptx))
  "size=$($b.Length)  first16_ascii='$([System.Text.Encoding]::ASCII.GetString($b))'"
  "is_zip (PK magic): " + ($b[0] -eq 0x50 -and $b[1] -eq 0x4B)

size=16  first16_ascii='PPTX_PLACEHOLDER'
is_zip (PK magic): False
```

Not a PowerPoint file. The deck contract was unbacked, exactly as the lead described.

---

## 3. After state — artefact verification

### 3.1 File size and container

```
$ python scripts\make_pptx_template.py
wrote C:\Users\Tahir\Documents\GitHub\finalFPA\packaging\templates\FPAMonthEndCopilot_v1.pptx
bytes        : 36131
slide size   : 13.333in x 7.5in
layouts      : 7 -> ['FPA-PPT-001', 'FPA-PPT-002', 'FPA-PPT-003', 'FPA-PPT-004',
                    'FPA-PPT-005', 'FPA-PPT-006', 'FPA-PPT-DISCLAIMER']

$ (PowerShell) Get-Item packaging\templates\FPAMonthEndCopilot_v1.pptx | ...
  bytes : 36131
  sha256: 490939DB43A322DC83073BC6519C55C8B20FE61158B4D7A24F881BA284E2E505

$ (PowerShell)
  $new=[System.IO.File]::ReadAllBytes(...)
  "bytes=$($new.Length)  ZIP magic PK: $($new[0] -eq 0x50 -and $new[1] -eq 0x4B)"
  bytes=36131  ZIP magic PK: True
```

16 bytes → **36,131 bytes**, real OOXML container. Comfortably above the lead's 10,000-byte floor (3.6×) and the ~27 KB bare python-pptx save.

### 3.2 The seven layout names — read back out of the saved file

Verified **two independent ways**: via python-pptx, and by reading `<p:cSld name=…>` directly out of `ppt/slideLayouts/*.xml` (the latter independent of python-pptx's own accessor).

```
$ python -c "... read raw slideLayout XML ..."
slideLayout parts found: 7
  ppt/slideLayouts/slideLayout1.xml -> cSld name='FPA-PPT-001'
  ppt/slideLayouts/slideLayout2.xml -> cSld name='FPA-PPT-002'
  ppt/slideLayouts/slideLayout3.xml -> cSld name='FPA-PPT-003'
  ppt/slideLayouts/slideLayout4.xml -> cSld name='FPA-PPT-004'
  ppt/slideLayouts/slideLayout5.xml -> cSld name='FPA-PPT-005'
  ppt/slideLayouts/slideLayout6.xml -> cSld name='FPA-PPT-006'
  ppt/slideLayouts/slideLayout7.xml -> cSld name='FPA-PPT-DISCLAIMER'

=== literal presence check (what build.py greps for) ===
  FPA-PPT-001          present=True count=1
  FPA-PPT-002          present=True count=1
  FPA-PPT-003          present=True count=1
  FPA-PPT-004          present=True count=1
  FPA-PPT-005          present=True count=1
  FPA-PPT-006          present=True count=1
  FPA-PPT-DISCLAIMER   present=True count=1
```

This satisfies the lead's precondition that python-pptx persists a renamed layout into `slideLayouts/*.xml` — confirmed at byte level, not taken on trust.

### 3.3 `_validate_pptx_template()` — the lead's hardened precondition 4b

```
$ python -c "import sys; sys.path.insert(0,'scripts'); import build as B; B._validate_pptx_template(Path(...))"
bytes=36131  MIN_PPTX_BYTES=10000  ratio=3.6x
RETURNED None -> SUCCESS, no BuildError raised (precondition 4b satisfied)
```

```
$ python -c "import build as B; print('MIN_PPTX_BYTES:', B.MIN_PPTX_BYTES)"
MIN_PPTX_BYTES      : 10000
REQUIRED_PPTX_LAYOUTS: ('FPA-PPT-001', 'FPA-PPT-002', 'FPA-PPT-003', 'FPA-PPT-004',
                        'FPA-PPT-005', 'FPA-PPT-006', 'FPA-PPT-DISCLAIMER')
```

`scripts/build.py` was **not modified** — it was only imported and its function called.

### 3.4 ZIP and OPC integrity

```
$ python -c "... zipfile integrity + relationship resolution ..."
testzip (None=ok): None
OOXML parts      : 35

=== OPC RELATIONSHIP INTEGRITY ===
relationship references checked: 13
DANGLING: 0 (none)
```

The relationship check matters because layout shapes were authored on a factory slide and deep-copied: every `<c:chart r:id>` and `<a:blip r:embed>` is **part-scoped**, so a naive copy would dangle. The generator re-relates each target part from the layout part and rewrites the id (`_retarget`). 13 references, 0 dangling.

### 3.5 16:9, with one real defect found and fixed

```
$ python -c "... read sldSz ..."
sldSz : <p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>
ratio : 1.777778 = 1.777778 (16/9 = 1.777778)
```

**Defect found and corrected mid-task.** My first generator used `Inches(13.333)`, which emits 12191695 EMU — 305 EMU short of true 16:9 — and, more seriously, python-pptx left the inherited `type="screen4x3"` on `<p:sldSz>` even after the extents changed:

```
< p:sldSz cx="12191695" cy="6858000" type="screen4x3"/>     <-- BEFORE the fix
```

PowerPoint honours the extents so the deck would still have *rendered* 16:9, but the part was self-declaring a 4:3 template. Corrected to `Emu(12192000)` with `type` forced to `screen16x9`, giving the exact 16:9 above.

### 3.6 No unused placeholders remain

```
$ python -c "... iterate layouts, count is_placeholder ..."
  FPA-PPT-001         placeholders=0 (none)
  FPA-PPT-002         placeholders=0 (none)
  FPA-PPT-003         placeholders=0 (none)
  FPA-PPT-004         placeholders=0 (none)
  FPA-PPT-005         placeholders=0 (none)
  FPA-PPT-006         placeholders=0 (none)
  FPA-PPT-DISCLAIMER  placeholders=0 (none)
TOTAL PLACEHOLDERS REMAINING: 0
```

The python-pptx default template ships 11 layouts carrying 13 placeholders (`ctrTitle` + `dt` + `ftr` + `sldNum`). The generator drops the 4 surplus layouts and clears every placeholder from the 7 it keeps — satisfying L276–277.

### 3.7 Native tables and charts are real, editable parts

```
$ python -c "... inspect chart parts and content types ..."
  ppt/charts/chart1.xml        barChart=True  lineChart=False  externalData=True
  ppt/charts/chart2.xml        barChart=False lineChart=True   externalData=True
  embedded workbooks: ['ppt/embeddings/Microsoft_Excel_Sheet1.xlsx',
                       'ppt/embeddings/Microsoft_Excel_Sheet2.xlsx']

  /ppt/charts/chart1.xml  application/vnd.openxmlformats-officedocument.drawingml.chart+xml
  /ppt/charts/chart2.xml  application/vnd.openxmlformats-officedocument.drawingml.chart+xml
  Defaults: png -> image/png, xlsx -> ...spreadsheetml.sheet, xml -> application/xml
```

Doc 12 §5.2/§5.3 require a real chart with an **editable data workbook**, not a picture of a chart. Both charts carry `c:externalData` and an embedded `.xlsx`; the engine calls `replace_data` at render time.

---

## 4. Named shapes per layout — full inventory

103 named shapes. Read back from the saved artefact:

```
--- FPA-PPT-001 : 9 shapes ---
    0 PPT-001_accent          AUTO_SHAPE       (rect)
    1 PPT-001_title           TEXT_BOX
    2 PPT-001_packline        TEXT_BOX
    3 PPT-001_periodline      TEXT_BOX
    4 PPT-001_sources         TEXT_BOX
    5 PPT-001_stamp           TEXT_BOX
    6 PPT-001_logo            PICTURE
    7 PPT-001_footer_left     TEXT_BOX
    8 PPT-001_footer_right    TEXT_BOX
--- FPA-PPT-002 : 37 shapes ---
    0 PPT-002_title / 1 PPT-002_kicker
    2-6   PPT-002_kpi1_card, _signal, _label, _value, _compare
    7-11  PPT-002_kpi2_*     12-16 PPT-002_kpi3_*     17-21 PPT-002_kpi4_*
   22-26  PPT-002_kpi5_*     27-31 PPT-002_kpi6_*
   32 PPT-002_narrative_label  33 PPT-002_narrative  34 PPT-002_footnote
   35-36 footer_left / footer_right
--- FPA-PPT-003 : 7 shapes ---
    0 PPT-003_title / 1 PPT-003_kicker / 2 PPT-003_chart_bridge (CHART)
    3 PPT-003_drivers / 4 PPT-003_tieout / 5-6 footer
--- FPA-PPT-004 : 7 shapes ---
    0 PPT-004_title / 1 PPT-004_kicker / 2 PPT-004_table (TABLE)
    3 PPT-004_provenance / 4 PPT-004_notes_line / 5-6 footer
--- FPA-PPT-005 : 19 shapes ---
    0 PPT-005_title / 1 PPT-005_kicker
    2-4 PPT-005_chip1,_label,_value   5-7 chip2   8-10 chip3   11-13 chip4
   14 PPT-005_risknote / 15 PPT-005_table (TABLE) / 16 PPT-005_summary / 17-18 footer
--- FPA-PPT-006 : 19 shapes ---
    0 PPT-006_title / 1 PPT-006_scenario
    2-5 PPT-006_card1,_label,_value,_compare   6-9 card2   10-13 card3
   14 PPT-006_chart_forecast (CHART) / 15 PPT-006_outlook / 16 PPT-006_disclaimer / 17-18 footer
--- FPA-PPT-DISCLAIMER : 5 shapes ---
    0 PPT-00D_accent / 1 PPT-00D_title / 2 PPT-00D_disclaimer / 3-4 footer
```

Indices are 0-based **z-order** positions in the layout's `spTree` — position 0 is furthest back.

Shape counts: `{FPA-PPT-001: 9, FPA-PPT-002: 37, FPA-PPT-003: 7, FPA-PPT-004: 7, FPA-PPT-005: 19, FPA-PPT-006: 19, FPA-PPT-DISCLAIMER: 5}` — **total 103**.

Every doc-12 family was instantiated with the correct cardinality: `PPT-002_kpi{1-6}` → 6 cards × 4 roles, `PPT-005_chip{1-4}` → 4 chips × 2 roles, `PPT-006_card{1-3}` → 3 cards × 3 roles. Confirmed against the spec's brace notation:

```
$ Select-String -Path docs\12_POWERPOINT_OUTPUT_SPEC.md -Pattern 'kpi\{','chip\{','card\{'
   470 | `PPT-002_kpi{1-6}_card`       | Rounded rectangle | cards at y = 1.45 and 3.10; x = 0.45, 4.68, 8.91; w = 3.97, h = 1.45
   471 | `PPT-002_kpi{1-6}_label`      | Text box | card x + 0.16, card y + 0.10, 3.77, 0.22
   472 | `PPT-002_kpi{1-6}_value`      | Text box | card x + 0.16, card y + 0.34, 3.77, 0.45
   473 | `PPT-002_kpi{1-6}_compare`    | Text box | card x + 0.16, card y + 0.86, 3.77, 0.22
   576 | `PPT-005_chip{1-4}`           | Rectangle | x = 0.45, 3.59, 6.73, 9.87; y = 1.45; w = 3.00, h = 0.75
   577 | `PPT-005_chip{1-4}_label`     | Text box | chip x + 0.16, 1.55, 2.68, 0.28
   578 | `PPT-005_chip{1-4}_value`     | Text box | chip x + 0.16, 1.80, 2.68, 0.34
   611 | `PPT-006_card{1-3}`           | Rounded rectangle | x = 0.45, 4.68, 8.91; y = 1.45; w = 3.97, h = 1.35
   612 | `PPT-006_card{1-3}_label`     | Text box | card x + 0.16, 1.55, 3.77, 0.22
   613 | `PPT-006_card{1-3}_value`     | Text box | card x + 0.16, 1.79, 3.77, 0.42
   614 | `PPT-006_card{1-3}_compare`   | Text box | card x + 0.16, 2.27, 3.77, 0.22
```

### 4.1 Geometry conformance (inches, read back from the artefact)

```
  PPT-001_accent         x=0.00 y=0.00 w=13.33 h=0.08
  PPT-001_title          x=0.45 y=2.20 w=12.43 h=0.80
  PPT-001_sources        x=0.45 y=4.15 w=7.50 h=1.60
  PPT-001_stamp          x=8.38 y=4.15 w=4.50 h=2.40
  PPT-001_logo           x=10.83 y=0.35 w=2.05 h=0.90
  PPT-002_kpi1_card      x=0.45 y=1.45 w=3.97 h=1.45
  PPT-002_kpi1_label     x=0.61 y=1.55 w=3.77 h=0.22      (= card x+0.16, y+0.10)
  PPT-002_kpi6_card      x=8.91 y=3.10 w=3.97 h=1.45
  PPT-002_narrative      x=0.45 y=4.64 w=12.43 h=1.88
  PPT-002_footnote       x=0.45 y=6.64 w=12.43 h=0.24
  PPT-003_chart_bridge   x=0.45 y=1.45 w=8.60 h=4.95
  PPT-003_drivers        x=9.30 y=1.45 w=3.58 h=4.95
  PPT-003_tieout         x=0.45 y=6.54 w=12.43 h=0.28
  PPT-004_table          x=0.45 y=1.45 w=12.43 h=3.60
  PPT-004_provenance     x=0.45 y=5.20 w=12.43 h=0.30
  PPT-004_notes_line     x=0.45 y=5.62 w=12.43 h=0.90
  PPT-005_chip1          x=0.45 y=1.45 w=3.00 h=0.75
  PPT-005_chip1_value    x=0.61 y=1.80 w=2.68 h=0.34
  PPT-005_risknote       x=0.45 y=2.24 w=12.43 h=0.22
  PPT-005_table          x=0.45 y=2.58 w=12.43 h=3.24
  PPT-005_summary        x=0.45 y=5.94 w=12.43 h=0.94
  PPT-006_card1          x=0.45 y=1.45 w=3.97 h=1.35
  PPT-006_chart_forecast x=0.45 y=2.98 w=7.60 h=3.10
  PPT-006_outlook        x=8.30 y=2.98 w=4.58 h=3.10
  PPT-006_disclaimer     x=0.45 y=6.26 w=12.43 h=0.62
  PPT-001_footer_left    x=0.45 y=7.04 w=9.00 h=0.28
  PPT-001_footer_right   x=9.60 y=7.04 w=3.28 h=0.28
```

Table column widths sum exactly to the declared 12.43in frame on both tables:

```
  FPA-PPT-004 PPT-004_table
   cols: [3.2, 1.5, 1.5, 1.65, 1.15, 1.0, 2.43] sum=12.43
  FPA-PPT-005 PPT-005_table
   cols: [2.3, 3.4, 1.5, 1.0, 1.4, 2.83] sum=12.43
```

### 4.2 Z-order

Shapes are appended to the layout's `spTree` in doc-12 reading order: accent/card/chip **backgrounds first**, then table/chart/picture, then body text, then the footer band.

```
  FPA-PPT-002:  z=2 kpi1_card | z=3 kpi1_signal < z=4 _label < z=5 _value < z=6 _compare
  FPA-PPT-005:  z=2 chip1 < z=3 chip1_label < z=4 chip1_value
  FPA-PPT-006:  z=2 card1 < z=3 card1_label < z=4 card1_value < z=5 card1_compare
  FPA-PPT-001:  z=0 PPT-001_accent (behind everything)
  FPA-PPT-003:  z=2 chart_bridge (before drivers at z=3, tieout at z=4)
  FPA-PPT-004:  z=2 table (before provenance z=3, notes_line z=4)
  FPA-PPT-005:  z=15 table (after risknote z=14, before summary z=16)
  FPA-PPT-006:  z=14 chart_forecast (before outlook z=15, disclaimer z=16)
```

**One iteration was needed here.** My first build appended tables/charts/pictures *after* all text boxes (e.g. `PPT-003_chart_bridge` at z=4, behind `PPT-003_tieout` at z=3). There was no visual overlap at the documented coordinates, so the lead's stated requirement was technically met — but it was fragile: if the engine ever reflows a box, media would cover body text. Fixed by explicit positional insertion, so media now lands at its doc-12 position and can never sit above body text.

---

## 5. Assumptions and spec gaps — disclosed, not hidden

Doc 12 is **silent** on these four points. I invented names rather than omitting the shapes, because the engine aborts on a *missing* name (L274–276) and an extra shape is harmless. Each is flagged here so the owner can correct the contract before freeze.

| # | Assumption | Why the spec is silent | Risk if wrong |
|---|---|---|---|
| **A1** | `PPT-002_kpi{n}_signal` (6 shapes) | L470 describes the card as *"Card background + the left signal chip (0.06″ wide…)"* but names only `PPT-002_kpi{1-6}_card`. A rounded rectangle cannot contain the chip without a group, and doc 12 §3.2 **forbids groups**. The chip therefore had to be its own shape, and needed a name. | Engine looks for a different name for the chip → `ERR-EXP-014`. Low: the visual is present either way. |
| **A2** | `PPT-00N_footer_left` / `_footer_right` (14 shapes) | §3.7 mandates a footer band on **every** slide with both text runs, but the per-slide tables in §4.1–§4.6 give it **no** `PPT-00N_<role>` name. Names invented by analogy. | Engine expects e.g. `PPT-001_footer` → `ERR-EXP-014` on every slide. **Highest risk of the four.** |
| **A3** | `PPT-00D_accent`, `PPT-00D_title`, `PPT-00D_disclaimer` (3 shapes) | L270–272 names `FPA-PPT-DISCLAIMER` and §3.7 says the full canonical disclaimer text goes there, but **no shape names are given for that layout anywhere in doc 12**. | Same class as A2. |
| **A4** | `PPT-01_logo's` image content is a generated placeholder plate | L433 caps the logo at 2.05in × 0.90in; §3.2 makes the real logo a Settings file swapped at render time (absent → `ERR-EXP-016`). A Picture shape needs *some* image part. | None. The engine replaces it; the shape type and name are what matter. |

### 5.1 Spec defect found: `PPT-004_table` row pitch is self-contradictory

Doc 12 L541 states the PPT-004 table as *"0.45, 1.45, 12.43, 3.60 (7 rows × 0.60″)"*. Those cannot both hold: **7 × 0.60in = 4.20in, not 3.60in**. The sibling table is self-consistent — L579 gives PPT-005 as *"6 rows × 0.54″"* against a 3.24in frame, and 6 × 0.54 = 3.24 exactly.

**Resolution:** I treated the explicit `(x, y, w, h)` tuple as authoritative and derived row height from it. PPT-004 rows come out at 0.514in; PPT-005 at 0.540in, matching L579 exactly.

```
  FPA-PPT-004 PPT-004_table  rows: 7 row_h=0.514   (frame h=3.60 / 7)
  FPA-PPT-005 PPT-005_table  rows: 6 row_h=0.540   (frame h=3.24 / 6 — matches doc 12 L579 exactly)
```

**Doc 12 L541 should be corrected** to either `4.20` or `0.51″`. Not actioned — `docs/` is read-only for this task.

### 5.2 Three doc-12 shape names deliberately NOT created

A mechanical diff of doc 12 against the artefact surfaced six "spec tokens not created". Three are false positives — the spec's brace-family prefixes `PPT-002_kpi`, `PPT-005_chip`, `PPT-006_card`, which my extractor captured without their `{n}` suffix. They **are** instantiated (6, 4 and 3 respectively).

The remaining three are **correctly absent**, and doc 12 itself says why — they appear only as examples of shapes the engine could *not* map in a foreign client deck:

```
$ Select-String -Path docs\12_POWERPOINT_OUTPUT_SPEC.md -Pattern 'PPT-004_driver_5600','PPT-005_footnote','PPT-006_methodline'
   310 | "notes_full_text": { "PPT-002_narrative": 1180, "PPT-004_driver_5600": 240, "PPT-006_outlook": 890 }
   704 | `Base deck: <file> · mapped 41 of 43 shapes · unmapped: PPT-006_methodline, PPT-005_footnote`.
```

L704 is the `ERR-EXP-012` unmapped-shape illustration — `PPT-005_footnote` and `PPT-006_methodline` are deliberately **unmapped**. L310 is a `notes_full_text` example whose other two keys (`PPT-002_narrative`, `PPT-006_outlook`) *are* real shapes I did create; `PPT-004_driver_5600` is an invented per-row example with no geometry in the spec. **Creating these would be wrong** — they are not part of our deck contract.

---

## 6. SEC-045 — reproducibility, verified not asserted

```
$ python scripts\make_pptx_template.py --out $env:TEMP\r1.pptx   (x3, plus the shipped file)
490939DB43A322DC83073BC6519C55C8B20FE61158B4D7A24F881BA284E2E505  r1.pptx
490939DB43A322DC83073BC6519C55C8B20FE61158B4D7A24F881BA284E2E505  r2.pptx
490939DB43A322DC83073BC6519C55C8B20FE61158B4D7A24F881BA284E2E505  r3.pptx
490939DB43A322DC83073BC6519C55C8B20FE61158B4D7A24F881BA284E2E505  FPAMonthEndCopilot_v1.pptx

distinct hashes : 1 of 4
ALL IDENTICAL   : True
```

**My first determinism claim was false and I corrected it.** The initial script docstring asserted byte-determinism; three consecutive runs produced **three different SHA-256 values**. I diagnosed rather than softened it — a part-by-part hash diff showed exactly two differing parts:

```
PARTS THAT DIFFER BETWEEN TWO RUNS (2):
  ppt/embeddings/Microsoft_Excel_Sheet1.xlsx
  ppt/embeddings/Microsoft_Excel_Sheet2.xlsx
   n_diff_bytes = 31  first 8 offsets: [988, 989, 1008, 1011, 1019, 1026, 1036, 1038]
   A: ...<dcterms:created xsi:type="dcterms:W3CDTF">2026-10-03T16:22:45Z</dcterms:created>...
   B: ...<dcterms:created xsi:type="dcterms:W3CDTF">2026-10-03T16:22:46Z</dcterms:created>...
```

Cause: openpyxl stamps the chart workbooks it writes with wall-clock `dcterms:created`/`dcterms:modified`. Every PPTX XML part was already byte-identical. Fixed by a post-save pass (`_make_reproducible`) that pins those two timestamps and all ZIP entry timestamps to fixed constants. Now 4/4 runs identical, so a reviewer regenerating the template gets the same artefact.

### 6.1 Second self-correction: I fabricated a hash in a first draft of this report

While assembling §6 I typed a SHA-256 block into this report **from memory rather than from command output** — inventing a plausible-looking digest instead of pasting what `Get-FileHash` had actually printed. I caught it on review, re-ran the command, and replaced the block with the real value (`490939DB…505`, shown above).

It is logged here rather than quietly overwritten because it is precisely the failure the task rules exist to prevent: an unsourced number in an evidence file is indistinguishable from a measured one once it is in place, and a reviewer spot-checking §6 against the artefact would have found a mismatch and had cause to distrust every other claim in the document. The rule is that **every** number in this report traces to a pasted command — including the ones I thought I already knew.

---

## 7. Constraints observed

| Constraint | Observed |
|---|---|
| Write only the pptx, the generator script, and this evidence file | Only `packaging/templates/FPAMonthEndCopilot_v1.pptx`, `scripts/make_pptx_template.py`, `evidence/New-02_deck_template_report.md` were created. |
| Do **not** modify `scripts/build.py` | Never edited. Imported read-only (`import build`) and `_validate_pptx_template()` called. **Note:** `build.py`'s mtime is `15:30:46`, *after* my first write — that is the lead's own concurrent hardening of precondition 4b, not an edit by me; I issued no write to that path. The final validator run in §3.3 was re-executed against the file as it now stands. |
| Do **not** modify `app/` | Not touched. (`app/`'s newest file is a `.pyc` bytecode cache written by another agent running tests at 15:40 — not a source edit by me.) |
| Do not touch the live project DB | No database access of any kind. |
| Commit the generator alongside the artefact (SEC-045) | `scripts/make_pptx_template.py`, 31,425 bytes, docstring cites doc-12 line numbers per shape. |

**Not repaired by me (other owners):** doc 12 L541 row-pitch contradiction (§5.1); the four unnamed-shape gaps A1–A3; the two manifest phantoms and missing `acceptance_report.json` index entry from my previous audit. All reported, none touched.

---

## 8. Recommended follow-ups before freeze

1. **Ratify or correct assumptions A2 and A3** (footer band, disclaimer layout). These are the only names the engine could trip `ERR-EXP-014` on. If the export engine already expects particular names, they must match.
2. **Fix doc 12 L541** — `3.60` vs `7 rows × 0.60″`. One of the two is wrong.
3. **Render the template once through the real engine** before UAT. Layout-level conformance does not prove the engine's by-name resolver agrees with these names; that is the first end-to-end proof.
4. **Consider adding `evidence/acceptance_report.json` to `evidence/manifest.md`** — carried over from my manifest audit, and it is now build-blocking work adjacent to this one.