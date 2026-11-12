"""IMPF Surgery Hospital: thoracoscopy (video-assisted thoracic surgery, VATS) — docs/THORACOSCOPY.md.

What a thoracoscopic lung resection needs beyond the general theatre, as catalog data: the camera tower and the
displays that show its picture, the instruments that go through the ports, lung isolation at the head of the table,
the aids for the lateral position, the chest drainage unit — and a training station in the simulation centre on which
the whole sequence can be rehearsed. Their rules are world predicates only (interactions.py): the tube's position is
confirmed before the patient is turned and again after; no port before the lung is down; no picture before the
white balance; no energy without smoke evacuation; a drain is placed with its unit primed, and connected before the
lung is re-expanded.

The theatre's devices work on a patient; the training station carries its own steps for what anaesthesia does to a
patient (the lung let down, the lung re-expanded), so it needs no patient and borrows only what stands in the room:
the tower's picture, smoke evacuation, a primed drainage unit, the count.

Imported at the end of catalog.py, after interactions.py (it appends to catalog.EQUIPMENT).
"""
from common import B, L
import catalog
from catalog import eq, casters
from interactions import AT_TABLE, IN_HAND, SCRUB, SCRUBBED, SURGEON, TEAM, instrument, near, op, st, thin

ANAESTHETIST = ["attending", "clinician"]

THORACIC_MATERIALS = [
    # clear tubing and chambers (PVC, silicone), a vacuum mattress (the simulator on the station is the world's own figure)
    {"id": "sc-clear-tube", "color": "#e7efe9", "pattern": "flat", "variance": 0.01, "opacity": 0.5, "roughness": 0.15, "castShadow": False},
    {"id": "sc-vacuum-mat", "color": "#56778f", "pattern": "noise", "variance": 0.04, "roughness": 0.85},
]
catalog.MATERIALS.extend(THORACIC_MATERIALS)
catalog.MAT_IDS.update(m["id"] for m in THORACIC_MATERIALS)

# ------------------------------------------------------------------------------------------------ what gates what
TOWER = "sc-thoracoscopy-tower"
ISOLATION = "sc-lung-isolation-cart"
POSITIONING = "sc-lateral-positioning-set"
DRAINAGE = "sc-chest-drainage-unit"
TRAINER = "sc-vats-trainer"

#: anaesthesia's work on the airway is done at the patient's head (the cart only holds what it takes)
AT_HEAD = [{"patientWithin": 2.5}]
SCOPE_READY = near(TOWER, "balanced", 7)
LUNG_DOWN = near(ISOLATION, "one-lung", 8)
SMOKE = near("sc-smoke-evacuator", "running", 6)
TIMED_OUT = near("sc-who-checklist", ["timed-out", "signed-out"], 7)

# ------------------------------------------------------------------------------------------------ the picture
# The camera's picture on the tower and on the displays: ClinicalCraft's `thoracoscopy` screen — the round field of
# a rigid scope in the chest, a representative picture as a `pacs` screen's slice is (never a patient's own).

eq(TOWER, L("4K 胸腔镜系统", "4K thoracoscopy tower"), "surgery",
   L("胸腔镜塔：4K 摄像主机、LED 冷光源、超声刀/高级双极能量平台、影像记录和 32 英寸监视器；侧面挂镜架和保温防雾杯（温无菌水浸泡镜头，入镜前防雾）。胸腔镜手术靠单肺通气让术侧肺萎陷来获得空间，一般不需要气腹机。",
     "Thoracoscopy tower: 4K camera control unit, LED light source, an ultrasonic / advanced-bipolar energy platform, image recorder and a 32-inch monitor; at its side a scope holder and a warming flask (the tip stands in warm sterile water so that it does not fog). Thoracoscopy gets its working space from one-lung ventilation — the lung on the operated side collapses — so no insufflator is routinely needed."),
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
       B("led-amber", 0.18, 0.82, 0.255, 0.08, 0.03, 0.01),
       B("steel", 0, 1.02, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 1.12, 0, 0.6, 0.16, 0.5),
       B("led-green", -0.18, 1.12, 0.255, 0.1, 0.06, 0.01),
       B("white", 0.15, 1.12, 0.255, 0.06, 0.06, 0.01),
       B("steel", 0, 1.32, 0, 0.68, 0.03, 0.62),
       B("plastic", 0, 1.4, 0, 0.6, 0.12, 0.5),
       B("led-blue", 0.18, 1.4, 0.255, 0.08, 0.03, 0.01),
       B("sc-matte-black", 0, 1.86, 0.02, 0.72, 0.44, 0.06),
       B("screen-dark", 0, 1.86, 0.054, 0.66, 0.38, 0.006, name="screen"),
       B("steel", 0, 1.6, -0.05, 0.12, 0.08, 0.12),
       B("chrome", 0.36, 1.0, 0.12, 0.03, 0.34, 0.03),
       B("steel", 0.375, 0.9, 0.12, 0.07, 0.16, 0.07),
   ],
   usage=L("接好光缆和摄像头，对白纱布做白平衡并调焦，镜头在保温杯里温好再入镜；镜头起雾或沾血时退出擦拭，不在胸腔内盲目操作。",
           "Connect the light cable and the camera, white-balance on a white swab and focus, and warm the tip in the flask before it goes in; when the picture fogs or is smeared, take the scope out and clean it — never work blind in the chest."),
   caps=["endoscopic-camera", "light-source"], interaction="device", prompt=L("E · 胸腔镜系统", "E · Thoracoscopy tower"),
   screen="thoracoscopy", portable="cart", tags=["or", "mis", "thoracic", "endoscopy", "display"],
   # switched off the tower gives no picture; on (self-test passed) its camera and light work (the laparoscopy tower's rule)
   behavior={"initial": "off",
             "states": {"off": st("关闭", "off", supplies=[]),
                        "on": st("开机自检完成", "on (self-test passed)", supplies=["endoscopic-camera", "light-source"]),
                        "balanced": st("已白平衡、调焦，镜头已温", "white-balanced and focused, the scope warm", supplies=["endoscopic-camera", "light-source"])},
             "operations": {
                 "power_on": op("开机自检", "Power on and self-test", ["off"], "on", [], TEAM, 30),
                 "white_balance": op("白平衡、调焦，镜头入保温杯", "White balance, focus, the scope into the warming flask", ["on"], "balanced", [], TEAM, 20),
                 "power_off": op("关机", "Power off", ["on", "balanced"], "off", [], TEAM, 5),
             }})

