#!/usr/bin/env python3
"""DeepSeek writes an explainer page; this script logs each call and checks the result.

Usage (run from the repo folder):
  explain.py draft  <dir>                  # brief.md -> v1.html
  explain.py revise <dir> <feedback.txt>   # latest vN.html + feedback -> v(N+1).html
  explain.py check  <dir> [file]           # automatic checks on the latest (or given) version
  explain.py preview <dir>                 # wrap latest version in the publish skeleton -> preview.html
Calls go to deepseek-v4.1-flash:cloud through the local Ollama server; log in <dir>/log.jsonl.
"""
import json, re, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "deepseek-v4.1-flash:cloud"
SYSTEM = ("You are an expert physics educator and front-end developer. You write correct physics and clean, "
          "accessible, self-contained HTML, CSS and JavaScript. Follow the brief exactly. "
          "Plan briefly in your reasoning (structure, design choices, physics), then write the code directly in your "
          "answer. Do not draft the code inside your reasoning: the output budget is shared and a draft there "
          "leaves no room for the answer.")
ALLOWED_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "mindnode.com")
LINKS = ["https://mindnode.com/document/3hq16XnASSIHX4fAHcm4wA/node/2f9wEGkux499WIIdqz8F9g",
         "https://mindnode.com/document/3hq16XnASSIHX4fAHcm4wA"]


def versions(d):
    return sorted(d.glob("v*.html"), key=lambda p: int(p.stem[1:]))


def call(d, tag, messages):
    body = {"model": MODEL, "stream": False, "think": "high", "messages": messages,
            "options": {"temperature": 0.5, "num_predict": 98304}}
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    m = r["message"]
    entry = {"tag": tag, "ts": time.strftime("%H:%M:%S"), "secs": round(time.time() - t0, 1),
             "prompt_tokens": r.get("prompt_eval_count"), "out_tokens": r.get("eval_count"),
             "thinking_chars": len(m.get("thinking") or ""), "done_reason": r.get("done_reason")}
    (d / f"{tag}.thinking.txt").write_text(m.get("thinking") or "")
    (d / f"{tag}.raw.txt").write_text(m.get("content") or "")
    fence = re.search(r"```html\s*\n(.*?)```", m.get("content") or "", re.S)
    entry["extracted"] = bool(fence)
    with (d / "log.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry))
    if not fence:
        raise SystemExit("no ```html fence in the reply; see the .raw.txt file")
    return fence.group(1).strip() + "\n"


def draft(d):
    html = call(d, "v1", [{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": (d / "brief.md").read_text()}])
    (d / "v1.html").write_text(html)
    check(d)


def revise(d, fb_path):
    cur = versions(d)[-1]
    n = int(cur.stem[1:]) + 1
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": (d / "brief.md").read_text()},
            {"role": "assistant", "content": "```html\n" + cur.read_text() + "```"},
            {"role": "user", "content": "A reviewer tested your page and found these problems. Fix every one, keep "
             "everything else that works, and return the complete corrected file in ONE ```html fence.\n\n"
             + Path(fb_path).read_text()}]
    html = call(d, f"v{n}", msgs)
    (d / f"v{n}.html").write_text(html)
    check(d)


def check(d, path=None):
    p = Path(path) if path else versions(d)[-1]
    h = p.read_text()
    issues = []
    head = h[:8192]
    if re.search(r"<!doctype|<html[\s>]|<head[\s>]|<body[\s>]", h, re.I): issues.append("has doctype/html/head/body tags")
    if not re.search(r"<title>[^<]+</title>", head): issues.append("no <title> in first 8KB")
    if 'name="claude:viewport-fit-sides"' not in head: issues.append("missing viewport-fit-sides meta")
    if "max(16px, env(safe-area-inset-left" not in h or "max(16px, env(safe-area-inset-right" not in h:
        issues.append("missing max() side gutters")
    if "prefers-color-scheme: dark" not in h: issues.append("no prefers-color-scheme dark block")
    if ':root[data-theme="dark"]' not in h: issues.append('no :root[data-theme="dark"] block')
    if 'not([data-theme="light"])' not in h: issues.append('dark media block not guarded by :not([data-theme="light"])')
    if "prefers-reduced-motion" not in h: issues.append("no prefers-reduced-motion handling")
    for bad in ["alert(", "confirm(", "prompt(", "window.print", "localStorage"]:
        if bad in h: issues.append(f"uses {bad}")
    for host in set(re.findall(r'(?:src|href)="https?://([^/"]+)', h)):
        if not host.endswith(ALLOWED_HOSTS): issues.append(f"external host not allowed: {host}")
    if re.search(r"<script[^>]+src=", h): issues.append("loads an external script")
    for l in LINKS:
        if f'href="{l}"' not in h: issues.append(f"missing link {l}")
    if re.search(r"font-family:[^;]*\b(Inter|Space Grotesk)\b", h): issues.append("uses Inter or Space Grotesk")
    ids = re.findall(r'\bid="([^"]+)"', h)
    dup = {i for i in ids if ids.count(i) > 1}
    if dup: issues.append(f"duplicate ids: {sorted(dup)}")
    for ctl in re.findall(r"<(?:input|select|textarea)\b[^>]*>", h):
        if "id=" not in ctl: issues.append(f"form control without id: {ctl[:60]}")
    # literal colors outside custom-property definitions (rough check on CSS only)
    css = "\n".join(re.findall(r"<style>(.*?)</style>", h, re.S))
    lit = [ln.strip() for ln in css.splitlines() if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", ln) and not ln.strip().startswith("--")]
    if lit: issues.append(f"{len(lit)} CSS lines use literal colors outside tokens, e.g. {lit[0][:70]}")
    # JS syntax
    for i, js in enumerate(re.findall(r"<script>(.*?)</script>", h, re.S)):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(js)
        r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
        if r.returncode: issues.append(f"script {i} syntax error: {r.stderr.strip().splitlines()[-1][:120]}")
    print(f"{p.name}: {len(h):,} chars, {len(re.findall(r'<canvas', h))} canvases, {len(re.findall(r'<input', h))} inputs")
    print("\n".join("  - " + i for i in issues) if issues else "  no automatic issues")


def preview(d):
    cur = versions(d)[-1]
    skel = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, '
            'initial-scale=1, viewport-fit=cover"><style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);'
            'padding-bottom:env(safe-area-inset-bottom)}body{margin:0;font:14px system-ui}img{max-width:100%}'
            '[hidden]{display:none!important}</style></head><body>\n')
    (d / "preview.html").write_text(skel + cur.read_text() + "\n</body></html>\n")
    print(d / "preview.html", "<-", cur.name)


if __name__ == "__main__":
    cmd, d = sys.argv[1], Path(sys.argv[2])
    {"draft": lambda: draft(d), "revise": lambda: revise(d, sys.argv[3]),
     "check": lambda: check(d, sys.argv[3] if len(sys.argv) > 3 else None), "preview": lambda: preview(d)}[cmd]()
