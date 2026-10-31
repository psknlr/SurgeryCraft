"""
SurgeryCraft equipment models, written in each type's own frame (ClinicalCraft's
scripts/blender/clinicalcraft_shapes.py: metres, x right, y up, z front, origin at the
footprint centre on the floor) from its voxel parts: working heights, screens and the
surfaces things are put on stay where the world expects them. `build.py` runs them.
"""
from __future__ import annotations

import math

from clinicalcraft_shapes import Kit, rrect

#: type id -> builder(kit, equipment)
MODELS = {}


def model(type_id):
    def register(fn):
        MODELS[type_id] = fn
        return fn
    return register


def handle_bar(k: Kit, a, b, standoff, r=0.007, m="chrome"):
    """A bar handle from a to b held off a face by `standoff` (towards +z of the frame)."""
    k.tube(a, b, r, m, seg=12)
    for p in (a, b):
        k.tube((p[0], p[1], p[2] - standoff), p, r * 0.8, m, seg=10)


def gas_outlet(k: Kit, x, y, z, colour, plate="white"):
    """A wall-type medical gas outlet facing +z: plate, coloured collar, socket."""
    k.box((x, y, z + 0.004), (0.07, 0.07, 0.008), plate, r=0.008, seg=2)
    k.torus((x, y, z + 0.011), 0.016, 0.005, colour, axis="z", seg=20, ring=8)
    k.cyl((x, y, z + 0.009), 0.011, 0.008, "coal", axis="z", seg=16)


# ------------------------------------------------------------------------------------------------
# set-up and Mayo
# ------------------------------------------------------------------------------------------------

@model("sc-sterile-setup-table")
def setup_table(k: Kit, eq):
    """Back table: four legs on casters, a lower shelf, a steel top under a sterile drape (top at 0.90 m)."""
    for x in (-0.52, 0.52):
        for z in (-0.22, 0.22):
            k.caster(x, z, r=0.035, stem=0.02)
            k.tube((x, 0.09, z), (x, 0.862, z), 0.016, "chrome", seg=16)
    k.slab(rrect(1.08, 0.48, 0.02), 0.248, 0.016, "steel", r=0.004)
    for z in (-0.234, 0.234):
        k.box((0, 0.276, z), (1.06, 0.024, 0.008), "steel", r=0.003, seg=2)
    for x in (-0.534, 0.534):
        k.box((x, 0.276, 0), (0.008, 0.024, 0.46), "steel", r=0.003, seg=2)
    for z in (-0.22, 0.22):
        k.box((0, 0.846, z), (1.02, 0.03, 0.022), "chrome", r=0.004, seg=2)
    for x in (-0.52, 0.52):
        k.box((x, 0.846, 0), (0.022, 0.03, 0.42), "chrome", r=0.004, seg=2)
    k.box((0, 0.873, 0), (1.14, 0.024, 0.52), "steel", r=0.006)
    # the drape: over the top and hanging down every side, flared a little like cloth
    k.slab(rrect(1.172, 0.572, 0.018), 0.885, 0.015, "sc-drape", r=0.004)
    drop = 0.22
    for z, tilt in ((0.284, 4), (-0.284, -4)):
        k.box((0, 0.892 - drop / 2, z + math.copysign(drop / 2 * math.sin(math.radians(4)), z)), (1.17, drop, 0.006), "sc-drape", r=0.002, seg=1, rot=(tilt, 0, 0))
    for x, tilt in ((0.584, -4), (-0.584, 4)):
        k.box((x + math.copysign(drop / 2 * math.sin(math.radians(4)), x), 0.892 - drop / 2, 0), (0.006, drop, 0.57), "sc-drape", r=0.002, seg=1, rot=(0, 0, tilt))


@model("sc-mayo-stand")
def mayo_stand(k: Kit, eq):
    """Mayo stand: an L base on three casters, a telescopic post with a clamp knob, the tray on its frame,
    a drape and the instruments laid out for the case."""
    cr = 0.025
    by = 2 * cr + 0.02 + 0.016
    k.box((0.015, by, 0.17), (0.51, 0.032, 0.045), "chrome", r=0.008)
    k.box((-0.22, by, -0.01), (0.045, 0.032, 0.40), "chrome", r=0.008)
    for x, z in ((-0.22, -0.19), (-0.22, 0.17), (0.25, 0.17)):
        k.caster(x, z, r=cr, stem=0.02)
    px, pz = -0.22, -0.12
    k.cyl((px, by + 0.02, pz), 0.034, 0.03, "chrome", bevel=0.006)
    k.cyl((px, 0.44, pz), 0.022, 0.68, "chrome", seg=20)
    k.cyl((px, 0.79, pz), 0.03, 0.04, "sc-matte-black", seg=20, bevel=0.006)
    k.cyl((px + 0.045, 0.79, pz), 0.008, 0.05, "chrome", axis="x", seg=10)
    k.ball((px + 0.075, 0.79, pz), 0.016, "sc-matte-black", seg=14)
    k.cyl((px, 0.94, pz), 0.016, 0.30, "chrome", seg=16)
    # tray frame and tray
    for z in (-0.16, 0.20):
        k.box((-0.04, 1.096, z), (0.46, 0.014, 0.016), "chrome", r=0.003, seg=2)
    for x in (-0.26, 0.18):
        k.box((x, 1.096, 0.02), (0.016, 0.014, 0.37), "chrome", r=0.003, seg=2)
    k.box((-0.04, 1.114, 0.02), (0.5, 0.022, 0.42), "steel", r=0.006)
    # drape over the tray, its front edge falling towards the surgeon
    k.slab(rrect(0.54, 0.46, 0.02), 1.125, 0.007, "sc-drape", at=(-0.04, 0, 0.02), r=0.002)
    k.box((-0.04, 1.06, 0.254), (0.54, 0.14, 0.005), "sc-drape", r=0.002, seg=1, rot=(6, 0, 0))
    # instruments: three ring instruments, a pair of forceps, a folded swab
    top = 1.132
    for x in (-0.19, -0.11, -0.03):
        k.slab([(x - 0.003, -0.07), (x + 0.003, -0.07), (x + 0.0015, 0.13), (x - 0.0015, 0.13)], top, 0.004, "chrome")
        for dz in (-0.012, 0.012):
            k.torus((x + dz, top + 0.002, -0.09), 0.009, 0.002, "chrome", seg=16, ring=6)
    k.slab([(0.05, -0.08), (0.062, -0.08), (0.058, 0.1), (0.054, 0.1)], top, 0.004, "chrome")
    k.box((0.14, top + 0.012, -0.08), (0.12, 0.024, 0.1), "paper", r=0.008, seg=2)


