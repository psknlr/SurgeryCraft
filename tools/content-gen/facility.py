"""SurgeryCraft Surgical Centre: ground floor (admissions, CSSD, lab, simulation) + first-floor operating department."""
from common import L, num
import footprints as fp
from templates import SEMI, OR_ROLES, CORE_ROLES, OR_WALL, CLEAN_WALL

FACILITY_ID = "surgical-centre"
ISSUES = []

ROOMS = []
PLACEMENTS = []
STAFF = []
INSTANCES = []
ACCESS = []
_room_rect = {}
_room_level = {}


def R(x0, x1, z0, z1):
    return {"x": num((x0 + x1) / 2), "z": num((z0 + z1) / 2), "w": num(x1 - x0), "d": num(z1 - z0)}


def lights_for(x0, x1, z0, z1, step=5.0):
    nx = max(1, round((x1 - x0) / step))
    nz = max(1, round((z1 - z0) / step))
    return [{"x": num(x0 + (i + 0.5) * (x1 - x0) / nx), "z": num(z0 + (j + 0.5) * (z1 - z0) / nz)} for j in range(nz) for i in range(nx)]


def room(id, name, kind, level, x0, x1, z0, z1, floor=None, partitions=(), sign=None, lights=None, step=5.0):
    r = {"id": id, "name": name, "kind": kind, "building": "main", "level": level, "rect": R(x0, x1, z0, z1)}
    if floor:
        r["floor"] = floor
    if partitions:
        r["partitions"] = list(partitions)
    if sign:
        r["sign"] = sign
    r["lights"] = lights if lights is not None else lights_for(x0, x1, z0, z1, step)
    ROOMS.append(r)
    _room_rect[id] = (x0, x1, z0, z1)
    _room_level[id] = level
    return r


def part(side, openings=(), style=None):
    p = {"side": side}
    if style:
        p.update(style)
    if openings:
        p["openings"] = list(openings)
    return p


def door(kind, width, offset=0, height=None):
    o = {"kind": kind, "offset": num(offset), "width": num(width)}
    if height:
        o["height"] = num(height)
    return o


def window(width, offset=0, sill=1.0, height=1.3):
    return {"kind": "window", "offset": num(offset), "width": num(width), "sill": num(sill), "height": num(height)}


def P(id, type, x, z, rot=0, room=None, label=None, **kw):
    p = {"id": id, "type": type, "x": num(x), "z": num(z)}
    if rot:
        p["rot"] = rot
    p["room"] = room
    if label:
        p["label"] = label
    p.update(kw)
    x0, x1, z0, z1 = _room_rect[room]
    if not (x0 - 0.05 <= x <= x1 + 0.05 and z0 - 0.05 <= z <= z1 + 0.05):
        ISSUES.append(f"placement {id} at ({x},{z}) outside room {room}")
    PLACEMENTS.append(p)
    return p


def d_of(type):
    return fp.TYPES[type]["footprint"]["d"]


# wall-backed placements inside an authored room (partitions / building walls 0.35 thick)
def on_n(id, type, x, room, label=None, **kw):
    return P(id, type, x, _room_rect[room][2] + 0.175 + d_of(type) / 2, 0, room, label, **kw)


def on_s(id, type, x, room, label=None, **kw):
    return P(id, type, x, _room_rect[room][3] - 0.175 - d_of(type) / 2, 180, room, label, **kw)


def on_w(id, type, z, room, label=None, **kw):
    return P(id, type, _room_rect[room][0] + 0.175 + d_of(type) / 2, z, 90, room, label, **kw)


def on_e(id, type, z, room, label=None, **kw):
    return P(id, type, _room_rect[room][1] - 0.175 - d_of(type) / 2, z, 270, room, label, **kw)


import templates as _tpl

TEMPLATE_SIZES = {t["id"]: (t["size"]["w"], t["size"]["d"]) for t in _tpl.TEMPLATES}
TEMPLATE_SIZES.update({"teaching-room": (10, 8), "outpatient-consult": (6, 8), "clinical-lab": (10, 8), "elevator-cabin": (2.4, 2.4)})


def inst(id, template, x, z, rot=0, level="L1", overrides=None):
    w, d = TEMPLATE_SIZES[template]
    if rot in (90, 270):
        w, d = d, w
    _room_rect[id] = (x - w / 2, x + w / 2, z - d / 2, z + d / 2)
    _room_level[id] = level
    i = {"id": id, "template": template, "x": num(x), "z": num(z)}
    if rot:
        i["rot"] = rot
    i["level"] = level
    if overrides:
        i["overrides"] = overrides
    INSTANCES.append(i)
    return i


def staff(id, role, name, room, x, z, rot=0, greeting=None, level=None):
    s = {"id": id, "role": role, "name": name, "room": room, "x": num(x), "z": num(z)}
    if rot:
        s["rot"] = rot
    if greeting:
        s["greeting"] = greeting
    STAFF.append(s)


def access(id, name, level, x0, x1, z0, z1, roles):
    ACCESS.append({"id": id, "name": name, "level": level, "rect": R(x0, x1, z0, z1), "roles": roles})


STEEL = {"material": "steel"}
SIGN_OR = "#3f8f5a"

# ======================================================================================== L1 · operating department
L1 = "L1"

# --- authored rooms (built before the template instances: they own the walls they share) ---
room("l1-corridor-n", L("北侧洁净走廊（半限制区）", "North clean corridor (semi-restricted)"), "corridor", L1, -32, 32, -22, -19, "lino",
     sign={"text": L("半限制区 · 着洗手衣、帽子、口罩", "Semi-restricted · scrubs, cap & mask"), "side": "n", "color": "#cf3b30"}, step=8)
room("l1-corridor-w", L("西侧洁净走廊", "West clean corridor"), "corridor", L1, -32, -29, -19, 10, "lino", step=7)
room("l1-corridor-e", L("东侧洁净走廊", "East clean corridor"), "corridor", L1, 29, 32, -19, 10, "lino", step=7)
room("l1-corridor-s", L("南侧洁净走廊（半限制区）", "South clean corridor (semi-restricted)"), "corridor", L1, -29, 29, 7, 10, "lino", step=8)
room("l1-core", L("无菌核心区（限制区）", "Sterile core (restricted)"), "storage", L1, -29, 29, -10, -2, "sc-core-floor",
     [part("w", [door("sliding-door", 1.6, 0, 2.6)], OR_WALL), part("e", (), OR_WALL)],
     {"text": L("无菌核心区 · 限制区", "Sterile core · restricted"), "color": "#2f7fd1"}, step=6)
room("l1-drug-room", L("手术部卫星药房与麻醉药品室", "Theatre pharmacy & controlled drugs"), "pharmacy", L1, -29, -22, -2, 2.5, "lino",
     [part("w", [door("door", 1.4, 0, 2.6)], CLEAN_WALL), part("n", (), OR_WALL), part("e", (), CLEAN_WALL), part("s", (), CLEAN_WALL)],
     {"text": L("卫星药房 · 麻醉药品", "Theatre pharmacy"), "color": "#a397bc"})
room("l1-equipment-store", L("设备存放间", "Equipment store"), "storage", L1, -29, -22, 2.5, 7, "lino",
     [part("s", [door("double-door", 2.0, 0, 2.8)], CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL)],
     {"text": L("设备间", "Equipment store")})
