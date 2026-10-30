"""SurgeryCraft room templates (template-local frame: origin at the room centre, door on local south +Z)."""
from common import L, num
import footprints as fp

TEMPLATES = []
ISSUES = []

SEMI = ["clinician", "attending", "nurse", "porter", "radiologist", "pathologist", "lab-tech", "pharmacist"]
OR_ROLES = ["clinician", "attending", "nurse", "porter"]
HYBRID_ROLES = OR_ROLES + ["radiologist"]
CORE_ROLES = ["clinician", "attending", "nurse"]

OR_WALL = {"material": "sc-or-wall", "base": "sc-or-wall-base", "height": 4.6}
CLEAN_WALL = {"material": "white", "base": "sc-or-wall-base"}


def P(id, type, x, z, rot=0, label=None, **kw):
    p = {"id": id, "type": type, "x": num(x), "z": num(z)}
    if rot:
        p["rot"] = rot
    if label:
        p["label"] = label
    p.update(kw)
    return p


def depth(type, rot=0):
    f = fp.TYPES[type]["footprint"]
    return f["d"]


# wall helpers: back of the item against the inner face of a wall (partitions 0.35 thick)
def on_n(id, type, x, D, label=None, **kw):
    return P(id, type, x, -D / 2 + 0.175 + depth(type) / 2, 0, label, **kw)


def on_s(id, type, x, D, label=None, **kw):
    return P(id, type, x, D / 2 - 0.175 - depth(type) / 2, 180, label, **kw)


def on_w(id, type, z, W, label=None, **kw):
    return P(id, type, -W / 2 + 0.175 + depth(type) / 2, z, 90, label, **kw)


def on_e(id, type, z, W, label=None, **kw):
    return P(id, type, W / 2 - 0.175 - depth(type) / 2, z, 270, label, **kw)


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


def grid_lights(W, D, nx, nz):
    return [{"x": num(-W / 2 + (i + 0.5) * W / nx), "z": num(-D / 2 + (j + 0.5) * D / nz)} for j in range(nz) for i in range(nx)]


def template(id, name, description, kind, size, floor, partitions, sign, lights, placements, slots=(), staff=(), zones=(), caps=(), tags=()):
    W, D = size
    ISSUES.extend(fp.overlaps(placements, where=id))
    ISSUES.extend(fp.inside(placements, W, D, where=id))
    ids = [p["id"] for p in placements]
    assert len(ids) == len(set(ids)), (id, "duplicate placement ids")
    provided = set()
    for p in placements:
        provided |= set(fp.TYPES[p["type"]].get("capabilities", []))
    for c in caps:
        if c not in provided:
            ISSUES.append(f"{id}: declares capability {c} that no equipment provides")
    t = {
        "schema": "clinicalcraft/room-template@1",
        "id": id,
        "name": name,
        "description": description,
        "kind": kind,
        "size": {"w": num(W), "d": num(D)},
        "floor": floor,
        "partitions": partitions,
    }
    if sign:
        t["sign"] = sign
    t["lights"] = lights
    t["placements"] = placements
    if slots:
        t["patientSlots"] = list(slots)
    if staff:
        t["staff"] = list(staff)
    if zones:
        t["zones"] = list(zones)
    t["capabilities"] = list(caps)
    t["tags"] = list(tags)
    TEMPLATES.append(t)
    return t


def slot(bed, monitor, x, z, rot=0, accepts=("operating-room",), id="slot"):
    s = {"id": id, "x": num(x), "z": num(z)}
    if rot:
        s["rot"] = rot
    s.update({"posture": "lying", "bed": bed, "accepts": list(accepts)})
    if monitor:
        s["monitor"] = monitor
    return s


def zone(id, name, W, D, roles):
    return {"id": id, "name": name, "rect": {"x": 0, "z": 0, "w": num(W), "d": num(D)}, "roles": roles}


OR_CAPS = ["surgery", "anesthesia", "airway", "ventilator", "capnography", "cardiac-monitor", "oxygen", "suction",
           "infusion-pump", "iv-access", "medications", "records"]

# --------------------------------------------------------------------------------------------- 9 × 9 operating rooms
# Shared skeleton: table along X at (0, −0.3); anaesthesia at the head (−X); corridor door on local south
# (patient entry, west half), core door on local north (sterile supply, east half), scrub door (z +3.1) and
# set-up-room door (z −1.2) on both side walls — rooms placed before an OR in a facility own those walls.

W9 = D9 = 9


# The sterile set-up table's lay-out (table-local offsets, items on the drape at 0.9 m): the container set, counted
# RFID swabs, gloves and gown at the back; the instruments for the first steps along the front edge.
SETUP_ITEMS = [
    ("set", "sc-instrument-set", -0.36, -0.14, L("基础剖腹器械盒", "Major laparotomy set")),
    ("swabs", "sc-gauze-swabs", -0.06, -0.14, L("RFID 纱布", "RFID swabs")),
    ("gloves", "sc-sterile-gloves", 0.13, -0.14, L("无菌手套", "Sterile gloves")),
    ("gown", "sc-sterile-gown", 0.4, -0.14, L("无菌手术衣", "Sterile gown")),
    ("scalpel", "sc-scalpel", -0.48, 0.16, L("手术刀", "Scalpel")),
    ("needle-holder", "sc-needle-holder", -0.3, 0.16, L("持针器", "Needle holder")),
    ("forceps", "sc-tissue-forceps", -0.12, 0.16, L("组织镊", "Tissue forceps")),
    ("scissors", "sc-metzenbaum-scissors", 0.06, 0.16, L("解剖剪", "Dissecting scissors")),
    ("artery-forceps", "sc-artery-forceps", 0.24, 0.16, L("止血钳", "Artery forceps")),
    ("esu-pencil", "sc-esu-pencil", 0.44, 0.16, L("电刀笔", "ESU pencil")),
]
SETUP_TOP = 0.9


def setup_layout(x, z, prefix=""):
    """The handheld items laid out on a sterile set-up table standing at (x, z), rotation 0."""
    return [P(f"{prefix}{id}", type, x + dx, z + dz, label=label, y=SETUP_TOP) for id, type, dx, dz, label in SETUP_ITEMS]


