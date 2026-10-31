"""
Build SurgeryCraft's equipment models (docs/MODELS.md): every builder in models.py runs in an
empty Blender scene, in its type's frame, and is exported with ClinicalCraft's Blender bridge
(scripts/blender) to content/assets/models/<type>.glb; the catalog references (sha256, offset,
licence, source, use status) go to tools/blender/models.json, which tools/content-gen/build.py
puts into the catalog.

    blender -b -P tools/blender/build.py [-- <type id> …]
    python3 tools/blender/build.py [<type id> …]        # a Python with the `bpy` module (Blender 4.1+)

ClinicalCraft is found at $CLINICALCRAFT_DIR or ../ClinicalCraft (as the content generator does).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CLINICALCRAFT = Path(os.environ.get("CLINICALCRAFT_DIR") or REPO.parent / "ClinicalCraft").resolve()
sys.path[:0] = [str(CLINICALCRAFT / "scripts" / "blender"), str(HERE)]

import bpy  # noqa: E402

import clinicalcraft_blender as cc  # noqa: E402
from clinicalcraft_shapes import Kit  # noqa: E402
from models import MODELS  # noqa: E402

CONTENT = REPO / "content"
OUT = CONTENT / "assets" / "models"
MANIFEST = HERE / "models.json"
#: Licence of the models (the same as ClinicalCraft's code); they are SurgeryCraft's own work.
LICENSE = "MIT"
ATTRIBUTION = {
    "zh-CN": "SurgeryCraft 贡献者，依据该设备类型的体素部件在 Blender 中建模（tools/blender/models.py）",
    "en": "SurgeryCraft contributors, modelled in Blender from the type's voxel parts (tools/blender/models.py)",
}


def build(type_id: str) -> dict:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    eq = cc.load_type(type_id, content=[CONTENT])
    k = Kit(eq)
    MODELS[type_id](k, eq)
    ob = k.finish()
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    ref = cc.export_model(
        eq, OUT / f"{type_id}.glb", license=LICENSE, use="cleared", attribution=ATTRIBUTION,
        source={"name": "SurgeryCraft tools/blender/models.py", "url": "https://github.com/psknlr/SurgeryCraft",
                "version": f"Blender {bpy.app.version_string}", "changes": "modelled procedurally from the type's voxel parts and footprint"},
    )
    print(f"{type_id}: {tris} triangles, {len(ob.data.materials)} materials, {(OUT / f'{type_id}.glb').stat().st_size} B")
    return ref


def main(argv: list[str]) -> None:
    ids = argv or sorted(MODELS)
    unknown = [i for i in ids if i not in MODELS]
    if unknown:
        raise SystemExit(f"no builder for {', '.join(unknown)} (models.py has {', '.join(sorted(MODELS))})")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    for type_id in ids:
        manifest[type_id] = build(type_id)
    manifest = {k: manifest[k] for k in sorted(manifest) if k in MODELS}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(ids)} model(s) to {OUT.relative_to(REPO)} and {MANIFEST.relative_to(REPO)}")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ([] if bpy.app.binary_path and Path(sys.argv[0]).name.startswith("blender") else sys.argv[1:])
    main(args)