room("l1-soiled", L("污物间（污梯）", "Soiled utility & dirty lift"), "storage", L1, 26, 29, -2, 7, "sc-cssd-floor",
     [part("n", (), OR_WALL), part("w", (), CLEAN_WALL), part("s", (), CLEAN_WALL), part("e", [door("door", 1.6, 2.0, 2.6)], CLEAN_WALL)],
     {"text": L("污物间 · 污梯", "Soiled utility · dirty lift"), "color": "#d65f3a"})
room("l1-dirty-lift", L("污物电梯", "Dirty lift"), "elevator", L1, 26, 29, -2, 0.6, "steel",
     [part("s", [door("sliding-door", 1.4, 0, 2.4)], STEEL)], lights=[{"x": 27.5, "z": -0.7}])
room("l1-transfer", L("换床间（患者交接区）", "Patient transfer zone"), "reception", L1, -9, -4, 10, 14, "sc-pacu-floor",
     [part("w", [door("door", 1.6, 0, 2.6)], CLEAN_WALL), part("n", [door("sliding-door", 2.0, 0, 2.8)], CLEAN_WALL), part("s", [door("sliding-door", 2.0, 0, 2.8)], CLEAN_WALL), part("e", (), CLEAN_WALL)],
     {"text": L("换床间 · 红线内为半限制区", "Transfer zone · red line = semi-restricted"), "side": "e", "color": "#cf3b30"})
room("l1-control", L("手术部控制台（手术协调）", "Theatre control desk"), "nurse-station", L1, -4, 6, 10, 14, "lino",
     [part("n", [door("opening", 6.0, 0, 3)], CLEAN_WALL), part("s", [window(3.0, 0, 0.95, 1.2)], CLEAN_WALL), part("e", (), CLEAN_WALL)],
     {"text": L("手术部控制台", "Theatre control"), "side": "s", "color": SIGN_OR})
room("l1-lobby", L("手术部入口厅（电梯厅）", "Operating department lobby (lifts)"), "reception", L1, -9, 6, 14, 22, "stone",
     [part("w", (), CLEAN_WALL), part("e", [door("opening", 2.6, 2.5, 3)], CLEAN_WALL)],
     {"text": L("手术部 · 员工经更衣室 · 患者经换床间", "Operating dept · staff via changing · patients via transfer"), "side": "w", "color": SIGN_OR})
room("l1-staff-corridor", L("员工通道（非限制区）", "Staff corridor (unrestricted)"), "corridor", L1, 6, 20, 19, 22, "lino", step=7)
room("l1-lounge", L("医护休息室", "Staff lounge"), "office", L1, 20, 26, 10, 22, "wood",
     [part("n", [door("door", 1.6, 0, 2.6)], CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL)],
     {"text": L("休息室", "Staff lounge")})
room("l1-escape-stair", L("疏散楼梯", "Escape stair"), "stairwell", L1, 26, 32, 10, 22, "stone",
     [part("n", [door("door", 1.6, 0, 2.6)], CLEAN_WALL)],
     {"text": L("疏散楼梯", "Escape stair"), "color": "#3f8f5a"})

# --- placements in authored L1 rooms ---
on_n("l1-crash-cart-n", "crash-cart", -1.5, "l1-corridor-n", L("抢救车", "Crash cart"))
on_n("l1-defib-n", "defibrillator", -0.4, "l1-corridor-n", L("除颤仪", "Defibrillator"))
on_n("l1-gas-valves-n", "sc-gas-zone-valve", -8.0, "l1-corridor-n", L("医用气体区域阀箱（北区）", "Medical-gas zone valves (north)"))
on_n("l1-sanitizer-n", "hand-sanitizer", 6.5, "l1-corridor-n", L("手消毒液", "Hand rub"))
on_s("l1-crash-cart-s", "crash-cart", 4.9, "l1-corridor-s", L("抢救车", "Crash cart"))
on_s("l1-defib-s", "defibrillator", 5.85, "l1-corridor-s", L("除颤仪", "Defibrillator"))
on_s("l1-gas-valves-s", "sc-gas-zone-valve", -21.0, "l1-corridor-s", L("医用气体区域阀箱（南区）", "Medical-gas zone valves (south)"))
on_s("l1-red-line-transfer", "sc-zone-line", -6.5, "l1-corridor-s")
P("l1-red-line-f", "sc-zone-line", 11.9, 9.65, 0, "l1-corridor-s")
P("l1-red-line-m", "sc-zone-line", 18.9, 9.65, 0, "l1-corridor-s")

# sterile core: back-to-back sterile rack islands, case carts, IUSS, implants
for k, xs in enumerate(((-24.75, -23.25, -21.75), (-17.25, -15.75, -14.25), (-1.5, 0.0, 1.5), (8.25, 9.75, 11.25), (17.25, 18.75, 20.25))):
    for j, x in enumerate(xs):
        P(f"l1-rack-{k + 1}{j + 1}a", "sc-sterile-rack", x, -5.7, 0, "l1-core", L("无菌存放架", "Sterile rack"))
        P(f"l1-rack-{k + 1}{j + 1}b", "sc-sterile-rack", x, -6.3, 180, "l1-core", L("无菌存放架", "Sterile rack"))
for k, x in enumerate((-19.0, -5.5, 6.5, 19.5)):
    on_n(f"l1-case-cart-n{k + 1}", "sc-case-cart", x, "l1-core", L("器械配送车（已备台）", "Case cart (picked for a case)"))
for k, x in enumerate((-20.0, -7.0, 5.0, 16.0)):
    on_s(f"l1-case-cart-s{k + 1}", "sc-case-cart", x, "l1-core", L("器械配送车（已备台）", "Case cart (picked for a case)"))
on_n("l1-iuss", "sc-iuss-steriliser", 24.5, "l1-core", L("快速压力蒸汽灭菌器", "Immediate-use steam steriliser"))
on_s("l1-core-warming-1", "sc-warming-cabinet", 22.0, "l1-core", L("加温柜", "Warming cabinet"))
on_s("l1-core-warming-2", "sc-warming-cabinet", 23.0, "l1-core", L("加温柜", "Warming cabinet"))
on_e("l1-implants", "pharmacy-shelves", -6.0, "l1-core", L("植入物与假体库", "Implant & prosthesis store"))
on_e("l1-implants-2", "cabinet", -8.5, "l1-core", L("植入物柜（可追溯）", "Implant cabinet (traceable)"))
P("l1-core-sanitizer", "hand-sanitizer", -28.4, -7.6, 0, "l1-core", L("手消毒液", "Hand rub"))

# theatre pharmacy & equipment store
on_n("l1-drugs-1", "medication-cabinet", -27.5, "l1-drug-room", L("自动发药柜", "Automated dispensing cabinet"))
on_n("l1-drugs-2", "medication-cabinet", -26.4, "l1-drug-room", L("麻醉/精神药品柜（双锁）", "Controlled-drugs cabinet (double-locked)"))
on_n("l1-drug-fridge", "medication-fridge", -25.3, "l1-drug-room", L("药品冰箱", "Drug fridge"))
on_e("l1-drug-shelves", "pharmacy-shelves", 0.25, "l1-drug-room", L("药品货架", "Pharmacy shelves"))
on_s("l1-drug-desk", "desk", -26.5, "l1-drug-room", L("核对台", "Checking desk"))
P("l1-drug-records", "records-terminal", -25.2, 1.9, 0, "l1-drug-room", L("药房终端", "Pharmacy terminal"))
P("l1-drug-chair", "office-chair", -26.5, 1.0, 0, "l1-drug-room")
staff("l1-pharmacist", "pharmacist", L("孙药师（手术部药房）", "Pharmacist Sun (theatre pharmacy)"), "l1-drug-room", -24.4, 0.3, 270,
      L("麻醉药品双人核对、逐支登记，空安瓿要交回。", "Controlled drugs are checked by two people and logged one by one — return the empty ampoules."))