def or_team(scrub, circulating, anaesthetist):
    """The OR team at their posts (named per OR in the facility): scrub nurse at the set-up table, circulating
    nurse, anaesthetist at the head of the table. The learner operates; they pass, count and anaesthetise."""
    return [
        {"id": "scrub-nurse", "role": "nurse", "name": L("洗手护士", "Scrub nurse"), "x": num(scrub[0]), "z": num(scrub[1]), "rot": scrub[2],
         "greeting": L("器械台已按清单摆好，纱布已清点。要什么器械说一声，我递给您。", "The set-up is laid out to the tray list and the swabs are counted. Call for what you need and I'll pass it.")},
        {"id": "circulating-nurse", "role": "nurse", "name": L("巡回护士", "Circulating nurse"), "x": num(circulating[0]), "z": num(circulating[1]), "rot": circulating[2],
         "greeting": L("我负责核查和清点，开台前我们一起做 Sign in 和 Time out。", "I run the checklist and the counts — we'll do the sign-in and the time-out together before you start.")},
        {"id": "anaesthetist", "role": "attending", "name": L("麻醉医生", "Anaesthetist"), "x": num(anaesthetist[0]), "z": num(anaesthetist[1]), "rot": anaesthetist[2],
         "greeting": L("麻醉机已完成开机检查，监测按日本麻醉科学会指南：SpO₂、ETCO₂、心电、无创血压、体温和肌松监测。", "The machine check is done; monitoring follows the JSA guideline — SpO₂, capnography, ECG, NIBP, temperature and neuromuscular monitoring.")},
    ]


OR_TEAM_9 = or_team((2.55, 1.95, 180), (-0.3, 3.4, 180), (-2.4, 0.3, 90))


def or_skeleton(canopy, light="surgical-light", table="operating-table"):
    """The clinical island (table, anaesthesia, pendants, back table) with ≥ 1.3 m clear round it: the world
    model plans on 0.5 m cells with colliders inflated by 0.38 m, so narrower aisles do not exist for walkers."""
    D = D9
    W = W9
    return [
        P("canopy", canopy, 0.5, 0.2, label=L("层流送风天花", "Laminar-flow ceiling")),
        P("table", table, 0.5, 0.2, 90, L("手术床", "Operating table")),
        P("light", light, 0.5, 0.2, label=L("LED 无影灯", "LED surgical light")),
        P("anaesthesia", "sc-anaesthesia-workstation", -1.45, -0.35, 90, L("麻醉工作站", "Anaesthesia workstation")),
        P("monitor", "patient-monitor", -1.45, 0.85, label=L("麻醉监护仪", "Anaesthesia monitor")),
        P("anaes-pendant", "sc-anaesthesia-pendant", -1.45, -1.65, label=L("麻醉吊塔", "Anaesthesia pendant")),
        P("surg-pendant", "sc-surgical-pendant", 2.35, -1.0, label=L("外科吊塔（电刀/气腹机）", "Surgical pendant (ESU / insufflator)")),
        P("back-table", "sc-sterile-setup-table", 2.55, 1.15, label=L("无菌器械台", "Sterile set-up table")),
        *setup_layout(2.55, 1.15),
        P("mayo", "sc-mayo-stand", 1.1, 1.25, label=L("Mayo 托盘", "Mayo stand")),
        P("smoke-evac", "sc-smoke-evacuator", 2.35, -1.62, label=L("烟雾排除器（吊塔旁）", "Smoke evacuator (by the pendant)")),
        P("infusion-pump", "infusion-pump", -0.45, 1.35, label=L("输液泵", "Infusion pump")),
        P("warmer", "sc-forced-air-warmer", 0.35, 1.85, label=L("充气保温机", "Forced-air warmer")),
        on_n("drugs", "medication-cabinet", -3.6, D, L("麻醉药品柜", "Anaesthetic drug cabinet")),
        on_n("iv-cart", "treatment-cart", -2.5, D, L("静脉穿刺与治疗车", "IV cannulation & treatment cart")),
        on_s("records", "records-terminal", 2.0, D, L("手术室电子病历终端", "Theatre EHR terminal")),
        on_e("pacs", "sc-wall-display", 1.2, W, L("PACS / 一体化显示屏", "PACS & integration display")),
        on_s("control-panel", "sc-or-control-panel", 0.6, D, L("环境控制面板", "OR control panel")),
        on_s("checklist", "sc-who-checklist", 3.3, D, L("WHO 手术安全核查板", "WHO Surgical Safety Checklist")),
        on_e("count-board", "sc-count-board", -3.0, W, L("手术清点板", "Surgical count board")),
        P("rf-wand", "sc-rf-wand", W / 2 - 0.3, -3.4, 90, L("RF 纱布检测棒", "RF sponge-detection wand"), y=0.75),
        on_n("grille-1", "sc-return-grille", 3.9, D),
        on_s("grille-2", "sc-return-grille", -3.9, D),
        P("sanitizer", "hand-sanitizer", -0.6, 4.0, label=L("手消毒液", "Hand rub")),
    ]


def or_partitions(s_door=True, n_door=True, side_doors=True, w_door=None):
    side = [door("sliding-door", 1.4, 3.1, 2.6), door("sliding-door", 1.4, -1.2, 2.6)] if side_doors else []
    w_open = list(side)
    if w_door:
        w_open = [w_door]
    return [
        part("n", [door("sliding-door", 1.6, 2.6, 2.6)] if n_door else [], OR_WALL),
        part("w", w_open, OR_WALL),
        part("e", side, OR_WALL),
        part("s", [door("sliding-door", 2.4, -2.2, 3)] if s_door else [], OR_WALL),
    ]


OR_LIGHTS = [{"x": -3, "z": -3}, {"x": 3, "z": -3}, {"x": -3, "z": 3}, {"x": 3, "z": 3}]

# OR · integrated digital OR (GB 50333 Class II, ASHRAE 170 conventional OR)
template(
    "sc-or-integrated",
    L("一体化数字手术室（Ⅱ级洁净）", "Integrated digital OR (Class II)"),
    L("9 × 9 m（81 m²）一体化数字手术室，用于普外、腔镜与急诊手术：层流送风天花与末端高效过滤、双吊塔、4K/3D 腹腔镜塔、两台吊臂 4K 显示器、墙嵌 PACS 屏、环境控制面板（温湿度、压差、层流状态、气体报警）与 WHO 手术安全核查板；四周下回风口，双开感应门。设计目标：GB 50333 Ⅱ级（手术区 ISO 6）、ASHRAE 170（≥ 20 次/h 总换气、≥ 4 次/h 新风、对走廊正压、20–24 °C、20–60 % RH）。",
      "9 × 9 m (81 m²) integrated digital OR for general, minimally invasive and emergency surgery: laminar-flow supply ceiling with terminal HEPA filters, anaesthesia and surgical pendants, a 4K/3D laparoscopy tower, two ceiling-boom 4K displays, a wall PACS screen, the room control panel (temperature, humidity, pressure, laminar-flow status, gas alarms) and the WHO Surgical Safety Checklist; low-level returns and sensor-operated sliding doors. Design targets: GB 50333 Class II (ISO 6 at the operating zone) and ASHRAE 170 (≥ 20 total and ≥ 4 outdoor air changes per hour, positive to the corridor, 20–24 °C, 20–60 % RH)."),
    "operating-room", (W9, D9), "sc-or-floor", or_partitions(),
    {"text": L("手术室 · Ⅱ级洁净", "OR · Class II"), "color": "#3f8f5a"},
    OR_LIGHTS,
    or_skeleton("sc-laminar-canopy") + [
        P("lap-tower", "sc-laparoscopy-tower", 0.5, -1.35, label=L("4K/3D 腹腔镜系统", "4K/3D laparoscopy tower")),
        on_n("ultrasound", "ultrasound-machine", 0.2, D9, L("超声 / 经食道超声", "Ultrasound / TOE")),
        on_n("airway", "sc-difficult-airway-trolley", -1.4, D9, L("困难气道车", "Difficult airway trolley")),
        P("display-1", "sc-ceiling-display", 1.6, 2.6, 180, L("吊臂显示器 1", "Ceiling display 1")),
        P("display-2", "sc-ceiling-display", -0.6, -2.7, label=L("吊臂显示器 2", "Ceiling display 2")),
    ],
    slots=[slot("table", "monitor", 0, -0.3, 90)],
    staff=OR_TEAM_9,
    zones=[zone("sterile", L("手术间（限制区）", "Operating room (restricted)"), W9, D9, OR_ROLES)],
    caps=OR_CAPS + ["ultrasound", "echocardiography"],
    tags=["surgery", "restricted", "integrated-or", "class-ii"],
)

