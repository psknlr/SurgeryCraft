"""SurgeryCraft operating-department catalog: materials + equipment (voxel parts, front faces +Z)."""
from common import B, L, BASE_MATERIALS, num

CATALOG_ID = "surgerycraft-or"

MATERIALS = [
    {"id": "sc-or-wall", "color": "#d5e7e3", "pattern": "grid", "variance": 0.025, "roughness": 0.5},
    {"id": "sc-or-wall-base", "color": "#7fb0a6", "pattern": "flat", "variance": 0.03, "roughness": 0.5},
    {"id": "sc-or-floor", "color": "#8dbcb3", "pattern": "noise", "variance": 0.035, "roughness": 0.6, "castShadow": False},
    {"id": "sc-core-floor", "color": "#b4d2cc", "pattern": "noise", "variance": 0.035, "roughness": 0.6, "castShadow": False},
    {"id": "sc-pacu-floor", "color": "#b9cfd9", "pattern": "noise", "variance": 0.035, "roughness": 0.6, "castShadow": False},
    {"id": "sc-cssd-floor", "color": "#c9d3cf", "pattern": "noise", "variance": 0.04, "roughness": 0.6, "castShadow": False},
    {"id": "sc-hepa", "color": "#f2f6f6", "pattern": "dots", "variance": 0.05, "emissive": "#e8f4ff", "emissiveIntensity": 0.25, "roughness": 0.5},
    {"id": "sc-drape", "color": "#3f84b6", "pattern": "noise", "variance": 0.06, "roughness": 0.9},
    {"id": "sc-drape-green", "color": "#4e9a86", "pattern": "noise", "variance": 0.06, "roughness": 0.9},
    {"id": "sc-carbon", "color": "#2c3135", "pattern": "grid", "variance": 0.05, "roughness": 0.4, "metalness": 0.2},
    {"id": "sc-robot", "color": "#f1f3f4", "pattern": "flat", "variance": 0.02, "roughness": 0.35, "metalness": 0.1},
    {"id": "sc-robot-accent", "color": "#2f7fd1", "pattern": "flat", "variance": 0.03, "roughness": 0.4},
    {"id": "sc-lead-acrylic", "color": "#b6d8d0", "pattern": "flat", "variance": 0.02, "opacity": 0.35, "roughness": 0.1, "castShadow": False},
    {"id": "sc-lead-rubber", "color": "#4b565a", "pattern": "stripe", "variance": 0.05, "roughness": 0.8},
    {"id": "sc-zone-red", "color": "#cf3b30", "pattern": "flat", "variance": 0.02, "castShadow": False},
    {"id": "sc-led-white", "color": "#f4f9ff", "pattern": "flat", "variance": 0, "emissive": "#ffffff", "emissiveIntensity": 1.0},
    {"id": "sc-frost-glass", "color": "#dcecec", "pattern": "flat", "variance": 0.02, "opacity": 0.55, "roughness": 0.2, "castShadow": False},
    {"id": "sc-gas-air", "color": "#2b2b2b", "pattern": "flat", "variance": 0.02},
    {"id": "sc-gas-n2o", "color": "#3a64b5", "pattern": "flat", "variance": 0.02},
    {"id": "sc-gas-agss", "color": "#b5479a", "pattern": "flat", "variance": 0.02},
    {"id": "sc-matte-black", "color": "#25292c", "pattern": "flat", "variance": 0.01, "roughness": 0.5},
]
MAT_IDS = BASE_MATERIALS | {m["id"] for m in MATERIALS}

EQUIPMENT = []


def eq(id, name, category, description, footprint, parts, *, usage=None, caps=(), solid=True, interaction="none",
       prompt=None, screen="none", light=None, tags=(), portable=None, reach=None, points=None, behavior=None):
    w, d, h = footprint
    tol = 0.05
    for i, p in enumerate(parts):
        assert p["m"] in MAT_IDS, (id, i, p["m"])
        (px, py, pz), (sx, sy, sz) = p["p"], p["s"]
        assert abs(px) + sx / 2 <= w / 2 + tol, (id, i, "x", p)
        assert abs(pz) + sz / 2 <= d / 2 + tol, (id, i, "z", p)
        assert py - sy / 2 >= -tol and py + sy / 2 <= h + tol, (id, i, "y", p)
    if screen != "none":
        assert any(p.get("name") == "screen" for p in parts), (id, "screen part")
    e = {"id": id, "name": name, "category": category, "description": description}
    if usage:
        e["usage"] = usage
    e["capabilities"] = list(caps)
    e["footprint"] = {"w": num(w), "d": num(d), "h": num(h)}
    e["solid"] = solid
    inter = {"kind": interaction}
    if prompt:
        inter["prompt"] = prompt
    e["interaction"] = inter
    e["screen"] = screen
    if light:
        e["light"] = light
    e["tags"] = list(tags)
    if portable:
        e["portable"] = portable
    if reach is not None:
        e["reach"] = reach
    if points:
        e["interactionPoints"] = points
    if behavior:
        e["behavior"] = behavior
    e["parts"] = parts
    EQUIPMENT.append(e)
    return e


def casters(w, d, inset=0.06, size=0.08, m="rubber"):
    hx, hz = w / 2 - inset, d / 2 - inset
    return [B(m, sx * hx, size / 2, sz * hz, size, size, size) for sx in (-1, 1) for sz in (-1, 1)]


# ---------------------------------------------------------------- tables & patient support

eq("sc-hybrid-table", L("复合手术床（碳纤维浮动床面）", "Hybrid OR table (floating carbon-fibre top)"), "surgery",
   L("复合手术室专用手术床：单立柱底座、可透 X 线的长碳纤维浮动床面（头脚全程可透视）、分节软垫、侧轨、双侧臂板、麻醉头架及床旁铅橡胶防护帘。",
     "Hybrid-OR table: single pedestal, long radiolucent carbon-fibre floating top for head-to-toe imaging, padded segments, side rails, arm boards, an anaesthesia screen frame and a table-side lead-rubber curtain."),
   (1.1, 3.2, 1.3),
   [
       B("plastic", 0, 0.04, 0.85, 0.6, 0.08, 1.1),
       B("sc-robot", 0, 0.4, 0.85, 0.38, 0.64, 0.46),
       B("sc-robot-accent", 0, 0.46, 1.085, 0.3, 0.04, 0.01),
       B("steel", 0, 0.76, 0.7, 0.5, 0.06, 0.8),
       B("sc-carbon", 0, 0.82, 0, 0.56, 0.06, 3.12),
       B("navy", 0, 0.885, -1.4, 0.32, 0.07, 0.3),
       B("navy", 0, 0.885, -0.65, 0.52, 0.07, 1.1),
       B("navy", 0, 0.885, 0.3, 0.52, 0.07, 0.72),
       B("navy", 0, 0.885, 1.05, 0.52, 0.07, 0.66),
       B("chrome", -0.29, 0.83, -0.2, 0.02, 0.03, 2.6),
       B("chrome", 0.29, 0.83, -0.2, 0.02, 0.03, 2.6),
       B("steel", -0.43, 0.82, -0.95, 0.28, 0.03, 0.14),
       B("navy", -0.44, 0.86, -0.95, 0.24, 0.05, 0.16),
       B("steel", 0.43, 0.82, -0.95, 0.28, 0.03, 0.14),
       B("navy", 0.44, 0.86, -0.95, 0.24, 0.05, 0.16),
       B("chrome", -0.3, 1.04, -1.12, 0.025, 0.4, 0.025),
       B("chrome", 0.3, 1.04, -1.12, 0.025, 0.4, 0.025),
       B("chrome", 0, 1.235, -1.12, 0.62, 0.025, 0.025),
       B("sc-drape", 0, 1.08, -1.12, 0.58, 0.3, 0.01),
       B("sc-lead-rubber", 0.3, 0.55, -0.1, 0.02, 0.5, 1.6),
       B("chrome", 0.3, 0.81, -0.1, 0.03, 0.03, 1.64),
       B("coal", -0.3, 0.68, 0.55, 0.05, 0.16, 0.04),
       B("led-blue", -0.3, 0.73, 0.575, 0.03, 0.02, 0.01),
   ],
   usage=L("按术式摆放体位并固定约束带，受压部位加衬垫；成像前将床面移入 C 形臂的投照范围，并确认铅帘与铅屏风到位。",
           "Position and strap the patient, pad pressure points; float the top into the C-arm's field before imaging and check that the lead curtain and shield are in place."),
   caps=["surgery"], interaction="bed", prompt=L("E · 复合手术床", "E · Hybrid OR table"), tags=["or", "bed", "hybrid", "radiolucent"])

eq("sc-mayo-stand", L("Mayo 器械托盘架", "Mayo instrument stand"), "surgery",
   L("跨越手术床的可升降器械托盘，铺无菌巾并摆放当前步骤常用器械。", "Height-adjustable tray that reaches over the table, draped sterile and laid with the instruments for the current step."),
   (0.6, 0.5, 1.25),
   [
       B("chrome", 0, 0.02, 0.16, 0.5, 0.04, 0.06),
       B("chrome", -0.22, 0.02, 0, 0.06, 0.04, 0.38),
       B("rubber", -0.22, 0.04, -0.18, 0.06, 0.06, 0.06),
       B("rubber", 0.22, 0.04, 0.16, 0.06, 0.06, 0.06),
       B("chrome", -0.22, 0.6, -0.12, 0.04, 1.1, 0.04),
       B("steel", -0.04, 1.12, 0.02, 0.5, 0.03, 0.42),
       B("sc-drape", -0.04, 1.145, 0.02, 0.54, 0.02, 0.46),
       B("chrome", -0.18, 1.165, 0.0, 0.02, 0.01, 0.2),
       B("chrome", -0.1, 1.165, 0.0, 0.02, 0.01, 0.22),
       B("chrome", -0.02, 1.165, 0.0, 0.02, 0.01, 0.2),
       B("chrome", 0.06, 1.165, 0.02, 0.03, 0.01, 0.16),
       B("paper", 0.15, 1.165, -0.08, 0.12, 0.02, 0.1),
   ],
   interaction="storage", prompt=L("E · Mayo 托盘", "E · Mayo stand"), tags=["or", "sterile"])

# ---------------------------------------------------------------- imaging

