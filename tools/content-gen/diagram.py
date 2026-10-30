"""Clean zoning diagrams of the compiled surgical centre (docs figures).

Usage: python3 diagram.py <compiled facility json> <output dir>
(`clinicalcraft facilities compile surgical-centre --out compiled.json` with the pack in contentDirs.)
Needs Pillow and a CJK font (WenQuanYi Zen Hei by default; set $CJK_FONT to override)."""
import json
import sys
from PIL import Image, ImageDraw, ImageFont

compiled = json.load(open(sys.argv[1]))
outdir = sys.argv[2]
SC = 15  # px per metre
MX, MZ = 60, 96
BX0, BX1, BZ0, BZ1 = -32, 32, -22, 22
W = int((BX1 - BX0) * SC + 2 * MX + 330)
H = int((BZ1 - BZ0) * SC + MZ + 60)
import os
FONT = os.environ.get("CJK_FONT", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
f_title = ImageFont.truetype(FONT, 26)
f_room = ImageFont.truetype(FONT, 13)
f_small = ImageFont.truetype(FONT, 11)
f_leg = ImageFont.truetype(FONT, 14)


def px(x, z):
    return (MX + (x - BX0) * SC, MZ + (z - BZ0) * SC)


ZONES = {
    "restricted": ("#f3c1b8", "Restricted · 限制区"),
    "semi": ("#f6e3a8", "Semi-restricted · 半限制区"),
    "transition": ("#cfe6e0", "Transition (changing / transfer) · 过渡区"),
    "unrestricted": ("#d6ebc7", "Unrestricted · 非限制区"),
    "vertical": ("#d4d7da", "Lifts & stairs · 垂直交通"),
    "cssd-dirty": ("#e6c9b0", "CSSD dirty (decontamination) · 去污区"),
    "cssd-clean": ("#f6e3a8", "CSSD clean (packing, sterilising) · 检查包装灭菌区"),
    "cssd-sterile": ("#f3c1b8", "CSSD sterile store · 无菌物品存放区"),
    "clinical": ("#c9dcf0", "Clinical support (lab, blood bank) · 医技支持"),
    "education": ("#ddd0ee", "Education & simulation · 教学与模拟"),
    "public": ("#d6ebc7", "Public & admissions · 公共与入院"),
    "service": ("#e3e3e3", "Service & plant · 后勤与机房"),
}


def zone_of(r):
    i, k = r["id"], r["kind"]
    if k in ("elevator", "stairwell"):
        return "vertical"
    if r.get("level") == "L1":
        if i.startswith(("or-", "prep-")) or i == "l1-core":
            return "restricted"
        if i.startswith("changing") or i == "l1-transfer":
            return "transition"
        if i in ("l1-lobby", "l1-staff-corridor"):
            return "unrestricted"
        return "semi"
    if i == "l0-decon" or i == "l0-dirty-lift":
        return "cssd-dirty"
    if i == "l0-iah":
        return "cssd-clean"
    if i == "l0-sterile-store":
        return "cssd-sterile"
    if i in ("l0-lab", "l0-blood-bank"):
        return "clinical"
    if i in ("l0-skills", "l0-observation", "l0-sim-or", "l0-debrief"):
        return "education"
    if i in ("l0-hall", "l0-family", "l0-day-surgery") or i.startswith("l0-consult"):
        return "public"
    return "service"


def wall_line(rect, side):
    x0, x1 = rect["x"] - rect["w"] / 2, rect["x"] + rect["w"] / 2
    z0, z1 = rect["z"] - rect["d"] / 2, rect["z"] + rect["d"] / 2
    if side == "n":
        return "x", z0, x0, x1, rect["x"]
    if side == "s":
        return "x", z1, x0, x1, rect["x"]
    if side == "w":
        return "z", x0, z0, z1, rect["z"]
    return "z", x1, z0, z1, rect["z"]


def draw_level(level, title, fname, flows, notes):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((MX, 22), title, font=f_title, fill="#1d2b2b")
    rooms = [r for r in compiled["rooms"] if r.get("level", "L0") == level]
    used = set()
    for r in rooms:
        z = zone_of(r)
        used.add(z)
        rc = r["rect"]
        a = px(rc["x"] - rc["w"] / 2, rc["z"] - rc["d"] / 2)
        b = px(rc["x"] + rc["w"] / 2, rc["z"] + rc["d"] / 2)
        d.rectangle([a, b], fill=ZONES[z][0], outline="#9aa5a8", width=1)
    # partitions with the engine's dedupe (first room to build a stretch owns it and its openings)
    built = {}
    for r in compiled["rooms"]:
        if r.get("level", "L0") != level:
            continue
        for p in r.get("partitions", []):
            axis, line, s0, s1, centre = wall_line(r["rect"], p["side"])
            key = (axis, round(line, 2))
            segs = [(s0, s1)]
            for a0, a1 in built.get(key, []):
                nxt = []
                for c0, c1 in segs:
                    if a1 <= c0 or a0 >= c1:
                        nxt.append((c0, c1))
                    else:
                        if a0 > c0:
                            nxt.append((c0, a0))
                        if a1 < c1:
                            nxt.append((a1, c1))
                segs = nxt
            built.setdefault(key, []).append((s0, s1))
            for c0, c1 in segs:
                if c1 - c0 < 0.05:
                    continue
                pa = px(c0, line) if axis == "x" else px(line, c0)
                pb = px(c1, line) if axis == "x" else px(line, c1)
                d.line([pa, pb], fill="#3c4446", width=3)
                for o in p.get("openings", []):
                    oc = centre + o.get("offset", 0)
                    g0, g1 = max(c0, oc - o.get("width", 2) / 2), min(c1, oc + o.get("width", 2) / 2)
                    if g1 - g0 <= 0.05:
                        continue
                    qa = px(g0, line) if axis == "x" else px(line, g0)
                    qb = px(g1, line) if axis == "x" else px(line, g1)
                    d.line([qa, qb], fill="#7fc4e8" if o.get("kind") == "window" else "white", width=4)
    # building outline
    d.rectangle([px(BX0, BZ0), px(BX1, BZ1)], outline="#1d2b2b", width=4)
    # connectors
    for c in compiled["connectors"]:
        for s in c["stops"]:
            if s["level"] == level:
                x, y = px(s["x"], s["z"])
                col = "#2f7fd1" if c["kind"] == "elevator" else "#b5479a"
                d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col, outline="white", width=2)
        if c["kind"] == "stairs":
            a, b = c["stops"][0], c["stops"][1]
            w = c.get("width", 2) / 2
            if a["z"] == b["z"]:
                box = [px(min(a["x"], b["x"]), a["z"] - w), px(max(a["x"], b["x"]), a["z"] + w)]
            else:
                box = [px(a["x"] - w, min(a["z"], b["z"])), px(a["x"] + w, max(a["z"], b["z"]))]
            d.rectangle(box, outline="#b5479a", width=2)
            (x0, y0), (x1, y1) = box
            steps = 12
            for k in range(1, steps):
                if a["z"] == b["z"]:
                    xx = x0 + (x1 - x0) * k / steps
                    d.line([(xx, y0), (xx, y1)], fill="#d9b8d0", width=1)
                else:
                    yy = y0 + (y1 - y0) * k / steps
                    d.line([(x0, yy), (x1, yy)], fill="#d9b8d0", width=1)
    # patient slots
    for s in compiled["patientSlots"]:
        room = next(r for r in compiled["rooms"] if r["id"] == s["room"])
        if room.get("level", "L0") != level:
            continue
        x, y = px(s["x"], s["z"])
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill="#3f8f5a")
    # labels (English, then Chinese; long English names wrap at " · ")
    for r in rooms:
        rc = r["rect"]
        if r["kind"] == "elevator" or rc["w"] * rc["d"] < 8:
            continue
        en, zh = label_en(r), short_zh(r["name"]["zh-CN"])
        cx, cy = px(rc["x"], rc["z"])
        maxw = rc["w"] * SC - 6
        lines = [en]
        if d.textlength(en, font=f_room) > maxw and " · " in en:
            lines = en.split(" · ", 1)
        rows = []
        for t in lines:
            font = f_room if d.textlength(t, font=f_room) <= maxw else f_small
            if d.textlength(t, font=font) <= maxw:
                rows.append((t, font))
        if d.textlength(zh, font=f_small) <= maxw:
            rows.append((zh, f_small))
        y = cy - 8 * len(rows)
        for t, font in rows:
            tw = d.textlength(t, font=font)
            d.text((cx - tw / 2, y), t, font=font, fill="#1d2b2b")
            y += 16
    # flows
    for name, col, pts in flows:
        xy = [px(x, z) for x, z in pts]
        d.line(xy, fill=col, width=4, joint="curve")
        (xa, ya), (xb, yb) = xy[-2], xy[-1]
        import math
        ang = math.atan2(yb - ya, xb - xa)
        for s in (2.6, -2.6):
            d.line([(xb, yb), (xb - 14 * math.cos(ang + s / 6), yb - 14 * math.sin(ang + s / 6))], fill=col, width=4)
    # legend
    lx = MX + (BX1 - BX0) * SC + 30
    ly = MZ
    d.text((lx, ly - 30), "Legend · 图例", font=f_leg, fill="#1d2b2b")
    for z in [k for k in ZONES if k in used]:
        col, lab = ZONES[z]
        d.rectangle([lx, ly, lx + 22, ly + 16], fill=col, outline="#9aa5a8")
        d.text((lx + 30, ly), lab, font=f_small, fill="#1d2b2b")
        ly += 24
    ly += 8
    for name, col, _ in flows:
        d.line([(lx, ly + 8), (lx + 22, ly + 8)], fill=col, width=4)
        d.text((lx + 30, ly), name, font=f_small, fill="#1d2b2b")
        ly += 22
    for col, lab in (("#2f7fd1", "Lift stop · 电梯"), ("#b5479a", "Stairs · 楼梯"), ("#3f8f5a", "Patient slot · 患者位")):
        d.ellipse([lx + 5, ly + 2, lx + 17, ly + 14], fill=col)
        d.text((lx + 30, ly), lab, font=f_small, fill="#1d2b2b")
        ly += 22
    d.line([(lx, ly + 10), (lx + 22, ly + 10)], fill="white", width=4)
    d.rectangle([lx - 1, ly + 7, lx + 23, ly + 13], outline="#3c4446")
    d.text((lx + 30, ly + 2), "Door / opening · 门", font=f_small, fill="#1d2b2b")
    ly += 30
    for line in notes:
        d.text((lx, ly), line, font=f_small, fill="#465354")
        ly += 18
    # scale bar + north
    sx, sy = MX, H - 34
    d.line([(sx, sy), (sx + 10 * SC, sy)], fill="#1d2b2b", width=3)
    d.text((sx + 10 * SC + 8, sy - 8), "10 m", font=f_small, fill="#1d2b2b")
    nx, ny = MX + 220, H - 40
    d.polygon([(nx, ny - 14), (nx - 7, ny + 6), (nx + 7, ny + 6)], fill="#1d2b2b")
    d.text((nx + 12, ny - 10), "N", font=f_leg, fill="#1d2b2b")
    im.save(f"{outdir}/{fname}")


