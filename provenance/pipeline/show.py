#!/usr/bin/env python3
"""Print branches compactly for review: show.py <branch_id> [...]"""
import json, sys
from pathlib import Path

HERE = Path(__file__).parent
for bid in sys.argv[1:]:
    data = json.loads((HERE / "branches" / f"{bid}.json").read_text())
    print(f"=== {bid}")
    for s in data["subtopics"]:
        print(f"* {s['title']} | {s['when']} | {', '.join(s['people'])}\n    {s['note']}")
        for c in s["concepts"]:
            print(f"    - {c['title']}: {c['note']}")