eq("sc-robotic-c-arm", L("机器人落地式血管造影 C 形臂", "Robotic floor-mounted angiography C-arm"), "imaging",
   L("复合手术室的机器人落地式血管造影系统：多轴机械臂带动 C 形臂（球管与平板探测器），停放位不占用手术区，可在术中完成血管造影、透视和锥形束 CT。",
     "Robotic floor-mounted angiography system for the hybrid OR: a multi-axis robot carries the C-arm (tube and flat-panel detector), parks clear of the sterile field and delivers angiography, fluoroscopy and cone-beam CT during surgery."),
   (1.4, 2.4, 2.6),
   [
       B("plastic", 0, 0.04, -0.5, 1.2, 0.08, 1.2),
       B("rubber", -0.5, 0.04, -1.0, 0.12, 0.08, 0.12),
       B("rubber", 0.5, 0.04, -1.0, 0.12, 0.08, 0.12),
       B("sc-robot", 0, 0.14, -0.5, 0.92, 0.12, 0.92),
       B("led-blue", 0, 0.205, -0.04, 0.5, 0.02, 0.01),
       B("sc-robot", 0, 0.66, -0.5, 0.62, 0.92, 0.62),
       B("sc-robot-accent", 0, 0.96, -0.5, 0.63, 0.06, 0.63),
       B("warning-yellow", 0.18, 0.78, -0.185, 0.16, 0.08, 0.01),
       B("coal", -0.1, 0.7, -0.19, 0.3, 0.22, 0.01),
       B("screen-dark", -0.1, 0.7, -0.183, 0.26, 0.18, 0.006, name="screen"),
       B("sc-robot", 0, 1.32, -0.38, 0.56, 0.42, 0.66),
       B("coal", 0, 1.32, -0.04, 0.3, 0.3, 0.02),
       B("sc-robot", 0, 1.52, 0.22, 0.4, 0.36, 0.92),
       B("sc-robot", 0, 1.4, 0.74, 0.34, 0.5, 0.34),
       B("sc-robot", -0.56, 1.36, 0.92, 0.18, 1.72, 0.22),
       B("sc-robot", -0.14, 2.2, 0.92, 0.66, 0.16, 0.22),
       B("sc-robot", -0.14, 0.52, 0.92, 0.66, 0.16, 0.22),
       B("coal", 0.26, 2.06, 0.92, 0.52, 0.14, 0.5),
       B("black", 0.26, 1.985, 0.92, 0.46, 0.012, 0.44),
       B("sc-robot-accent", 0.26, 2.08, 0.92, 0.53, 0.03, 0.51),
       B("sc-robot", 0.26, 0.72, 0.92, 0.42, 0.32, 0.42),
       B("coal", 0.26, 0.92, 0.92, 0.26, 0.08, 0.26),
       B("warning-yellow", 0.26, 0.72, 1.135, 0.12, 0.06, 0.01),
   ],
   usage=L("由放射技师在控制室或床旁操作：先确认术区人员佩戴铅衣、铅屏风就位，再进行透视、数字减影血管造影或锥形束 CT；遵循辐射防护最优化（ALARA）原则。",
           "Run by the radiographer from the control room or tableside: confirm lead aprons and the ceiling shield first, then acquire fluoroscopy, DSA or cone-beam CT; keep doses as low as reasonably achievable (ALARA)."),
   caps=["fluoroscopy"], interaction="device", prompt=L("E · 使用血管造影 C 形臂", "E · Use the angiography C-arm"), screen="xray",
   tags=["or", "hybrid", "imaging", "radiation"])

eq("sc-contrast-injector", L("高压造影剂注射器", "Contrast power injector"), "imaging",
   L("双筒高压注射器（造影剂与生理盐水），立柱式，带触摸控制屏，与血管造影系统联动。", "Dual-syringe power injector (contrast and saline) on a pedestal with a touch-screen controller, synchronised with the angiography system."),
   (0.6, 0.6, 1.65),
   casters(0.6, 0.6) + [
       B("plastic", 0, 0.12, 0, 0.5, 0.08, 0.5),
       B("chrome", 0, 0.75, -0.05, 0.06, 1.2, 0.06),
       B("sc-robot", 0, 1.38, 0.0, 0.34, 0.22, 0.3),
       B("lead-glass", -0.08, 1.38, 0.2, 0.08, 0.08, 0.16),
       B("lead-glass", 0.08, 1.38, 0.2, 0.08, 0.08, 0.16),
       B("water", 0.08, 1.38, 0.22, 0.05, 0.05, 0.1),
       B("led-amber", -0.08, 1.45, 0.16, 0.08, 0.02, 0.02),
       B("plastic", 0, 1.56, -0.12, 0.3, 0.18, 0.04),
       B("screen-dark", 0, 1.56, -0.097, 0.26, 0.14, 0.006, name="screen"),
   ],
   screen="text", tags=["or", "hybrid", "imaging"])

eq("sc-lead-shield", L("吊顶式铅屏风", "Ceiling-suspended lead shield"), "imaging",
   L("吊顶悬挂的铅当量丙烯酸防护屏，配多关节臂；可移至球管与术者之间，减少散射线剂量。", "Ceiling-suspended lead-acrylic shield on an articulated arm, swung between the patient and the operator to cut scattered radiation."),
   (0.9, 0.4, 5),
   [
       B("plastic", 0, 4.97, 0, 0.4, 0.06, 0.3),
       B("chrome", 0, 4.0, 0, 0.08, 1.9, 0.08),
       B("plastic", 0.2, 3.05, 0, 0.5, 0.08, 0.08),
       B("chrome", 0.4, 2.5, 0, 0.05, 1.05, 0.05),
       B("steel", 0.0, 1.98, 0, 0.84, 0.04, 0.04),
       B("sc-lead-acrylic", 0.0, 1.6, 0, 0.8, 0.74, 0.02),
       B("steel", -0.41, 1.6, 0, 0.03, 0.76, 0.03),
       B("steel", 0.41, 1.6, 0, 0.03, 0.76, 0.03),
       B("steel", 0.0, 1.22, 0, 0.84, 0.03, 0.03),
       B("chrome", 0.33, 1.3, 0.05, 0.12, 0.03, 0.03),
   ],
   solid=False, tags=["or", "hybrid", "ceiling", "radiation"])

eq("sc-apron-rack", L("铅衣架", "Lead apron rack"), "imaging",
   L("挂墙式铅衣架，挂有铅围裙、铅颈围（甲状腺防护）和铅眼镜，按尺码分类。", "Wall rack with lead aprons, thyroid collars and lead glasses sorted by size."),
   (1.2, 0.3, 1.9),
   [
       B("steel", 0, 1.65, -0.12, 1.1, 0.06, 0.05),
       B("chrome", -0.4, 1.6, -0.06, 0.03, 0.03, 0.14),
       B("chrome", 0, 1.6, -0.06, 0.03, 0.03, 0.14),
       B("chrome", 0.4, 1.6, -0.06, 0.03, 0.03, 0.14),
       B("navy", -0.4, 1.15, -0.03, 0.36, 0.8, 0.05),
       B("sc-robot-accent", 0, 1.15, -0.03, 0.36, 0.8, 0.05),
       B("purple", 0.4, 1.15, -0.03, 0.36, 0.8, 0.05),
       B("navy", -0.4, 1.5, 0.0, 0.18, 0.08, 0.04),
       B("sc-robot-accent", 0, 1.5, 0.0, 0.18, 0.08, 0.04),
       B("coal", 0.4, 1.78, -0.08, 0.14, 0.04, 0.08),
   ],
   solid=False, interaction="storage", prompt=L("E · 取铅衣", "E · Take a lead apron"), tags=["wall", "or", "hybrid", "radiation"])

# ---------------------------------------------------------------- ceiling systems

def canopy(id, name, size, desc, skirts, tags):
    w = d = size
    half = size / 2
    parts = [
        B("steel", 0, 4.36, 0, 0.9, 1.28, 0.9),
        B("plastic", 0, 3.33, 0, w, 0.6, d),
        B("steel", 0, 3.025, 0, w, 0.05, d),
        B("sc-hepa", 0, 2.995, 0, w - 0.12, 0.02, d - 0.12),
    ]
    n = 4 if size >= 3 else 3
    for k in range(1, n):
        o = -half + 0.06 + k * (w - 0.12) / n
        parts.append(B("steel", o, 2.99, 0, 0.04, 0.025, d - 0.12))
        parts.append(B("steel", 0, 2.99, o, w - 0.12, 0.025, 0.04))
    parts += [
        B("led-green", half - 0.2, 3.1, half - 0.02, 0.1, 0.04, 0.02),
        B("sc-led-white", 0, 2.985, half - 0.25, w - 0.5, 0.012, 0.06),
        B("sc-led-white", 0, 2.985, -half + 0.25, w - 0.5, 0.012, 0.06),
    ]
    if skirts:
        parts += [
            B("glass", 0, 2.7, half - 0.02, w, 0.6, 0.02),
            B("glass", 0, 2.7, -half + 0.02, w, 0.6, 0.02),
            B("glass", half - 0.02, 2.7, 0, 0.02, 0.6, d),
            B("glass", -half + 0.02, 2.7, 0, 0.02, 0.6, d),
            B("steel", 0, 2.4, half - 0.02, w, 0.03, 0.03),
            B("steel", 0, 2.4, -half + 0.02, w, 0.03, 0.03),
            B("steel", half - 0.02, 2.4, 0, 0.03, 0.03, d),
            B("steel", -half + 0.02, 2.4, 0, 0.03, 0.03, d),
        ]
    eq(id, name, "structure", desc, (w, d, 5), parts, solid=False, tags=tags)


canopy("sc-laminar-canopy-xl",
       L("Ⅰ级层流送风天花（3.2 × 3.2 m）", "Class I laminar-flow ceiling (3.2 × 3.2 m)"), 3.2,
       L("手术台正上方的单向流（低紊流置换流）送风天花：末端 HEPA 高效过滤器、均流膜面和周边导流玻璃裙边；3.2 × 3.2 m 送风面覆盖手术台与器械台。对应 GB 50333 Ⅰ级（手术区 ISO 5 级）、DIN 1946-4 Ⅰa 级（TAV）和 HTM 03-01 超净通风（≤ 10 CFU/m³）的设计意图。",
         "Unidirectional (low-turbulence displacement) supply ceiling over the table: terminal HEPA filters, a flow-equalising face and perimeter glass skirts; the 3.2 × 3.2 m supply face covers the table and the instrument tables. Design intent: GB 50333 Class I (ISO 5 at the operating zone), DIN 1946-4 class Ia (TAV) and HTM 03-01 ultra-clean ventilation (≤ 10 CFU/m³)."),
       True, ["or", "ceiling", "hvac", "ultraclean"])

canopy("sc-laminar-canopy",
       L("层流送风天花（2.6 × 2.6 m）", "Laminar-flow supply ceiling (2.6 × 2.6 m)"), 2.6,
       L("手术台上方的单向流送风天花，末端 HEPA 过滤，送风面覆盖手术区；适用于 GB 50333 Ⅱ级洁净手术室与常规通风手术室（ASHRAE 170：手术台上方送风阵列、总换气 ≥ 20 次/h）。",
         "Unidirectional supply ceiling with terminal HEPA filters over the operating zone, for GB 50333 Class II rooms and conventionally ventilated ORs (ASHRAE 170: a primary supply array over the table, ≥ 20 total air changes per hour)."),
       False, ["or", "ceiling", "hvac"])