# OR · ultra-clean (UCV / Class I / DIN Ia) for arthroplasty, cardiac, transplant
template(
    "sc-or-ultraclean",
    L("超净层流手术室（Ⅰ级洁净）", "Ultra-clean laminar-flow OR (Class I)"),
    L("9 × 9 m 超净手术室，用于关节置换、心脏与器官移植等植入物手术：3.2 × 3.2 m 单向流送风天花带玻璃导流裙边，手术台和器械台都在保护区内；移动 C 形臂、双器械台、双吊塔与 4K 显示。设计目标：GB 50333 Ⅰ级（手术区 ISO 5、浮游菌 ≤ 5 CFU/m³）、DIN 1946-4 Ⅰa（TAV）与 HTM 03-01 超净通风（≤ 10 CFU/m³）。",
      "9 × 9 m ultra-clean OR for implant surgery (arthroplasty, cardiac, transplant): a 3.2 × 3.2 m unidirectional supply ceiling with glass skirts covering both the table and the instrument tables, a mobile C-arm, two back tables, both pendants and 4K displays. Design targets: GB 50333 Class I (ISO 5 at the operating zone, ≤ 5 CFU/m³), DIN 1946-4 class Ia (TAV) and HTM 03-01 ultra-clean ventilation (≤ 10 CFU/m³)."),
    "operating-room", (W9, D9), "sc-or-floor", or_partitions(),
    {"text": L("手术室 · Ⅰ级超净", "OR · Class I ultra-clean"), "color": "#2f7fd1"},
    OR_LIGHTS,
    or_skeleton("sc-laminar-canopy-xl") + [
        P("c-arm", "c-arm", -3.95, 1.0, 0, L("移动 C 形臂", "Mobile C-arm")),
        P("back-table-2", "instrument-table", 0.5, -1.35, label=L("器械台 2（层流保护区内）", "Back table 2 (inside the clean zone)")),
        on_n("airway", "sc-difficult-airway-trolley", -1.4, D9, L("困难气道车", "Difficult airway trolley")),
        P("display-1", "sc-ceiling-display", 1.6, 2.6, 180, L("吊臂显示器 1", "Ceiling display 1")),
        P("display-2", "sc-ceiling-display", -0.6, -2.7, label=L("吊臂显示器 2", "Ceiling display 2")),
    ],
    slots=[slot("table", "monitor", 0, -0.3, 90)],
    staff=OR_TEAM_9,
    zones=[zone("sterile", L("手术间（限制区）", "Operating room (restricted)"), W9, D9, OR_ROLES)],
    caps=OR_CAPS + ["fluoroscopy"],
    tags=["surgery", "restricted", "ultraclean", "class-i"],
)

# OR · robotic surgery
template(
    "sc-or-robotic",
    L("机器人手术室", "Robotic surgery OR"),
    L("9 × 9 m 机器人辅助手术室：床旁机械臂系统停靠在手术床旁，医生控制台位于房间一角并可看到术野与团队，视频系统车供台上助手观看；其余配置同一体化手术室（层流天花、双吊塔、4K 显示、WHO 核查）。",
      "9 × 9 m robotic-assisted surgery OR: the patient-side cart docks beside the table, the surgeon console sits in a corner with a view of the field and the team, and the vision cart serves the bedside assistant; otherwise as the integrated OR (laminar ceiling, two pendants, 4K displays, WHO checklist)."),
    "operating-room", (W9, D9), "sc-or-floor", or_partitions(),
    {"text": L("手术室 · 机器人", "OR · Robotic"), "color": "#2f7fd1"},
    OR_LIGHTS,
    or_skeleton("sc-laminar-canopy") + [
        P("robot", "sc-robotic-patient-cart", 0.5, -1.75, label=L("床旁机械臂系统", "Robotic patient-side cart")),
        P("console", "sc-robotic-console", 0.9, 3.3, label=L("医生控制台", "Surgeon console")),
        P("vision", "sc-robotic-vision-cart", -3.6, 0.35, 90, L("视频系统车", "Vision cart")),
        P("display-1", "sc-ceiling-display", 1.6, 2.6, 180, L("吊臂显示器", "Ceiling display")),
        P("display-2", "sc-ceiling-display", -0.6, -2.9, label=L("吊臂显示器 2", "Ceiling display 2")),
    ],
    slots=[slot("table", "monitor", 0, -0.3, 90)],
    staff=OR_TEAM_9,
    zones=[zone("sterile", L("手术间（限制区）", "Operating room (restricted)"), W9, D9, OR_ROLES)],
    caps=OR_CAPS,
    tags=["surgery", "restricted", "robotic", "mis"],
)

