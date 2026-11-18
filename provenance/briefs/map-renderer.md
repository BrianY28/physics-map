# Brief: two-sided mind map renderer for the Physics Map site

You are an expert front-end engineer. Write a small, dependency-light mind map renderer for the public site of the Physics Map (https://github.com/BrianY28/physics-map).

## Why
The current page draws all 82 topics down one side of the root. The tree is about 1,700 px tall and 440 px wide, so on a 1920×1000 window it is scaled down to 8 px rows and fills only 23% of the width. The new renderer puts branches on BOTH sides of a central root (like MindNode or XMind) so the map fills the window at a readable size.

## Deliverables
Two files, complete and working:
- `tools/site/map.js`: defines `window.PhysicsMap = { mount }`.
- `tools/site/map.css`: every style the map needs.

The page (not your job) loads `map.css`, then d3 v7.9.0 as the global `d3` (https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js), then `map.js`, then calls `PhysicsMap.mount(host, data)` once, where `host` is an empty block element that already has a size (it fills the window below a slim header). The page defines these CSS custom properties on `:root`, with light and dark values: `--bg`, `--fg`, `--muted`, `--line`, `--accent`, `--signal`. Use them for every colour except the branch palette. Do not load any script, font or stylesheet yourself. Use d3 only for zoom and pan (d3.zoom, d3.select, d3.zoomIdentity, d3.zoomTransform); build the DOM with plain JavaScript or d3, as you prefer. Plain ES2017 in one IIFE, no modules, no build step.

## Data passed to mount (exact shape)
```json
{
  "title": "Physics: From Newton to the Frontier",
  "branches": [
    {
      "title": "Newtonian mechanics",
      "span": "1687-1830s",
      "url": "https://github.com/BrianY28/physics-map/tree/main/nodes/01-newtonian-mechanics",
      "nodes": [
        {
          "title": "Newton's laws",
          "when": "1687",
          "open": false,
          "url": "https://github.com/BrianY28/physics-map/blob/main/nodes/01-newtonian-mechanics/newtons-laws.md",
          "concepts": [
            { "title": "First law: inertia", "explainer": "explainers/first-law/" },
            { "title": "Second law F = dp/dt" }
          ]
        }
      ]
    }
  ]
}
```
There are 11 branches, 82 nodes and 326 concepts today. `open: true` marks an unsolved (frontier) topic. `explainer` is optional and is a relative URL.

## Tree and initial state
Depth 0 is the root (the map title). Depth 1 = branches, depth 2 = nodes, depth 3 = concepts. Initially branches are expanded and nodes are collapsed, so the root, 11 branches and 82 nodes are visible and concepts are hidden.

## Layout (world coordinates in px at zoom 1; root centre is the origin)
- Mode: two-sided when `host.clientWidth / host.clientHeight >= 1.15`, otherwise one-sided (every branch on the right). Portrait phones get the one-sided layout.
- Two-sided split: the LEFT side holds the first k branches, top to bottom; the RIGHT side holds the rest, top to bottom (older fields on the left, newer on the right). Choose k to minimise the difference between the two sides' heights in the initial state. Recompute the split only at mount and when the mode flips after a resize, never when a node is toggled.
- Rows: every visible leaf takes one row. Row height by depth: depth 1 = 28, depth 2 = 20, depth 3 = 18. Add a 12 px gap between consecutive branches on the same side. A parent's y is the midpoint between its first and last visible child. After assigning rows, shift each side so that its vertical extent is centred on y = 0.
- Fonts: family `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. Root 18 px weight 700; branch 15 px weight 600; node 14 px weight 400; concept 13 px weight 400; meta text (branch span, "open" tag, "explainer" link) 11 px weight 400. Measure label widths with a canvas 2D context using exactly these fonts, and set the same font on the SVG text, so measurement and rendering agree.
- Label = title, then optional meta text 6 px after it: branch meta = its `span`; node meta = `open` (only when `open` is true); concept meta = `explainer` (only when it has one). Label width = title width + (meta ? 6 + meta width : 0). Labels are a single line; no wrapping.
- Horizontal distances are measured outward from the centre, the same on both sides (multiply by −1 for the left side). The root is a rounded box centred on the origin: width = title width + 32, height 40. For a child at depth d: `inner = parentOuter + GAP[d]`, `outer = inner + labelWidth`, with GAP = {1: 48, 2: 40, 3: 32}; for the root, `parentOuter` is half the root box width.
- Each non-root node is drawn as: an underline from `inner` to `outer` at the node's y; the label text sitting just above the underline (baseline about 5 px above it), spanning the same extent; a link from the parent's attach point (the parent underline's outer end, or the middle of the root box's side edge) to this node's inner end, as a cubic Bézier with horizontal tangents (`M x0,y0 C mx,y0 mx,y1 x1,y1`, mx halfway). Stroke widths: depth 1 = 2.5, depth 2 = 2, depth 3 = 1.5, same for the link and the underline. Links, underlines and toggles use the branch colour.
- On the left side the label still reads left to right in the order title, meta, and its right end sits at the inner end (use `text-anchor: end`).
- Branch palette, by branch index: `["#3b82c4","#e8833a","#cf4f4f","#2aa198","#5aa846","#c9a227","#a66bbe","#e377a2","#a0785a","#6f8fa6","#7b61ff"]`.
- Toggle: branches, and nodes that have concepts, get a circle of radius 5 centred on the underline's outer end: filled with the branch colour when collapsed, filled with `var(--bg)` and stroked with the branch colour when expanded. Give it an invisible hit area of radius 11.

## Behaviour
- Clicking a toggle (or pressing Enter or Space on it) expands or collapses that node, recomputes the layout and re-renders. Keep the toggled node at the same place on screen: after the re-layout, adjust the zoom translation by the node's change in world position. No animation is needed; a full re-render is fine.
- Titles are links (SVG `<a>` with `target="_blank"` and `rel="noopener"`): branch title → branch `url`; node title → node `url`; a concept's `explainer` meta → the explainer URL. Concept titles and the root are plain text. A click on a link must open it; a drag that starts on a label must pan the map and must not open the link.
- Tooltips with an SVG `<title>`: node = `Title · when` plus ` · open question` when open; branch = `Title · span`.
- Zoom and pan with d3.zoom on the SVG: scale extent 0.15 to 4, wheel and pinch zoom, drag to pan, double-click zoom disabled.
- `fit()`: scale and centre the whole drawing (all labels and toggles) inside the host with 20 px padding, with a maximum scale of 1.6. Call it at mount.
- Resizing: observe the host with a ResizeObserver, debounced 150 ms. If the mode flips, redo the split and layout, then `fit()`. Otherwise call `fit()` only when the user has not zoomed or panned since the last fit. If the host has no size yet at mount, wait for the first resize.
- Toolbar: inside the host, bottom right, three `<button type="button">` elements with these labels and aria-labels: `−` (Zoom out), `+` (Zoom in), `Fit` (Fit map to window). Zoom buttons scale by 1.25 around the centre of the view.
- `mount(host, data)` returns `{ fit, zoomBy(factor), destroy }`.

## DOM contract (used by the reviewer's tests; follow it exactly)
- `host` gets the class `pm-host`. Inside it: one `<svg class="pm-svg">` containing one `<g class="pm-view">` that carries the zoom transform, and one `<div class="pm-toolbar">`.
- Every drawn node is a `<g class="pm-node" data-depth="0|1|2|3" data-side="left|right|center" data-id="...">` positioned with `transform="translate(x,y)"`, where (x, y) is the world position of its inner end (the root uses its centre). `data-id` is `root`, `b3` (branch index), `b3-n2`, or `b3-n2-c1`.
- Inside a node group: `<path class="pm-underline">`, `<text class="pm-label">` (the title in `<tspan class="pm-title">`, the meta in `<tspan class="pm-meta">`), and, when it has children, `<g class="pm-toggle" role="button" tabindex="0" aria-expanded="true|false" aria-label="...">`.
- Links are `<path class="pm-link">` elements placed before the node groups so that labels draw on top.

## CSS requirements (`map.css`)
- `.pm-host { position: relative; overflow: hidden; }`; the SVG fills it (`width: 100%; height: 100%; display: block`), with `touch-action: none`, `cursor: grab` (and `grabbing` while dragging), and `user-select: none` on text.
- Text fill `var(--fg)`; meta text `var(--muted)`; the `open` tag `var(--signal)`; the explainer link `var(--accent)` and underlined. Link titles show an underline on hover and a visible focus style. Root box: fill `var(--bg)`, stroke `var(--line)`.
- Toolbar: compact buttons using the page colours, readable in light and dark, with a visible `:focus-visible` outline and a hit area of at least 32×32 px.
- Prefix every class with `pm-`. No colour literals except inside the branch palette (which lives in the JavaScript).

## Quality bar
- No console errors. No overlapping labels: rows must never collide, in either mode, with any combination of expanded nodes.
- At 1920×1000 the initial two-sided fit must use at least 60% of the host width and at least 85% of its height. At 400×800 the one-sided layout must fit entirely inside the host.
- Clean, commented code that a contributor can read: named constants at the top, one function for layout, one for rendering.
