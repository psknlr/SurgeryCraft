"""
Render a preview of each built model (content/assets/models/<type>.glb) from a three-quarter front
view with Cycles on the CPU — a look at the models without a browser (docs/MODELS.md).

    blender -b -P tools/blender/preview.py -- [--out DIR] [<type id> …]
    python3 tools/blender/preview.py [--out DIR] [<type id> …]       # a Python with the `bpy` module

Writes DIR/<type>.png (default tools/blender/previews/, git-ignored). A contact sheet:
`montage -label '%t' -geometry 300x300+4+4 -tile 5x DIR/*.png sheet.png` (ImageMagick).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
MODELS = HERE.parents[1] / "content" / "assets" / "models"


def render(glb: Path, out: Path, size: int = 300, samples: int = 16) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    sc = bpy.context.scene
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for ob in sc.objects:
        if ob.type == "MESH":
            for corner in ob.bound_box:
                w = ob.matrix_world @ Vector(corner)
                lo, hi = Vector(map(min, lo, w)), Vector(map(max, hi, w))
    centre, extent = (lo + hi) / 2, (hi - lo).length
    cam = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    view = Vector((0.9, -1.6, 0.75)).normalized() * extent * 1.7  # the front faces Blender -Y
    cam.location = centre + view
    cam.rotation_euler = (-view).to_track_quat("-Z", "Y").to_euler()
    for name, energy, rot in (("key", 3.5, (50, 10, 30)), ("fill", 1.2, (60, 0, 200))):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "SUN"))
        light.data.energy = energy
        light.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.collection.objects.link(light)
    world = bpy.data.worlds.new("world")
    sc.world = world
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.75, 0.82, 0.82, 1)
    bg.inputs[1].default_value = 0.9
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)


def main(argv: list[str]) -> None:
    out_dir = HERE / "previews"
    if "--out" in argv:
        i = argv.index("--out")
        out_dir = Path(argv[i + 1]).resolve()
        del argv[i:i + 2]
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [MODELS / f"{i}.glb" for i in argv] if argv else sorted(MODELS.glob("*.glb"))
    for glb in files:
        render(glb, out_dir / f"{glb.stem}.png")
        print(f"{glb.stem} -> {out_dir / (glb.stem + '.png')}")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ([] if Path(sys.argv[0]).name.startswith("blender") else sys.argv[1:]))
