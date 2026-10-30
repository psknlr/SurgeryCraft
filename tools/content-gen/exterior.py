"""IMPF Surgery Hospital: the exterior — envelope, arrival, landscape and roof.

Design concept: a calm white rainscreen volume wrapped in continuous dark ribbon glazing; the entrance hall and
the lobby above it a double-height glass lantern under a floating canopy with a timber soffit and the IMPF
letters; a rhythm of timber-look vertical fins screening the operating floor on three sides (solar control and
privacy) while the ground floor stays open; a granite arrival plaza with a reflecting pool, a tree bosque,
corten planter-benches and light bollards; on the roof a helipad, photovoltaics, a louvred plant screen and a
skylight over the lobby.

Imported by catalog.py (materials and exterior equipment types) and facility.py (openings, placements, terrain,
signs). Every exterior element is decor (`interaction: "none"`), non-solid unless people could walk into it.
"""
import math

from common import B, L, num
import catalog
from catalog import eq

# ------------------------------------------------------------------------------------------------ materials
EXT_MATERIALS = [
    {"id": "sc-ext-panel", "color": "#ecedea", "pattern": "grid", "variance": 0.015, "roughness": 0.55},
    {"id": "sc-ext-spandrel", "color": "#2d353c", "pattern": "flat", "variance": 0.01, "roughness": 0.22, "metalness": 0.35},
    {"id": "sc-ext-frame", "color": "#2a2f34", "pattern": "flat", "variance": 0.01, "roughness": 0.35, "metalness": 0.45},
    {"id": "sc-ext-roof", "color": "#f2f3f1", "pattern": "flat", "variance": 0.01, "roughness": 0.6},
    {"id": "sc-ext-timber", "color": "#b5835a", "pattern": "plank", "variance": 0.07, "roughness": 0.7},
    {"id": "sc-ext-soffit", "color": "#c49a6c", "pattern": "plank", "variance": 0.06, "roughness": 0.75},
    {"id": "sc-ext-led", "color": "#fff4dc", "pattern": "flat", "variance": 0, "emissive": "#ffe9c0", "emissiveIntensity": 1.4},
    {"id": "sc-ext-paving", "color": "#dcdbd4", "pattern": "tile", "variance": 0.04, "roughness": 0.8, "castShadow": False},
    {"id": "sc-ext-paving-dark", "color": "#7d817f", "pattern": "tile", "variance": 0.04, "roughness": 0.8, "castShadow": False},
    {"id": "sc-ext-corten", "color": "#8c4a26", "pattern": "noise", "variance": 0.08, "roughness": 0.85},
    {"id": "sc-ext-pv", "color": "#1d2c47", "pattern": "grid", "variance": 0.03, "roughness": 0.25, "metalness": 0.5},
    {"id": "sc-ext-deck", "color": "#3b4045", "pattern": "noise", "variance": 0.04, "roughness": 0.8},
    {"id": "sc-ext-shrub", "color": "#4f7d45", "pattern": "noise", "variance": 0.12, "roughness": 0.95},
    {"id": "sc-ext-louvre", "color": "#c3c8cb", "pattern": "stripe", "variance": 0.03, "roughness": 0.45, "metalness": 0.3},
]
catalog.MATERIALS.extend(EXT_MATERIALS)
catalog.MAT_IDS.update(m["id"] for m in EXT_MATERIALS)

# the envelope: white panels, a dark spandrel band at every floor line merging with the ribbon glazing, slim dark
# aluminium frames and mullions, a white floating roof plate
WALLS = {"height": 5, "base": "sc-ext-spandrel", "body": "sc-ext-panel", "top": "sc-ext-panel", "thickness": 0.35,
         "frame": "sc-ext-frame", "mullion": "sc-ext-frame"}
ROOF = {"material": "sc-ext-roof", "skylights": [{"x": -1.5, "z": 16, "w": 12, "d": 3}], "beams": "sc-ext-frame"}


def deco(id, name, desc, footprint, parts, solid=False, tags=()):
    eq(id, name, "decor", desc, footprint, parts, solid=solid, tags=["exterior", *tags])


# ------------------------------------------------------------------------------------------------ facade fins
FIN_W, FIN_D, FIN_H = 4.8, 0.7, 5.3
_fins = []
for i in range(8):
    depth = 0.3 + 0.35 * (0.5 + 0.5 * math.sin(2 * math.pi * i / 8))
    _fins.append(B("sc-ext-timber", -2.1 + i * 0.6, FIN_H / 2, -FIN_D / 2 + depth / 2, 0.09, FIN_H - 0.1, depth))
