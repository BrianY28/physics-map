#!/usr/bin/env python3
"""Drafting helper: asks DeepSeek V4.1 Flash (through a local Ollama server) to draft content.
Every draft is reviewed by a person (or another model) before it is merged.

Usage:
  python3 tools/draft/deepseek.py sources nodes/01-newtonian-mechanics   # -> provenance/sources-drafts/<dir>.json
  python3 tools/draft/deepseek.py write [--think=low|high] BRIEF.md [CONTEXT_FILE ...]   # drafts every path=FILE fence

Calls are logged to provenance/logs/deepseek.jsonl. Needs `ollama` running and signed in.
"""
import json, re, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import nodelib  # noqa: E402

ROOT = nodelib.ROOT
OLLAMA = "http://localhost:11434/api/chat"
MODEL = "deepseek-v4.1-flash:cloud"
LOGS = ROOT / "provenance" / "logs"
SYSTEM = ("You are a careful physicist, historian of science and technical writer. Be factually precise. "
          "Plan briefly in your reasoning, then write the answer directly; do not draft the answer inside your reasoning.")


def call(tag, messages, tools=None, think="high"):
    LOGS.mkdir(parents=True, exist_ok=True)
    body = {"model": MODEL, "stream": False, "think": think, "messages": messages,
            "options": {"temperature": 0.3, "num_predict": 131072}}
    if tools:
        body["tools"] = tools
    t0 = time.time()
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    m = r["message"]
    (LOGS / f"{tag}.thinking.txt").write_text(m.get("thinking") or "")
    entry = {"tag": tag, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "secs": round(time.time() - t0, 1),
             "out_tokens": r.get("eval_count"), "done_reason": r.get("done_reason"),
             "tool_call": bool(m.get("tool_calls"))}
    with (LOGS / "deepseek.jsonl").open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry), flush=True)
    return m


SOURCES_SCHEMA = {"type": "object", "properties": {"nodes": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "string"},
    "sources": {"type": "array", "items": {"type": "object", "properties": {
        "citation": {"type": "string", "description": "Author, A. & Author, B. (Year). Title. Journal or publisher, volume, pages."},
        "confidence": {"type": "string", "enum": ["high", "medium"]}}, "required": ["citation", "confidence"]}}},
    "required": ["id", "sources"]}}}, "required": ["nodes"]}


def sources(branch_dir):
    bdir = (ROOT / branch_dir).resolve()
    b = next(x for x in nodelib.load() if x["dir"] == bdir.name)
    nodes = [{"id": n["id"], "title": n["title"], "when": n["when"], "people": n.get("people", []),
              "status": n["status"], "note": n["note"], "concepts": [c["title"] for c in n["concepts"]]} for n in b["nodes"]]
    msg = (
        f"These are the nodes of the branch '{b['title']}' of an open, citable mind map of physics. "
        "For each node, give 1 to 3 sources a reader can use to check it.\n"
        "- Established topics: the original publication of the key result (paper or book), and optionally one standard "
        "textbook or review. Frontier (status open) topics: the key recent result papers or collaboration papers, and/or "
        "one well-known review.\n"
        "- Format each citation as: Author, A., & Author, B. (Year). Title. Journal or Publisher, volume, pages. "
        "Use 'et al.' after three authors. Use the original-language title for old works and add an English title in brackets if helpful.\n"
        "- Give only works you are certain exist, with the correct year and venue. Do NOT give URLs or DOIs. "
        "If unsure about volume or page numbers, leave them out rather than guess. Fewer correct sources beat more uncertain ones.\n"
        "- Mark confidence 'high' only when you are sure of author, year, title and venue; otherwise 'medium'.\n"
        "Answer by calling the submit tool once with every node id.\n\n" + json.dumps(nodes, ensure_ascii=False, indent=1))
    tools = [{"type": "function", "function": {"name": "submit", "description": "Submit sources", "parameters": SOURCES_SCHEMA}}]
    for attempt in range(3):
        m = call(f"sources-{bdir.name}", [{"role": "system", "content": SYSTEM}, {"role": "user", "content": msg}], tools)
        if m.get("tool_calls"):
            args = m["tool_calls"][0]["function"]["arguments"]
            args = json.loads(args) if isinstance(args, str) else args
            got = {n["id"] for n in args.get("nodes", [])}
            if got >= {n["id"] for n in nodes}:
                out = ROOT / "provenance" / "sources-drafts" / f"{bdir.name}.json"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(args, indent=1, ensure_ascii=False))
                print("wrote", out.relative_to(ROOT))
                return
            print(f"missing ids: {sorted({n['id'] for n in nodes} - got)}; retrying")
    raise SystemExit("no complete answer")


def write(brief, context_files, think="high"):
    parts = [Path(brief).read_text()]
    for c in context_files:
        parts.append(f"\n\n===== CONTEXT FILE: {c} =====\n" + (ROOT / c).read_text())
    parts.append("\n\nReturn each file in its own FOUR-backtick fence whose info string names it, for example\n"
                 "````markdown path=README.md\n...file content (may contain ordinary ``` code blocks)...\n````\n"
                 "Return nothing else.")
    tag = "write-" + Path(brief).stem
    m = call(tag, [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "".join(parts)}], think=think)
    content = m.get("content") or ""
    (LOGS / f"{tag}.raw.txt").write_text(content)
    files = re.findall(r"^````[a-zA-Z]*\s+path=(\S+)[ \t]*\n(.*?)\n````[ \t]*$", content, re.S | re.M)
    if not files:
        raise SystemExit(f"no path= fences found; see provenance/logs/{tag}.raw.txt")
    for path, text in files:
        dest = ROOT / "provenance" / "drafts" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text.rstrip() + "\n")
        print("drafted", dest.relative_to(ROOT))


if __name__ == "__main__":
    if sys.argv[1] == "sources":
        sources(sys.argv[2])
    elif sys.argv[1] == "write":
        # --think=low keeps long code answers out of the model's reasoning (which shares the output budget)
        flags = [a for a in sys.argv[2:] if a.startswith("--think=")]
        rest = [a for a in sys.argv[2:] if not a.startswith("--think=")]
        write(rest[0], rest[1:], think=flags[0].split("=", 1)[1] if flags else "high")
    else:
        print(__doc__)
