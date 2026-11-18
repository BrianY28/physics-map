// Reviewer's browser test for the map renderer (tools/site/map.js).
// Paste into the page's console, or run it from an automation tool. Returns a report object.
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const host = document.querySelector(".pm-host");
  const view = document.querySelector(".pm-view");
  const q = sel => [...document.querySelectorAll(sel)];
  const rect = el => el.getBoundingClientRect();
  const out = {};

  const counts = () => {
    const c = { 0: 0, 1: 0, 2: 0, 3: 0 };
    q(".pm-node").forEach(n => c[n.dataset.depth]++);
    return c;
  };
  const usage = () => {
    const h = rect(host), v = rect(view);
    return {
      host: [Math.round(h.width), Math.round(h.height)],
      widthPct: Math.round(100 * v.width / h.width), heightPct: Math.round(100 * v.height / h.height),
      inside: v.left >= h.left - 1 && v.right <= h.right + 1 && v.top >= h.top - 1 && v.bottom <= h.bottom + 1,
    };
  };
  // Labels may not overlap each other (1 px tolerance).
  const overlaps = () => {
    const boxes = q(".pm-node .pm-label").map(t => ({ id: t.closest(".pm-node").dataset.id, r: rect(t) }));
    const bad = [];
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i].r, b = boxes[j].r;
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 1 && h > 1) bad.push(`${boxes[i].id} x ${boxes[j].id} (${Math.round(w)}x${Math.round(h)})`);
    }
    return bad;
  };
  const click = el => el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));

  // 1. Initial state
  out.counts = counts();
  out.sides = { left: q('.pm-node[data-depth="1"][data-side="left"]').length, right: q('.pm-node[data-depth="1"][data-side="right"]').length };
  out.usage = usage();
  out.overlapsInitial = overlaps().slice(0, 5);
  const rowH = (() => { const ys = q('.pm-node[data-depth="2"][data-side="right"]').map(n => rect(n).top).sort((a, b) => a - b); return ys.length > 1 ? +(ys[1] - ys[0]).toFixed(1) : null; })();
  out.nodeRowPxOnScreen = rowH;
  const lab = document.querySelector('.pm-node[data-depth="2"] .pm-label .pm-title');
  out.nodeFontPxOnScreen = lab ? +(parseFloat(getComputedStyle(lab).fontSize) * (rect(view).width / view.getBBox().width)).toFixed(1) : null;

  // 2. Links
  const anchors = q(".pm-node a");
  out.links = {
    total: anchors.length,
    branch: q('.pm-node[data-depth="1"] a').length, node: q('.pm-node[data-depth="2"] a').length,
    badTarget: anchors.filter(a => a.getAttribute("target") !== "_blank" || !/noopener/.test(a.getAttribute("rel") || "")).length,
    sample: anchors.slice(0, 1).map(a => a.getAttribute("href") || a.getAttribute("xlink:href")),
  };

  // 3. Expand one node: concepts appear, the node stays put, nothing overlaps
  const node = document.querySelector('.pm-node[data-id="b0-n0"]');
  const before = rect(node);
  click(node.querySelector(".pm-toggle"));
  await sleep(300);
  const after = rect(document.querySelector('.pm-node[data-id="b0-n0"]'));
  out.expandNode = {
    conceptsShown: q('.pm-node[data-depth="3"]').length,
    movedPx: [Math.round(after.left - before.left), Math.round(after.top - before.top)],
    ariaExpanded: document.querySelector('.pm-node[data-id="b0-n0"] .pm-toggle').getAttribute("aria-expanded"),
    explainerLinks: q('.pm-node[data-depth="3"] a').map(a => a.getAttribute("href")),
    overlaps: overlaps().slice(0, 5),
  };

  // 4. Expand every node on screen, check overlaps, then collapse again
  for (const t of q('.pm-node[data-depth="2"] .pm-toggle[aria-expanded="false"]').map(t => t.closest(".pm-node").dataset.id)) {
    click(document.querySelector(`.pm-node[data-id="${t}"] .pm-toggle`));
  }
  await sleep(300);
  out.expandAll = { counts: counts(), overlaps: overlaps().slice(0, 5) };
  for (const t of q('.pm-node[data-depth="2"] .pm-toggle[aria-expanded="true"]').map(t => t.closest(".pm-node").dataset.id)) {
    click(document.querySelector(`.pm-node[data-id="${t}"] .pm-toggle`));
  }
  await sleep(300);

  // 5. Collapse and reopen a branch
  click(document.querySelector('.pm-node[data-id="b1"] .pm-toggle'));
  await sleep(300);
  out.collapseBranch = { counts: counts() };
  click(document.querySelector('.pm-node[data-id="b1"] .pm-toggle'));
  await sleep(300);
  out.afterRestore = { counts: counts(), overlaps: overlaps().slice(0, 5) };

  // 6. Toolbar
  const buttons = q(".pm-toolbar button");
  out.toolbar = buttons.map(b => `${b.textContent.trim()} / ${b.getAttribute("aria-label")} / ${Math.round(rect(b).width)}x${Math.round(rect(b).height)}`);
  const fitBtn = buttons.find(b => /fit/i.test(b.textContent));
  const w0 = rect(view).width;
  click(buttons.find(b => b.textContent.trim() === "+")); await sleep(300);
  const w1 = rect(view).width;
  click(fitBtn); await sleep(400);
  out.zoom = { zoomInFactor: +(w1 / w0).toFixed(2), afterFit: usage() };
  return out;
})();
