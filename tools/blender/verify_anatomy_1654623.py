"""Verify the case 126 (cmcr-1654623) v4 anatomy asset. Plain Python 3, standard library only.

    python3 -I tools/blender/verify_anatomy_1654623.py [path/to/anatomy.glb [path/to/anatomy.json]]

Reads the JSON chunk of anatomy.glb (node names, mesh bounds, index counts) and anatomy.json, checks names,
laterality, gallbladder size, the topology of the ported hepatobiliary tree, the ports and the integrity of the
GLB, prints a summary and exits non-zero if any check fails.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CASE_DIR = REPO / "content" / "assets" / "cases" / "cmcr-1654623"

REQUIRED = [
    "liver", "gallbladder", "gallbladder-fundus", "gallbladder-body", "gallbladder-infundibulum", "cystic-plate",
    "stomach", "duodenum", "pancreas", "spleen", "right-hepatic-duct", "left-hepatic-duct", "common-hepatic-duct",
    "cystic-duct", "common-bile-duct", "common-hepatic-artery", "proper-hepatic-artery", "right-hepatic-artery",
    "left-hepatic-artery", "cystic-artery", "gastroduodenal-artery", "portal-vein",
]
PORTS = ["A", "B", "C", "D", "E", "G", "H"]
MAX_TRIANGLES = 250_000

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))


def dist(a, b):
    return math.dist(a, b)


def catmull_rom(pts, samples=60):
    """Same spline as the build (Layered Human smooth_path), pure Python."""
    pts = [list(map(float, p)) for p in pts]
    if len(pts) < 3:
        return [[pts[0][k] + (pts[-1][k] - pts[0][k]) * i / (samples - 1) for k in range(3)] for i in range(samples)]
    ext = [[2 * a - b for a, b in zip(pts[0], pts[1])]] + pts + [[2 * a - b for a, b in zip(pts[-1], pts[-2])]]
    per = max(2, samples // (len(pts) - 1))
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(per):
            t = j / per
            t2, t3 = t * t, t * t * t
            out.append([0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                        for a, b, c, d in zip(p0, p1, p2, p3)])
    out.append(pts[-1])
    return out


def point_to_polyline(p, poly):
    best = float("inf")
    for a, b in zip(poly, poly[1:]):
        ab = [y - x for x, y in zip(a, b)]
        ap = [y - x for x, y in zip(a, p)]
        L2 = sum(c * c for c in ab)
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, sum(x * y for x, y in zip(ap, ab)) / L2))
        q = [x + t * c for x, c in zip(a, ab)]
        best = min(best, dist(p, q))
    return best


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or length != len(data):
        raise ValueError("not a glTF 2.0 binary")
    clen, ctype = struct.unpack_from("<I4s", data, 12)
    if ctype != b"JSON":
        raise ValueError("first chunk is not JSON")
    return json.loads(data[20:20 + clen].decode("utf-8")), data


def node_bounds(gltf, index, parent=None):
    """World-space AABB of a node's mesh (translation/scale only; the build exports identity transforms)."""
    node = gltf["nodes"][index]
    t = node.get("translation", [0, 0, 0])
    s = node.get("scale", [1, 1, 1])
    lo, hi = [math.inf] * 3, [-math.inf] * 3
    if "mesh" in node:
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            for k in range(3):
                a, b = acc["min"][k] * s[k] + t[k], acc["max"][k] * s[k] + t[k]
                lo[k], hi[k] = min(lo[k], a, b), max(hi[k], a, b)
    for c in node.get("children", []):
        clo, chi = node_bounds(gltf, c)
        lo = [min(x, y) for x, y in zip(lo, clo)]
        hi = [max(x, y) for x, y in zip(hi, chi)]
    return lo, hi


