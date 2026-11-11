"""
The thoracoscopy models (docs/THORACOSCOPY.md), written like the others in each type's own frame (metres, x right,
y up, z front, origin at the footprint centre on the floor; instruments lie flat, the tip towards +x): the
thoracoscope with its camera head, the port, the long instruments that go through an incision, the cutter-stapler,
the chest tube and its drainage unit, the tower and the lung-isolation cart, the aids for the lateral position —
and the training station: a torso on its side on a flexed table, the upper arm on its support, the three incisions
of the anterior approach with the scope standing in its port.

Imported at the end of models.py (it registers its builders there).
"""
from __future__ import annotations

import math

from clinicalcraft_shapes import Kit, rrect

from models import ceiling_display, finger_rings, handle_bar, model, ring_shanks, strip


# ------------------------------------------------------------------------------------------------
# the picture: tower and display
# ------------------------------------------------------------------------------------------------

@model("sc-thoracoscopy-tower")
def thoracoscopy_tower(k: Kit, eq):
    """Thoracoscopy tower: a four-post cart with shelves carrying the recorder, the energy platform, the light
    source and the camera control unit, the monitor on its arm (its screen is the world's display); at the
    side a ring holder with the warming flask and a hook with the coiled light cable."""
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
    for i, y in enumerate((0.52, 0.82, 1.12, 1.40)):
        hgt = 0.12 if i == 3 else 0.16
        k.box((0, y, 0), (0.6, hgt, 0.5), "plastic", r=0.015)
        k.box((0, y, 0.251), (0.56, hgt - 0.03, 0.004), "sc-matte-black", r=0.006, seg=1)
    # recorder: a slot and a button row
    k.box((-0.08, 0.52, 0.255), (0.26, 0.012, 0.004), "coal", r=0.002, seg=1)
    for x in (0.12, 0.17, 0.22):
        k.cyl((x, 0.52, 0.256), 0.012, 0.008, "steel", axis="z", seg=12)
    # energy platform: its display strip, two sockets, a standby light
    k.box((-0.12, 0.84, 0.255), (0.2, 0.05, 0.004), "screen-dark", r=0.004, seg=1)
    for x in (0.06, 0.14):
        k.torus((x, 0.8, 0.256), 0.018, 0.005, "steel", axis="z", seg=16, ring=6)
    k.box((0.22, 0.86, 0.256), (0.06, 0.025, 0.006), "led-amber", r=0.004, seg=1)
    # light source: the light port with the cable plugged in, the intensity knob, its indicator
    k.cyl((0.15, 1.12, 0.26), 0.026, 0.02, "steel", axis="z", seg=20, bevel=0.004)
    k.cyl((0.15, 1.12, 0.272), 0.014, 0.012, "white", axis="z", seg=14)
    k.cyl((-0.02, 1.12, 0.258), 0.022, 0.014, "coal", axis="z", seg=18, bevel=0.003)
    k.box((-0.18, 1.13, 0.256), (0.1, 0.05, 0.006), "led-green", r=0.004, seg=1)
    # camera control unit: the camera socket, a white-balance button, the power light
    k.cyl((-0.16, 1.40, 0.257), 0.02, 0.012, "steel", axis="z", seg=16, bevel=0.003)
    k.box((0.02, 1.40, 0.256), (0.05, 0.03, 0.006), "white", r=0.004, seg=1)
    k.box((0.2, 1.40, 0.256), (0.07, 0.025, 0.006), "led-blue", r=0.004, seg=1)
    # the monitor on its arm
    k.cyl((0, 1.71, -0.05), 0.022, 0.1, "steel", seg=16)
    k.box((0, 1.78, -0.03), (0.16, 0.12, 0.04), "steel", r=0.01)
    k.box((0, 1.86, 0.02), (0.72, 0.44, 0.06), "sc-matte-black", r=0.016)
    k.screen_bezel(eq.screens()[0], "sc-matte-black", border=0.02, depth=0.01, r=0.004)
    # at the side: the warming flask in its ring, the light cable coiled on a hook
    k.path([(0.34, 1.0, 0.12), (0.375, 1.0, 0.12)], 0.006, "chrome", seg=8)
    k.torus((0.378, 1.0, 0.12), 0.034, 0.005, "chrome", seg=18, ring=6)
    k.cyl((0.378, 0.93, 0.12), 0.03, 0.17, "steel", seg=20, bevel=0.008)
    k.cyl((0.378, 1.022, 0.12), 0.026, 0.014, "sc-matte-black", seg=18, bevel=0.003)
    k.path([(0.34, 1.26, -0.1), (0.385, 1.26, -0.1), (0.385, 1.29, -0.1)], 0.005, "chrome", seg=8)
    for i in range(3):
        k.torus((0.386 + 0.004 * i, 1.19, -0.1), 0.07, 0.0045, "coal", axis="x", seg=20, ring=6)
    k.hose([(0.15, 1.12, 0.278), (0.2, 1.1, 0.32), (0.3, 1.14, 0.2), (0.386, 1.22, -0.04)], 0.0045, "coal", seg=6, steps=3)


@model("sc-scope-display")
def scope_display(k: Kit, eq):
    """Ceiling-boom endoscopy display: the boom display, its light green while it is routed to the camera."""
    ceiling_display(k, eq, led="led-green")


# ------------------------------------------------------------------------------------------------
# instruments (handheld: lying flat on the table, the tip towards +x)
# ------------------------------------------------------------------------------------------------

