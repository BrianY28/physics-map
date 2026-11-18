# Review of your map renderer (v1): 4 changes

The renderer was tested in a browser at 1920×1000, 1400×860 and 400×800, in light and dark. Results: the two-sided map fills 90% of the width and 96% of the height at 1920×1000 (the old page used 23% of the width); no labels overlap in any state, including all 326 concepts expanded; links, tooltips, wheel zoom, drag to pan, drag-on-a-label, keyboard toggling and the toolbar all work. Good work.

The two context files are your `tools/site/map.js` and `tools/site/map.css`. Make ONLY the changes below and return both complete files. Keep every name, comment and structure that is not affected.

1. Bug (already patched by the reviewer in the context file; keep the patch): only depth-1 nodes got `side = 'left'`, so the children of left-side branches were drawn rightwards, on top of their branch title. The fix is the line in `assignX` that sets `ln.side` from `dir`.

2. Toggle circles touch the text. The circle is centred on the end of the underline, which is also where the label text ends, so it overlaps the last letter (right side) or the first letter (left side). Extend the underline of EVERY non-root node by 8 px past the label on the outer side (a new constant `OUTER_PAD = 8`): the underline runs from the inner end to `labelWidth + OUTER_PAD`, the toggle sits at that end, children measure their gap from that end, and `boundsOf` uses it. The label text itself does not move.

3. Expanded children can land outside the window. After a toggle that EXPANDS a node (and after pinning the node as now), pan the view by the smallest amount that brings the toggled node's label and all of its direct children's labels inside the host with 16 px of padding. Do not change the scale. If they cannot all fit at the current scale, bring in as much as possible while keeping the toggled node's own label fully visible. Use `applyTransform` so it does not count as a user move. Collapsing does not pan.

4. Put the SVG `<title>` tooltip element first inside each node group (before the underline), as the SVG specification recommends.