def short(en):
    rep = {"(semi-restricted)": "", "Operating department lobby (lifts)": "Lobby & lifts", "OR 1 · Hybrid (cardiovascular & neuro-interventional)": "OR 1 · Hybrid",
           "OR 3 · Cardiac & transplant (ultra-clean)": "OR 3 · Cardiac (UCV)", "OR 4 · Orthopaedic & neurosurgery (ultra-clean)": "OR 4 · Ortho/neuro (UCV)",
           "OR 5 · General & colorectal MIS": "OR 5 · General MIS", "OR 6 · Urology, gynaecology & head-and-neck MIS": "OR 6 · MIS",
           "OR 7 · Emergency & obstetric (24/7)": "OR 7 · Emergency & obstetric", "OR 8 · Negative-pressure isolation": "OR 8 · Neg-pressure isolation",
           "Post-anaesthesia care unit (8 bays)": "PACU (8 bays)", "Pre-operative holding (5 bays)": "Pre-op holding (5)", "OR 1 hybrid control room": "Hybrid control",
           "Theatre pharmacy & controlled drugs": "Theatre pharmacy", "Soiled utility & dirty lift": "Soiled · dirty lift",
           "Ground-floor main corridor": "Main corridor", "Ground-floor service corridor": "Service corridor", "Main hall & surgical admissions": "Main hall & admissions",
           "Day-surgery admission & discharge": "Day surgery", "CSSD · sterile store & dispatch": "CSSD sterile store", "CSSD · inspection, packing & sterilisation": "CSSD packing & sterilising",
           "CSSD · decontamination": "CSSD decontamination", "Theatre stores & clean linen": "Theatre stores & linen", "OR live-video observation & conference room": "OR live-video room",
           "Perioperative laboratory (stat lab)": "Perioperative lab", "Pre-anaesthesia assessment clinic 1": "Pre-anaes. 1", "Pre-anaesthesia assessment clinic 2": "Pre-anaes. 2",
           "Simulation control & debrief": "Sim debrief", "OR air-handling plant room": "OR AHU plant room", "Surgical skills & simulation lab": "Skills lab",
           "High-fidelity simulation OR": "Simulation OR", "Blood bank & transfusion": "Blood bank", "Staff changing · women": "Changing (F)", "Staff changing · men": "Changing (M)",
           "Staff corridor (unrestricted)": "Staff corridor", "Theatre control desk": "Control desk", "Patient transfer zone": "Transfer zone", "Frozen-section laboratory": "Frozen section",
           "Anaesthesia workroom": "Anaes. workroom", "Sterile core (restricted)": "STERILE CORE", "North clean corridor ": "North clean corridor", "South clean corridor ": "South clean corridor"}
    en = rep.get(en, en)
    return rep.get(en.strip(), en.strip())