# ------------------------------------------------------------------------------------------------
# anaesthesia
# ------------------------------------------------------------------------------------------------

@model("sc-anaesthesia-workstation")
def anaesthesia_workstation(k: Kit, eq):
    """Anaesthesia workstation: cabinet with drawers on casters, cylinders at the back, the work surface,
    the ventilator housing with flowmeters, two vaporisers on their rail, the CO2 absorber, the breathing
    circuit with bag and mask, and the patient monitor on its post (its screen is the world's live display)."""
    for x in (-0.42, 0.42):
        for z in (-0.345, 0.345):
            k.caster(x, z, r=0.04, stem=0.02)
    k.box((0, 0.47, -0.055), (0.84, 0.74, 0.55), "plastic", r=0.03)
    for y in (0.28, 0.54):
        k.box((0, y, 0.226), (0.76, 0.235, 0.02), "white", r=0.008)
        handle_bar(k, (-0.12, y + 0.07, 0.252), (0.12, y + 0.07, 0.252), 0.016)
    for x, colour in ((-0.22, "oxygen-green"), (0.22, "blue")):
        k.cyl((x, 0.5, -0.378), 0.045, 0.56, colour, seg=20, bevel=0.02)
        k.cyl((x, 0.80, -0.378), 0.018, 0.05, "chrome", seg=12)
        k.box((x, 0.6, -0.34), (0.11, 0.03, 0.04), "steel", r=0.006, seg=2)
    # work surface with side rails
    k.box((0, 0.87, -0.03), (0.92, 0.035, 0.74), "steel", r=0.01)
    for x in (-0.475, 0.475):
        k.tube((x, 0.90, -0.34), (x, 0.90, 0.30), 0.011, "chrome", seg=12)
        for z in (-0.32, 0.28):
            k.tube((x * 0.97, 0.90, z), (x, 0.90, z), 0.008, "chrome", seg=10)
    # ventilator housing
    k.box((0, 1.26, -0.2), (0.74, 0.74, 0.36), "plastic", r=0.035)
    k.box((0, 1.64, -0.2), (0.76, 0.02, 0.38), "steel", r=0.006, seg=2)
    k.box((-0.15, 1.12, -0.012), (0.36, 0.27, 0.02), "coal", r=0.012)
    k.box((-0.15, 1.12, -0.002), (0.31, 0.22, 0.004), k.paint("vent-display", "screen-dark", emissiveIntensity=0.6), r=0.002, seg=1)
    for i, colour in enumerate(("oxygen-green", "sc-gas-n2o", "sc-gas-air")):
        x = 0.07 + 0.075 * i
        k.box((x, 1.13, -0.017), (0.05, 0.2, 0.008), "lead-glass", r=0.004, seg=1)
        k.cyl((x, 1.0, -0.008), 0.016, 0.03, colour, axis="z", seg=16, bevel=0.004)
    k.cyl((0.28, 1.12, -0.008), 0.028, 0.026, "coal", axis="z", seg=24, bevel=0.006)
    k.cyl((0.28, 1.25, -0.012), 0.014, 0.02, "oxygen-green", axis="z", seg=16)
    # vaporisers on their rail
    k.box((0.19, 1.33, -0.01), (0.32, 0.03, 0.03), "chrome", r=0.006, seg=2)
    for x, colour in ((0.12, "yellow"), (0.26, "purple")):
        k.box((x, 1.42, 0.04), (0.105, 0.19, 0.12), colour, r=0.016)
        k.cyl((x, 1.535, 0.04), 0.038, 0.03, "coal", seg=24, bevel=0.006)
        k.box((x, 1.556, 0.04), (0.012, 0.012, 0.05), "white", r=0.004, seg=1)
        k.box((x, 1.42, 0.101), (0.05, 0.06, 0.004), "white", r=0.004, seg=1)
    # CO2 absorber on the left
    k.box((-0.385, 1.24, -0.05), (0.06, 0.06, 0.1), "plastic", r=0.01)
    k.cyl((-0.42, 1.235, -0.05), 0.066, 0.04, "plastic", seg=24, bevel=0.008)
    k.cyl((-0.42, 1.10, -0.05), 0.06, 0.23, "lead-glass", seg=24)
    k.cyl((-0.42, 1.09, -0.05), 0.052, 0.18, "purple", seg=20)
    k.cyl((-0.42, 0.98, -0.05), 0.064, 0.02, "coal", seg=24, bevel=0.005)
    # breathing circuit: two limbs to a Y-piece and mask on the work surface; reservoir bag on its arm
    k.path([(-0.39, 1.215, 0.0), (-0.39, 1.06, 0.07), (-0.38, 0.935, 0.17), (-0.37, 0.93, 0.29)], 0.016, "clin-hose-blue", seg=12)
    k.path([(-0.45, 1.215, -0.02), (-0.455, 1.02, 0.06), (-0.42, 0.93, 0.19), (-0.37, 0.93, 0.29)], 0.016, "clin-hose-blue", seg=12)
    k.cyl((-0.37, 0.93, 0.31), 0.018, 0.04, "lead-glass", axis="z", seg=14)
    k.ball((-0.37, 0.925, 0.355), 0.055, "black", seg=18, squash=(1.0, 0.55, 0.75))
    k.tube((-0.29, 1.15, -0.02), (-0.29, 1.15, 0.05), 0.008, "chrome")
    k.ball((-0.29, 1.03, 0.06), 0.05, "rubber", seg=18, squash=(0.9, 1.6, 0.9))
    # patient monitor on its post: housing and bezel behind the live screen
    scr = eq.screens()[0]
    k.cyl((0.3, 1.69, -0.2), 0.022, 0.09, "chrome", seg=16)
    k.box((0.3, 1.74, -0.19), (0.07, 0.05, 0.06), "plastic", r=0.012)
    k.box((0.18, 1.86, -0.148), (0.62, 0.36, 0.084), "plastic", r=0.022)
    k.screen_bezel(scr, "coal", border=0.02, depth=0.012, r=0.006)
    handle_bar(k, (0.0, 2.035, -0.15), (0.36, 2.035, -0.15), 0.0, r=0.008, m="plastic")


