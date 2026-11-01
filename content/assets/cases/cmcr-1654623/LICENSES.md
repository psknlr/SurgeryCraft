# Case 126 (cmcr-1654623) anatomy asset v4 — licences

Files: `anatomy.glb`, `anatomy.json`, `asset-provenance.json` (built by
`tools/blender/build_anatomy_1654623.py`, verified by `tools/blender/verify_anatomy_1654623.py`).

This is adapted reference anatomy for teaching. It is **not** patient-specific (no images or
reconstructions of the case patient were used) and it has **not** been reviewed by a clinician.
`asset-provenance.json` lists the transformation history, the GLB's SHA-256 and the structures that
need clinical verification.

The asset combines three sources. Each part keeps its own licence; every GLB node carries
`provenance`, `source` and `attribution` extras, and `anatomy.json` tags every structure.

## 1. BodyParts3D — CC BY 4.0 (organ surfaces)

Used for: `liver`, `gallbladder` (`gallbladder-fundus`, `gallbladder-body`,
`gallbladder-infundibulum`), `stomach`, `duodenum`, `pancreas`.

> BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International

- Licence: https://creativecommons.org/licenses/by/4.0/
- Licence evidence: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Source: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip
  (BodyParts3D 4.0, PART-OF, 99 % reduction); files, archive entries and SHA-256 in
  `tools/blender/sources/bodyparts3d/sources.json`.
- Changes made: X-axis reflection (situs inversus), scaling to metres and translation into the
  case frame; union of the hepatic segment surfaces with seam closure, voxel remesh and smoothing
  (liver); one subdivision level; collapse decimation (liver); the gallbladder cut into three
  parts; new materials and vertex colours.
- Note: the comment header inside the source OBJ files still names "CC Attribution-Share Alike 2.1
  Japan". The CC BY 4.0 statement above is the DBCLS licence page as recorded by the v3 handoff; it
  could not be re-checked from the build environment. Confirm it before redistribution.

## 2. Layered Human / AnatomyExplorer — MIT (hepatobiliary centrelines and radii)

Used for the centrelines and calibres of: `right-hepatic-duct`, `left-hepatic-duct`,
`common-hepatic-duct`, `cystic-duct`, `common-bile-duct`, `common-hepatic-artery`,
`proper-hepatic-artery`, `right-hepatic-artery`, `left-hepatic-artery`, `cystic-artery`,
`gastroduodenal-artery`, `portal-vein`. The values were copied unchanged from
`app/micro/hepatobiliary.py` of https://github.com/ethanprince4/AnatomyExplorer (commit
`d5f522fa51d6919b6a3fe28a9e075b531320a92a`) into `tools/blender/anatomy_1654623/lh_hepatobiliary.py`
and transformed once (mirror, metres, one translation; see `anatomy.json`
`portedCentrelineTransform`). The tube spline follows the source's `smooth_path`.

```
MIT License

Copyright (c) 2026 Ethan Prince

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 3. SurgeryCraft authored parts — MIT

Authored (labelled `authored` in `anatomy.json`): the `spleen` ellipsoid, the `cystic-plate` patch,
the gallbladder neck connector inside `gallbladder-infundibulum`, the adjusted proximal and distal
points of the `cystic-artery`, the abdominal-wall model, landmarks, ports and regions, the build and
verification scripts, materials and vertex colours.

```
MIT License

Copyright (c) 2026 SurgeryCraft contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Evaluated and not used

- **OrganUI gallbladder-3d** (based on BodyParts3D 4.3, CC BY-SA 2.1 JP): share-alike licence.
- **BodyVista** (Z-Anatomy based, CC BY-SA 4.0, with NC / research-only labels on parts):
  share-alike and unverified non-commercial / research-only labels.

No code, meshes or data from either were copied.