@model("sc-thoracoscope")
def thoracoscope(k: Kit, eq):
    """30° thoracoscope: the 10 mm telescope with its oblique tip, the light post at right angles, the eyepiece in
    the coupler of the camera head (two buttons, a focus ring), the camera cable leaving the back."""
    y = 0.017
    k.cyl((0.075, y, 0), 0.005, 0.33, "chrome", axis="x", seg=14)
    # the tip cut at 30°: a short dark wedge
    k.cyl((0.243, y, 0), 0.005, 0.008, "sc-matte-black", axis="x", seg=14, r2=0.0036)
    k.cyl((-0.11, y, 0), 0.0105, 0.045, "steel", axis="x", seg=18, bevel=0.002)
    k.cyl((-0.108, y, 0.019), 0.0058, 0.026, "steel", axis="z", seg=12)
    k.cyl((-0.108, y, 0.034), 0.0072, 0.006, "chrome", axis="z", seg=12)
    k.lathe([(0.0105, -0.133), (0.017, -0.146), (0.017, -0.152), (0.0, -0.152)], (0, y, 0), "sc-matte-black", axis="x", seg=18)
    # camera head: coupler, focus ring, body with two buttons, cable
    k.cyl((-0.158, y, 0), 0.019, 0.012, "steel", axis="x", seg=20, bevel=0.002)
    k.cyl((-0.169, y, 0), 0.0165, 0.01, "blue", axis="x", seg=20, bevel=0.002)
    k.box((-0.203, y, 0), (0.058, 0.03, 0.04), "plastic", r=0.01)
    for x in (-0.212, -0.194):
        k.box((x, y + 0.0158, 0), (0.011, 0.003, 0.014), "blue", r=0.0012, seg=1)
    k.hose([(-0.232, y, 0), (-0.238, y - 0.004, 0.004), (-0.24, 0.006, 0.014)], 0.0042, "coal", seg=6, steps=2)


@model("sc-thoracoport")
def thoracoport(k: Kit, eq):
    """Thoracic port: a short threaded cannula with its flange, the blunt obturator through it and its cap."""
    y = 0.02
    k.cyl((0.02, y, 0), 0.0082, 0.07, "white", axis="x", seg=18)
    for i in range(5):
        k.torus((-0.005 + 0.012 * i, y, 0), 0.0086, 0.0013, "white", axis="x", seg=16, ring=4)
    k.cyl((-0.022, y, 0), 0.017, 0.012, "white", axis="x", seg=22, bevel=0.003)
    k.lathe([(0.0066, 0.055), (0.0066, 0.059), (0.004, 0.064), (0.0, 0.0655)], (0, y, 0), "steel", axis="x", seg=14)
    k.cyl((-0.042, y, 0), 0.0195, 0.026, "blue", axis="x", seg=22, bevel=0.005)
    for a in range(6):
        ang = math.radians(60 * a)
        k.box((-0.042, y + 0.0195 * math.cos(ang), 0.0195 * math.sin(ang)), (0.02, 0.003, 0.003), "blue", r=0.001, seg=1, rot=(math.degrees(ang), 0, 0))


@model("sc-lung-forceps")
def lung_forceps(k: Kit, eq):
    """Lung grasping forceps: finger rings and a ratchet, long shanks to a joint far forward, and oval
    fenestrated jaws that hold lung without crushing it."""
    finger_rings(k, -0.135, "steel")
    ring_shanks(k, -0.135, 0.085, "chrome")
    for sgn in (-1, 1):
        for i in range(3):
            k.box((-0.118 + 0.003 * i, 0.0026, sgn * 0.0046), (0.0018, 0.004, 0.0035), "steel", r=0.0004, seg=1)
    k.box((0.085, 0.003, 0), (0.011, 0.006, 0.009), "chrome", r=0.0015, seg=2)
    k.cyl((0.085, 0.0064, 0), 0.002, 0.0012, "steel", seg=10)
    for y in (0.0018, 0.0052):
        k.slab(strip(0.09, 0.118, lambda t: 0, lambda t: 0.0048 - 0.001 * t), y - 0.0012, 0.0024, "chrome", r=0.0006, seg=1)
        k.torus((0.132, y, 0), 0.0105, 0.0019, "chrome", seg=20, ring=6, stretch=(1.45, 1))


@model("sc-endo-dissector")
def endo_dissector(k: Kit, eq):
    """Right-angle dissector: finger rings, long shanks, and fine jaws that turn through a right angle at the
    tip to pass behind a vessel."""
    finger_rings(k, -0.155, "steel")
    ring_shanks(k, -0.155, 0.1, "chrome")
    k.box((0.1, 0.003, 0), (0.011, 0.006, 0.009), "chrome", r=0.0015, seg=2)
    k.cyl((0.1, 0.0064, 0), 0.002, 0.0012, "steel", seg=10)
    turn = lambda t: 0.024 * max(0.0, (t - 0.45) / 0.55) ** 2.2  # noqa: E731
    for y in (0.0008, 0.0036):
        k.slab(strip(0.104, 0.158, turn, lambda t: 0.0056 - 0.0032 * t), y, 0.0024, "chrome", r=0.0006, seg=1)
    k.ball((0.158, 0.003, turn(1)), 0.002, "chrome", seg=8)


