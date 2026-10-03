# Branding assets — proposal for the lead

**Status:** proposals only. Nothing merged, nothing installed.
**Branding stance:** neutral professional defaults. **No client branding is invented anywhere in
this folder.** If a real client brand arrives later, `logo-mark.svg` and `logo-lockup.svg` are the
only two files that need redrawing, and everything else (icon generation, contrast targets, the
installer/taskbar wiring in `packaging/pyinstaller.spec`) is driven by those two files.

---

## Files

| File | What it is |
|---|---|
| `logo-mark.svg` | The mark on its own. Square. For favicon, app icon, splash, deck corner. |
| `logo-lockup.svg` | Mark + wordmark, horizontal. For the About screen, deck cover, installer. |
| `logo-lockup-stacked.svg` | Mark + wordmark, stacked. For square placements (deck cover, splash). |
| `palette.md` | The two brand colours, documented with contrast ratios and permitted pairings. |
| `make_icons.py` | Generates the multi-size `app.ico` and PNG set from `logo-mark.svg`. |

---

## Two decisions I made, and why you may want to change them

**1. The mark is an abstract ledger, not a glyph.**
It is a set of four horizontal bars of different lengths inside a rounded frame — a balance sheet
read as a column of figures. It says "month-end" and "review" without saying anything that could be
mistaken for a bank, a currency symbol, or a specific accounting standard. It is monochrome by
construction (current colour only), so it survives being printed in one colour, engraved on a
favicon at 16 px, or dropped onto a dark surface.

**If you would rather have a monogram ("FM", "C")** — that is a legitimate alternative and the
`make_icons.py` pipeline does not change. Edit `logo-mark.svg`, re-run the script, done. I chose
the abstract mark because a two-letter monogram with a generic wordmark is the single most
over-used shape in this product category, and it ages badly.

**2. The wordmark uses the application name in a humanist sans, not a stylised logotype.**
"FP&A Month-End Copilot" is long and contains an ampersand and a hyphen. A custom logotype for
that string is expensive to do well and fragile across the ten places it has to fit (installer
title bar, About screen, deck cover at 13.3 in, Excel pack footer, doc header). **I recommend the
plain-wordmark treatment below** and would spend the design budget on the mark instead. If the
client later wants a distinctive logotype, that is a real piece of work with its own lead time, and
it should not be smuggled into a pilot.

---

## The two brand colours

Full detail, contrast ratios and permitted pairings: **`palette.md`**.

| Role | Hex | Where it is used |
|---|---|---|
| **Primary — Ledger Blue** | `#0369A1` | App chrome accents, primary buttons, the mark itself, links, the deck's title rule |
| **Neutral — Slate Ink** | `#0F172A` | Headings, primary body text, the deck's title text, table headers |

**No third brand colour.** Status colours (`PASS`/`WARN`/`FAIL`, exception severity) are
**functional**, not brand: they are the documented status palette, they must not be restyled to
look on-brand, and they must never be the only signal (`docs/01` `P19`: colour is never the only
signal — every status carries a word and, where it matters, an icon). See `palette.md` §4.

---

## ⚠ One finding you should know about

**The primary colour already in the UI fails WCAG AA for body text.**

The built UI uses `#0284C7` (sky-600) as its accent — it is what you will see in the About screen,
the forecast chips, and the bundled `app/static/assets/index-*.js`. Measured against white it is
**4.09 : 1**, below the **4.5 : 1** AA threshold for normal-size text. It passes the 3 : 1 bar
that applies to large text and to UI component boundaries, which is why it has not been obvious.

`palette.md` recommends `#0369A1` (sky-700, **5.93 : 1**) as the primary, which is already in the
colour family the UI uses, so this is a one-token change rather than a redesign. **This is a
recommendation, not a change I made** — the tokens live in `ui/src/`, which is not my folder.

Related, and from the same file: the UI's status green `#16A34A` measures **3.30 : 1** on white,
also below 4.5. `palette.md` §4 gives a compliant alternative. Note that `docs/08_UI_UX_SPEC.md`
§"formatting" sets the WCAG AA baseline as a project rule, so this is a conformance gap against the
project's own standard, not an external opinion.

---

## The `app.ico` question — and why I did not just hand you a binary

**I cannot create a binary `.ico` here.** This host has no shell (see
`audit-external/progress.md` §Environment blocker), so I cannot run an image encoder, and I will
not fabricate a file by pasting unverified base64 that nobody can inspect.

What I have provided instead is the thing that actually produces it:

- `logo-mark.svg` is resolution-independent — it is the real master.
- `make_icons.py` renders it to PNG at 16/24/32/48/64/128/256 px, packs a proper multi-size
  `app.ico`, and writes the PNG set. It depends only on `cairosvg` and `Pillow`.
- Running it produces `app.ico` plus a PNG ladder in `out/`.

**Windows icon guidance the script implements** (this is why the ladder matters):

- **16 px** is the taskbar and the Alt-Tab entry. This is where most icons fail — thin strokes
  and internal detail vanish. The mark is drawn with strokes at a ratio that survives 16 px.
- **32/48 px** cover Explorer medium/large icons and the Alt-Tab preview.
- **256 px** is the Explorer icon size and what the installer should ship at.
- An `.ico` with **all seven sizes in one container** is what Windows expects; shipping a single
  256 px image inside an `.ico` is the common cause of a blurry taskbar.

**Where to wire it** (lead's edit, not mine — `packaging/pyinstaller.spec` and any UI shell config):

| Target | Setting |
|---|---|
| Installer icon (Inno Setup) | `[Setup] SetupIconFile=` → the 256 px PNG or the `.ico` |
| Exe file icon (PyInstaller) | `icon=` on the `EXE(...)` / `BINARY(...)` entry |
| App window / taskbar | `pywebview` window `icon`, or an `<link rel="icon">` in `ui/index.html` |
| Deck / Excel pack | `docs/12` / `docs/11` own the stamping — they take the icon path as a parameter |

---

## Accessibility notes on the mark itself

- The mark is **not** a pictogram that carries meaning on its own — it is a brand mark, always
  paired with the product name. So it does not need a text alternative in the UI beyond the app
  title that is already there.
- In `logo-lockup.svg` the wordmark is real `<text>`, so it is selectable and screen-readable. If
  the lead converts these to outlined paths for the installer, **keep an accessible copy with live
  text** and use the outlined version only for print/export.
- The mark uses no gradients, no thin strokes, and no colour-only distinction. `docs/08` `P19`
  applies to charts and status, and the mark complies by construction.