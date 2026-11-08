"""Read, validate and write node files. Standard library only.

A node file is Markdown with a small front-matter block:

    ---
    order: 10
    when: "1687"
    people:
      - Isaac Newton
    status: established        # established | open
    as_of: 2026-11-08          # required when status is open
    sources:
      - "Newton, I. (1687). Philosophiae Naturalis Principia Mathematica. London."
    drafted_by: DeepSeek V4.1 Flash
    reviewed_by:
      - Claude (AI)
    ---

    # Newton's laws

    One or two sentences: the core idea.

    ## Concepts

    - **First law: inertia**: One sentence. [Explainer](../../explainers/first-law/)

The front matter accepts only: `key: value`, `key:` followed by `  - item` lines, and
`# comments`. Values are bare words or "double-quoted strings".
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "nodes"

FIELDS = {"order", "when", "people", "status", "as_of", "sources", "drafted_by", "reviewed_by"}
LIST_FIELDS = {"people", "sources", "reviewed_by"}
BRANCH_FIELDS = {"span"}
CONCEPT_RE = re.compile(r"^- \*\*(?P<title>.+?)\*\*: (?P<note>.+?)(?: \[Explainer\]\((?P<explainer>[^)]+)\))?\s*$")


class NodeError(Exception):
    pass


def _scalar(raw, where):
    raw = raw.strip()
    if raw.startswith('"'):
        if not raw.endswith('"') or len(raw) < 2:
            raise NodeError(f"{where}: unterminated quoted string")
        return raw[1:-1].replace('\\"', '"')
    if raw.startswith(("'", "[", "{", "|", ">")):
        raise NodeError(f"{where}: use a bare value or a \"double-quoted\" string (found {raw[:12]!r})")
    return raw


def parse_front_matter(text, where):
    if not text.startswith("---\n"):
        raise NodeError(f"{where}: file must start with a '---' front-matter line")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise NodeError(f"{where}: front matter has no closing '---' line")
    meta, key = {}, None
    for n, line in enumerate(text[4:end].split("\n"), start=2):
        loc = f"{where}:{n}"
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if key is None or not isinstance(meta.get(key), list):
                raise NodeError(f"{loc}: list item without a list key above it")
            meta[key].append(_scalar(line[4:], loc))
            continue
        m = re.match(r"^([a-z_]+):(.*)$", line)
        if not m:
            raise NodeError(f"{loc}: cannot read this line: {line!r}")
        key, rest = m.group(1), m.group(2).split(" #")[0].strip()
        meta[key] = [] if rest == "" else _scalar(rest, loc)
    return meta, text[end + 5:]


def quote(s):
    s = str(s)
    return s if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 .()'’,&-]*", s) and ": " not in s else '"' + s.replace('"', '\\"') + '"'


def dump_front_matter(meta, order):
    out = ["---"]
    for k in order:
        if k not in meta:
            continue
        v = meta[k]
        if isinstance(v, list):
            out.append(f"{k}:")
            out += [f"  - {quote(x) if k != 'sources' else chr(34) + str(x).replace(chr(34), chr(92) + chr(34)) + chr(34)}" for x in v]
        else:
            out.append(f"{k}: {v if k in ('order', 'as_of', 'status') else quote(v)}")
    out.append("---")
    return "\n".join(out) + "\n"


def parse_body(body, where):
    lines = body.strip("\n").split("\n")
    if not lines or not lines[0].startswith("# "):
        raise NodeError(f"{where}: body must start with '# Title'")
    title = lines[0][2:].strip()
    try:
        ci = lines.index("## Concepts")
    except ValueError:
        raise NodeError(f"{where}: missing '## Concepts' section")
    note = "\n".join(lines[1:ci]).strip()
    concepts = []
    for l in lines[ci + 1:]:
        if not l.strip():
            continue
        m = CONCEPT_RE.match(l)
        if not m:
            raise NodeError(f"{where}: concept lines must look like '- **Title**: One sentence.' (got {l[:60]!r})")
        concepts.append({k: v for k, v in m.groupdict().items() if v})
    return title, note, concepts


def load():
    """Return the whole map: [{dir, title, span, summary, nodes: [...]}, ...]."""
    branches = []
    for bdir in sorted(p for p in NODES.iterdir() if p.is_dir()):
        readme = bdir / "README.md"
        meta, body = parse_front_matter(readme.read_text(), str(readme.relative_to(ROOT)))
        btitle, summary = body.strip().split("\n", 1)[0][2:].strip(), "\n".join(body.strip().split("\n")[1:]).strip()
        nodes = []
        for f in sorted(bdir.glob("*.md")):
            if f.name == "README.md":
                continue
            rel = str(f.relative_to(ROOT))
            m, b = parse_front_matter(f.read_text(), rel)
            title, note, concepts = parse_body(b, rel)
            nodes.append({"id": f.stem, "path": rel, "title": title, "note": note, "concepts": concepts, **m})
        nodes.sort(key=lambda n: int(n.get("order", 0)))
        branches.append({"dir": bdir.name, "path": str(readme.relative_to(ROOT)), "title": btitle,
                         "summary": summary, "nodes": nodes, **meta})
    return branches


def validate(branches):
    errs, ids = [], {}
    for b in branches:
        if "span" not in b:
            errs.append(f"{b['path']}: missing 'span'")
        orders = [n.get("order") for n in b["nodes"]]
        if len(set(orders)) != len(orders):
            errs.append(f"{b['dir']}: two nodes share the same 'order'")
        for n in b["nodes"]:
            p = n["path"]
            unknown = set(n) - FIELDS - {"id", "path", "title", "note", "concepts"}
            if unknown:
                errs.append(f"{p}: unknown field(s) {sorted(unknown)}")
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n["id"]):
                errs.append(f"{p}: file name must be lowercase-words-with-hyphens.md")
            if n["id"] in ids:
                errs.append(f"{p}: duplicate node id, also in {ids[n['id']]}")
            ids[n["id"]] = p
            if not str(n.get("order", "")).isdigit():
                errs.append(f"{p}: 'order' must be a whole number")
            for k in ("when", "status"):
                if not n.get(k):
                    errs.append(f"{p}: missing '{k}'")
            for k in LIST_FIELDS:
                if k in n and not isinstance(n[k], list):
                    errs.append(f"{p}: '{k}' must be a list of '  - item' lines")
            if n.get("status") not in ("established", "open"):
                errs.append(f"{p}: 'status' must be established or open")
            if n.get("status") == "open" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(n.get("as_of", ""))):
                errs.append(f"{p}: open (frontier) nodes need 'as_of: YYYY-MM-DD'")
            if not n.get("sources"):
                errs.append(f"{p}: add at least one source under 'sources:'")
            if len(n["title"].split()) > 7:
                errs.append(f"{p}: title longer than 7 words")
            if not 2 <= len(n["concepts"]) <= 5:
                errs.append(f"{p}: needs 2 to 5 concepts (has {len(n['concepts'])})")
            for c in n["concepts"]:
                if "explainer" in c and not (ROOT / Path(p).parent / c["explainer"]).resolve().exists():
                    errs.append(f"{p}: explainer link {c['explainer']} points to a missing folder")
    return errs