deco("sc-ext-fins", L("立面竖向遮阳格栅", "Facade fin screen"),
     L("手术部立面的竖向遮阳格栅：仿木纹铝合金翼片按 0.6 m 间距排列、进深在 0.30–0.65 m 之间起伏，遮挡低角度日照与视线，同时让病房和走廊保留远景。",
       "Vertical solar-shading screen of the operating floor: timber-look aluminium fins at 0.6 m centres whose depth undulates between 0.30 and 0.65 m, cutting low-angle sun and overlooking while keeping the view out."),
     (FIN_W, FIN_D, FIN_H),
     _fins + [B("sc-ext-frame", 0, 0.08, -0.3, FIN_W, 0.06, 0.08), B("sc-ext-frame", 0, FIN_H - 0.08, -0.3, FIN_W, 0.06, 0.08)],
     tags=["facade", "shading"])

# ------------------------------------------------------------------------------------------------ entrance
CAN_W, CAN_D = 16.0, 7.0
deco("sc-ext-canopy", L("入口悬挑雨篷", "Entrance canopy"),
     L("主入口的白色悬挑雨篷：28 cm 薄板、暖色木纹吊顶与嵌入式 LED 筒灯，两根细柱落在车道一侧，雨天也能从落客区一路走到门口。",
       "Floating white entrance canopy: a 28 cm plate with a warm timber soffit and recessed LED downlights on two slender columns, so you walk from the drop-off to the door under cover."),
     (CAN_W, CAN_D, 4.9),
     [B("sc-ext-roof", 0, 4.71, 0, CAN_W, 0.28, CAN_D), B("sc-ext-soffit", 0, 4.555, 0, CAN_W - 0.2, 0.03, CAN_D - 0.2),
      B("sc-ext-frame", 0, 4.71, CAN_D / 2 - 0.01, CAN_W, 0.08, 0.02)]
     + [B("sc-ext-led", x, 4.535, z, 0.25, 0.01, 0.25) for x in (-6, -3, 0, 3, 6) for z in (-2.2, 0.4, 2.8)],
     tags=["entrance"])
WALK_W, WALK_D = 15.0, 3.5
deco("sc-ext-walkway-canopy", L("有盖连廊雨篷", "Covered walkway canopy"),
     L("沿立面的悬挑连廊雨篷，把落客区和主入口连成一条有遮蔽的步道，吊顶同为暖色木纹并带 LED 筒灯。",
       "A cantilevered walkway canopy along the facade linking the drop-off to the main entrance under cover, with the same warm timber soffit and LED downlights."),
     (WALK_W, WALK_D, 4.9),
     [B("sc-ext-roof", 0, 4.73, 0, WALK_W, 0.24, WALK_D), B("sc-ext-soffit", 0, 4.595, 0, WALK_W - 0.2, 0.03, WALK_D - 0.2),
      B("sc-ext-frame", 0, 4.73, WALK_D / 2 - 0.01, WALK_W, 0.08, 0.02)]
     + [B("sc-ext-led", x, 4.575, 0.3, 0.25, 0.01, 0.25) for x in (-6, -3, 0, 3, 6)],
     tags=["entrance"])
eq("sc-ext-column", L("雨篷柱", "Canopy column"), "decor",
   L("雨篷的细钢柱。", "A slender steel canopy column."), (0.24, 0.24, 4.6), [B("sc-ext-frame", 0, 2.28, 0, 0.22, 4.56, 0.22)],
   solid=True, tags=["exterior", "entrance"])


def _letters():
    """"IMPF" in 0.2 m strokes, 1.2 m tall, on a glowing base line (centred on x)."""
    m, s, h, y0 = "sc-ext-frame", 0.2, 1.2, 0.06
    top, mid = y0 + h - s / 2, y0 + h / 2
    x = -1.9
    parts = [B(m, x + s / 2, y0 + h / 2, 0, s, h, 0.18)]  # I
    x += s + 0.35
    parts += [B(m, x + s / 2, y0 + h / 2, 0, s, h, 0.18), B(m, x + 1.0 - s / 2, y0 + h / 2, 0, s, h, 0.18),  # M
              B(m, x + 0.33, y0 + h - 0.16, 0, 0.26, 0.3, 0.18), B(m, x + 0.5, y0 + h - 0.41, 0, 0.2, 0.3, 0.18),
              B(m, x + 0.67, y0 + h - 0.16, 0, 0.26, 0.3, 0.18)]
    x += 1.0 + 0.35
    parts += [B(m, x + s / 2, y0 + h / 2, 0, s, h, 0.18), B(m, x + 0.4, top, 0, 0.8, s, 0.18),  # P
              B(m, x + 0.4, mid + 0.06, 0, 0.8, s, 0.18), B(m, x + 0.8 - s / 2, (top + mid + 0.06) / 2, 0, s, top - mid - 0.06, 0.18)]
    x += 0.8 + 0.35
    parts += [B(m, x + s / 2, y0 + h / 2, 0, s, h, 0.18), B(m, x + 0.375, top, 0, 0.75, s, 0.18),  # F
              B(m, x + 0.3, mid + 0.06, 0, 0.6, s, 0.18)]
    return parts + [B("sc-ext-led", 0, 0.03, 0.1, 4.0, 0.03, 0.04)]