def pendant_column(k: Kit, drop_z: float):
    """A ceiling pendant's flange, column, arm and drop post down to a head top at 2.26 m."""
    k.cyl((0, 4.97, -0.22), 0.26, 0.06, "plastic", seg=40, bevel=0.015)
    k.cyl((0, 4.18, -0.22), 0.07, 1.52, "chrome", seg=28)
    k.cyl((0, 3.45, -0.22), 0.1, 0.1, "plastic", seg=32, bevel=0.02)
    k.box((0, 3.36, -0.02), (0.24, 0.14, 0.64), "plastic", r=0.05)
    k.cyl((0, 3.27, drop_z), 0.09, 0.06, "plastic", seg=32, bevel=0.015)
    k.cyl((0, 2.78, drop_z), 0.055, 0.92, "chrome", seg=24)
    k.cyl((0, 2.29, drop_z), 0.08, 0.06, "plastic", seg=32, bevel=0.015)


def service_head(k: Kit):
    """The service head: column 0.94–2.26 m with an accent band, a status light and side rails."""
    k.box((0, 1.6, 0), (0.44, 1.32, 0.42), "plastic", r=0.04)
    k.box((0, 2.18, 0), (0.452, 0.034, 0.432), "sc-robot-accent", r=0.012, seg=2)
    k.box((0, 2.215, 0.212), (0.12, 0.012, 0.006), "led-green", r=0.003, seg=1)
    for x in (-0.224, 0.224):
        k.box((x, 1.55, 0.13), (0.012, 1.1, 0.03), "steel", r=0.003, seg=1)
        for y in (1.3, 1.42):
            k.box((x, y, -0.05), (0.012, 0.065, 0.09), "coal", r=0.006, seg=1)


def pendant_shelf(k: Kit, top: float):
    """A pendant shelf (top surface at `top`) with a front rail."""
    k.slab(rrect(0.74, 0.54, 0.03), top - 0.026, 0.026, "steel", at=(0, 0, 0.12), r=0.005)
    k.tube((-0.35, top + 0.012, 0.392), (0.35, top + 0.012, 0.392), 0.008, "chrome", seg=12)
    for x in (-0.35, 0.35):
        k.tube((x, top, 0.392), (x, top + 0.012, 0.392), 0.008, "chrome", seg=10)


@model("sc-surgical-pendant")
def surgical_pendant(k: Kit, eq):
    """Surgical pendant: ceiling column, arm and drop post; the service head with gas outlets and sockets;
    two shelves carrying the electrosurgical generator (its screen is the world's display) and a second unit."""
    pendant_column(k, 0.12)
    service_head(k)
    for x, colour in ((-0.1, "oxygen-green"), (0.1, "yellow")):
        gas_outlet(k, x, 1.38, 0.21, colour)
    pendant_shelf(k, 1.035)
    pendant_shelf(k, 1.635)
    for y in (1.13, 1.73):
        k.box((0, y, 0.17), (0.62, 0.18, 0.44), "sc-robot", r=0.022)
        k.box((0, y - 0.088, 0.17), (0.6, 0.006, 0.42), "coal", r=0.002, seg=1)
    scr = eq.screens()[0]
    k.screen_bezel(scr, "coal", border=0.012, depth=0.01, r=0.004)
    for x, colour in ((0.14, "blue"), (0.24, "yellow")):
        k.cyl((x, 1.1, 0.392), 0.02, 0.012, colour, axis="z", seg=18, bevel=0.004)
        k.cyl((x, 1.165, 0.392), 0.012, 0.01, "coal", axis="z", seg=14)
    k.box((-0.1, 1.73, 0.392), (0.3, 0.1, 0.008), "coal", r=0.006, seg=1)
    k.box((-0.1, 1.73, 0.396), (0.27, 0.075, 0.004), "screen-dark", r=0.002, seg=1)
    k.box((0.18, 1.75, 0.394), (0.06, 0.03, 0.006), "led-green", r=0.004, seg=1)
    k.cyl((0.18, 1.69, 0.392), 0.016, 0.012, "coal", axis="z", seg=16)