P("l1-spare-c-arm", "c-arm", -27.5, 3.3, 90, "l1-equipment-store", L("备用移动 C 形臂", "Spare mobile C-arm"))
P("l1-spare-lap-tower", "sc-laparoscopy-tower", -25.6, 3.2, 0, "l1-equipment-store", L("备用腹腔镜系统", "Spare laparoscopy tower"))
P("l1-spare-pump-1", "infusion-pump", -24.2, 3.2, 0, "l1-equipment-store")
P("l1-spare-pump-2", "infusion-pump", -23.4, 3.2, 0, "l1-equipment-store")
P("l1-spare-warmer-1", "sc-forced-air-warmer", -28.3, 6.2, 0, "l1-equipment-store")
P("l1-spare-warmer-2", "sc-forced-air-warmer", -27.6, 6.2, 0, "l1-equipment-store")
P("l1-iv-pole", "iv-pole", -23.0, 6.2, 0, "l1-equipment-store")
on_e("l1-store-cabinet", "cabinet", 5.2, "l1-equipment-store", L("耗材柜", "Supplies cabinet"))

# soiled utility
on_s("l1-sluice", "sc-sluice", 27.5, "l1-soiled", L("污物处置池", "Sluice"))
on_w("l1-waste", "sc-waste-station", 2.4, "l1-soiled", L("分类污物收集站", "Segregated waste station"))
P("l1-dirty-cart", "sc-case-cart", 28.4, 2.4, 90, "l1-soiled", L("污染器械回收车（密闭）", "Used-instrument cart (closed)"))

# transfer zone, control desk, lobby, staff corridor, lounge
P("l1-transfer-trolley", "stretcher", -4.6, 12.0, 0, "l1-transfer", L("手术转运平车", "Theatre transfer trolley"))
P("l1-transfer-sanitizer", "hand-sanitizer", -8.5, 10.6, 0, "l1-transfer", L("手消毒液", "Hand rub"))
P("l1-red-line-lobby", "sc-zone-line", -6.5, 13.65, 0, "l1-transfer", L("红线", "Red line"))
P("l1-control-desk", "nurse-station-desk", 1.0, 11.1, 180, "l1-control", L("手术协调台", "Theatre coordination desk"))
P("l1-control-chair-1", "office-chair", 0.2, 12.6, 0, "l1-control")
P("l1-control-chair-2", "office-chair", 1.8, 12.6, 0, "l1-control")
on_s("l1-status-board", "sc-status-board", -2.4, "l1-control", L("手术排程与状态大屏", "Theatre schedule & status board"))
P("l1-control-records", "records-terminal", 4.8, 11.0, 0, "l1-control", L("电子病历终端", "EHR terminal"))
on_s("l1-control-clock", "wall-clock", 4.2, "l1-control")
staff("l1-coordinator", "nurse", L("林护士长（手术协调）", "Charge Nurse Lin (theatre coordinator)"), "l1-control", 1.0, 13.3, 180,
      L("急诊剖宫产随时可以进 7 号手术间；先到更衣室换洗手衣。", "OR 7 is held for emergencies and caesareans — change into scrubs in the changing room first."))
staff("l1-anaesthetist", "attending", L("王医生（麻醉科值班主治）", "Dr Wang (duty consultant anaesthetist)"), "l1-control", 3.0, 13.3, 180,
      L("麻醉前核查：气道评估、禁食时间、过敏史和备血情况都要确认。", "Before induction I want the airway assessment, fasting times, allergies and blood availability confirmed."))
P("l1-lobby-chairs", "waiting-chairs", -3.0, 15.0, 0, "l1-lobby")
P("l1-lobby-plant", "potted-plant", -8.3, 15.0, 0, "l1-lobby")
P("l1-lobby-sanitizer", "hand-sanitizer", -1.4, 14.5, 0, "l1-lobby", L("手消毒液", "Hand rub"))
staff("l1-porter", "porter", L("赵师傅（转运）", "Porter Zhao"), "l1-lobby", -5.4, 16.2, 180,
      L("病房床推到换床间，在红线处换手术平车。", "Ward beds stop at the transfer zone — we swap to the theatre trolley at the red line."))
P("l1-staff-plant", "potted-plant", 19.4, 21.4, 0, "l1-staff-corridor")
on_w("l1-lounge-sofa-1", "waiting-chairs", 15.0, "l1-lounge")
on_w("l1-lounge-sofa-2", "waiting-chairs", 17.2, "l1-lounge")
P("l1-lounge-table", "desk", 22.6, 16.1, 0, "l1-lounge")
P("l1-lounge-chair-1", "chair", 22.6, 15.3, 0, "l1-lounge")
P("l1-lounge-chair-2", "chair", 22.6, 16.9, 180, "l1-lounge")
on_e("l1-lounge-vending", "vending-machine", 13.0, "l1-lounge")
P("l1-lounge-water", "water-dispenser", 25.6, 14.2, 0, "l1-lounge")
on_e("l1-lounge-board", "whiteboard", 18.0, "l1-lounge", L("交班白板", "Handover whiteboard"))
P("l1-lounge-plant", "potted-plant", 25.4, 21.4, 0, "l1-lounge")

# --- template instances (rooms that share walls are listed before the ORs so they own those walls) ---
SCRUB_SOLID_E = {"partitions": [
    {"side": "n", **OR_WALL}, {"side": "w", **OR_WALL, "openings": [door("sliding-door", 1.4, 0.6, 2.6)]},
    {"side": "e", **OR_WALL}, {"side": "s", **OR_WALL, "openings": [door("opening", 2.2, 0, 3)]},
]}
PREP_SOLID_E = {"partitions": [
    {"side": "n", **OR_WALL, "openings": [door("sliding-door", 1.4, 0, 2.6)]}, {"side": "w", **OR_WALL, "openings": [door("sliding-door", 1.4, 0.8, 2.6)]},
    {"side": "e", **OR_WALL}, {"side": "s", **OR_WALL},
]}


def scrub_name(n):
    return {"name": L(f"刷手间 {n}", f"Scrub bay {n}")}