def pendant(id, name, desc, usage, caps, interaction, prompt, extra, tags, screen="none"):
    parts = [
        B("plastic", 0, 4.97, 0, 0.6, 0.06, 0.6),
        B("chrome", 0, 4.18, 0, 0.14, 1.52, 0.14),
        B("plastic", 0, 3.36, 0, 0.26, 0.14, 0.7),
        B("chrome", 0, 2.85, 0.22, 0.12, 0.92, 0.12),
        B("plastic", 0, 1.6, 0.0, 0.44, 1.32, 0.42),
        B("sc-robot-accent", 0, 2.18, 0.0, 0.45, 0.04, 0.43),
        B("steel", 0, 1.02, 0.12, 0.74, 0.03, 0.54),
        B("steel", 0, 1.62, 0.12, 0.74, 0.03, 0.54),
        B("coal", -0.226, 1.3, -0.05, 0.01, 0.06, 0.1),
        B("coal", -0.226, 1.42, -0.05, 0.01, 0.06, 0.1),
        B("coal", 0.226, 1.3, -0.05, 0.01, 0.06, 0.1),
        B("coal", 0.226, 1.42, -0.05, 0.01, 0.06, 0.1),
        B("led-green", 0, 2.2, 0.215, 0.12, 0.02, 0.01),
    ] + extra
    eq(id, name, "surgery", desc, (0.8, 0.8, 5), parts, usage=usage, caps=caps, interaction=interaction, prompt=prompt,
       tags=tags, screen=screen)


pendant("sc-anaesthesia-pendant", L("麻醉吊塔", "Anaesthesia pendant"),
        L("吊顶式麻醉吊塔：氧气、医用空气、笑气、负压吸引和麻醉废气排放（AGSS）终端，双层设备托架和多路电源插座（含隔离电源），吊臂可旋转升降。",
          "Ceiling-mounted anaesthesia supply pendant: oxygen, medical air, nitrous oxide, vacuum and anaesthetic gas scavenging (AGSS) outlets, two equipment shelves and power sockets (including isolated-power circuits) on a rotating, height-adjustable arm."),
        L("从吊塔取氧气和负压吸引：调节吸引负压并检查吸引瓶，麻醉机接 AGSS 废气排放；设备停放在托架上，地面不留拖线。",
          "Draw oxygen and suction from the pendant: set the vacuum and check the canister, connect the anaesthesia machine to the AGSS scavenging outlet; keep equipment on the shelves and cables off the floor."),
        ["oxygen", "suction"], "device", L("E · 使用吊塔气体终端", "E · Use pendant gas outlets"),
        [
            B("oxygen-green", -0.15, 1.26, 0.215, 0.06, 0.06, 0.02),
            B("sc-gas-air", -0.05, 1.26, 0.215, 0.06, 0.06, 0.02),
            B("sc-gas-n2o", 0.05, 1.26, 0.215, 0.06, 0.06, 0.02),
            B("yellow", 0.15, 1.26, 0.215, 0.06, 0.06, 0.02),
            B("sc-gas-agss", 0.0, 1.38, 0.215, 0.06, 0.06, 0.02),
            B("coal", 0.0, 1.13, 0.215, 0.3, 0.05, 0.02),
            B("lead-glass", 0.27, 0.86, 0.3, 0.12, 0.26, 0.12),
            B("blue", 0.27, 1.0, 0.3, 0.13, 0.03, 0.13),
            B("chrome", 0.27, 1.07, 0.2, 0.04, 0.1, 0.04),
            B("coal", -0.18, 1.74, 0.18, 0.3, 0.2, 0.26),
            B("led-amber", -0.18, 1.74, 0.315, 0.12, 0.03, 0.01),
        ],
        ["or", "ceiling", "pendant", "medical-gas"])

pendant("sc-surgical-pendant", L("外科设备吊塔", "Surgical equipment pendant"),
        L("吊顶式外科设备吊塔：托架上放置高频电刀（电外科工作站）和气腹机，配医用气体、负压和电源/数据接口。",
          "Ceiling-mounted surgical pendant carrying the electrosurgical generator and the insufflator, with medical gas, vacuum, power and data outlets."),
        L("电刀负极板贴于肌肉丰厚、干燥部位，使用前确认功率设置；气腹压力按术式设定并持续观察。",
          "Place the electrosurgical return electrode on dry, well-perfused muscle and check the power settings before use; set the insufflation pressure for the procedure and watch it throughout."),
        [], "none", L("E · 外科设备吊塔", "E · Surgical pendant"),
        [
            B("sc-robot", 0, 1.13, 0.17, 0.62, 0.18, 0.44),
            B("screen-dark", -0.12, 1.13, 0.392, 0.26, 0.12, 0.006, name="screen"),
            B("blue", 0.14, 1.1, 0.392, 0.05, 0.05, 0.006),
            B("yellow", 0.24, 1.1, 0.392, 0.05, 0.05, 0.006),
            B("sc-robot", 0, 1.73, 0.17, 0.62, 0.18, 0.44),
            B("coal", -0.1, 1.73, 0.392, 0.3, 0.1, 0.006),
            B("led-green", 0.18, 1.75, 0.392, 0.06, 0.03, 0.006),
            B("oxygen-green", -0.1, 1.38, 0.215, 0.06, 0.06, 0.02),
            B("yellow", 0.1, 1.38, 0.215, 0.06, 0.06, 0.02),
        ],
        ["or", "ceiling", "pendant"], screen="text")

eq("sc-ceiling-display", L("吊臂式 4K 医用显示器", "Ceiling-boom 4K surgical display"), "surgery",
   L("吊臂悬挂的 55 英寸 4K 医用显示器，可显示腔镜图像、PACS 影像、导航或造影画面（数字化一体化手术室视频路由）。",
     "55-inch 4K surgical display on a ceiling spring arm, routed by the integrated-OR video system: endoscopy, PACS images, navigation or angiography."),
   (1.6, 0.6, 5),
   [
       B("plastic", 0, 4.97, 0, 0.4, 0.06, 0.4),
       B("chrome", 0, 3.78, 0, 0.12, 2.34, 0.12),
       B("plastic", 0, 2.6, 0, 0.18, 0.12, 0.18),
       B("chrome", 0, 2.53, 0.06, 0.08, 0.1, 0.08),
       B("sc-matte-black", 0, 2.1, 0.12, 1.4, 0.82, 0.08),
       B("sc-matte-black", 0, 2.1, 0.162, 1.36, 0.78, 0.006),
       B("screen-dark", 0, 2.1, 0.166, 1.3, 0.72, 0.006, name="screen"),
       B("led-blue", 0.6, 1.72, 0.165, 0.04, 0.02, 0.006),
   ],
   solid=False, screen="pacs", tags=["or", "ceiling", "display", "integrated-or"])

eq("sc-wall-display", L("墙嵌式医用显示屏", "Wall-mounted clinical display"), "computing",
   L("嵌墙安装的 55 英寸医用显示屏，显示 PACS 影像、电子病历和一体化手术室的视频源。", "Flush-mounted 55-inch clinical display for PACS images, the electronic record and integrated-OR video sources."),
   (1.4, 0.12, 2.3),
   [
       B("sc-matte-black", 0, 1.75, -0.035, 1.34, 0.8, 0.05),
       B("screen-dark", 0, 1.75, -0.006, 1.28, 0.72, 0.006, name="screen"),
       B("led-blue", 0.6, 1.38, -0.006, 0.04, 0.015, 0.006),
   ],
   solid=False, screen="pacs", tags=["wall", "or", "display"])

eq("sc-or-control-panel", L("手术室环境控制面板", "OR environment & control panel"), "monitoring",
   L("墙嵌式手术室控制面板：显示室温（设计目标 20–24 °C）、相对湿度、对走廊的压差（正压/负压）、层流运行状态和医用气体报警，并带手术计时、麻醉计时、无影灯与照明控制。",
     "Flush OR control panel: room temperature (design target 20–24 °C), relative humidity, pressure differential to the corridor (positive or negative), laminar-flow status and medical-gas alarms, plus surgical and anaesthesia timers and light controls."),
   (1.0, 0.1, 1.9),
   [
       B("plastic", 0, 1.45, -0.03, 0.94, 0.74, 0.04),
       B("coal", -0.16, 1.5, -0.008, 0.54, 0.4, 0.006),
       B("screen-dark", -0.16, 1.5, -0.004, 0.5, 0.36, 0.006, name="screen"),
       B("black", 0.3, 1.66, -0.008, 0.26, 0.1, 0.006),
       B("led-red", 0.3, 1.66, -0.004, 0.22, 0.06, 0.004),
       B("black", 0.3, 1.52, -0.008, 0.26, 0.1, 0.006),
       B("led-green", 0.3, 1.52, -0.004, 0.22, 0.06, 0.004),
       B("led-green", 0.22, 1.32, -0.006, 0.04, 0.04, 0.006),
       B("led-green", 0.3, 1.32, -0.006, 0.04, 0.04, 0.006),
       B("led-green", 0.38, 1.32, -0.006, 0.04, 0.04, 0.006),
       B("steel", -0.16, 1.18, -0.006, 0.5, 0.08, 0.006),
       B("steel", 0.3, 1.18, -0.006, 0.26, 0.08, 0.006),
   ],
   solid=False, prompt=L("E · 查看环境参数", "E · Read the room parameters"), screen="text", tags=["wall", "or", "hvac"])

eq("sc-pressure-monitor", L("房间压差监测仪", "Room pressure monitor"), "monitoring",
   L("负压/隔离手术室门旁的房间压差监测仪：显示相对相邻房间的压差，压力梯度失效时声光报警。",
     "Room pressure monitor beside the isolation-room door: shows the differential to the adjacent space and alarms when the pressure cascade fails."),
   (0.4, 0.08, 1.8),
   [
       B("plastic", 0, 1.55, -0.025, 0.3, 0.36, 0.03),
       B("screen-dark", 0, 1.6, -0.008, 0.24, 0.14, 0.006, name="screen"),
       B("led-green", -0.06, 1.44, -0.008, 0.05, 0.05, 0.006),
       B("led-red", 0.06, 1.44, -0.008, 0.05, 0.05, 0.006),
   ],
   solid=False, screen="text", tags=["wall", "hvac", "isolation"])

eq("sc-who-checklist", L("WHO 手术安全核查板", "WHO Surgical Safety Checklist board"), "teaching",
   L("世界卫生组织手术安全核查表墙板：麻醉前核查（Sign in）、切皮前暂停核查（Time out）、离室前核查（Sign out）三个阶段。",
     "Wall board with the WHO Surgical Safety Checklist: Sign in before induction, Time out before skin incision and Sign out before the patient leaves the room."),
   (1.2, 0.08, 2.0),
   [
       B("plastic", 0, 1.5, -0.03, 1.12, 0.84, 0.02),
       B("sc-robot-accent", -0.36, 1.86, -0.017, 0.34, 0.07, 0.006),
       B("green", 0, 1.86, -0.017, 0.34, 0.07, 0.006),
       B("purple", 0.36, 1.86, -0.017, 0.34, 0.07, 0.006),
   ] + [B("coal", cx + 0.03, 1.74 - k * 0.09, -0.017, 0.26, 0.014, 0.004) for cx in (-0.36, 0, 0.36) for k in range(6)]
     + [B("led-green", cx - 0.14, 1.74 - k * 0.09, -0.017, 0.03, 0.03, 0.004) for cx in (-0.36, 0, 0.36) for k in range(6)],
   solid=False, prompt=L("E · 手术安全核查", "E · Surgical safety checklist"), tags=["wall", "or", "safety"])