deco("sc-ext-letters-impf", L("IMPF 立体字", "IMPF letters"),
     L("雨篷上的 IMPF 立体字：石墨色铝字，底部暖光灯带。", "The IMPF letters standing on the canopy: graphite aluminium with a warm light line below."),
     (4.0, 0.3, 1.3), _letters(), tags=["entrance", "brand"])
eq("sc-ext-totem", L("医院标识塔", "Hospital totem"), "decor",
   L("入口广场的标识塔：石墨色铝板塔身、白色标识面和竖向暖光灯带。", "The arrival totem: a graphite aluminium column with a white sign face and a vertical warm light line."),
   (1.4, 0.45, 4.2),
   [B("sc-ext-frame", 0, 2.1, 0, 1.3, 4.2, 0.4), B("sc-ext-roof", 0, 2.75, 0.205, 1.1, 1.7, 0.01), B("sc-ext-led", -0.58, 2.1, 0.205, 0.05, 3.6, 0.01)],
   solid=True, tags=["exterior", "brand", "wayfinding"])

# ------------------------------------------------------------------------------------------------ landscape
deco("sc-ext-planter-bench", L("耐候钢花池座椅", "Corten planter bench"),
     L("耐候钢花池与木质长椅：低矮灌木、香草与座位，供患者家属在室外等候。", "A corten steel planter with a timber bench: low shrubs, herbs and a seat for families waiting outside."),
     (4.0, 1.4, 1.1),
     [B("sc-ext-corten", 0, 0.25, -0.2, 4.0, 0.5, 1.0), B("sc-ext-timber", 0, 0.46, 0.47, 3.8, 0.06, 0.45),
      B("sc-ext-frame", -1.6, 0.21, 0.47, 0.08, 0.42, 0.4), B("sc-ext-frame", 1.6, 0.21, 0.47, 0.08, 0.42, 0.4)]
     + [B("sc-ext-shrub", x, 0.7, -0.2, 0.8, 0.4 + 0.15 * (i % 2), 0.8) for i, x in enumerate((-1.45, -0.5, 0.45, 1.4))],
     solid=True, tags=["landscape", "seating"])
deco("sc-ext-bollard", L("庭院灯柱", "Light bollard"),
     L("1 m 高的石墨色庭院灯柱，顶部暖光。", "A 1 m graphite light bollard with a warm head."),
     (0.18, 0.18, 1.0), [B("sc-ext-frame", 0, 0.45, 0, 0.16, 0.9, 0.16), B("sc-ext-led", 0, 0.93, 0, 0.17, 0.06, 0.17)], tags=["landscape", "lighting"])

# ------------------------------------------------------------------------------------------------ roof
_garden = [B("sc-ext-timber", 0, 0.06, 0, 12, 0.12, 4)]
_garden += [B("sc-ext-corten", x, 0.35, -1.35, 2.6, 0.5, 1.1) for x in (-4.5, -1.5, 1.5, 4.5)]
_garden += [B("sc-ext-shrub", x, 0.75, -1.35, 2.2, 0.35 + 0.15 * (i % 2), 0.8) for i, x in enumerate((-4.5, -1.5, 1.5, 4.5))]
_garden += [B("sc-ext-timber", x, 0.4, 1.0, 2.4, 0.08, 0.5) for x in (-3.5, 0.5, 4.0)]
_garden += [B("glass", 0, 0.7, 1.97, 12, 1.1, 0.04)]
deco("sc-ext-roof-garden", L("屋顶员工花园", "Rooftop staff garden"),
     L("手术部屋顶的员工花园：木平台、耐候钢花池与长椅、玻璃护栏——手术间隙可以到室外透口气（循证设计：自然与日光减轻医护疲劳）。",
       "The staff garden on the operating department roof: a timber deck, corten planters and benches behind a glass balustrade — fresh air between cases (evidence-based design: nature and daylight reduce staff fatigue)."),
     (12, 4, 1.3), _garden, tags=["roof", "garden"])