inst("scrub-1", "sc-scrub-bay", -27.5, -17, 180, overrides={**scrub_name("1"), **SCRUB_SOLID_E})
inst("prep-1", "sc-prep-room", -27.5, -12.5, 180, overrides={"name": L("无菌准备间 1", "Set-up room 1"), **PREP_SOLID_E})
inst("scrub-2", "sc-scrub-bay", -0.5, -17, 180, overrides=scrub_name("2–3"))
inst("prep-2", "sc-prep-room", -0.5, -12.5, 180, overrides={"name": L("无菌准备间 2–3", "Set-up room 2–3")})
inst("scrub-3", "sc-scrub-bay", 11.5, -17, 180, overrides=scrub_name("3–4"))
inst("prep-3", "sc-prep-room", 11.5, -12.5, 180, overrides={"name": L("无菌准备间 3–4", "Set-up room 3–4")})
inst("scrub-5", "sc-scrub-bay", -11.5, 5, 0, overrides=scrub_name("5–6"))
inst("prep-5", "sc-prep-room", -11.5, 0.5, 0, overrides={"name": L("无菌准备间 5–6", "Set-up room 5–6")})
inst("scrub-6", "sc-scrub-bay", 0.5, 5, 0, overrides=scrub_name("6–7"))
inst("prep-6", "sc-prep-room", 0.5, 0.5, 0, overrides={"name": L("无菌准备间 6–7", "Set-up room 6–7")})
inst("scrub-7", "sc-scrub-bay", 12.5, 5, 0, overrides={**scrub_name("7"), **SCRUB_SOLID_E})
inst("prep-7", "sc-prep-room", 12.5, 0.5, 0, overrides={"name": L("无菌准备间 7", "Set-up room 7"), **PREP_SOLID_E})
inst("or-8-ante", "sc-or-anteroom", 15.5, 2.5, 0, overrides={"name": L("8 号手术间缓冲间", "OR 8 anteroom")})
inst("hybrid-control", "sc-or-hybrid-control", -13, -14.5, 180, overrides={"name": L("1 号复合手术室控制室", "OR 1 hybrid control room")})
inst("anaes-workroom", "sc-anaesthesia-workroom", 25.5, -16.75, 180)
inst("frozen-lab", "sc-frozen-section-lab", 25.5, -12.25, 90,
     overrides={"staff": {"pathologist": {"name": L("周医生（病理科）", "Dr Zhou (pathology)")}}})


def or_sign(zh, en, color):
    return {"text": L(zh, en), "color": color}


# OR 7 first: the first slot accepting the operating-room setting is where a case starts
inst("or-7", "sc-or-integrated", 6.5, 2.5, 0, overrides={
    "name": L("7 号手术间 · 急诊与产科（24 小时）", "OR 7 · Emergency & obstetric (24/7)"),
    "sign": or_sign("7 号 · 急诊/产科 · Ⅱ级", "OR 7 · Emergency & obstetric · Class II", "#c9473c"),
})
inst("or-1", "sc-or-hybrid", -20.5, -14.5, 180, overrides={
    "name": L("1 号复合手术室（心血管/神经介入）", "OR 1 · Hybrid (cardiovascular & neuro-interventional)"),
    "sign": or_sign("1 号 · 复合手术室 · Ⅰ级 · 放射防护", "OR 1 · Hybrid · Class I · radiation", "#d98a3d"),
})
inst("or-2", "sc-or-robotic", -6.5, -14.5, 180, overrides={
    "name": L("2 号手术间 · 机器人手术", "OR 2 · Robotic surgery"),
    "sign": or_sign("2 号 · 机器人手术 · Ⅱ级", "OR 2 · Robotic · Class II", "#2f7fd1"),
})
inst("or-3", "sc-or-ultraclean", 5.5, -14.5, 180, overrides={
    "name": L("3 号手术间 · 心脏与移植（超净）", "OR 3 · Cardiac & transplant (ultra-clean)"),
    "sign": or_sign("3 号 · 心脏/移植 · Ⅰ级超净", "OR 3 · Cardiac & transplant · Class I", "#2f7fd1"),
})
inst("or-4", "sc-or-ultraclean", 17.5, -14.5, 180, overrides={
    "name": L("4 号手术间 · 骨科关节与神经外科（超净）", "OR 4 · Orthopaedic & neurosurgery (ultra-clean)"),
    "sign": or_sign("4 号 · 关节/神经 · Ⅰ级超净", "OR 4 · Arthroplasty & neuro · Class I", "#2f7fd1"),
})
inst("or-5", "sc-or-integrated", -17.5, 2.5, 0, overrides={
    "name": L("5 号手术间 · 普外与结直肠腔镜", "OR 5 · General & colorectal MIS"),
    "sign": or_sign("5 号 · 普外腔镜 · Ⅱ级", "OR 5 · General & colorectal MIS · Class II", SIGN_OR),
})
inst("or-6", "sc-or-integrated", -5.5, 2.5, 0, overrides={
    "name": L("6 号手术间 · 泌尿/妇科/头颈腔镜", "OR 6 · Urology, gynaecology & head-and-neck MIS"),
    "sign": or_sign("6 号 · 腔镜 · Ⅱ级", "OR 6 · MIS · Class II", SIGN_OR),
})
inst("or-8", "sc-or-isolation", 21.5, 2.5, 0, overrides={
    "name": L("8 号手术间 · 负压隔离", "OR 8 · Negative-pressure isolation"),
})
inst("preop", "sc-preop-holding", -13.5, 16, 180)
inst("pacu", "sc-pacu-8", -25, 16, 180)
inst("changing-f", "sc-staff-changing", 9.5, 14.5, 0, overrides={
    "name": L("女医护更衣室", "Staff changing · women"),
    "sign": {"text": L("女更衣 · 外区 → 内区", "Women · outer → inner"), "color": "#7fb0a6"},
})
inst("changing-m", "sc-staff-changing", 16.5, 14.5, 0, overrides={
    "name": L("男医护更衣室", "Staff changing · men"),
    "sign": {"text": L("男更衣 · 外区 → 内区", "Men · outer → inner"), "color": "#7fb0a6"},
})
inst("bed-lift-1-l1", "sc-bed-lift-car", 4.5, 15.3, 270, overrides={"name": L("1 号病床电梯", "Bed lift 1")})
inst("bed-lift-2-l1", "sc-bed-lift-car", 4.5, 17.9, 270, overrides={"name": L("2 号病床电梯", "Bed lift 2")})
inst("clean-lift-l1", "elevator-cabin", -6, -6, 90, overrides={"name": L("洁净物品电梯", "Clean lift")})

# specialty equipment added to template rooms
# (template-local positions; rot 0 rooms add the centre, rot 180 rooms subtract it: world = centre − local)
P("or-7-infant-warmer", "sc-infant-warmer", 6.5 - 3.6, 2.5 + 0.45, 90, "or-7", L("新生儿复苏辐射台", "Neonatal resuscitation warmer"))
P("or-7-cell-salvage", "sc-cell-salvage", 6.5 - 0.1, 2.5 + 3.0, 180, "or-7", L("术中自体血回收", "Cell salvage"))
P("or-3-hlm", "sc-heart-lung-machine", 5.5 - 2.4, -14.5 - 3.0, 180, "or-3", L("体外循环机", "Heart-lung machine"))
P("or-3-cell-salvage", "sc-cell-salvage", 5.5 + 3.6, -14.5 + 2.6, 180, "or-3", L("术中自体血回收", "Cell salvage"))
P("or-4-navigation", "sc-surgical-navigation", 17.5 - 2.6, -14.5 - 2.6, 180, "or-4", L("光学手术导航", "Optical navigation"))
P("or-4-microscope", "sc-surgical-microscope", 17.5 + 3.6, -14.5 + 2.6, 180, "or-4", L("手术显微镜", "Operating microscope"))