eq("sc-status-board", L("手术排程与状态大屏", "Theatre schedule & status board"), "computing",
   L("手术部控制台的大屏：各手术间当日排程、当前阶段（准备 / 麻醉 / 手术 / 复苏 / 清洁）、预计时间和急诊插台。",
     "Control-desk wall screen: today's list for every OR, the current phase (set-up / anaesthesia / surgery / recovery / cleaning), expected times and emergency add-ons."),
   (2.4, 0.1, 2.4),
   [
       B("sc-matte-black", 0, 1.75, -0.03, 2.3, 1.2, 0.04),
       B("screen-dark", 0, 1.75, -0.006, 2.2, 1.1, 0.006, name="screen"),
   ] + [B(m, 1.0, 2.15 - k * 0.14, -0.006, 0.08, 0.08, 0.006) for k, m in enumerate(["led-green", "led-amber", "led-green", "led-red", "led-green", "led-amber"])],
   solid=False, screen="text", tags=["wall", "control-desk", "display"])

# ---------------------------------------------------------------- anaesthesia

eq("sc-anaesthesia-workstation", L("高级麻醉工作站", "Advanced anaesthesia workstation"), "surgery",
   L("符合 ISO 80601-2-13 的麻醉工作站：电子流量计、双挥发罐、循环回路与二氧化碳吸收罐、具备多种通气模式的麻醉呼吸机、呼气末气体监测和独立监护屏。",
     "Anaesthesia workstation built to ISO 80601-2-13: electronic flowmeters, two vaporisers, a circle system with CO₂ absorber, an anaesthesia ventilator with ICU-grade modes, end-tidal gas monitoring and a separate monitor screen."),
   (1.0, 0.85, 2.05),
   casters(1.0, 0.85, inset=0.08) + [
       B("plastic", 0, 0.47, -0.08, 0.84, 0.74, 0.6),
       B("white", 0, 0.28, 0.23, 0.76, 0.24, 0.02),
       B("white", 0, 0.54, 0.23, 0.76, 0.24, 0.02),
       B("chrome", 0, 0.34, 0.245, 0.26, 0.02, 0.02),
       B("chrome", 0, 0.6, 0.245, 0.26, 0.02, 0.02),
       B("steel", 0, 0.87, -0.03, 0.92, 0.04, 0.74),
       B("plastic", 0, 1.26, -0.2, 0.74, 0.74, 0.36),
       B("coal", -0.15, 1.12, -0.012, 0.34, 0.26, 0.015),
       B("screen-dark", -0.15, 1.12, -0.003, 0.31, 0.22, 0.005),
       B("yellow", 0.12, 1.42, 0.04, 0.11, 0.2, 0.12),
       B("purple", 0.26, 1.42, 0.04, 0.11, 0.2, 0.12),
       B("coal", 0.12, 1.54, 0.04, 0.08, 0.03, 0.08),
       B("coal", 0.26, 1.54, 0.04, 0.08, 0.03, 0.08),
       B("lead-glass", -0.42, 1.1, -0.05, 0.12, 0.22, 0.12),
       B("purple", -0.42, 1.09, -0.05, 0.1, 0.18, 0.1),
       B("clin-hose-blue", -0.41, 0.97, 0.06, 0.06, 0.17, 0.06),
       B("clin-hose-blue", -0.41, 0.91, 0.2, 0.06, 0.06, 0.2),
       B("mattress", -0.33, 0.97, 0.06, 0.06, 0.17, 0.06),
       B("black", -0.37, 0.92, 0.33, 0.15, 0.07, 0.05),
       B("chrome", 0.3, 1.66, -0.2, 0.06, 0.16, 0.06),
       B("plastic", 0.18, 1.86, -0.15, 0.62, 0.36, 0.08),
       B("coal", 0.18, 1.86, -0.106, 0.58, 0.32, 0.008),
       B("screen-dark", 0.18, 1.86, -0.1, 0.55, 0.29, 0.004, name="screen"),
       B("oxygen-green", -0.22, 0.52, -0.4, 0.1, 0.55, 0.04),
       B("blue", 0.22, 0.52, -0.4, 0.1, 0.55, 0.04),
   ],
   usage=L("使用前完成自检与回路检漏，设定新鲜气体流量和挥发罐浓度；诱导插管后选择通气模式，持续监测呼气末二氧化碳、吸入/呼出麻醉气体浓度与气道压力。",
           "Complete the self-test and leak test before use, set fresh gas flows and vaporiser concentration; after induction and intubation choose a ventilation mode and watch end-tidal CO₂, inspired/expired agent and airway pressures."),
   caps=["anesthesia", "airway", "ventilator", "capnography"], interaction="device", prompt=L("E · 使用麻醉工作站", "E · Use the anaesthesia workstation"),
   screen="vitals", tags=["or", "airway", "anaesthesia"])

eq("sc-difficult-airway-trolley", L("困难气道车", "Difficult airway trolley"), "resuscitation",
   L("按困难气道处理流程分层抽屉（A 面罩通气与插管 / B 声门上气道 / C 面罩通气抢救 / D 紧急颈前气道）的推车，顶部配可视喉镜，另有纤维支气管镜、探条和环甲膜切开套件。",
     "Trolley with drawers in difficult-airway-algorithm order (Plan A intubation, B supraglottic airway, C face-mask rescue, D emergency front-of-neck access), a video laryngoscope on top, a flexible scope, bougies and a cricothyroidotomy kit."),
   (0.75, 0.55, 1.6),
   casters(0.75, 0.55) + [
       B("plastic", 0, 0.52, 0, 0.7, 0.84, 0.5),
       B("green", 0, 0.82, 0.252, 0.64, 0.16, 0.01),
       B("yellow", 0, 0.62, 0.252, 0.64, 0.16, 0.01),
       B("orange", 0, 0.42, 0.252, 0.64, 0.16, 0.01),
       B("ambulance-red", 0, 0.22, 0.252, 0.64, 0.16, 0.01),
       B("chrome", 0, 0.82, 0.262, 0.2, 0.02, 0.01),
       B("chrome", 0, 0.62, 0.262, 0.2, 0.02, 0.01),
       B("chrome", 0, 0.42, 0.262, 0.2, 0.02, 0.01),
       B("chrome", 0, 0.22, 0.262, 0.2, 0.02, 0.01),
       B("steel", 0, 0.96, 0, 0.74, 0.04, 0.54),
       B("chrome", -0.25, 1.2, -0.15, 0.03, 0.44, 0.03),
       B("plastic", -0.25, 1.42, -0.12, 0.22, 0.16, 0.04),
       B("screen-dark", -0.25, 1.42, -0.098, 0.19, 0.12, 0.004, name="screen"),
       B("coal", 0.15, 1.04, 0.05, 0.12, 0.12, 0.3),
       B("purple", 0.0, 1.0, 0.1, 0.12, 0.04, 0.16),
   ],
   caps=["airway"], interaction="device", prompt=L("E · 使用困难气道车", "E · Use the difficult airway trolley"), screen="text",
   portable="cart", tags=["or", "airway", "anaesthesia", "resus"])

# ---------------------------------------------------------------- robotic & minimally invasive surgery

eq("sc-robotic-patient-cart", L("手术机器人床旁机械臂系统", "Robotic surgery patient-side cart"), "surgery",
   L("机器人辅助手术系统的床旁机械臂车：立柱与悬吊平台带四条器械臂（3 条器械臂 + 1 条内镜臂），对接穿刺器后由主刀在控制台远程操控。",
     "Patient-side cart of the robotic surgical system: a column and boom carrying four arms (three instrument arms and one endoscope arm), docked to the ports and driven from the surgeon console."),
   (1.2, 1.4, 2.4),
   casters(1.2, 1.4, inset=0.12, size=0.12) + [
       B("sc-robot", 0, 0.24, -0.1, 1.0, 0.3, 1.0),
       B("sc-robot-accent", 0, 0.3, -0.1, 1.01, 0.04, 1.01),
       B("sc-robot", 0, 1.1, -0.3, 0.42, 1.44, 0.42),
       B("led-blue", 0, 1.83, -0.3, 0.44, 0.03, 0.44),
       B("coal", 0, 1.25, -0.085, 0.28, 0.2, 0.01),
       B("screen-dark", 0, 1.25, -0.078, 0.24, 0.16, 0.006, name="screen"),
       B("chrome", 0, 1.05, -0.63, 0.6, 0.04, 0.04),
       B("sc-robot", 0, 1.95, 0.05, 1.12, 0.2, 0.52),
   ] + [p for x in (-0.42, -0.14, 0.14, 0.42) for p in (
       B("sc-robot", x, 1.82, 0.38, 0.12, 0.14, 0.42),
       B("sc-robot", x, 1.48, 0.6, 0.1, 0.56, 0.1),
       B("sc-robot-accent", x, 1.06, 0.6, 0.08, 0.3, 0.08),
       B("chrome", x, 0.76, 0.6, 0.02, 0.3, 0.02),
   )],
   usage=L("由床旁助手对接穿刺器并安装器械，主刀在控制台操作；紧急中转开放手术时按预案快速撤离机械臂。",
           "The bedside assistant docks the ports and loads the instruments while the surgeon operates from the console; rehearse the emergency undocking drill for conversion to open surgery."),
   caps=["surgery"], interaction="device", prompt=L("E · 手术机器人机械臂", "E · Robotic patient cart"), screen="text",
   tags=["or", "robotic", "mis"])

eq("sc-robotic-console", L("手术机器人医生控制台", "Robotic surgeon console"), "surgery",
   L("主刀医生控制台：三维高清立体视窗、主控手柄、脚踏（能量、离合、镜头）和人机工程扶手。", "Surgeon console: 3D HD stereo viewer, master controllers, foot pedals (energy, clutch, camera) and an ergonomic armrest."),
   (1.1, 0.95, 1.65),
   [
       B("plastic", 0, 0.05, 0, 1.04, 0.1, 0.9),
       B("coal", 0, 0.14, 0.24, 0.62, 0.08, 0.32),
       B("blue", -0.18, 0.2, 0.28, 0.12, 0.03, 0.14),
       B("yellow", 0, 0.2, 0.28, 0.12, 0.03, 0.14),
       B("black", 0.18, 0.2, 0.28, 0.12, 0.03, 0.14),
       B("sc-robot", 0, 0.58, -0.18, 1.02, 0.86, 0.56),
       B("sc-robot", 0, 0.86, 0.17, 0.92, 0.08, 0.26),
       B("navy", 0, 0.91, 0.17, 0.88, 0.03, 0.22),
       B("chrome", -0.18, 1.0, 0.24, 0.06, 0.14, 0.06),
       B("chrome", 0.18, 1.0, 0.24, 0.06, 0.14, 0.06),
       B("sc-robot", 0, 1.33, -0.1, 0.84, 0.46, 0.62),
       B("black", 0, 1.33, 0.215, 0.42, 0.12, 0.02),
       B("led-blue", 0, 1.42, 0.215, 0.2, 0.02, 0.01),
       B("sc-robot-accent", 0, 1.5, -0.1, 0.85, 0.04, 0.63),
       B("coal", 0.43, 0.96, 0.28, 0.16, 0.12, 0.02),
       B("screen-dark", 0.43, 0.96, 0.292, 0.14, 0.1, 0.004, name="screen"),
   ],
   prompt=L("E · 医生控制台", "E · Surgeon console"), screen="text", tags=["or", "robotic", "mis"])