# OR · negative-pressure isolation (entered only through its anteroom)
template(
    "sc-or-isolation",
    L("负压隔离手术室", "Negative-pressure isolation OR"),
    L("9 × 9 m 正负压可切换的隔离手术室，用于经空气/飞沫传播感染患者：只经缓冲间（local 西侧）进出，不与无菌核心区和走廊直接相通；房间压差监测仪在门旁显示负压，排风经高效过滤后排放。其余配置同一体化手术室。",
      "9 × 9 m switchable-pressure isolation OR for patients with airborne or droplet-transmitted infection: entered only through its anteroom (local west), with no direct door to the sterile core or the corridor; a room pressure monitor by the door shows the negative differential and the exhaust is HEPA-filtered. Otherwise equipped as the integrated OR."),
    "operating-room", (W9, D9), "sc-or-floor",
    or_partitions(s_door=False, n_door=False, side_doors=False, w_door=door("sliding-door", 2.0, 1.0, 2.6)),
    {"text": L("负压隔离手术室", "Negative-pressure isolation OR"), "color": "#c9473c"},
    OR_LIGHTS,
    [p for p in or_skeleton("sc-laminar-canopy") if p["id"] not in ("sanitizer",)] + [
        P("lap-tower", "sc-laparoscopy-tower", 0.5, -1.35, label=L("4K/3D 腹腔镜系统", "4K/3D laparoscopy tower")),
        on_n("ultrasound", "ultrasound-machine", 0.2, D9, L("超声", "Ultrasound")),
        on_n("airway", "sc-difficult-airway-trolley", -1.4, D9, L("困难气道车", "Difficult airway trolley")),
        P("display-1", "sc-ceiling-display", 1.6, 2.6, 180, L("吊臂显示器 1", "Ceiling display 1")),
        P("display-2", "sc-ceiling-display", -0.6, -2.7, label=L("吊臂显示器 2", "Ceiling display 2")),
        on_w("pressure", "sc-pressure-monitor", 2.6, W9, L("房间压差监测（负压）", "Room pressure monitor (negative)")),
        P("sanitizer", "hand-sanitizer", -3.9, 3.6, label=L("手消毒液", "Hand rub")),
    ],
    slots=[slot("table", "monitor", 0, -0.3, 90)],
    staff=OR_TEAM_9,
    zones=[zone("sterile", L("隔离手术间（限制区）", "Isolation OR (restricted)"), W9, D9, OR_ROLES)],
    caps=OR_CAPS + ["ultrasound", "echocardiography"],
    tags=["surgery", "restricted", "isolation", "negative-pressure"],
)

# OR · hybrid (11 × 9)
WH, DH = 11, 9
template(
    "sc-or-hybrid",
    L("复合手术室（机器人血管造影）", "Hybrid OR (robotic angiography)"),
    L("11 × 9 m（99 m²）复合手术室：机器人落地式血管造影 C 形臂、可透 X 线的碳纤维浮动手术床、3.2 × 3.2 m Ⅰ级层流天花、吊顶铅屏风与床旁铅帘、高压注射器、体外循环机待命、经食道超声；西侧墙为带铅玻璃观察窗的控制室。适用于 TAVI、腔内修复（EVAR/TEVAR）、复合神经血管与创伤手术。防护按医学物理师的屏蔽计算（常见 1.5–3 mm 铅当量）。",
      "11 × 9 m (99 m²) hybrid OR: robotic floor-mounted angiography C-arm, radiolucent carbon-fibre floating table, a 3.2 × 3.2 m Class I laminar ceiling, ceiling lead shield and table-side lead curtain, contrast injector, a heart-lung machine on standby and TOE ultrasound; the west wall is the control room's lead-glass window. For TAVI, EVAR/TEVAR, hybrid neurovascular and trauma surgery. Shielding follows the medical physicist's calculation (commonly 1.5–3 mm lead equivalent)."),
    "operating-room", (WH, DH), "sc-or-floor",
    [
        part("n", [door("sliding-door", 1.6, 3.4, 2.6)], OR_WALL),
        part("w", [window(3.0, 0, 1.0, 1.3), door("sliding-door", 1.4, 3.0, 2.4)], OR_WALL),
        part("e", [door("sliding-door", 1.4, 3.1, 2.6), door("sliding-door", 1.4, -1.2, 2.6)], OR_WALL),
        part("s", [door("sliding-door", 2.4, -2.4, 3)], OR_WALL),
    ],
    {"text": L("复合手术室 · 放射防护", "Hybrid OR · radiation area"), "color": "#d98a3d"},
    [{"x": -3.5, "z": -2.5}, {"x": 3.5, "z": -2.5}, {"x": -3.5, "z": 2.5}, {"x": 3.5, "z": 2.5}],
    [
        P("canopy", "sc-laminar-canopy-xl", 0.6, 0.2, label=L("Ⅰ级层流送风天花", "Class I laminar-flow ceiling")),
        P("table", "sc-hybrid-table", 0.6, 0.2, 90, L("复合手术床", "Hybrid OR table")),
        P("light", "surgical-light", 0.6, 0.2, label=L("LED 无影灯", "LED surgical light")),
        P("c-arm", "sc-robotic-c-arm", 1.2, -2.3, label=L("机器人血管造影 C 形臂", "Robotic angiography C-arm")),
        P("shield", "sc-lead-shield", 1.4, -0.75, label=L("铅屏风", "Lead shield")),
        P("injector", "sc-contrast-injector", 2.9, -1.6, label=L("高压注射器", "Contrast injector")),
        P("anaesthesia", "sc-anaesthesia-workstation", -1.95, -0.2, 90, L("麻醉工作站", "Anaesthesia workstation")),
        P("monitor", "patient-monitor", -1.95, 1.0, label=L("麻醉监护仪", "Anaesthesia monitor")),
        P("anaes-pendant", "sc-anaesthesia-pendant", -1.95, -1.5, label=L("麻醉吊塔", "Anaesthesia pendant")),
        P("ultrasound", "ultrasound-machine", -3.0, -3.7, label=L("经食道超声", "TOE ultrasound")),
        P("hlm", "sc-heart-lung-machine", -1.6, -3.85, label=L("体外循环机（待命）", "Heart-lung machine (standby)")),
        on_w("drugs", "medication-cabinet", -3.4, WH, L("麻醉药品柜", "Anaesthetic drug cabinet")),
        on_w("iv-cart", "treatment-cart", -2.2, WH, L("静脉穿刺与治疗车", "IV cannulation & treatment cart")),
        P("infusion-pump", "infusion-pump", -0.6, 1.3, label=L("输液泵", "Infusion pump")),
        P("surg-pendant", "sc-surgical-pendant", 3.0, 1.2, label=L("外科吊塔", "Surgical pendant")),
        P("back-table", "sc-sterile-setup-table", 0.8, 2.0, label=L("无菌器械台", "Sterile set-up table")),
        *setup_layout(0.8, 2.0),
        P("mayo", "sc-mayo-stand", 1.8, 1.25, label=L("Mayo 托盘", "Mayo stand")),
        P("smoke-evac", "sc-smoke-evacuator", 3.0, 1.82, label=L("烟雾排除器（吊塔旁）", "Smoke evacuator (by the pendant)")),
        on_e("count-board", "sc-count-board", 1.0, WH, L("手术清点板", "Surgical count board")),
        P("rf-wand", "sc-rf-wand", WH / 2 - 0.3, 1.0, 90, L("RF 纱布检测棒", "RF sponge-detection wand"), y=0.75),
        P("apron-1", "sc-lead-apron", -4.85, DH / 2 - 0.4, 0, L("铅衣", "Lead apron"), y=0.95),
        P("apron-2", "sc-lead-apron", -4.3, DH / 2 - 0.4, 0, L("铅衣", "Lead apron"), y=0.95),
        P("display-1", "sc-ceiling-display", -0.4, 2.7, 180, L("吊臂显示器（造影/导航）", "Ceiling display (angiography / navigation)")),
        P("display-2", "sc-ceiling-display", -0.6, -2.4, label=L("吊臂显示器 2", "Ceiling display 2")),
        on_e("pacs", "sc-wall-display", -3.4, WH, L("PACS 显示屏", "PACS display")),
        on_s("control-panel", "sc-or-control-panel", 0.6, DH, L("环境控制面板", "OR control panel")),
        on_s("checklist", "sc-who-checklist", 2.6, DH, L("WHO 手术安全核查板", "WHO Surgical Safety Checklist")),
        on_s("aprons", "sc-apron-rack", -4.6, DH, L("铅衣架", "Lead apron rack")),
        on_s("records", "records-terminal", 4.6, DH, L("手术室电子病历终端", "Theatre EHR terminal")),
        on_n("grille-1", "sc-return-grille", 2.0, DH),
        on_s("grille-2", "sc-return-grille", -4.6, DH),
        P("sanitizer", "hand-sanitizer", -0.6, 4.0, label=L("手消毒液", "Hand rub")),
    ],
    slots=[slot("table", "monitor", 0.6, 0.2, 90)],
    staff=or_team((0.8, 2.85, 180), (2.4, 3.6, 180), (-2.85, 0.4, 90)),
    zones=[zone("sterile", L("复合手术室（限制区，放射防护）", "Hybrid OR (restricted, radiation)"), WH, DH, HYBRID_ROLES)],
    caps=OR_CAPS + ["fluoroscopy", "ultrasound", "echocardiography"],
    tags=["surgery", "restricted", "hybrid", "class-i", "radiation"],
)