@model("sc-clip-applier")
def clip_applier(k: Kit, eq):
    """Endoscopic clip applier: a fixed and a moving ring handle, the rotating knob, a 10 mm shaft and two
    prongs holding a clip open."""
    y = 0.011
    k.torus((-0.175, 0.004, -0.016), 0.014, 0.0032, "sc-matte-black", seg=20, ring=6, stretch=(1.2, 1))
    k.torus((-0.15, 0.004, 0.02), 0.013, 0.003, "sc-matte-black", seg=20, ring=6, stretch=(1.3, 1))
    k.slab(strip(-0.17, -0.1, lambda t: -0.012 * (1 - t), lambda t: 0.012 + 0.006 * t), 0.002, 0.014, "sc-matte-black", r=0.003, seg=2)
    k.slab(strip(-0.146, -0.108, lambda t: 0.014 * (1 - t) + 0.004, lambda t: 0.007), 0.004, 0.008, "sc-matte-black", r=0.002, seg=1)
    k.cyl((-0.092, y, 0), 0.012, 0.018, "blue", axis="x", seg=18, bevel=0.003)
    for a in range(8):
        ang = math.radians(45 * a)
        k.box((-0.092, y + 0.012 * math.cos(ang), 0.012 * math.sin(ang)), (0.016, 0.0022, 0.0022), "blue", r=0.0006, seg=1, rot=(math.degrees(ang), 0, 0))
    k.cyl((0.048, y, 0), 0.005, 0.262, "chrome", axis="x", seg=14)
    for sgn in (-1, 1):
        k.slab(strip(0.178, 0.205, lambda t, s=sgn: s * (0.002 + 0.0042 * t), lambda t: 0.0034 - 0.001 * t), y - 0.002, 0.004, "steel", r=0.0006, seg=1)
    # the clip between the prongs: a V, open
    for sgn in (-1, 1):
        k.slab(strip(0.186, 0.204, lambda t, s=sgn: s * (0.0006 + 0.0034 * t), lambda t: 0.0016), y - 0.0014, 0.0028, "gold", r=0.0004, seg=1)


@model("sc-ultrasonic-shears")
def ultrasonic_shears(k: Kit, eq):
    """Ultrasonic shears lying on their side: the pistol grip with its trigger loop and two activation
    buttons, the rotation knob, a long 5.5 mm shaft, the clamp arm over the active blade, and the cable."""
    y = 0.017
    k.box((-0.15, y, 0.004), (0.15, 0.03, 0.05), "white", r=0.012)
    k.slab(strip(-0.2, -0.13, lambda t: -0.022 - 0.045 * (1 - t) * 0 - 0.03, lambda t: 0.05), 0.003, 0.028, "white", r=0.008, seg=2)
    k.slab([(-0.196, -0.03), (-0.146, -0.03), (-0.158, -0.076), (-0.198, -0.076)], 0.003, 0.028, "white", r=0.008, seg=2)
    k.torus((-0.118, y, -0.045), 0.02, 0.0042, "plastic", seg=20, ring=6, stretch=(0.8, 1.25))
    for x, colour in ((-0.094, "blue"), (-0.094, "purple")):
        z = -0.006 if colour == "blue" else -0.02
        k.box((x, y, z), (0.008, 0.012, 0.01), colour, r=0.002, seg=1)
    k.cyl((-0.066, y, 0.004), 0.014, 0.022, "blue", axis="x", seg=18, bevel=0.004)
    for a in range(8):
        ang = math.radians(45 * a)
        k.box((-0.066, y + 0.014 * math.cos(ang), 0.004 + 0.014 * math.sin(ang)), (0.018, 0.0024, 0.0024), "blue", r=0.0006, seg=1, rot=(math.degrees(ang), 0, 0))
    k.cyl((0.082, y, 0.004), 0.0028, 0.274, "chrome", axis="x", seg=12)
    # the jaw: the active blade below, the clamp arm with its white pad above, a little open
    k.cyl((0.232, y - 0.001, 0.004), 0.0016, 0.026, "steel", axis="x", seg=8, r2=0.0011)
    k.box((0.232, y + 0.0034, 0.004), (0.026, 0.0018, 0.0036), "white", r=0.0006, seg=1, rot=(0, 0, 7))
    k.box((0.232, y + 0.005, 0.004), (0.027, 0.0016, 0.004), "steel", r=0.0006, seg=1, rot=(0, 0, 7))
    k.hose([(-0.225, y, 0.004), (-0.24, y - 0.004, 0.02), (-0.245, 0.006, 0.05)], 0.0045, "coal", seg=6, steps=2)


@model("sc-endo-stapler")
def endo_stapler(k: Kit, eq):
    """Endoscopic linear cutter-stapler lying on its side: the handle with its firing trigger and release
    button, the rotating collar, a 12 mm shaft with the articulation joint, and the jaws — the anvil with its
    graduation marks over the cartridge, whose colour says what tissue it is for."""
    y = 0.02
    k.box((-0.16, y, 0.012), (0.17, 0.036, 0.052), "white", r=0.014)
    k.slab([(-0.24, -0.012), (-0.185, -0.012), (-0.2, -0.078), (-0.245, -0.078)], 0.004, 0.032, "white", r=0.009, seg=2)
    k.slab([(-0.17, -0.014), (-0.125, -0.014), (-0.142, -0.07), (-0.162, -0.07)], 0.008, 0.024, "coal", r=0.007, seg=2)
    k.box((-0.2, y, 0.04), (0.028, 0.016, 0.01), "led-green", r=0.003, seg=1)
    k.cyl((-0.066, y, 0.012), 0.017, 0.026, "plastic", axis="x", seg=20, bevel=0.004)
    for a in range(8):
        ang = math.radians(45 * a)
        k.box((-0.066, y + 0.017 * math.cos(ang), 0.012 + 0.017 * math.sin(ang)), (0.02, 0.0028, 0.0028), "plastic", r=0.0008, seg=1, rot=(math.degrees(ang), 0, 0))
    k.cyl((0.052, y, 0.012), 0.006, 0.21, "chrome", axis="x", seg=14)
    k.cyl((0.162, y, 0.012), 0.0068, 0.012, "sc-matte-black", axis="x", seg=14, bevel=0.002)
    # jaws: cartridge channel below, anvil above and a little open
    k.box((0.21, y - 0.0034, 0.012), (0.084, 0.0062, 0.011), "steel", r=0.0016, seg=2)
    k.box((0.212, y - 0.0002, 0.012), (0.072, 0.0018, 0.0088), "purple", r=0.0006, seg=1)
    k.box((0.2495, y - 0.003, 0.012), (0.008, 0.0066, 0.0108), "purple", r=0.002, seg=2)
    k.box((0.209, y + 0.0062, 0.012), (0.082, 0.0042, 0.0104), "chrome", r=0.0014, seg=2, rot=(0, 0, 5))
    for i in range(4):
        k.box((0.184 + 0.016 * i, y + 0.0062 + 0.0014 * (i - 1.5), 0.0174), (0.0012, 0.004, 0.0004), "coal", seg=1, rot=(0, 0, 5))