@model("sc-anaesthesia-pendant")
def anaesthesia_pendant(k: Kit, eq):
    """Anaesthesia pendant: the same column and head with the full row of gas outlets (O2, air, N2O,
    vacuum, AGSS), a suction regulator and canister, and a monitoring module on the upper shelf."""
    pendant_column(k, 0.12)
    service_head(k)
    for x, colour in ((-0.15, "oxygen-green"), (-0.05, "sc-gas-air"), (0.05, "sc-gas-n2o"), (0.15, "yellow")):
        gas_outlet(k, x, 1.26, 0.21, colour)
    gas_outlet(k, 0, 1.38, 0.21, "sc-gas-agss")
    k.box((0, 1.13, 0.218), (0.3, 0.05, 0.016), "coal", r=0.006, seg=1)
    pendant_shelf(k, 1.035)
    pendant_shelf(k, 1.635)
    # suction regulator under the lower shelf and its canister
    k.box((0.27, 0.985, 0.22), (0.07, 0.04, 0.06), "steel", r=0.008, seg=2)
    k.cyl((0.27, 1.06, 0.205), 0.022, 0.05, "chrome", axis="z", seg=16)
    k.cyl((0.27, 0.86, 0.3), 0.058, 0.25, "lead-glass", seg=24)
    k.cyl((0.27, 0.80, 0.3), 0.054, 0.12, "paper", seg=20)
    k.cyl((0.27, 0.995, 0.3), 0.064, 0.026, "blue", seg=24, bevel=0.006)
    k.path([(0.27, 1.01, 0.3), (0.27, 1.05, 0.28), (0.27, 1.06, 0.235)], 0.006, "lead-glass", seg=8)
    # monitoring module on the upper shelf
    k.box((-0.18, 1.74, 0.18), (0.3, 0.2, 0.26), "coal", r=0.016)
    k.box((-0.18, 1.74, 0.312), (0.12, 0.03, 0.006), "led-amber", r=0.004, seg=1)
    for i in range(4):
        k.cyl((-0.29 + 0.04 * i, 1.68, 0.312), 0.008, 0.008, "steel", axis="z", seg=12)


@model("sc-ceiling-display")
def ceiling_display(k: Kit, eq):
    """Ceiling-boom display: flange, drop column, hub and yoke; a slim monitor with sterile handles
    (its screen is the world's display)."""
    k.cyl((0, 4.97, 0), 0.18, 0.06, "plastic", seg=36, bevel=0.012)
    k.cyl((0, 3.79, 0), 0.055, 2.30, "chrome", seg=24)
    k.cyl((0, 2.6, 0), 0.085, 0.12, "plastic", seg=32, bevel=0.02)
    k.box((0, 2.52, 0.04), (0.06, 0.1, 0.06), "chrome", r=0.012)
    k.box((0, 2.42, 0.07), (0.22, 0.16, 0.03), "sc-matte-black", r=0.008)
    k.box((0, 2.1, 0.12), (1.4, 0.82, 0.07), "sc-matte-black", r=0.02)
    k.screen_bezel(eq.screens()[0], "sc-matte-black", border=0.03, depth=0.012, r=0.006)
    k.box((0.6, 1.72, 0.168), (0.04, 0.012, 0.004), "led-blue", r=0.002, seg=1)
    handle_bar(k, (-0.3, 1.655, 0.15), (0.3, 1.655, 0.15), 0.0, r=0.012, m="plastic")
    for x in (-0.3, 0.3):
        k.tube((x, 1.69, 0.12), (x, 1.655, 0.15), 0.01, "plastic", seg=10)


# ------------------------------------------------------------------------------------------------
# carts and units
# ------------------------------------------------------------------------------------------------