# zones (template zones add each OR, set-up room and the anteroom)
access("l1-semi-restricted", L("手术部半限制区", "Operating department · semi-restricted"), L1, -32, 32, -22, 10, SEMI)
access("l1-semi-perioperative", L("术前/复苏区（半限制区）", "Pre-op & recovery (semi-restricted)"), L1, -32, -9, 10, 22, SEMI)
access("l1-semi-control", L("换床间与控制台（半限制区）", "Transfer zone & control desk (semi-restricted)"), L1, -9, 6, 10, 14, SEMI)
access("l1-semi-lounge", L("医护休息室（半限制区）", "Staff lounge (semi-restricted)"), L1, 20, 26, 10, 22, SEMI)
access("l1-sterile-core", L("无菌核心区（限制区）", "Sterile core (restricted)"), L1, -29, 29, -10, -2, CORE_ROLES)

# ======================================================================================== L0 · ground floor
L0 = "L0"
room("l0-corridor", L("一层主走廊", "Ground-floor main corridor"), "corridor", L0, -32, 32, 4, 8, "lino", step=8)
room("l0-service-corridor", L("一层后勤走廊", "Ground-floor service corridor"), "corridor", L0, -12, -8, -22, 4, "lino", step=7)
room("l0-hall", L("入口大厅与手术患者入院处", "Main hall & surgical admissions"), "reception", L0, -9, 16, 8, 22, "stone",
     [part("n", [door("opening", 14, 0, 3.2)]), part("w", [door("door", 1.6, 4, 2.6)]), part("e", [door("door", 1.6, 4, 2.6)])],
     {"text": L("外科手术中心 · 入院登记", "Surgical Centre · admissions"), "side": "n", "color": "#2f7fd1"}, step=6)
room("l0-family", L("家属等候区", "Family waiting lounge"), "waiting", L0, -21, -9, 16, 22, "wood",
     [part("n"), part("w")], {"text": L("家属等候", "Family waiting")})
room("l0-day-surgery", L("日间手术入院与出院区", "Day-surgery admission & discharge"), "ward", L0, -32, -21, 8, 22, "sc-pacu-floor",
     [part("n", [door("double-door", 2.0, 0, 2.8)]), part("e")], {"text": L("日间手术", "Day surgery"), "color": "#6d9fba"})
room("l0-blood-bank", L("输血科（血库）", "Blood bank & transfusion"), "laboratory", L0, 16, 26, 16, 22, "lino",
     [part("n"), part("e")], {"text": L("输血科", "Blood bank"), "color": "#a3313a"})
room("l0-escape-stair", L("疏散楼梯", "Escape stair"), "stairwell", L0, 26, 32, 8, 22, "stone",
     [part("n", [door("door", 1.6, 0, 2.6)]), part("w")], {"text": L("疏散楼梯", "Escape stair"), "color": "#3f8f5a"})
room("l0-sterile-store", L("消毒供应中心 · 无菌物品存放区", "CSSD · sterile store & dispatch"), "storage", L0, -8, 6, -14, 4, "sc-cssd-floor",
     [part("w"), part("n"), part("s", [door("double-door", 2.0, 0, 2.8)]),
      part("e", [door("opening", 1.6, -4, 2.4), door("opening", 1.6, -1, 2.4), door("door", 1.4, 5, 2.6)])],
     {"text": L("无菌物品存放区", "Sterile store"), "side": "s", "color": "#2f7fd1"}, step=6)
room("l0-iah", L("消毒供应中心 · 检查包装及灭菌区", "CSSD · inspection, packing & sterilisation"), "storage", L0, 6, 22, -14, 4, "sc-cssd-floor",
     [part("n"), part("s", [door("door", 1.4, 4, 2.6)]),
      part("e", [door("opening", 1.2, -5, 2.2), door("opening", 1.2, -3, 2.2), door("opening", 1.2, -1, 2.2)])],
     {"text": L("检查包装及灭菌区", "Packing & sterilisation"), "side": "s", "color": "#3f8f5a"}, step=6)
room("l0-decon", L("消毒供应中心 · 去污区", "CSSD · decontamination"), "storage", L0, 22, 32, -14, 4, "sc-cssd-floor",
     [part("n"), part("s", [door("door", 1.6, 0, 2.6)])],
     {"text": L("去污区", "Decontamination"), "side": "s", "color": "#d65f3a"}, step=6)
room("l0-dirty-lift", L("污物电梯", "Dirty lift"), "elevator", L0, 26, 29, -2, 0.6, "steel",
     [part("n", (), STEEL), part("w", (), STEEL), part("e", (), STEEL), part("s", [door("sliding-door", 1.4, 0, 2.4)], STEEL)],
     lights=[{"x": 27.5, "z": -0.7}])
room("l0-stores", L("手术部物资库与洁净布类", "Theatre stores & clean linen"), "storage", L0, -8, 32, -22, -14, "lino",
     [part("w", [door("double-door", 2.0, 0, 2.8)])], {"text": L("物资库", "Stores")}, step=8)
room("l0-debrief", L("模拟控制与复盘室", "Simulation control & debrief"), "teaching", L0, -32, -21, -13, -4, "wood",
     [part("e", [window(3.0, 0.5, 0.9, 1.4), door("sliding-door", 1.6, -2.6, 2.6)]), part("s", [door("door", 1.4, -4.5, 2.6)]), part("n")],
     {"text": L("模拟复盘", "Sim debrief"), "color": "#a397bc"})
room("l0-plant", L("手术部空调机房", "OR air-handling plant room"), "storage", L0, -32, -12, -22, -13, "stone",
     [part("e", [door("double-door", 2.0, 0, 2.8)]), part("s")], {"text": L("空调机房 · 闲人免进", "Plant room · authorised only"), "color": "#e8c547"}, step=7)

# hall
P("l0-reception", "reception-desk", 8.0, 17.0, 90, "l0-hall", L("手术入院登记台", "Surgical admissions desk"))
P("l0-reception-chair", "office-chair", 7.0, 17.0, 0, "l0-hall")
P("l0-reception-records", "records-terminal", 7.0, 18.8, 0, "l0-hall", L("入院登记终端", "Admissions terminal"))
for k, (x, z) in enumerate(((-6.5, 10.0), (-6.5, 12.0), (-3.5, 10.0), (-3.5, 12.0)), start=1):
    P(f"l0-hall-chairs-{k}", "waiting-chairs", x, z, 0, "l0-hall")
on_w("l0-family-board", "sc-status-board", 12.0, "l0-hall", L("手术进程公告屏（匿名编号）", "Surgery progress board (anonymised)"))
on_e("l0-vending", "vending-machine", 11.5, "l0-hall")
P("l0-water", "water-dispenser", 15.6, 12.8, 0, "l0-hall")
P("l0-plant-1", "potted-plant", 8.6, 21.4, 0, "l0-hall")
P("l0-plant-2", "potted-plant", 13.4, 21.4, 0, "l0-hall")
P("l0-hall-sanitizer", "hand-sanitizer", 14.4, 21.4, 0, "l0-hall", L("手消毒液", "Hand rub"))
staff("l0-receptionist", "receptionist", L("许女士（入院登记）", "Ms Xu (admissions)"), "l0-hall", 7.0, 16.0, 90,
      L("手术患者请在这里登记；家属可在西侧等候区看手术进程屏。", "Surgical patients check in here; families can follow progress on the board in the west lounge."))
# family lounge
for k, (x, z, r) in enumerate(((-18.5, 17.5, 0), (-15.5, 17.5, 0), (-18.5, 21.2, 180), (-15.5, 21.2, 180)), start=1):
    P(f"l0-family-chairs-{k}", "waiting-chairs", x, z, r, "l0-family")
