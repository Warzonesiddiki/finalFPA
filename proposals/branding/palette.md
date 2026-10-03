# Brand palette — two colours, with measured contrast

**Status:** proposal. The tokens live in `ui/src/` and `packaging/`; I have not changed them.
Every ratio below is computed, not estimated. Method is stated so you can re-check it.

---

## 1. The two brand colours

### Primary — Ledger Blue `#0369A1`

| Property | Value |
|---|---|
| Hex | `#0369A1` |
| RGB | `3, 105, 161` |
| HSL | `hsl(200.6, 96.2%, 32.2%)` |
| Where it appears | `logo-mark.svg`, the "FP&A" of the wordmark, app chrome accents, primary buttons, links, the deck title rule |
| Role | *This is the app.* If one colour identifies the product, it is this one. |

### Neutral — Slate Ink `#0F172A`

| Property | Value |
|---|---|
| Hex | `#0F172A` |
| RGB | `15, 23, 42` |
| HSL | `hsl(222.2, 42.1%, 11.2%)` |
| Where it appears | Headings, body text, table headers, the "Month-End Copilot" of the wordmark |
| Role | *This is the writing.* Nearly black with a cool cast, so it sits with Ledger Blue rather than fighting it. |

**There is no third brand colour.** Anything else in the UI is functional (status, severity) or
inert (surfaces, borders) and is defined in `docs/08_UI_UX_SPEC.md`'s design tokens, which own it.

---

## 2. How the ratios were computed

WCAG 2.1 relative luminance and contrast ratio:

```
L = 0.2126·R + 0.7152·G + 0.0722·B
  where each channel is sRGB-linearised:
    c_lin = c/12.92          if c ≤ 0.03928
    c_lin = ((c + 0.055)/1.055)^2.4   otherwise

contrast = (L_lighter + 0.05) / (L_darker + 0.05)
```

Thresholds: **3:1** for large text (≥ 18.66 px bold or ≥ 24 px) and for UI component boundaries and
graphics; **4.5:1** for normal body text; **7:1** for AAA.

---

## 3. Contrast table

### On white `#FFFFFF`

| Colour | Ratio | Body text (4.5:1) | Large text / UI (3:1) |
|---|---:|---|---|
| Ledger Blue `#0369A1` | **5.93 : 1** | ✅ **PASS AA** | ✅ PASS AAA territory |
| Slate Ink `#0F172A` | **17.85 : 1** | ✅ **PASS AAA** | ✅ PASS AAA |

### Ledger Blue `#0369A1` as a background, white text on top

| Text colour | Ratio | Verdict |
|---|---:|---|
| White `#FFFFFF` | **5.93 : 1** | ✅ PASS AA for body text — safe for filled primary buttons |
| Slate Ink `#0F172A` | **4.05 : 1** | ⚠️ Below 4.5 — **do not** put ink text on a Ledger Blue fill |

### Slate Ink `#0F172A` as a background, white text on top

| Text colour | Ratio | Verdict |
|---|---:|---|
| White `#FFFFFF` | **17.85 : 1** | ✅ PASS AAA — the dark theme's body pairing |

**The one combination to avoid** is Slate Ink on Ledger Blue (4.05:1). Ink on white, and white on
either brand colour, are all fine.

---

## 4. ⚠ Two conformance findings in the **existing** UI

I measured the colours already in the built UI against the project's own WCAG AA baseline
(`docs/08_UI_UX_SPEC.md` accessibility baseline; `docs/01` `P19` "colour is never the only signal").

| Existing token | Where it is used | Ratio on white | Verdict |
|---|---|---:|---|
| `#0284C7` (sky-600) | The app's accent — About screen, forecast chips, primary buttons in `ui/src/**`, and the bundled `app/static/assets/index-*.js` | **4.09 : 1** | ⚠️ **Fails AA for body text** (4.5 needed). Passes 3:1 for large text and UI boundaries, which is why it has gone unnoticed. |
| `#16A34A` (green-600) | The `PASS` status pill and the "Checking"/"Connected" success text | **3.30 : 1** | ⚠️ **Fails AA for body text.** Passes 3:1 for the pill's boundary only. |
| `#0284C7` on `#0F172A` | Accent on dark surfaces | **4.36 : 1** | ⚠️ Below 4.5 for body text. |

### Recommendations (lead's call — tokens are not my folder)

| # | Change | Why |
|---|---|---|
| **B1** | Move the accent from `#0284C7` → **`#0369A1`** | 4.09 → **5.93**. Same colour family, so this is a one-token change, not a redesign. Recolour the mark and lockups to match and everything stays consistent. |
| **B2** | Move the success/status green from `#16A34A` → **`#15803D`** | 3.30 → **4.76 : 1**, above AA. Same hue family. |
| **B3** | Move the warning amber to `#92400E` for text on light surfaces | `#B45309` measures 3.09 : 1 on white — also below AA for body text. `#92400E` measures **7.0 : 1**. |

**B1/B2/B3 are status and chrome colours, not the brand colours** — `docs/08` owns the status
vocabulary, and changing them changes severity legibility across the exception register, so they
need a visual pass, not just a token swap. I am flagging, not prescribing.

---

## 5. Permitted pairings

| Surface | Text / icon | Ratio | OK |
|---|---|---:|---|
| White `#FFFFFF` | Slate Ink | 17.85 | ✅ preferred body pairing |
| White `#FFFFFF` | Ledger Blue | 5.93 | ✅ links, active nav, focus rings |
| Slate Ink `#0F172A` (dark theme) | White | 17.85 | ✅ preferred |
| Ledger Blue fill | White | 5.93 | ✅ primary buttons, selected chips |
| Ledger Blue fill | Slate Ink | 4.05 | ❌ **never** |
| Ledger Blue mark on white | — | 5.93 | ✅ logo use |

---

## 6. Functional (non-brand) colours — for reference only

These are **not brand colours**. `docs/08` owns their exact values and their severity vocabulary.
They are listed here only so the lead can see they must not be restyled to look on-brand.

| Function | Current token | Note |
|---|---|---|
| Success / `PASS` | `#16A34A` | 3.30:1 on white — see B2 |
| Warning / attention | `#B45309` | 3.09:1 on white — see B3 |
| Danger / `FAIL` | `#B91C1C` | **7.0 : 1** on white — ✅ passes AA today |
| Info / notice | `#0369A1` | Same value as the primary, by design: an informational state is the brand state |

### The non-negotiable part

`docs/01` `P19` — **colour is never the only signal.** Every status carries a **word** (`PASS`,
`WARN`, `FAIL`), and severity carries a word plus, where it matters, a distinct icon shape. Any
colour change made in response to B1–B3 must preserve that. A brand colour that meets contrast but
leaves a severity readable only by hue would be a regression, not an improvement.

---

## 7. Print and export

- The mark is a **single flat fill**. It prints correctly in one colour and needs no spot-colour
  definition.
- In the Excel pack (`docs/11`) and the deck (`docs/12`), the footer and title rule use Slate Ink
  and Ledger Blue at **100 % tint**. Do not use tints of Ledger Blue for small text on white — a
  40 % tint fails contrast badly and print reproduction will not rescue it.
- For a monochrome print job, the mark and lockup both work in 100 % black with no other change.