@model("sc-forced-air-warmer")
def forced_air_warmer(k: Kit, eq):
    """Forced-air warming unit on a four-leg rolling stand: blower with display and controls, carry
    handle, side intake grilles and the warming hose hanging in a loop."""
    for x in (-0.175, 0.175):
        for z in (-0.175, 0.175):
            k.caster(x, z, r=0.03, stem=0.015)
            k.tube((0, 0.095, -0.02), (x, 0.085, z), 0.014, "plastic", seg=12)
    k.cyl((0, 0.095, -0.02), 0.04, 0.04, "plastic", seg=24, bevel=0.01)
    k.cyl((0, 0.44, -0.02), 0.017, 0.68, "chrome", seg=16)
    k.box((0, 0.92, 0), (0.36, 0.3, 0.32), "plastic", r=0.05)
    k.box((0, 0.785, 0), (0.30, 0.012, 0.26), "coal", r=0.004, seg=1)
    k.screen_bezel(eq.screens()[0], "coal", border=0.014, depth=0.008, r=0.004)
    for x in (-0.08, -0.02, 0.04):
        k.cyl((x, 0.88, 0.158), 0.013, 0.01, "coal", axis="z", seg=16, bevel=0.003)
    k.box((0.12, 0.88, 0.161), (0.05, 0.03, 0.006), "led-amber", r=0.004, seg=1)
    for x in (-0.181, 0.181):
        for i in range(4):
            k.box((x, 0.86 + 0.05 * i, 0.0), (0.006, 0.012, 0.2), "coal", r=0.003, seg=1)
    k.path([(-0.09, 1.07, -0.06), (-0.09, 1.11, -0.06), (0.09, 1.11, -0.06), (0.09, 1.07, -0.06)], 0.011, "chrome", seg=12)
    # the hose: down from the outlet and coiled once round the pole, its nozzle clipped to the pole
    k.cyl((0, 0.765, 0.11), 0.034, 0.03, "clin-hose-blue", seg=20)
    hose = [(0, 0.75, 0.11), (0, 0.68, 0.125)]
    for i in range(15):
        a = math.radians(90 + 330 * i / 14)
        hose.append((0.135 * math.cos(a), 0.62 - 0.12 * i / 14, -0.02 + 0.13 * math.sin(a)))
    k.path(hose, 0.026, "clin-hose-blue", seg=14)
    k.cyl((0.04, 0.5, -0.07), 0.03, 0.05, "plastic", axis="x", seg=16)


@model("sc-smoke-evacuator")
def smoke_evacuator(k: Kit, eq):
    """Smoke evacuator: a white cabinet on a rubber plinth, control panel with display, the hose port
    and status light, a filter door with its handle and side vents."""
    k.box((0, 0.02, 0), (0.4, 0.04, 0.34), "rubber", r=0.01, seg=2)
    k.box((0, 0.42, 0), (0.44, 0.76, 0.38), "white", r=0.035)
    k.box((0, 0.812, 0), (0.42, 0.024, 0.36), "plastic", r=0.01)
    k.box((0, 0.68, 0.188), (0.38, 0.2, 0.01), "plastic", r=0.012, seg=2)
    k.screen_bezel(eq.screens()[0], "coal", border=0.014, depth=0.008, r=0.004)
    k.torus((0.12, 0.62, 0.196), 0.028, 0.009, "blue", axis="z", seg=24, ring=8)
    k.cyl((0.12, 0.62, 0.192), 0.02, 0.008, "coal", axis="z", seg=18)
    k.box((0.12, 0.74, 0.196), (0.04, 0.02, 0.006), "led-green", r=0.004, seg=1)
    k.box((0, 0.3, 0.19), (0.38, 0.4, 0.008), "white", r=0.012, seg=2)
    handle_bar(k, (-0.1, 0.48, 0.206), (0.1, 0.48, 0.206), 0.012, r=0.006)
    for x in (-0.221, 0.221):
        for i in range(5):
            k.box((x, 0.2 + 0.045 * i, 0), (0.006, 0.014, 0.24), "coal", r=0.003, seg=1)


@model("sc-difficult-airway-trolley")
def difficult_airway_trolley(k: Kit, eq):
    """Difficult airway trolley: colour-coded drawers on a rolling cabinet with a push handle, a railed
    top with the video-laryngoscope screen on its pole (the world's display), its case, a laryngoscope
    and a pouch."""
    for x in (-0.315, 0.315):
        for z in (-0.215, 0.215):
            k.caster(x, z, r=0.04, stem=0.02)
    k.box((0, 0.52, 0), (0.7, 0.84, 0.5), "plastic", r=0.025)
    for y, colour in ((0.82, "green"), (0.62, "yellow"), (0.42, "orange"), (0.22, "ambulance-red")):
        k.box((0, y, 0.254), (0.64, 0.17, 0.012), colour, r=0.01)
        handle_bar(k, (-0.1, y + 0.05, 0.272), (0.1, y + 0.05, 0.272), 0.012, r=0.006)
        k.box((0.22, y - 0.02, 0.261), (0.1, 0.05, 0.002), "white", r=0.003, seg=1)
    k.box((0, 0.96, 0), (0.74, 0.04, 0.54), "steel", r=0.01)
    k.path([(-0.355, 0.98, 0.25), (-0.355, 1.02, 0.25), (-0.355, 1.02, -0.255), (0.355, 1.02, -0.255), (0.355, 1.02, 0.25), (0.355, 0.98, 0.25)], 0.008, "chrome", seg=10)
    k.path([(0.35, 0.86, -0.17), (0.385, 0.86, -0.17), (0.385, 0.86, 0.17), (0.35, 0.86, 0.17)], 0.012, "chrome", seg=12)
    k.cyl((-0.25, 1.17, -0.15), 0.012, 0.38, "chrome", seg=14)
    scr = eq.screens()[0]
    k.box((-0.25, 1.42, -0.128), (0.22, 0.16, 0.044), "plastic", r=0.012)
    k.screen_bezel(scr, "coal", border=0.01, depth=0.008, r=0.004)
    k.box((0.15, 1.04, 0.05), (0.12, 0.12, 0.3), "coal", r=0.02)
    k.box((0.0, 1.0, 0.1), (0.12, 0.04, 0.16), "purple", r=0.015)
    k.cyl((-0.12, 0.995, 0.14), 0.014, 0.13, "chrome", axis="z", seg=16, bevel=0.003)
    k.path([(-0.12, 0.995, 0.205), (-0.12, 1.0, 0.22), (-0.12, 0.99, 0.29)], 0.005, "chrome", seg=8)