P("l0-family-water", "water-dispenser", -20.4, 16.6, 0, "l0-family")
P("l0-family-plant", "potted-plant", -10.0, 21.2, 0, "l0-family")
on_n("l0-family-status", "sc-status-board", -12.5, "l0-family", L("手术进程公告屏", "Surgery progress board"))
# day surgery
for k, x in enumerate((-30.0, -27.5, -25.0, -22.5), start=1):
    P(f"l0-ds-trolley-{k}", "stretcher", x, 20.475, 180, "l0-day-surgery", L(f"日间手术床 {k}", f"Day-surgery trolley {k}"))
    on_s(f"l0-ds-oxygen-{k}", "oxygen-outlet", x, "l0-day-surgery")
    P(f"l0-ds-chair-{k}", "chair", x, 18.6, 180, "l0-day-surgery")
for k, x in enumerate((-28.75, -26.25, -23.75), start=1):
    P(f"l0-ds-curtain-{k}", "privacy-curtain", x, 20.5, 90, "l0-day-surgery")
P("l0-ds-desk", "desk", -26.5, 11.5, 0, "l0-day-surgery", L("日间手术护士台", "Day-surgery nurses' desk"))
P("l0-ds-desk-chair", "office-chair", -26.5, 12.4, 180, "l0-day-surgery")
P("l0-ds-records", "records-terminal", -24.8, 11.5, 0, "l0-day-surgery", L("电子病历终端", "EHR terminal"))
for k, z in enumerate((12.0, 13.0, 14.0), start=1):
    on_w(f"l0-ds-locker-{k}", "locker", z, "l0-day-surgery", L("患者物品柜", "Patient property locker"))
on_e("l0-ds-waiting", "waiting-chairs", 14.0, "l0-day-surgery")
on_n("l0-ds-sink", "sink", -30.5, "l0-day-surgery")
staff("l0-ds-nurse", "nurse", L("高护士（日间手术）", "Nurse Gao (day surgery)"), "l0-day-surgery", -25.4, 12.9, 0,
      L("日间手术患者术前禁食核对后，由我送到二层换床间。", "Day-surgery patients are checked for fasting here, then I take them up to the transfer zone."))
# blood bank
for k, x in enumerate((19.0, 20.0, 21.0), start=1):
    on_s(f"l0-bb-fridge-{k}", "blood-bank-fridge", x, "l0-blood-bank", L("储血冰箱", "Blood refrigerator"))
on_s("l0-bb-freezer", "lab-fridge", 22.0, "l0-blood-bank", L("血浆冰柜", "Plasma freezer"))
on_s("l0-bb-centrifuge", "centrifuge", 23.2, "l0-blood-bank")
on_n("l0-bb-bench", "lab-bench", 22.0, "l0-blood-bank", L("交叉配血工作台", "Cross-match bench"))
P("l0-bb-records", "records-terminal", 17.0, 16.9, 0, "l0-blood-bank", L("输血管理终端", "Transfusion records terminal"))
on_e("l0-bb-desk", "desk", 18.5, "l0-blood-bank")
P("l0-bb-chair", "office-chair", 24.6, 18.5, 0, "l0-blood-bank")
staff("l0-bb-scientist", "lab-tech", L("钱技师（输血科）", "Qian, transfusion scientist"), "l0-blood-bank", 20.0, 19.0, 180,
      L("大出血预案启动后，第一批红细胞和血浆十分钟内送到手术部。", "When the major-haemorrhage protocol is called, the first red cells and plasma reach theatres within ten minutes."))
# CSSD
for k, z in enumerate((-11.3, -10.7, -6.3, -5.7, -1.3, -0.7)):
    for j, x in enumerate((-2.25, -0.75, 0.75, 2.25), start=1):
        P(f"l0-store-rack-{k + 1}{j}", "sc-sterile-rack", x, z, 180 if k % 2 == 0 else 0, "l0-sterile-store", L("无菌物品存放架", "Sterile store rack"))
P("l0-dispatch-cart-1", "sc-case-cart", -5.0, 2.8, 0, "l0-sterile-store", L("发放车", "Dispatch cart"))
P("l0-dispatch-cart-2", "sc-case-cart", -3.8, 2.8, 0, "l0-sterile-store", L("发放车", "Dispatch cart"))
P("l0-store-records", "records-terminal", 4.6, 2.6, 0, "l0-sterile-store", L("追溯系统终端", "Traceability terminal"))
P("l0-steriliser-1", "sc-steam-steriliser", 6.0, -9.0, 90, "l0-iah", L("1 号双门压力蒸汽灭菌器", "Pass-through steriliser 1"))
P("l0-steriliser-2", "sc-steam-steriliser", 6.0, -6.0, 90, "l0-iah", L("2 号双门压力蒸汽灭菌器", "Pass-through steriliser 2"))
for k, (x, z) in enumerate(((10.0, -2.0), (13.0, -2.0), (16.0, -2.0), (10.0, 1.0), (13.0, 1.0), (16.0, 1.0)), start=1):
    P(f"l0-pack-bench-{k}", "sc-inspection-bench", x, z, 0, "l0-iah", L("检查包装台", "Inspection & packing bench"))
on_n("l0-lowtemp-steriliser", "sc-iuss-steriliser", 8.0, "l0-iah", L("低温等离子灭菌器（过氧化氢）", "Low-temperature H₂O₂ plasma steriliser"))
on_n("l0-pack-rack-1", "sc-sterile-rack", 11.0, "l0-iah", L("待灭菌器械包", "Packs awaiting sterilisation"))
on_n("l0-pack-rack-2", "sc-sterile-rack", 13.0, "l0-iah", L("待灭菌器械包", "Packs awaiting sterilisation"))
on_n("l0-iah-sink", "sink", 16.0, "l0-iah")
P("l0-load-cart", "sc-case-cart", 8.0, -9.0, 0, "l0-iah", L("灭菌装载车", "Steriliser loading cart"))
P("l0-iah-records", "records-terminal", 19.0, -12.5, 0, "l0-iah", L("追溯条码终端", "Barcode traceability terminal"))
for k, z in enumerate((-10.0, -8.0, -6.0), start=1):
    P(f"l0-washer-{k}", "sc-washer-disinfector", 22.0, z, 90, "l0-decon", L(f"{k} 号清洗消毒器", f"Washer-disinfector {k}"))
on_n("l0-decon-sink-1", "sc-decon-sink", 25.0, "l0-decon", L("手工清洗槽", "Manual cleaning sink"))
on_n("l0-decon-sink-2", "sc-decon-sink", 28.0, "l0-decon", L("超声清洗槽", "Ultrasonic cleaning sink"))
on_e("l0-decon-waste", "sc-waste-station", -9.0, "l0-decon")
on_e("l0-decon-ppe", "sc-ppe-station", -6.0, "l0-decon", L("去污区防护用品（防水围裙、面屏）", "Decontamination PPE (apron, visor)"))
on_e("l0-decon-handwash", "sink", -4.0, "l0-decon", L("洗手池", "Hand-wash sink"))
P("l0-dirty-cart-1", "sc-case-cart", 24.5, -3.0, 0, "l0-decon", L("回收的污染器械车", "Returned dirty cart"))
P("l0-dirty-cart-2", "sc-case-cart", 24.5, -1.5, 0, "l0-decon", L("回收的污染器械车", "Returned dirty cart"))
# stores
for k, x in enumerate((-4.5, -2.5, -0.5, 8.0, 10.0, 12.0, 22.0, 24.0, 26.0), start=1):
    on_n(f"l0-stores-shelf-n{k}", "pharmacy-shelves", x, "l0-stores", L("耗材货架", "Supplies shelving"))
