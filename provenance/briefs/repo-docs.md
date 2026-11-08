# Brief: README.md and CONTRIBUTING.md for the Physics Map repository

Write two files for a public GitHub repository. Use only the facts below; do not invent features, numbers, people or links.

## Facts

- Repository: https://github.com/BrianY28/physics-map
- Live interactive map (GitHub Pages): https://briany28.github.io/physics-map/ . It is a zoomable mind map; every node in it links to that node's Markdown file on GitHub, where anyone can propose an edit.
- What it is: an open mind map of physics, from Newton's Principia (1687) to the open research frontier, built from plain-text files so that anyone can correct, extend or review a single node through a pull request.
- Size today: 11 branches, 82 nodes, 326 concepts. Branch table (title | period | nodes | concepts):
  | Newtonian mechanics | 1687-1830s | 6 | 24 |
  | Electromagnetism and optics | 1785-1900 | 7 | 26 |
  | Thermodynamics and statistical mechanics | 1824-1902 | 7 | 28 |
  | Quantum mechanics and QFT | 1900-1970s | 8 | 32 |
  | Relativity and gravitation | 1905-present | 7 | 27 |
  | Nuclear and particle physics | 1896-2012 | 8 | 32 |
  | Atomic, molecular, optical physics | 1814-present | 7 | 28 |
  | Condensed matter physics | 1911-present | 8 | 32 |
  | Astrophysics and cosmology | 1915-present | 8 | 32 |
  | Fluids, plasmas and complex systems | 1822-present | 7 | 28 |
  | Open frontier | today | 9 | 37 |