@model("sc-laparoscopy-tower")
def laparoscopy_tower(k: Kit, eq):
    """Laparoscopy tower: a four-post cart with shelves carrying the camera control unit, light source,
    insufflator and recorder, and the 4K monitor on its arm (its screen is the world's display)."""
    for x in (-0.315, 0.315):
        for z in (-0.29, 0.29):
            k.caster(x, z, r=0.04, stem=0.02)
    k.box((0, 0.15, 0), (0.7, 0.06, 0.64), "plastic", r=0.02)
    for x in (-0.32, 0.32):
        for z in (-0.28, 0.28):
            k.cyl((x, 0.92, z), 0.019, 1.48, "chrome", seg=16)
    for y in (0.42, 0.72, 1.02, 1.32):
        k.slab(rrect(0.68, 0.62, 0.025), y - 0.015, 0.03, "steel", r=0.004)
    k.slab(rrect(0.7, 0.64, 0.03), 1.655, 0.02, "plastic", r=0.005)
    units = (
        (0.52, (("led-blue", 0.18),)),
        (0.82, (("led-blue", 0.18),)),
        (1.12, (("oxygen-green", -0.18), ("led-amber", 0.15))),
        (1.40, ()),
    )
    for i, (y, lights) in enumerate(units):
        hgt = 0.12 if i == 3 else 0.16
        k.box((0, y, 0), (0.6, hgt, 0.5), "plastic", r=0.015)
        k.box((0, y, 0.251), (0.56, hgt - 0.03, 0.004), "sc-matte-black", r=0.006, seg=1)
        for m, x in lights:
            k.box((x, y, 0.255), (0.1, 0.03, 0.006), m, r=0.004, seg=1)
        k.cyl((-0.2, y, 0.256), 0.018, 0.01, "steel", axis="z", seg=16)
    k.torus((-0.05, 0.82, 0.258), 0.02, 0.006, "steel", axis="z", seg=18, ring=8)
    k.cyl((0, 1.71, -0.05), 0.022, 0.1, "steel", seg=16)
    k.box((0, 1.78, -0.03), (0.16, 0.12, 0.04), "steel", r=0.01)
    k.box((0, 1.86, 0.02), (0.72, 0.44, 0.06), "sc-matte-black", r=0.016)
    k.screen_bezel(eq.screens()[0], "sc-matte-black", border=0.02, depth=0.01, r=0.004)


# ------------------------------------------------------------------------------------------------
# the hybrid table
# ------------------------------------------------------------------------------------------------

@model("sc-hybrid-table")
def hybrid_table(k: Kit, eq):
    """Hybrid OR table: floor plate and column, the floating carbon-fibre top on its cradle with
    segmented pads and headrest, side rails, arm boards, the anaesthesia screen with its drape, the
    lead skirt hanging from the rail and the handset."""
    k.box((0, 0.04, 0.85), (0.6, 0.08, 1.1), "plastic", r=0.03)
    k.box((0, 0.4, 0.85), (0.38, 0.64, 0.46), "sc-robot", r=0.06)
    k.box((0, 0.46, 1.083), (0.3, 0.04, 0.006), "sc-robot-accent", r=0.004, seg=1)
    k.box((0, 0.755, 0.7), (0.5, 0.06, 0.8), "steel", r=0.015)
    k.slab(rrect(0.56, 3.12, 0.05), 0.79, 0.055, "sc-carbon", r=0.01)
    for z, length, width in ((-0.65, 1.1, 0.52), (0.3, 0.72, 0.52), (1.05, 0.66, 0.52)):
        k.box((0, 0.885, z), (width, 0.07, length - 0.012), "navy", r=0.025)
    k.slab(rrect(0.3, 0.3, 0.12), 0.85, 0.07, "navy", at=(0, 0, -1.4), r=0.025)
    for x in (-0.29, 0.29):
        k.box((x, 0.83, -0.2), (0.012, 0.03, 2.6), "chrome", r=0.004, seg=2)
        for z in (-1.4, -0.2, 1.0):
            k.box((x * 0.97, 0.83, z), (0.02, 0.02, 0.03), "chrome", r=0.003, seg=1)
    for x in (-0.43, 0.43):
        k.slab(rrect(0.28, 0.14, 0.05), 0.808, 0.024, "steel", at=(x, 0, -0.95), r=0.004)
        k.slab(rrect(0.25, 0.15, 0.06), 0.832, 0.05, "navy", at=(x + (0.01 if x > 0 else -0.01), 0, -0.95), r=0.018)
    k.path([(-0.3, 0.84, -1.12), (-0.3, 1.235, -1.12), (0.3, 1.235, -1.12), (0.3, 0.84, -1.12)], 0.0125, "chrome", seg=12)
    k.box((0, 1.08, -1.12), (0.58, 0.3, 0.008), "sc-drape", r=0.003, seg=1)
    for i in range(7):
        z = -0.88 + i * 0.23
        k.box((0.3 + (0.006 if i % 2 else 0), 0.55, z), (0.016, 0.5, 0.24), "sc-lead-rubber", r=0.006, seg=2)
    k.box((0.3, 0.81, -0.1), (0.03, 0.03, 1.64), "chrome", r=0.006, seg=2)
    k.box((-0.3, 0.68, 0.55), (0.05, 0.16, 0.04), "coal", r=0.012)
    k.box((-0.3, 0.73, 0.572), (0.03, 0.02, 0.004), "led-blue", r=0.003, seg=1)
    k.path([(-0.3, 0.6, 0.55), (-0.31, 0.55, 0.58), (-0.3, 0.6, 0.62), (-0.29, 0.83, 0.62)], 0.004, "coal", seg=8)


