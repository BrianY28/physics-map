#!/usr/bin/env python3
"""Summarise log.jsonl: one line per DeepSeek call."""
import json
from pathlib import Path

rows = [json.loads(l) for l in (Path(__file__).parent / "log.jsonl").read_text().splitlines() if l.strip()]
for r in rows:
    status = "ok " if r["ok"] else "ERR"
    print(f"{r['tag']:36} try{r['attempt']} {status} {r.get('secs', 0):6.1f}s out={r.get('out_tokens')} "
          f"think_chars={r.get('thinking_chars')} via={r.get('via', '-')} {r.get('error', '')}")
ok = [r for r in rows if r["ok"]]
print(f"total: {len(rows)} calls ({len(ok)} ok), {sum(r.get('out_tokens') or 0 for r in ok)} output tokens")