eq("sc-robotic-vision-cart", L("机器人视频系统车", "Robotic vision cart"), "surgery",
   L("机器人系统的视频车：三维内镜图像处理、光源、电外科能量平台和触摸显示屏，供台上助手和巡回护士观看。",
     "Vision cart of the robotic system: 3D endoscope image processing, light source, energy platform and a touch display for the bedside team."),
   (0.8, 0.75, 2.15),
   casters(0.8, 0.75) + [
       B("sc-robot", 0, 0.75, -0.05, 0.72, 1.3, 0.6),
       B("coal", 0, 0.5, 0.252, 0.6, 0.16, 0.01),
       B("coal", 0, 0.75, 0.252, 0.6, 0.16, 0.01),
       B("coal", 0, 1.0, 0.252, 0.6, 0.16, 0.01),
       B("led-green", 0.22, 1.0, 0.258, 0.06, 0.03, 0.004),
       B("led-blue", 0.22, 0.75, 0.258, 0.06, 0.03, 0.004),
       B("chrome", 0, 1.6, -0.1, 0.08, 0.4, 0.08),
       B("sc-matte-black", 0, 1.9, 0.0, 0.76, 0.46, 0.06),
       B("screen-dark", 0, 1.9, 0.034, 0.7, 0.4, 0.006, name="screen"),
   ],
   screen="pacs", tags=["or", "robotic", "mis", "display"])

eq("sc-laparoscopy-tower", L("4K/3D 腹腔镜系统", "4K/3D laparoscopy tower"), "surgery",
   L("腹腔镜塔：4K/3D 摄像主机、LED 冷光源、二氧化碳气腹机、影像记录和 32 英寸监视器，配医用隔离变压器。",
     "Laparoscopy tower: 4K/3D camera control unit, LED light source, CO₂ insufflator, image recorder and a 32-inch monitor on a medical isolation transformer."),
   (0.75, 0.7, 2.15),
   casters(0.75, 0.7) + [
       B("plastic", 0, 0.15, 0, 0.7, 0.06, 0.64),
       B("chrome", -0.32, 0.9, -0.28, 0.04, 1.5, 0.04),
       B("chrome", 0.32, 0.9, -0.28, 0.04, 1.5, 0.04),
       B("chrome", -0.32, 0.9, 0.28, 0.04, 1.5, 0.04),
       B("chrome", 0.32, 0.9, 0.28, 0.04, 1.5, 0.04),
       B("steel", 0, 0.42, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 0.52, 0, 0.6, 0.16, 0.5),
       B("steel", 0, 0.72, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 0.82, 0, 0.6, 0.16, 0.5),
       B("led-blue", 0.18, 0.82, 0.255, 0.08, 0.03, 0.01),
       B("steel", 0, 1.02, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 1.12, 0, 0.6, 0.16, 0.5),
       B("oxygen-green", -0.18, 1.12, 0.255, 0.1, 0.06, 0.01),
       B("led-amber", 0.15, 1.12, 0.255, 0.12, 0.04, 0.01),
       B("steel", 0, 1.32, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 1.4, 0, 0.6, 0.12, 0.5),
       B("sc-matte-black", 0, 1.86, 0.02, 0.72, 0.44, 0.06),
       B("screen-dark", 0, 1.86, 0.054, 0.66, 0.38, 0.006, name="screen"),
       B("steel", 0, 1.6, -0.05, 0.12, 0.08, 0.12),
   ],
   usage=L("连接光缆和摄像头，白平衡后入镜；气腹压力按术式和患者情况设定，并留意高压报警。",
           "Connect the light cable and camera, white-balance, then insert the scope; set the insufflation pressure for the procedure and patient, and respond to over-pressure alarms."),
   screen="pacs", portable="cart", tags=["or", "mis", "endoscopy", "display"])

# ---------------------------------------------------------------- cardiac, neuro, ortho

eq("sc-heart-lung-machine", L("体外循环机（人工心肺机）", "Heart-lung machine (cardiopulmonary bypass)"), "therapy",
   L("体外循环机：五个滚压泵头、膜式氧合器、静脉回流储血罐、变温水箱接口、压力/流量/温度监测屏和气泡探测。", "Cardiopulmonary bypass machine: five roller-pump heads, a membrane oxygenator, venous reservoir, heater-cooler connections, pressure/flow/temperature display and bubble detection."),
   (1.3, 0.8, 1.9),
   casters(1.3, 0.8, inset=0.08) + [
       B("plastic", 0, 0.4, 0, 1.22, 0.62, 0.7),
       B("sc-robot-accent", 0, 0.7, 0.352, 1.2, 0.03, 0.01),
       B("steel", 0, 0.74, 0, 1.24, 0.04, 0.74),
   ] + [p for x in (-0.48, -0.24, 0, 0.24, 0.48) for p in (
       B("steel", x, 0.83, 0.05, 0.22, 0.14, 0.22),
       B("lead-glass", x, 0.92, 0.05, 0.2, 0.04, 0.2),
       B("coal", x, 0.83, 0.17, 0.12, 0.05, 0.02),
   )] + [
       B("chrome", -0.5, 1.3, -0.25, 0.05, 1.1, 0.05),
       B("lead-glass", -0.4, 1.18, -0.12, 0.16, 0.24, 0.16),
       B("clin-blood-bag", -0.4, 1.17, -0.12, 0.12, 0.18, 0.12),
       B("lead-glass", -0.4, 1.52, -0.12, 0.18, 0.3, 0.18),
       B("clin-blood-bag", -0.4, 1.47, -0.12, 0.14, 0.16, 0.14),
       B("clin-blood-bag", -0.15, 0.95, 0.15, 0.4, 0.02, 0.02),
       B("clin-hose-blue", 0.15, 0.95, 0.15, 0.4, 0.02, 0.02),
       B("chrome", 0.35, 1.2, -0.2, 0.05, 0.6, 0.05),
       B("plastic", 0.35, 1.6, -0.15, 0.52, 0.34, 0.06),
       B("screen-dark", 0.35, 1.6, -0.117, 0.48, 0.3, 0.006, name="screen"),
   ],
   usage=L("由灌注师管理：预充排气、核对抗凝（ACT）后转机，监测灌注流量、压力、温度和静脉储血罐液面。",
           "Run by the perfusionist: prime and de-air the circuit, confirm anticoagulation (ACT) before going on bypass, and watch flows, pressures, temperatures and the reservoir level."),
   prompt=L("E · 体外循环机", "E · Heart-lung machine"), screen="text", tags=["or", "cardiac", "perfusion"])

eq("sc-cell-salvage", L("术中自体血回收机", "Intraoperative cell salvage"), "therapy",
   L("术中自体血回收机：回收术野出血，离心洗涤后回输浓缩红细胞，用于大出血风险手术（心脏、骨科、产科大出血）。",
     "Cell saver: collects shed blood from the field, centrifuges and washes it, and returns concentrated red cells, for operations with major blood-loss risk (cardiac, orthopaedic, obstetric haemorrhage)."),
   (0.55, 0.6, 1.6),
   casters(0.55, 0.6) + [
       B("plastic", 0, 0.5, 0, 0.5, 0.8, 0.52),
       B("steel", 0, 0.92, 0, 0.5, 0.04, 0.52),
       B("lead-glass", 0, 1.0, 0.08, 0.22, 0.12, 0.22),
       B("chrome", 0, 1.3, -0.2, 0.04, 0.56, 0.04),
       B("clin-blood-bag", -0.08, 1.4, -0.16, 0.14, 0.2, 0.03),
       B("paper", 0.08, 1.4, -0.16, 0.14, 0.2, 0.03),
       B("coal", 0, 0.75, 0.262, 0.3, 0.2, 0.01),
       B("screen-dark", 0, 0.75, 0.268, 0.26, 0.16, 0.004, name="screen"),
   ],
   screen="text", portable="cart", tags=["or", "blood", "cardiac", "obstetric"])

eq("sc-surgical-navigation", L("光学手术导航系统", "Optical surgical navigation system"), "imaging",
   L("光学手术导航：红外立体定位相机追踪器械与患者参考架，将器械位置叠加到术前 CT/MRI 或术中锥形束 CT 上（神经外科、脊柱、关节置换）。",
     "Optical navigation: an infrared stereo camera tracks instruments and the patient reference array and overlays them on pre-operative CT/MRI or intra-operative cone-beam CT (neurosurgery, spine, arthroplasty)."),
   (0.8, 0.8, 2.35),
   casters(0.8, 0.8) + [
       B("plastic", 0, 0.14, 0, 0.7, 0.1, 0.7),
       B("chrome", 0, 1.2, -0.1, 0.07, 2.0, 0.07),
       B("black", 0, 2.24, -0.05, 0.74, 0.1, 0.14),
       B("lead-glass", -0.3, 2.24, 0.025, 0.08, 0.06, 0.01),
       B("lead-glass", 0.3, 2.24, 0.025, 0.08, 0.06, 0.01),
       B("led-red", 0, 2.24, 0.025, 0.06, 0.03, 0.01),
       B("plastic", 0, 1.4, 0.0, 0.62, 0.4, 0.06),
       B("screen-dark", 0, 1.4, 0.034, 0.56, 0.34, 0.006, name="screen"),
       B("plastic", 0, 0.5, -0.05, 0.4, 0.3, 0.3),
   ],
   screen="ct", tags=["or", "neuro", "ortho", "navigation"])

eq("sc-surgical-microscope", L("落地式手术显微镜", "Floor-stand operating microscope"), "surgery",
   L("落地式手术显微镜：平衡臂、电磁锁、双人双目镜筒、荧光造影模块和高清摄像输出，用于神经外科、脊柱和显微外科。",
     "Floor-stand operating microscope: balanced arm with electromagnetic brakes, binocular heads for surgeon and assistant, fluorescence module and HD video output, for neuro, spine and microsurgery."),
   (1.0, 1.0, 2.25),
   casters(1.0, 1.0, inset=0.1) + [
       B("plastic", 0, 0.12, -0.15, 0.9, 0.12, 0.6),
       B("sc-robot", 0, 0.9, -0.3, 0.26, 1.5, 0.26),
       B("sc-robot", 0, 1.75, -0.15, 0.18, 0.18, 0.6),
       B("sc-robot", 0, 1.9, 0.18, 0.16, 0.16, 0.2),
       B("sc-robot", 0, 1.58, 0.3, 0.1, 0.5, 0.1),
       B("coal", 0, 1.3, 0.34, 0.24, 0.22, 0.24),
       B("black", 0, 1.17, 0.34, 0.16, 0.04, 0.16),
       B("black", -0.12, 1.4, 0.43, 0.06, 0.06, 0.12),
       B("black", 0.12, 1.4, 0.43, 0.06, 0.06, 0.12),
       B("chrome", -0.16, 1.28, 0.34, 0.05, 0.03, 0.03),
       B("chrome", 0.16, 1.28, 0.34, 0.05, 0.03, 0.03),
       B("led-blue", 0, 1.2, 0.465, 0.06, 0.02, 0.01),
   ],
   tags=["or", "neuro", "microsurgery"])