def short_zh(zh):
    if zh.startswith("消毒供应中心 · "):
        return zh.split(" · ", 1)[1]
    return zh.split("（")[0].split(" · ")[0]


def label_en(r):
    i = r["id"]
    if i.startswith("scrub-"):
        return "Scrub"
    if i.startswith("prep-"):
        return "Set-up"
    if i == "or-8-ante":
        return "Buffer"
    if i == "hybrid-control":
        return "Control"
    return short(r["name"]["en"])


L1_FLOWS = [
    ("Patient · 患者", "#2f7fd1", [(1.5, 17.0), (-6.5, 16.6), (-6.5, 8.5), (4.3, 8.5), (4.3, 5.2)]),
    ("Patient to PACU · 术后复苏", "#6aa9e8", [(-6.5, 8.5), (-25.0, 8.5), (-25.0, 12.0)]),
    ("Staff · 医护", "#3f8f5a", [(4.0, 20.6), (7.1, 20.6), (7.1, 16.5), (11.9, 12.0), (11.9, 8.9)]),
    ("Sterile supplies · 无菌物品", "#8a5bc4", [(-4.8, -6.0), (2.9, -6.0), (2.9, -9.3)]),
    ("Soiled return · 污物回收", "#a0522d", [(17.5, 8.5), (30.5, 8.5), (30.5, 4.5), (28.0, 4.5), (27.5, 0.0)]),
]
L0_FLOWS = [
    ("Instruments (one way) · 器械单向流程", "#a0522d", [(27.5, 1.0), (24.5, -3.0), (23.0, -8.0)]),
    ("Clean → sterile · 洁净 → 无菌", "#8a5bc4", [(20.5, -8.0), (8.0, -8.0), (5.0, -7.5), (-4.6, -6.0)]),
    ("Visitors & patients · 来访与患者", "#2f7fd1", [(11.0, 23.0), (11.0, 19.0), (6.2, 16.6)]),
]
draw_level("L1", "First floor · Operating department  二层 · 手术部", "surgical-floor-L1-zoning.png", L1_FLOWS,
           ["8 ORs ring a central sterile core;", "clean corridors loop round them.", "Staff enter via changing rooms,", "patients via the transfer zone.",
            "Clean lift: CSSD → sterile core.", "Dirty lift: soiled utility → decon."])
draw_level("L0", "Ground floor · Admissions, CSSD & simulation  一层 · 入院、消毒供应与模拟", "surgical-floor-L0-zoning.png", L0_FLOWS,
           ["CSSD flows one way:", "decontamination → packing &", "sterilising → sterile store.", "Washer-disinfectors and", "sterilisers are pass-through."])
print("ok")