- Structure: map > branch > node > concept. A node is a topic such as "Newton's laws" or "Quantum gravity"; concepts are its 2-5 key results, laws, experiments or open questions.
- Folder layout:
  - `nodes/NN-branch-name/README.md`: the branch (front matter `span`, then `# Title` and a one-paragraph summary). The NN prefix sets branch order.
  - `nodes/NN-branch-name/node-name.md`: one file per node.
  - `explainers/NAME/index.html`: optional interactive explainer pages for single concepts. The first one is `explainers/first-law/` (Newton's first law, three simulations).
  - `tools/build.py`: checks every node and generates the outputs. `tools/nodelib.py`: the file format. `tools/draft/deepseek.py`: optional AI drafting helper.
  - `provenance/`: how the first version was drafted and reviewed (DeepSeek drafts, review feedback, logs).
  - Generated files committed to the repo: `INDEX.md` (every branch and node with links, for browsing on GitHub) and `map.opml` (import into MindNode, XMind or any OPML outliner). The website is generated into `site/` (not committed).
- Node file format (exact). Front matter, then the body:
  ```
  ---
  order: 10
  when: 1687
  people:
    - Isaac Newton
  status: established
  sources:
    - "Newton, I. (1687). Philosophiae Naturalis Principia Mathematica. London: Royal Society."
  drafted_by: DeepSeek V4.1 Flash
  reviewed_by:
    - Claude (AI)
  ---

  # Newton's laws

  The Principia states three laws: inertia, force proportional to change of motion, and equal and opposite action-reaction, giving F = dp/dt (commonly F = ma). Together they define inertial frames and reduce mechanics to solving differential equations.

  ## Concepts

  - **First law: inertia**: A body persists in uniform motion unless acted on by a net force, which implicitly defines the inertial frames where the laws hold. [Explainer](../../explainers/first-law/)
  - **Second law F = dp/dt**: The rate of change of momentum equals the applied force, so trajectories follow from integrating the equations of motion.
  ```
- Field rules (the build enforces them):
  - `order`: whole number that sets the node's position in its branch; numbers go up in tens so a new node can slot in between (for example 15).
  - `when`: year, span or decade (for example `1925-1926`, `1970s`, `since 1933`).
  - `people`: list of key people (may be empty for frontier topics).
  - `status`: `established` or `open`. Open means an unsolved problem or an active research programme; open nodes live mainly in the Open frontier branch.
  - `as_of`: required when status is open; the date (YYYY-MM-DD) when the node's facts were last checked. The build warns when an open node has not been checked for more than 12 months.
  - `sources`: at least one. Format: `Author, A., & Author, B. (Year). Title. Journal or Publisher, volume, pages.` in double quotes. Prefer the original paper or book; for frontier nodes, the result paper or collaboration paper, or a peer-reviewed review. Press releases and news articles may be added only next to a primary source.
  - `drafted_by`: who or what wrote the text (a person's GitHub handle, or the AI model).
  - `reviewed_by`: list of reviewers, each as `"github-handle, background"` (for example `"octocat, physics PhD student"`).
  - Title (the `# ` line): at most 7 words. The paragraph under it: 1-2 plain sentences, key equation in plain Unicode (F = ma, E = mc²), not LaTeX.
  - Concepts: 2-5 lines, each exactly `- **Title**: One sentence.` An optional ` [Explainer](../../explainers/NAME/)` link at the end of a concept line.
  - File name: lowercase words joined by hyphens, unique across the whole map (it is the node's id).
  - Front matter values are bare words or "double-quoted strings"; lists use `  - item` lines. Anything else is rejected with a message saying what to fix.
- Building and checking (Python 3.9 or newer, no other dependencies):
  - `python3 tools/build.py` checks every file and regenerates `INDEX.md`, `map.opml` and `site/`.
  - `python3 tools/build.py --check` checks every file and fails if `INDEX.md` or `map.opml` are out of date. GitHub runs this on every pull request; after a merge to `main`, GitHub rebuilds and publishes the live map.
- Ways to contribute:
  1. Fix a node: open its file on GitHub (or click it in the live map), press the pencil icon, edit, and open a pull request. Or open an issue with the "Node correction" form.
  2. Add sources or review a node: adding sources and reviewing existing nodes are the most useful first contributions. Add yourself to `reviewed_by` when you have checked a node against its sources.
  3. Add a node: create a new file in the right branch folder; one node per pull request. Or propose it with the "New node" issue form.
  4. Update the frontier: when a result changes the status of an open question, update the node, its sources and `as_of`. "Frontier update" issue form. When a question is settled, change status to established and, if it fits better, move the node to its home branch.
  5. Write an explainer page (see below).
- Explainer pages: `explainers/NAME/index.html`, one interactive page per concept. Format: the idea stated plainly with its key equation; 1 to 3 small interactive simulations, each with 2-3 sentences of setup and the one common mistake it disproves; a short collapsed history; sources; links back to the node. At most about 600 words of prose. Technical rules: the file is an HTML fragment (no doctype, html, head or body tags; the build adds them), all CSS and JavaScript inline, no external scripts (Google Fonts allowed), colors as CSS custom properties with a dark-mode version, readable at 400 px wide. Link it from the concept line in the node file. Physics in a simulation must match the stated formulas.
- AI-assisted contributions are welcome if disclosed: put the model name in `drafted_by`, check every claim against the sources yourself, and say in the pull request what you checked. The repository's own helper, `tools/draft/deepseek.py`, drafts with DeepSeek V4.1 Flash through a local Ollama server.
- How the first version was made (be plain and honest about this in the README): on 8 November 2026 the map was drafted by DeepSeek V4.1 Flash (through Ollama) and supervised by Claude (Anthropic's AI model). Claude designed the outline, checked every branch and sent DeepSeek about 40 factual corrections (for example a misattributed quotation translation, outdated frontier results such as the muon g-2 anomaly, which largely went away in 2025, and missing recent results), and verified frontier facts against published sources as of November 2026. No physicist has reviewed the map yet, so every node currently lists only "Claude (AI)" under `reviewed_by`. Expert review is the most valuable contribution. The full record is in `provenance/`.
- Licenses: content (everything in `nodes/`, `explainers/`, and the generated `INDEX.md` and `map.opml`) is CC BY-SA 4.0, see `LICENSE-CONTENT.md`; code (`tools/`, `.github/`) is MIT, see `LICENSE`. By opening a pull request, contributors agree their contribution is licensed the same way.
- Issue forms that exist: "Node correction", "New node", "Frontier update". A pull request template with a checklist exists.

## README.md requirements
- Under about 110 lines. Order: title "Physics Map" and a one-sentence description; "View the map" (live map link, INDEX.md, map.opml); "What's inside" (the branch table plus one sentence on map > branch > node > concept); "Contribute" (the five ways, each 1-2 lines, linking to CONTRIBUTING.md sections and the issue forms via https://github.com/BrianY28/physics-map/issues/new/choose); "How this map was made" (the honest paragraph above); "Build it locally" (the two commands); "License".
- Plain, direct sentences in active voice. No emoji, no badges, no marketing language, no em-dash asides.

## CONTRIBUTING.md requirements
- Sections in this order: Ground rules (accuracy over completeness, sources for every claim, plain language, one topic per pull request, be civil); Quick edits on GitHub; The node file (the exact example above and a table of every field and rule); Adding a node; Frontier nodes; Sources; Reviewing a node; AI-assisted contributions; Explainer pages; Checking your change (the two commands and what GitHub checks); Licensing of contributions.
- Use the exact rules above. Include code blocks where they help. Same writing style as the README.