# ---------------------------------------------------------------- obstetric & perioperative

eq("sc-infant-warmer", L("新生儿复苏辐射台", "Neonatal resuscitation warmer"), "resuscitation",
   L("新生儿复苏单元：辐射加热器、可倾斜复苏床、空氧混合器与氧流量计、T 组合复苏器、负压吸引、Apgar 计时器和血氧探头，剖宫产手术间必备。",
     "Neonatal resuscitation unit: radiant heater, tilting bed, air–oxygen blender and flowmeter, T-piece resuscitator, suction, Apgar timer and an SpO₂ probe; standard equipment in an obstetric theatre."),
   (0.95, 0.8, 2.05),
   casters(0.95, 0.8) + [
       B("plastic", 0, 0.42, -0.1, 0.84, 0.62, 0.52),
       B("coal", 0, 0.35, 0.162, 0.7, 0.3, 0.01),
       B("plastic", 0, 0.82, 0.05, 0.9, 0.12, 0.62),
       B("mattress", 0, 0.9, 0.05, 0.78, 0.05, 0.5),
       B("glass", 0, 0.98, 0.36, 0.86, 0.12, 0.02),
       B("glass", -0.44, 0.98, 0.05, 0.02, 0.12, 0.6),
       B("glass", 0.44, 0.98, 0.05, 0.02, 0.12, 0.6),
       B("chrome", -0.38, 1.4, -0.3, 0.06, 1.2, 0.06),
       B("plastic", -0.1, 1.94, -0.05, 0.7, 0.12, 0.42),
       B("led-amber", -0.1, 1.875, -0.05, 0.6, 0.012, 0.3),
       B("plastic", 0.28, 1.3, -0.32, 0.36, 0.3, 0.06),
       B("screen-dark", 0.28, 1.32, -0.287, 0.3, 0.2, 0.006, name="screen"),
       B("led-red", 0.28, 1.19, -0.287, 0.12, 0.03, 0.006),
       B("oxygen-green", -0.28, 1.15, -0.27, 0.06, 0.2, 0.06),
       B("lead-glass", 0.4, 0.68, 0.0, 0.1, 0.18, 0.1),
   ],
   usage=L("分娩前预热辐射台并检查氧源、吸引和 T 组合复苏器；新生儿出生后擦干保暖，按新生儿复苏流程评估呼吸与心率，记录 Apgar 评分。",
           "Pre-warm the unit and check oxygen, suction and the T-piece before delivery; dry and warm the baby, assess breathing and heart rate by the newborn life-support algorithm and record Apgar scores."),
   caps=["oxygen", "suction"], interaction="device", prompt=L("E · 新生儿复苏台", "E · Neonatal resuscitation warmer"), screen="text",
   tags=["or", "obstetric", "neonatal", "resus"], portable="cart")

eq("sc-forced-air-warmer", L("充气式保温毯主机", "Forced-air warming unit"), "therapy",
   L("充气式患者保温系统主机，经软管连接保温毯，围术期维持核心体温、预防意外低体温。", "Forced-air patient warming unit feeding a warming blanket by hose, to keep core temperature up and prevent inadvertent perioperative hypothermia."),
   (0.45, 0.45, 1.15),
   casters(0.45, 0.45, inset=0.05, size=0.06) + [
       B("plastic", 0, 0.08, 0, 0.4, 0.04, 0.4),
       B("chrome", 0, 0.5, -0.08, 0.04, 0.8, 0.04),
       B("plastic", 0, 0.92, 0, 0.36, 0.3, 0.32),
       B("screen-dark", 0, 0.98, 0.162, 0.2, 0.08, 0.006, name="screen"),
       B("led-amber", 0.12, 0.88, 0.162, 0.05, 0.03, 0.006),
       B("clin-hose-blue", 0.0, 0.72, 0.15, 0.1, 0.12, 0.1),
   ],
   screen="text", portable="cart", tags=["or", "pacu", "warming"])

eq("sc-warming-cabinet", L("加温柜（毯子与输液）", "Warming cabinet (blankets & fluids)"), "storage",
   L("双温区加温柜：上层加温毯，下层加温冲洗液与输液（按设定温度保存），玻璃门可视。", "Two-zone warming cabinet: blankets above, irrigation and IV fluids below at set temperatures, behind glass doors."),
   (0.7, 0.62, 1.9),
   [
       B("steel", 0, 0.95, -0.02, 0.68, 1.86, 0.56),
       B("glass", 0, 1.38, 0.265, 0.6, 0.78, 0.02),
       B("glass", 0, 0.52, 0.265, 0.6, 0.78, 0.02),
       B("paper", 0, 1.16, 0.0, 0.54, 0.12, 0.42),
       B("paper", 0, 1.3, 0.0, 0.54, 0.12, 0.42),
       B("paper", 0, 1.44, 0.0, 0.54, 0.12, 0.42),
       B("water", -0.15, 0.4, 0.0, 0.18, 0.26, 0.14),
       B("water", 0.0, 0.4, 0.0, 0.18, 0.26, 0.14),
       B("water", 0.15, 0.4, 0.0, 0.18, 0.26, 0.14),
       B("black", 0.18, 1.82, 0.262, 0.2, 0.06, 0.01),
       B("led-amber", 0.18, 1.82, 0.268, 0.16, 0.04, 0.004),
       B("chrome", -0.26, 1.38, 0.28, 0.02, 0.2, 0.02),
       B("chrome", -0.26, 0.52, 0.28, 0.02, 0.2, 0.02),
   ],
   interaction="storage", prompt=L("E · 取加温毯/液体", "E · Take warmed blankets / fluids"), tags=["or", "warming", "storage"])

# ---------------------------------------------------------------- sterile supply

eq("sc-sterile-rack", L("无菌物品存放架", "Sterile storage rack"), "storage",
   L("不锈钢网格存放架：无菌器械包（双层包布）、硬质灭菌盒和一次性无菌物品，距地 ≥ 20 cm、距顶 ≥ 50 cm 存放，先进先出。",
     "Stainless wire rack with wrapped instrument sets, rigid sterilisation containers and single-use sterile supplies, kept off the floor and away from the ceiling, first in, first out."),
   (1.5, 0.6, 2.0),
   [B("chrome", sx * 0.72, 1.0, sz * 0.27, 0.03, 2.0, 0.03) for sx in (-1, 1) for sz in (-1, 1)]
   + [B("chrome", 0, y, 0, 1.46, 0.025, 0.56) for y in (0.3, 0.75, 1.2, 1.65)]
   + [
       B("sc-drape", -0.45, 0.42, 0, 0.42, 0.2, 0.42), B("sc-drape", 0.05, 0.42, 0, 0.42, 0.2, 0.42), B("steel", 0.5, 0.43, 0, 0.36, 0.22, 0.46),
       B("steel", -0.45, 0.88, 0, 0.42, 0.22, 0.46), B("sc-drape", 0.05, 0.86, 0, 0.42, 0.18, 0.42), B("sc-drape-green", 0.5, 0.86, 0, 0.36, 0.18, 0.42),
       B("sc-drape", -0.45, 1.3, 0, 0.42, 0.16, 0.42), B("steel", 0.05, 1.32, 0, 0.42, 0.2, 0.46), B("paper", 0.5, 1.3, 0, 0.36, 0.16, 0.42),
       B("paper", -0.45, 1.74, 0, 0.42, 0.14, 0.42), B("sc-drape", 0.05, 1.75, 0, 0.42, 0.16, 0.42), B("sc-drape-green", 0.5, 1.74, 0, 0.36, 0.14, 0.42),
       B("yellow", 0.5, 0.43, 0.235, 0.08, 0.04, 0.01), B("ambulance-red", -0.45, 0.88, 0.235, 0.08, 0.04, 0.01), B("green", 0.05, 1.32, 0.235, 0.08, 0.04, 0.01),
   ],
   interaction="storage", prompt=L("E · 取无菌物品", "E · Take sterile supplies"), tags=["sterile", "storage", "core", "cssd"])

eq("sc-case-cart", L("手术器械配送车（闭式）", "Closed case cart"), "storage",
   L("闭式不锈钢器械配送车：按手术排程由消毒供应中心备齐一台手术的器械与耗材，经洁净电梯送至无菌核心区；术后污染器械密闭送回去污区。",
     "Closed stainless case cart: CSSD picks the instruments and supplies for one case to the theatre list and sends it up the clean lift to the sterile core; used instruments go back closed to decontamination."),
   (0.95, 0.65, 1.15),
   casters(0.95, 0.65) + [
       B("steel", 0, 0.62, 0, 0.92, 0.98, 0.6),
       B("chrome", 0, 0.62, 0.302, 0.02, 0.92, 0.01),
       B("chrome", -0.1, 0.62, 0.306, 0.02, 0.3, 0.01),
       B("chrome", 0.1, 0.62, 0.306, 0.02, 0.3, 0.01),
       B("paper", 0.3, 0.95, 0.304, 0.16, 0.1, 0.006),
       B("chrome", 0, 1.03, -0.32, 0.7, 0.03, 0.03),
       B("green", -0.3, 0.95, 0.304, 0.08, 0.04, 0.006),
   ],
   interaction="storage", prompt=L("E · 器械配送车", "E · Case cart"), portable="cart", tags=["sterile", "core", "cssd"])

eq("sc-iuss-steriliser", L("快速压力蒸汽灭菌器", "Immediate-use steam steriliser"), "sanitation",
   L("无菌核心区的台式快速压力蒸汽灭菌器，仅用于术中意外污染的单件器械紧急再处理（不替代消毒供应中心的常规灭菌），每锅记录生物/化学监测结果。",
     "Benchtop immediate-use steam steriliser in the sterile core, only for urgent reprocessing of a single dropped instrument during a case (never a substitute for routine CSSD sterilisation); each cycle is logged with its indicators."),
   (0.85, 0.7, 1.6),
   [
       B("steel", 0, 0.42, 0, 0.82, 0.84, 0.64),
       B("chrome", 0, 0.42, 0.322, 0.7, 0.02, 0.01),
       B("plastic", 0, 1.13, -0.02, 0.78, 0.58, 0.62),
       B("steel", -0.12, 1.13, 0.292, 0.42, 0.42, 0.02),
       B("chrome", -0.12, 1.13, 0.306, 0.3, 0.3, 0.01),
       B("coal", 0.25, 1.22, 0.292, 0.2, 0.14, 0.006),
       B("screen-dark", 0.25, 1.22, 0.297, 0.17, 0.11, 0.004, name="screen"),
       B("led-green", 0.22, 1.05, 0.296, 0.04, 0.04, 0.006),
       B("led-amber", 0.3, 1.05, 0.296, 0.04, 0.04, 0.006),
   ],
   screen="text", tags=["sterile", "core"])

