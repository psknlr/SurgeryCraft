# BodyParts3D source surfaces — licence

The `FJ*.obj` files in this directory are unmodified copies of entries of the DBCLS archive
`partof_BP3D_4.0_obj_99.zip` (BodyParts3D 4.0, PART-OF, 99 % reduction). File names, archive
entries, sizes and SHA-256 digests are listed in `sources.json`; they were fetched for the v3
handoff of SurgeryCraft case 126 (`fetch_anatomy_reference.py` in that package) and copied here
so that `tools/blender/build_anatomy_1654623.py` can be rebuilt from this repository alone.

**Attribution (required):**
BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.

- Licence: Creative Commons Attribution 4.0 International — https://creativecommons.org/licenses/by/4.0/
- Licence evidence (DBCLS): https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- Source archive: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip

Note: the comment header inside each OBJ file still carries the older notice
"Creative Commons Attribution-Share Alike 2.1 Japan". The CC BY 4.0 statement above is the one
recorded from the DBCLS licence page in `sources.json` by the v3 handoff; it could not be
re-checked from this build environment (no network access to dbarchive.biosciencedbc.jp).
Confirm the current DBCLS licence page before redistribution.

The files are reference anatomy of a single adult atlas body; they are not images or
reconstructions of any patient.
