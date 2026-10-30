"""Approximate the world model's navigation rule on a single room template (EMBODIED §7):
0.5 m cells (centres at ±0.25 + k·0.5 in the template frame), a cell is blocked when a disk of radius 0.38
around its centre overlaps a solid footprint or a partition (0.35 thick, door/opening gaps passable).
Reachability = 4-connected flood from the cells in front of each door; an item is reachable when a reachable
cell lies within its interaction reach. Conservative (no 8-connectivity, no line-of-sight relaxation)."""
import math
import footprints as fp

INF = 0.38
CELL = 0.5
REACH = {"workstation": 1.2, "monitor": 2.0, "bed": 1.5, "device": 1.2, "atlas": 1.5, "board": 2.5, "craft": 1.2,
         "door": 1.2, "sink": 1.0, "storage": 1.0, "none": 1.0}


def box_dist(px, pz, x0, x1, z0, z1):
    """Chebyshev distance: the world model inflates colliders as boxes."""
    return max(x0 - px, 0, px - x1, z0 - pz, 0, pz - z1)


def rect_dist(px, pz, x0, x1, z0, z1):
    dx = max(x0 - px, 0, px - x1)
    dz = max(z0 - pz, 0, pz - z1)
    return math.hypot(dx, dz)


def wall_segments(t):
    W, D = t["size"]["w"], t["size"]["d"]
    hw, hd = W / 2, D / 2
    segs = []
    for p in t["partitions"]:
        side = p["side"]
        th = p.get("thickness", 0.35) / 2
        if side in ("n", "s"):
            line = -hd if side == "n" else hd
            a, b, centre = -hw, hw, 0.0
        else:
            line = -hw if side == "w" else hw
            a, b, centre = -hd, hd, 0.0
        gaps = []
        for o in p.get("openings", []):
            if o.get("kind") == "window":
                continue
            c = centre + o.get("offset", 0)
            gaps.append((c - o.get("width", 2) / 2, c + o.get("width", 2) / 2))
        pts = [a]
        for g0, g1 in sorted(gaps):
            pts += [g0, g1]
        pts.append(b)
        for i in range(0, len(pts), 2):
            s0, s1 = pts[i], pts[i + 1]
            if s1 - s0 <= 1e-6:
                continue
            if side in ("n", "s"):
                segs.append((s0, s1, line - th, line + th))
            else:
                segs.append((line - th, line + th, s0, s1))
    return segs, gaps_all(t)


def gaps_all(t):
    W, D = t["size"]["w"], t["size"]["d"]
    out = []
    for p in sorted(t["partitions"], key=lambda p: 0 if p["side"] == "s" and p.get("openings") else 1):
        for o in p.get("openings", []):
            if o.get("kind") == "window":
                continue
            c = o.get("offset", 0)
            side = p["side"]
            if side == "n":
                out.append((c, -D / 2 + 0.5))
            elif side == "s":
                out.append((c, D / 2 - 0.5))
            elif side == "w":
                out.append((-W / 2 + 0.5, c))
            else:
                out.append((W / 2 - 0.5, c))
    return out


def analyse(t, extra=()):
    W, D = t["size"]["w"], t["size"]["d"]
    placements = list(t["placements"]) + list(extra)
    obstacles = [fp.box(p)[:4] for p in placements if fp.solid(p)]
    walls, doors = wall_segments(t)
    obstacles += walls
    xs = [-W / 2 + 0.25 + k * CELL for k in range(int(W / CELL))]
    zs = [-D / 2 + 0.25 + k * CELL for k in range(int(D / CELL))]
    # template frame cells at ±0.25 + k·0.5 regardless of W parity
    xs = [x for x in (k * 0.5 + 0.25 for k in range(-40, 40)) if -W / 2 < x < W / 2]
    zs = [z for z in (k * 0.5 + 0.25 for k in range(-40, 40)) if -D / 2 < z < D / 2]
    free = {}
    for x in xs:
        for z in zs:
            free[(x, z)] = all(box_dist(x, z, *o) >= INF for o in obstacles)
    # seed: the free cell nearest the main door (the first door); every other door must be reached from it
    seen = set()
    stack = []
    door_cells = []
    for gx, gz in doors:
        best = min((c for c in free if free[c]), key=lambda c: math.hypot(c[0] - gx, c[1] - gz), default=None)
        door_cells.append(best if best and math.hypot(best[0] - gx, best[1] - gz) < 0.9 else None)
    if door_cells and door_cells[0]:
        stack.append(door_cells[0])
    while stack:
        c = stack.pop()
        if c in seen or not free.get(c):
            continue
        seen.add(c)
        x, z = c
        for n in ((x + CELL, z), (x - CELL, z), (x, z + CELL), (x, z - CELL)):
            if free.get(n) and n not in seen:
                stack.append(n)
    bad = []
    for p in placements:
        typ = fp.TYPES[p["type"]]
        kind = typ.get("interaction", {}).get("kind", "none")
        if kind == "none":
            continue
        reach = typ.get("reach", REACH[kind])
        x0, x1, z0, z1, _, _ = fp.box(p)
        if not any(rect_dist(cx, cz, x0, x1, z0, z1) <= reach for cx, cz in seen):
            bad.append(p["id"])
    for k, c in enumerate(door_cells):
        if c is None or c not in seen:
            bad.append(f"door#{k}@{doors[k]}")
    return bad, seen, free, xs, zs


def ascii(t, extra=()):
    bad, seen, free, xs, zs = analyse(t, extra)
    rows = []
    for z in zs:
        rows.append("".join("o" if (x, z) in seen else ("." if free[(x, z)] else "#") for x in xs))
    return "\n".join(rows), bad
