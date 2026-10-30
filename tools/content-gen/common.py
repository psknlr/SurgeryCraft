"""Shared helpers for the SurgeryCraft content generator (python3 build.py rewrites ../../content)."""
import json

BASE_MATERIALS = {
    'ambulance-red', 'ambulance-white', 'asphalt', 'beacon-blue', 'beige', 'biohazard', 'black', 'blue', 'brick-red',
    'chrome', 'clin-blood-bag', 'clin-hose-blue', 'coal', 'cream', 'curtain', 'darkwood', 'dirt', 'dx-led-blue', 'floor',
    'glass', 'gold', 'grass', 'green', 'hair', 'lamp', 'lead-glass', 'leaf', 'leaflight', 'led-amber', 'led-blue',
    'led-green', 'led-red', 'lightbox', 'lino', 'mattress', 'mint', 'navy', 'orange', 'oxygen-green', 'paper', 'path',
    'pink', 'plastic', 'purple', 'red', 'roof', 'rubber', 'sand', 'screen', 'screen-dark', 'scrubs', 'skin', 'steel',
    'stone', 'teal', 'tile-blue', 'tile-white', 'vehicle-glass', 'warning-yellow', 'water', 'white', 'wood', 'yellow',
}


def num(v):
    v = round(float(v), 4)
    if v == int(v):
        return int(v)
    return v


def L(zh, en):
    return {"zh-CN": zh, "en": en}


def B(m, x, y, z, w, h, d, **kw):
    """A voxel part: material, centre (x, y, z), size (w, h, d)."""
    part = {"m": m, "p": [num(x), num(y), num(z)], "s": [num(w), num(h), num(d)]}
    for k, v in kw.items():
        part[k] = v
    return part


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(", ", ": "))


def dump_doc(doc, list_keys_one_per_line=(), expand_keys=()):
    """Repo style: one top-level key per line; listed arrays one item per line; listed objects one key per line."""
    lines = ["{"]
    keys = list(doc.keys())
    for i, k in enumerate(keys):
        v = doc[k]
        comma = "," if i < len(keys) - 1 else ""
        if k in list_keys_one_per_line and isinstance(v, list) and v:
            lines.append(f'  "{k}": [')
            for j, item in enumerate(v):
                c2 = "," if j < len(v) - 1 else ""
                lines.append(f"    {compact(item)}{c2}")
            lines.append(f"  ]{comma}")
        elif k in expand_keys and isinstance(v, dict) and v:
            lines.append(f'  "{k}": {{')
            sub = list(v.keys())
            for j, sk in enumerate(sub):
                c2 = "," if j < len(sub) - 1 else ""
                sv = v[sk]
                if isinstance(sv, list) and sv and isinstance(sv[0], dict):
                    lines.append(f'    "{sk}": [')
                    for n, item in enumerate(sv):
                        c3 = "," if n < len(sv) - 1 else ""
                        lines.append(f"      {compact(item)}{c3}")
                    lines.append(f"    ]{c2}")
                else:
                    lines.append(f'    "{sk}": {compact(sv)}{c2}')
            lines.append(f"  }}{comma}")
        else:
            lines.append(f'  "{k}": {compact(v)}{comma}')
    lines.append("}")
    return "\n".join(lines) + "\n"


def dump_catalog(cat):
    """Catalog style of core-clinical.json: equipment entries expanded, parts one per line."""
    out = ["{"]
    out.append(f'  "schema": {compact(cat["schema"])},')
    out.append(f'  "id": {compact(cat["id"])},')
    out.append(f'  "name": {compact(cat["name"])},')
    out.append('  "materials": [')
    for i, m in enumerate(cat["materials"]):
        out.append(f"    {compact(m)}" + ("," if i < len(cat["materials"]) - 1 else ""))
    out.append("  ],")
    out.append('  "equipment": [')
    for i, e in enumerate(cat["equipment"]):
        out.append("    {")
        keys = list(e.keys())
        for j, k in enumerate(keys):
            c = "," if j < len(keys) - 1 else ""
            v = e[k]
            if k in ("description", "usage"):
                out.append(f'      "{k}": {{')
                out.append(f'        "zh-CN": {compact(v["zh-CN"])},')
                out.append(f'        "en": {compact(v["en"])}')
                out.append(f"      }}{c}")
            elif k == "parts":
                out.append('      "parts": [')
                for n, p in enumerate(v):
                    out.append(f"        {compact(p)}" + ("," if n < len(v) - 1 else ""))
                out.append(f"      ]{c}")
            else:
                out.append(f'      "{k}": {compact(v)}{c}')
        out.append("    }" + ("," if i < len(cat["equipment"]) - 1 else ""))
    out.append("  ]")
    out.append("}")
    return "\n".join(out) + "\n"