_pv = []
for zc in (-1.05, 0.0, 1.05):
    _pv += [B("sc-ext-pv", 0, 0.42, zc - 0.2, 7.8, 0.06, 0.42), B("sc-ext-pv", 0, 0.62, zc + 0.2, 7.8, 0.06, 0.42)]
    _pv += [B("chrome", x, 0.24, zc, 0.06, 0.48, 0.06) for x in (-3.8, 0, 3.8)]
deco("sc-ext-pv-array", L("屋顶光伏阵列", "Rooftop photovoltaic array"),
     L("屋面光伏阵列：倾斜单晶硅组件，为不间断电源和空调系统补充电力。", "Rooftop photovoltaic array: tilted monocrystalline modules feeding the UPS and HVAC plant."),
     (8.0, 3.2, 1.0), _pv, tags=["roof", "energy"])

_heli = [B("sc-ext-deck", 0, 0.8, 0, 15, 0.2, 15)]
_heli += [B("steel", x, 0.35, z, 0.25, 0.7, 0.25) for x in (-7, 0, 7) for z in (-7, 0, 7)]
_heli += [B("white", 0, 0.915, z, 7.2, 0.02, 0.35) for z in (-3.6, 3.6)] + [B("white", x, 0.915, 0, 0.35, 0.02, 7.2) for x in (-3.6, 3.6)]
_heli += [B("white", -1.1, 0.92, 0, 0.45, 0.02, 3.4), B("white", 1.1, 0.92, 0, 0.45, 0.02, 3.4), B("white", 0, 0.92, 0, 1.75, 0.02, 0.45)]
_heli += [B("yellow", 0, 0.912, z, 14.6, 0.02, 0.2) for z in (-7.2, 7.2)] + [B("yellow", x, 0.912, 0, 0.2, 0.02, 14.6) for x in (-7.2, 7.2)]
_heli += [B("led-green", u, 0.95, s * 7.35, 0.18, 0.08, 0.18) for u in (-6, -3, 0, 3, 6) for s in (-1, 1)]
_heli += [B("led-green", s * 7.35, 0.95, u, 0.18, 0.08, 0.18) for u in (-6, -3, 3, 6) for s in (-1, 1)]
_heli += [B("steel", 0, 0.8, s * 7.45, 15, 0.12, 0.1) for s in (-1, 1)]
_heli += [B("steel", 6.9, 2.0, 6.9, 0.08, 2.4, 0.08), B("orange", 6.55, 3.0, 6.9, 0.6, 0.26, 0.26), B("white", 6.35, 3.0, 6.9, 0.12, 0.27, 0.27)]
deco("sc-ext-helipad", L("屋顶直升机停机坪", "Rooftop helipad"),
     L("屋顶直升机停机坪：15 × 15 m 抬升甲板、黄色安全区边线、白色着陆圈与 H 标、绿色边界灯和风向袋，供创伤和器官转运直达复合手术室。",
       "Rooftop helipad: a raised 15 × 15 m deck with a yellow safety-area line, the white touchdown marking and H, green perimeter lights and a windsock — trauma and organ retrieval straight to the hybrid OR."),
     (15, 15, 3.4), _heli, tags=["roof", "helipad"])

_screen = [B("sc-ext-louvre", 0, y, s * 2.95, 12, 0.12, 0.08) for y in (0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.4) for s in (-1, 1)]
_screen += [B("sc-ext-louvre", s * 5.95, y, 0, 0.08, 0.12, 6) for y in (0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.4) for s in (-1, 1)]
_screen += [B("sc-ext-frame", sx * 5.95, 1.3, sz * 2.95, 0.1, 2.6, 0.1) for sx in (-1, 1) for sz in (-1, 1)]
_screen += [B("steel", x, 1.0, 0, 3.0, 2.0, 2.6) for x in (-3.5, 0.2)] + [B("coal", x, 2.05, 0, 1.0, 0.1, 1.0) for x in (-3.5, 0.2)]
_screen += [B("steel", 4.0, 0.9, 0, 1.6, 1.8, 2.0)]
deco("sc-ext-plant-screen", L("屋顶设备百叶围护", "Rooftop plant screen"),
     L("屋顶设备区的铝合金百叶围护，遮挡排风机与冷却设备，从地面和直升机坪看都是整洁的屋面。",
       "Louvred aluminium screen round the rooftop plant (exhaust fans and heat rejection), so the roof reads clean from the ground and the helipad."),
     (12, 6, 2.6), _screen, tags=["roof", "plant"])
