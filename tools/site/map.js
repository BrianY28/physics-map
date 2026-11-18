/*
 * Physics Map — two-sided mind map renderer.
 *
 * Public API:  window.PhysicsMap = { mount }
 *   const map = PhysicsMap.mount(hostElement, data);
 *   map.fit(); map.zoomBy(1.25); map.destroy();
 *
 * Requires a global `d3` (v7) for zoom/pan only. Everything else is plain DOM.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ *
   * Constants
   * ------------------------------------------------------------------ */

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var XLINK_NS = 'http://www.w3.org/1999/xlink';

  var FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

  // Canvas font strings (used for measuring) — must match the CSS exactly.
  var FONTS = [
    '700 18px ' + FONT_FAMILY, // depth 0 — root
    '600 15px ' + FONT_FAMILY, // depth 1 — branch
    '400 14px ' + FONT_FAMILY, // depth 2 — node
    '400 13px ' + FONT_FAMILY  // depth 3 — concept
  ];
  var FONT_META = '400 11px ' + FONT_FAMILY;
  var TEXT_SIZE = [18, 15, 14, 13];

  var ROW_HEIGHT = [0, 28, 20, 18];  // indexed by depth
  var LEVEL_GAP = [0, 48, 40, 32];   // horizontal gap from parent's outer end

  var BRANCH_GAP = 12;   // vertical gap between two branches on the same side
  var META_GAP = 6;      // px between title and meta text
  var ROOT_PAD_X = 32;   // root box = title width + this
  var ROOT_HEIGHT = 40;
  var ROOT_RADIUS = 10;
  var LABEL_RISE = 5;    // text baseline sits this far above the underline
  var OUTER_PAD = 8;     // extra underline past the label, where the toggle sits

  var FIT_PADDING = 20;
  var MAX_FIT_SCALE = 1.6;
  var MIN_SCALE = 0.15;
  var MAX_SCALE = 4;
  var ZOOM_STEP = 1.25;
  var TWO_SIDED_RATIO = 1.15;
  var RESIZE_DEBOUNCE = 150;
  var DRAG_SLOP = 4;

  var PALETTE = [
    '#3b82c4', '#e8833a', '#cf4f4f', '#2aa198', '#5aa846', '#c9a227',
    '#a66bbe', '#e377a2', '#a0785a', '#6f8fa6', '#7b61ff'
  ];

  /* ------------------------------------------------------------------ *
   * Small helpers
   * ------------------------------------------------------------------ */

  function svgEl(name, attrs) {
    var el = document.createElementNS(SVG_NS, name);
    if (attrs) {
      for (var key in attrs) {
        if (Object.prototype.hasOwnProperty.call(attrs, key) && attrs[key] != null) {
          el.setAttribute(key, attrs[key]);
        }
      }
    }
    return el;
  }

  // Round to 2 decimals so the emitted markup stays tidy.
  function fmt(n) {
    return Math.round(n * 100) / 100;
  }

  function paletteFor(index) {
    return PALETTE[((index % PALETTE.length) + PALETTE.length) % PALETTE.length];
  }

  /* ------------------------------------------------------------------ *
   * mount()
   * ------------------------------------------------------------------ */

  function mount(host, data) {
    data = data || {};
    var branches = data.branches || [];

    /* ---- measurement (canvas 2D, same fonts as the SVG text) -------- */

    var measureCtx = document.createElement('canvas').getContext('2d');

    function measure(text, font) {
      measureCtx.font = font;
      return measureCtx.measureText(text).width;
    }

    /* ---- expansion state -------------------------------------------- */

    var state = {
      branch: branches.map(function () { return true; }),
      node: branches.map(function (b) {
        return (b.nodes || []).map(function () { return false; });
      })
    };

    /* ---- view state -------------------------------------------------- */

    var mode = 'two';       // 'two' | 'one'
    var splitK = 0;         // branches on the left side (two-sided mode)
    var layout = null;      // { root, order, byId, bbox }
    var userMoved = false;  // user zoomed/panned since the last fit
    var pendingFit = false; // host had no size at mount
    var programmatic = false; // suppress userMoved while we set the transform
    var suppressClick = false; // a drag happened; swallow the trailing click
    var resizeTimer = 0;

    /* ---- DOM skeleton ------------------------------------------------ */

    host.classList.add('pm-host');
    host.textContent = '';

    var svg = svgEl('svg', { 'class': 'pm-svg' });
    var viewG = svgEl('g', { 'class': 'pm-view' });
    viewG.setAttribute('transform', 'translate(0,0) scale(1)');
    svg.appendChild(viewG);

    var toolbar = document.createElement('div');
    toolbar.className = 'pm-toolbar';

    var btnOut = makeButton('\u2212', 'Zoom out');
    var btnIn = makeButton('+', 'Zoom in');
    var btnFit = makeButton('Fit', 'Fit map to window');
    toolbar.appendChild(btnOut);
    toolbar.appendChild(btnIn);
    toolbar.appendChild(btnFit);

    host.appendChild(svg);
    host.appendChild(toolbar);

    function makeButton(label, aria) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.setAttribute('aria-label', aria);
      b.title = aria;
      return b;
    }

    /* ---- zoom / pan (d3) --------------------------------------------- */

    var svgSelection = d3.select(svg);

    var zoomBehaviour = d3.zoom()
      .scaleExtent([MIN_SCALE, MAX_SCALE])
      .on('start', function () { svg.classList.add('pm-dragging'); })
      .on('zoom', function (event) {
        var t = event.transform;
        viewG.setAttribute('transform',
          'translate(' + t.x + ',' + t.y + ') scale(' + t.k + ')');
        if (!programmatic) userMoved = true;
      })
      .on('end', function () { svg.classList.remove('pm-dragging'); });

    svgSelection.call(zoomBehaviour);
    svgSelection.on('dblclick.zoom', null); // double-click zoom disabled

    function applyTransform(t) {
      programmatic = true;
      try {
        svgSelection.call(zoomBehaviour.transform, t);
      } finally {
        programmatic = false;
      }
    }

    /* ---- tree construction (visible nodes only) ---------------------- */

    function buildTree() {
      var rootTitle = data.title || 'Physics Map';
      var root = {
        id: 'root', depth: 0, side: 'center', parent: null,
        title: rootTitle, meta: null, metaKind: null, url: null,
        linkTitle: false, linkMeta: false, children: [], hasToggle: false,
        expanded: true, open: false,
        width: measure(rootTitle, FONTS[0]) + ROOT_PAD_X
      };

      for (var bi = 0; bi < branches.length; bi++) {
        var b = branches[bi] || {};
        var bNode = {
          id: 'b' + bi,
          depth: 1,
          branchIndex: bi,
          side: 'right',
          parent: null,
          title: b.title || '',
          meta: b.span || null,
          metaKind: b.span ? 'span' : null,
          url: b.url || null,
          linkTitle: !!b.url,
          linkMeta: false,
          open: false,
          expanded: !!state.branch[bi],
          children: [],
          hasToggle: (b.nodes || []).length > 0
        };
        measureNode(bNode, 1);

        if (bNode.expanded) {
          var nodeList = b.nodes || [];
          for (var ni = 0; ni < nodeList.length; ni++) {
            var n = nodeList[ni] || {};
            var nNode = {
              id: 'b' + bi + '-n' + ni,
              depth: 2,
              branchIndex: bi,
              nodeIndex: ni,
              side: 'right',
              parent: null,
              title: n.title || '',
              meta: n.open ? 'open' : null,
              metaKind: n.open ? 'open' : null,
              url: n.url || null,
              linkTitle: !!n.url,
              linkMeta: false,
              open: !!n.open,
              when: n.when || '',
              expanded: !!state.node[bi][ni],
              children: [],
              hasToggle: (n.concepts || []).length > 0
            };
            measureNode(nNode, 2);

            if (nNode.expanded) {
              var concepts = n.concepts || [];
              for (var ci = 0; ci < concepts.length; ci++) {
                var c = concepts[ci] || {};
                var cNode = {
                  id: 'b' + bi + '-n' + ni + '-c' + ci,
                  depth: 3,
                  branchIndex: bi,
                  side: 'right',
                  parent: null,
                  title: c.title || '',
                  meta: c.explainer ? 'explainer' : null,
                  metaKind: c.explainer ? 'explainer' : null,
                  url: c.explainer || null,
                  linkTitle: false,
                  linkMeta: !!c.explainer,
                  open: false,
                  expanded: false,
                  children: [],
                  hasToggle: false
                };
                measureNode(cNode, 3);
                nNode.children.push(cNode);
              }
            }
            bNode.children.push(nNode);
          }
        }
        root.children.push(bNode);
      }
      return root;
    }

    function measureNode(ln, depth) {
      ln.titleW = measure(ln.title, FONTS[depth]);
      ln.metaW = ln.meta ? measure(ln.meta, FONT_META) : 0;
      ln.labelWidth = ln.titleW + (ln.meta ? META_GAP + ln.metaW : 0);
    }

    /* ---- layout ------------------------------------------------------ */

    // Height in rows: leaves take one row, parents stack their children.
    function assignRows(ln, top) {
      if (ln.children.length === 0) {
        ln.h = ROW_HEIGHT[ln.depth];
        ln.y = top + ln.h / 2;
        return ln.h;
      }
      var cur = top;
      for (var i = 0; i < ln.children.length; i++) {
        cur += assignRows(ln.children[i], cur);
      }
      ln.h = cur - top;
      ln.y = (ln.children[0].y + ln.children[ln.children.length - 1].y) / 2;
      return ln.h;
    }

    function shiftSubtree(ln, dy) {
      ln.y += dy;
      for (var i = 0; i < ln.children.length; i++) shiftSubtree(ln.children[i], dy);
    }

    // Stack one side's branches, then centre the side on y = 0.
    function layoutSide(list) {
      var cur = 0;
      for (var i = 0; i < list.length; i++) {
        cur += assignRows(list[i], cur);
        if (i < list.length - 1) cur += BRANCH_GAP;
      }
      var shift = cur / 2;
      for (var j = 0; j < list.length; j++) shiftSubtree(list[j], -shift);
    }

    function assignX(ln, parentOuter, dir, parent) {
      ln.inner = parentOuter + LEVEL_GAP[ln.depth];
      ln.side = dir < 0 ? 'left' : 'right'; // children inherit their branch's side
      ln.x = dir * ln.inner;
      ln.parent = parent;
      ln.attachX = dir * parentOuter;
      ln.attachY = parent.y;
      var nextOuter = ln.inner + ln.labelWidth + OUTER_PAD;
      for (var i = 0; i < ln.children.length; i++) {
        assignX(ln.children[i], nextOuter, dir, ln);
      }
    }

    function collect(ln, out) {
      out.push(ln);
      for (var i = 0; i < ln.children.length; i++) collect(ln.children[i], out);
    }

    function boundsOf(order) {
      var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      function add(x0, y0, x1, y1) {
        if (x0 < minX) minX = x0;
        if (y0 < minY) minY = y0;
        if (x1 > maxX) maxX = x1;
        if (y1 > maxY) maxY = y1;
      }
      for (var i = 0; i < order.length; i++) {
        var ln = order[i];
        if (ln.depth === 0) {
          add(-ln.width / 2, -ROOT_HEIGHT / 2, ln.width / 2, ROOT_HEIGHT / 2);
          continue;
        }
        var dir = ln.side === 'left' ? -1 : 1;
        var outerX = ln.x + dir * (ln.labelWidth + OUTER_PAD);
        var pad = 6; // covers the 5px toggle circle
        add(
          Math.min(ln.x, outerX) - pad,
          ln.y - LABEL_RISE - TEXT_SIZE[ln.depth] * 0.8 - 2,
          Math.max(ln.x, outerX) + pad,
          ln.y + 6
        );
      }
      return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
    }

    function labelBoundsOf(ln) {
      var dir = ln.side === 'left' ? -1 : 1;
      var x0 = ln.x;
      var x1 = ln.x + dir * ln.labelWidth;
      var top = ln.y - LABEL_RISE - TEXT_SIZE[ln.depth] * 0.8 - 2;
      return {
        minX: Math.min(x0, x1),
        maxX: Math.max(x0, x1),
        minY: top,
        maxY: ln.y + 6
      };
    }

    function unionBoundsOf(list) {
      var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (var i = 0; i < list.length; i++) {
        var b = labelBoundsOf(list[i]);
        if (b.minX < minX) minX = b.minX;
        if (b.minY < minY) minY = b.minY;
        if (b.maxX > maxX) maxX = b.maxX;
        if (b.maxY > maxY) maxY = b.maxY;
      }
      return { minX: minX, minY: minY, maxX: maxX, maxY: maxY };
    }

    // Smallest pan (in screen px) for one axis. The focus interval must stay
    // fully visible; if the whole group cannot fit, cover as much as possible
    // without pushing the focus out.
    function axisPan(gMin, gMax, fMin, fMax, size, pad) {
      var lo = pad;
      var hi = size - pad;
      var focusLo = lo - fMin;
      var focusHi = hi - fMax;

      if (focusLo > focusHi) {
        return (lo + hi) / 2 - (fMin + fMax) / 2;
      }

      if (gMax - gMin <= hi - lo) {
        var d = 0;
        if (gMin < lo) d = lo - gMin;
        else if (gMax > hi) d = hi - gMax;
        return Math.max(focusLo, Math.min(focusHi, d));
      }

      // Group is bigger than the viewport. Any d in [coverLo, coverHi]
      // makes the group cover the full padded viewport.
      var coverLo = hi - gMax;
      var coverHi = lo - gMin;
      var a = Math.max(focusLo, coverLo);
      var b = Math.min(focusHi, coverHi);
      if (a <= b) {
        if (a > 0) return a;
        if (b < 0) return b;
        return 0;
      }
      if (focusHi < coverLo) return focusHi;
      if (focusLo > coverHi) return focusLo;
      return Math.max(focusLo, Math.min(focusHi, 0));
    }

    function panExpandedIntoView(id) {
      var ln = layout && layout.byId[id];
      if (!ln) return;

      var rect = host.getBoundingClientRect();
      var W = rect.width;
      var H = rect.height;
      if (!W || !H) return;

      var t = d3.zoomTransform(svg);
      var group = [ln].concat(ln.children);
      var gb = unionBoundsOf(group);
      var fb = labelBoundsOf(ln);
      var pad = 16;

      var dx = axisPan(
        t.k * gb.minX + t.x, t.k * gb.maxX + t.x,
        t.k * fb.minX + t.x, t.k * fb.maxX + t.x,
        W, pad
      );
      var dy = axisPan(
        t.k * gb.minY + t.y, t.k * gb.maxY + t.y,
        t.k * fb.minY + t.y, t.k * fb.maxY + t.y,
        H, pad
      );
      if (!dx && !dy) return;

      applyTransform(d3.zoomIdentity
        .translate(t.x + dx, t.y + dy)
        .scale(t.k));
    }

    function computeLayout() {
      var root = buildTree();
      var list = root.children;
      var k = (mode === 'two') ? splitK : 0;
      k = Math.max(0, Math.min(list.length, k));

      var left = [], right = [];
      for (var i = 0; i < list.length; i++) {
        if (i < k) { list[i].side = 'left'; left.push(list[i]); }
        else { list[i].side = 'right'; right.push(list[i]); }
      }

      layoutSide(left);
      layoutSide(right);

      root.side = 'center';
      root.x = 0;
      root.y = 0;
      root.parent = null;

      for (var j = 0; j < list.length; j++) {
        assignX(list[j], root.width / 2, list[j].side === 'left' ? -1 : 1, root);
      }

      var order = [];
      collect(root, order);

      var byId = {};
      for (var m = 0; m < order.length; m++) byId[order[m].id] = order[m];

      return { root: root, order: order, byId: byId, bbox: boundsOf(order) };
    }

    // Best split of branches for the *initial* state (branches open, nodes shut).
    function computeSplit() {
      var n = branches.length;
      var heights = branches.map(function (b) {
        var count = (b.nodes || []).length;
        return count ? count * ROW_HEIGHT[2] : ROW_HEIGHT[1];
      });
      var best = 0;
      var bestDiff = Infinity;
      for (var k = 0; k <= n; k++) {
        var l = 0, r = 0, i;
        for (i = 0; i < k; i++) l += heights[i];
        if (k > 0) l += BRANCH_GAP * (k - 1);
        for (i = k; i < n; i++) r += heights[i];
        if (n - k > 0) r += BRANCH_GAP * (n - k - 1);
        var diff = Math.abs(l - r);
        if (diff < bestDiff) { bestDiff = diff; best = k; }
      }
      return best;
    }

    /* ---- rendering ---------------------------------------------------- */

    function render() {
      layout = computeLayout();

      while (viewG.firstChild) viewG.removeChild(viewG.firstChild);

      var linksG = svgEl('g', { 'class': 'pm-links' });
      var nodesG = svgEl('g', { 'class': 'pm-nodes' });
      viewG.appendChild(linksG);
      viewG.appendChild(nodesG);

      var order = layout.order;
      for (var i = 0; i < order.length; i++) {
        var ln = order[i];
        if (ln.parent) linksG.appendChild(renderLink(ln));
        nodesG.appendChild(renderNode(ln));
      }
    }

    function renderLink(ln) {
      var mx = (ln.attachX + ln.x) / 2;
      var d = 'M' + fmt(ln.attachX) + ',' + fmt(ln.attachY) +
              ' C' + fmt(mx) + ',' + fmt(ln.attachY) +
              ' ' + fmt(mx) + ',' + fmt(ln.y) +
              ' ' + fmt(ln.x) + ',' + fmt(ln.y);
      var p = svgEl('path', {
        'class': 'pm-link',
        'data-depth': String(ln.depth),
        d: d
      });
      p.style.setProperty('--pm-c', paletteFor(ln.branchIndex));
      return p;
    }

    function renderNode(ln) {
      var dir = ln.side === 'left' ? -1 : 1;
      var g = svgEl('g', {
        'class': 'pm-node',
        'data-depth': String(ln.depth),
        'data-side': ln.side,
        'data-id': ln.id,
        transform: 'translate(' + fmt(ln.x) + ',' + fmt(ln.y) + ')'
      });

      // --- root: rounded box, plain text -------------------------------
      if (ln.depth === 0) {
        g.appendChild(svgEl('rect', {
          'class': 'pm-root-box',
          x: fmt(-ln.width / 2),
          y: fmt(-ROOT_HEIGHT / 2),
          width: fmt(ln.width),
          height: fmt(ROOT_HEIGHT),
          rx: ROOT_RADIUS,
          ry: ROOT_RADIUS
        }));
        var rootText = svgEl('text', {
          'class': 'pm-label',
          x: 0, y: 0,
          'text-anchor': 'middle',
          dy: '0.35em'
        });
        rootText.appendChild(titleSpan(ln));
        g.appendChild(rootText);
        return g;
      }

      // --- every other node: underline + label (+ toggle) --------------
      g.style.setProperty('--pm-c', paletteFor(ln.branchIndex));

      var outer = ln.labelWidth + OUTER_PAD;

      var tip = tooltipFor(ln);
      if (tip) {
        var titleNode = svgEl('title');
        titleNode.textContent = tip;
        g.appendChild(titleNode);
      }

      g.appendChild(svgEl('path', {
        'class': 'pm-underline',
        d: 'M0,0 L' + fmt(dir * outer) + ',0'
      }));

      var text = svgEl('text', {
        'class': 'pm-label',
        x: 0,
        y: -LABEL_RISE,
        'text-anchor': dir < 0 ? 'end' : 'start'
      });
      text.appendChild(titleSpan(ln));
      if (ln.meta) text.appendChild(metaSpan(ln));
      g.appendChild(text);

      if (ln.hasToggle) g.appendChild(toggleEl(ln, dir * outer));

      return g;
    }

    function titleSpan(ln) {
      var tspan = svgEl('tspan', { 'class': 'pm-title' });
      tspan.textContent = ln.title;
      if (ln.linkTitle && ln.url) {
        var a = anchorEl(ln.url);
        a.appendChild(tspan);
        return a;
      }
      return tspan;
    }

    function metaSpan(ln) {
      var cls = 'pm-meta';
      if (ln.metaKind === 'open') cls += ' pm-meta-open';
      if (ln.metaKind === 'explainer') cls += ' pm-meta-explainer';
      var tspan = svgEl('tspan', { 'class': cls, dx: META_GAP });
      tspan.textContent = ln.meta;
      if (ln.linkMeta && ln.url) {
        var a = anchorEl(ln.url);
        a.appendChild(tspan);
        return a;
      }
      return tspan;
    }

    function anchorEl(href) {
      var a = svgEl('a', { href: href, target: '_blank', rel: 'noopener' });
      a.setAttributeNS(XLINK_NS, 'xlink:href', href); // older engines
      a.addEventListener('click', onLinkClick);
      return a;
    }

    function onLinkClick(event) {
      if (suppressClick) {
        event.preventDefault();
        event.stopPropagation();
        suppressClick = false;
      }
    }

    function tooltipFor(ln) {
      if (ln.depth === 1) {
        return ln.title + (ln.meta ? ' \u00b7 ' + ln.meta : '');
      }
      if (ln.depth === 2) {
        return ln.title +
          (ln.when ? ' \u00b7 ' + ln.when : '') +
          (ln.open ? ' \u00b7 open question' : '');
      }
      return ln.title;
    }

    function toggleEl(ln, x) {
      var g = svgEl('g', {
        'class': 'pm-toggle' + (ln.expanded ? ' is-open' : ''),
        role: 'button',
        tabindex: '0',
        'aria-expanded': ln.expanded ? 'true' : 'false',
        'aria-label': (ln.expanded ? 'Collapse ' : 'Expand ') + ln.title,
        transform: 'translate(' + fmt(x) + ',0)'
      });
      g.appendChild(svgEl('circle', { 'class': 'pm-toggle-hit', r: 11 }));
      g.appendChild(svgEl('circle', { 'class': 'pm-toggle-dot', r: 5 }));

      g.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        toggleNode(ln.id);
      });
      g.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
          event.preventDefault();
          event.stopPropagation();
          toggleNode(ln.id);
        }
      });
      return g;
    }

    /* ---- expand / collapse -------------------------------------------- */

    function toggleNode(id) {
      var ln = layout && layout.byId[id];
      if (!ln) return;

      var oldX = ln.x;
      var oldY = ln.y;

      var expanding;
      if (ln.depth === 1) {
        expanding = !state.branch[ln.branchIndex];
        state.branch[ln.branchIndex] = !state.branch[ln.branchIndex];
      } else if (ln.depth === 2) {
        var arr = state.node[ln.branchIndex];
        expanding = !arr[ln.nodeIndex];
        arr[ln.nodeIndex] = !arr[ln.nodeIndex];
      } else {
        return;
      }

      render();

      // Keep the toggled node pinned to its screen position.
      var moved = layout.byId[id];
      if (moved) {
        var t = d3.zoomTransform(svg);
        applyTransform(d3.zoomIdentity
          .translate(t.x + t.k * (oldX - moved.x), t.y + t.k * (oldY - moved.y))
          .scale(t.k));
      }

      if (expanding) panExpandedIntoView(id);

      var focusTarget = svg.querySelector(
        '.pm-node[data-id="' + id + '"] .pm-toggle'
      );
      if (focusTarget && focusTarget.focus) {
        try { focusTarget.focus({ preventScroll: true }); } catch (e) { /* older browsers */ }
      }
    }

    /* ---- fit / zoom ---------------------------------------------------- */

    function fit() {
      if (!layout) return;
      var rect = host.getBoundingClientRect();
      var W = rect.width;
      var H = rect.height;
      if (!W || !H) return;

      var bb = layout.bbox;
      var bw = Math.max(1, bb.maxX - bb.minX);
      var bh = Math.max(1, bb.maxY - bb.minY);

      var s = Math.min(
        (W - 2 * FIT_PADDING) / bw,
        (H - 2 * FIT_PADDING) / bh,
        MAX_FIT_SCALE
      );
      s = Math.max(MIN_SCALE, Math.min(MAX_SCALE, s));

      var cx = (bb.minX + bb.maxX) / 2;
      var cy = (bb.minY + bb.maxY) / 2;

      applyTransform(d3.zoomIdentity
        .translate(W / 2 - s * cx, H / 2 - s * cy)
        .scale(s));
      userMoved = false;
    }

    function zoomBy(factor) {
      var rect = host.getBoundingClientRect();
      var W = rect.width;
      var H = rect.height;
      if (!W || !H) return;

      var t = d3.zoomTransform(svg);
      var k = Math.max(MIN_SCALE, Math.min(MAX_SCALE, t.k * factor));
      var ratio = k / t.k;

      // Scale about the centre of the view.
      var cx = W / 2;
      var cy = H / 2;
      var tx = cx - ratio * (cx - t.x);
      var ty = cy - ratio * (cy - t.y);

      applyTransform(d3.zoomIdentity.translate(tx, ty).scale(k));
      userMoved = true;
    }

    /* ---- drag-vs-click discrimination for links ------------------------ */

    var pointerDown = null;

    function onPointerDown(event) {
      pointerDown = { x: event.clientX, y: event.clientY };
      suppressClick = false;
    }

    function onPointerMove(event) {
      if (!pointerDown) return;
      if (Math.abs(event.clientX - pointerDown.x) > DRAG_SLOP ||
          Math.abs(event.clientY - pointerDown.y) > DRAG_SLOP) {
        suppressClick = true;
      }
    }

    function onPointerUp() {
      pointerDown = null;
    }

    svg.addEventListener('pointerdown', onPointerDown);
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);

    /* ---- toolbar ------------------------------------------------------- */

    btnOut.addEventListener('click', function () { zoomBy(1 / ZOOM_STEP); });
    btnIn.addEventListener('click', function () { zoomBy(ZOOM_STEP); });
    btnFit.addEventListener('click', function () { fit(); });

    /* ---- resize handling ------------------------------------------------ */

    function currentMode() {
      var w = host.clientWidth;
      var h = host.clientHeight;
      if (!w || !h) return mode;
      return (w / h >= TWO_SIDED_RATIO) ? 'two' : 'one';
    }

    function handleResize() {
      var w = host.clientWidth;
      var h = host.clientHeight;
      if (!w || !h) return;

      var next = (w / h >= TWO_SIDED_RATIO) ? 'two' : 'one';
      var flipped = next !== mode;

      if (flipped) {
        mode = next;
        if (mode === 'two') splitK = computeSplit();
      }

      if (flipped || pendingFit) {
        pendingFit = false;
        render();
        fit();
      } else if (!userMoved) {
        fit();
      }
    }

    var observer = new ResizeObserver(function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(handleResize, RESIZE_DEBOUNCE);
    });
    observer.observe(host);

    /* ---- initial paint --------------------------------------------------- */

    mode = currentMode();
    splitK = computeSplit();
    render();

    if (host.clientWidth && host.clientHeight) {
      fit();
    } else {
      pendingFit = true; // wait for the first real resize
    }

    /* ---- public API ------------------------------------------------------ */

    function destroy() {
      clearTimeout(resizeTimer);
      if (observer) observer.disconnect();
      svg.removeEventListener('pointerdown', onPointerDown);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      svgSelection.on('.zoom', null);
      host.classList.remove('pm-host');
      while (host.firstChild) host.removeChild(host.firstChild);
      layout = null;
    }

    return { fit: fit, zoomBy: zoomBy, destroy: destroy };
  }

  window.PhysicsMap = { mount: mount };
})();