# Hybrid OR control & technical room (4 × 9); its local east wall is the OR's local west wall
template(
    "sc-or-hybrid-control",
    L("复合手术室控制室", "Hybrid OR control room"),
    L("复合手术室的控制与技术间：成像控制台面向铅玻璃观察窗，内侧是高压发生器、不间断电源与图像处理机柜；门可直通手术间。",
      "Control and technical room of the hybrid OR: the imaging console faces the lead-glass window, with the generator, UPS and image-processing cabinets behind; a door leads straight into the OR."),
    "imaging", (4, 9), "lino",
    [
        part("n", (), CLEAN_WALL),
        part("w", (), CLEAN_WALL),
        part("e", [window(3.0, 0, 1.0, 1.3), door("sliding-door", 1.4, 3.0, 2.4)], OR_WALL),
        part("s", [door("door", 1.4, -0.8, 2.6)], CLEAN_WALL),
    ],
    {"text": L("复合手术控制室", "Hybrid OR control"), "color": "#d98a3d"},
    [{"x": 0, "z": -2.5}, {"x": 0, "z": 2.5}],
    [
        P("console", "radiology-console", 1.05, 0, 90, L("血管造影控制台", "Angiography console")),
        P("chair-1", "office-chair", -0.1, -0.6),
        P("chair-2", "office-chair", -0.1, 0.6),
        on_n("generator", "cabinet", -1.0, 9, L("高压发生器柜", "X-ray generator cabinet")),
        on_n("ups", "cabinet", 0.1, 9, L("UPS 与图像处理机柜", "UPS & image-processing rack")),
        P("records", "records-terminal", 1.45, -2.6, label=L("电子病历终端", "EHR terminal")),
        on_w("pacs", "sc-wall-display", -1.6, 4, L("PACS 显示屏", "PACS display")),
        on_w("aprons", "sc-apron-rack", 3.4, 4, L("铅衣架", "Lead apron rack")),
    ],
    staff=[{"id": "radiographer", "role": "radiologist", "name": L("介入放射医师", "Interventional radiologist"), "x": -0.6, "z": -2.0, "rot": 90,
            "greeting": L("造影前请所有人穿好铅衣，铅屏风我来摆位。", "Lead aprons on for everyone before we screen — I'll position the shield.")}],
    caps=["records"],
    tags=["hybrid", "imaging", "control-room"],
)

# Scrub bay (3 × 4): open to the corridor, sliding doors into the ORs on both sides
template(
    "sc-scrub-bay",
    L("刷手间", "Scrub bay"),
    L("两间手术室之间的刷手间：双人感应刷手池、手消毒液和刷手计时器，向半限制区走廊敞开，两侧感应门直通手术室。",
      "Scrub bay between two ORs: a twin sensor-operated scrub trough, surgical hand-rub and a scrub timer; open to the semi-restricted corridor, with sensor doors straight into the ORs on both sides."),
    "corridor", (3, 4), "sc-or-floor",
    [
        part("n", (), OR_WALL),
        part("w", [door("sliding-door", 1.4, 0.6, 2.6)], OR_WALL),
        part("e", [door("sliding-door", 1.4, 0.6, 2.6)], OR_WALL),
        part("s", [door("opening", 2.2, 0, 3)], OR_WALL),
    ],
    {"text": L("刷手", "Scrub"), "color": "#3f8f5a"},
    [{"x": 0, "z": 0}],
    [
        on_n("scrub", "sc-scrub-trough", 0, 4, L("双人刷手池", "Twin scrub trough")),
        P("clock", "wall-clock", 0, -1.775, label=L("刷手计时钟", "Scrub clock")),
        on_e("caps-masks", "glove-dispenser", -1.0, 3, L("帽子/口罩", "Caps & masks")),
    ],
    caps=[],
    tags=["scrub", "semi-restricted"],
)