# ------------------------------------------------------------------------------------------------
# instruments and small items (handheld: lying flat on the set-up table, the tip towards +x)
# ------------------------------------------------------------------------------------------------

def strip(x0: float, x1: float, centre, width, n: int = 12):
    """Outline (x, z) of a strip from x0 to x1 whose centre line and width are functions of t in [0, 1]."""
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        c, w = centre(t), width(t)
        left.append((x, c + w / 2))
        right.append((x, c - w / 2))
    return left + right[::-1]


def finger_rings(k: Kit, x: float, m: str, spread: float = 0.013, y: float = 0.0022):
    """The two finger rings of a ring-handled instrument, flat on the table."""
    for z in (-spread, spread):
        k.torus((x, y, z), 0.0085, 0.0022, m, seg=20, ring=8, stretch=(1.25, 1))


def ring_shanks(k: Kit, x_ring: float, x_joint: float, m: str, spread: float = 0.013, thick: float = 0.0036):
    """The two shanks from the rings to the joint, crossing there."""
    for sgn in (-1, 1):
        k.slab(strip(x_ring + 0.006, x_joint, lambda t, s=sgn: s * spread * (1 - t) * 0.92, lambda t: 0.0048 - 0.0012 * t), 0.0004, thick, "chrome", r=0.0008, seg=1)


@model("sc-scalpel")
def scalpel(k: Kit, eq):
    """Safety scalpel: a No. 3 handle with a grip, the retractable shield (pushed back) and a No. 10 blade."""
    k.slab(strip(-0.078, 0.032, lambda t: 0, lambda t: 0.0095 - 0.003 * t), 0.0, 0.0028, "steel", r=0.0009, seg=1)
    for i in range(7):
        k.box((-0.062 + 0.0045 * i, 0.003, 0), (0.0018, 0.0008, 0.007), "steel", r=0.0003, seg=1)
    k.box((0.012, 0.0045, 0), (0.045, 0.009, 0.0155), "sc-robot-accent", r=0.003)
    k.box((0.01, 0.0095, 0), (0.008, 0.002, 0.006), "white", r=0.0008, seg=1)
    blade = [(0.03, 0.0032), (0.062, 0.0032), (0.074, 0.0026), (0.0805, 0.0016), (0.08, 0.0004),
             (0.074, -0.0024), (0.066, -0.0042), (0.056, -0.0052), (0.044, -0.0052), (0.034, -0.004), (0.03, -0.0028)]
    k.slab(blade, 0.0012, 0.0006, "chrome")


@model("sc-needle-holder")
def needle_holder(k: Kit, eq):
    """Mayo-Hegar needle holder: gold rings (tungsten-carbide), shanks, ratchet, box joint and short jaws."""
    finger_rings(k, -0.07, "gold")
    ring_shanks(k, -0.07, 0.045, "chrome")
    for sgn in (-1, 1):
        k.box((-0.054, 0.0026, sgn * 0.004), (0.012, 0.004, 0.004), "steel", r=0.0008, seg=1)
    k.box((0.045, 0.003, 0), (0.012, 0.006, 0.0095), "chrome", r=0.0015, seg=2)
    k.cyl((0.045, 0.0064, 0), 0.0022, 0.0012, "steel", seg=12)
    k.slab(strip(0.05, 0.088, lambda t: 0, lambda t: 0.0068 - 0.0035 * t), 0.0008, 0.0046, "chrome", r=0.0008, seg=1)
    k.box((0.078, 0.0055, 0), (0.016, 0.0008, 0.0038), "gold", r=0.0002, seg=1)


@model("sc-tissue-forceps")
def tissue_forceps(k: Kit, eq):
    """DeBakey forceps: two spring legs joined at the back, a ribbed grip, fine atraumatic tips."""
    k.box((-0.073, 0.0018, 0), (0.014, 0.0036, 0.012), "steel", r=0.001, seg=2)
    for sgn in (-1, 1):
        k.slab(strip(-0.068, 0.078, lambda t, s=sgn: s * (0.0034 + 0.0042 * math.sin(math.pi * min(t * 1.4, 1)) * (1 - t)), lambda t: 0.0055 - 0.0037 * t), 0.0004, 0.0024, "chrome", r=0.0006, seg=1)
        for i in range(6):
            x = -0.03 + 0.005 * i
            t = (x + 0.068) / 0.146
            k.box((x, 0.003, sgn * (0.0034 + 0.0042 * math.sin(math.pi * min(t * 1.4, 1)) * (1 - t))), (0.0014, 0.0006, 0.004), "steel", r=0.0002, seg=1)


@model("sc-metzenbaum-scissors")
def metzenbaum_scissors(k: Kit, eq):
    """Curved Metzenbaum scissors: black rings (tungsten-carbide edges), shanks, the pivot and two
    curved blades, closed."""
    finger_rings(k, -0.066, "sc-matte-black")
    ring_shanks(k, -0.066, 0.02, "chrome")
    k.cyl((0.02, 0.0045, 0), 0.0032, 0.0016, "steel", seg=14)
    curve = lambda t: 0.004 * t * t
    k.slab(strip(0.012, 0.088, curve, lambda t: 0.0072 - 0.0042 * t), 0.0004, 0.0018, "chrome", r=0.0005, seg=1)
    k.slab(strip(0.012, 0.087, curve, lambda t: 0.0066 - 0.0040 * t), 0.0022, 0.0018, "chrome", r=0.0005, seg=1)
    k.ball((0.088, 0.0022, curve(1)), 0.0016, "chrome", seg=10)


