"""Case 126 (cmcr-1654623, laparoscopic cholecystectomy in situs inversus totalis): the v4 anatomy asset.

    python3.11 -I tools/blender/build_anatomy_1654623.py          # a Python with the `bpy` module (Blender 4.1+)
    blender -b --factory-startup -P tools/blender/build_anatomy_1654623.py

Writes content/assets/cases/cmcr-1654623/{anatomy.glb, anatomy.json, asset-provenance.json} (byte-reproducible).
Add `--diagnostics` to print per-point signed distances of the ported tree to the liver and gallbladder.
Then check it with: python3 -I tools/blender/verify_anatomy_1654623.py

* Organ surfaces (liver, gallbladder, stomach, duodenum, pancreas): BodyParts3D 4.0 (DBCLS, CC BY 4.0),
  rebuilt exactly as the v3 handoff did (anatomy_1654623/bp3d_surfaces.py: X reflected once for situs
  inversus, v3 seam closure/remesh/smoothing for the liver, one subdivision level), expressed in metres in
  the v3 frame, then decimated where needed to stay inside the triangle budget. The gallbladder is cut into
  fundus / body / infundibulum at the Layered Human part fractions.
* Hepatobiliary tree (ducts, hepatic arteries, cystic and gastroduodenal arteries, portal vein): the
  Layered Human / AnatomyExplorer centrelines and radii (anatomy_1654623/lh_hepatobiliary.py, MIT, copied
  unchanged), transformed ONCE: mirror x, 0.1 m per unit, one translation fitted to the BodyParts3D
  gallbladder and liver hilum (recorded in anatomy.json).
* Authored (SurgeryCraft, MIT; labelled `authored`): spleen ellipsoid, cystic plate, the gallbladder
  neck connector, the distal cystic-artery landing on the gallbladder, abdominal wall model, landmarks,
  ports and regions.

Frame (glTF / the GLB): +X patient left, +Y cranial, +Z anterior; metres; origin = the v3 scene origin
(the v3 frame re-expressed in metres; v3 scene units were 69.93 mm). Blender: +X left, -Y anterior, +Z
cranial. Nothing here is patient-specific; nothing is clinician-reviewed.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpy  # noqa: E402  (before bmesh)
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from anatomy_1654623 import bp3d_surfaces as S  # noqa: E402
from anatomy_1654623 import lh_hepatobiliary as LH  # noqa: E402
from anatomy_1654623 import tubes  # noqa: E402

REPO = HERE.parents[1]
CASE = "cmcr-1654623"
OUT = REPO / "content" / "assets" / "cases" / CASE
GLB = OUT / "anatomy.glb"
JSON_OUT = OUT / "anatomy.json"
PROV_OUT = OUT / "asset-provenance.json"

XM = S.SOURCE_MIDLINE_X          # BodyParts3D sagittal midplane (X = 0) in this frame
LH_SOURCE = "Layered Human procedural model (MIT), mirrored once"
BP3D_SOURCE = "BodyParts3D 4.0 (DBCLS), CC BY 4.0"
BP3D_ATTRIBUTION = json.loads((S.SOURCE / "sources.json").read_text(encoding="utf-8"))["attribution"]
LH_ATTRIBUTION = f"Layered Human / AnatomyExplorer, {LH.COPYRIGHT}, MIT ({LH.SOURCE_URL} @ {LH.SOURCE_COMMIT[:12]})"
SC_ATTRIBUTION = "SurgeryCraft contributors, MIT (authored teaching geometry)"

LIVER_IDS = ["FJ2816", "FJ2818", "FJ2819", "FJ2820", "FJ2821", "FJ2822", "FJ2409", "FJ2823", "FJ2824"]
BUDGET = {"liver": 100_000, "pancreas": 20_000, "stomach": 14_000, "duodenum": 14_000, "gallbladder": 16_000}

LABELS = {
    "liver": ("Liver", "肝脏"), "gallbladder": ("Gallbladder", "胆囊"),
    "gallbladder-fundus": ("Fundus of gallbladder", "胆囊底"), "gallbladder-body": ("Body of gallbladder", "胆囊体"),
    "gallbladder-infundibulum": ("Infundibulum (Hartmann's pouch) and neck of gallbladder", "胆囊漏斗部（Hartmann 袋）及胆囊颈"),
    "cystic-plate": ("Cystic plate", "胆囊板"), "stomach": ("Stomach", "胃"), "duodenum": ("Duodenum", "十二指肠"),
    "pancreas": ("Pancreas", "胰腺"), "spleen": ("Spleen", "脾脏"),
    "right-hepatic-duct": ("Right hepatic duct", "右肝管"), "left-hepatic-duct": ("Left hepatic duct", "左肝管"),
    "common-hepatic-duct": ("Common hepatic duct", "肝总管"), "cystic-duct": ("Cystic duct", "胆囊管"),
    "common-bile-duct": ("Common bile duct", "胆总管"), "common-hepatic-artery": ("Common hepatic artery", "肝总动脉"),
    "proper-hepatic-artery": ("Proper hepatic artery", "肝固有动脉"),
    "right-hepatic-artery": ("Right hepatic artery", "肝右动脉"), "left-hepatic-artery": ("Left hepatic artery", "肝左动脉"),
    "cystic-artery": ("Cystic artery", "胆囊动脉"), "gastroduodenal-artery": ("Gastroduodenal artery", "胃十二指肠动脉"),
    "portal-vein": ("Portal vein", "门静脉"),
}

# id, kind, LH centreline, branches (name, LH centreline), n_theta
TUBES = [
    ("right-hepatic-duct", "duct", "RHD_CTRL", [], 18),
    ("left-hepatic-duct", "duct", "LHD_CTRL", [], 18),
    ("common-hepatic-duct", "duct", "CHD_CTRL", [], 20),
    ("cystic-duct", "duct", "CYSTIC_CTRL", [], 18),
    ("common-bile-duct", "duct", "CBD_CTRL", [], 20),
    ("common-hepatic-artery", "artery", "CHA_CTRL", [], 18),
    ("proper-hepatic-artery", "artery", "PHA_CTRL", [], 16),
    ("right-hepatic-artery", "artery", "RHA_CTRL", [], 14),
    ("left-hepatic-artery", "artery", "LHA_CTRL", [], 14),
    ("cystic-artery", "artery", "CYSTIC_A_CTRL", [("cystic-artery-second-branch", "CYSTIC_A_BRANCH_CTRL")], 12),
    ("gastroduodenal-artery", "artery", "GDA_CTRL", [("gastroduodenal-artery-terminal-continuation", "GDA_BRANCH_CTRL")], 14),
    ("portal-vein", "vein", "PV_CTRL", [("right-portal-vein", "RPV_CTRL"), ("left-portal-vein", "LPV_CTRL")], 24),
]
# organ (or plate) each tube end is expected to enter: (structure, end)
ENTERS = {
    "right-hepatic-duct": [("liver", "start")], "left-hepatic-duct": [("liver", "start")],
    "cystic-duct": [("gallbladder-infundibulum", "start")], "common-bile-duct": [("duodenum", "end")],
    "right-hepatic-artery": [("liver", "end")], "left-hepatic-artery": [("liver", "end")],
    "cystic-artery": [("gallbladder", "end")],
    "portal-vein": [("liver", "end:right-portal-vein"), ("liver", "end:left-portal-vein")],
}


def r5(v):
    return [round(float(c), 5) for c in v]


# ----------------------------------------------------------------------------------------- scene, materials
bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, roughness=.38, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    if hasattr(m, "use_nodes") and not m.use_nodes:
        m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if not metallic:
        bsdf.inputs["Subsurface Weight"].default_value = .07
    return m


M = {  # v3 palette, one material per structure kind
    "liver": material("Liver capsule", (.22, .038, .027), .33),
    "gallbladder": material("Gallbladder serosa", (.18, .245, .095), .28),
    "duct": material("Biliary ducts", (.48, .36, .19), .37),
    "artery": material("Arteries", (.40, .07, .055), .34),
    "vein": material("Portal vein", (.15, .105, .14), .38),
    "stomach": material("Gastric serosa", (.52, .24, .19), .39),
    "pancreas": material("Pancreas", (.83, .55, .35), .48),
    "duodenum": material("Duodenum", (.76, .48, .36), .43),
    "spleen": material("Spleen", (.36, .105, .19), .37),
    "plate": material("Cystic plate (authored)", (.62, .47, .38), .55),
}


def link(obj):
    if obj.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)
    return obj


def mesh_object(name, verts_gltf, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(S.gltf_to_blender(verts_gltf).tolist(), [], [tuple(int(i) for i in f) for f in faces])
    mesh.update()
    return link(bpy.data.objects.new(name, mesh))


def tag(obj, structure, kind, provenance, source, attribution, mat=None, note=None):
    obj.name = structure
    obj["structureId"] = structure
    obj["kind"] = kind
    obj["provenance"] = provenance
    obj["source"] = source
    obj["attribution"] = attribution
    obj["patientSpecific"] = False
    if note:
        obj["note"] = note
    if mat is not None and obj.type == "MESH":
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        S.shade_smooth(obj.data)
    return obj


def arrays(obj):
    """Vertices (glTF frame) and triangles of a mesh object (world = local here)."""
    me = obj.data
    v = np.array([vv.co[:] for vv in me.vertices])
    tris = []
    for p in me.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return S.blender_to_gltf(v), np.array(tris, int)


def bvh(verts, tris):
    return BVHTree.FromPolygons([Vector(p) for p in verts], [tuple(int(i) for i in t) for t in tris])


_DIRS = [Vector((1, 0.0013, 0.0007)).normalized(), Vector((-0.0011, 1, 0.0017)).normalized(),
         Vector((0.0009, -0.0012, -1)).normalized()]


def inside(tree, p):
    votes = 0
    for d in _DIRS:
        o, n = Vector(p), 0
        for _ in range(80):
            hit = tree.ray_cast(o, d)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + d * 1e-6
        votes += n % 2
    return votes >= 2


def signed_distance(tree, p):
    d = tree.find_nearest(Vector(p))[3]
    return -d if inside(tree, p) else d


def volume_centroid(verts, tris):
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6
    return (vol[:, None] * (a + b + c) / 4).sum(0) / vol.sum(), abs(vol.sum())


def bounding_radius(verts, centre):
    return float(np.max(np.linalg.norm(verts - centre, axis=1)))


# ----------------------------------------------------------------------------------------- organs (reference)
objects = {}


def organ(structure, ids, mat_key, merge=False):
    obj = S.atlas_surface(structure, ids, merge=merge, max_triangles=BUDGET.get(structure))
    tag(obj, structure, "organ", "reference", BP3D_SOURCE, BP3D_ATTRIBUTION, M[mat_key],
        "BodyParts3D reference anatomy; X reflected once for situs inversus, v3 surface processing; not patient-specific")
    obj["sourceMeshes"] = ",".join(ids)
    objects[structure] = obj
    return obj


organ("liver", LIVER_IDS, "liver", merge=True)
organ("stomach", ["FJ2564"], "stomach")
organ("duodenum", ["FJ2573"], "duodenum")
organ("pancreas", ["FJ1895"], "pancreas")
gb_whole = S.atlas_surface("gallbladder-surface", ["FJ2817"], max_triangles=BUDGET["gallbladder"])

# ----------------------------------------------------------------------------------------- fit features
# All targets are measured on the processed surfaces that go into the GLB (the v3 liver processing inflates the
# capsule by ~2 mm, so the raw source surfaces would put hilar structures inside the exported liver).
gb_raw_v, gb_raw_t = arrays(gb_whole)
gb_c_ref, _ = volume_centroid(gb_raw_v, gb_raw_t)
_x = gb_raw_v - gb_c_ref
_w, _u = np.linalg.eigh(_x.T @ _x)
GB_AXIS = _u[:, 2] if _u[:, 2] @ np.array([0, -1, 1]) > 0 else -_u[:, 2]   # neck -> fundus (inferior, anterior)
_pr = _x @ GB_AXIS
GB_FUNDUS_TIP_REF = gb_raw_v[_pr > _pr.max() - 0.003].mean(0)
GB_NECK_TIP_REF = gb_raw_v[_pr < _pr.min() + 0.003].mean(0)

liver_raw_v, liver_raw_f = S.raw_surface(LIVER_IDS)
liver_raw_tree = BVHTree.FromPolygons([Vector(p) for p in liver_raw_v], liver_raw_f)   # diagnostics only
liver_proc_v, liver_proc_t = arrays(objects["liver"])
liver_tree = bvh(liver_proc_v, liver_proc_t)
# Porta hepatis target: the deepest point of the visceral liver surface between the caudate lobe (FJ2816) and
# segment IV (FJ2820): vertical rays on a 1 mm grid over source X in [-40, 0] mm (right of the source midline,
# i.e. left of it after the reflection) and source anterior depth -Y in [130, 160] mm; PORTA_DEPTH below it.
PORTA_DEPTH = 0.005
best = None
y0 = liver_proc_v[:, 1].min() - 0.01
for x in np.arange(XM, XM + 0.0405, 0.001):
    for z in np.arange(0.130, 0.1605, 0.001) - S.OFFSET_BLENDER[1]:
        hit = liver_tree.ray_cast(Vector((x, y0, z)), Vector((0, 1, 0)))
        if hit[0] is not None and (best is None or hit[0][1] > best[1]):
            best = (float(x), float(hit[0][1]), float(z))
PORTA_TARGET = np.array([best[0], best[1] - PORTA_DEPTH, best[2]])

Mlh = np.diag([-LH.UNIT_METRES, LH.UNIT_METRES, LH.UNIT_METRES])   # mirror x once, 0.1 m per unit


def lh_gb_solid_centroid():
    """Centroid (source units) of the Layered Human gallbladder solid: spheres along GB_CTRL with GB_R
    (as its _gb_shapes) plus the Hartmann pouch ellipsoid, voxelised on a 0.01-unit (1 mm) grid."""
    path = tubes.resample(tubes.catmull_rom(LH.GB_CTRL, max(len(LH.GB_CTRL) * 30, 60)), 0.02)
    r = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(LH.GB_R)), LH.GB_R)
    lo, hi = (path - r[:, None]).min(0) - 0.02, (path + r[:, None]).max(0) + 0.02
    g = np.stack(np.meshgrid(*[np.arange(lo[k], hi[k], 0.01) for k in range(3)], indexing="ij"), -1).reshape(-1, 3)
    ins = np.zeros(len(g), bool)
    for p, rr in zip(path, r):
        ins |= ((g - p) ** 2).sum(1) < rr * rr
    ins |= (((g - np.array(LH.HARTMANN_CENTRE)) / np.array(LH.HARTMANN_RADII)) ** 2).sum(1) < 1
    q = g[ins]
    xq = q - q.mean(0)
    w, u = np.linalg.eigh(xq.T @ xq)
    ax = u[:, 2] if u[:, 2] @ np.array([0, -1, 1]) > 0 else -u[:, 2]
    pr = xq @ ax
    return q.mean(0), ax, float(pr.max() - pr.min())


lh_gb_c, lh_gb_axis, lh_gb_len = lh_gb_solid_centroid()
FEATURES = [  # (name, LH point in source units, target in this frame, description)
    ("gallbladder-centroid", lh_gb_c, gb_c_ref,
     "volume centroid of the Layered Human gallbladder solid -> volume centroid of the BodyParts3D gallbladder (FJ2817)"),
    ("gallbladder-neck", np.array(LH.CYSTIC_CTRL[0]), GB_NECK_TIP_REF,
     "gallbladder neck = cystic-duct origin (CYSTIC_CTRL[0], 0.5 mm from GB_CTRL[-1]) -> neck tip of the "
     "BodyParts3D gallbladder along its long axis"),
    ("hepatic-duct-confluence", np.array(LH.RHD_CTRL[-1]), PORTA_TARGET,
     "RHD/LHD confluence -> porta hepatis of the BodyParts3D liver (deepest visceral-surface point between "
     "caudate lobe and segment IV, 5 mm inferior)"),
]
P_lh = np.array([Mlh @ f[1] for f in FEATURES])
Q_ref = np.array([f[2] for f in FEATURES])
T = (Q_ref - P_lh).mean(0)                     # equal-weight least squares, translation only
FIT_SCALE = 1.0                                # uniform fit scale: not applied (see the record)


def to_case(p_lh):
    return (Mlh @ np.asarray(p_lh, float).T).T * FIT_SCALE + T


residuals = np.linalg.norm(P_lh + T - Q_ref, axis=1)
# For the record: the least-squares optimum with a free uniform scale, and the centroid-only translation.
A = np.zeros((9, 4))
A[:, 0] = P_lh.reshape(-1)
for k in range(3):
    A[k::3, 1 + k] = 1
sol = np.linalg.lstsq(A, Q_ref.reshape(-1), rcond=None)[0]
s_opt, T_opt = float(sol[0]), sol[1:]
res_opt = np.linalg.norm(P_lh * s_opt + T_opt - Q_ref, axis=1)
T_centroid = Q_ref[0] - P_lh[0]
res_centroid = np.linalg.norm(P_lh + T_centroid - Q_ref, axis=1)
lh_axis_case = Mlh @ lh_gb_axis
lh_axis_case /= np.linalg.norm(lh_axis_case)
axis_angle = math.degrees(math.acos(min(1.0, abs(float(lh_axis_case @ GB_AXIS)))))
print("FIT T", T, "residuals mm", np.round(residuals * 1000, 1), "s_opt", round(s_opt, 3),
      "axis angle", round(axis_angle, 1))


# --- gallbladder parts: planes normal to the BodyParts3D long axis at the Layered Human fractions
split = {name: (t0, t1) for name, t0, t1 in LH.GB_PART_SPLIT}
U_FUNDUS_BODY, U_BODY_NECK = split["gb_body"]
d_fn = GB_NECK_TIP_REF - GB_FUNDUS_TIP_REF
L_fn = float(np.linalg.norm(d_fn))
d_hat = d_fn / L_fn


def plane(u):
    co = S.gltf_to_blender(GB_FUNDUS_TIP_REF + u * d_fn)
    no = S.gltf_to_blender(d_hat)
    return Vector(co.tolist()), Vector(no.tolist())


def cut(src_mesh, name, keep_below=None, keep_above=None):
    bm = bmesh.new()
    bm.from_mesh(src_mesh)
    for u, outer in ((keep_below, True), (keep_above, False)):
        if u is None:
            continue
        co, no = plane(u)
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=outer, clear_inner=not outer)
        boundary = [e for e in bm.edges if e.is_boundary]
        res = bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
        new_faces = res["faces"]
        if new_faces:
            tri = bmesh.ops.triangulate(bm, faces=new_faces)
            for f in tri["faces"]:
                f.smooth = False
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


gb_group = link(bpy.data.objects.new("gallbladder", None))
tag(gb_group, "gallbladder", "organ", "reference", BP3D_SOURCE, BP3D_ATTRIBUTION,
    note="group of gallbladder-fundus, gallbladder-body, gallbladder-infundibulum")
gb_parts = {}
for structure, below, above in (("gallbladder-fundus", U_FUNDUS_BODY, None),
                                ("gallbladder-body", U_BODY_NECK, U_FUNDUS_BODY),
                                ("gallbladder-infundibulum", None, U_BODY_NECK)):
    me = cut(gb_whole.data, structure, keep_below=below, keep_above=above)
    obj = link(bpy.data.objects.new(structure, me))
    tag(obj, structure, "organ", "reference", BP3D_SOURCE, BP3D_ATTRIBUTION, M["gallbladder"],
        f"BodyParts3D gallbladder (FJ2817) cut normal to its long axis at the Layered Human part fractions "
        f"{U_FUNDUS_BODY} / {U_BODY_NECK} (fundus tip = 0, neck tip = 1)")
    # flat-shade the caps of the cuts (all their vertices on a cutting plane) so the rims keep smooth normals
    for u in (below, above):
        if u is None:
            continue
        co, no = plane(u)
        on = [abs((v.co - co).dot(no)) < 1e-7 for v in me.vertices]
        for poly in me.polygons:
            if all(on[i] for i in poly.vertices):
                poly.use_smooth = False
    obj.parent = gb_group
    obj["sourceMeshes"] = "FJ2817"
    gb_parts[structure] = obj
    objects[structure] = obj
objects["gallbladder"] = gb_group
bpy.data.objects.remove(gb_whole)

# ----------------------------------------------------------------------------------------- ported tree
CENT = {}      # structure -> dict(main=..., branches={...}) in this frame (metres)
for structure, kind, ctrl, branches, _nt in TUBES:
    CENT[structure] = {"main": to_case(getattr(LH, ctrl)), "ctrl": ctrl,
                       "radius": [r * LH.UNIT_METRES for r in np.atleast_1d(LH.RADII[ctrl])],
                       "branches": {b: (bc, to_case(getattr(LH, bc)), [r * LH.UNIT_METRES for r in np.atleast_1d(LH.RADII[bc])])
                                    for b, bc in branches}}

# final gallbladder geometry (for the neck anchor, the connector and the cystic-artery landing)
gb_v, gb_t = [], []
for structure in ("gallbladder-fundus", "gallbladder-body", "gallbladder-infundibulum"):
    v, t = arrays(gb_parts[structure])
    gb_t.append(t + sum(len(x) for x in gb_v))
    gb_v.append(v)
GB_V, GB_T = np.vstack(gb_v), np.vstack(gb_t)
gb_tree = bvh(GB_V, GB_T)
_pr = (GB_V - GB_FUNDUS_TIP_REF) @ d_hat
GB_NECK_TIP = GB_V[_pr > _pr.max() - 0.003].mean(0)
GB_FUNDUS_TIP = GB_V[_pr < _pr.min() + 0.003].mean(0)

# --- authored: gallbladder neck connector, from 4 mm inside the infundibulum tip to the cystic-duct origin
cys0 = CENT["cystic-duct"]["main"][0]
conn_start = GB_NECK_TIP - d_hat * 0.004
conn_ctrl = np.array([conn_start, (conn_start + cys0) / 2, cys0])
conn_r = [0.0036, CENT["cystic-duct"]["radius"][0]]
cv, cf, _, _ = tubes.tube(conn_ctrl, conn_r, 16, 0.001)
inf = gb_parts["gallbladder-infundibulum"]
bm = bmesh.new()
bm.from_mesh(inf.data)
base = [bm.verts.new(Vector(p)) for p in S.gltf_to_blender(cv).tolist()]
for f in cf:
    face = bm.faces.new([base[i] for i in f])
    face.smooth = True
bm.to_mesh(inf.data)
bm.free()
inf["authoredParts"] = "neck connector tube (SurgeryCraft, MIT) joining the BodyParts3D infundibulum to the cystic duct"

# --- authored: distal cystic artery lands on the BodyParts3D gallbladder serosa
ca = CENT["cystic-artery"]
ca["ported"] = ca["main"].copy()
CA_LAND_MAIN_FROM, CA_LAND_BRANCH_FROM = 3, 1


# free (peritoneal) gallbladder surface: GB faces whose centre lies >= 1.5 mm outside the processed liver
_gb_fc = GB_V[GB_T].mean(1)
_free = np.array([signed_distance(liver_tree, p) >= 0.0015 for p in _gb_fc])
gb_free_tree = bvh(GB_V, GB_T[_free])


def land(points, first):
    out = points.copy()
    for i in range(first, len(points)):
        loc, nrm, _, _ = gb_free_tree.find_nearest(Vector(points[i]))
        out[i] = np.array(loc) + np.array(nrm) * 0.001
    return out


CA_LIFT = (1, 2)              # proximal points lifted out of the liver capsule
CA_LIFT_CLEARANCE = 0.0015


def lift_out(points, indices, clearance):
    out = points.copy()
    moved = []
    for i in indices:
        if signed_distance(liver_tree, out[i]) < clearance:
            loc, nrm, _, _ = liver_tree.find_nearest(Vector(out[i]))
            out[i] = np.array(loc) + np.array(nrm) * clearance
            moved.append(i)
    return out, moved


ca["main"], CA_LIFTED = lift_out(ca["main"], CA_LIFT, CA_LIFT_CLEARANCE)
ca["main"] = land(ca["main"], CA_LAND_MAIN_FROM)
bname, (bctrl, bpts, brad) = next(iter(ca["branches"].items()))
# the second branch starts on CYSTIC_A_CTRL[2] (as in the source): it follows that point if it was lifted
assert np.allclose(bpts[0], ca["ported"][2])
_b = land(bpts, CA_LAND_BRANCH_FROM)
_b[0] = ca["main"][2]
ca["branches"][bname] = (bctrl, _b, brad)
ca["branchPorted"] = bpts

for structure, kind, ctrl, branches, n_theta in TUBES:
    c = CENT[structure]
    verts, faces = [], []
    for pts, rad in [(c["main"], c["radius"])] + [(b[1], b[2]) for b in c["branches"].values()]:
        v, f, _, _ = tubes.tube(pts, rad if len(rad) > 1 else rad[0], n_theta, 0.0015)
        faces.extend([tuple(i + len(verts) for i in fc) for fc in f])
        verts.extend(v.tolist())
    obj = mesh_object(structure, np.array(verts), faces)
    prov_note = "Layered Human centreline and radii, mirrored once; smooth tube (Catmull-Rom spline, linear radius profile)"
    if structure == "cystic-artery":
        prov_note += ("; authored adjustments: proximal points lifted out of the liver capsule, distal points landed "
                      "on the free gallbladder serosa")
    tag(obj, structure, kind, "reference", LH_SOURCE, LH_ATTRIBUTION, M[kind], prov_note)
    objects[structure] = obj

# ----------------------------------------------------------------------------------------- liver bed, plate
liver_v, liver_t = liver_proc_v, liver_proc_t
inf_v, inf_t = arrays(gb_parts["gallbladder-infundibulum"])
# the connector tube is not part of the bed: measure against the BodyParts3D part only
inf_v_bp, inf_t_bp = inf_v, inf_t[: len(inf_t) - sum(len(f) - 2 for f in cf)]
inf_tree = bvh(inf_v_bp, inf_t_bp)
rest_v = np.vstack([arrays(gb_parts[s])[0] for s in ("gallbladder-fundus", "gallbladder-body")])
rest_t, off = [], 0
for s in ("gallbladder-fundus", "gallbladder-body"):
    v, t = arrays(gb_parts[s])
    rest_t.append(t + off)
    off += len(v)
rest_tree = bvh(rest_v, np.vstack(rest_t))
tri_c = liver_v[liver_t].mean(1)
tri_area = 0.5 * np.linalg.norm(np.cross(liver_v[liver_t[:, 1]] - liver_v[liver_t[:, 0]],
                                         liver_v[liver_t[:, 2]] - liver_v[liver_t[:, 0]]), axis=1)
d_inf = np.array([inf_tree.find_nearest(Vector(p))[3] for p in tri_c])
d_rest = np.array([rest_tree.find_nearest(Vector(p))[3] for p in tri_c])
# gallbladder bed under the rest of the gallbladder (fundus + body): liver faces within PLATE_DIST of it
PLATE_DIST = 0.003
bed_sel = (d_rest < PLATE_DIST) & (d_rest < d_inf)
# cystic plate = the footprint of the lower (infundibular) third of the gallbladder on its bed: infundibulum
# faces that touch or sink into the liver (signed distance <= PLATE_CONTACT), projected onto the liver surface,
# lifted 0.7 mm, 1 mm thick. Built on the regular gallbladder mesh so that its outline stays smooth.
PLATE_CONTACT = 0.0015
co_cut, no_cut = (np.array(x) for x in plane(U_BODY_NECK))
co_cut, no_cut = S.blender_to_gltf(co_cut), S.blender_to_gltf(no_cut)
on_cut = np.abs((inf_v_bp - co_cut) @ no_cut) < 1e-6
sd_inf = np.array([signed_distance(liver_tree, p) for p in inf_v_bp])
contact = sd_inf <= PLATE_CONTACT
ptris = np.array([t for t in inf_t_bp if contact[t].all() and not on_cut[t].all()], int)
# keep the largest edge-connected piece
parent = list(range(len(ptris)))


def _find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


edge_owner = {}
for fi, t in enumerate(ptris):
    for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        key = (min(a_, b_), max(a_, b_))
        if key in edge_owner:
            parent[_find(fi)] = _find(edge_owner[key])
        else:
            edge_owner[key] = fi
roots = np.array([_find(i) for i in range(len(ptris))])
ptris = ptris[roots == np.bincount(roots).argmax()]
used = np.unique(ptris)
remap = {int(o): i for i, o in enumerate(used)}
pv_ = []
for i in used:
    loc, nrm, _, _ = liver_tree.find_nearest(Vector(inf_v_bp[i]))
    pv_.append(np.array(loc) + np.array(nrm) * 0.0007)
pv_ = np.array(pv_)
pf_ = [tuple(remap[int(i)] for i in t) for t in ptris]
# the gallbladder faces point away from the liver; the plate faces must point out of the liver (towards the GB)
_f0 = pf_[0]
_n0 = np.cross(pv_[_f0[1]] - pv_[_f0[0]], pv_[_f0[2]] - pv_[_f0[0]])
_ln = np.array(liver_tree.find_nearest(Vector(pv_[_f0[0]]))[1])
if _n0 @ _ln < 0:
    pf_ = [tuple(reversed(f)) for f in pf_]
plate = mesh_object("cystic-plate", pv_, pf_)
sm_p = plate.modifiers.new("Even outline", "SMOOTH")
sm_p.factor, sm_p.iterations = 0.5, 3
sol_m = plate.modifiers.new("Plate thickness", "SOLIDIFY")
sol_m.thickness = 0.001
sol_m.offset = 0.0
S.apply_modifiers(plate)
plate_area = float(sum(0.5 * np.linalg.norm(np.cross(pv_[f[1]] - pv_[f[0]], pv_[f[2]] - pv_[f[0]])) for f in pf_))
tag(plate, "cystic-plate", "plate", "authored", "SurgeryCraft authored teaching geometry (MIT)", SC_ATTRIBUTION,
    M["plate"], "1 mm patch on the liver bed: footprint of the lower (infundibular) third of the gallbladder "
    "projected onto the liver surface and lifted 0.7 mm; not a reconstruction")
objects["cystic-plate"] = plate

# ----------------------------------------------------------------------------------------- spleen (authored)
stomach_v, stomach_t = arrays(objects["stomach"])
liver_c, liver_vol = volume_centroid(liver_v, liver_t)
# designed in normal-situs source millimetres (x patient left, y cranial, z anterior), then reflected like the
# BodyParts3D organs: posterolateral to the gastric fundus, long axis along the 10th rib.
SPLEEN_AXES = np.array([55.0, 35.0, 20.0])        # semi-axes mm: 11 x 7 x 4 cm
u_ = np.array([0.35, -0.45, 0.82]); u_ /= np.linalg.norm(u_)
w_ = np.array([0.8, 0.25, -0.4]); w_ -= (w_ @ u_) * u_; w_ /= np.linalg.norm(w_)
v_ = np.cross(w_, u_)
R_sp = np.stack([u_, v_, w_], 1)


def n_to_case(p_n):
    p_n = np.atleast_2d(p_n)
    src = np.stack([p_n[:, 0], -p_n[:, 2], p_n[:, 1]], 1)    # (X, Y, Z) of the source frame
    return S.source_to_gltf(src)


def case_to_n(g):
    b = S.gltf_to_blender(np.atleast_2d(g))
    src = np.stack([-(b[:, 0] - S.OFFSET_BLENDER[0]), b[:, 1] - S.OFFSET_BLENDER[1], b[:, 2] - S.OFFSET_BLENDER[2]], 1) / 0.001
    return np.stack([src[:, 0], src[:, 2], -src[:, 1]], 1)


sto_n = case_to_n(stomach_v)
liv_n = case_to_n(liver_v)
centre_n = np.array([95.0, 1112.0, 50.0])
for _ in range(80):
    clash = []
    for pts in (sto_n, liv_n):
        q = (pts - centre_n) @ R_sp
        e = ((q / (SPLEEN_AXES + 2.0)) ** 2).sum(1)
        clash.append(pts[e < 1])
    clash = np.vstack(clash)
    if not len(clash):
        break
    away = centre_n - clash.mean(0)
    away[1] = 0
    centre_n = centre_n + away / np.linalg.norm(away) * 1.0
SPLEEN_CENTRE_N = centre_n
nu, nv = 48, 24
sv, sf = [], []
for j in range(nv + 1):
    th = math.pi * j / nv
    for i in range(nu):
        ph = 2 * math.pi * i / nu
        q = np.array([math.cos(th), math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph)]) * SPLEEN_AXES
        q[2] += 6.0 * (q[0] / SPLEEN_AXES[0]) ** 2 - 3.0      # gentle curve: concave visceral (anteromedial) face
        sv.append(centre_n + R_sp @ q)
for j in range(nv):
    for i in range(nu):
        a, b = j * nu + i, j * nu + (i + 1) % nu
        c_, d_ = (j + 1) * nu + (i + 1) % nu, (j + 1) * nu + i
        sf.append((a, d_, c_, b))
spleen_case = n_to_case(np.array(sv))
spleen = mesh_object("spleen", spleen_case, sf)
# weld the poles
bm = bmesh.new()
bm.from_mesh(spleen.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(spleen.data)
bm.free()
tag(spleen, "spleen", "organ", "authored", "SurgeryCraft authored teaching geometry (MIT)", SC_ATTRIBUTION, M["spleen"],
    "authored ellipsoid 11 x 7 x 4 cm in the right upper quadrant (situs inversus); no BodyParts3D spleen was "
    "available offline; not patient-derived")
objects["spleen"] = spleen

for key, mat_key in (("liver", "liver"), ("stomach", "stomach"), ("duodenum", "duodenum"), ("pancreas", "pancreas"),
                     ("gallbladder-fundus", "gallbladder"), ("gallbladder-body", "gallbladder"),
                     ("gallbladder-infundibulum", "gallbladder"), ("spleen", "spleen")):
    S.tissue(objects[key], M[mat_key])

# ----------------------------------------------------------------------------------------- measurements
A_ = {k: arrays(o) for k, o in objects.items() if o.type == "MESH"}
TREES = {k: bvh(*A_[k]) for k in ("liver", "stomach", "duodenum", "pancreas", "spleen")}
TREES["gallbladder"] = gb_tree
TREES["gallbladder-infundibulum"] = inf_tree


def organ_record(structure, anchors, extra=None):
    v, t = A_[structure] if structure in A_ else (GB_V, GB_T)
    c, vol = volume_centroid(v, t)
    rec = {"anchors": {k: r5(p) for k, p in anchors.items()}, "centreline": [r5(p) for p in anchors.values()],
           "radius": round(bounding_radius(v, c), 5), "volumeM3": float(f"{vol:.4g}"),
           "triangles": int(len(t))}
    rec.update(extra or {})
    return rec


cent = {k: volume_centroid(*A_[k])[0] for k in A_}
gb_c_final = volume_centroid(GB_V, GB_T)[0]
# porta and gallbladder fossa on the processed liver
porta_surface = np.array(liver_tree.find_nearest(Vector(PORTA_TARGET))[0])
bed_w = tri_area[bed_sel]
bed_centre = (tri_c[bed_sel] * bed_w[:, None]).sum(0) / bed_w.sum()
bed_radius = float(np.max(np.linalg.norm(tri_c[bed_sel] - bed_centre, axis=1)))
plate_v, plate_t = A_["cystic-plate"]
pl_tc = plate_v[plate_t].mean(1)
pl_w = 0.5 * np.linalg.norm(np.cross(plate_v[plate_t[:, 1]] - plate_v[plate_t[:, 0]],
                                     plate_v[plate_t[:, 2]] - plate_v[plate_t[:, 0]]), axis=1)
plate_centre = (pl_tc * pl_w[:, None]).sum(0) / pl_w.sum()
plate_radius = float(np.max(np.linalg.norm(plate_v - plate_centre, axis=1)))

fund_v = A_["gallbladder-fundus"][0]
body_v = A_["gallbladder-body"][0]
infd_v = inf_v[: len(inf_v) - len(cv)]          # BodyParts3D part without the connector
sp_axis = n_to_case(SPLEEN_CENTRE_N + R_sp @ np.array([SPLEEN_AXES[0], 0, 0]))[0]
sp_axis2 = n_to_case(SPLEEN_CENTRE_N - R_sp @ np.array([SPLEEN_AXES[0], 0, 0]))[0]

# ----------------------------------------------------------------------------------------- wall, landmarks, ports
front_v = np.vstack([A_["liver"][0], GB_V])
z_front_i = int(np.argmax(front_v[:, 2]))
FRONT = front_v[z_front_i]
WALL_A, WALL_B, WALL_RY = 0.17, 0.13, 0.60   # half-width, anterior bulge, craniocaudal radius (m), authored
Y_L1 = float(T[1])                          # Layered Human origin = L1 level, mapped by the fit
Y_UMB = Y_L1 - 0.090                        # umbilicus ~ L3/L4 disc (authored estimate)
Y_XIPH = Y_L1 + 0.090                       # xiphoid tip ~ T10 (authored estimate)
Y_APEX = (Y_UMB + Y_XIPH) / 2
CM_MCL_Y, CM_AAL_Y = 0.075, 0.045           # costal margin height at the MCL / AAL (authored estimate)
MCL_DX, AAL_DX = 0.095, 0.135               # lateral distance of the MCL / AAL from the midline (authored)
CLEAR_MIN = 0.030                           # wall at least 30 mm anterior to every liver/GB/stomach vertex


def wall_shape(x, y):
    u = np.clip((np.asarray(x) - XM) / WALL_A, -0.999, 0.999)
    return WALL_B * np.sqrt(1 - u * u) - WALL_B - (np.asarray(y) - Y_APEX) ** 2 / (2 * WALL_RY)


clear_v = np.vstack([A_["liver"][0], GB_V, A_["stomach"][0]])
Z_APEX = float(np.max(clear_v[:, 2] + CLEAR_MIN - wall_shape(clear_v[:, 0], clear_v[:, 1])))


def wall_z(x, y):
    return Z_APEX + wall_shape(x, y)


def wall_normal(x, y):
    u = np.clip((x - XM) / WALL_A, -0.999, 0.999)
    g = np.array([WALL_B * u / (WALL_A * math.sqrt(1 - u * u)), (y - Y_APEX) / WALL_RY, 1.0])
    return g / np.linalg.norm(g)


def on_wall(x, y):
    return np.array([x, y, wall_z(x, y)])


clear_all = {k: float(np.min(wall_z(A_[k][0][:, 0], A_[k][0][:, 1]) - A_[k][0][:, 2]))
             for k in ("liver", "stomach", "duodenum", "pancreas", "spleen")}
clear_all["gallbladder"] = float(np.min(wall_z(GB_V[:, 0], GB_V[:, 1]) - GB_V[:, 2]))
clear_front = float(wall_z(FRONT[0], FRONT[1]) - FRONT[2])

LANDMARKS = {
    "umbilicus": (on_wall(XM, Y_UMB), "midline; ~L3/L4 level, 9 cm below the L1 level of the fitted tree"),
    "xiphoid": (on_wall(XM, Y_XIPH), "xiphoid tip, midline; ~T10 level, 9 cm above L1"),
    "left-costal-margin-mcl": (on_wall(XM + MCL_DX, CM_MCL_Y), "left midclavicular line (9.5 cm from midline)"),
    "right-costal-margin-mcl": (on_wall(XM - MCL_DX, CM_MCL_Y), "right midclavicular line (9.5 cm from midline)"),
    "left-costal-margin-aal": (on_wall(XM + AAL_DX, CM_AAL_Y), "left anterior axillary line (13.5 cm)"),
    "right-costal-margin-aal": (on_wall(XM - AAL_DX, CM_AAL_Y), "right anterior axillary line (13.5 cm)"),
}
PORTS = {  # mirror-image port plan for situs inversus (liver on the patient's left)
    "A": (XM, Y_UMB - 0.010, "infraumbilical, 1 cm below the umbilicus, midline (camera)"),
    "B": (XM + 0.010, Y_XIPH - 0.020, "subxiphoid, 1 cm left of the midline, 2 cm below the xiphoid tip"),
    "C": (XM + MCL_DX, CM_MCL_Y - 0.020, "left midclavicular line, 2 cm below the costal margin"),
    "D": (XM + AAL_DX, CM_AAL_Y - 0.020, "left anterior axillary line, 2 cm below the costal margin (subcostal)"),
    "E": (XM - 0.015, Y_XIPH - 0.050, "epigastric, 1.5 cm right of the midline, 5 cm below the xiphoid tip"),
    "G": (XM - MCL_DX, CM_MCL_Y - 0.020, "right midclavicular line, 2 cm below the costal margin"),
    "H": (XM - AAL_DX, CM_AAL_Y - 0.020, "right anterior axillary line, 2 cm below the costal margin (subcostal)"),
}

# ----------------------------------------------------------------------------------------- regions
J = CENT["common-hepatic-duct"]["main"][-1]
N = CENT["cystic-duct"]["main"][0]
U_ = CENT["common-hepatic-duct"]["main"][0]
N_edge = np.array(liver_tree.find_nearest(Vector(N))[0])
U_edge = np.array(liver_tree.find_nearest(Vector(U_))[0])
hct_pts = np.array([J, N, N_edge, U_edge])
HCT_CENTRE = hct_pts.mean(0)
HCT_RADIUS = float(np.max(np.linalg.norm(hct_pts - HCT_CENTRE, axis=1)))

# ----------------------------------------------------------------------------------------- export
for o in bpy.context.scene.objects:
    o.select_set(True)
GLB.parent.mkdir(parents=True, exist_ok=True)
COPYRIGHT = ("Organ surfaces: BodyParts3D, (c) DBCLS, CC BY 4.0. Hepatobiliary centrelines/radii: Layered Human / "
             "AnatomyExplorer, (c) 2026 Ethan Prince, MIT. Authored parts: SurgeryCraft, MIT. Not patient-derived.")
export_kw = dict(filepath=str(GLB), export_format="GLB", export_extras=True, export_apply=True, export_yup=True,
                 export_cameras=False, export_lights=False, export_animations=False, export_copyright=COPYRIGHT)
try:
    bpy.ops.export_scene.gltf(**export_kw)
except TypeError:
    export_kw.pop("export_animations")
    bpy.ops.export_scene.gltf(**export_kw)
glb_bytes = GLB.read_bytes()
GLB_SHA = hashlib.sha256(glb_bytes).hexdigest()
TRIS = {k: int(len(v[1])) for k, v in A_.items()}
TOTAL_TRIS = sum(TRIS.values())

# ----------------------------------------------------------------------------------------- anatomy.json
def endpoint(structure, which):
    c = CENT[structure]
    if which.startswith("end:"):
        return c["branches"][which[4:]][1][-1]
    return c["main"][0] if which == "start" else c["main"][-1]


def polyline_distance(p, pts):
    path = tubes.spline(pts, 0.0005)
    return float(np.min(np.linalg.norm(path - p, axis=1)))


structures = []


def add(sid, kind, provenance, source, rec, topology=None, extra=None):
    d = {"id": sid, "node": sid, "kind": kind, "label": {"en": LABELS[sid][0], "zh-CN": LABELS[sid][1]},
         "provenance": provenance, "source": source}
    d.update(rec)
    d["topology"] = topology or {"joins": [], "enters": []}
    d.update(extra or {})
    structures.append(d)


bp3d_proc = "X reflected once (situs inversus), v3 processing (seam closure + 1.75 mm voxel remesh + smoothing for the liver; one subdivision level), metric v3 frame"
add("liver", "organ", "reference", BP3D_SOURCE,
    organ_record("liver", {"centroid": cent["liver"], "porta-hepatis": porta_surface, "gallbladder-fossa": bed_centre}),
    extra={"sourceMeshes": LIVER_IDS, "processing": bp3d_proc + f"; decimated to {BUDGET['liver']} triangles",
           "note": "morphological right lobe lies on the patient's LEFT (situs inversus)"})
add("gallbladder", "organ", "reference", BP3D_SOURCE,
    organ_record("gallbladder", {"fundus-tip": GB_FUNDUS_TIP, "centroid": gb_c_final,
                                 "infundibulum": volume_centroid(infd_v, inf_t_bp)[0], "neck": GB_NECK_TIP}),
    extra={"sourceMeshes": ["FJ2817"], "parts": ["gallbladder-fundus", "gallbladder-body", "gallbladder-infundibulum"],
           "processing": bp3d_proc,
           "longAxis": {"fundusTip": r5(GB_FUNDUS_TIP), "neckTip": r5(GB_NECK_TIP),
                        "lengthM": round(float(np.linalg.norm(GB_NECK_TIP - GB_FUNDUS_TIP)), 5),
                        "direction": r5(-d_hat), "note": "neck -> fundus; PCA long axis of the BodyParts3D gallbladder"},
           "node_note": "GLB node 'gallbladder' is a group whose children are the three part meshes"})
for sid, anchors in (("gallbladder-fundus", {"centroid": cent["gallbladder-fundus"], "fundus-tip": GB_FUNDUS_TIP}),
                     ("gallbladder-body", {"centroid": cent["gallbladder-body"]}),
                     ("gallbladder-infundibulum", {"centroid": volume_centroid(infd_v, inf_t_bp)[0], "neck": GB_NECK_TIP})):
    extra = {"partOf": "gallbladder", "sourceMeshes": ["FJ2817"],
             "split": f"planes normal to the long axis at fractions {U_FUNDUS_BODY} and {U_BODY_NECK} from the fundus tip (Layered Human GB_PART_SPLIT)"}
    if sid == "gallbladder-infundibulum":
        extra["authoredModifications"] = [{
            "what": "neck connector tube (authored, SurgeryCraft MIT)", "centreline": [r5(p) for p in conn_ctrl],
            "radiusProfile": r5(conn_r),
            "why": "joins the BodyParts3D infundibulum to the ported cystic-duct origin; the Hartmann pouch and a "
                   "tortuous neck are not modelled specifically"}]
    add(sid, "organ", "reference", BP3D_SOURCE, organ_record(sid, anchors), extra=extra)
add("cystic-plate", "plate", "authored", "SurgeryCraft authored teaching geometry (MIT)",
    organ_record("cystic-plate", {"centroid": plate_centre}),
    topology={"joins": [], "enters": [], "liesOn": ["liver"], "under": ["gallbladder-infundibulum"]},
    extra={"thicknessM": 0.001, "areaM2": round(plate_area, 7),
           "construction": f"footprint of the infundibular (lower) third of the gallbladder where it touches or sinks into "
                           f"the liver (signed distance <= {PLATE_CONTACT*1000:.1f} mm), projected onto the liver surface, "
                           "lifted 0.7 mm, lightly smoothed, 1 mm solidify"})
for sid in ("stomach", "duodenum", "pancreas"):
    ids = {"stomach": ["FJ2564"], "duodenum": ["FJ2573"], "pancreas": ["FJ1895"]}[sid]
    add(sid, "organ", "reference", BP3D_SOURCE, organ_record(sid, {"centroid": cent[sid]}),
        extra={"sourceMeshes": ids, "processing": bp3d_proc})
add("spleen", "organ", "authored", "SurgeryCraft authored teaching geometry (MIT)",
    organ_record("spleen", {"centroid": cent["spleen"], "posterior-pole": sp_axis2, "anterior-pole": sp_axis}),
    extra={"semiAxesM": r5(SPLEEN_AXES / 1000),
           "note": "authored ellipsoid in the patient's right upper quadrant, posterolateral to the stomach; no "
                   "BodyParts3D spleen was available offline (FJ2561 missing from the fetched set)"})

# tube topology: endpoint joins found geometrically (<= 3 mm), plus the expected organ entries with their gap
ends = {}
KIND = {t[0]: t[1] for t in TUBES}
for structure, *_ in TUBES:
    c = CENT[structure]
    ends[(structure, "start")] = c["main"][0]
    ends[(structure, "end")] = c["main"][-1]
for structure, kind, ctrl, branches, _ in TUBES:
    c = CENT[structure]
    joins = []
    for here in ("start", "end"):
        p = ends[(structure, here)]
        for (other, there), q in ends.items():
            if other != structure and KIND[other] == kind and np.linalg.norm(p - q) <= 0.003:
                joins.append({"id": other, "here": here, "there": there, "gapM": round(float(np.linalg.norm(p - q)), 5)})
        for other, *_r in TUBES:
            if other == structure or KIND[other] != kind:
                continue
            dmin = polyline_distance(p, CENT[other]["main"])
            if dmin <= 0.003 and not any(j["id"] == other for j in joins):
                joins.append({"id": other, "here": here, "there": "along", "gapM": round(dmin, 5)})
    enters = []
    for organ_id, which in ENTERS.get(structure, []):
        p = endpoint(structure, which)
        enters.append({"id": organ_id, "at": which, "signedGapM": round(signed_distance(TREES[organ_id], p), 5),
                       "note": "negative = endpoint inside the organ surface"})
    rec = {"centreline": [r5(p) for p in c["main"]], "spline": "catmull-rom through the points (Layered Human smooth_path)",
           "radius": round(max(c["radius"]), 5), "radiusProfile": r5(c["radius"]),
           "sourceRef": {"file": LH.SOURCE_FILE, "commit": LH.SOURCE_COMMIT, "centreline": ctrl}}
    if c["branches"]:
        rec["branches"] = [{"name": b, "centreline": [r5(p) for p in pts], "radius": round(max(rad), 5),
                            "radiusProfile": r5(rad), "sourceRef": {"centreline": bc}}
                           for b, (bc, pts, rad) in c["branches"].items()]
    extra = {}
    if structure == "cystic-artery":
        extra["authoredModifications"] = [{
            "what": f"proximal points {CA_LIFTED} lifted out of the liver capsule to {CA_LIFT_CLEARANCE*1000:.1f} mm "
                    "along the liver normal (the origin, on the right hepatic artery, is unchanged; the second "
                    "branch still starts on point 2)",
            "mainPointIndices": CA_LIFTED,
            "why": "the ported course ran just under the (v3-processed) liver capsule at the hilum; lifted so the "
                   "artery is visible in the hepatocystic triangle"}, {
            "what": "distal points landed on the free (peritoneal) BodyParts3D gallbladder serosa, outside the liver bed (+1 mm along its normal)",
            "mainPointIndices": list(range(CA_LAND_MAIN_FROM, len(ca["ported"]))),
            "branchPointIndices": list(range(CA_LAND_BRANCH_FROM, len(ca["branchPorted"]))),
            "portedCentreline": [r5(p) for p in ca["ported"]],
            "portedBranchCentreline": [r5(p) for p in ca["branchPorted"]],
            "why": "after the single transform the ported distal course ran into the liver parenchyma / beside the "
                   "gallbladder, because the Layered Human and BodyParts3D gallbladders differ in orientation"}]
        rec["provenanceDetail"] = "reference (ported) origin and proximal course; distal points authored"
    if structure in ("right-hepatic-artery", "left-hepatic-artery", "right-hepatic-duct", "left-hepatic-duct"):
        extra["namingNote"] = ("morphological name kept: 'right' = the morphological right lobe, which lies on the "
                               "patient's LEFT in situs inversus")
    add(structure, kind, "reference", LH_SOURCE, rec, topology={"joins": joins, "enters": enters}, extra=extra)
    if structure == "cystic-duct":
        enters[0]["bridgedBy"] = ("authored neck connector of gallbladder-infundibulum (the ported cystic-duct origin "
                                  "lies just outside the BodyParts3D infundibulum)")

# organs: which ported structures enter them
_by_id = {d["id"]: d for d in structures}
for d in list(structures):
    for e in d["topology"].get("enters", []):
        _by_id[e["id"]]["topology"].setdefault("receives", []).append({"id": d["id"], "at": e["at"]})

ids_in_order = ["liver", "gallbladder", "gallbladder-fundus", "gallbladder-body", "gallbladder-infundibulum",
                "cystic-plate", "stomach", "duodenum", "pancreas", "spleen"] + [t[0] for t in TUBES]
structures.sort(key=lambda d: ids_in_order.index(d["id"]))

feature_records = [{"name": f[0], "lhPointSourceUnits": r5(f[1]), "lhPointMapped": r5(Mlh @ f[1] + T),
                    "target": r5(f[2]), "residualM": round(float(r), 5), "description": f[3]}
                   for f, r in zip(FEATURES, residuals)]
transform = {
    "appliesTo": "every Layered Human centreline and radius in tools/blender/anatomy_1654623/lh_hepatobiliary.py, applied once",
    "formula": "p_case[m] = M . p_LH[unit] + T ; radius_case[m] = 0.1 * radius_LH[unit]",
    "M": [[-0.1, 0.0, 0.0], [0.0, 0.1, 0.0], [0.0, 0.0, 0.1]],
    "steps": ["mirror x -> -x once (situs inversus; the Layered Human values are normal situs)",
              "scale 0.1 m per Layered Human unit (1 unit = 10 cm; the case frame is metric)",
              "uniform fit scale 1.0 (not applied, see fit.scaleNote)",
              f"translate T = {r5(T)} m"],
    "T": r5(T),
    "fitScale": FIT_SCALE,
    "fit": {
        "method": "translation-only least squares, equal weights, over the three features below",
        "features": feature_records,
        "rmsResidualM": round(float(np.sqrt((residuals ** 2).mean())), 5),
        "longAxis": {"angleDeg": round(axis_angle, 1),
                     "layeredHumanLengthM": round(lh_gb_len * LH.UNIT_METRES, 5),
                     "bodyParts3DLengthM": round(L_fn, 5),
                     "note": "a translation cannot rotate the axis; the Layered Human gallbladder is longer and more "
                             "anteriorly directed than the BodyParts3D one"},
        "scaleNote": (f"the least-squares optimum with a free uniform scale is s = {s_opt:.3f}, a {abs(1 - s_opt) * 100:.0f} % "
                      f"change (not a small scale) that only lowers the residuals to "
                      f"{', '.join(f'{x*1000:.1f}' for x in res_opt)} mm (from {', '.join(f'{x*1000:.1f}' for x in residuals)} mm); "
                      "not clearly needed, so not applied (it would also change duct and vessel calibres)"),
        "centroidOnlyAlternative": {
            "T": r5(T_centroid),
            "residualsM": {f[0]: round(float(r), 5) for f, r in zip(FEATURES, res_centroid)},
            "rejectedBecause": "matching the gallbladder centroid alone leaves the duct confluence under the caudate "
                               "lobe, far from the porta, and the cystic-duct origin away from the BodyParts3D "
                               "gallbladder neck; the gallbladder-to-porta vector differs between the two sources",
        },
    },
}
anatomy = {
    "schema": "surgerycraft/case-anatomy@1",
    "caseId": CASE,
    "version": 4,
    "glb": "anatomy.glb",
    "glbSha256": GLB_SHA,
    "units": "m",
    "frame": {
        "statement": "glTF frame of anatomy.glb: +X = patient's left, +Y = cranial, +Z = anterior; metres. Same origin "
                     "and axes as the v3 asset (cmcr-1654623-mirror-abdomen.glb), whose scene units were 1/0.0143 mm "
                     "= 69.93 mm: v4 coordinates = v3 coordinates x 0.0699301. Blender build frame: +X left, -Y "
                     "anterior, +Z cranial.",
        "axes": {"x": "patient left", "y": "cranial", "z": "anterior"},
        "v3UnitM": round(S.V3_UNIT_M, 7),
        "sourceMidlineX": round(XM, 6),
        "sourceMidlineNote": "the BodyParts3D sagittal midplane (source X = 0) is at x = +0.023566 m; midline "
                             "landmarks and ports use it",
        "situs": "inversus totalis: liver and gallbladder on the patient's left (x > midline), stomach and spleen on the right",
    },
    "patientSpecific": False,
    "clinicianReviewed": False,
    "structures": structures,
    "regions": [
        {"id": "hepatocystic-triangle", "label": {"en": "Hepatocystic triangle", "zh-CN": "肝胆囊三角（Calot 三角）"},
         "provenance": "authored", "derivedFrom": ["cystic-duct", "common-hepatic-duct", "liver"],
         "centre": r5(HCT_CENTRE), "radius": round(HCT_RADIUS, 5),
         "boundary": {"cysticDuctJunction": r5(J), "gallbladderNeck": r5(N), "liverEdgeAboveNeck": r5(N_edge),
                      "commonHepaticDuctAtLiverEdge": r5(U_edge)},
         "note": "bounded by the cystic duct, the common hepatic duct and the inferior liver edge; centre = mean of "
                 "the four boundary points, radius = farthest of them"},
        {"id": "cystic-plate", "label": {"en": "Cystic plate (lower third of the gallbladder bed)", "zh-CN": "胆囊板（胆囊床下 1/3）"},
         "provenance": "authored", "derivedFrom": ["liver", "gallbladder-infundibulum"], "structure": "cystic-plate",
         "centre": r5(plate_centre), "radius": round(plate_radius, 5), "areaM2": round(plate_area, 7)},
        {"id": "gallbladder-bed", "label": {"en": "Gallbladder bed (rest of the fossa)", "zh-CN": "胆囊床（其余部分）"},
         "provenance": "authored", "derivedFrom": ["liver", "gallbladder-fundus", "gallbladder-body"],
         "centre": r5(bed_centre), "radius": round(bed_radius, 5), "areaM2": round(float(tri_area[bed_sel].sum()), 7)},
    ],
    "abdominalWall": {
        "provenance": "authored",
        "model": "z = zApex + b*sqrt(1-((x-x0)/a)^2) - b - (y-yApex)^2/(2*Ry)  (insufflated anterior wall, curving "
                 "posteriorly laterally); outward normal = normalise(b*u/(a*sqrt(1-u^2)), (y-yApex)/Ry, 1), u=(x-x0)/a",
        "params": {"x0": round(XM, 6), "a": WALL_A, "b": WALL_B, "Ry": WALL_RY, "yApex": round(Y_APEX, 5),
                   "zApex": round(Z_APEX, 5)},
        "clearanceM": {"atMostAnteriorLiverOrGallbladderPoint": round(clear_front, 5),
                       "mostAnteriorPoint": r5(FRONT), "minimumPerOrgan": {k: round(v, 5) for k, v in clear_all.items()},
                       "rule": f"zApex chosen so that the wall is >= {CLEAR_MIN*1000:.0f} mm anterior to every liver, gallbladder and stomach vertex"},
        "levels": {"L1": round(Y_L1, 5), "note": "L1 = origin level of the Layered Human tree after the fit; other "
                   "levels are authored offsets from it"},
    },
    "landmarks": [
        {"id": k, "provenance": "authored", "point": r5(p), "normal": r5(wall_normal(p[0], p[1])), "note": note}
        for k, (p, note) in LANDMARKS.items()],
    "ports": [
        {"id": k, "provenance": "authored", "point": r5(on_wall(x, y)), "normal": r5(wall_normal(x, y)), "note": note,
         "distanceToHepatocysticTriangleM": round(float(np.linalg.norm(on_wall(x, y) - HCT_CENTRE)), 5)}
        for k, (x, y, note) in PORTS.items()],
    "portedCentrelineTransform": transform,
    "triangles": {"total": TOTAL_TRIS, "perNode": TRIS},
}
JSON_OUT.write_text(json.dumps(anatomy, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------------------------- geometry checks
checks = {}
for structure, kind, ctrl, branches, _ in TUBES:
    c = CENT[structure]
    dense = np.vstack([tubes.spline(c["main"], 0.002)] + [tubes.spline(b[1], 0.002) for b in c["branches"].values()])
    checks[structure] = {k: round(float(np.mean([inside(TREES[k], p) for p in dense])), 3)
                         for k in ("liver", "gallbladder", "stomach", "duodenum", "pancreas")}
GB_IN_LIVER = float(np.mean([inside(TREES["liver"], p) for p in GB_V[::5]]))
print("GEOMETRY CHECKS (fraction of centreline inside each organ)")
for k, v in checks.items():
    print(f"  {k:26s} {v}")

prov = {
    "schema": "surgerycraft/asset-provenance@1",
    "caseId": CASE,
    "asset": "content/assets/cases/cmcr-1654623/anatomy.glb",
    "sha256": GLB_SHA,
    "bytes": len(glb_bytes),
    "triangles": TOTAL_TRIS,
    "builtWith": {"blender": bpy.app.version_string, "script": "tools/blender/build_anatomy_1654623.py"},
    "clinicianReviewed": False,
    "patientSpecific": False,
    "sources": [
        {"id": "bodyparts3d", "provenance": "reference", "name": "BodyParts3D 4.0 (PART-OF, 99 % reduction)",
         "holder": "The Database Center for Life Science (DBCLS)", "licence": "CC BY 4.0",
         "licenceUrl": "https://creativecommons.org/licenses/by/4.0/",
         "licenceEvidence": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html",
         "attribution": BP3D_ATTRIBUTION, "noticeFile": "content/assets/cases/cmcr-1654623/LICENSES.md",
         "files": "tools/blender/sources/bodyparts3d (sources.json: archive entries, sizes, SHA-256)",
         "meshes": json.loads((S.SOURCE / "sources.json").read_text(encoding="utf-8"))["meshes"],
         "licenceNote": "the comment header inside each OBJ still names CC BY-SA 2.1 JP; the CC BY 4.0 statement is "
                        "the DBCLS licence page as recorded by the v3 handoff; not re-checked offline",
         "usedFor": ["liver", "gallbladder", "gallbladder-fundus", "gallbladder-body", "gallbladder-infundibulum",
                     "stomach", "duodenum", "pancreas"]},
        {"id": "layered-human", "provenance": "reference", "name": "Layered Human / AnatomyExplorer, app/micro/hepatobiliary.py",
         "holder": "Ethan Prince", "licence": "MIT", "copyright": LH.COPYRIGHT, "url": LH.SOURCE_URL,
         "commit": LH.SOURCE_COMMIT, "fileSha256": LH.SOURCE_SHA256,
         "notice": "MIT License, " + LH.COPYRIGHT + "; the full permission notice is reproduced in LICENSES.md and in "
                   "the header of lh_hepatobiliary.py",
         "port": "tools/blender/anatomy_1654623/lh_hepatobiliary.py (values copied unchanged, read with ast; module never executed)",
         "usedFor": [t[0] for t in TUBES]},
        {"id": "surgerycraft-authored", "provenance": "authored", "name": "SurgeryCraft authored teaching geometry",
         "licence": "MIT", "holder": "SurgeryCraft contributors",
         "notice": "MIT License, Copyright (c) 2026 SurgeryCraft contributors (full text in LICENSES.md)",
         "usedFor": ["spleen", "cystic-plate", "gallbladder neck connector", "cystic-artery distal landing",
                     "abdominal wall model", "landmarks", "ports", "regions", "materials and vertex colours"]},
    ],
    "evaluatedNotUsed": [
        {"name": "OrganUI gallbladder-3d", "basis": "BodyParts3D 4.3", "licence": "CC BY-SA 2.1 JP",
         "reason": "share-alike licence; not used"},
        {"name": "BodyVista (Z-Anatomy based)", "licence": "CC BY-SA 4.0, with NC / research-only labels on parts",
         "reason": "share-alike and unverified non-commercial/research-only labels; no code or models copied"},
    ],
    "transformationHistory": [
        "BodyParts3D OBJ (mm, normal situs) -> X reflected once, face winding reversed, 0.001 m/mm, offset "
        f"{r5(S.OFFSET_BLENDER)} m (Blender axes) = the v3 transform re-expressed in metres",
        "liver: segments FJ2816/2818-2824/2409 pushed 2.45 mm along normals, 1.75 mm voxel remesh (union), Smooth "
        f"0.70 x 9, subdivision 1, collapse-decimated to {BUDGET['liver']} triangles",
        "gallbladder, stomach, duodenum, pancreas: subdivision 1 (pancreas decimated to the budget if needed)",
        f"gallbladder cut into fundus/body/infundibulum normal to its PCA long axis at {U_FUNDUS_BODY}/{U_BODY_NECK}",
        "Layered Human centrelines: p = M.p + T with M = diag(-0.1, 0.1, 0.1) (mirror once, metres), "
        f"T = {r5(T)} m (fit, see anatomy.json portedCentrelineTransform); tubes swept along the source's "
        "Catmull-Rom spline with its radius profiles (x 0.1 m)",
        "cystic artery (authored adjustments): points 1-2 lifted 1.5 mm out of the liver capsule; points 3-4 of the main "
        "course and 1-2 of the second branch landed on the free gallbladder serosa (+1 mm); origin on the RHA unchanged",
        "authored: spleen ellipsoid, cystic plate patch, neck connector, wall model, landmarks, ports, regions",
        "glTF export (Blender exporter, +Y up), no animation, no instruments",
    ],
    "needsClinicalVerification": [
        "cystic artery course and branching (single artery from the right hepatic artery inside the hepatocystic "
        "triangle; distal landing authored; variants such as a double cystic artery or a low-lying origin not modelled)",
        "ductal confluence position and the cystic-duct insertion (side, length, angle; low or medial insertion and "
        "parallel course not modelled)",
        "tortuous gallbladder neck / Hartmann pouch not modelled specifically (authored straight neck connector)",
        "right hepatic artery relation to the common hepatic duct (Layered Human course; caterpillar hump not modelled)",
        "portal vein and left-sided branches ending at the liver surface (they stop within a few millimetres of the capsule)",
        "laterality of every structure in situs inversus (mirrored reference anatomy, not the patient's imaging)",
        "gallbladder size and orientation (BodyParts3D atlas body, ~6 cm long axis)",
        "spleen size and position (authored ellipsoid)",
        "abdominal wall, costal margins, umbilicus, xiphoid and port positions (authored estimates)",
        "cystic plate extent (authored patch under the lower third)",
    ],
    "knownLimitations": [
        f"the v3 liver processing (2.45 mm seam-closure push, remesh, smoothing) inflates the capsule by about 2 mm: "
        f"{GB_IN_LIVER * 100:.0f} % of the gallbladder vertices lie inside the exported liver (the hepatic surface of "
        "the gallbladder is embedded in its bed, as in v3)",
        f"the Layered Human and BodyParts3D gallbladders differ by {axis_angle:.1f} deg in long-axis direction and "
        f"{(lh_gb_len * LH.UNIT_METRES - L_fn) * 1000:.0f} mm in length; one translation cannot match both the "
        "gallbladder and the porta (fit residuals in anatomy.json)",
        "left portal vein, left hepatic duct and left hepatic artery end at the liver capsule rather than deep in "
        "the umbilical fissure (signed gaps in anatomy.json topology.enters)",
        "the gallbladder parts are closed by flat caps at the cutting planes",
    ],
    "geometryChecks": {"centrelineFractionInside": checks, "gallbladderVerticesInsideLiver": round(GB_IN_LIVER, 3),
                       "fitResidualsM": {f[0]: round(float(r), 5) for f, r in zip(FEATURES, residuals)},
                       "plateContactDistanceM": PLATE_CONTACT, "gallbladderBedDistanceM": PLATE_DIST},
}
PROV_OUT.write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
if "--diagnostics" in sys.argv:
    for structure, *_ in TUBES:
        c = CENT[structure]
        for name, pts in [("main", c["main"])] + [(b, v[1]) for b, v in c["branches"].items()]:
            print("DEBUG", structure, name, " ".join(
                f"[{i}] L{signed_distance(TREES['liver'], p)*1000:+.1f} G{signed_distance(gb_tree, p)*1000:+.1f}"
                for i, p in enumerate(pts)))
    gbin = np.mean([inside(TREES["liver"], p) for p in GB_V[::7]])
    print("DEBUG gallbladder vertices inside processed liver:", round(float(gbin), 3))
    rawin = np.mean([inside(liver_raw_tree, p) for p in GB_V[::7]])
    print("DEBUG gallbladder vertices inside raw liver union:", round(float(rawin), 3))
    print("DEBUG spleen centre n", SPLEEN_CENTRE_N, "plate dist", PLATE_DIST, "plate area cm2", plate_area * 1e4,
          "bed area cm2", float(tri_area[bed_sel].sum()) * 1e4, "clear", clear_front, clear_all)

print("MODEL_BUILT", json.dumps({"glb": str(GLB.relative_to(REPO)), "bytes": len(glb_bytes), "sha256": GLB_SHA,
                                  "triangles": TOTAL_TRIS, "T": r5(T),
                                  "residualsMm": [round(float(r) * 1000, 2) for r in residuals]}))
