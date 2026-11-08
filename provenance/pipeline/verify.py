#!/usr/bin/env python3
"""Check that DeepSeek applied the review fixes: required facts present, wrong ones gone, and how much else changed."""
import json
from pathlib import Path

HERE = Path(__file__).parent
MUST = {  # branch -> strings that must now appear
    "newtonian-mechanics": ["least action", "Maupertuis", "1743", "1765", "density"],
    "electromagnetism-optics": ["Heaviside", "1884", "Electrostatic"],
    "thermodynamics-statmech": ["caloric", "Kelvin"],
    "quantum-mechanics-qft": ["Ehrenfest", "Kennard", "Anderson", "Aspect", "2015", "2022"],
    "relativity-gravitation": ["GW170817", "kilonova", "pulsar timing", "Finkelstein"],
    "amo-physics": ["10⁻¹⁸", "attosecond", "Strickland", "laser cooling", "1997"],
    "condensed-matter": ["gapped", "iron-based", "H₃S"],
    "astrophysics-cosmology": ["gas pressure", "r-process", "Bullet Cluster", "Bell Burnell", "1990", "aryon acoustic"],
    "fluids-plasmas-complexity": ["1987-1999"],
    "open-frontier-2026": ["neutrino fog", "10⁻⁴⁸", "2.8", "2027", "Freedman", "lattice", "0.45", "JUNO", "Halzen",
                           "anomalous Hall", "6,100", "Quantum Echoes", "Devoret", "8.6", "1,066", "1,337", "Lawson",
                           "Spitzer", "Hopfield", "R(K)"],
}
MUST_NOT = {
    "newtonian-mechanics": ["Tautochrone", "Clairaut", "non-conservative constraints"],
    "condensed-matter": ["gaped"],
    "astrophysics-cosmology": ["radiative pressure balance"],
    "fluids-plasmas-complexity": ["Extending the period"],
    "open-frontier-2026": ["0.8 eV", "Budil", "Bigot", "Mumgaard", "Galactic rotation evidence"],
}


def flat(data):
    out = {}
    for s in data["subtopics"]:
        out[s["title"]] = s["when"] + " | " + ", ".join(s["people"]) + " | " + s["note"]
        for c in s["concepts"]:
            out[s["title"] + " / " + c["title"]] = c["note"]
    return out


for bid in sorted(MUST):
    new_p, old_p = HERE / "branches" / f"{bid}.json", HERE / "branches.v1" / f"{bid}.json"
    new, old = json.loads(new_p.read_text()), json.loads(old_p.read_text())
    text = new_p.read_text().lower()
    missing = [k for k in MUST[bid] if k.lower() not in text]
    still = [k for k in MUST_NOT.get(bid, []) if k.lower() in text]
    fo, fn = flat(old), flat(new)
    changed = sum(1 for k in fn if fo.get(k) != fn[k])
    print(f"{bid:28} subtopics {len(old['subtopics'])}->{len(new['subtopics'])}  fields changed {changed}/{len(fn)}"
          f"  {'OK' if not missing and not still else ''}")
    if missing: print(f"    missing: {missing}")
    if still: print(f"    still present: {still}")
