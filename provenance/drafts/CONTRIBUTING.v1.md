# Contributing to Physics Map

This map is a set of plain-text files. Every correction, new node or review arrives as a pull request against one file, and the rest of the map stays as it is.

## Ground rules

- **Accuracy over completeness.** A short node that is right is worth more than a long one that is uncertain.
- **Sources for every claim.** Each node lists at least one source in the front matter. A claim that no source backs should not be in the file.
- **Plain language.** Write for a physics student who is new to the topic. Give the key equation in plain Unicode, not LaTeX.
- **One topic per pull request.** A node fix, a new node, a source addition or an explainer each go in their own pull request, so each can be reviewed on its own.
- **Be civil.** Review the text, not the person.

## Quick edits on GitHub

You do not need to clone the repository to fix a node.

1. Open the node's file on GitHub. From the live map, click the node.
2. Press the pencil icon to edit the file.
3. Make the change and open a pull request.

If you would rather describe the problem than edit the file, open an issue with the "Node correction" form. The issue forms, "Node correction", "New node" and "Frontier update", are all at https://github.com/BrianY28/physics-map/issues/new/choose. A pull request template with a checklist appears when you open a pull request.

## The node file

There is one file per node at `nodes/NN-branch-name/node-name.md`. The `NN` prefix sets the order of the branch, and the branch summary lives in `nodes/NN-branch-name/README.md`. The node file format is fixed, and the build checks it:

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

| Field or part | Rule |
| --- | --- |
| `order` | Whole number that sets the node's position in its branch. Numbers go up in tens so a new node can slot in between, for example 15. |
| `when` | Year, span or decade, for example `1925-1926`, `1970s`, `since 1933`. |
| `people` | List of key people. May be empty for frontier topics. |
| `status` | `established` or `open`. Open means an unsolved problem or an active research programme, and open nodes live mainly in the Open frontier branch. |
| `as_of` | Required when status is open: the date (YYYY-MM-DD) when the node's facts were last checked. The build warns when an open node has not been checked for more than 12 months. |
| `sources` | At least one. Format and choice of source are set out under [Sources](#sources). |
| `drafted_by` | Who or what wrote the text: a person's GitHub handle, or the AI model. |
| `reviewed_by` | List of reviewers, each as `"github-handle, background"`, for example `"octocat, physics PhD student"`. |
| Title (the `# ` line) | At most 7 words. |
| Paragraph under the title | 1 to 2 plain sentences, with the key equation in plain Unicode (F = ma, E = mc²), not LaTeX. |
| Concepts | 2 to 5 lines, each exactly `- **Title**: One sentence.` An optional ` [Explainer](../../explainers/NAME/)` link goes at the end of a concept line. |
| File name | Lowercase words joined by hyphens, unique across the whole map. It is the node's id. |

Front matter values are bare words or "double-quoted strings", and lists use `  - item` lines. Anything else is rejected with a message saying what to fix.

## Adding a node

1. Create the file in the folder of the branch it belongs to: `nodes/NN-branch-name/node-name.md`.
2. Pick an `order` in tens that puts it where you want it. A node between `order: 10` and `order: 20` gets `order: 15`.
3. Give it 2 to 5 concepts, at least one source and a `status`.
4. Open one pull request for that node. One node per pull request.

If you would rather propose the node than write it, open an issue with the "New node" form.

## Frontier nodes

An open node marks an unsolved problem or an active research programme. It needs `status: open` and an `as_of` date, the day its facts were last checked. The build warns when an open node's `as_of` is more than 12 months old, so check the literature and move the date forward when you review the node.

When a result changes the status of an open question, update the node text, its sources and `as_of`, and use the "Frontier update" form if you prefer to report it. When a question is settled, change `status` to established and, if it fits better in another branch, move the node to its home branch.

## Sources

Every node needs at least one source, given as a double-quoted string in this form:

```
Author, A., & Author, B. (Year). Title. Journal or Publisher, volume, pages.
```

- Prefer the original paper or book.
- For frontier nodes, cite the result paper, the collaboration paper, or a peer-reviewed review.
- Press releases and news articles may be added only next to a primary source.

Adding sources to existing nodes is one of the most useful first contributions.

## Reviewing a node

Review means checking the node's claims against the sources it lists. When you have done that, add yourself to `reviewed_by`:

```
reviewed_by:
  - "octocat, physics PhD student"
```

Each entry is a GitHub handle and a short background, separated by a comma. Expert review is the most valuable contribution to the map, because every node currently lists only "Claude (AI)".

## AI-assisted contributions

AI-assisted contributions are welcome if you disclose them.

- Put the model name in `drafted_by`.
- Check every claim against the sources yourself.
- Say in the pull request what you checked.

The repository's own helper is `tools/draft/deepseek.py`. It drafts with DeepSeek V4.1 Flash through a local Ollama server.

## Explainer pages

An explainer page is one interactive page for a single concept, at `explainers/NAME/index.html`. The first one is `explainers/first-law/`, which covers Newton's first law with three simulations. The file is an HTML fragment with the page content, and the build adds the document around it.

The page contains:

- the idea stated plainly, with its key equation;
- 1 to 3 small interactive simulations, each with 2 to 3 sentences of setup and the one common mistake it disproves;
- a short collapsed history;
- sources;
- links back to the node.

Keep the prose to at most about 600 words.

Technical rules:

- The file is an HTML fragment. Do not add a doctype, `html`, `head` or `body` tags; the build adds them.
- All CSS and JavaScript are inline, with no external scripts. Google Fonts is allowed.
- Colors are CSS custom properties with a dark-mode version.
- The page is readable at 400 px wide.
- Physics in a simulation must match the stated formulas.

Link the page from the concept line in the node file, at the end of the line: ` [Explainer](../../explainers/NAME/)`.

## Checking your change

Check the map locally before you open a pull request. You need Python 3.9 or newer and no other dependencies.

```
python3 tools/build.py
python3 tools/build.py --check
```

The first command checks every file and regenerates `INDEX.md`, `map.opml` and `site/`. The second checks every file and fails if `INDEX.md` or `map.opml` are out of date. GitHub runs `--check` on every pull request. After a merge to `main`, GitHub rebuilds and publishes the live map.

`tools/build.py` checks every node and generates the outputs. `tools/nodelib.py` holds the file format. `provenance/` records how the first version was drafted and reviewed, with the DeepSeek drafts, the review feedback and the logs.

## Licensing of contributions

Content in `nodes/`, `explainers/`, `INDEX.md` and `map.opml` is CC BY-SA 4.0, see `LICENSE-CONTENT.md`. Code in `tools/` and `.github/` is MIT, see `LICENSE`. By opening a pull request, you agree that your contribution is licensed the same way.