@model("sc-specimen-bag")
def specimen_bag(k: Kit, eq):
    """Specimen retrieval bag: a clear pouch folded flat, its mouth on a blue spring rim, the draw string
    and its pull tab."""
    k.slab(rrect(0.15, 0.085, 0.012), 0.0, 0.006, "sc-clear-tube", at=(0.012, 0, 0), r=0.002)
    k.slab(rrect(0.11, 0.06, 0.01), 0.006, 0.003, "sc-clear-tube", at=(0.025, 0, 0), r=0.001, seg=1)
    k.torus((-0.045, 0.006, 0), 0.022, 0.0026, "blue", seg=22, ring=6, stretch=(0.75, 1.55))
    k.hose([(-0.06, 0.006, 0.0), (-0.072, 0.005, 0.012), (-0.08, 0.004, 0.02)], 0.0012, "white", seg=5, steps=2)
    k.box((-0.083, 0.004, 0.024), (0.01, 0.004, 0.012), "blue", r=0.0015, seg=1)


@model("sc-chest-tube")
def chest_tube(k: Kit, eq):
    """28 Fr chest tube: clear and straight, the blue radiopaque line along it, side holes near the rounded
    tip, depth marks, the funnel end for the connector."""
    y = 0.0062
    k.cyl((0.01, y, 0), 0.0047, 0.4, "sc-clear-tube", axis="x", seg=14)
    k.ball((0.21, y, 0), 0.0047, "sc-clear-tube", seg=10)
    k.box((0.01, y + 0.0048, 0), (0.4, 0.0008, 0.0014), "blue", seg=1)
    for i, x in enumerate((0.19, 0.165, 0.14, 0.115)):
        k.cyl((x, y, 0.0046 if i % 2 else -0.0046), 0.0022, 0.0012, "coal", axis="z", seg=8)
    for x in (0.02, -0.03, -0.08):
        k.torus((x, y, 0), 0.00475, 0.0005, "coal", axis="x", seg=12, ring=3)
    k.lathe([(0.0047, -0.19), (0.0072, -0.204), (0.0072, -0.222), (0.0, -0.222)], (0, y, 0), "white", axis="x", seg=14)


# ------------------------------------------------------------------------------------------------
# drainage, lung isolation, positioning
# ------------------------------------------------------------------------------------------------

@model("sc-chest-drainage-unit")
def chest_drainage_unit(k: Kit, eq):
    """Chest drainage unit on its fold-out floor stand: the white body with the clear face of the collection
    chambers (graduated), the water-seal chamber with its blue water and the air-leak meter above it, the
    orange suction regulator, the carrying handle and bed hangers, and the patient tube looped over the top."""
    for sgn in (-1, 1):
        k.box((0, 0.012, sgn * 0.09), (0.3, 0.024, 0.05), "plastic", r=0.01, seg=2)
    k.box((0, 0.06, 0), (0.26, 0.08, 0.05), "plastic", r=0.012, seg=2)
    k.box((0, 0.3, 0), (0.3, 0.38, 0.09), "white", r=0.022)
    # collection: three clear columns with graduation lines
    for i, x in enumerate((-0.108, -0.068, -0.028)):
        k.box((x, 0.29, 0.0455), (0.034, 0.3, 0.004), "sc-clear-tube", r=0.003, seg=1)
        for j in range(7):
            k.box((x, 0.165 + 0.04 * j, 0.0478), (0.02 if j % 2 == 0 else 0.012, 0.0016, 0.0006), "coal", seg=1)
    # water seal (blue to the 2 cm line) with the air-leak meter above it
    k.box((0.045, 0.2, 0.0455), (0.05, 0.1, 0.004), "blue", r=0.003, seg=1)
    k.box((0.045, 0.335, 0.0455), (0.05, 0.16, 0.004), "sc-clear-tube", r=0.003, seg=1)
    for j in range(5):
        k.ball((0.045, 0.28 + 0.03 * j, 0.0475), 0.006, "white", seg=8, squash=(1, 1, 0.3))
    # suction regulator: an orange dial, and the float window beneath it
    k.cyl((0.115, 0.4, 0.05), 0.024, 0.014, "orange", axis="z", seg=20, bevel=0.003)
    k.box((0.115, 0.4, 0.0585), (0.006, 0.03, 0.002), "white", r=0.0008, seg=1)
    k.box((0.115, 0.3, 0.0455), (0.04, 0.09, 0.004), "sc-clear-tube", r=0.003, seg=1)
    k.ball((0.115, 0.3, 0.047), 0.01, "orange", seg=10, squash=(1, 1, 0.35))
    # handle and hangers
    k.path([(-0.06, 0.49, 0), (-0.06, 0.525, 0), (0.06, 0.525, 0), (0.06, 0.49, 0)], 0.008, "white", seg=10)
    for x in (-0.12, 0.12):
        k.path([(x, 0.485, -0.03), (x, 0.52, -0.03), (x, 0.52, -0.06), (x, 0.5, -0.06)], 0.0035, "chrome", seg=6)
    # the patient tube: up from the collection chamber, looped, its end capped until it is connected
    k.cyl((-0.12, 0.5, 0.02), 0.012, 0.03, "white", seg=12)
    k.hose([(-0.12, 0.51, 0.02), (-0.125, 0.58, 0.03), (-0.08, 0.6, 0.07), (0.02, 0.56, 0.1), (0.07, 0.47, 0.105), (0.03, 0.4, 0.1)], 0.0075, "sc-clear-tube", seg=8, steps=3)
    k.cyl((0.03, 0.39, 0.1), 0.0095, 0.03, "blue", seg=10, bevel=0.002)
    # suction port
    k.cyl((0.12, 0.5, 0.02), 0.008, 0.024, "white", seg=10)