def main(argv):
    glb_path = Path(argv[1]) if len(argv) > 1 else CASE_DIR / "anatomy.glb"
    json_path = Path(argv[2]) if len(argv) > 2 else glb_path.with_name("anatomy.json")
    gltf, raw = read_glb(glb_path)
    anatomy = json.loads(json_path.read_text(encoding="utf-8"))
    S = {s["id"]: s for s in anatomy["structures"]}
    names = {n.get("name"): i for i, n in enumerate(gltf["nodes"])}

    # --- format and integrity
    check("schema", anatomy.get("schema") == "surgerycraft/case-anatomy@1" and anatomy.get("units") == "m",
          f"schema={anatomy.get('schema')} units={anatomy.get('units')}")
    sha = hashlib.sha256(raw).hexdigest()
    check("glb sha256 = anatomy.json glbSha256", sha == anatomy.get("glbSha256"), sha[:16] + "...")
    prov_path = json_path.with_name("asset-provenance.json")
    if prov_path.exists():
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        check("glb sha256 = asset-provenance.json", prov.get("sha256") == sha and prov.get("clinicianReviewed") is False
              and prov.get("patientSpecific") is False, "sha256, clinicianReviewed=false, patientSpecific=false")
    check("no animations", not gltf.get("animations"), f"animations={len(gltf.get('animations', []))}")
    tris = 0
    for m in gltf.get("meshes", []):
        for prim in m["primitives"]:
            if prim.get("mode", 4) == 4:
                tris += gltf["accessors"][prim["indices"]]["count"] // 3 if "indices" in prim else \
                    gltf["accessors"][prim["attributes"]["POSITION"]]["count"] // 3
    check(f"triangles <= {MAX_TRIANGLES}", tris <= MAX_TRIANGLES, f"{tris} triangles, {len(raw) / 1e6:.2f} MB")

    # --- names
    missing_nodes = [i for i in REQUIRED if i not in names]
    missing_json = [i for i in REQUIRED if i not in S]
    check("every structure id is a GLB node", not missing_nodes, "missing: " + (", ".join(missing_nodes) or "none"))
    check("every structure id is in anatomy.json", not missing_json, "missing: " + (", ".join(missing_json) or "none"))
    bad_node = [s["id"] for s in anatomy["structures"] if s.get("node") not in names]
    check("every anatomy.json node exists in the GLB", not bad_node, ", ".join(bad_node) or "all present")
    no_prov = [s["id"] for s in anatomy["structures"] if s.get("provenance") not in ("reference", "authored")]
    check("every structure has a provenance tag", not no_prov, ", ".join(no_prov) or "reference/authored on all")
    if missing_json:
        return finish()

    # --- laterality (frame: +x = patient's left)
    for sid, sign in (("liver", 1), ("gallbladder", 1), ("stomach", -1), ("spleen", -1)):
        c = S[sid]["anchors"]["centroid"]
        lo, hi = node_bounds(gltf, names[sid])
        bx = (lo[0] + hi[0]) / 2
        check(f"laterality {sid} x {'>' if sign > 0 else '<'} 0", c[0] * sign > 0 and bx * sign > 0,
              f"centroid x = {c[0] * 100:+.1f} cm, GLB box centre x = {bx * 100:+.1f} cm")

    # --- gallbladder size
    ax = S["gallbladder"]["longAxis"]
    L = dist(ax["fundusTip"], ax["neckTip"])
    lo, hi = node_bounds(gltf, names["gallbladder"])
    diag = dist(lo, hi)
    check("gallbladder long axis 5-10 cm", 0.05 <= L <= 0.10 and diag >= L * 0.999,
          f"fundus tip -> neck tip {L * 100:.1f} cm (GLB box diagonal {diag * 100:.1f} cm)")

    # --- topology of the ported tree
    def c(sid):
        return S[sid]["centreline"]

    neck = S["gallbladder"]["anchors"]["neck"]
    d = dist(c("cystic-duct")[0], neck)
    check("cystic duct GB end <= 5 mm from the gallbladder neck anchor", d <= 0.005, f"{d * 1000:.1f} mm")
    d1, d2 = dist(c("cystic-duct")[-1], c("common-hepatic-duct")[-1]), dist(c("cystic-duct")[-1], c("common-bile-duct")[0])
    check("cystic duct other end <= 3 mm from the CHD/CBD junction", max(d1, d2) <= 0.003,
          f"{d1 * 1000:.1f} mm to the CHD end, {d2 * 1000:.1f} mm to the CBD start")
    d1, d2 = dist(c("common-hepatic-duct")[0], c("right-hepatic-duct")[-1]), dist(c("common-hepatic-duct")[0], c("left-hepatic-duct")[-1])
    check("CHD starts at the RHD/LHD confluence (<= 3 mm)", max(d1, d2) <= 0.003,
          f"{d1 * 1000:.1f} mm to the RHD end, {d2 * 1000:.1f} mm to the LHD end")
    d = dist(c("common-bile-duct")[0], c("common-hepatic-duct")[-1])
    check("CBD starts where the CHD ends (<= 3 mm)", d <= 0.003, f"{d * 1000:.1f} mm")
    rha = catmull_rom(c("right-hepatic-artery"), 400)
    d = point_to_polyline(c("cystic-artery")[0], rha)
    check("cystic artery origin <= 3 mm from the RHA centreline", d <= 0.003, f"{d * 1000:.2f} mm")
    d1, d2 = dist(c("right-hepatic-artery")[0], c("proper-hepatic-artery")[-1]), dist(c("left-hepatic-artery")[0], c("proper-hepatic-artery")[-1])
    check("RHA and LHA arise from the PHA end (<= 3 mm)", max(d1, d2) <= 0.003,
          f"RHA {d1 * 1000:.1f} mm, LHA {d2 * 1000:.1f} mm")
    d1, d2 = dist(c("proper-hepatic-artery")[0], c("common-hepatic-artery")[-1]), dist(c("gastroduodenal-artery")[0], c("common-hepatic-artery")[-1])
    check("PHA and GDA arise from the CHA end (<= 3 mm)", max(d1, d2) <= 0.003,
          f"PHA {d1 * 1000:.1f} mm, GDA {d2 * 1000:.1f} mm")
    long_tubes = [s["id"] for s in anatomy["structures"] if s["kind"] in ("duct", "artery", "vein") and len(s["centreline"]) > 8]
    check("tube centrelines have <= 8 points", not long_tubes, ", ".join(long_tubes) or "all <= 8")

    # --- regions and ports
    regions = {r["id"]: r for r in anatomy["regions"]}
    check("regions present", all(k in regions for k in ("hepatocystic-triangle", "cystic-plate", "gallbladder-bed")),
          ", ".join(sorted(regions)))
    hct = regions["hepatocystic-triangle"]["centre"]
    ports = {p["id"]: p for p in anatomy["ports"]}
    for pid in PORTS:
        p = ports.get(pid)
        if not p:
            check(f"port {pid}", False, "missing")
            continue
        n = p["normal"]
        dn = dist(p["point"], hct)
        check(f"port {pid} reaches the hepatocystic triangle (<= 0.34 m)",
              dn <= 0.34 and abs(math.hypot(*n) - 1) < 1e-3 and n[2] > 0,
              f"{dn * 100:.1f} cm; normal {[round(v, 2) for v in n]}")
    lm = {m["id"] for m in anatomy["landmarks"]}
    need = {"umbilicus", "xiphoid", "left-costal-margin-mcl", "right-costal-margin-mcl"}
    check("landmarks present", need <= lm, ", ".join(sorted(lm)))
    return finish(anatomy, tris, len(raw))


def finish(anatomy=None, tris=None, size=None):
    width = max(len(n) for n, _, _ in results)
    print("Case 126 (cmcr-1654623) v4 anatomy verification")
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {detail}")
    if anatomy:
        t = anatomy.get("portedCentrelineTransform", {})
        print(f"  transform: M = diag(-0.1, 0.1, 0.1), T = {t.get('T')} m, fit RMS {t.get('fit', {}).get('rmsResidualM')} m")
    failed = sum(not ok for _, ok, _ in results)
    print(f"{len(results) - failed}/{len(results)} checks passed" + (f", {failed} FAILED" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
