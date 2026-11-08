#!/usr/bin/env python3
"""Text-level checks that DeepSeek applied feedback-v1 (visual fixes are re-tested in a browser)."""
import re, sys
from pathlib import Path

p = Path(sys.argv[1])
h = p.read_text()
low = h.lower()
checks = {
    "1 Motte 1729 wording": "perseveres in its state of rest" in h and "impress'd thereon" in h,
    "1 old 1934 wording gone": "forces impressed upon it" not in h,
    "2 Buridan quantity of matter": "quantity of matter" in low,
    "3 Voyager interstellar 2012": "interstellar" in low and "2012" in h,
    "3 Voyager 'engines off' gone": "engines have been off" not in low,
    "4 fictitious force names a_bus": bool(re.search(r"a_bus|a<sub>bus|a<sub>\s*bus", h)),
    "5 'side by side' gone": "side by side" not in low,
    "6 symbol span exempt from uppercase": bool(re.search(r"text-transform:\s*none", h)),
    "8 slow-motion note": "slow motion" in low and ("0.25" in h or "¼" in h),
    "9 wall explained": "wall" in low,
    "10 frame-labelled readouts": "(ground)" in low and ("rel. bus" in low or "relative to the bus" in low),
    "12 time axis label": "t (s)" in h,
}
for k, ok in checks.items():
    print(("PASS " if ok else "FAIL ") + k)
print(f"{sum(checks.values())}/{len(checks)} text checks pass")