@model("sc-lung-isolation-cart")
def lung_isolation_cart(k: Kit, eq):
    """Lung-isolation cart: three drawers on a rolling cabinet, a railed top with a double-lumen tube in its
    tray (the bronchial cuff and its pilot balloon blue) and two tube clamps, and the flexible bronchoscope
    hanging from a pole beside its screen (the world's display)."""
    for x in (-0.25, 0.25):
        for z in (-0.2, 0.2):
            k.caster(x, z, r=0.035, stem=0.02)
    k.box((0, 0.5, 0), (0.56, 0.78, 0.46), "plastic", r=0.022)
    for y in (0.76, 0.56, 0.36):
        k.box((0, y, 0.233), (0.5, 0.165, 0.012), "white", r=0.01)
        handle_bar(k, (-0.03, y + 0.045, 0.252), (0.13, y + 0.045, 0.252), 0.012, r=0.006)
    k.box((-0.17, 0.76, 0.2405), (0.1, 0.05, 0.003), "blue", r=0.004, seg=1)
    k.box((-0.17, 0.56, 0.2405), (0.1, 0.05, 0.003), "paper", r=0.004, seg=1)
    k.box((-0.17, 0.36, 0.2405), (0.1, 0.05, 0.003), "paper", r=0.004, seg=1)
    k.box((0, 0.915, 0), (0.6, 0.035, 0.5), "steel", r=0.01)
    k.path([(-0.285, 0.935, 0.235), (-0.285, 0.975, 0.235), (-0.285, 0.975, -0.235), (0.285, 0.975, -0.235), (0.285, 0.975, 0.235), (0.285, 0.935, 0.235)], 0.007, "chrome", seg=8)
    # a double-lumen tube in its tray: the curved tube, the tracheal (clear) and bronchial (blue) cuffs, the two
    # limbs with their connectors and the pilot balloons
    k.box((-0.07, 0.94, 0.08), (0.4, 0.014, 0.12), "paper", r=0.005, seg=1)
    tube = [(-0.2, 0.957, 0.07), (-0.08, 0.957, 0.066), (0.04, 0.957, 0.074), (0.1, 0.957, 0.1), (0.118, 0.957, 0.128)]
    k.hose(tube, 0.0065, "sc-clear-tube", seg=8, steps=3)
    k.cyl((0.02, 0.957, 0.071), 0.0105, 0.03, "sc-clear-tube", axis="x", seg=12, bevel=0.004)
    k.ball((0.106, 0.957, 0.108), 0.0092, "blue", seg=10, squash=(1, 1, 1))
    for z, colour in ((0.05, "sc-clear-tube"), (0.092, "blue")):
        k.hose([(-0.2, 0.957, 0.07), (-0.235, 0.958, z)], 0.0055, "sc-clear-tube", seg=6, steps=1)
        k.cyl((-0.245, 0.958, z), 0.0075, 0.02, colour if colour == "blue" else "white", axis="x", seg=10, bevel=0.002)
        k.hose([(-0.17, 0.957, 0.07), (-0.19, 0.955, z + (0.035 if z > 0.07 else -0.02))], 0.0012, colour, seg=4, steps=1)
        k.ball((-0.195, 0.955, z + (0.04 if z > 0.07 else -0.024)), 0.0075, colour, seg=8, squash=(1.3, 0.7, 1))
    # tube clamps
    for x in (-0.02, 0.05):
        k.slab(strip(x - 0.045, x + 0.045, lambda t: 0, lambda t: 0.006), 0.94, 0.004, "chrome", at=(0, 0, -0.1), r=0.001, seg=1, rot=(0, 20, 0))
        k.torus((x - 0.05, 0.942, -0.085), 0.008, 0.002, "chrome", seg=12, ring=4)
    # the bronchoscope: its pole and screen, the control body on a hook, the insertion tube hanging in a loop
    scr = eq.screens()[0]
    k.cyl((0.22, 1.16, -0.16), 0.011, 0.46, "chrome", seg=14)
    k.box((0.18, 1.4, -0.142), (0.22, 0.16, 0.04), "plastic", r=0.012)
    k.screen_bezel(scr, "coal", border=0.01, depth=0.008, r=0.004)
    k.path([(0.22, 1.3, -0.16), (0.27, 1.3, -0.13), (0.27, 1.32, -0.11)], 0.004, "chrome", seg=6)
    k.box((0.27, 1.27, -0.1), (0.03, 0.11, 0.035), "sc-matte-black", r=0.008)
    k.cyl((0.27, 1.335, -0.1), 0.012, 0.02, "sc-matte-black", seg=10)
    k.hose([(0.27, 1.215, -0.1), (0.272, 1.1, -0.09), (0.25, 1.02, -0.04), (0.2, 1.0, 0.0), (0.16, 1.04, -0.04), (0.17, 1.12, -0.08)], 0.0028, "sc-matte-black", seg=6, steps=3)