eq("sc-scope-display", L("吊臂式内镜显示器", "Ceiling-boom endoscopy display"), "surgery",
   L("吊臂悬挂的 55 英寸 4K 医用显示器，由一体化手术室视频系统接到内镜摄像主机：术者和助手各看一台，都正对自己的视线，不必扭头。",
     "55-inch 4K surgical display on a ceiling spring arm, routed by the integrated-OR video system to the endoscopic camera: the surgeon and the assistant each look at one straight ahead, without turning the head."),
   (1.6, 0.6, 5),
   [
       B("plastic", 0, 4.97, 0, 0.4, 0.06, 0.4),
       B("chrome", 0, 3.78, 0, 0.12, 2.34, 0.12),
       B("plastic", 0, 2.6, 0, 0.18, 0.12, 0.18),
       B("chrome", 0, 2.53, 0.06, 0.08, 0.1, 0.08),
       B("sc-matte-black", 0, 2.1, 0.12, 1.4, 0.82, 0.08),
       B("sc-matte-black", 0, 2.1, 0.162, 1.36, 0.78, 0.006),
       B("screen-dark", 0, 2.1, 0.166, 1.3, 0.72, 0.006, name="screen"),
       B("led-green", 0.6, 1.72, 0.165, 0.04, 0.02, 0.006),
   ],
   solid=False, screen="thoracoscopy", tags=["or", "ceiling", "display", "integrated-or", "thoracic"])

# ------------------------------------------------------------------------------------------------ lung isolation
eq(ISOLATION, L("肺隔离用具车（双腔支气管导管与纤维支气管镜）", "Lung-isolation cart (double-lumen tubes & flexible bronchoscope)"), "resuscitation",
   L("麻醉侧的肺隔离用具车：各型号双腔支气管导管（常用左侧管：左主支气管较长，安全范围更大；支气管套囊和它的指示球囊为蓝色，气管套囊的为透明）、支气管封堵器、导管夹和接头；顶部挂纤维支气管镜及其显示屏，用于确认导管位置。",
     "Lung-isolation cart at the anaesthetic end: double-lumen tubes in every size (a left-sided tube is the usual choice: the left main bronchus is longer, the margin of safety greater; the bronchial cuff and its pilot balloon are blue, the tracheal ones clear), bronchial blockers, tube clamps and connectors; on top a flexible bronchoscope with its screen, for confirming where the tube lies."),
   (0.6, 0.5, 1.5),
   casters(0.6, 0.5) + [
       B("plastic", 0, 0.5, 0, 0.56, 0.8, 0.46),
       B("white", 0, 0.76, 0.232, 0.5, 0.16, 0.01),
       B("white", 0, 0.56, 0.232, 0.5, 0.16, 0.01),
       B("white", 0, 0.36, 0.232, 0.5, 0.16, 0.01),
       B("blue", -0.17, 0.76, 0.24, 0.1, 0.05, 0.006),
       B("chrome", 0.05, 0.76, 0.242, 0.18, 0.02, 0.01),
       B("chrome", 0.05, 0.56, 0.242, 0.18, 0.02, 0.01),
       B("chrome", 0.05, 0.36, 0.242, 0.18, 0.02, 0.01),
       B("steel", 0, 0.92, 0, 0.6, 0.04, 0.5),
       B("sc-clear-tube", -0.08, 0.96, 0.08, 0.36, 0.03, 0.04),
       B("blue", 0.07, 0.96, 0.08, 0.03, 0.035, 0.045),
       B("chrome", 0.22, 1.15, -0.16, 0.03, 0.42, 0.03),
       B("plastic", 0.18, 1.4, -0.14, 0.22, 0.16, 0.04),
       B("screen-dark", 0.18, 1.4, -0.118, 0.19, 0.12, 0.004, name="screen"),
       B("black", 0.27, 1.12, -0.1, 0.02, 0.4, 0.02),
       B("coal", 0.27, 1.34, -0.1, 0.04, 0.1, 0.04),
   ],
   usage=L("置管后用纤维支气管镜确认位置：从气管腔看，蓝色支气管套囊充气后刚好可见，不疝出到隆突上。患者体位每次改变后都要再确认——摆好侧卧位后导管可能已经移位。",
           "After placing the tube, confirm its position with the flexible bronchoscope: seen down the tracheal lumen, the blue bronchial cuff, inflated, is just visible and does not herniate over the carina. Confirm it again whenever the patient's position has been changed — the tube may have moved once the patient is on their side."),
   caps=["airway"], interaction="device", prompt=L("E · 肺隔离", "E · Lung isolation"), screen="text", portable="cart",
   tags=["or", "airway", "anaesthesia", "thoracic"],
   behavior={"initial": "two-lung",
             # (names worded for the world's refusal: '… needs the nearby "…" to be {states} (it is {state}).')
             "states": {"two-lung": st("双肺通气", "on both lungs"),
                        "tube-placed": st("已置管（位置未确认）", "intubated (the tube's position not yet confirmed)"),
                        "confirmed": st("导管位置已确认（纤支镜）", "confirmed (the tube's position, with the bronchoscope)"),
                        "one-lung": st("单肺通气（术侧肺已萎陷）", "on one-lung ventilation (the operated lung down)"),
                        "re-expanded": st("已恢复双肺通气（直视下膨肺）", "back on both lungs (re-expanded under vision)")},
             "operations": {
                 "place_tube": op("置入双腔支气管导管", "Place the double-lumen tube", ["two-lung"], "tube-placed", AT_HEAD, ANAESTHETIST, 120),
                 "confirm_position": op("纤支镜确认导管位置（蓝色套囊刚好可见，不疝过隆突）", "Confirm the tube's position with the bronchoscope (the blue cuff just visible, not herniating over the carina)",
                                        ["tube-placed"], "confirmed", AT_HEAD, ANAESTHETIST, 60),
                 # one lung only once the patient is on their side and the tube has been looked at again
                 "isolate": op("再次确认导管位置，夹闭术侧管腔开始单肺通气", "Confirm the tube again, then clamp the operated side: one-lung ventilation",
                               ["confirmed"], "one-lung", [*AT_HEAD, near(POSITIONING, "checked", 8)], ANAESTHETIST, 90),
                 # the lung comes up again with the drain in and on its seal, watched through the scope
                 "re_expand": op("直视下缓慢膨肺，恢复双肺通气", "Re-expand the lung slowly under vision: both lungs again",
                                 ["one-lung"], "re-expanded", [*AT_HEAD, near(DRAINAGE, ["water-seal", "suction"], 8)], ANAESTHETIST, 60),
                 "reset": op("下一台手术：整理用具车", "Next case: restock the cart", ["re-expanded", "tube-placed", "confirmed"], "two-lung", [], ANAESTHETIST + ["nurse"], 30),
             }})