eq("sc-steam-steriliser", L("双门脉动真空压力蒸汽灭菌器", "Pass-through pre-vacuum steam steriliser"), "sanitation",
   L("消毒供应中心的双门（穿墙式）脉动真空压力蒸汽灭菌器：包装区装载、无菌物品存放区卸载，门互锁；每锅做 B-D 试验与化学/生物监测并可追溯（ISO 17665）。",
     "CSSD pass-through pre-vacuum steam steriliser: loaded from the packing room, unloaded into sterile storage, doors interlocked; Bowie-Dick test, chemical and biological indicators and full traceability (ISO 17665)."),
   (1.6, 1.6, 2.3),
   [
       B("steel", 0, 1.12, 0, 1.56, 2.2, 1.4),
       B("chrome", -0.12, 1.1, 0.71, 1.0, 1.3, 0.02),
       B("chrome", -0.12, 1.1, -0.71, 1.0, 1.3, 0.02),
       B("coal", 0.58, 1.5, 0.71, 0.28, 0.3, 0.02),
       B("screen-dark", 0.58, 1.5, 0.722, 0.24, 0.26, 0.006, name="screen"),
       B("coal", 0.58, 1.5, -0.71, 0.28, 0.3, 0.02),
       B("led-green", 0.58, 1.25, 0.722, 0.06, 0.04, 0.006),
       B("led-amber", 0.58, 1.25, -0.722, 0.06, 0.04, 0.006),
       B("steel", -0.12, 0.28, 0.76, 1.0, 0.04, 0.08),
       B("steel", -0.12, 0.28, -0.76, 1.0, 0.04, 0.08),
       B("warning-yellow", -0.12, 1.9, 0.712, 0.6, 0.06, 0.01),
   ],
   screen="text", tags=["cssd", "sterile"])

eq("sc-washer-disinfector", L("双门清洗消毒器", "Pass-through washer-disinfector"), "sanitation",
   L("去污区与包装区之间的穿墙式清洗消毒器：器械在去污区装载，经清洗、湿热消毒（A0 值）和干燥后从包装区取出（ISO 15883）。",
     "Pass-through washer-disinfector between decontamination and packing: loaded dirty side, washed, thermally disinfected (A0) and dried, unloaded clean side (ISO 15883)."),
   (1.1, 1.4, 2.1),
   [
       B("steel", 0, 1.03, 0, 1.06, 2.02, 1.2),
       B("glass", 0, 1.0, 0.61, 0.8, 1.0, 0.02),
       B("glass", 0, 1.0, -0.61, 0.8, 1.0, 0.02),
       B("steel", 0, 0.9, 0.0, 0.8, 0.04, 1.0),
       B("steel", 0, 1.2, 0.0, 0.8, 0.04, 1.0),
       B("coal", 0, 1.78, 0.61, 0.5, 0.2, 0.02),
       B("screen-dark", 0, 1.78, 0.622, 0.46, 0.16, 0.006, name="screen"),
       B("coal", 0, 1.78, -0.61, 0.5, 0.2, 0.02),
       B("led-green", 0.4, 1.78, 0.622, 0.05, 0.05, 0.006),
       B("led-amber", 0.4, 1.78, -0.622, 0.05, 0.05, 0.006),
   ],
   screen="text", tags=["cssd"])

eq("sc-inspection-bench", L("器械检查包装台", "Inspection & packing bench"), "sanitation",
   L("器械检查包装台：带光源放大镜检查清洗质量与功能，按器械清单组装、双层包装或装入硬质容器，封口并打印追溯条码。",
     "Inspection and packing bench: illuminated magnifier for cleanliness and function checks, sets assembled to the tray list, double-wrapped or containerised, sealed and labelled with a traceability barcode."),
   (1.8, 0.8, 1.7),
   [
       B("steel", 0, 0.88, 0, 1.78, 0.05, 0.76),
       B("steel", -0.82, 0.43, 0, 0.05, 0.86, 0.7),
       B("steel", 0.82, 0.43, 0, 0.05, 0.86, 0.7),
       B("steel", 0, 0.2, 0, 1.6, 0.03, 0.66),
       B("sc-drape", -0.55, 0.95, 0.05, 0.5, 0.06, 0.5),
       B("steel", 0.05, 0.95, 0.08, 0.4, 0.08, 0.3),
       B("chrome", 0.0, 0.92, 0.0, 0.2, 0.01, 0.04),
       B("chrome", -0.6, 1.25, -0.3, 0.04, 0.7, 0.04),
       B("chrome", -0.45, 1.58, -0.18, 0.3, 0.03, 0.03),
       B("plastic", -0.3, 1.5, -0.06, 0.24, 0.05, 0.24),
       B("lightbox", -0.3, 1.47, -0.06, 0.18, 0.01, 0.18),
       B("coal", 0.6, 0.97, -0.15, 0.3, 0.14, 0.3),
       B("plastic", 0.55, 1.16, -0.3, 0.36, 0.26, 0.04),
       B("screen-dark", 0.55, 1.16, -0.277, 0.32, 0.2, 0.004, name="screen"),
       B("sc-drape", 0.3, 0.35, 0, 0.8, 0.2, 0.2),
   ],
   screen="text", tags=["cssd"])

eq("sc-decon-sink", L("去污清洗槽（含超声清洗）", "Decontamination sink with ultrasonic bath"), "sanitation",
   L("去污区的双槽手工清洗台与超声清洗机，配高压水枪和气枪，用于预处理和复杂器械（管腔器械）的清洗。",
     "Twin-bowl manual decontamination sink with an ultrasonic cleaner, water and air guns, for pre-cleaning and complex (lumened) instruments."),
   (2.0, 0.75, 1.6),
   [
       B("steel", 0, 0.45, 0, 1.96, 0.9, 0.7),
       B("steel", -0.5, 0.92, 0.02, 0.8, 0.06, 0.6),
       B("water", -0.5, 0.9, 0.02, 0.7, 0.03, 0.5),
       B("steel", 0.35, 0.92, 0.02, 0.5, 0.06, 0.6),
       B("water", 0.35, 0.9, 0.02, 0.42, 0.03, 0.5),
       B("plastic", 0.82, 1.0, 0.02, 0.28, 0.2, 0.5),
       B("led-green", 0.82, 1.05, 0.275, 0.06, 0.03, 0.006),
       B("plastic", 0, 1.3, -0.34, 1.96, 0.6, 0.04),
       B("chrome", -0.5, 1.15, -0.25, 0.04, 0.3, 0.14),
       B("chrome", 0.35, 1.15, -0.25, 0.04, 0.3, 0.14),
       B("yellow", -0.8, 1.35, -0.3, 0.06, 0.2, 0.04),
       B("navy", 0.6, 1.35, -0.3, 0.06, 0.2, 0.04),
   ],
   interaction="sink", prompt=L("E · 去污清洗", "E · Decontaminate"), tags=["cssd", "dirty"])

# ---------------------------------------------------------------- scrub, PPE, staff areas

eq("sc-scrub-trough", L("双人外科刷手池", "Twin-station surgical scrub trough"), "sanitation",
   L("双人外科刷手池：感应/膝控水龙头、外科手消毒液和刷手海绵分配器、刷手计时器，水槽深且防溅。",
     "Twin-station scrub trough: sensor/knee-operated taps, surgical hand-rub and scrub-sponge dispensers, a scrub timer and a deep, splash-proof basin."),
   (2.4, 0.7, 1.85),
   [
       B("steel", 0, 0.92, 0.0, 2.36, 0.08, 0.64),
       B("steel", -0.6, 0.78, 0.02, 1.0, 0.22, 0.56),
       B("steel", 0.6, 0.78, 0.02, 1.0, 0.22, 0.56),
       B("water", -0.6, 0.9, 0.02, 0.9, 0.01, 0.46),
       B("water", 0.6, 0.9, 0.02, 0.9, 0.01, 0.46),
       B("steel", -0.6, 0.45, 0.18, 0.3, 0.3, 0.02),
       B("steel", 0.6, 0.45, 0.18, 0.3, 0.3, 0.02),
       B("steel", -1.12, 0.33, -0.2, 0.06, 0.66, 0.06),
       B("steel", 1.12, 0.33, -0.2, 0.06, 0.66, 0.06),
       B("plastic", 0, 1.38, -0.32, 2.4, 0.86, 0.05),
       B("chrome", -0.6, 1.18, -0.2, 0.05, 0.18, 0.2),
       B("chrome", 0.6, 1.18, -0.2, 0.05, 0.18, 0.2),
       B("led-red", -0.6, 1.24, -0.29, 0.03, 0.02, 0.006),
       B("led-red", 0.6, 1.24, -0.29, 0.03, 0.02, 0.006),
       B("plastic", -1.0, 1.4, -0.24, 0.12, 0.2, 0.08),
       B("plastic", 0.0, 1.4, -0.24, 0.12, 0.2, 0.08),
       B("plastic", 1.0, 1.4, -0.24, 0.12, 0.2, 0.08),
       B("black", 0, 1.72, -0.29, 0.34, 0.12, 0.01),
       B("led-red", 0, 1.72, -0.284, 0.28, 0.07, 0.004),
       B("lightbox", 0, 1.78, -0.29, 2.2, 0.05, 0.02),
   ],
   interaction="sink", prompt=L("E · 外科刷手", "E · Surgical scrub"), tags=["or", "scrub", "hand-hygiene"])

eq("sc-ppe-station", L("防护用品穿戴站", "PPE donning station"), "sanitation",
   L("挂墙式防护用品站：一次性手术衣、无菌手套、医用防护口罩（N95/FFP3）、护目镜与面屏、鞋套，配穿戴步骤图与穿衣镜。",
     "Wall PPE station: single-use gowns, sterile gloves, respirators (N95/FFP3), goggles and face shields, overshoes, a donning sequence chart and a mirror."),
   (1.2, 0.3, 2.0),
   [
       B("plastic", 0, 1.3, -0.13, 1.16, 1.2, 0.03),
       B("chrome", 0, 1.0, -0.02, 1.1, 0.02, 0.2),
       B("chrome", 0, 1.4, -0.02, 1.1, 0.02, 0.2),
       B("paper", -0.4, 1.07, -0.02, 0.28, 0.12, 0.18),
       B("scrubs", -0.05, 1.07, -0.02, 0.3, 0.12, 0.18),
       B("white", 0.33, 1.07, -0.02, 0.3, 0.12, 0.18),
       B("sc-drape", -0.4, 1.47, -0.02, 0.28, 0.12, 0.18),
       B("yellow", -0.05, 1.47, -0.02, 0.3, 0.12, 0.18),
       B("lightbox", 0.38, 1.66, -0.11, 0.3, 0.5, 0.01),
       B("paper", -0.25, 1.75, -0.11, 0.5, 0.3, 0.01),
       B("ambulance-red", -0.25, 1.88, -0.105, 0.5, 0.04, 0.004),
   ],
   solid=False, interaction="storage", prompt=L("E · 穿戴防护用品", "E · Put on PPE"), tags=["wall", "ppe", "isolation"])