@model("sc-lateral-positioning-set")
def lateral_positioning_set(k: Kit, eq):
    """Lateral-positioning aids on their trolley: the vacuum mattress rolled and strapped on the lower shelf;
    on top the pillow, the gel head ring, the axillary roll and the padded arm support on its post; a safety
    strap hanging at the end."""
    for x in (-0.4, 0.4):
        for z in (-0.225, 0.225):
            k.caster(x, z, r=0.035, stem=0.02)
            k.cyl((x, 0.52, z), 0.014, 0.86, "chrome", seg=12)
    k.slab(rrect(0.84, 0.5, 0.02), 0.185, 0.02, "steel", r=0.004)
    k.slab(rrect(0.86, 0.52, 0.02), 0.705, 0.022, "steel", r=0.004)
    k.path([(-0.4, 0.9, -0.225), (-0.4, 0.95, -0.225), (-0.4, 0.95, 0.225), (-0.4, 0.9, 0.225)], 0.01, "chrome", seg=10)
    # the vacuum mattress, rolled, with two straps and its valve
    k.cyl((0, 0.345, 0), 0.14, 0.72, "sc-vacuum-mat", axis="x", seg=24, bevel=0.03)
    for x in (-0.2, 0.2):
        k.torus((x, 0.345, 0), 0.142, 0.006, "coal", axis="x", seg=24, ring=5)
    k.cyl((0.365, 0.345, 0.05), 0.014, 0.016, "ambulance-red", axis="x", seg=12, bevel=0.003)
    # on top: pillow, head ring, axillary roll, arm support
    k.box((-0.2, 0.775, 0.1), (0.38, 0.09, 0.26), "white", r=0.04)
    k.torus((-0.24, 0.762, -0.15), 0.065, 0.032, "teal", seg=22, ring=8)
    k.cyl((0.2, 0.782, -0.15), 0.052, 0.36, "sc-vacuum-mat", axis="x", seg=18, bevel=0.02)
    k.box((0.2, 0.752, 0.1), (0.38, 0.05, 0.15), "navy", r=0.02)
    for sgn in (-1, 1):
        k.box((0.2, 0.78, 0.1 + sgn * 0.066), (0.38, 0.07, 0.022), "navy", r=0.01, seg=2)
    k.cyl((0.37, 0.92, 0.1), 0.011, 0.34, "chrome", seg=12)
    k.box((0.37, 0.77, 0.1), (0.04, 0.05, 0.05), "coal", r=0.008, seg=2)
    k.ball((0.395, 0.77, 0.1), 0.014, "coal", seg=10)
    # a safety strap over the handle end
    k.box((-0.415, 0.7, 0.0), (0.008, 0.42, 0.06), "coal", r=0.002, seg=1)
    k.box((-0.42, 0.52, 0.0), (0.012, 0.04, 0.07), "steel", r=0.003, seg=1)


# ------------------------------------------------------------------------------------------------
# the training station
# ------------------------------------------------------------------------------------------------