# ------------------------------------------------------------------------------------------------ the lateral position
eq(POSITIONING, L("侧卧位体位用具车", "Lateral-positioning aids trolley"), "surgery",
   L("侧卧位用具：真空塑形垫（抽气后贴合躯干固定）、腋下垫（放在腋窝下方的胸壁下，保护臂丛和腋血管）、上臂托架、头圈、两膝之间的软枕、髋部固定带和各受压点的凝胶垫。",
     "Aids for the lateral position: a vacuum mattress (moulded round the trunk, then evacuated), the axillary roll (under the chest wall below the armpit, to protect the brachial plexus and the axillary vessels), a support for the upper arm, a head ring, a pillow for between the knees, a strap across the hip and gel pads for every pressure point."),
   (0.9, 0.55, 1.15),
   casters(0.9, 0.55) + [
       B("chrome", -0.41, 0.52, -0.235, 0.03, 0.88, 0.03),
       B("chrome", 0.41, 0.52, -0.235, 0.03, 0.88, 0.03),
       B("chrome", -0.41, 0.52, 0.235, 0.03, 0.88, 0.03),
       B("chrome", 0.41, 0.52, 0.235, 0.03, 0.88, 0.03),
       B("steel", 0, 0.2, 0, 0.84, 0.03, 0.5),
       B("steel", 0, 0.72, 0, 0.86, 0.03, 0.52),
       B("sc-vacuum-mat", 0, 0.36, 0, 0.74, 0.28, 0.4),
       B("coal", -0.2, 0.36, 0.204, 0.04, 0.29, 0.008),
       B("coal", 0.2, 0.36, 0.204, 0.04, 0.29, 0.008),
       B("white", -0.2, 0.79, 0.1, 0.38, 0.1, 0.26),
       B("teal", -0.24, 0.775, -0.16, 0.22, 0.07, 0.18),
       B("sc-vacuum-mat", 0.2, 0.795, -0.14, 0.36, 0.11, 0.12),
       B("navy", 0.2, 0.79, 0.1, 0.38, 0.06, 0.15),
       B("chrome", 0.36, 0.93, 0.1, 0.03, 0.36, 0.03),
   ],
   usage=L("导管位置确认后再翻身，多人协同、麻醉医生护住头颈和导管：术侧向上，腋下垫到位，双臂向前、外展不超过 90°（上臂放托架），颈部居中，下腿屈曲、两膝之间加垫，髋部固定。折床让肋间隙张开；最后核对颈部居中、眼耳不受压、各受压点有垫、管线通畅。",
           "Turn only after the tube's position is confirmed, with enough hands and the anaesthetist holding the head, neck and tube: operated side up, the axillary roll in place, both arms forward and abducted no more than 90° (the upper one on its support), the neck neutral, the lower leg flexed with padding between the knees, the hip secured. Flex the table to widen the intercostal spaces; then check — the neck in line, eyes and ears free, every pressure point padded, lines and tube running free."),
   interaction="device", prompt=L("E · 摆放侧卧位", "E · Lateral positioning"), portable="cart", tags=["or", "positioning", "thoracic"],
   behavior={"initial": "stowed",
             "states": {"stowed": st("未使用（患者仰卧）", "stowed (patient supine)"),
                        "lateral": st("已侧卧（术侧向上，腋下垫、托臂架、真空垫就位）", "turned (operated side up; axillary roll, arm support and vacuum mattress in place)"),
                        "flexed": st("已折床（肋间隙张开）", "flexed (the intercostal spaces open)"),
                        "checked": st("体位已核对（颈部居中，受压点有垫，管线通畅）", "checked (neck in line, pressure points padded, lines and tube free)")},
             "operations": {
                 "turn": op("翻身摆侧卧位", "Turn the patient to the lateral position",
                            ["stowed"], "lateral", [{"patientWithin": 2}, near(ISOLATION, ["confirmed", "one-lung"], 8)], TEAM, 300),
                 "flex_table": op("折床，张开肋间隙", "Flex the table to open the intercostal spaces", ["lateral"], "flexed", [{"patientWithin": 2}], TEAM, 60),
                 "check_position": op("核对体位：颈部、眼耳、受压点、管线", "Check the position: neck, eyes and ears, pressure points, lines", ["flexed"], "checked", [{"patientWithin": 2}], TEAM, 60),
                 "return_supine": op("术毕放平手术床，撤除用具，转回仰卧位", "At the end: level the table, remove the aids, turn back supine", ["lateral", "flexed", "checked"], "stowed", [], TEAM, 180),
             }})

# ------------------------------------------------------------------------------------------------ chest drainage
eq(DRAINAGE, L("胸腔闭式引流装置（三腔，水封）", "Chest drainage unit (three chambers, water seal)"), "therapy",
   L("一次性三腔胸腔引流装置：带刻度的集液腔、水封腔（注水到刻度线，一般为 2 cm：气体只出不进，水柱随呼吸波动，持续冒泡提示漏气）和负压调节；带挂钩和落地支架，始终放在胸腔水平以下。",
     "Single-use three-chamber chest drainage unit: a graduated collection chamber, the water-seal chamber (filled to its line, 2 cm in most units: air leaves and cannot return, the column swings with breathing, and steady bubbling means an air leak) and a suction regulator; with hangers and a floor stand, always kept below the level of the chest."),
   (0.36, 0.25, 0.62),
   [
       B("plastic", 0, 0.04, 0, 0.34, 0.08, 0.24),
       B("white", 0, 0.3, 0, 0.3, 0.38, 0.09),
       B("sc-clear-tube", -0.07, 0.29, 0.047, 0.13, 0.32, 0.006),
       B("sc-clear-tube", 0.045, 0.34, 0.047, 0.05, 0.16, 0.006),
       B("blue", 0.045, 0.2, 0.047, 0.05, 0.1, 0.006),
       B("orange", 0.115, 0.38, 0.05, 0.05, 0.05, 0.012),
       B("white", 0, 0.52, 0, 0.14, 0.04, 0.03),
       B("chrome", -0.1, 0.5, -0.03, 0.02, 0.06, 0.02),
       B("chrome", 0.1, 0.5, -0.03, 0.02, 0.06, 0.02),
       B("sc-clear-tube", -0.12, 0.55, 0.02, 0.02, 0.12, 0.02),
   ],
   usage=L("先向水封腔注水到刻度线（一般为 2 cm），再接胸管；装置低于胸腔、保持直立，管路不打折、不下垂成圈。观察：引流量与性状、水柱波动、有无冒泡（漏气）。是否加负压按医嘱：ERAS 学会与欧洲胸外科医师学会（ESTS）的肺手术加速康复指南建议不常规加外部负压吸引，并推荐使用数字化引流系统。",
           "Fill the water-seal chamber to its line first (2 cm in most units), then connect the chest tube; keep the unit upright and below the chest, the tubing free of kinks and dependent loops. Watch the volume and character of the drainage, the swing of the water column, and bubbling (an air leak). Suction only as prescribed: the ERAS Society / ESTS guideline for lung surgery advises against routine external suction and recommends digital drainage systems."),
   interaction="device", solid=False, prompt=L("E · 胸腔引流装置", "E · Chest drainage unit"), tags=["or", "thoracic", "drain", "single-use"],
   behavior={"initial": "sealed",
             "states": {"sealed": st("未开封", "sealed (in its sterile pack)"),
                        "primed": st("已注水封（水封腔注水到刻度线）", "primed (water seal filled to its line)"),
                        "water-seal": st("水封引流中（已接胸管，水柱随呼吸波动）", "on water seal (connected; the column swings with breathing)"),
                        "suction": st("负压吸引中（已接胸管，按医嘱）", "on suction (connected; as prescribed)"),
                        "used": st("已使用（待处置）", "used (for disposal)", False)},
             "operations": {
                 "prime": op("开包，水封腔注水到刻度线（一般为 2 cm）", "Open the pack and fill the water seal to its line (2 cm in most units)", ["sealed"], "primed", [], TEAM, 60),
                 "connect": op("接胸管，装置置于胸腔水平以下", "Connect the chest tube, the unit below the level of the chest", ["primed"], "water-seal",
                               [near("sc-chest-tube", "placed", 4)], TEAM, 30),
                 "apply_suction": op("接负压吸引（按医嘱）", "Apply suction (as prescribed)", ["water-seal"], "suction", [], TEAM, 15),
                 "to_water_seal": op("停负压，改水封引流", "Stop suction: back to water seal", ["suction"], "water-seal", [], TEAM, 10),
                 "dispose": op("拔管或更换后：按医疗废物处置", "After the drain is out or the unit changed: dispose of it as clinical waste", ["water-seal", "suction", "primed"], "used", [], TEAM, 30),
             }})

