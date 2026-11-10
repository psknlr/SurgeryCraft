"""
SurgeryCraft's bespoke equipment models, written in each type's own frame (ClinicalCraft's
scripts/blender/clinicalcraft_shapes.py: metres, x right, y up, z front, origin at the
footprint centre on the floor) from its voxel parts: working heights, screens and the
surfaces things are put on stay where the world expects them. Every other type of the pack
is refined from its voxel parts (`clinicalcraft_refine`). `build.py` runs them.
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


def gas_outlet(k: Kit, x, y, z, colour, plate="steel"):
    """A wall-type medical gas outlet facing +z: plate, the collar in the gas's ISO 32 colour (white
    oxygen, blue nitrous oxide, yellow vacuum, magenta AGSS; medical air black with a white ring)
    and the socket."""
    k.box((x, y, z + 0.004), (0.07, 0.07, 0.008), plate, r=0.008, seg=1)
    k.torus((x, y, z + 0.011), 0.016, 0.005, colour, axis="z", seg=14, ring=5)
    if colour == "sc-gas-air":
        k.torus((x, y, z + 0.0125), 0.0245, 0.003, "gas-oxygen", axis="z", seg=14, ring=4)
    k.cyl((x, y, z + 0.009), 0.011, 0.008, "coal", axis="z", seg=10)


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
    for x, colour in ((-0.22, "gas-oxygen"), (0.22, "blue")):
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
    for i, colour in enumerate(("gas-oxygen", "sc-gas-n2o", "sc-gas-air")):
        x = 0.07 + 0.075 * i
        k.box((x, 1.13, -0.017), (0.05, 0.2, 0.008), "lead-glass", r=0.004, seg=1)
        k.cyl((x, 1.0, -0.008), 0.016, 0.03, colour, axis="z", seg=16, bevel=0.004)
    k.cyl((0.28, 1.12, -0.008), 0.028, 0.026, "coal", axis="z", seg=24, bevel=0.006)
    k.cyl((0.28, 1.25, -0.012), 0.014, 0.02, "gas-oxygen", axis="z", seg=16)
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
    k.cyl((-0.42, 1.09, -0.05), 0.052, 0.18, "paper", seg=20)
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
    for x, colour in ((-0.1, "gas-oxygen"), (0.1, "yellow")):
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
    for x, colour in ((-0.15, "gas-oxygen"), (-0.05, "sc-gas-air"), (0.05, "sc-gas-n2o"), (0.15, "yellow")):
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
    k.hose(hose, 0.026, "clin-hose-blue", seg=10, steps=2)
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
        (1.12, (("led-green", -0.18), ("led-amber", 0.15))),
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
    """Curved Metzenbaum scissors: black rings (a supercut edge; gold rings would mark tungsten-carbide
    inserts), shanks, the pivot and two curved blades, closed."""
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


@model("sc-gauze-swab")
def gauze_swab(k: Kit, eq):
    """One X-ray-detectable RFID swab: a gauze square folded in three, the blue X-ray thread woven
    across it and over its edge, and the RF tag sewn into a corner."""
    for i in range(3):
        k.box((0.0008 * (i - 1), 0.0026 + 0.0046 * i, 0.0006 * (1 - i)), (0.098 - 0.002 * i, 0.0046, 0.098 - 0.002 * i), "white", r=0.002, seg=2,
              rot=(0, (1.2, -0.8, 0.5)[i], 0))
    k.box((0, 0.0144, -0.012), (0.092, 0.0012, 0.006), "sc-drape", r=0.0005, seg=1)
    k.box((-0.0484, 0.0072, -0.012), (0.0014, 0.0132, 0.006), "sc-drape", r=0.0004, seg=1)
    k.box((0.03, 0.0148, 0.03), (0.02, 0.002, 0.02), "blue", r=0.002, seg=1)


@model("sc-rf-wand")
def rf_wand(k: Kit, eq):
    """RF detection wand: the grip with its ribs, scan button and ready light, a cranked neck that
    keeps the hand clear, and the flat loop-antenna paddle that is swept over the patient; the
    cable leaves the butt of the grip."""
    k.lathe([(0.0, -0.174), (0.013, -0.171), (0.0178, -0.16), (0.0185, -0.09), (0.016, -0.045), (0.012, -0.025), (0.0105, -0.02)], (0, 0.03, 0), "plastic", axis="x", seg=16)
    for i in range(4):
        k.torus((-0.148 + 0.014 * i, 0.03, 0), 0.0182, 0.0016, "coal", axis="x", seg=16, ring=4)
    k.box((-0.075, 0.0485, 0), (0.03, 0.004, 0.012), "sc-robot-accent", r=0.0015, seg=1)
    k.box((-0.108, 0.0482, 0), (0.014, 0.003, 0.008), "led-green", r=0.001, seg=1)
    k.hose([(-0.022, 0.03, 0), (0.0, 0.027, 0), (0.02, 0.016, 0), (0.04, 0.011, 0)], 0.0105, "plastic", seg=10, steps=3, r2=0.008)
    k.slab(rrect(0.156, 0.074, 0.036), 0.0, 0.016, "sc-robot-accent", at=(0.1, 0, 0), r=0.006, seg=2)
    k.slab(rrect(0.11, 0.036, 0.017), 0.0158, 0.0012, "plastic", at=(0.1, 0, 0), r=0.0004, seg=1)
    k.hose([(-0.172, 0.03, 0), (-0.177, 0.026, 0.004), (-0.179, 0.012, 0.012)], 0.0045, "coal", seg=6, steps=2)


def moved(outline, dx: float = 0.0, dy: float = 0.0):
    """An outline shifted by (dx, dy)."""
    return [(x + dx, y + dy) for x, y in outline]


@model("sc-lead-apron")
def lead_apron(k: Kit, eq):
    """Wrap-around lead apron on its hanger: shoulders, the neck scoop and arm holes, the front
    panel with its belt and the lead-equivalence label, the overlapping back panel behind."""
    front = [(-0.23, 0.04), (-0.2, 0.012), (0.2, 0.012), (0.23, 0.04), (0.23, 0.52), (0.185, 0.62), (0.17, 0.7), (0.19, 0.8), (0.2, 0.845),
             (0.1, 0.852), (0.082, 0.8), (0.05, 0.745), (0.0, 0.73), (-0.05, 0.745), (-0.082, 0.8), (-0.1, 0.852),
             (-0.2, 0.845), (-0.19, 0.8), (-0.17, 0.7), (-0.185, 0.62), (-0.23, 0.52)]
    k.panel(front, 0.004, 0.03, "sc-lead-rubber", r=0.012)
    back = [(-0.22, 0.05), (-0.19, 0.03), (0.19, 0.03), (0.22, 0.05), (0.22, 0.6), (0.19, 0.84), (0.11, 0.846), (0.09, 0.79), (-0.09, 0.79), (-0.11, 0.846), (-0.19, 0.84), (-0.22, 0.6)]
    k.panel(back, -0.04, 0.03, "sc-lead-rubber", r=0.012)
    k.box((0, 0.43, 0.0375), (0.468, 0.05, 0.008), "sc-robot-accent", r=0.003, seg=1)
    k.box((0.09, 0.43, 0.0425), (0.05, 0.06, 0.006), "coal", r=0.003, seg=1)
    k.box((-0.12, 0.6, 0.0352), (0.09, 0.05, 0.003), "paper", r=0.001, seg=1)
    k.box((0.13, 0.15, 0.0352), (0.06, 0.04, 0.003), "warning-yellow", r=0.001, seg=1)
    k.pipe([(-0.17, 0.835, -0.003), (0.0, 0.866, -0.003), (0.17, 0.835, -0.003)], 0.006, "chrome", bend=0.03, seg=6)
    k.hose([(0.0, 0.866, -0.003), (0.0, 0.882, -0.003), (0.012, 0.893, -0.003), (0.024, 0.884, -0.003)], 0.005, "chrome", seg=6, steps=3)


@model("sc-surgical-microscope")
def surgical_microscope(k: Kit, eq):
    """Floor-stand operating microscope: an H base on castors, the column with its control panel
    and counterweight, the balanced parallelogram arm on its joints, and the optics carrier hanging
    in its yoke — objective pointing down, the surgeon's inclined binocular tube, the assistant's
    side tube and a handgrip on each side."""
    for x in (-0.4, 0.4):
        for z in (-0.4, 0.4):
            k.caster(x, z, r=0.04, stem=0.01)
        k.box((x, 0.125, 0.0), (0.12, 0.09, 0.9), "plastic", r=0.035, seg=2)
    k.slab(rrect(0.9, 0.56, 0.08), 0.07, 0.12, "plastic", at=(0, 0, -0.17), r=0.03, seg=2)
    k.slab(rrect(0.26, 0.26, 0.06), 0.19, 1.47, "sc-robot", at=(0, 0, -0.3), r=0.03, seg=2)
    k.box((0, 1.25, -0.166), (0.17, 0.13, 0.012), "coal", r=0.01, seg=1)
    k.box((0, 1.26, -0.159), (0.13, 0.07, 0.003), "screen-dark", r=0.002, seg=1)
    k.box((0, 1.205, -0.159), (0.04, 0.012, 0.003), "led-green", r=0.002, seg=1)
    k.slab(rrect(0.27, 0.27, 0.065), 1.56, 0.03, "sc-robot-accent", at=(0, 0, -0.3), r=0.008, seg=1)
    k.box((0, 1.74, -0.43), (0.2, 0.22, 0.12), "coal", r=0.03, seg=2)
    # balanced arm: shoulder, two parallel links, elbow, the drop link
    k.cyl((0, 1.74, -0.3), 0.105, 0.24, "sc-robot", axis="x", seg=24, bevel=0.02)
    for dy in (-0.06, 0.06):
        k.tube((0, 1.74 + dy, -0.3), (0, 1.96 + dy, 0.2), 0.036, "sc-robot", seg=12)
    k.cyl((0, 1.96, 0.2), 0.1, 0.2, "sc-robot", axis="x", seg=24, bevel=0.02)
    for x in (-0.105, 0.105):
        k.cyl((x, 1.96, 0.2), 0.06, 0.012, "coal", axis="x", seg=18)
        k.cyl((x * 1.2, 1.74, -0.3), 0.065, 0.012, "coal", axis="x", seg=18)
    k.tube((0, 1.93, 0.22), (0, 1.56, 0.33), 0.045, "sc-robot", seg=12, r2=0.038)
    k.ball((0, 1.54, 0.335), 0.062, "sc-robot-accent", seg=14)
    # optics carrier in its yoke
    k.pipe([(-0.135, 1.34, 0.34), (-0.135, 1.5, 0.34), (0.135, 1.5, 0.34), (0.135, 1.34, 0.34)], 0.018, "sc-robot", bend=0.05, seg=8)
    k.box((0, 1.31, 0.34), (0.22, 0.2, 0.24), "coal", r=0.045, seg=3)
    k.cyl((0, 1.185, 0.34), 0.072, 0.07, "black", seg=20, bevel=0.01)
    k.cyl((0, 1.148, 0.34), 0.056, 0.005, "lead-glass", seg=18)
    k.torus((0, 1.152, 0.34), 0.064, 0.006, "led-blue", seg=20, ring=6)
    for x in (-0.034, 0.034):
        k.tube((x, 1.37, 0.42), (x, 1.455, 0.468), 0.023, "black", seg=10)
        k.cyl((x, 1.462, 0.472), 0.027, 0.02, "rubber", seg=10, rot=(29, 0, 0))
    k.box((0, 1.37, 0.43), (0.13, 0.07, 0.07), "coal", r=0.02, seg=2)
    k.tube((-0.1, 1.33, 0.36), (-0.2, 1.39, 0.4), 0.02, "black", seg=10)
    k.cyl((-0.207, 1.394, 0.403), 0.024, 0.02, "rubber", axis="x", seg=10)
    for sx in (-1, 1):
        k.pipe([(sx * 0.11, 1.3, 0.38), (sx * 0.185, 1.3, 0.4), (sx * 0.185, 1.19, 0.44)], 0.014, "chrome", bend=0.03, seg=8)
        k.cyl((sx * 0.185, 1.17, 0.447), 0.019, 0.07, "rubber", seg=10, rot=(-19, 0, 0))
    k.box((0, 1.225, 0.461), (0.06, 0.02, 0.006), "led-blue", r=0.002, seg=1)


# ------------------------------------------------------------------------------------------------
# cardiac and robotic systems, hybrid imaging
# ------------------------------------------------------------------------------------------------

@model("sc-heart-lung-machine")
def heart_lung_machine(k: Kit, eq):
    """Heart-lung machine: the console on castors with push rails; five roller pumps in a row, each
    a housing with its raceway under a clear lid, the rotor showing through, and a control strip
    with its speed knob; on the mast the hard-shell venous reservoir above the membrane oxygenator,
    the sweep-gas blender beside them; the venous line (blue) coming in to the reservoir and the
    arterial line (red) leaving the oxygenator for the field; the monitoring display on its post
    (the world's screen)."""
    venous = k.paint("venous-blood", "clin-blood-bag", color="#6f2230")
    for x in (-0.57, 0.57):
        for z in (-0.32, 0.32):
            k.caster(x, z, r=0.04, stem=0.01, lite=True)
    k.box((0, 0.4, 0), (1.22, 0.62, 0.7), "plastic", r=0.04, seg=2)
    k.box((0, 0.7, 0.352), (1.2, 0.03, 0.008), "sc-robot-accent")
    for x in (-0.3, 0.3):
        k.box((x, 0.38, 0.352), (0.54, 0.42, 0.006), "sc-robot", r=0.012, seg=1)
        k.box((x, 0.56, 0.358), (0.2, 0.014, 0.01), "chrome")
    for sx in (-1, 1):
        k.pipe([(sx * 0.6, 0.55, -0.26), (sx * 0.645, 0.6, -0.26), (sx * 0.645, 0.6, 0.26), (sx * 0.6, 0.55, 0.26)], 0.012, "chrome", bend=0.03, seg=6, step=45)
    k.slab(rrect(1.24, 0.74, 0.03, 2), 0.72, 0.04, "steel", r=0.008, seg=1)
    # the five pumps: arterial, cardioplegia, vent and two suckers, tagged by colour
    for i, (x, tag) in enumerate(((-0.48, "ambulance-red"), (-0.24, "yellow"), (0.0, "green"), (0.24, "blue"), (0.48, "blue"))):
        k.box((x, 0.825, 0.05), (0.215, 0.13, 0.22), "steel", r=0.014, seg=1)
        k.cyl((x, 0.905, 0.035), 0.088, 0.04, "sc-robot", seg=16)
        k.box((x, 0.921, 0.035), (0.13, 0.014, 0.03), "coal", rot=(0, 25 + 37 * i, 0))
        k.cyl((x, 0.921, 0.035), 0.022, 0.018, "chrome", seg=8)
        k.cyl((x, 0.937, 0.035), 0.09, 0.012, "lead-glass", seg=16)
        k.box((x, 0.83, 0.162), (0.14, 0.06, 0.008), "coal")
        k.box((x - 0.03, 0.836, 0.167), (0.05, 0.026, 0.003), "screen-dark")
        k.cyl((x + 0.04, 0.83, 0.171), 0.014, 0.012, "chrome", axis="z", seg=8)
        k.box((x, 0.878, 0.1615), (0.05, 0.014, 0.004), tag)
    # mast: reservoir above the oxygenator, the gas blender
    k.cyl((-0.5, 1.31, -0.25), 0.022, 1.1, "chrome", seg=8)
    k.tube((-0.5, 1.72, -0.25), (-0.4, 1.72, -0.12), 0.012, "chrome", seg=6)
    k.tube((-0.5, 1.2, -0.25), (-0.4, 1.2, -0.12), 0.012, "chrome", seg=6)
    k.cyl((-0.4, 1.53, -0.12), 0.092, 0.3, "lead-glass", seg=16)
    k.cyl((-0.4, 1.455, -0.12), 0.084, 0.14, venous, seg=14)
    k.cyl((-0.4, 1.69, -0.12), 0.096, 0.024, "sc-robot-accent", seg=16)
    for a in (40, 160, 280):
        k.cyl((-0.4 + 0.05 * math.cos(math.radians(a)), 1.715, -0.12 + 0.05 * math.sin(math.radians(a))), 0.011, 0.03, "plastic", seg=6)
    k.lathe([(0.03, 1.38), (0.07, 1.36), (0.03, 1.33)], (-0.4, 0, -0.12), "plastic", seg=12)
    k.cyl((-0.4, 1.18, -0.12), 0.082, 0.22, "lead-glass", seg=16)
    k.cyl((-0.4, 1.18, -0.12), 0.068, 0.18, "paper", seg=12)
    k.cyl((-0.4, 1.18, -0.12), 0.074, 0.05, "clin-blood-bag", seg=12)
    k.cyl((-0.4, 1.3, -0.12), 0.086, 0.02, "plastic", seg=16)
    k.cyl((-0.4, 1.06, -0.12), 0.086, 0.02, "plastic", seg=16)
    for dz, m in ((-0.03, "clin-hose-blue"), (0.03, "ambulance-red")):
        k.hose([(-0.33, 1.08, -0.12 + dz), (-0.25, 1.02, -0.2 + dz), (-0.25, 0.8, -0.3 + dz)], 0.009, m, seg=5, steps=3)
    k.box((-0.5, 0.98, -0.2), (0.11, 0.15, 0.07), "plastic", r=0.012, seg=1)
    for dx, m in ((-0.025, "gas-oxygen"), (0.025, "sc-gas-air")):
        k.cyl((-0.5 + dx, 0.945, -0.158), 0.014, 0.016, m, axis="z", seg=8)
        k.box((-0.5 + dx, 1.01, -0.163), (0.016, 0.06, 0.004), "lead-glass")
    # the circuit: venous return in, through the arterial pump and the oxygenator, arterial line out
    k.hose([(0.56, 0.79, 0.33), (0.2, 0.99, 0.27), (-0.22, 1.5, 0.1), (-0.36, 1.76, -0.07), (-0.38, 1.705, -0.1)], 0.011, "clin-hose-blue", seg=6, steps=4)
    k.hose([(-0.4, 1.33, -0.12), (-0.52, 1.2, -0.02), (-0.56, 1.02, 0.03), (-0.54, 0.95, 0.035)], 0.011, venous, seg=6, steps=3)
    k.hose([(-0.42, 0.95, 0.035), (-0.36, 1.02, 0.0), (-0.36, 1.08, -0.06)], 0.011, venous, seg=6, steps=3)
    k.hose([(-0.33, 1.26, -0.08), (-0.2, 1.1, 0.1), (0.2, 0.93, 0.3), (0.56, 0.79, 0.37)], 0.011, "clin-blood-bag", seg=6, steps=4)
    # display on its post
    k.cyl((0.35, 1.1, -0.2), 0.022, 0.7, "chrome", seg=8)
    k.box((0.35, 1.45, -0.185), (0.08, 0.08, 0.05), "plastic")
    k.box((0.35, 1.6, -0.152), (0.52, 0.34, 0.06), "plastic", r=0.02, seg=1)
    k.screen_bezel(eq.screens()[0], "coal", border=0.012, depth=0.01, r=0.004)


@model("sc-robotic-console")
def robotic_console(k: Kit, eq):
    """Surgeon console: the base with its footswitch panel (clutch and camera pedals, the yellow cut
    and blue coagulation pedals), two side pillars with leg room between, the padded armrest with
    its touchpad (the world's screen), the two master controllers hanging in front of it and the
    stereo viewer hood with its head rest and eyepieces above."""
    k.slab(rrect(1.04, 0.9, 0.08), 0.0, 0.1, "plastic", r=0.02)
    k.box((0, 0.135, 0.24), (0.64, 0.07, 0.34), "coal", r=0.02, seg=2)
    for x, m, w in ((-0.2, "black", 0.14), (0.02, "yellow", 0.11), (0.17, "blue", 0.11)):
        k.box((x, 0.19, 0.27), (w, 0.028, 0.15), m, r=0.01, seg=2, rot=(-8, 0, 0))
    k.box((-0.2, 0.19, 0.12), (0.14, 0.024, 0.07), "black", r=0.008, seg=1)
    for sx in (-1, 1):
        k.slab(rrect(0.22, 0.56, 0.06), 0.1, 0.92, "sc-robot", at=(sx * 0.4, 0, -0.18), r=0.03, seg=2)
    k.box((0, 0.56, -0.32), (0.62, 0.9, 0.26), "sc-robot", r=0.03, seg=2)
    k.box((0, 0.5, -0.188), (0.5, 0.5, 0.006), "sc-carbon", r=0.01, seg=1)
    # armrest, touchpad, master controllers
    k.slab(rrect(0.94, 0.28, 0.06), 0.82, 0.08, "sc-robot", at=(0, 0, 0.17), r=0.025, seg=2)
    k.slab(rrect(0.6, 0.2, 0.05), 0.9, 0.03, "navy", at=(-0.06, 0, 0.17), r=0.013, seg=2)
    k.box((0.43, 0.96, 0.275), (0.17, 0.13, 0.03), "coal", r=0.01, seg=1)
    k.screen_bezel(eq.screens()[0], "coal", border=0.006, depth=0.004, r=0.002)
    for sx in (-1, 1):
        k.hose([(sx * 0.21, 1.14, 0.06), (sx * 0.2, 1.1, 0.2), (sx * 0.185, 1.04, 0.27), (sx * 0.18, 1.0, 0.27)], 0.016, "chrome", seg=8, steps=3)
        k.ball((sx * 0.18, 0.985, 0.27), 0.024, "coal", seg=12)
        for dz in (-0.022, 0.022):
            k.box((sx * 0.18, 0.955, 0.27 + dz), (0.016, 0.05, 0.008), "sc-robot-accent", r=0.003, seg=1, rot=(-18 if dz > 0 else 18, 0, 0))
    # stereo viewer
    k.slab(rrect(0.84, 0.62, 0.1), 1.1, 0.46, "sc-robot", at=(0, 0, -0.1), r=0.06, seg=3)
    k.slab(rrect(0.846, 0.626, 0.103), 1.485, 0.03, "sc-robot-accent", at=(0, 0, -0.1), r=0.006, seg=1)
    k.box((0, 1.32, 0.203), (0.44, 0.17, 0.03), "black", r=0.014, seg=2)
    for x in (-0.065, 0.065):
        k.cyl((x, 1.32, 0.219), 0.04, 0.006, "screen-dark", axis="z", seg=18)
        k.torus((x, 1.32, 0.221), 0.041, 0.006, "rubber", axis="z", seg=18, ring=6)
    k.box((0, 1.44, 0.214), (0.3, 0.05, 0.04), "navy", r=0.02, seg=2)
    k.box((0, 1.215, 0.214), (0.2, 0.012, 0.008), "led-blue", r=0.003, seg=1)


def _aim(a, b, t: float):
    """The point a fraction `t` of the way from a to b."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


@model("sc-robotic-patient-cart")
def robotic_patient_cart(k: Kit, eq):
    """Patient-side cart: the base on castors with its outriggers and push handle, the column with
    its status ring and touchscreen (the world's screen), the boom, and four jointed arms reaching
    down over the field — three with instrument carriages and shafts, one with the endoscope —
    their shafts converging on the ports."""
    for x in (-0.48, 0.48):
        for z in (-0.58, 0.58):
            k.caster(x, z, r=0.06, stem=0.0, lite=True)
        k.box((x, 0.165, 0.5), (0.16, 0.11, 0.34), "sc-robot", r=0.035, seg=1)
    k.slab(rrect(1.0, 1.0, 0.14, 3), 0.09, 0.3, "sc-robot", at=(0, 0, -0.1), r=0.05)
    k.slab(rrect(1.008, 1.008, 0.144, 3), 0.285, 0.035, "sc-robot-accent", at=(0, 0, -0.1))
    k.pipe([(-0.3, 0.9, -0.5), (-0.3, 1.05, -0.63), (0.3, 1.05, -0.63), (0.3, 0.9, -0.5)], 0.02, "chrome", bend=0.06, seg=6, step=30)
    k.slab(rrect(0.42, 0.42, 0.1, 3), 0.38, 1.44, "sc-robot", at=(0, 0, -0.3), r=0.03, seg=1)
    k.slab(rrect(0.436, 0.436, 0.108, 3), 1.815, 0.03, "led-blue", at=(0, 0, -0.3))
    k.box((0, 1.25, -0.0865), (0.29, 0.21, 0.012), "coal", r=0.012, seg=1)
    k.screen_bezel(eq.screens()[0], "coal", border=0.008, depth=0.004, r=0.003)
    k.cyl((0, 1.86, -0.3), 0.2, 0.06, "sc-robot", seg=20)
    k.slab(rrect(1.12, 0.56, 0.2, 4), 1.87, 0.18, "sc-robot", at=(0, 0, 0.03), r=0.06)
    for i, x0 in enumerate((-0.42, -0.14, 0.14, 0.42)):
        scope = i == 1
        shoulder = (x0, 1.84, 0.24)
        elbow = (x0 * 1.16, 1.74, 0.55)
        wrist = (x0 * 1.04, 1.3, 0.62)
        port = (x0 * 0.4, 0.7, 0.66)
        k.cyl(shoulder, 0.062, 0.1, "sc-robot", seg=12)
        k.tube(shoulder, elbow, 0.046, "sc-robot", seg=8)
        k.ball(elbow, 0.062, "sc-robot", seg=10)
        k.torus(elbow, 0.05, 0.016, "sc-robot-accent", axis="x", seg=12, ring=5)
        k.tube(elbow, wrist, 0.04, "sc-robot", seg=8)
        k.ball(wrist, 0.052, "sc-robot", seg=10)
        k.tube(_aim(wrist, port, 0.04), _aim(wrist, port, 0.5), 0.036 if scope else 0.03, "coal" if scope else "sc-robot-accent", seg=8)
        k.tube(_aim(wrist, port, 0.5), _aim(wrist, port, 0.56), 0.022, "coal", seg=6)
        k.tube(_aim(wrist, port, 0.56), port, 0.008 if scope else 0.006, "chrome", seg=5)


@model("sc-robotic-c-arm")
def robotic_c_arm(k: Kit, eq):
    """Robotic floor-mounted angiography system: the floor plate and turret, the rotating column
    with its control panel (the world's screen), a jointed robot arm — shoulder, upper arm, elbow,
    forearm, wrist — holding the C by its back, and the C itself: one arc about the isocentre with
    the flat-panel detector at its upper end and the X-ray tube and collimator at the lower."""
    k.slab(rrect(1.2, 1.2, 0.1), 0.0, 0.08, "plastic", at=(0, 0, -0.5), r=0.02)
    k.cyl((0, 0.14, -0.5), 0.46, 0.12, "sc-robot", seg=28, bevel=0.025)
    k.torus((0, 0.205, -0.5), 0.4, 0.012, "led-blue", seg=28, ring=5)
    k.slab(rrect(0.62, 0.62, 0.14, 3), 0.2, 0.84, "sc-robot", at=(0, 0, -0.5), r=0.04)
    k.slab(rrect(0.63, 0.63, 0.145, 3), 0.93, 0.06, "sc-robot-accent", at=(0, 0, -0.5))
    k.box((-0.1, 0.7, -0.189), (0.3, 0.22, 0.008), "coal", r=0.01, seg=1)
    k.screen_bezel(eq.screens()[0], "coal", border=0.008, depth=0.004, r=0.003)
    k.box((0.18, 0.78, -0.187), (0.16, 0.08, 0.006), "warning-yellow", r=0.004, seg=1)
    # the robot: shoulder, upper arm, elbow, forearm, wrist
    shoulder, elbow, wrist = (0, 1.2, -0.45), (0, 1.68, 0.08), (-0.4, 1.4, 0.62)
    k.cyl(shoulder, 0.25, 0.62, "sc-robot", axis="x", seg=24, bevel=0.03)
    for x in (-0.312, 0.312):
        k.cyl((x, 1.2, -0.45), 0.17, 0.012, "coal", axis="x", seg=18)
    k.tube(shoulder, elbow, 0.165, "sc-robot", seg=14, r2=0.14)
    k.cyl(elbow, 0.17, 0.44, "sc-robot", axis="x", seg=20, bevel=0.025)
    for x in (-0.222, 0.222):
        k.cyl((x, elbow[1], elbow[2]), 0.115, 0.012, "coal", axis="x", seg=14)
    k.tube(elbow, wrist, 0.125, "sc-robot", seg=12, r2=0.1)
    k.ball(wrist, 0.135, "sc-robot", seg=14)
    k.torus(wrist, 0.11, 0.03, "sc-robot-accent", axis="x", seg=16, ring=6)
    # the C about the isocentre, held at its back
    iso, radius = (0.26, 1.37, 0.92), 0.83
    half, thick, c = 0.09, 0.05, 0.016
    k.box((iso[0] - radius, 1.37, 0.8), (0.24, 0.42, 0.2), "coal", r=0.04, seg=2)
    k.tube(wrist, (iso[0] - radius + 0.02, 1.37, 0.76), 0.09, "sc-robot", seg=10)
    k.revolve([(radius - thick, -half + c), (radius - thick + c, -half), (radius + thick - c, -half), (radius + thick, -half + c),
               (radius + thick, half - c), (radius + thick - c, half), (radius - thick + c, half), (radius - thick, half - c)],
              iso, "sc-robot", axis="z", a0=80, a1=280, seg=56)
    k.revolve([(radius + thick - 0.002, -0.03), (radius + thick + 0.005, -0.03), (radius + thick + 0.005, 0.03), (radius + thick - 0.002, 0.03)],
              iso, "coal", axis="z", a0=92, a1=268, seg=56)
    # detector above, tube and collimator below, facing each other across the isocentre
    k.box((0.34, 2.165, 0.92), (0.22, 0.1, 0.2), "sc-robot", r=0.03, seg=1)
    k.box((0.26, 2.06, 0.92), (0.52, 0.14, 0.5), "coal", r=0.035, seg=3)
    k.box((0.26, 2.075, 0.92), (0.53, 0.03, 0.51), "sc-robot-accent", r=0.01, seg=1)
    k.box((0.26, 1.985, 0.92), (0.46, 0.012, 0.44), "black", r=0.004, seg=1)
    k.box((0.26, 0.72, 0.92), (0.42, 0.32, 0.42), "sc-robot", r=0.06, seg=3)
    k.box((0.26, 0.905, 0.92), (0.26, 0.07, 0.26), "coal", r=0.02, seg=2)
    k.box((0.26, 0.943, 0.92), (0.16, 0.006, 0.16), "lead-glass", r=0.002, seg=1)
    k.box((0.26, 0.72, 1.132), (0.12, 0.06, 0.006), "warning-yellow", r=0.003, seg=1)