@model("sc-vats-trainer")
def vats_trainer(k: Kit, eq):
    """Thoracoscopy training station: a pedestal table flexed under the trunk, a vacuum mattress, and on it a
    torso on its right side — the head on a ring and a pillow towards −x so that the neck lies in line, the
    lower arm out on a board, the upper arm on its padded support, hips and legs under the drape (the lower
    leg bent). The side of the chest is bare inside four towels: the axillary lines drawn on the skin, and the
    three incisions of the standardized three-port anterior approach — the utility incision in the 4th space
    with its wound protector and a lung forceps through it, the camera port low and anterior with the 30°
    scope standing in it on a holder, the third port at the same level further back. The monitor at the back
    shows the camera's picture (the world's display)."""
    flex = 9.0
    rad = math.radians(flex)
    apex = 0.87          # the top of the table top at the break
    bx = -0.12           # where the table breaks: under the chest

    def at(s, lift=0.0, dz=0.0):
        """A point `s` along the top from the break (towards the head: negative) and `lift` above it."""
        if s < 0:
            return (bx + s * math.cos(rad) - lift * math.sin(rad), apex + s * math.sin(rad) + lift * math.cos(rad), dz)
        return (bx + s * math.cos(rad) + lift * math.sin(rad), apex - s * math.sin(rad) + lift * math.cos(rad), dz)

    def lay(s, lift, size, m, r=0.0, seg=2, dz=0.0, turn=0.0):
        """A box lying along the top at `s`, its middle `lift` above it (`turn`: about its own long axis)."""
        k.box(at(s, lift, dz), size, m, r=r, seg=seg, rot=(turn, 0, flex if s < 0 else -flex))

    # pedestal, the hinge, the two halves of the top with their side rails
    k.box((0, 0.04, 0), (0.72, 0.08, 0.6), "plastic", r=0.03)
    k.box((0, 0.42, 0), (0.34, 0.68, 0.38), "sc-robot", r=0.04)
    k.box((0, 0.3, 0.195), (0.24, 0.03, 0.006), "sc-robot-accent", r=0.003, seg=1)
    k.cyl((bx, apex - 0.055, 0), 0.03, 0.5, "steel", axis="z", seg=12)
    lay(-0.45, -0.025, (0.9, 0.05, 0.54), "steel", r=0.012)
    lay(0.53, -0.025, (1.06, 0.05, 0.54), "steel", r=0.012)
    for z in (-0.285, 0.285):
        lay(-0.45, -0.04, (0.84, 0.03, 0.014), "chrome", r=0.004, seg=1, dz=z)
        lay(0.53, -0.04, (1.0, 0.03, 0.014), "chrome", r=0.004, seg=1, dz=z)
    # the vacuum mattress under the trunk, moulded up against its back and its front
    lay(-0.34, 0.03, (0.68, 0.06, 0.58), "sc-vacuum-mat", r=0.025)
    lay(0.33, 0.03, (0.66, 0.06, 0.58), "sc-vacuum-mat", r=0.025)
    lay(-0.16, 0.105, (0.46, 0.1, 0.05), "sc-vacuum-mat", r=0.02, dz=-0.185)
    lay(-0.12, 0.09, (0.3, 0.07, 0.045), "sc-vacuum-mat", r=0.018, dz=0.185)

    # the torso on its right side: thorax (shoulder to costal margin) and abdomen over the break
    lay(-0.19, 0.225, (0.42, 0.33, 0.24), "sc-manikin", r=0.105, seg=3)
    lay(0.16, 0.215, (0.34, 0.3, 0.235), "sc-manikin", r=0.1, seg=2)
    k.ball(at(-0.37, 0.33, 0.035), 0.085, "sc-manikin", seg=14, squash=(1.0, 0.95, 1.05))      # the upper shoulder
    # the neck in line with the trunk, the head on a ring over a pillow
    k.tube(at(-0.4, 0.215), at(-0.53, 0.215), 0.052, "sc-manikin", seg=14)
    head = at(-0.62, 0.215)
    k.ball(head, 0.1, "sc-manikin", seg=16, squash=(1.1, 0.88, 0.92))
    k.ball((head[0] - 0.012, head[1] - 0.012, 0.086), 0.015, "sc-manikin", seg=8)               # the nose, facing front
    lay(-0.62, 0.065, (0.3, 0.07, 0.34), "white", r=0.03)
    k.torus(at(-0.62, 0.118), 0.072, 0.024, "teal", seg=20, ring=7, rot=(0, 0, flex))
    # the airway: the double-lumen tube taped at the mouth, its connector towards the anaesthetic end
    mouth = (head[0] + 0.012, head[1] - 0.04, 0.082)
    k.hose([mouth, (mouth[0] - 0.03, mouth[1] + 0.004, 0.14), (mouth[0] - 0.11, mouth[1] + 0.012, 0.165)], 0.007, "sc-clear-tube", seg=8, steps=3)
    k.cyl((mouth[0] - 0.125, mouth[1] + 0.013, 0.167), 0.01, 0.03, "blue", axis="x", seg=10, bevel=0.002)
    k.box((mouth[0], mouth[1], 0.081), (0.05, 0.016, 0.004), "white", r=0.002, seg=1)

    # the lower arm out in front on its board
    low = at(-0.36, 0.07)
    k.box((low[0] - 0.03, low[1] - 0.02, 0.31), (0.16, 0.024, 0.4), "navy", r=0.01)
    k.hose([(low[0], low[1] + 0.04, 0.09), (low[0] - 0.02, low[1] + 0.035, 0.27), (low[0] - 0.04, low[1] + 0.03, 0.46)], 0.04, "sc-manikin", seg=8, steps=2, r2=0.026)
    # the upper arm forward on the padded support at shoulder height, the elbow a little bent
    up = at(-0.37, 0.33, 0.07)
    elbow = (up[0] - 0.05, up[1] + 0.1, 0.33)
    hand = (elbow[0] - 0.25, elbow[1] + 0.03, 0.39)
    k.hose([up, ((up[0] + elbow[0]) / 2, up[1] + 0.07, 0.2), elbow], 0.046, "sc-manikin", seg=8, steps=2, r2=0.037)
    k.hose([elbow, ((elbow[0] + hand[0]) / 2, elbow[1] + 0.02, 0.36), hand], 0.036, "sc-manikin", seg=8, steps=2, r2=0.025)
    k.ball((hand[0] - 0.03, hand[1], hand[2] + 0.005), 0.03, "sc-manikin", seg=10, squash=(1.5, 0.5, 1))
    gx, gy, gz = (elbow[0] + hand[0]) / 2, elbow[1] - 0.035, 0.36
    k.box((gx, gy, gz), (0.36, 0.03, 0.14), "navy", r=0.014)
    for sgn in (-1, 1):
        k.box((gx, gy + 0.03, gz + sgn * 0.066), (0.36, 0.06, 0.02), "navy", r=0.009, seg=2)
    k.box((gx - 0.02, gy + 0.062, gz), (0.04, 0.004, 0.16), "white", r=0.001, seg=1)
    clamp = at(-0.62, -0.04, 0.29)
    k.box(clamp, (0.05, 0.06, 0.04), "coal", r=0.008, seg=2)
    k.path([clamp, (clamp[0], gy - 0.06, 0.3), (gx - 0.04, gy - 0.016, gz)], 0.012, "chrome", seg=10)

    # the drape over hips and legs — the upper leg straight, the lower bent forward, a pillow between — and down both sides
    lay(0.42, 0.2, (0.36, 0.31, 0.36), "sc-drape", r=0.12, seg=2)
    lay(0.74, 0.215, (0.56, 0.17, 0.2), "sc-drape", r=0.075, seg=2, dz=-0.05)
    lay(0.6, 0.13, (0.34, 0.2, 0.26), "sc-drape", r=0.08, seg=2, dz=0.12)
    lay(0.86, 0.1, (0.36, 0.14, 0.2), "sc-drape", r=0.06, seg=2, dz=0.14)
    lay(0.66, 0.012, (0.84, 0.014, 0.62), "sc-drape", r=0.004, seg=1)
    for z in (0.314, -0.314):
        lay(0.66, -0.12, (0.84, 0.26, 0.006), "sc-drape", r=0.002, seg=1, dz=z)

    # the chest wall: how far its surface drops away from the mid-axillary line (the thorax is rounded)
    top = 0.39
    drop = lambda dz: 0.0 if abs(dz) < 0.015 else 0.105 - math.sqrt(max(0.0, 0.105 ** 2 - (abs(dz) - 0.015) ** 2))  # noqa: E731
    skin = lambda s_, dz, out=0.0: at(s_, top - drop(dz) + out, dz)  # noqa: E731

    # four towels round the field: one at the axilla, one below the costal margin, one along the front, one along the back
    lay(-0.41, 0.232, (0.07, 0.345, 0.255), "sc-drape-green", r=0.11, seg=2)
    lay(0.07, 0.224, (0.09, 0.325, 0.25), "sc-drape-green", r=0.105, seg=2)
    for sgn in (-1, 1):
        lay(-0.17, top - drop(0.108) + 0.001, (0.44, 0.007, 0.045), "sc-drape-green", r=0.003, seg=1, dz=sgn * 0.108, turn=sgn * 62)

    # on the skin, in a skin marker's violet: the anterior, mid- and posterior axillary lines
    for z in (0.075, 0.0, -0.075):
        k.tube(skin(-0.34, z, 0.0012), skin(0.0, z, 0.0012), 0.0015, "purple", seg=5)
    # utility incision — 4th space, just in front of latissimus dorsi: a wound protector, a lung forceps through it
    u = skin(-0.27, 0.075, 0.003)
    k.torus(u, 0.028, 0.005, "white", seg=20, ring=6, stretch=(1.3, 0.75), rot=(-32, 0, flex))
    f0, f1 = (u[0] + 0.01, u[1] - 0.04, u[2] - 0.02), (u[0] - 0.05, u[1] + 0.24, u[2] + 0.19)
    k.tube(f0, f1, 0.0035, "chrome", seg=8)
    for sgn in (-1, 1):
        k.torus((f1[0] + sgn * 0.012, f1[1] + 0.012, f1[2] + 0.008), 0.011, 0.0026, "steel", axis="z", seg=14, ring=5, rot=(-35, 0, 0))
    # camera port — low and anterior, at about the level of the top of the diaphragm: the port, the scope standing
    # in it towards the apex, the camera head with the light cable and the camera cable falling away behind
    c = skin(-0.07, 0.07)
    k.cyl((c[0], c[1] + 0.008, c[2] + 0.004), 0.014, 0.03, "white", seg=16, bevel=0.003, rot=(28, 0, 0))
    tip = (c[0] - 0.045, c[1] - 0.04, c[2] - 0.02)
    eye = (c[0] + 0.15, c[1] + 0.27, c[2] + 0.12)
    k.tube(tip, eye, 0.005, "chrome", seg=10)
    n = math.sqrt(sum((e - t) ** 2 for e, t in zip(eye, tip)))
    ux, uy, uz = ((e - t) / n for e, t in zip(eye, tip))
    along_scope = lambda d: (eye[0] + ux * d, eye[1] + uy * d, eye[2] + uz * d)  # noqa: E731
    k.tube(along_scope(-0.005), along_scope(0.02), 0.014, "steel", seg=14)
    k.tube(along_scope(0.022), along_scope(0.085), 0.02, "plastic", seg=14)
    post = along_scope(-0.03)
    k.tube(post, (post[0], post[1], post[2] - 0.035), 0.006, "steel", seg=8)
    back = along_scope(0.087)
    floor_back = at(0.2, -0.1, -0.33)
    k.hose([back, (back[0] + 0.05, back[1] + 0.02, back[2] - 0.08), (back[0] + 0.03, back[1] - 0.22, back[2] - 0.26), floor_back], 0.0045, "coal", seg=6, steps=3)
    k.hose([(post[0], post[1], post[2] - 0.04), (c[0] + 0.12, c[1] + 0.1, -0.2), (floor_back[0] - 0.08, floor_back[1], -0.33)], 0.004, "coal", seg=6, steps=3)
    # the scope holder: clamped to the side rail behind, an arm up to the scope
    rail = at(0.26, -0.04, -0.29)
    k.box(rail, (0.05, 0.06, 0.04), "coal", r=0.008, seg=2)
    grip = along_scope(-0.07)
    k.path([rail, (rail[0], rail[1] + 0.36, rail[2] + 0.02), (rail[0] - 0.07, rail[1] + 0.52, rail[2] + 0.15), grip], 0.009, "chrome", seg=10)
    k.ball(grip, 0.016, "coal", seg=10)
    # the third port, at the camera port's level further back: straight down from the scapula
    p = skin(-0.07, -0.09)
    k.cyl((p[0], p[1] + 0.006, p[2] - 0.004), 0.011, 0.024, "white", seg=14, bevel=0.002, rot=(-35, 0, 0))

    # the monitor on its pole at the back of the head end
    scr = eq.screens()[0]
    px, py, pz = scr["p"]
    foot = at(-0.82, -0.04, pz - 0.03)
    k.box(foot, (0.05, 0.06, 0.05), "coal", r=0.008, seg=2)
    k.cyl((foot[0], (foot[1] + py) / 2, foot[2]), 0.016, py - foot[1], "chrome", seg=14)
    k.box(((foot[0] + px) / 2, py, pz - 0.03), (abs(px - foot[0]), 0.05, 0.03), "steel", r=0.008, seg=2)
    k.box((px, py, pz - 0.028), (scr["s"][0] + 0.06, scr["s"][1] + 0.06, 0.05), "sc-matte-black", r=0.014)
    k.screen_bezel(scr, "sc-matte-black", border=0.016, depth=0.01, r=0.004)
    k.box((px + scr["s"][0] / 2 - 0.02, py - scr["s"][1] / 2 - 0.018, pz), (0.03, 0.008, 0.004), "led-green", r=0.002, seg=1)