# Sterile set-up (lay-up) room (3 × 5): door to the sterile core (local north) and to the ORs on both sides
template(
    "sc-prep-room",
    L("无菌准备间", "Sterile set-up room"),
    L("器械护士打开器械包、按清点单摆台的无菌准备间：连通无菌核心区（北侧）和两侧手术室；配无菌存放架、摆台器械台与器械配送车。",
      "Sterile set-up (lay-up) room where the scrub nurse opens and lays out the instrument sets against the count sheet: connected to the sterile core (north) and the ORs on both sides; sterile rack, lay-up table and a case cart."),
    "storage", (3, 5), "sc-or-floor",
    [
        part("n", [door("sliding-door", 1.4, 0, 2.6)], OR_WALL),
        part("w", [door("sliding-door", 1.4, 0.8, 2.6)], OR_WALL),
        part("e", [door("sliding-door", 1.4, 0.8, 2.6)], OR_WALL),
        part("s", (), OR_WALL),
    ],
    {"text": L("无菌准备", "Sterile set-up"), "color": "#2f7fd1"},
    [{"x": 0, "z": 0}],
    [
        on_s("rack", "sc-sterile-rack", 0, 5, L("无菌存放架", "Sterile rack")),
        P("lay-up", "instrument-table", -1.025, -1.4, 90, L("摆台器械台", "Lay-up table")),
        P("case-cart", "sc-case-cart", 1.0, -1.525, 90, L("器械配送车", "Case cart")),
    ],
    zones=[zone("sterile", L("无菌准备间（限制区）", "Set-up room (restricted)"), 3, 5, CORE_ROLES)],
    caps=[],
    tags=["sterile", "restricted"],
)

# Anteroom of the isolation OR (3 × 9)
template(
    "sc-or-anteroom",
    L("隔离手术室缓冲间", "Isolation OR anteroom"),
    L("负压隔离手术室的缓冲间：两道互锁门不同时开启，维持走廊 → 缓冲间 → 手术间的压力梯度；配刷手池、防护用品穿戴站、手消毒液和压差监测。",
      "Anteroom of the negative-pressure OR: two interlocked doors never open together, holding the corridor → anteroom → OR pressure cascade; scrub trough, PPE donning station, hand-rub and a pressure monitor."),
    "corridor", (3, 9), "sc-or-floor",
    [
        part("n", (), OR_WALL),
        part("w", (), OR_WALL),
        part("e", [door("sliding-door", 2.0, 1.0, 2.6)], OR_WALL),
        part("s", [door("sliding-door", 1.6, 0, 2.6)], OR_WALL),
    ],
    {"text": L("缓冲间 · 互锁门", "Anteroom · interlocked doors"), "color": "#c9473c"},
    [{"x": 0, "z": -2.5}, {"x": 0, "z": 2.5}],
    [
        on_n("scrub", "sc-scrub-trough", 0, 9, L("刷手池", "Scrub trough")),
        on_w("ppe", "sc-ppe-station", -1.0, 3, L("防护用品穿戴站", "PPE donning station")),
        on_w("pressure", "sc-pressure-monitor", 1.4, 3, L("压差监测", "Pressure monitor")),
        on_e("gloves", "glove-dispenser", -1.6, 3, L("手套", "Gloves")),
        P("sanitizer", "hand-sanitizer", -1.0, 2.6, label=L("手消毒液", "Hand rub")),
        P("ppe-bin", "trash-bin", 1.0, 3.8, label=L("防护用品脱卸废物桶", "PPE doffing bin")),
    ],
    zones=[zone("buffer", L("隔离缓冲间（限制区）", "Isolation anteroom (restricted)"), 3, 9, OR_ROLES)],
    caps=[],
    tags=["isolation", "restricted"],
)

# PACU (14 × 12): 8 bays round a central station
WP, DP = 14, 12
pacu = []
pacu_slots = []
for i, bx in enumerate((-4.5, -1.5, 1.5, 4.5), start=1):
    pacu += [
        P(f"bed-{i}", "hospital-bed", bx, -4.425, label=L(f"复苏床 {i}", f"Recovery bay {i}")),
        P(f"monitor-{i}", "patient-monitor", bx - 0.95, -5.3, label=L(f"{i} 床监护仪", f"Bay {i} monitor")),
        P(f"pump-{i}", "infusion-pump", bx + 0.95, -5.3),
        on_n(f"oxygen-{i}", "oxygen-outlet", bx, DP),
    ]
    pacu_slots.append(slot(f"bed-{i}", f"monitor-{i}", bx, -4.425, 0, id=f"bay-{i}"))
for x in (-3, 0, 3):
    pacu.append(P(f"curtain-n{int(x) + 3}", "privacy-curtain", x, -4.4, 90))
for side, sx, rot in (("w", -1, 90), ("e", 1, 270)):
    for k, zb in enumerate((-0.8, 2.2)):
        i = 5 + k if side == "w" else 7 + k
        pacu += [
            P(f"bed-{i}", "hospital-bed", sx * 5.425, zb, rot, L(f"复苏床 {i}", f"Recovery bay {i}")),
            P(f"monitor-{i}", "patient-monitor", sx * 6.3, zb - 1.15, label=L(f"{i} 床监护仪", f"Bay {i} monitor")),
            (on_w if side == "w" else on_e)(f"oxygen-{i}", "oxygen-outlet", zb, WP),
        ]
        pacu_slots.append(slot(f"bed-{i}", f"monitor-{i}", sx * 5.425, zb, rot, id=f"bay-{i}"))
    pacu.append(P(f"curtain-{side}", "privacy-curtain", sx * 5.4, 0.7))
pacu += [
    P("station", "nurse-station-desk", 0, 0.6, 180, L("复苏室护士站", "PACU nurses' station")),
    P("station-chair", "office-chair", -1.0, 1.9),
    on_s("sink", "sink", -5.6, DP, L("洗手池", "Hand-wash sink")),
    on_s("warming", "sc-warming-cabinet", -4.6, DP, L("加温柜", "Warming cabinet")),
    on_s("drugs", "medication-cabinet", -3.5, DP, L("复苏室药品柜", "PACU drug cabinet")),
    on_s("blood-gas", "blood-gas-analyzer", -2.4, DP, L("床旁血气分析仪", "Point-of-care blood gas analyser")),
    on_s("sanitizer", "hand-sanitizer", -1.6, DP, L("手消毒液", "Hand rub")),
    on_s("crash-cart", "crash-cart", 2.0, DP, L("抢救车", "Crash cart")),
    on_s("defibrillator", "defibrillator", 3.0, DP, L("除颤仪", "Defibrillator")),
    on_s("ventilator", "ventilator", 4.0, DP, L("呼吸机", "Ventilator")),
    on_s("airway", "sc-difficult-airway-trolley", 5.0, DP, L("困难气道车", "Difficult airway trolley")),
    P("warmer-1", "sc-forced-air-warmer", -2.4, 0.6, label=L("充气保温机", "Forced-air warmer")),
    P("warmer-2", "sc-forced-air-warmer", 2.4, 0.6, label=L("充气保温机", "Forced-air warmer")),
    on_n("clock", "wall-clock", 0, DP),
]
template(
    "sc-pacu-8",
    L("麻醉后恢复室（8 床）", "Post-anaesthesia care unit (8 bays)"),
    L("8 床麻醉后恢复室（PACU，一期复苏），护士站居中可直视每张床：每床中心供氧/负压、监护仪（含呼气末二氧化碳）、输液泵与床间隔帘；配抢救车、除颤仪、呼吸机、困难气道车、床旁血气分析与保温设备。8 个手术间对应 8 个复苏床位（常用规划比例约 1:1–1.5:1）。",
      "8-bay post-anaesthesia care unit (Phase I recovery) with a central station in direct view of every bay: piped oxygen and suction, a monitor with capnography, an infusion pump and curtains at each bay; crash cart, defibrillator, ventilator, difficult airway trolley, point-of-care blood gas and warming. Eight bays for eight ORs (a common planning ratio is about 1–1.5 bays per OR)."),
    "icu", (WP, DP), "sc-pacu-floor",
    [part("n", (), CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL), part("s", [door("double-door", 2.4, 0, 3)], CLEAN_WALL)],
    {"text": L("麻醉后恢复室 PACU", "Recovery · PACU"), "color": "#6d9fba"},
    grid_lights(WP, DP, 3, 2),
    pacu,
    slots=pacu_slots,
    staff=[{"id": "nurse", "role": "nurse", "name": L("复苏室护士", "Recovery nurse"), "x": 0, "z": 1.9, "rot": 180,
            "greeting": L("交接时请说清楚术式、麻醉方式、术中出血和镇痛计划。", "For handover I need the procedure, the anaesthetic, blood loss and the analgesia plan.")}],
    caps=["cardiac-monitor", "capnography", "oxygen", "suction", "infusion-pump", "ventilator", "niv", "defibrillator", "crash-cart", "airway", "medications", "lab-blood-gas", "records"],
    tags=["pacu", "recovery", "perioperative"],
)