# ------------------------------------------------------------------------------------------------ instruments
instrument(
    "sc-thoracoscope", L("30° 胸腔镜（10 mm 硬镜）", "30° thoracoscope (10 mm rigid telescope)"),
    L("10 mm、30° 斜视硬质胸腔镜，接 4K 摄像头和导光束；斜视镜转动导光束接口就能绕过肺和器械看到肺门前后与胸顶、膈面。UDI 直接标记，可高压蒸汽或低温等离子灭菌（按厂家说明）。",
      "10 mm rigid thoracoscope with a 30° oblique view, coupled to the 4K camera head and the light cable; turning the light post swings the view round the lung and the instruments — in front of and behind the hilum, up to the apex, down onto the diaphragm. UDI direct-marked; steam or low-temperature plasma sterilisation as its maker allows."),
    L("入镜前白平衡、调焦并温好镜头；由扶镜手持镜，保持地平线水平、术野居中。", "White-balance, focus and warm the tip before it goes in; the camera holder keeps the horizon level and the working point in the middle of the picture."),
    (0.48, 0.06, 0.04),
    [thin("chrome", 0.07, 0.018, 0, 0.34, 0.012, 0.012), thin("steel", -0.12, 0.018, 0, 0.05, 0.03, 0.03),
     thin("coal", -0.19, 0.025, 0, 0.1, 0.05, 0.045), thin("steel", -0.1, 0.018, 0.03, 0.014, 0.014, 0.035)],
    {"insert": op("入镜探查", "Insert the scope and look round", ["sterile", "in-use"], "in-use",
                  [IN_HAND, *SCRUBBED, AT_TABLE, SCOPE_READY], SCRUB, 30)})

instrument(
    "sc-thoracoport", L("胸腔穿刺套管（10.5 mm，钝头）", "Thoracic port (10.5 mm, blunt)"),
    L("胸腔镜用短套管与钝头内芯：胸壁薄、不需要密封气体，所以套管短而无阀；用于观察孔，镜头经它进出不沾血。",
      "Short cannula with a blunt obturator for thoracoscopy: the chest wall is thin and no gas has to be held in, so the port is short and has no valve; it lines the camera port so that the scope goes in and out clean."),
    L("切口沿下位肋骨上缘（肋间血管神经走在上位肋骨下缘的肋沟里）；先用手指探查有无粘连，再置入套管。其余操作孔在镜下直视置入。",
      "Cut down onto the upper border of the lower rib (the intercostal vessels and nerve run in the groove under the rib above); sweep a finger inside for adhesions before the port goes in. Every further port is placed under vision."),
    (0.13, 0.045, 0.045),
    [thin("white", -0.02, 0.022, 0, 0.07, 0.03, 0.03), thin("steel", 0.04, 0.022, 0, 0.05, 0.018, 0.018), thin("blue", -0.055, 0.022, 0, 0.02, 0.04, 0.04)],
    {"place": op("置入观察孔套管", "Place the camera port", ["sterile", "in-use"], "in-use",
                 [IN_HAND, *SCRUBBED, AT_TABLE, TIMED_OUT, LUNG_DOWN], SURGEON, 60)})

instrument(
    "sc-lung-forceps", L("腔镜肺钳（卵圆钳）", "Thoracoscopic lung grasping forceps (ring forceps)"),
    L("长柄卵圆形开窗钳口的无损伤肺钳，双关节设计可在小切口内张开；轻夹肺组织牵拉显露，也可夹持纱布球或“花生米”剥离子做钝性分离。ISO 7153-1 不锈钢，UDI 直接标记。",
      "Long atraumatic lung forceps with oval fenestrated jaws and a double joint that opens inside a small incision; they hold the lung gently for exposure, and carry a swab or a peanut dissector for blunt dissection. ISO 7153-1 stainless steel, UDI direct-marked."),
    None, (0.3, 0.05, 0.02),
    [thin("chrome", 0.03, 0.008, -0.005, 0.2, 0.008, 0.008), thin("chrome", 0.03, 0.008, 0.005, 0.2, 0.008, 0.008),
     thin("steel", -0.115, 0.01, 0, 0.05, 0.012, 0.06), thin("chrome", 0.135, 0.008, 0, 0.03, 0.008, 0.022)],
    {"retract": op("轻夹肺叶牵拉显露", "Hold the lung gently for exposure", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SCRUB, 10)})

instrument(
    "sc-endo-dissector", L("腔镜直角分离钳", "Thoracoscopic right-angle dissector"),
    L("长柄直角分离钳：分离肺门血管与支气管后方，穿过后带出血管牵引带（硅胶带）环绕结构，为切割缝合器开出通道。ISO 7151 关节器械，UDI 直接标记。",
      "Long right-angle dissecting forceps: they open the plane behind a hilar vessel or the bronchus and draw a vessel loop (a silicone sling) round it, making the tunnel the stapler will pass through. An articulated instrument to ISO 7151, UDI direct-marked."),
    None, (0.34, 0.055, 0.03),
    [thin("chrome", 0.03, 0.008, -0.005, 0.24, 0.008, 0.008), thin("chrome", 0.03, 0.008, 0.005, 0.24, 0.008, 0.008),
     thin("steel", -0.135, 0.01, 0, 0.05, 0.012, 0.06), thin("chrome", 0.16, 0.012, 0.012, 0.012, 0.012, 0.03)],
    {"dissect": op("分离肺门结构并套带", "Dissect a hilar structure and pass a loop round it", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 60)})

instrument(
    "sc-clip-applier", L("腔镜施夹钳（结扎夹）", "Endoscopic clip applier (ligating clips)"),
    L("腔镜施夹钳，施放带锁扣的高分子结扎夹或钛夹：用于细小的血管分支；夹子要完全跨过血管、锁扣闭合，近端留足够的残端。",
      "Endoscopic applier for locking polymer or titanium ligating clips: for small vessel branches — the clip right across the vessel, its lock closed, and enough of a stump left on the side that stays."),
    None, (0.42, 0.08, 0.03),
    [thin("chrome", 0.06, 0.01, 0, 0.3, 0.01, 0.01), thin("sc-matte-black", -0.14, 0.012, 0, 0.1, 0.02, 0.07),
     thin("gold", 0.2, 0.01, 0, 0.02, 0.012, 0.014)],
    {"apply_clip": op("夹闭血管分支", "Clip a vessel branch", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 15)})

