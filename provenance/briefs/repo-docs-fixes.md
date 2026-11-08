# Review of your README.md and CONTRIBUTING.md drafts

Both drafts are good: accurate, well structured and in the requested style. Return both files again with only these changes. Keep everything else word for word.

## README.md
1. Replace the "How this map was made" paragraph. The previous brief was wrong about one example (the quotation fix was on the explainer page, not in the map), and sources were added after it. Use these facts, in 2 short paragraphs:
   - On 8 November 2026 the map was drafted by DeepSeek V4.1 Flash (through Ollama) and supervised by Claude (Anthropic's AI model). Claude designed the outline, checked every branch and sent DeepSeek about 40 factual corrections; for example, the four-equation vector form of Maxwell's equations is Heaviside's (1884), not Maxwell's; Carnot never wrote η = 1 − T_C/T_H; and several frontier results were out of date, such as the muon g-2 anomaly, which largely went away in 2025.
   - DeepSeek then drafted 224 citations. Claude checked every one, fixed a citation that blended two different dark-matter papers, a wrong author list and frontier entries that cited only old discoveries, and verified the recent papers against publisher records. The map now has 228 sources. The Newton's first law explainer was also written by DeepSeek and tested by Claude in a browser, with 18 fixes over three rounds.
   - Keep the sentences saying no physicist has reviewed the map yet, every node lists only "Claude (AI)" under `reviewed_by`, expert review is the most valuable contribution, and the full record is in `provenance/`.
2. Contribute item 2: rename it "Check a node or improve its sources" and say: every node already lists sources; checking a node against them, or adding a better primary source, is the most useful first contribution. Add yourself to `reviewed_by` when you have checked a node.
3. Give the build code block the language `bash`.

## CONTRIBUTING.md
4. "The node file": replace the example's single source with the three sources of the real file, given in the context file `nodes/01-newtonian-mechanics/newtons-laws.md` (copy its whole front matter and body exactly; it has all four concepts).
5. "Sources": replace "Adding sources to existing nodes is one of the most useful first contributions." with "Checking an existing source, or adding a better primary source, is one of the most useful first contributions." Add a bullet: "If the work has a DOI, add it at the end of the citation as https://doi.org/..., which lets reviewers check it quickly."
6. Give every code block a language: `yaml` for front-matter snippets, `markdown` for the whole node file, `text` for the citation pattern, `bash` for commands.
7. "Explainer pages": add "Start from `explainers/first-law/index.html`, which follows this format." and add to the list of contents "links to the live map and to the node's file on GitHub".

Return both complete files as `README.md` and `CONTRIBUTING.md`.