# Pre-operative holding (9 × 12): 5 bays; local west door leads to the patient transfer zone
WQ, DQ = 9, 12
preop = []
preop_slots = []
for i, bx in enumerate((-3.0, 0.0, 3.0), start=1):
    preop += [
        P(f"bed-{i}", "hospital-bed", bx, -4.425, label=L(f"术前床 {i}", f"Holding bay {i}")),
        P(f"monitor-{i}", "patient-monitor", bx - 0.95, -5.3, label=L(f"{i} 床监护仪", f"Bay {i} monitor")),
        on_n(f"oxygen-{i}", "oxygen-outlet", bx, DQ),
    ]
    preop_slots.append(slot(f"bed-{i}", f"monitor-{i}", bx, -4.425, 0, id=f"bay-{i}"))
preop += [P("curtain-1", "privacy-curtain", -1.5, -4.4, 90), P("curtain-2", "privacy-curtain", 1.5, -4.4, 90)]
for k, zb in enumerate((-0.6, 2.6)):
    i = 4 + k
    preop += [
        P(f"bed-{i}", "hospital-bed", 2.925, zb, 270, L(f"术前床 {i}", f"Holding bay {i}")),
        P(f"monitor-{i}", "patient-monitor", 3.8, zb - 1.15, label=L(f"{i} 床监护仪", f"Bay {i} monitor")),
        on_e(f"oxygen-{i}", "oxygen-outlet", zb, WQ),
    ]
    preop_slots.append(slot(f"bed-{i}", f"monitor-{i}", 2.925, zb, 270, id=f"bay-{i}"))
preop += [
    P("curtain-3", "privacy-curtain", 2.9, 1.0),
    on_w("desk", "desk", -0.6, WQ, L("核对台", "Check-in desk")),
    P("chair", "office-chair", -3.0, -0.6),
    P("records", "records-terminal", -4.025, 1.0, label=L("电子病历终端", "EHR terminal")),
    P("ultrasound", "ultrasound-machine", -1.0, 2.0, label=L("超声（神经阻滞）", "Ultrasound (nerve blocks)")),
    on_s("iv-cart", "treatment-cart", -3.0, DQ, L("静脉穿刺与治疗车", "IV cannulation & treatment cart")),
    on_s("sink", "sink", 2.6, DQ, L("洗手池", "Hand-wash sink")),
    on_s("sanitizer", "hand-sanitizer", -1.6, DQ, L("手消毒液", "Hand rub")),
]
template(
    "sc-preop-holding",
    L("术前等候与准备区（5 床）", "Pre-operative holding (5 bays)"),
    L("术前等候与准备区：核对身份、手术部位标记与知情同意，建立静脉通路，超声引导神经阻滞；每床监护与中心供氧。经换床间（local 西门）接收病房患者，经北侧走廊送入手术室。",
      "Pre-operative holding: identity, site-marking and consent checks, IV access and ultrasound-guided nerve blocks; each bay monitored with piped oxygen. Receives ward patients through the transfer zone (local west door) and sends them to the ORs along the corridor."),
    "ward", (WQ, DQ), "sc-pacu-floor",
    [part("n", (), CLEAN_WALL), part("w", [door("door", 1.6, 4.0, 2.6)], CLEAN_WALL), part("e", (), CLEAN_WALL), part("s", [door("double-door", 2.0, 0, 3)], CLEAN_WALL)],
    {"text": L("术前准备区", "Pre-op holding"), "color": "#6d9fba"},
    grid_lights(WQ, DQ, 2, 2),
    preop,
    slots=preop_slots,
    staff=[{"id": "nurse", "role": "nurse", "name": L("术前准备护士", "Pre-op nurse"), "x": -2.4, "z": 0.8, "rot": 90,
            "greeting": L("先核对腕带、手术部位标记和知情同意，再送进手术室。", "Wristband, site marking and consent are checked here before anyone goes in.")}],
    caps=["cardiac-monitor", "capnography", "oxygen", "suction", "iv-access", "ultrasound", "records"],
    tags=["preop", "perioperative"],
)

# Staff changing room (7 × 9): enter from the unrestricted side (local south), leave in scrubs to the corridor (local north)
WC, DC = 7, 9
template(
    "sc-staff-changing",
    L("医护更衣室", "Staff changing room"),
    L("从非限制区进入（南门）：脱外出鞋与外衣存入外区更衣柜，跨过换鞋凳，在内区领取洗手衣、帽子和口罩，经北门进入半限制区走廊——单向流线。",
      "Enter from the unrestricted side (south door): outdoor shoes and clothes go in the outer lockers, step over the bench, collect scrubs, cap and mask on the inner side and leave by the north door into the semi-restricted corridor — a one-way route."),
    "restroom", (WC, DC), "tile-white",
    [part("n", [door("door", 1.4, 2.4, 2.6)], CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL), part("s", [door("door", 1.4, -2.4, 2.6)], CLEAN_WALL)],
    {"text": L("更衣 · 外区 → 内区", "Changing · outer → inner"), "color": "#7fb0a6"},
    [{"x": 0, "z": -2.2}, {"x": 0, "z": 2.2}],
    [on_w(f"locker-o{k}", "locker", z, WC, L("外区更衣柜", "Outer locker")) for k, z in enumerate((1.2, 2.2, 3.2), start=1)]
    + [on_s(f"locker-s{k}", "locker", x, DC, L("外区更衣柜", "Outer locker")) for k, x in enumerate((-0.6, 0.4, 1.4, 2.4), start=1)]
    + [
        P("bench", "sc-step-over-bench", -1.825, 0, label=L("换鞋跨越凳", "Step-over bench")),
        on_n("scrubs", "sc-scrubs-dispenser", -2.6, DC, L("洗手衣发放机", "Scrub dispenser")),
        on_n("sink", "sink", -1.0, DC, L("洗手池", "Hand-wash sink")),
        on_n("caps-masks", "glove-dispenser", 0.4, DC, L("帽子/口罩", "Caps & masks")),
        P("laundry", "trash-bin", 1.0, -3.9, label=L("洗手衣回收", "Scrubs return")),
    ]
    + [on_e(f"locker-i{k}", "locker", z, WC, L("内区鞋柜", "Theatre-shoe locker")) for k, z in enumerate((-2.6, -1.6), start=1)],
    caps=[],
    tags=["changing", "staff", "zoning"],
)

