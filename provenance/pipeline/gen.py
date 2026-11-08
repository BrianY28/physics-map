#!/usr/bin/env python3
"""Generate a physics mind map (Newton -> frontier) with DeepSeek V4.1 Flash via the local Ollama server.

Usage:
  gen.py skeleton                 # phase 1: top-level branches -> skeleton.json
  gen.py expand [branch_id ...]   # phase 2: expand branches -> branches/<id>.json
  gen.py revise <branch_id> <feedback.txt>   # send review feedback, rewrite one branch
  gen.py check                    # run automatic checks on everything generated
  gen.py opml                     # build the OPML file for MindNode
Every model call is logged to log.jsonl; thinking text goes to thinking/.
"""
import json, re, sys, time, urllib.request, concurrent.futures as cf
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLLAMA = "http://localhost:11434/api/chat"
MODEL = "deepseek-v4.1-flash:cloud"
THINK = "high"
LOG = HERE / "log.jsonl"
(HERE / "branches").mkdir(exist_ok=True)
(HERE / "thinking").mkdir(exist_ok=True)

SYSTEM = (
    "You are a physics historian and working physicist building a mind map of physics, "
    "from Newton's Principia (1687) to the research frontier as of November 2026. "
    "Be factually precise: correct names, years and equations. Use the canonical attribution and the "
    "year of first publication or discovery. If you are not sure of an exact year, give the decade "
    "(for example '1920s') instead of guessing. Node titles must be short (at most 6 words). "
    "Notes are 1-2 plain sentences. Write equations in plain Unicode (for example F = ma, E = mc², iħ∂ψ/∂t = Ĥψ), not LaTeX. "
    "Answer only by calling the provided tool exactly once."
)

SKELETON_SCHEMA = {
    "type": "object",
    "properties": {
        "root_title": {"type": "string"},
        "branches": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string", "description": "short lowercase slug"},
            "title": {"type": "string"},
            "span": {"type": "string", "description": "period when the field took shape, e.g. 1687-1850"},
            "summary": {"type": "string", "description": "one sentence"},
            "subtopics": {"type": "array", "items": {"type": "string"}, "description": "4-7 subtopic titles"},
        }, "required": ["id", "title", "span", "summary", "subtopics"]}},
    },
    "required": ["root_title", "branches"],
}

BRANCH_SCHEMA = {
    "type": "object",
    "properties": {
        "subtopics": {"type": "array", "items": {"type": "object", "properties": {
            "title": {"type": "string"},
            "when": {"type": "string", "description": "year, span or decade"},
            "people": {"type": "array", "items": {"type": "string"}},
            "note": {"type": "string", "description": "1-2 sentences; key idea and, if a classic one exists, the key equation"},
            "concepts": {"type": "array", "items": {"type": "object", "properties": {
                "title": {"type": "string"},
                "note": {"type": "string", "description": "one sentence"},
            }, "required": ["title", "note"]}, "description": "2-4 key concepts, results or experiments"},
        }, "required": ["title", "when", "people", "note", "concepts"]}},
    },
    "required": ["subtopics"],
}