for k, x in enumerate((3.0, 5.0, 15.0, 17.0, 27.0, 29.0), start=1):
    P(f"l0-stores-island-{k}a", "pharmacy-shelves", x, -17.75, 0, "l0-stores", L("耗材货架", "Supplies shelving"))
    P(f"l0-stores-island-{k}b", "pharmacy-shelves", x, -18.25, 180, "l0-stores", L("耗材货架", "Supplies shelving"))
for k, x in enumerate((0.0, 1.0, 2.0), start=1):
    on_s(f"l0-linen-{k}", "cabinet", x, "l0-stores", L("洁净布类柜", "Clean linen cabinet"))
# plant room
for k, x in enumerate((-28.5, -22.0, -15.5), start=1):
    on_n(f"l0-ahu-{k}", "sc-ahu", x, "l0-plant", L(f"{k} 号手术部空调机组", f"OR air-handling unit {k}"))
P("l0-bms", "records-terminal", -14.0, -14.0, 0, "l0-plant", L("楼宇自控（BMS）终端", "Building management (BMS) terminal"))
on_s("l0-plant-alarm", "sc-gas-zone-valve", -25.0, "l0-plant", L("医用气体与空调报警面板", "Medical-gas & HVAC alarm panel"))
# debrief
P("l0-sim-station", "workstation", -22.6, -8.5, 90, "l0-debrief", L("模拟控制工作站", "Simulation control station"), capabilities=["records"])
P("l0-sim-chair-1", "office-chair", -24.2, -9.2, 90, "l0-debrief")
P("l0-sim-chair-2", "office-chair", -24.2, -7.8, 90, "l0-debrief")
on_w("l0-debrief-board", "evidence-board", -8.5, "l0-debrief", L("复盘病例讨论板", "Debrief case board"))
P("l0-debrief-desk-1", "desk", -28.0, -11.2, 0, "l0-debrief")
P("l0-debrief-desk-2", "desk", -25.5, -11.2, 0, "l0-debrief")
P("l0-debrief-chair-1", "chair", -28.0, -10.4, 180, "l0-debrief")
P("l0-debrief-chair-2", "chair", -25.5, -10.4, 180, "l0-debrief")
on_n("l0-debrief-whiteboard", "whiteboard", -26.5, "l0-debrief")

inst("l0-skills", "teaching-room", -27, 0, 0, L0, {
    "name": L("外科技能与模拟实训室", "Surgical skills & simulation lab"),
    "sign": {"text": L("技能实训", "Skills lab"), "color": "#a397bc"},
    "staff": {"attending": {"name": L("陈主任（外科教学）", "Dr Chen (surgical educator)"),
                            "greeting": L("先在模拟手术室把核查流程练熟，再上二层手术部。", "Rehearse the checklist in the simulation OR before you go up to theatres.")}},
})
inst("l0-observation", "teaching-room", -17, 0, 0, L0, {
    "name": L("手术直播观摩与会议室", "OR live-video observation & conference room"),
    "sign": {"text": L("手术直播观摩", "OR live video"), "color": "#a397bc"},
    "omit": ["atlas", "attending"],
})
inst("l0-sim-or", "sc-or-integrated", -16.5, -8.5, 90, L0, {
    "name": L("高仿真模拟手术室", "High-fidelity simulation OR"),
    "sign": {"text": L("模拟手术室", "Simulation OR"), "color": "#a397bc"},
    "omit": ["slot", "sterile"],
})
inst("l0-consult-1", "outpatient-consult", -18, 12, 180, L0, {"name": L("麻醉术前评估门诊 1", "Pre-anaesthesia assessment clinic 1"), "omit": ["slot"]})
inst("l0-consult-2", "outpatient-consult", -12, 12, 180, L0, {"name": L("麻醉术前评估门诊 2", "Pre-anaesthesia assessment clinic 2"), "omit": ["slot"]})
inst("l0-lab", "clinical-lab", 21, 12, 180, L0, {
    "name": L("围术期检验室（急诊检验）", "Perioperative laboratory (stat lab)"),
    "staff": {"lab-tech": {"name": L("郑技师（检验科）", "Zheng, lab technician")}},
})
inst("bed-lift-1-l0", "sc-bed-lift-car", 4.5, 15.3, 270, L0, {"name": L("1 号病床电梯", "Bed lift 1")})
inst("bed-lift-2-l0", "sc-bed-lift-car", 4.5, 17.9, 270, L0, {"name": L("2 号病床电梯", "Bed lift 2")})
inst("clean-lift-l0", "elevator-cabin", -6, -6, 90, L0, {"name": L("洁净物品电梯", "Clean lift")})

access("l0-cssd", L("消毒供应中心（工作人员）", "CSSD (staff only)"), L0, -8, 32, -14, 4, ["nurse", "porter", "clinician", "attending"])
access("l0-plant", L("空调机房（授权人员）", "Plant room (authorised staff)"), L0, -32, -12, -22, -13, ["porter", "clinician", "attending"])

CONNECTORS = [
    {"id": "bed-lift-1", "kind": "elevator", "name": L("1 号病床电梯", "Bed lift 1"), "travelSeconds": 20,
     "stops": [{"level": "L0", "x": 4.5, "z": 15.3}, {"level": "L1", "x": 4.5, "z": 15.3}]},
    {"id": "bed-lift-2", "kind": "elevator", "name": L("2 号病床电梯", "Bed lift 2"), "travelSeconds": 20,
     "stops": [{"level": "L0", "x": 4.5, "z": 17.9}, {"level": "L1", "x": 4.5, "z": 17.9}]},
    {"id": "clean-lift", "kind": "elevator", "name": L("洁净物品电梯（供应中心 → 无菌核心区）", "Clean lift (CSSD → sterile core)"), "travelSeconds": 20,
     "stops": [{"level": "L0", "x": -6, "z": -6}, {"level": "L1", "x": -6, "z": -6}], "roles": ["nurse"]},
    {"id": "dirty-lift", "kind": "elevator", "name": L("污物电梯（污物间 → 去污区）", "Dirty lift (soiled utility → decontamination)"), "travelSeconds": 20,
     "stops": [{"level": "L0", "x": 27.5, "z": -0.7}, {"level": "L1", "x": 27.5, "z": -0.7}], "roles": ["nurse", "porter"]},
    {"id": "main-stairs", "kind": "stairs", "name": L("主楼梯", "Main stairs"), "width": 2,
     "stops": [{"level": "L0", "x": -1, "z": 20.6}, {"level": "L1", "x": -7, "z": 20.6}]},
    {"id": "escape-stairs", "kind": "stairs", "name": L("疏散楼梯", "Escape stairs"), "width": 2,
     "stops": [{"level": "L0", "x": 29, "z": 20.3}, {"level": "L1", "x": 29, "z": 13.3}]},
]


def win(side, offset, levels, width=2.0):
    return {"side": side, "offset": num(offset), "width": num(width), "height": 1.6, "kind": "window", "sill": 1.0, "levels": levels}


