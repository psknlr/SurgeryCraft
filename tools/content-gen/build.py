"""Write the SurgeryCraft content pack JSON (catalog, room templates, facility)."""
import json
import os
import sys

from common import dump_catalog, dump_doc, L
import catalog

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "content"))


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", full)


# equipment models: tools/blender/build.py writes the GLBs (content/assets/models/) and their catalog references
MODELS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender", "models.json")
if os.path.exists(MODELS):
    with open(MODELS, encoding="utf-8") as f:
        refs = json.load(f)
    types = {e["id"]: e for e in catalog.EQUIPMENT}
    for type_id, ref in refs.items():
        assert type_id in types, ("model of an unknown type", type_id)
        assert os.path.exists(os.path.join(OUT, "assets", ref["uri"])), ("model file missing: run tools/blender/build.py", ref["uri"])
        types[type_id]["model"] = ref

cat = {
    "schema": "clinicalcraft/equipment-catalog@1",
    "id": catalog.CATALOG_ID,
    "name": L("SurgeryCraft 手术部设备", "SurgeryCraft operating-department equipment"),
    "materials": catalog.MATERIALS,
    "equipment": catalog.EQUIPMENT,
}
write(f"catalogs/{catalog.CATALOG_ID}.json", dump_catalog(cat))

try:
    import templates
except ImportError:
    templates = None
if templates:
    for t in templates.TEMPLATES:
        write(f"templates/{t['id']}.json", dump_doc(t, list_keys_one_per_line=("partitions", "lights", "placements", "patientSlots", "staff", "zones")))

try:
    import facility
except ImportError:
    facility = None
if facility:
    f = facility.build()
    write(f"facilities/{f['id']}.json", dump_doc(
        f,
        list_keys_one_per_line=("levels", "buildings", "rooms", "placements", "patientSlots", "staff", "connectors", "access", "instances", "materials"),
        expand_keys=("terrain",),
    ))
