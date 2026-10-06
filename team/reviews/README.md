# Whole-project design reviews (task `RV-01` → synthesis `RV-90`)

**Why this exists.** This is the third attempt at this product (`github.com/Warzonesiddiki/fpa`,
`.../fp-A-betterversion`, now `.../finalFPA`). Two prior repos of lessons and one shared codebase make a
five-agent independent review cheap and unusually valuable: five different contexts, five sets of eyes,
written before anyone reads anyone else's, so agreement is evidence rather than politeness.

## Rules
1. **One file per agent:** `team/reviews/<agent>.md`. Never edit another agent's review — respond in yours.
2. Write it **independently first**; read the others' only after yours is committed to disk.
3. Every claim needs evidence: a file, a number, a spec clause, or "opinion" stated as opinion.
4. Rank your top 5 suggestions by (impact on the accountant's day) ÷ (cost), and say what you would
   **remove** as well as add — over-built surface is a real defect class here.
5. Check every suggestion against the spec of record (`R1`): if it changes scope, behaviour or a bar, it
   goes to `buffy` as an `OQ`/proposal, not into code.

## Prompt to answer (same for all four)
- What is the single most valuable thing this tool does for an FP&A analyst at month-end today, measured
  against the docs — and where does the implementation currently fall short of that promise?
- What does the product do that a real month-end close would never need (cut it)?
- What is missing that a real analyst would ask for in the first hour of using it?
- Where is the architecture working against the product (`09` module map, `12` deck, `03`/`04` import)?
- What did the earlier attempts likely get right that this one has not carried over?
- Your top 5 suggestions, with evidence, expected impact, effort and trade-off.

## Synthesis (`RV-90`, leader)
`team/reviews/SYNTHESIS.md`: consensus, disagreements and why, ranked recommendation list, the spec-conflict
check, and the `OQ`/`DEC` list the owner must rule on. Nothing lands in `docs/` without that check (`R1`).
`hermes`'s `UX-01` journey audit (`team/reviews/hermes-journey.md`) feeds this synthesis as the
analyst-side input.
