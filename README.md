# SurgeryCraft

SurgeryCraft builds surgical training content on the
[ClinicalCraft](https://github.com/psknlr/ClinicalCraft) engine (the engine is archived here as
`ClinicalCraft-main (1).zip`). This repository is a ClinicalCraft **content pack**: plain JSON
that ClinicalCraft loads through its `contentDirs` setting, with no engine changes.

## The surgical floor · 手术部

![Operating department zoning](docs/img/surgical-floor-L1-zoning.png)

**SurgeryCraft Surgical Centre** (`surgical-centre`) is a two-storey facility whose first
floor is a full operating department designed around international OR practice:

* 8 ORs round a central sterile core: a **hybrid OR** with robotic angiography and its control
  room, a **robotic surgery** OR, two **Class I ultra-clean** laminar-flow ORs (cardiac &
  transplant, arthroplasty & neuro), three **integrated digital** ORs (one held 24/7 for
  emergency and obstetric surgery) and a **negative-pressure isolation** OR behind an
  interlocked anteroom;
* restricted / semi-restricted / unrestricted zoning enforced by access zones, one-way staff
  changing rooms, a patient transfer zone with a red line, scrub bays and sterile set-up rooms
  between the ORs, an 8-bay PACU and 5-bay pre-op holding;
* clean and dirty lifts to the ground-floor CSSD, which runs one way from decontamination to
  the sterile store; plus admissions, day surgery, the perioperative lab, blood bank and a
  surgical skills & simulation centre.

Design specification, standards basis, room schedule and screenshots:
**[docs/SURGICAL_FLOOR.md](docs/SURGICAL_FLOOR.md)**.

## Layout

```
content/
  catalogs/surgerycraft-or.json      47 equipment types, 21 materials (bilingual)
  templates/sc-*.json                15 room templates (ORs, scrub, set-up, PACU, pre-op, changing, …)
  facilities/surgical-centre.json    the two-storey surgical centre
docs/SURGICAL_FLOOR.md               design specification · docs/img/ figures
tools/check.sh                       validate the pack + navigation/zoning test against ClinicalCraft
tools/navcheck.test.ts               the navigation/zoning test (run by check.sh)
tools/content-gen/                   Python generator that writes content/ (python3 build.py)
```

## Use it with ClinicalCraft

Point ClinicalCraft at the pack, e.g. in `ClinicalCraft/.clinicalcraft/settings.local.json`
(git-ignored; a relative path resolves against the settings file's folder):

```json
{ "contentDirs": ["../../SurgeryCraft/content"] }
```

Then, from the ClinicalCraft checkout:

```bash
npm run cc -- facilities validate --all
```

```bash
npm run cc -- facilities compile surgical-centre
```

```bash
npm run cc -- serve
```

`serve` offers the pack to the web world (choose the *SurgeryCraft Surgical Centre*
facility). An operating-room case such as `cmcr-1653406` starts in OR 7.

## Check and regenerate

```bash
tools/check.sh ../ClinicalCraft
```

```bash
python3 tools/content-gen/build.py
```

The generator reads ClinicalCraft's built-in catalogs from `../ClinicalCraft` (or
`$CLINICALCRAFT_DIR`) for footprint checks and rewrites `content/` byte-for-byte.