@model("sc-artery-forceps")
def artery_forceps(k: Kit, eq):
    """Curved Kelly artery forceps: rings, shanks, the ratchet, a box lock and serrated curved jaws."""
    finger_rings(k, -0.06, "steel")
    ring_shanks(k, -0.06, 0.022, "chrome")
    for sgn in (-1, 1):
        for i in range(3):
            k.box((-0.047 + 0.003 * i, 0.0026, sgn * 0.0042), (0.0018, 0.004, 0.0035), "steel", r=0.0004, seg=1)
    k.box((0.022, 0.003, 0), (0.011, 0.006, 0.009), "chrome", r=0.0015, seg=2)
    curve = lambda t: 0.006 * t * t
    k.slab(strip(0.026, 0.078, curve, lambda t: 0.0055 - 0.003 * t), 0.0008, 0.0042, "chrome", r=0.0008, seg=1)
    for i in range(8):
        t = (i + 0.5) / 8
        k.box((0.028 + 0.05 * t, 0.0052, curve(t)), (0.0012, 0.0006, 0.0045 - 0.0025 * t), "steel", r=0.0002, seg=1)


@model("sc-esu-pencil")
def esu_pencil(k: Kit, eq):
    """Electrosurgical pencil: the handpiece with cut (yellow) and coag (blue) buttons, the clear
    smoke-evacuation shroud, the blade electrode and the cable."""
    body = [(0.0, -0.098), (0.0045, -0.097), (0.0068, -0.09), (0.0074, -0.05), (0.0072, 0.0), (0.0062, 0.03), (0.0055, 0.036), (0.0, 0.037)]
    k.lathe(body, (0, 0.0075, 0), "white", axis="x", seg=20)
    k.lathe([(0.0, 0.028), (0.0084, 0.03), (0.009, 0.045), (0.0068, 0.064), (0.0, 0.066)], (0, 0.0075, 0), "lead-glass", axis="x", seg=20)
    for x, colour in ((-0.022, "yellow"), (0.002, "blue")):
        k.box((x, 0.0143, 0), (0.016, 0.003, 0.0075), colour, r=0.0012, seg=2)
    k.box((0.08, 0.0075, 0), (0.032, 0.0008, 0.0026), "chrome", r=0.0003, seg=1)
    k.cyl((0.066, 0.0075, 0), 0.0016, 0.006, "chrome", axis="x", seg=10)
    k.tube((-0.098, 0.0075, 0), (-0.1, 0.006, 0), 0.0032, "white", seg=10)


@model("sc-instrument-set")
def instrument_set(k: Kit, eq):
    """Rigid sterile container: anodised body, filter lid, latches, fold-down handles, the tamper-evident
    lock, the sterility indicator and the load card."""
    k.box((0, 0.055, 0), (0.38, 0.11, 0.26), "steel", r=0.008)
    k.slab(rrect(0.382, 0.262, 0.012), 0.11, 0.012, "chrome", r=0.003)
    k.slab(rrect(0.26, 0.16, 0.03), 0.122, 0.004, "steel", r=0.0015)
    for i in range(5):
        k.box((-0.08 + 0.04 * i, 0.1265, 0), (0.012, 0.0015, 0.13), "chrome", r=0.0005, seg=1)
    for x in (-0.11, 0.11):
        for z in (-0.131, 0.131):
            k.box((x, 0.1, z), (0.04, 0.035, 0.008), "chrome", r=0.003, seg=2)
    for x in (-0.19, 0.19):
        k.path([(x, 0.08, -0.07), (x + (0.012 if x > 0 else -0.012), 0.08, -0.07), (x + (0.012 if x > 0 else -0.012), 0.08, 0.07), (x, 0.08, 0.07)], 0.003, "chrome", seg=8)
    k.box((0.17, 0.08, 0.133), (0.03, 0.05, 0.006), "sc-robot-accent", r=0.003, seg=1)
    k.box((-0.15, 0.1, 0.133), (0.04, 0.02, 0.004), "led-green", r=0.003, seg=1)
    k.box((0, 0.06, 0.1325), (0.12, 0.05, 0.003), "paper", r=0.002, seg=1)


@model("sc-gauze-swabs")
def gauze_swabs(k: Kit, eq):
    """Pack of ten X-ray-detectable RFID swabs: a folded stack, the blue X-ray thread on each and the tag."""
    for i in range(5):
        k.box((0.001 * (i % 2), 0.003 + 0.0058 * i, -0.0008 * (i % 3)), (0.108, 0.0056, 0.088), "white", r=0.0022, seg=2, rot=(0, (-1.5, 1, -0.5, 1.5, 0)[i], 0))
    for i in range(5):
        k.box((-0.054, 0.003 + 0.0058 * i, 0.01), (0.002, 0.003, 0.05), "sc-drape", r=0.0008, seg=1)
    k.box((0, 0.0312, 0), (0.11, 0.0016, 0.012), "sc-drape", r=0.0006, seg=1)
    k.box((0.04, 0.0318, 0.03), (0.02, 0.002, 0.02), "blue", r=0.002, seg=1)
