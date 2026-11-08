// Paste into the page (browser devtools or an automation tool) to audit a generated explainer.
// Reports layout overflow, canvas sizing, unlabeled controls and link targets. Read-only.
(() => {
  const out = {};
  const doc = document.documentElement;
  out.viewport = innerWidth;
  out.pageScrollWidth = doc.scrollWidth;
  out.horizontalOverflow = doc.scrollWidth > innerWidth + 1;
  out.overflowingElements = [...document.querySelectorAll("body *")]
    .filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1); })
    .slice(0, 8).map(el => `${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""}${el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : ""} right=${Math.round(el.getBoundingClientRect().right)}`);
  out.canvases = [...document.querySelectorAll("canvas")].map(c => ({
    id: c.id, cssW: Math.round(c.getBoundingClientRect().width), cssH: Math.round(c.getBoundingClientRect().height),
    pxW: c.width, pxH: c.height,
    blank: (() => { try { const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; for (let i = 3; i < d.length; i += 16) if (d[i]) return false; return true; } catch (e) { return "n/a"; } })(),
  }));
  out.controls = [...document.querySelectorAll("input,select,button,textarea")].map(el => ({
    tag: el.tagName.toLowerCase(), id: el.id, type: el.type,
    label: (el.labels && el.labels[0] && el.labels[0].textContent.trim().slice(0, 40)) || el.getAttribute("aria-label") || el.textContent.trim().slice(0, 40) || null,
  }));
  out.unlabeled = out.controls.filter(c => !c.label).map(c => c.id || c.tag);
  out.links = [...document.querySelectorAll("a[href]")].map(a => ({ text: a.textContent.trim().slice(0, 50), href: a.getAttribute("href"), target: a.target }));
  out.title = document.title;
  out.bodyBg = getComputedStyle(document.body).backgroundColor;
  out.fonts = [...new Set([...document.querySelectorAll("h1,h2,p,label,button")].map(el => getComputedStyle(el).fontFamily.split(",")[0]))];
  return out;
})();