eq("sc-ultrasonic-shears", L("超声刀（36 cm）", "Ultrasonic shears (36 cm)"), "surgery",
   L("一次性超声切割止血刀头，接胸腔镜塔上的能量平台：刀头高频振动同时切割和凝闭小血管，用于松解粘连、打开纵隔胸膜和下肺韧带、清扫淋巴结。工作刀头很热，离开血管壁和支气管膜部使用，烟雾经排烟系统排出。",
     "Single-use ultrasonic shears on the tower's energy platform: the active blade vibrates, cutting and sealing small vessels at once — for freeing adhesions, opening the mediastinal pleura and the pulmonary ligament, and taking lymph nodes. The active blade is hot: keep it off vessel walls and the membranous bronchus, and evacuate the plume."),
   (0.5, 0.14, 0.04),
   [thin("chrome", 0.08, 0.016, 0, 0.32, 0.01, 0.01), thin("white", -0.15, 0.018, 0, 0.14, 0.034, 0.05),
    thin("white", -0.16, 0.018, -0.055, 0.05, 0.03, 0.06), thin("blue", -0.1, 0.018, 0.03, 0.03, 0.03, 0.02),
    thin("steel", 0.24, 0.016, 0, 0.02, 0.008, 0.012)],
   usage=L("烟雾排除器运行、能量平台开机后才能激发（AORN：所有手术烟雾都应排出并过滤）。",
           "Activates only with the smoke evacuator running and the energy platform on (AORN: evacuate and filter all surgical smoke)."),
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 超声刀", "E · Ultrasonic shears"),
   tags=["or", "instrument", "single-use", "energy", "thoracic"],
   behavior={"initial": "sterile", "states": {"sterile": st("无菌", "sterile"), "in-use": st("使用中", "in use"), "discarded": st("已丢弃", "discarded", False)},
             "operations": {
                 "activate": op("切割 / 凝闭", "Cut / seal", ["sterile", "in-use"], "in-use",
                                [IN_HAND, *SCRUBBED, AT_TABLE, near(TOWER, ["on", "balanced"], 7), SMOKE], SURGEON, 20),
                 "discard": op("用毕丢弃", "Discard after use", ["in-use"], "discarded", [IN_HAND], SCRUB),
             }})