# Frozen-section lab (4.5 × 7)
WF, DF = 4.5, 7
template(
    "sc-frozen-section-lab",
    L("术中冰冻病理室", "Frozen-section laboratory"),
    L("紧邻手术室的术中快速冰冻病理室：冰冻切片机、快速染色台、显微镜与数字切片扫描，病理医师在约 20–30 分钟内回报术中诊断（如切缘、淋巴结）。",
      "Intra-operative frozen-section lab next to the ORs: cryostat, rapid staining bench, microscope and slide scanner; the pathologist reports intra-operative diagnoses (margins, nodes) within about 20–30 minutes."),
    "pathology", (WF, DF), "lino",
    [part("n", (), CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL), part("s", [door("door", 1.4, 0, 2.6)], CLEAN_WALL)],
    {"text": L("冰冻病理", "Frozen section"), "color": "#a397bc"},
    [{"x": 0, "z": -1.8}, {"x": 0, "z": 1.8}],
    [
        P("cryostat", "sc-cryostat", -1.6, -2.6, label=L("冰冻切片机", "Cryostat")),
        P("scanner", "slide-scanner", -1.6, -1.2, label=L("数字切片扫描仪", "Slide scanner")),
        on_w("microscope", "microscope", 0.5, WF, L("显微镜", "Microscope")),
        on_e("bench", "lab-bench", -1.0, WF, L("快速染色台", "Rapid staining bench")),
        on_n("sink", "sink", 1.4, DF, L("洗手池", "Sink")),
        P("records", "records-terminal", 1.7, 1.2, label=L("病理报告终端", "Pathology reporting terminal")),
        P("stool", "stool", -0.9, 0.5),
    ],
    staff=[{"id": "pathologist", "role": "pathologist", "name": L("病理医师", "Pathologist"), "x": 0, "z": -0.6, "rot": 270,
            "greeting": L("冰冻标本送来后大约二十分钟出报告。", "Send the frozen specimen over — I'll call the result through in about twenty minutes.")}],
    caps=["histopathology", "cytology", "records"],
    tags=["pathology", "frozen-section"],
)

# Anaesthesia workroom (7 × 4.5)
WA, DA = 7, 4.5
template(
    "sc-anaesthesia-workroom",
    L("麻醉准备间", "Anaesthesia workroom"),
    L("麻醉科准备间：备用麻醉工作站、困难气道车、除颤仪、神经阻滞超声，手术部卫星血库冰箱、床旁血气分析仪、麻醉药品柜与药品冰箱。",
      "Anaesthesia workroom: spare anaesthesia workstation, difficult airway trolley, defibrillator and block ultrasound, the suite's satellite blood refrigerator, a point-of-care blood gas analyser, the anaesthetic drug cabinet and the drug fridge."),
    "storage", (WA, DA), "lino",
    [part("n", (), CLEAN_WALL), part("w", (), CLEAN_WALL), part("e", (), CLEAN_WALL), part("s", [door("door", 1.4, 2.2, 2.6)], CLEAN_WALL)],
    {"text": L("麻醉准备间", "Anaesthesia workroom"), "color": "#3f8f5a"},
    [{"x": -1.75, "z": 0}, {"x": 1.75, "z": 0}],
    [
        on_n("blood-fridge", "blood-bank-fridge", -2.9, DA, L("卫星血库冰箱", "Satellite blood refrigerator")),
        on_n("drug-fridge", "medication-fridge", -2.0, DA, L("药品冰箱", "Drug fridge")),
        on_n("drugs", "medication-cabinet", -0.95, DA, L("麻醉药品柜", "Anaesthetic drug cabinet")),
        on_n("blood-gas", "blood-gas-analyzer", 0.05, DA, L("血气分析仪", "Blood gas analyser")),
        on_n("cabinet", "cabinet", 1.0, DA, L("气道耗材柜", "Airway supplies")),
        on_n("sink", "sink", 2.2, DA, L("洗手池", "Sink")),
        on_s("spare-machine", "sc-anaesthesia-workstation", -2.7, DA, L("备用麻醉工作站", "Spare anaesthesia workstation")),
        on_s("airway", "sc-difficult-airway-trolley", -1.6, DA, L("困难气道车", "Difficult airway trolley")),
        on_s("ultrasound", "ultrasound-machine", -0.6, DA, L("神经阻滞超声", "Block ultrasound")),
        on_s("defibrillator", "defibrillator", 0.4, DA, L("除颤仪", "Defibrillator")),
        P("records", "records-terminal", 3.0, 1.0, label=L("电子病历终端", "EHR terminal")),
    ],
    caps=["anesthesia", "airway", "ventilator", "blood-bank", "medications", "lab-blood-gas", "defibrillator", "ultrasound", "records"],
    tags=["anaesthesia", "storage"],
)

# Bed lift car (2.6 × 3.0)
template(
    "sc-bed-lift-car",
    L("医用病床电梯", "Bed lift"),
    L("医用病床电梯轿厢：2.6 × 3.0 m，1.8 m 宽侧开门，可容纳病床与陪同医护。", "Hospital bed-lift car: 2.6 × 3.0 m with a 1.8 m side-opening door, room for a bed and its escort."),
    "elevator", (2.6, 3.0), "steel",
    [part("n", (), {"material": "steel"}), part("w", (), {"material": "steel"}), part("e", (), {"material": "steel"}),
     part("s", [door("sliding-door", 1.8, 0, 2.4)], {"material": "steel"})],
    None,
    [{"x": 0, "z": 0}],
    [],
    caps=[],
    tags=["elevator", "connector", "bed-lift"],
)