OPENINGS = [{"side": "s", "offset": 11, "width": 3.2, "height": 3.2, "kind": "double-door", "levels": ["L0"]}]
OPENINGS += [win("n", x, ["L1"]) for x in (-28, -20, -12, -4, 4, 12, 20, 28)]
OPENINGS += [win("s", x, ["L1"]) for x in (-29, -25, -21, -15, -12, -4, 1, 9, 17, 23)]
OPENINGS += [win("w", z, ["L1"]) for z in (-15, -8, 0, 7, 13, 19)]
OPENINGS += [win("e", z, ["L1"]) for z in (-15, -8, 0, 7, 16)]
OPENINGS += [win("s", x, ["L0"]) for x in (-30, -27, -24, -18, -12, -6, 2, 19, 23, 29)]
OPENINGS += [win("w", z, ["L0"]) for z in (-18, -8.5, 0, 12, 18)]
OPENINGS += [win("n", x, ["L0"]) for x in (-28, -22, -16, -4, 4, 12, 20, 28)]
OPENINGS += [win("e", z, ["L0"]) for z in (-10, -4, 2, 14)]


def build():
    for issue in ISSUES:
        print("ISSUE", issue)
    for lv in ("L0", "L1"):
        ps = [p for p in PLACEMENTS if _room_level[p["room"]] == lv]
        for msg in fp.overlaps(ps, where=f"authored {lv}"):
            print("ISSUE", msg)
    return {
        "schema": "clinicalcraft/facility@1",
        "id": FACILITY_ID,
        "name": L("SurgeryCraft 外科手术中心", "SurgeryCraft Surgical Centre"),
        "description": L(
            "两层外科手术中心。二层手术部按国际手术室规范设计：限制区/半限制区/非限制区三级流线（AORN、FGI），环形洁净走廊包围中央无菌核心区；8 间手术室——复合手术室（机器人血管造影）、机器人手术室、两间Ⅰ级超净层流手术室（心脏/移植、骨科关节/神经）、三间一体化数字手术室（含 24 小时急诊与产科手术间）和带缓冲间的负压隔离手术室；刷手间与无菌准备间成对位于手术室之间；麻醉后恢复室 8 床、术前准备区 5 床、换床间、男女更衣室（单向流线）、手术部控制台、卫星药房、麻醉准备间（卫星血库）、术中冰冻病理室和污物间。洁净电梯直通一层消毒供应中心的无菌物品存放区，污梯直通去污区。一层为入口大厅与入院登记、家属等候、日间手术、麻醉术前评估门诊、围术期检验室、输血科、消毒供应中心（去污 → 检查包装灭菌 → 无菌存放的单向流程）、外科技能与模拟中心和空调机房。",
            "A two-storey surgical centre. The first-floor operating department follows international OR practice: restricted / semi-restricted / unrestricted zoning (AORN, FGI) with a ring of clean corridors round a central sterile core; eight ORs — a hybrid OR with robotic angiography, a robotic surgery OR, two Class I ultra-clean laminar-flow ORs (cardiac & transplant, arthroplasty & neuro), three integrated digital ORs (one held 24/7 for emergency and obstetric surgery) and a negative-pressure isolation OR behind its anteroom; paired scrub bays and sterile set-up rooms between the ORs; an 8-bay PACU, 5-bay pre-op holding, a patient transfer zone, one-way staff changing rooms, the theatre control desk, a theatre pharmacy, the anaesthesia workroom (satellite blood fridge), a frozen-section lab and a soiled utility. A clean lift links the sterile core to the CSSD sterile store below and a dirty lift returns used instruments to decontamination. Ground floor: main hall and admissions, family waiting, day surgery, pre-anaesthesia clinics, the perioperative lab, the blood bank, the CSSD (decontamination → packing & sterilisation → sterile store, one way), a surgical skills & simulation centre and the OR plant room."),
        "bounds": {"minX": -44, "maxX": 44, "minZ": -34, "maxZ": 46},
        "spawn": {"x": 11, "z": 38, "yaw": 0},
        "environment": {"sky": "#a8d5e0", "fog": {"color": "#b9d8d6", "near": 45, "far": 110}, "sunIntensity": 3.4},
        "catalogs": ["materials", "core-furniture", "core-clinical", "core-diagnostics", "surgerycraft-or"],
        "terrain": {
            "ground": "grass",
            "paths": [
                {"x": 11, "z": 27.5, "w": 18, "d": 11, "material": "stone"},
                {"x": 11, "z": 38.5, "w": 4, "d": 11, "material": "path"},
                {"x": -12, "z": 28, "w": 26, "d": 6, "material": "asphalt"},
                {"x": 0, "z": -27, "w": 72, "d": 3, "material": "path"},
            ],
            "trees": [{"x": x, "z": z, "h": h} for x, z, h in (
                (-38, -28, 5), (-26, -29, 6), (-12, -29, 5), (4, -29, 6), (18, -29, 5), (32, -29, 6), (39, -15, 5), (39, 0, 6),
                (39, 15, 5), (-39, -15, 6), (-39, 0, 5), (-39, 15, 6), (-34, 33, 5), (-24, 38, 6), (28, 34, 5), (36, 40, 6), (24, 42, 5), (-2, 42, 6))],
            "flowers": {"count": 60, "seed": 4242, "exclude": [
                {"x": 0, "z": 0, "w": 66, "d": 46}, {"x": 11, "z": 30, "w": 20, "d": 16}, {"x": -12, "z": 28, "w": 28, "d": 8}, {"x": 0, "z": -27, "w": 74, "d": 5}]},
            "horizon": {"count": 40, "radius": 85},
            "clouds": 14,
        },
        "levels": [
            {"id": "L0", "name": L("一层 · 入院、消毒供应与模拟中心", "Ground floor · admissions, CSSD & simulation"), "elevation": 0, "height": 5},
            {"id": "L1", "name": L("二层 · 手术部", "First floor · operating department"), "elevation": 5, "height": 5},
        ],
        "buildings": [{
            "id": "main",
            "name": L("SurgeryCraft 外科手术中心", "SurgeryCraft Surgical Centre"),
            "rect": {"x": 0, "z": 0, "w": 64, "d": 44},
            "levels": ["L0", "L1"],
            "floor": "floor",
            "walls": {"height": 5, "base": "navy", "body": "white", "top": "steel", "thickness": 0.35},
            "openings": OPENINGS,
            "roof": {"material": "tile-white"},
            "sign": {"text": L("外科手术中心", "Surgical Centre"), "side": "s", "color": "#2f7fd1"},
        }],
        "rooms": ROOMS,
        "placements": PLACEMENTS,
        "staff": STAFF,
        "signs": [
            {"text": L("外科手术中心 · 入口", "Surgical Centre · Entrance"), "x": 16.8, "y": 2.6, "z": 31.5, "rot": 0, "width": 3.2, "color": "#2f7fd1", "post": True},
            {"text": L("患者接送区", "Patient drop-off"), "x": -12, "y": 2.4, "z": 32.2, "rot": 0, "width": 2.6, "color": "#3f8f5a", "post": True},
        ],
        "outdoorRegion": L("医院园区", "Hospital grounds"),
        "connectors": CONNECTORS,
        "access": ACCESS,
        "instances": INSTANCES,
    }