eq("sc-endo-stapler", L("腔镜直线切割缝合器", "Endoscopic linear cutter-stapler"), "surgery",
   L("一次性腔镜直线切割缝合器：钉砧与钉仓夹闭组织后击发，两侧各打数排缝钉、中间切开。钉仓按组织厚度选择——肺血管用薄组织（血管）钉仓，支气管和肺实质用更厚的钉仓（各厂家的颜色标识不同，按说明书选择）；钳口上有刻度线，组织不得超过。",
     "Single-use endoscopic linear cutter-stapler: anvil and cartridge close on the tissue and, fired, lay rows of staples on each side and cut between them. The reload is chosen for the thickness of the tissue — a thin-tissue (vascular) reload for the pulmonary vessels, thicker ones for the bronchus and the lung itself (makers code them in different colours: follow the instructions for use); the tissue must not pass the mark on the jaws."),
   (0.52, 0.13, 0.045),
   [thin("chrome", 0.1, 0.02, 0, 0.26, 0.014, 0.014), thin("steel", 0.265, 0.02, 0, 0.07, 0.016, 0.014),
    thin("purple", 0.27, 0.011, 0, 0.06, 0.008, 0.012), thin("white", -0.12, 0.022, 0, 0.18, 0.04, 0.05),
    thin("white", -0.15, 0.02, -0.055, 0.06, 0.036, 0.07), thin("coal", -0.09, 0.02, -0.04, 0.04, 0.03, 0.04)],
   usage=L("击发前：钳口内只有要切断的结构，尖端完全穿出，周围的血管、神经和导管不在钳口里。夹闭支气管后先请麻醉医生膨肺，确认余肺能通气，再击发。",
           "Before firing: only the structure to be divided lies in the jaws, the tip is clear beyond it, and no neighbouring vessel, nerve or tube is caught. On the bronchus, close the jaws and have the anaesthetist inflate the lung first — the lobes that stay must ventilate — then fire."),
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 切割缝合器", "E · Stapler"),
   tags=["or", "instrument", "single-use", "stapler", "thoracic"],
   behavior={"initial": "sterile",
             "states": {"sterile": st("无菌，未装钉仓", "sterile, no reload in"), "loaded": st("已装钉仓", "reload in"),
                        "fired": st("已击发（换钉仓可再用）", "fired (takes a fresh reload)"), "discarded": st("已丢弃", "discarded", False)},
             "operations": {
                 "load": op("装钉仓（按组织厚度选择）", "Load a reload (chosen for the tissue's thickness)", ["sterile", "fired"], "loaded", [IN_HAND, *SCRUBBED], SCRUB, 20),
                 "fire": op("夹闭、核对钳口内容后击发", "Close, check what is in the jaws, fire", ["loaded"], "fired", [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 30),
                 "discard": op("用毕丢弃", "Discard after use", ["fired", "loaded"], "discarded", [IN_HAND], SCRUB),
             }})

eq("sc-specimen-bag", L("腔镜标本取出袋", "Endoscopic specimen retrieval bag"), "surgery",
   L("一次性标本袋：切下的肺叶或肺组织在胸腔内装袋，收口后经操作口取出，标本不接触切口，避免肿瘤细胞污染切口。",
     "Single-use specimen bag: the resected lobe or wedge is bagged inside the chest and, the mouth drawn shut, brought out through the utility incision without touching the wound — so that no tumour cells are left in it."),
   (0.18, 0.1, 0.02),
   [thin("sc-clear-tube", 0.01, 0.008, 0, 0.15, 0.012, 0.09), thin("blue", -0.075, 0.009, 0, 0.02, 0.014, 0.05)],
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 标本袋", "E · Specimen bag"),
   tags=["or", "instrument", "single-use", "thoracic"],
   behavior={"initial": "sterile", "states": {"sterile": st("无菌", "sterile"), "used": st("已装标本取出", "used: specimen out", False)},
             "operations": {
                 "retrieve": op("胸腔内装袋，经操作口取出标本", "Bag the specimen inside the chest and bring it out through the utility incision", ["sterile"], "used",
                                [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 60),
             }})

eq("sc-chest-tube", L("胸腔引流管（28 Fr）", "Chest tube (28 Fr)"), "surgery",
   L("一次性透明胸腔引流管，带侧孔和 X 线显影线；术毕经观察孔置入一根（指南建议一根而不是两根）、缝线固定，接水封引流装置。",
     "Single-use clear chest tube with side holes and a radiopaque line; at the end of the operation one tube (the guideline advises one, not two) goes in through the camera port, is stitched to the skin and connected to the water-seal drainage unit."),
   (0.45, 0.03, 0.02),
   [thin("sc-clear-tube", 0, 0.008, 0, 0.44, 0.012, 0.012), thin("blue", 0.05, 0.015, 0, 0.3, 0.003, 0.003), thin("white", -0.205, 0.008, 0, 0.03, 0.016, 0.016)],
   usage=L("引流装置先注好水封再置管；镜下确认管尖位置、所有侧孔都在胸腔内，然后固定并接引流装置。",
           "Prime the drainage unit before the tube goes in; confirm through the scope where the tip lies and that every side hole is inside the chest, then secure it and connect the unit."),
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 胸管", "E · Chest tube"),
   tags=["or", "instrument", "single-use", "drain", "thoracic"],
   behavior={"initial": "sterile", "states": {"sterile": st("无菌", "sterile"), "placed": st("已置入并固定", "placed and secured")},
             "operations": {
                 "place": op("经观察孔置入胸管，镜下确认位置后固定", "Place the tube through the camera port, confirm it under vision, secure it",
                             ["sterile"], "placed", [IN_HAND, *SCRUBBED, AT_TABLE, near(DRAINAGE, ["primed", "water-seal", "suction"], 5)], SURGEON, 90),
             }})

# ------------------------------------------------------------------------------------------------ the simulator
HOLDING = lambda type_id: {"actorHolding": type_id}  # noqa: E731


def step(zh, en, frm, to, requires=(), seconds=60):
    return op(zh, en, [frm], to, requires, TEAM, seconds)


# The body on the station's table is the world's own figure (ClinicalCraft docs/FACILITIES.md "A body drawn with
# equipment"), not a part of the model: on its right side, the left side up, asleep, over a table flexed 9° each
# way — as the station is found: under a blanket to the waist, ventilated on both lungs (each step's look changes
# that: TRAINER_LOOKS). `x`, `z`: the middle of the table where it breaks (under the chest); `y`: the top of the
# mattress there. tools/figure-fit.mts measures this body (draped, as it is operated on) for the model built round it.
TRAINER_BODY = {"posture": "lateral", "sideUp": "left", "cover": "blanket", "breathing": "both", "flex": 9, "asleep": True,
                "x": -0.27, "z": -0.13, "y": 0.93, "rot": 90,
                "appearance": {"skin": "#d9b596", "hair": "#2b2420", "hairStyle": "short", "build": "average", "presentation": "neutral"}}

# What is drawn of the station at each step (ClinicalCraft docs/FACILITIES.md "A look for each state"): the layers of
# its model that show (tools/blender/thoracic_models.py builds them), the picture on its monitor, and what the step
# changes of the simulator — under a blanket or draped, ventilated on both lungs or on the one underneath. The look
# follows the station's state, whoever moved it on: the learner at the station, a colleague, an agent — each through
# the same operation. docs/THORACOSCOPY.md "The station follows the operation" shows it step by step.
TRAINER_LAYERS = {
    "lines": "the anterior, mid- and posterior axillary lines marked on the skin",
    "site-camera": "the camera port's site marked (1 cm)",
    "site-working": "the utility incision's and the third port's sites marked (5 cm, 1.5 cm)",
    "camera-port": "the camera port in its incision",
    "scope": "the 30° scope standing in the camera port on its holder, its cables",
    "working-ports": "the utility incision with its wound protector, the third port",
    "retractor": "a lung grasper through the third port, holding the lung",
    "mayo": "an instrument tray over the draped legs, a bowl on it",
    "specimen": "the lobe in its bag in the bowl",
    "chest-tube": "the chest tube through the camera port's incision, its tubing down to the drainage unit",
    "scope-utility": "the scope watching from the utility incision while the drain goes in",
    "dressings": "a dressing over each wound",
}
ONE_LUNG = {"cover": "drapes", "breathing": "one-lung"}       # draped, the lung on the operated side down
TWO_LUNGS = {"cover": "drapes", "breathing": "both"}          # draped, the lung up again
MARKED = ["lines", "site-camera", "site-working"]
IN_THE_CHEST = ["lines", "camera-port", "scope", "working-ports", "mayo"]


def look(layers, screen="none", manikin=None):
    """A state's look: the layers shown (every other layer of the model is hidden), the monitor's picture
    (`thoracoscopy` while the scope is in, else dark), what changes of the simulator."""
    unknown = [layer for layer in layers if layer not in TRAINER_LAYERS]
    assert not unknown, ("layers the station's model does not have", unknown)
    return {"layers": list(layers), "screen": screen, **({"manikin": dict(manikin)} if manikin else {})}


TRAINER_LOOKS = {
    # on the table under a blanket, both lungs ventilated; once the position is checked, the skin is marked
    "ready": look([]),
    "positioned": look(MARKED),
    # prepared and draped, the tray over the legs; the lung is let down
    "lung-down": look(MARKED + ["mayo"], manikin=ONE_LUNG),
    "camera-port": look(["lines", "site-working", "camera-port", "mayo"], manikin=ONE_LUNG),
    # the scope in: the monitor shows the chest
    "explored": look(["lines", "site-working", "camera-port", "scope", "mayo"], "thoracoscopy", ONE_LUNG),
    "working-ports": look(IN_THE_CHEST, "thoracoscopy", ONE_LUNG),
    # the lung held through the third port while the lobe is freed and its vein, artery and bronchus divided
    **{state: look(IN_THE_CHEST + ["retractor"], "thoracoscopy", ONE_LUNG)
       for state in ("mobilised", "hilum", "vein-divided", "artery-divided", "bronchus-divided", "lobe-free")},
    # the lobe out in its bag; the lung held again for the nodes; the leak test
    "specimen-out": look(IN_THE_CHEST + ["specimen"], "thoracoscopy", ONE_LUNG),
    "nodes": look(IN_THE_CHEST + ["retractor", "specimen"], "thoracoscopy", ONE_LUNG),
    "leak-tested": look(IN_THE_CHEST + ["specimen"], "thoracoscopy", ONE_LUNG),
    # the drain through the camera port's incision, watched from the utility incision; then the lung up again
    "drained": look(["lines", "working-ports", "chest-tube", "scope-utility", "mayo", "specimen"], "thoracoscopy", ONE_LUNG),
    "re-expanded": look(["lines", "working-ports", "chest-tube", "scope-utility", "mayo", "specimen"], "thoracoscopy", TWO_LUNGS),
    # closed: the dressings on, the drapes off, a blanket again; the drain stays
    "closed": look(["lines", "chest-tube", "dressings"]),
}
assert sorted({layer for lk in TRAINER_LOOKS.values() for layer in lk["layers"]}) == sorted(TRAINER_LAYERS), "a layer of the model that no step shows"

eq(TRAINER, L("胸腔镜手术模拟训练台", "Thoracoscopy (VATS) training station"), "teaching",
   L("胸腔镜肺叶切除的模拟训练台：模拟人取侧卧位（左侧向上），躺在折起的床面和真空垫上——头枕头圈，颈部与躯干成一直线；下方手臂前伸放在托手板上，上方手臂前屈放在带垫托架上；下腿屈髋屈膝，两腿之间垫枕；腋下垫置于腋窝下方的胸壁下；口角固定着双腔气管导管。台上的样子随步骤变化：刚开始时盖着毯子、双肺通气；核对体位后皮肤上画好腋前线、腋中线、腋后线和切口位置；铺巾后术侧肺萎陷；随后标准化三孔前入路的切口按各自的步骤出现——位置低而靠前、约在膈顶水平的 1 cm 观察孔（10 mm 30° 胸腔镜立在其中），第 4 肋间、背阔肌前缘之前约 5 cm 的操作口（放切口保护套，不撑开肋骨），以及与观察孔同一水平、更靠后（肩胛骨正下方）的 1.5 cm 操作孔（经此用肺钳牵开肺）；标本装袋放在器械台的弯盘里，胸管经观察孔切口置入，肺复张，最后贴好敷料、重新盖上毯子。胸腔镜在胸腔内时，床头后方的显示器显示镜头画面。从核对体位到关胸，按顺序演练下肺叶切除的每一步（静脉、动脉、支气管；不同肺叶的顺序不同）。",
     "A simulator for thoracoscopic lobectomy: a full-body patient simulator in the lateral position (left side up) on a flexed top and a vacuum mattress — the head on a ring so that the neck lies in line with the trunk, the lower arm out in front on its board, the upper arm forward on a padded support, the lower leg bent at hip and knee with a pillow between the legs, the axillary roll under the chest wall below the armpit — the double-lumen tube taped at the mouth. What lies on it follows the steps: under a blanket and ventilated on both lungs as it is found; the axillary lines and the sites of the incisions marked once the position is checked; draped, the lung on the operated side down; then the incisions of the standardized three-port anterior approach, each as its step makes it — the 1 cm camera port low and anterior at about the level of the top of the diaphragm (the 10 mm 30° thoracoscope stands in it), the utility incision of about 5 cm in the 4th intercostal space just in front of latissimus dorsi (a wound protector in it, the ribs not spread) and a 1.5 cm port at the camera port's level further back, straight down from the scapula (a lung grasper through it holds the lung); the lobe out in its bag in the bowl on the instrument tray, the chest tube through the camera port's incision, the lung up again, and at the end the dressings and a blanket. The monitor behind the head end shows the camera's picture while the scope is in. Every step of a lower lobectomy is rehearsed in order, from the position check to the closure (vein, artery, bronchus — the order differs from lobe to lobe)."),
   (2.1, 1.15, 1.8),
   [
       # (the fallback when the model is not loaded; the body is the world's own figure either way: TRAINER_BODY)
       B("plastic", 0, 0.04, -0.13, 0.7, 0.08, 0.6),
       B("sc-robot", -0.07, 0.42, -0.13, 0.36, 0.68, 0.4),
       B("steel", -0.635, 0.8, -0.13, 0.74, 0.05, 0.54),
       B("steel", 0.37, 0.75, -0.13, 1.28, 0.05, 0.54),
       B("sc-vacuum-mat", -0.635, 0.855, -0.13, 0.72, 0.06, 0.58),
       B("sc-vacuum-mat", 0.37, 0.805, -0.13, 1.26, 0.06, 0.58),
       B("white", -0.69, 0.93, -0.19, 0.3, 0.08, 0.34),
       B("teal", -0.69, 0.985, -0.19, 0.17, 0.04, 0.17),
       B("navy", -0.5, 0.89, 0.35, 0.16, 0.03, 0.44),
       B("chrome", -0.64, 1.0, 0.17, 0.03, 0.3, 0.03),
       B("navy", -0.64, 1.17, 0.13, 0.4, 0.05, 0.14),
       B("white", -0.37, 1.275, -0.14, 0.07, 0.012, 0.05),
       B("white", -0.234, 1.265, -0.13, 0.03, 0.03, 0.03),
       B("white", -0.234, 1.265, -0.26, 0.03, 0.03, 0.03),
       B("chrome", -0.16, 1.42, -0.07, 0.02, 0.3, 0.02),
       B("coal", -0.07, 1.57, -0.02, 0.05, 0.08, 0.05),
       B("chrome", -0.94, 1.2, -0.445, 0.04, 0.9, 0.04),
       B("sc-matte-black", -0.68, 1.56, -0.5, 0.56, 0.36, 0.05),
       B("screen-dark", -0.68, 1.56, -0.472, 0.5, 0.3, 0.006, name="screen"),
   ],
   usage=L("拿好这一步要用的器械，在训练台前按顺序操作；每一步的前提不满足时，训练台会说明还缺什么。演练的是流程和安全要点，不是手感。",
           "Take the instrument the step needs and work through the steps in order at the station; when a step's conditions are not met, the station says what is missing. It rehearses the sequence and its safety points, not the feel of tissue."),
   interaction="device", prompt=L("E · 胸腔镜模拟训练", "E · Thoracoscopy training"), screen="thoracoscopy",
   tags=["simulation", "thoracic", "mis", "trainer", "teaching"], manikin=TRAINER_BODY,
   behavior={"initial": "ready",
             "states": {state: {**spec, "look": TRAINER_LOOKS[state]} for state, spec in {
                 "ready": st("待训练", "ready"),
                 "positioned": st("体位已核对（侧卧、腋下垫、托臂、折床）", "position checked (lateral, axillary roll, arm support, table flexed)"),
                 "lung-down": st("导管位置已再次确认，术侧肺已萎陷", "tube position confirmed again, the lung on the operated side down"),
                 "camera-port": st("观察孔已置入", "camera port in"),
                 "explored": st("已探查胸腔", "chest explored"),
                 "working-ports": st("操作口已在镜下建立", "working incisions made under vision"),
                 "mobilised": st("粘连已松解，下肺韧带已打开", "adhesions freed, pulmonary ligament divided"),
                 "hilum": st("肺门已解剖，结构已套带", "hilum dissected, the structures looped"),
                 "vein-divided": st("下肺静脉已切断", "inferior pulmonary vein divided"),
                 "artery-divided": st("肺动脉分支已切断", "arterial branches divided"),
                 "bronchus-divided": st("下叶支气管已切断", "lower lobe bronchus divided"),
                 "lobe-free": st("叶间裂已切开，肺叶游离", "fissure completed, the lobe free"),
                 "specimen-out": st("标本已装袋取出", "specimen out in its bag"),
                 "nodes": st("淋巴结已清扫", "lymph nodes taken"),
                 "leak-tested": st("注水膨肺试验无漏气", "no leak under water"),
                 "drained": st("胸管已置入", "chest tube in"),
                 "re-expanded": st("肺已在直视下复张", "lung re-expanded under vision"),
                 "closed": st("已关胸", "closed"),
             }.items()},
             "operations": {
                 "check_position": step("核对体位：术侧向上，腋下垫在腋窝下方的胸壁下，上臂在托架上，折床张开肋间隙，受压点有垫",
                                        "Check the position: operated side up, the axillary roll under the chest wall below the armpit, the upper arm on its support, the table flexed to open the spaces, pressure points padded",
                                        "ready", "positioned"),
                 "isolate_lung": step("（模拟麻醉）侧卧位后再次用纤支镜确认双腔管位置，夹闭术侧管腔：单肺通气，术侧肺萎陷",
                                      "(Simulated anaesthesia) confirm the double-lumen tube again with the bronchoscope now that the manikin is on its side, clamp the operated side: one-lung ventilation, the lung comes down",
                                      "positioned", "lung-down"),
                 "place_camera_port": step("建立观察孔：位置低而靠前，约在膈顶水平、肺门与膈神经的前方（1 cm）；沿下位肋骨上缘进入，手指探查后置入套管",
                                           "Camera port: low and anterior, at about the level of the top of the diaphragm, in front of the hilum and the phrenic nerve (1 cm); in over the upper border of the lower rib, a finger sweep, then the port",
                                           "lung-down", "camera-port", [HOLDING("sc-thoracoport")]),
                 "explore": step("入镜探查：胸膜、肺、膈肌和纵隔，有无粘连、积液和未预料的病变",
                                 "Scope in and look round: pleura, lung, diaphragm and mediastinum — adhesions, fluid, anything unexpected",
                                 "camera-port", "explored", [HOLDING("sc-thoracoscope"), SCOPE_READY], 90),
                 "place_working_ports": step("镜下直视建立操作口：第 4 肋间、背阔肌前缘之前约 5 cm 的操作口（放切口保护套，不撑开肋骨），和与观察孔同一水平、更靠后（肩胛骨正下方）的 1.5 cm 操作孔；从胸腔内看着器械尖端穿入",
                                             "Working incisions under vision: the utility incision of about 5 cm in the 4th space just in front of latissimus dorsi (a wound protector, no rib spreading) and the 1.5 cm port at the camera port's level further back, straight down from the scapula — watch each tip come through from inside",
                                             "explored", "working-ports", [], 120),
                 "free_adhesions": step("超声刀松解粘连、打开下肺韧带", "Free the adhesions and divide the pulmonary ligament with the ultrasonic shears",
                                        "working-ports", "mobilised", [HOLDING("sc-ultrasonic-shears"), SMOKE], 180),
                 "dissect_hilum": step("打开纵隔胸膜，解剖肺门：直角钳游离静脉、动脉分支和支气管，逐一套带",
                                       "Open the mediastinal pleura and dissect the hilum: free the vein, the arterial branches and the bronchus with the right-angle dissector and pass a loop round each",
                                       "mobilised", "hilum", [HOLDING("sc-endo-dissector")], 300),
                 "divide_vein": step("切断下肺静脉：血管钉仓，钳口内只有静脉、尖端完全穿出后击发", "Divide the inferior pulmonary vein: a vascular reload; fire only with the vein alone in the jaws and the tip clear beyond it",
                                     "hilum", "vein-divided", [HOLDING("sc-endo-stapler")], 120),
                 "divide_artery": step("切断肺动脉分支：血管钉仓；细小分支用结扎夹", "Divide the arterial branches: vascular reloads; clips for the small ones",
                                       "vein-divided", "artery-divided", [{"any": [HOLDING("sc-endo-stapler"), HOLDING("sc-clip-applier")]}], 180),
                 "divide_bronchus": step("切断下叶支气管：缝合器夹闭在预定位置后，先请麻醉医生膨肺，确认余肺通气，再击发",
                                         "Divide the lower lobe bronchus: close the stapler where it is to fire, have the anaesthetist inflate — the lobe that stays must ventilate — then fire",
                                         "artery-divided", "bronchus-divided", [HOLDING("sc-endo-stapler")], 120),
                 "complete_fissure": step("切割缝合器切开叶间裂，肺叶游离", "Complete the fissure with the stapler: the lobe is free",
                                          "bronchus-divided", "lobe-free", [HOLDING("sc-endo-stapler")], 120),
                 "retrieve_specimen": step("标本装袋，经操作口取出", "Bag the specimen and bring it out through the utility incision",
                                           "lobe-free", "specimen-out", [HOLDING("sc-specimen-bag")], 90),
                 "take_nodes": step("超声刀清扫肺门与纵隔淋巴结", "Take the hilar and mediastinal lymph nodes with the ultrasonic shears",
                                    "specimen-out", "nodes", [HOLDING("sc-ultrasonic-shears"), SMOKE], 300),
                 "leak_test": step("注温生理盐水浸没支气管残端，请麻醉医生膨肺并维持 20–30 cmH₂O：无气泡", "Cover the bronchial stump with warm saline and have the anaesthetist inflate the lung to a sustained 20–30 cmH₂O: no bubbles",
                                   "nodes", "leak-tested", [], 90),
                 "place_drain": step("经观察孔置入一根胸管，镜下确认位置", "One chest tube through the camera port, its position confirmed under vision",
                                     "leak-tested", "drained", [HOLDING("sc-chest-tube"), near(DRAINAGE, ["primed", "water-seal", "suction"], 6)], 90),
                 "re_expand": step("（模拟麻醉）直视下缓慢膨肺，确认各肺叶复张，恢复双肺通气", "(Simulated anaesthesia) re-expand the lung slowly under vision, see every lobe come up: both lungs ventilated again",
                                   "drained", "re-expanded"),
                 "close": step("逐层关闭切口", "Close in layers",
                               "re-expanded", "closed", [near("sc-count-board", ["cavity", "closing", "reconciled", "excluded"], 12)], 180),
                 "reset": op("下一位学员：复位训练台", "Next trainee: reset the station", ["closed"], "ready", [], TEAM, 30),
             }})

# ------------------------------------------------------------------------------------------------ the lay-out
# The thoracoscopy instruments on their own draped table (table-local offsets, on the drape at 0.9 m): the long
# instruments side by side, their tips one way.
VATS_ITEMS = [
    ("vats-scope", "sc-thoracoscope", -0.3, -0.21, L("30° 胸腔镜", "30° thoracoscope")),
    ("vats-stapler", "sc-endo-stapler", -0.3, -0.06, L("切割缝合器", "Stapler")),
    ("vats-shears", "sc-ultrasonic-shears", -0.3, 0.14, L("超声刀", "Ultrasonic shears")),
    ("vats-lung-forceps", "sc-lung-forceps", 0.24, -0.22, L("肺钳", "Lung forceps")),
    ("vats-dissector", "sc-endo-dissector", 0.26, -0.13, L("直角分离钳", "Right-angle dissector")),
    ("vats-clip-applier", "sc-clip-applier", 0.3, -0.03, L("施夹钳", "Clip applier")),
    ("vats-chest-tube", "sc-chest-tube", 0.3, 0.06, L("胸管", "Chest tube")),
    ("vats-port", "sc-thoracoport", 0.12, 0.17, L("胸腔穿刺套管", "Thoracic port")),
    ("vats-bag", "sc-specimen-bag", 0.4, 0.19, L("标本袋", "Specimen bag")),
]