def log(entry):
    with LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def ask(tag, user_msg, schema, history=None, tries=3):
    """One structured call. Returns the tool arguments dict. Retries on missing/invalid output."""
    tools = [{"type": "function", "function": {"name": "submit", "description": "Submit the result", "parameters": schema}}]
    msgs = [{"role": "system", "content": SYSTEM}] + (history or []) + [{"role": "user", "content": user_msg}]
    for attempt in range(1, tries + 1):
        body = {"model": MODEL, "stream": False, "think": THINK, "tools": tools, "messages": msgs,
                "options": {"temperature": 0.4}}
        t0 = time.time()
        entry = {"tag": tag, "attempt": attempt, "ts": time.strftime("%H:%M:%S")}
        try:
            req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=600))
            m = d["message"]
            entry.update(secs=round(time.time() - t0, 1), prompt_tokens=d.get("prompt_eval_count"),
                         out_tokens=d.get("eval_count"), thinking_chars=len(m.get("thinking") or ""))
            (HERE / "thinking" / f"{tag}.a{attempt}.txt").write_text(m.get("thinking") or "")
            args = None
            if m.get("tool_calls"):
                args = m["tool_calls"][0]["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                entry["via"] = "tool_call"
            else:  # fallback: JSON in the content
                c = re.sub(r"^```(?:json)?|```$", "", (m.get("content") or "").strip(), flags=re.M)
                args = json.loads(c)
                entry["via"] = "content_json"
            missing = [k for k in schema["required"] if k not in args]
            if missing:
                raise ValueError(f"missing keys {missing}")
            entry["ok"] = True
            log(entry)
            return args
        except Exception as e:
            entry.update(ok=False, error=f"{type(e).__name__}: {e}"[:300], secs=round(time.time() - t0, 1))
            log(entry)
            print(f"  [{tag}] attempt {attempt} failed: {entry['error']}", flush=True)
    raise RuntimeError(f"{tag}: all {tries} attempts failed")


def cmd_skeleton():
    msg = (
        "Design the top level of the mind map. Give 9-11 major branches, ordered roughly by when each field "
        "took shape, starting with Newtonian mechanics and ending with one branch for the open frontier "
        "(unsolved problems and active research programmes as of 2026). The map must cover the whole present-day "
        "discipline, not only its history. For each branch give 4-7 subtopics, ordered from oldest to newest. "
        "Subtopics must not repeat across branches."
    )
    out = ask("skeleton", msg, SKELETON_SCHEMA)
    (HERE / "skeleton.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))


def branch_prompt(b, sk):
    others = [x["title"] for x in sk["branches"] if x["id"] != b["id"]]
    frontier = b is sk["branches"][-1]
    msg = (
        f"Expand the branch '{b['title']}' ({b['span']}): {b['summary']}\n"
        f"Use exactly these subtopics, in this order (keep the count; drop the year from each title, it belongs in 'when'):{json.dumps(b['subtopics'], ensure_ascii=False)}.\n"
        "For each subtopic give: when, the key people, a 1-2 sentence note with the core idea (and the key equation if a "
        "classic one exists), and 2-4 concepts (key results, laws, experiments or open questions) with one-sentence notes.\n"
        f"Other branches of the map (do not duplicate their content): {json.dumps(others, ensure_ascii=False)}."
    )
    if frontier:
        msg += ("\nThis is the frontier branch. For each item, say what is known and unknown as of 2026, name the main "
                "experiments or approaches, and give the year of the most recent decisive result you are confident about. "
                "Do not invent results; if a status is uncertain, say so.")
    return msg


def cmd_expand(ids):
    sk = json.loads((HERE / "skeleton.json").read_text())
    todo = [b for b in sk["branches"] if not ids or b["id"] in ids]

    def run(b):
        out = ask(f"branch-{b['id']}", branch_prompt(b, sk), BRANCH_SCHEMA)
        (HERE / "branches" / f"{b['id']}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
        return b["id"], len(out["subtopics"])

    with cf.ThreadPoolExecutor(4) as ex:
        for fut in cf.as_completed([ex.submit(run, b) for b in todo]):
            try:
                bid, n = fut.result()
                print(f"  done {bid}: {n} subtopics", flush=True)
            except Exception as e:
                print(f"  FAILED: {e}", flush=True)


def cmd_revise(bid, feedback_path):
    sk = json.loads((HERE / "skeleton.json").read_text())
    b = next(x for x in sk["branches"] if x["id"] == bid)
    cur = (HERE / "branches" / f"{bid}.json").read_text()
    fb = Path(feedback_path).read_text()
    history = [{"role": "user", "content": branch_prompt(b, sk)},
               {"role": "assistant", "content": "Draft submitted:\n" + cur}]
    msg = ("A reviewer checked your draft and found these problems. Fix every one of them, keep everything else "
           "unchanged unless it is also wrong, and submit the full corrected branch.\n\n" + fb)
    out = ask(f"revise-{bid}", msg, BRANCH_SCHEMA, history=history)
    (HERE / "branches" / f"{bid}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))


def cmd_check():
    sk = json.loads((HERE / "skeleton.json").read_text())
    issues, seen, total = [], {}, 0
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    for b in sk["branches"]:
        p = HERE / "branches" / f"{b['id']}.json"
        if not p.exists():
            issues.append(f"{b['id']}: not generated"); continue
        data = json.loads(p.read_text())
        if len(data["subtopics"]) != len(b["subtopics"]):
            issues.append(f"{b['id']}: {len(data['subtopics'])} subtopics, skeleton had {len(b['subtopics'])}")
        for s in data["subtopics"]:
            total += 1 + len(s.get("concepts", []))
            where = f"{b['id']} / {s['title']}"
            if len(s["title"].split()) > 7: issues.append(f"{where}: title too long")
            if re.search(r"\(\d", s["title"]): issues.append(f"{where}: year left in title")
            frontier = b is sk["branches"][-1]
            max_c, max_year = (5, 2045) if frontier else (4, 2026)  # frontier may cite planned dates
            if not 2 <= len(s.get("concepts", [])) <= max_c: issues.append(f"{where}: {len(s.get('concepts', []))} concepts")
            for y in map(int, re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", s["when"] + " " + s["note"])):
                if y > max_year or y < 1600: issues.append(f"{where}: suspicious year {y}")
            if "\\" in s["note"] or "$" in s["note"]: issues.append(f"{where}: LaTeX in note")
            for c in s.get("concepts", []):
                if len(c["title"].split()) > 7: issues.append(f"{where} / {c['title']}: concept title too long")
                k = norm(c["title"])
                if k in seen and seen[k] != b["id"]: issues.append(f"duplicate concept '{c['title']}' in {b['id']} and {seen[k]}")
                seen.setdefault(k, b["id"])
    print(f"branches: {len(sk['branches'])}, nodes: {total + len(sk['branches']) + 1}")
    print("\n".join(issues) if issues else "no automatic issues")


def cmd_opml():
    from xml.sax.saxutils import quoteattr
    sk = json.loads((HERE / "skeleton.json").read_text())
    root = sk.get("root_title") or "Physics: From Newton to the Frontier"
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<opml version="2.0">',
         f"  <head><title>{root}</title></head>", "  <body>",
         f"    <outline text={quoteattr(root)} _note={quoteattr('Generated by DeepSeek V4.1 Flash via Ollama, reviewed by Claude, ' + time.strftime('%Y-%m-%d'))}>"]
    for b in sk["branches"]:
        data = json.loads((HERE / "branches" / f"{b['id']}.json").read_text())
        L.append(f"      <outline text={quoteattr(b['title'])} _note={quoteattr(b['span'] + ' · ' + b['summary'])}>")
        for s in data["subtopics"]:
            meta = s["when"] + (" · " + ", ".join(s["people"]) if s["people"] else "")
            L.append(f"        <outline text={quoteattr(s['title'])} _note={quoteattr(meta + chr(10) + s['note'])}>")
            for c in s["concepts"]:
                L.append(f"          <outline text={quoteattr(c['title'])} _note={quoteattr(c['note'])}/>")
            L.append("        </outline>")
        L.append("      </outline>")
    L += ["    </outline>", "  </body>", "</opml>"]
    out = HERE / f"{root.replace(':', ' -').replace('/', '-')}.opml"
    out.write_text("\n".join(L) + "\n")
    print(out)


if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    {"skeleton": lambda: cmd_skeleton(), "expand": lambda: cmd_expand(sys.argv[2:]),
     "revise": lambda: cmd_revise(sys.argv[2], sys.argv[3]), "check": cmd_check, "opml": cmd_opml}.get(c, lambda: print(__doc__))()
