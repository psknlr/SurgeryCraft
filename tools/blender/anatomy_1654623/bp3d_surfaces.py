"""BodyParts3D reference organ surfaces for case 126 (cmcr-1654623), rebuilt the way the v3 handoff did.

Port of `tools/blender/anatomy_surfaces.py` of the v3 package (SurgeryCraft, MIT) to a metric frame:

* v3 read each OBJ (millimetres), reflected X (situs inversus: X -> -X, face winding reversed), scaled by
  0.0143 scene units per mm and translated by (0.337, 1.65, -14.22) scene units (Blender axes: +X patient
  left, -Y anterior, +Z cranial). One v3 scene unit is therefore 1/0.0143 mm = 69.93 mm: the v3 frame is
  NOT metric.
* v4 keeps the v3 origin and axes and expresses them in metres: every v3 length is multiplied by
  V3_UNIT_M = 0.001 / 0.0143. The OBJ scale becomes exactly 0.001 m per mm, the offset (0.337, 1.65,
  -14.22) x V3_UNIT_M, and the liver seam-closure offset / voxel size / noise frequencies are converted
  with the same factor, so the surfaces are the v3 surfaces at life size.
* The reflection happens here, once. The source OBJs are normal anatomy; nothing downstream mirrors them
  again.

Organ surfaces: BodyParts3D, (c) The Database Center for Life Science, CC BY 4.0 (sources.json).
Requires the `bpy` module (Blender 4.1+); `import bpy` comes before `bmesh`.
"""
from __future__ import annotations

from pathlib import Path

import bpy  # noqa: F401  (bpy must be imported before bmesh)
import bmesh
import numpy as np
from mathutils import Vector, noise

SOURCE = Path(__file__).resolve().parents[1] / "sources" / "bodyparts3d"

V3_SCALE_PER_MM = 0.0143                    # v3 scene units per millimetre
V3_UNIT_M = 0.001 / V3_SCALE_PER_MM         # metres per v3 scene unit (= 0.0699301)
V3_PER_M = 1.0 / V3_UNIT_M                  # v3 scene units per metre (= 14.3)
SCALE_M_PER_MM = 0.001
V3_OFFSET = (0.337, 1.65, -14.22)           # v3 scene units, Blender axes
OFFSET_BLENDER = tuple(c * V3_UNIT_M for c in V3_OFFSET)   # metres, Blender axes
#: The BodyParts3D sagittal plane X = 0 lands at this glTF/Blender x (metres).
SOURCE_MIDLINE_X = OFFSET_BLENDER[0]

# v3 liver seam closure (scene units) converted to metres
MERGE_OFFSET = 0.035 * V3_UNIT_M            # 2.448 mm push along the normals before the union
MERGE_VOXEL = 0.025 * V3_UNIT_M             # 1.748 mm voxel remesh
MERGE_SMOOTH = (0.70, 9)                    # Smooth modifier factor, iterations (unitless)


def load_obj(id_: str):
    """Vertices (mm, source frame) and faces of one BodyParts3D OBJ."""
    vs, faces = [], []
    for line in (SOURCE / (id_ + ".obj")).read_text().splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == "v":
            vs.append([float(w) for w in words[1:4]])
        elif words[0] == "f":
            faces.append([int(w.split("/")[0]) - 1 for w in words[1:]])
    return np.array(vs, float), faces


def source_to_blender(v_mm) -> np.ndarray:
    """Source mm -> v4 Blender metres: reflect X (once), scale, translate (v3 transform in metres)."""
    v = np.asarray(v_mm, float)
    out = np.empty_like(v)
    out[:, 0] = -v[:, 0] * SCALE_M_PER_MM + OFFSET_BLENDER[0]
    out[:, 1] = v[:, 1] * SCALE_M_PER_MM + OFFSET_BLENDER[1]
    out[:, 2] = v[:, 2] * SCALE_M_PER_MM + OFFSET_BLENDER[2]
    return out


def blender_to_gltf(b) -> np.ndarray:
    b = np.asarray(b, float)
    return np.stack([b[..., 0], b[..., 2], -b[..., 1]], -1)