eq("sc-scrubs-dispenser", L("手术衣自动发放机", "Scrub-suit dispensing machine"), "storage",
   L("刷卡领取的洗手衣自动发放机（按尺码），回收口收集换下的洗手衣，减少更衣室堆放和交叉污染。", "Card-operated scrub-suit dispenser (by size) with a return chute for worn scrubs, cutting clutter and cross-contamination in the changing room."),
   (1.0, 0.8, 2.05),
   [
       B("plastic", 0, 1.02, -0.02, 0.98, 2.02, 0.74),
       B("sc-robot-accent", 0, 1.95, 0.352, 0.96, 0.12, 0.01),
       B("glass", -0.12, 1.25, 0.352, 0.6, 0.9, 0.01),
   ] + [B("scrubs", -0.12, 0.9 + k * 0.17, 0.25, 0.54, 0.1, 0.2) for k in range(5)] + [
       B("coal", 0.35, 1.4, 0.352, 0.2, 0.16, 0.01),
       B("screen-dark", 0.35, 1.4, 0.358, 0.17, 0.12, 0.004, name="screen"),
       B("black", 0.35, 1.15, 0.352, 0.12, 0.06, 0.01),
       B("coal", -0.12, 0.45, 0.352, 0.6, 0.2, 0.01),
       B("steel", 0.35, 0.6, 0.352, 0.2, 0.3, 0.01),
   ],
   interaction="storage", prompt=L("E · 领取洗手衣", "E · Get scrubs"), screen="text", tags=["changing", "staff"])

eq("sc-step-over-bench", L("换鞋跨越凳", "Step-over shoe-change bench"), "furniture",
   L("更衣室中划分外区与内区的跨越凳：坐下脱外出鞋放入外侧鞋柜，转身跨过后换上手术室专用鞋。", "Step-over bench dividing the outer and inner sides of the changing room: sit, put outdoor shoes in the outer rack, swing over and put on theatre shoes."),
   (3.0, 0.5, 0.5),
   [
       B("wood", 0, 0.45, 0, 2.96, 0.06, 0.44),
       B("steel", -1.35, 0.21, 0, 0.06, 0.42, 0.4),
       B("steel", 1.35, 0.21, 0, 0.06, 0.42, 0.4),
       B("steel", 0, 0.12, 0, 2.7, 0.03, 0.4),
       B("black", -0.9, 0.17, 0.08, 0.26, 0.08, 0.14),
       B("navy", -0.3, 0.17, 0.08, 0.26, 0.08, 0.14),
       B("white", 0.4, 0.17, -0.08, 0.26, 0.08, 0.14),
       B("sc-robot-accent", 1.0, 0.17, -0.08, 0.26, 0.08, 0.14),
   ],
   tags=["changing", "staff"])

eq("sc-sluice", L("污物处置池与便器清洗机", "Sluice & bedpan washer-disinfector"), "sanitation",
   L("污物间的冲洗池（污物处置池）和便器清洗消毒机，用于倾倒和处理体液、术后污物。", "Sluice (flushing rim sink) and bedpan washer-disinfector in the soiled utility room, for disposing of body fluids and post-operative waste."),
   (1.6, 0.7, 1.6),
   [
       B("steel", -0.4, 0.45, 0, 0.76, 0.9, 0.66),
       B("steel", -0.4, 0.92, 0.02, 0.6, 0.06, 0.5),
       B("water", -0.4, 0.9, 0.02, 0.5, 0.02, 0.4),
       B("chrome", -0.4, 1.15, -0.25, 0.05, 0.25, 0.12),
       B("plastic", 0.4, 0.75, -0.01, 0.76, 1.5, 0.66),
       B("steel", 0.4, 0.95, 0.33, 0.5, 0.5, 0.01),
       B("coal", 0.4, 1.35, 0.33, 0.3, 0.12, 0.01),
       B("led-green", 0.52, 1.35, 0.336, 0.04, 0.04, 0.004),
   ],
   interaction="sink", prompt=L("E · 污物处置", "E · Use the sluice"), tags=["soiled", "dirty"])

eq("sc-waste-station", L("分类污物收集站", "Segregated waste & linen station"), "sanitation",
   L("分类收集站：感染性医疗废物（黄色）、锐器盒、病理性废物、生活垃圾和污染布类，均为脚踏加盖。", "Segregated collection: infectious clinical waste (yellow), sharps, pathological waste, general waste and soiled linen, all with foot-operated lids."),
   (1.8, 0.6, 1.1),
   [
       B("yellow", -0.66, 0.42, 0, 0.42, 0.84, 0.5),
       B("biohazard", -0.21, 0.42, 0, 0.42, 0.84, 0.5),
       B("coal", 0.24, 0.42, 0, 0.42, 0.84, 0.5),
       B("chrome", 0.68, 0.05, 0, 0.42, 0.06, 0.5),
       B("sc-drape", 0.68, 0.5, 0, 0.4, 0.86, 0.46),
       B("chrome", 0.68, 0.95, 0, 0.42, 0.04, 0.5),
       B("rubber", -0.66, 0.86, 0, 0.44, 0.04, 0.52),
       B("rubber", -0.21, 0.86, 0, 0.44, 0.04, 0.52),
       B("rubber", 0.24, 0.86, 0, 0.44, 0.04, 0.52),
   ],
   tags=["soiled", "waste"])

eq("sc-zone-line", L("限制区地面红线", "Restricted-boundary floor line"), "decor",
   L("地面红线：标示半限制区的边界，越线必须穿戴洗手衣、帽子（及按要求佩戴口罩）。", "Red floor line marking the semi-restricted boundary: beyond it, scrubs and a cap (and a mask where required) are mandatory."),
   (2.4, 0.14, 0.03),
   [B("sc-zone-red", 0, 0.01, 0, 2.4, 0.012, 0.12)],
   solid=False, tags=["floor", "signage", "zoning"])

eq("sc-return-grille", L("下回风口", "Low-level return-air grille"), "structure",
   L("靠近地面的回风/排风口，成对设在房间对角，使送风自上而下流经手术区后排出。", "Return/exhaust grille near the floor, in pairs at opposite corners, so supply air flows down through the operating zone before it leaves."),
   (0.9, 0.08, 0.6),
   [B("steel", 0, 0.32, -0.03, 0.86, 0.38, 0.02)] + [B("coal", 0, 0.18 + k * 0.05, -0.018, 0.8, 0.018, 0.004) for k in range(6)],
   solid=False, tags=["wall", "hvac"])

eq("sc-gas-zone-valve", L("医用气体区域阀箱与报警器", "Medical-gas zone valve box & area alarm"), "structure",
   L("医用气体区域阀箱（氧气、医用空气、笑气、负压、废气排放）与区域报警器：压力异常时声光报警，紧急情况下可关断本区供气。",
     "Medical-gas zone valve box (oxygen, medical air, nitrous oxide, vacuum, scavenging) and area alarm: alarms on abnormal pressure and lets staff isolate the zone in an emergency."),
   (0.95, 0.12, 1.95),
   [
       B("steel", 0, 1.35, -0.04, 0.9, 0.5, 0.04),
       B("glass", 0, 1.35, -0.018, 0.82, 0.42, 0.006),
       B("oxygen-green", -0.3, 1.35, -0.025, 0.08, 0.16, 0.02),
       B("sc-gas-air", -0.15, 1.35, -0.025, 0.08, 0.16, 0.02),
       B("sc-gas-n2o", 0.0, 1.35, -0.025, 0.08, 0.16, 0.02),
       B("yellow", 0.15, 1.35, -0.025, 0.08, 0.16, 0.02),
       B("sc-gas-agss", 0.3, 1.35, -0.025, 0.08, 0.16, 0.02),
       B("plastic", 0, 1.78, -0.04, 0.6, 0.22, 0.04),
   ] + [B("led-green", -0.22 + k * 0.11, 1.78, -0.018, 0.05, 0.05, 0.006) for k in range(5)],
   solid=False, tags=["wall", "medical-gas", "safety"])

# ---------------------------------------------------------------- pathology & plant

eq("sc-cryostat", L("冰冻切片机", "Cryostat (frozen-section microtome)"), "pathology",
   L("术中快速冰冻切片机：在 -20 °C 左右的冷冻箱内切片，快速染色后由病理医师在显微镜下出具术中诊断。",
     "Cryostat for intra-operative frozen sections: tissue is cut in a chamber at about −20 °C, rapidly stained and read under the microscope by the pathologist."),
   (0.8, 0.8, 1.3),
   casters(0.8, 0.8) + [
       B("plastic", 0, 0.55, -0.02, 0.76, 0.98, 0.72),
       B("glass", 0, 1.12, 0.1, 0.6, 0.3, 0.4),
       B("steel", 0, 1.05, 0.0, 0.3, 0.12, 0.2),
       B("chrome", 0.32, 0.95, 0.12, 0.04, 0.04, 0.14),
       B("coal", -0.2, 0.75, 0.345, 0.26, 0.12, 0.01),
       B("screen-dark", -0.2, 0.75, 0.351, 0.22, 0.08, 0.004, name="screen"),
       B("sc-led-white", 0, 1.26, 0.1, 0.4, 0.02, 0.1),
   ],
   caps=["histopathology"], interaction="device", prompt=L("E · 冰冻切片", "E · Frozen section"), screen="text", tags=["pathology", "frozen-section"])

eq("sc-ahu", L("手术部专用空调机组", "Dedicated OR air-handling unit"), "structure",
   L("手术部专用组合式空调机组：新风/回风段、粗中效过滤、表冷与加热盘管、干蒸汽加湿、EC 风机墙和中效末级过滤；送风经风管至各手术间吊顶的末端高效过滤器（HEPA）。",
     "Dedicated OR air-handling unit: fresh/return air section, pre- and bag filters, cooling and heating coils, dry-steam humidifier, EC fan wall and final filters; ducted to the terminal HEPA filters in each OR ceiling."),
   (5.0, 1.8, 4.9),
   [
       B("plastic", 0, 1.3, 0, 4.96, 2.4, 1.76),
       B("steel", 0, 0.08, 0, 4.96, 0.16, 1.76),
   ] + [B("steel", -2.0 + k * 1.0, 1.3, 0.885, 0.04, 2.36, 0.02) for k in range(5)] + [
       B("lead-glass", -1.5, 1.6, 0.89, 0.3, 0.3, 0.01),
       B("lead-glass", 0.5, 1.6, 0.89, 0.3, 0.3, 0.01),
       B("chrome", -1.2, 1.3, 0.9, 0.04, 0.3, 0.02),
       B("chrome", 0.2, 1.3, 0.9, 0.04, 0.3, 0.02),
       B("coal", 1.9, 1.7, 0.885, 0.6, 0.4, 0.02),
       B("screen-dark", 1.9, 1.7, 0.893, 0.52, 0.32, 0.006, name="screen"),
       B("steel", -1.6, 3.65, -0.2, 1.0, 2.5, 0.9),
       B("steel", 1.4, 3.65, -0.2, 1.2, 2.5, 1.0),
       B("warning-yellow", 0, 2.4, 0.885, 4.9, 0.06, 0.02),
   ],
   prompt=L("E · 空调机组", "E · Air-handling unit"), screen="text", tags=["plant", "hvac"])
