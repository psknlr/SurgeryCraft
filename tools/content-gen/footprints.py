"""Equipment footprints (core catalogs + SurgeryCraft catalog) and a solid-overlap checker."""
import json
import os
import catalog

# ClinicalCraft checkout (for the built-in catalogs): $CLINICALCRAFT_DIR, else ../ClinicalCraft next to this repository
HERE = os.path.dirname(os.path.abspath(__file__))
CC_DIR = os.environ.get("CLINICALCRAFT_DIR") or os.path.normpath(os.path.join(HERE, "..", "..", "..", "ClinicalCraft"))
CORE = os.path.join(CC_DIR, "packages", "content", "catalogs")
TYPES = {}
for fn in ("core-furniture", "core-clinical", "core-diagnostics"):
    for e in json.load(open(f"{CORE}/{fn}.json"))["equipment"]:
        TYPES[e["id"]] = e
for e in catalog.EQUIPMENT:
    TYPES[e["id"]] = e


def box(p):
    t = TYPES[p["type"]]
    fp = t["footprint"]
    rot = int(p.get("rot", 0)) % 360
    w, d = (fp["w"], fp["d"]) if rot in (0, 180) else (fp["d"], fp["w"])
    y = p.get("y", 0)
    return (p["x"] - w / 2, p["x"] + w / 2, p["z"] - d / 2, p["z"] + d / 2, y, y + fp["h"])


def solid(p):
    return TYPES[p["type"]].get("solid", True)


def overlaps(placements, tol=0.05, where=""):
    out = []
    sol = [p for p in placements if solid(p)]
    for i in range(len(sol)):
        a = box(sol[i])
        for j in range(i + 1, len(sol)):
            b = box(sol[j])
            ox = min(a[1], b[1]) - max(a[0], b[0])
            oz = min(a[3], b[3]) - max(a[2], b[2])
            oy = min(a[5], b[5]) - max(a[4], b[4])
            if ox > tol and oz > tol and oy > tol:
                out.append(f"{where}: {sol[i]['id']} overlaps {sol[j]['id']} by {ox:.2f}x{oz:.2f}")
    return out


def inside(placements, w, d, where="", tol=0.05):
    """Solid footprints must stay inside the room's inner faces (walls 0.35 thick)."""
    out = []
    hw, hd = w / 2 - 0.175, d / 2 - 0.175
    for p in placements:
        x0, x1, z0, z1, _, _ = box(p)
        if not solid(p):
            continue
        if x0 < -hw - tol or x1 > hw + tol or z0 < -hd - tol or z1 > hd + tol:
            out.append(f"{where}: {p['id']} ({p['type']}) pokes through a wall: x[{x0:.2f},{x1:.2f}] z[{z0:.2f},{z1:.2f}] room ±{hw:.2f}/±{hd:.2f}")
    return out