def gltf_to_blender(g) -> np.ndarray:
    g = np.asarray(g, float)
    return np.stack([g[..., 0], -g[..., 2], g[..., 1]], -1)


def source_to_gltf(v_mm) -> np.ndarray:
    return blender_to_gltf(source_to_blender(v_mm))


def raw_surface(ids):
    """The mirrored source surfaces (glTF frame, metres) without any processing, for measurements."""
    verts, faces = [], []
    for id_ in ids:
        v, f = load_obj(id_)
        off = len(verts)
        verts.extend(source_to_gltf(v).tolist())
        faces.extend([tuple(off + i for i in reversed(face)) for face in f])
    return np.array(verts), faces


def apply_modifiers(obj):
    """Bake the modifier stack into the mesh (no operator context needed)."""
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    old = obj.data
    name = old.name
    obj.modifiers.clear()
    obj.data = mesh
    bpy.data.meshes.remove(old)
    mesh.name = name


def triangle_count(mesh) -> int:
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def shade_smooth(mesh):
    for p in mesh.polygons:
        p.use_smooth = True


_O1 = Vector((17.3, -5.1, 9.7))
_O2 = Vector((-11.9, 23.4, 3.3))


def tissue(obj, mat):
    """Exportable per-corner colour variation (v3 `tissue`, frequencies converted to metres)."""
    mesh = obj.data
    attr = mesh.color_attributes.new(name="TissueVariation", type="FLOAT_COLOR", domain="CORNER")
    rgb = mat.diffuse_color[:3]
    k = V3_PER_M
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co * k
        # v3 used noise.noise_vector, which is not reproducible between sessions; three offset scalar noise
        # samples give the same kind of variation and byte-identical rebuilds.
        n = noise.noise(p * 27) * .08 + noise.noise(p * 95 + _O1) * .035 + noise.noise(p * 5 + _O2) * .09
        attr.data[loop.index].color = tuple(max(.001, c * (1 + n)) for c in rgb) + (1,)
    nodes = mat.node_tree.nodes
    node = nodes.get("TissueVariation") or nodes.new("ShaderNodeVertexColor")
    node.name = "TissueVariation"
    node.layer_name = attr.name
    mat.node_tree.links.new(node.outputs["Color"], nodes.get("Principled BSDF").inputs["Base Color"])


def atlas_surface(name, ids, merge=False, max_triangles=None):
    """One reference organ: v3 `atlas_surface` (mirror, optional seam closure + remesh + smoothing,
    one subdivision level), then, only when over budget, a collapse decimation to `max_triangles`."""
    vs, faces = [], []
    for id_ in ids:
        v, f = load_obj(id_)
        off = len(vs)
        vs.extend(source_to_blender(v).tolist())
        # Reflecting the source's X axis reverses orientation.
        faces.extend([tuple(off + i for i in reversed(face)) for face in f])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vs, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    if merge:
        # Close atlas segment seams before the union so partition boundaries do not become
        # fictitious scars on the liver capsule (v3).
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.normal_update()
        for v in bm.verts:
            v.co += v.normal * MERGE_OFFSET
        bm.to_mesh(mesh)
        bm.free()
        rem = obj.modifiers.new("Seam closure", "REMESH")
        rem.mode = "VOXEL"
        rem.voxel_size = MERGE_VOXEL
        rem.adaptivity = 0.0
        sm = obj.modifiers.new("Capsule continuity", "SMOOTH")
        sm.factor, sm.iterations = MERGE_SMOOTH
        apply_modifiers(obj)
    sub = obj.modifiers.new("Smooth anatomical surface", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    apply_modifiers(obj)
    before = triangle_count(obj.data)
    if max_triangles and before > max_triangles:
        dec = obj.modifiers.new("Triangle budget", "DECIMATE")
        dec.decimate_type = "COLLAPSE"
        dec.ratio = max_triangles / before
        apply_modifiers(obj)
    shade_smooth(obj.data)
    obj["sourceMeshes"] = ",".join(ids)
    obj["trianglesBeforeBudget"] = before
    return obj
