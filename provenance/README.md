# Provenance

How the first version of the map was made, kept so that anyone can see what an AI drafted and what a reviewer changed.
Nothing here is needed to build the map.

| Folder or file | What it holds |
| --- | --- |
| `review-notes.md` | The reviewer's (Claude's) notes on every review round. |
| `map-draft/skeleton.deepseek-original.json` | DeepSeek's first outline of the map, before review. |
| `map-draft/deepseek-drafts/` | DeepSeek's first draft of each branch. |
| `map-draft/feedback/` | The corrections sent back to DeepSeek for each branch. |
| `map-draft/reviewed/` | The branches after review; converted into `nodes/` on 8 November 2026. |
| `sources-drafts/` | DeepSeek's draft citations. The reviewed versions, with corrections, are in the node files. |
| `explainer-first-law/` | Every version of the Newton's first law page (v1 to v5), the brief and the feedback for each round. |
| `briefs/` | The instructions given to DeepSeek for the README, CONTRIBUTING, issue forms and page rewrite. |
| `drafts/` | First drafts of README and CONTRIBUTING, before the last review round. |
| `map-renderer/` | Both DeepSeek versions of the live map's renderer and the review feedback between them. |
| `pipeline/` | The scripts used for the first drafts and checks (written for the earlier JSON layout; kept for reference). |
| `logs/` | One line per DeepSeek call: time taken, tokens, result. |

Raw model reasoning (`thinking` files) is excluded from the repository because it is large and not useful to readers.
