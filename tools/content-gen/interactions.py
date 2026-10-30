"""IMPF Surgery Hospital: what people do with the operating department's things (ClinicalCraft EMBODIED §5, §8.1).

Handheld instruments and wearables with lifecycles (sterile → in use → used → reprocessed in the CSSD), and declarative
state machines on the devices the team operates — the WHO checklist, the surgical count board and its RF adjunct, the
smoke evacuator and the electrosurgical generator, the room control panel, the laparoscopy tower, the hybrid OR's lead
shield and contrast injector, the CSSD washer-disinfector and steriliser. Gating uses the engine's world predicates
only (`handsClean`, `actorHolding` — worn items count —, `role`, `state`, `nearbyState`, `patientWithin`), so the
rules are data: no incision before the time-out with the room in operating mode, gowned, gloved and scrubbed; no
energy without smoke evacuation; no closing sign-out before the counts reconcile with the RF scan; no injection under
fluoroscopy without lead; no reuse of an instrument before it went through the washer and the steriliser.

Imported at the end of catalog.py (it appends to catalog.EQUIPMENT and patches existing types in place).
"""
from common import B, L
import catalog
from catalog import eq

SURGEON = ["clinician", "attending"]
SCRUB = ["clinician", "attending", "nurse"]
TEAM = ["clinician", "attending", "nurse"]
CIRCULATOR = ["nurse", "clinician", "attending"]
IMAGING = ["radiologist", "attending", "clinician"]
CSSD = ["nurse", "porter", "lab-tech", "clinician", "attending"]

IN_HAND = {"state": "held"}
SCRUBBED = [{"handsClean": True}, {"actorHolding": "sc-sterile-gown"}, {"actorHolding": "sc-sterile-gloves"}]
AT_TABLE = {"patientWithin": 1.4}


def st(zh, en, available=None):
    s = {"name": L(zh, en)}
    if available is not None:
        s["available"] = available
    return s


def op(zh, en, frm, to=None, requires=(), roles=None, seconds=None):
    o = {"name": L(zh, en), "from": frm}
    if to:
        o["to"] = to
    if requires:
        o["requires"] = list(requires)
    if seconds:
        o["durationSeconds"] = seconds
    if roles:
        o["roles"] = list(roles)
    return o


def near(type, state, within=None):
    n = {"type": type, "state": state}
    if within is not None:
        n["within"] = within
    return {"nearbyState": n}


def attach(id, behavior, prompt=None, description=None, usage=None):
    """Give an existing catalog type a behaviour (and make it operable: interaction kind `device`)."""
    e = next(x for x in catalog.EQUIPMENT if x["id"] == id)
    e["interaction"] = {"kind": "device", **({"prompt": prompt} if prompt else ({"prompt": e["interaction"]["prompt"]} if "prompt" in e["interaction"] else {}))}
    if description:
        e["description"] = description
    if usage:
        e["usage"] = usage
    parts = e.pop("parts")
    e["behavior"] = behavior
    e["parts"] = parts


# ------------------------------------------------------------------------------------------------ reprocessing
# Reusable instruments go back through the CSSD: washed and thermally disinfected (ISO 15883-1:2024), inspected and
# packed, steam-sterilised with a released load (EN 285:2015+A1:2021, ISO 17665:2024) — the instrument's own
# `reprocess` needs both machines nearby in those states, so the tray must physically travel to the CSSD.
REPROCESS = op("消毒供应中心再处理（清洗消毒→检查包装→灭菌）", "Reprocess in the CSSD (wash → inspect & pack → sterilise)",
               ["used"], "sterile",
               [near("sc-washer-disinfector", "complete", 12), near("sc-steam-steriliser", "released", 12)], CSSD, 120)

LIFE = {
    "sterile": st("无菌（UDI 可追溯）", "sterile (UDI-traceable)"),
    "in-use": st("使用中", "in use"),
    "used": st("已使用，待再处理", "used — to the CSSD"),
}


def instrument(id, name, desc, usage, footprint, parts, uses):
    """A reusable handheld instrument: sterile → in use (its own operations, in hand, scrubbed) → used → reprocessed."""
    ops = dict(uses)
    ops["finish"] = op("用毕放回待再处理", "Finished with — mark for reprocessing", ["in-use"], "used", [IN_HAND], SCRUB)
    ops["reprocess"] = REPROCESS
    eq(id, name, "surgery", desc, footprint, parts, usage=usage, interaction="device", solid=False, portable="handheld", reach=1.2,
       prompt=L("E · 器械", "E · Instrument"), tags=["or", "instrument", "sterile", "udi"],
       behavior={"initial": "sterile", "states": LIFE, "operations": ops})


def thin(m, x, y, z, w, h, d):
    return B(m, x, y, z, w, h, d)


# ------------------------------------------------------------------------------------------------ instruments
instrument(
    "sc-scalpel", L("安全手术刀（3 号刀柄 + 10/15 号刀片）", "Safety scalpel (No. 3 handle, No. 10/15 blade)"),
    L("可回缩护套的安全手术刀：刀柄与刀片配合尺寸符合 ISO 7740，刀片为马氏体不锈钢（ISO 7153-1、ASTM F899-23），护套单手推出、用后回缩，刀柄激光直接标记 UDI（欧盟 MDR 附录 VI、21 CFR 801.45）。锐器经中立区传递（AORN），不手递手。",
      "Safety scalpel with a retractable shield: handle-to-blade fit to ISO 7740, martensitic stainless blade (ISO 7153-1, ASTM F899-23), one-handed shield advance and retraction, UDI laser-marked on the handle (EU MDR Annex VI, 21 CFR 801.45). Pass sharps through a neutral zone, never hand to hand (AORN)."),
    L("切皮前必须完成 WHO 暂停核查，手术间处于手术模式，术者已外科手消毒并穿无菌手术衣、戴无菌手套。",
      "Before skin incision: the WHO time-out done, the room in operating mode, the surgeon scrubbed, gowned and gloved."),
    (0.16, 0.04, 0.03),
    [thin("steel", -0.025, 0.01, 0, 0.1, 0.012, 0.016), thin("chrome", 0.055, 0.01, 0, 0.05, 0.006, 0.012),
     thin("sc-robot-accent", 0.02, 0.016, 0, 0.03, 0.012, 0.02)],
    {"incise": op("切开（切皮）", "Incise (skin incision)", ["sterile", "in-use"], "in-use",
                  [IN_HAND, *SCRUBBED, AT_TABLE, near("sc-who-checklist", ["timed-out", "signed-out"], 7),
                   near("sc-or-control-panel", "operating", 7)], SURGEON, 20)})

instrument(
    "sc-needle-holder", L("Mayo-Hegar 持针器（碳化钨钳口）", "Mayo-Hegar needle holder (tungsten-carbide jaws)"),
    L("碳化钨镶片钳口的持针器（金色手柄识别），关节器械通用要求与试验按 ISO 7151:2024，耐高压蒸汽与腐蚀按 ISO 13402:2025 验证，UDI 直接标记。",
      "Needle holder with tungsten-carbide jaw inserts (gold handles), articulated-instrument requirements and tests to ISO 7151:2024, autoclave and corrosion resistance verified to ISO 13402:2025, UDI direct-marked."),
    L("先夹针（针体后 1/3），再缝合；锐器计数。", "Load the needle (at the back third of the body), then suture; count the needles."),
    (0.18, 0.05, 0.02),
    [thin("chrome", -0.01, 0.008, -0.01, 0.12, 0.008, 0.008), thin("chrome", -0.01, 0.008, 0.01, 0.12, 0.008, 0.008),
     thin("gold", -0.07, 0.01, 0, 0.03, 0.012, 0.04), thin("steel", 0.065, 0.008, 0, 0.04, 0.008, 0.012)],
    {"load_needle": op("夹针", "Load a needle", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED], SCRUB, 10),
     "suture": op("缝合", "Suture", ["in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 60)})

instrument(
    "sc-tissue-forceps", L("DeBakey 无损伤组织镊", "DeBakey atraumatic tissue forceps"),
    L("DeBakey 无损伤组织镊（纵向细齿，适合血管与肠管），ISO 7153-1 不锈钢，UDI 直接标记。",
      "DeBakey atraumatic tissue forceps (fine longitudinal teeth for vessels and bowel), ISO 7153-1 stainless steel, UDI direct-marked."),
    None, (0.16, 0.03, 0.02),
    [thin("chrome", 0, 0.008, -0.006, 0.15, 0.006, 0.006), thin("chrome", 0, 0.008, 0.006, 0.15, 0.006, 0.006),
     thin("steel", -0.06, 0.008, 0, 0.02, 0.008, 0.018)],
    {"grasp": op("夹持组织", "Grasp tissue", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SCRUB, 10)})

instrument(
    "sc-metzenbaum-scissors", L("Metzenbaum 解剖剪（碳化钨刃口）", "Metzenbaum dissecting scissors (tungsten-carbide edges)"),
    L("弯头 Metzenbaum 解剖剪，碳化钨刃口（黑色手柄识别），剪刀通用要求与切割试验按 ISO 7741:1986，UDI 直接标记。",
      "Curved Metzenbaum dissecting scissors with tungsten-carbide edges (black handles), scissors requirements and cutting test to ISO 7741:1986, UDI direct-marked."),
    None, (0.18, 0.05, 0.02),
    [thin("chrome", 0.02, 0.008, -0.005, 0.12, 0.008, 0.008), thin("chrome", 0.02, 0.008, 0.005, 0.12, 0.008, 0.008),
     thin("sc-matte-black", -0.065, 0.01, 0, 0.04, 0.012, 0.04)],
    {"dissect": op("锐性分离", "Dissect", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SURGEON, 30)})

instrument(
    "sc-artery-forceps", L("弯止血钳（Kelly）", "Curved artery forceps (Kelly)"),
    L("Kelly 弯止血钳，带锁扣的关节器械（ISO 7151:2024），UDI 直接标记。",
      "Curved Kelly artery forceps, a ratcheted articulated instrument (ISO 7151:2024), UDI direct-marked."),
    None, (0.16, 0.05, 0.02),
    [thin("chrome", 0.02, 0.008, -0.005, 0.11, 0.008, 0.008), thin("chrome", 0.02, 0.008, 0.005, 0.11, 0.008, 0.008),
     thin("steel", -0.06, 0.01, 0, 0.03, 0.012, 0.04)],
    {"clamp": op("钳夹止血", "Clamp a bleeding vessel", ["sterile", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SCRUB, 10)})

eq("sc-esu-pencil", L("带排烟罩的电刀笔", "Electrosurgical pencil with smoke-evacuation shroud"), "surgery",
   L("一次性单极电刀笔，带排烟罩（直接接烟雾排除器），按钮激发切割/电凝；配合 IEC 60601-2-2:2017+A1:2023 的电刀主机和负极板接触质量监测使用。",
     "Single-use monopolar pencil with an integrated smoke-evacuation shroud (piped to the smoke evacuator), hand-switched cut and coag; used with an IEC 60601-2-2:2017+A1:2023 generator with return-electrode contact-quality monitoring."),
   (0.2, 0.04, 0.03),
   [thin("white", -0.02, 0.012, 0, 0.13, 0.016, 0.02), thin("yellow", -0.02, 0.022, 0, 0.02, 0.006, 0.01),
    thin("blue", 0.01, 0.022, 0, 0.02, 0.006, 0.01), thin("chrome", 0.075, 0.01, 0, 0.04, 0.004, 0.006),
    thin("plastic", 0.05, 0.014, 0, 0.03, 0.022, 0.026)],
   usage=L("电刀主机就绪（负极板已监测）且烟雾排除器运行时才能激发（AORN：所有手术烟雾都应排出并过滤）。",
           "Activates only with the generator ready (return electrode monitored) and the smoke evacuator running (AORN: evacuate and filter all surgical smoke)."),
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 电刀笔", "E · ESU pencil"),
   tags=["or", "instrument", "single-use", "energy"],
   behavior={"initial": "sterile", "states": {"sterile": st("无菌", "sterile"), "in-use": st("使用中", "in use"), "discarded": st("已丢弃", "discarded", False)},
             "operations": {
                 "cut": op("切割 / 电凝", "Cut / coagulate", ["sterile", "in-use"], "in-use",
                           [IN_HAND, *SCRUBBED, AT_TABLE, near("sc-surgical-pendant", "ready", 6), near("sc-smoke-evacuator", "running", 6)], SURGEON, 15),
                 "discard": op("用毕丢弃", "Discard after use", ["in-use"], "discarded", [IN_HAND], SCRUB),
             }})

eq("sc-gauze-swabs", L("X 线可显影 RFID 纱布（10 块）", "X-ray-detectable RFID gauze swabs (pack of 10)"), "surgery",
   L("带 X 线显影线与 RFID 标签的腹部纱布垫，每包 10 块；清点按日本手术医学会指南的时点进行，RF 检测作为计数的辅助手段（AORN）。",
     "Abdominal swabs with an X-ray-detectable thread and an RFID tag, ten to a pack; counted at the JAOM guideline points, with RF detection as the count adjunct (AORN)."),
   (0.12, 0.1, 0.04),
   [thin("white", 0, 0.015, 0, 0.11, 0.03, 0.09), thin("sc-drape", 0, 0.032, 0, 0.11, 0.004, 0.02), thin("blue", 0.04, 0.032, 0.03, 0.02, 0.004, 0.02)],
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 纱布", "E · Swabs"),
   tags=["or", "count", "rfid"],
   behavior={"initial": "counted", "states": {"counted": st("已清点", "counted"), "in-use": st("使用中", "in use"), "retrieved": st("已取回并计数", "retrieved and counted")},
             "operations": {
                 "pack": op("填塞 / 拭血", "Pack / mop", ["counted", "in-use"], "in-use", [IN_HAND, *SCRUBBED, AT_TABLE], SCRUB, 10),
                 "retrieve": op("取回并计数", "Retrieve and count", ["in-use"], "retrieved", [IN_HAND], SCRUB, 20),
             }})

eq("sc-instrument-set", L("硬质无菌器械盒（基础剖腹器械包）", "Rigid sterile container (major laparotomy set)"), "surgery",
   L("带过滤器与一次性封签的硬质灭菌容器（EN 868-8:2018），内放化学指示物（ISO 11140-1 第 5 类）与器械清单；开包前核对封签、外部指示物和有效期，开包后核对内部指示物。",
     "Rigid sterilisation container with filters and tamper-evident seals (EN 868-8:2018), a class 5 chemical integrator (ISO 11140-1) and the tray list inside; check seal, external indicator and expiry before opening and the internal integrator after."),
   (0.38, 0.26, 0.15),
   [B("steel", 0, 0.06, 0, 0.38, 0.12, 0.26), B("chrome", 0, 0.125, 0, 0.36, 0.01, 0.24), B("sc-robot-accent", 0.17, 0.08, 0.131, 0.03, 0.05, 0.004),
    B("led-green", -0.15, 0.1, 0.131, 0.04, 0.02, 0.004), B("paper", 0, 0.06, 0.131, 0.12, 0.05, 0.004)],
   usage=L("先核对（封签、指示物、有效期），再在无菌区内无菌开包；用毕关盒送消毒供应中心再处理。",
           "Verify (seal, indicators, expiry), then open aseptically inside the sterile field; close after use and send to the CSSD for reprocessing."),
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · 器械盒", "E · Instrument set"),
   tags=["or", "instrument", "container", "cssd"],
   behavior={"initial": "sealed",
             "states": {"sealed": st("密封（灭菌合格）", "sealed (sterile)"), "verified": st("已核对封签与指示物", "seal & indicators verified"),
                        "open": st("已无菌打开", "open (sterile field)"), "used": st("已使用，待再处理", "used — to the CSSD")},
             "operations": {
                 "verify": op("核对封签、指示物与有效期", "Check seal, indicators and expiry", ["sealed"], "verified", [], TEAM, 20),
                 "open_aseptically": op("无菌开包", "Open aseptically", ["verified"], "open", [{"handsClean": True}], TEAM, 30),
                 "close_case": op("用毕关盒，送消毒供应中心", "Close and send to the CSSD", ["open"], "used", [], TEAM, 20),
                 "reprocess": op("清洗、检查包装、灭菌（消毒供应中心）", "Wash, inspect & pack, sterilise (CSSD)", ["used"], "sealed",
                                 [near("sc-washer-disinfector", "complete", 12), near("sc-steam-steriliser", "released", 12)], CSSD, 180),
             }})

# ------------------------------------------------------------------------------------------------ wearables
# Worn (equipped) items leave the hands free; `actorHolding` counts them, so instruments can require them.


def wearable(id, name, desc, footprint, parts, tags):
    eq(id, name, "surgery", desc, footprint, parts, interaction="device", solid=False, portable="handheld", reach=1.2,
       prompt=L("E · 穿戴", "E · Put on"), tags=["or", "wearable", *tags])


wearable("sc-sterile-gown", L("加强型无菌手术衣（AAMI 4 级）", "Reinforced sterile surgical gown (AAMI Level 4)"),
         L("加强型无菌手术衣：关键区达到 AAMI PB70:2022 4 级屏障，同时满足 EN 13795-1:2019 高性能要求；外科手消毒后在无菌区内由洗手护士协助穿戴。",
           "Reinforced sterile gown: AAMI PB70:2022 Level 4 barrier in the critical zones and EN 13795-1:2019 high-performance; put on in the sterile field after the surgical scrub, helped by the scrub nurse."),
         (0.3, 0.24, 0.06),
         [B("sc-drape", 0, 0.025, 0, 0.3, 0.05, 0.24), B("paper", 0.08, 0.052, 0.06, 0.08, 0.004, 0.06), B("sc-robot-accent", -0.1, 0.052, -0.08, 0.06, 0.004, 0.04)],
         ["gown", "sterile"])
wearable("sc-sterile-gloves", L("无粉无菌外科手套（双层带穿孔指示）", "Powder-free sterile surgical gloves (double-glove indicator system)"),
         L("无粉灭菌外科手套，内层彩色穿孔指示（EN 455 系列、ASTM D3577），按 AORN 建议双层佩戴。",
           "Powder-free sterile surgical gloves with a coloured perforation-indicator underglove (EN 455 series, ASTM D3577), double-gloved as AORN recommends."),
         (0.18, 0.12, 0.03),
         [B("paper", 0, 0.012, 0, 0.18, 0.024, 0.12), B("green", -0.04, 0.026, 0, 0.06, 0.004, 0.08), B("cream", 0.04, 0.026, 0, 0.06, 0.004, 0.08)],
         ["gloves", "sterile"])
wearable("sc-lead-apron", L("铅衣（0.5 mm 铅当量，环绕式）", "Lead apron (0.5 mm Pb, wrap-around)"),
         L("环绕式铅/无铅复合防护围裙，正面 0.5 mm 铅当量（IEC 61331-3:2014 标识），透视与注射时佩戴；定期做透视完整性检查。",
           "Wrap-around lead-composite apron, 0.5 mm lead equivalent at the front (marked to IEC 61331-3:2014), worn during fluoroscopy and injections; screened for integrity periodically."),
         (0.5, 0.1, 0.9),
         [B("sc-lead-rubber", 0, 0.45, 0, 0.46, 0.84, 0.06), B("sc-robot-accent", 0, 0.86, 0, 0.3, 0.06, 0.07), B("chrome", 0, 0.89, 0, 0.04, 0.02, 0.02)],
         ["radiation", "lead"])

# ------------------------------------------------------------------------------------------------ new devices
eq("sc-sterile-setup-table", L("无菌器械台（铺巾摆台）", "Sterile set-up table (draped back table)"), "surgery",
   L("不锈钢器械后台，双层无菌巾铺到台面以下（台面以下视为非无菌），按器械清单摆台；整台位于层流保护区内。",
     "Stainless back table draped double to below the top (below the top is non-sterile), laid out to the tray list; the whole table sits inside the clean airflow zone."),
   (1.2, 0.6, 1.0),
   [B("rubber", x, 0.03, z, 0.06, 0.06, 0.06) for x in (-0.52, 0.52) for z in (-0.22, 0.22)]
   + [B("chrome", x, 0.46, z, 0.04, 0.8, 0.04) for x in (-0.52, 0.52) for z in (-0.22, 0.22)]
   + [B("steel", 0, 0.265, 0, 1.06, 0.03, 0.46), B("steel", 0, 0.875, 0, 1.12, 0.03, 0.52), B("sc-drape", 0, 0.895, 0, 1.16, 0.01, 0.56),
      B("sc-drape", 0, 0.8, 0.285, 1.16, 0.2, 0.01), B("sc-drape", 0, 0.8, -0.285, 1.16, 0.2, 0.01),
      B("sc-drape", -0.585, 0.8, 0, 0.01, 0.2, 0.57), B("sc-drape", 0.585, 0.8, 0, 0.01, 0.2, 0.57)],
   interaction="storage", prompt=L("E · 无菌器械台", "E · Sterile set-up table"), tags=["or", "sterile"])

eq("sc-smoke-evacuator", L("手术烟雾排除器（ULPA 过滤）", "Surgical smoke evacuator (ULPA filtration)"), "surgery",
   L("外科吊塔旁的手术烟雾排除器：四级过滤（预过滤、ULPA ≥ 99.9995 % @ 0.1–0.2 µm、活性炭），电刀激发时自动启动；AORN 要求排出并过滤所有手术烟雾。",
     "Surgical smoke evacuator beside the surgical pendant: four-stage filtration (pre-filter, ULPA ≥ 99.9995 % at 0.1–0.2 µm, activated carbon), auto-starting with electrosurgical activation; AORN: evacuate and filter all surgical smoke."),
   (0.46, 0.4, 0.9),
   [B("white", 0, 0.42, 0, 0.44, 0.8, 0.38), B("coal", -0.08, 0.7, 0.195, 0.2, 0.12, 0.006), B("screen-dark", -0.08, 0.7, 0.199, 0.17, 0.09, 0.004, name="screen"),
    B("blue", 0.12, 0.62, 0.195, 0.08, 0.08, 0.006), B("led-green", 0.12, 0.74, 0.195, 0.04, 0.02, 0.006), B("rubber", 0, 0.02, 0, 0.4, 0.04, 0.34)],
   interaction="device", solid=False, prompt=L("E · 烟雾排除器", "E · Smoke evacuator"), screen="text", tags=["or", "smoke", "energy"],
   behavior={"initial": "off",
             "states": {"off": st("关闭", "off"), "running": st("运行中（ULPA）", "running (ULPA)"), "filter-due": st("滤芯到期", "filter due", False)},
             "operations": {
                 "switch_on": op("开启（自动激发模式）", "Switch on (auto-activation mode)", ["off"], "running", [], TEAM, 5),
                 "switch_off": op("关闭", "Switch off", ["running"], "off", [], TEAM, 5),
             }})

eq("sc-count-board", L("手术清点板（RF 计数辅助）", "Surgical count board (RF count adjunct)"), "teaching",
   L("墙挂式清点板与 RF/条码计数系统读写器：纱布、缝针、器械在切皮前、关闭体腔前、关闭皮肤前及人员交接时清点（日本手术医学会《手术医疗实践指南》）；即使清点相符，最终清点前也用 RF 检测棒扫描患者（AORN）。",
     "Wall count board with the RF/barcode count reader: swabs, sharps and instruments counted before incision, before closing a cavity, before skin closure and at every staff hand-over (JAOM Practice Guidelines); even when the counts reconcile, the patient is scanned with the RF wand before the final count (AORN)."),
   (1.2, 0.08, 2.0),
   [B("white", 0, 1.45, -0.03, 1.12, 0.9, 0.02), B("sc-robot-accent", 0, 1.86, -0.017, 1.0, 0.06, 0.006)]
   + [B("coal", -0.3 + 0.3 * c, 1.7 - k * 0.1, -0.017, 0.24, 0.012, 0.004) for c in range(3) for k in range(6)]
   + [B("plastic", 0.42, 1.12, -0.025, 0.18, 0.22, 0.03), B("screen-dark", 0.42, 1.12, -0.009, 0.14, 0.12, 0.004, name="screen"),
      B("led-green", 0.42, 1.2, -0.008, 0.04, 0.03, 0.004)],
   interaction="device", solid=False, prompt=L("E · 清点", "E · Count"), screen="text", tags=["wall", "or", "count", "safety"],
   behavior={"initial": "not-started",
             "states": {"not-started": st("未开始", "not started"), "baseline": st("切皮前清点完成", "baseline counted (before incision)"),
                        "cavity": st("关体腔前清点完成", "counted before cavity closure"), "closing": st("关皮前清点完成", "counted before skin closure"),
                        "reconciled": st("最终清点相符（RF 扫描阴性）", "final count reconciled (RF scan clear)"), "discrepancy": st("清点不符：寻找 / X 线", "discrepancy: search / X-ray")},
             "operations": {
                 "baseline_count": op("切皮前清点（洗手护士与巡回护士唱点）", "Baseline count before incision (scrub and circulator aloud)", ["not-started"], "baseline", [{"actorWithin": 2.5}], CIRCULATOR, 120),
                 "handover_count": op("人员交接清点", "Count at a staff hand-over", ["baseline", "cavity", "closing"], None, [{"actorWithin": 2.5}], CIRCULATOR, 90),
                 "cavity_count": op("关闭体腔前清点", "Count before closing a cavity", ["baseline"], "cavity", [{"actorWithin": 2.5}], CIRCULATOR, 90),
                 "closing_count": op("关闭皮肤前清点", "Count before skin closure", ["baseline", "cavity"], "closing", [{"actorWithin": 2.5}], CIRCULATOR, 90),
                 "final_count": op("最终清点（需 RF 扫描阴性）", "Final count (needs a clear RF scan)", ["closing"], "reconciled",
                                   [{"actorWithin": 2.5}, near("sc-rf-wand", "clear", 6)], CIRCULATOR, 60),
                 "report_discrepancy": op("报告清点不符（寻找，必要时术中 X 线）", "Report a discrepancy (search; intra-operative X-ray if needed)", ["baseline", "cavity", "closing"], "discrepancy", [], CIRCULATOR, 30),
                 "resolve": op("找到缺失物品，重新清点", "Missing item found — recount", ["discrepancy"], "closing", [{"actorWithin": 2.5}], CIRCULATOR, 120),
                 "reset": op("下一台手术：清空清点板", "Next case: clear the board", ["reconciled"], "not-started", [], CIRCULATOR, 30),
             }})

eq("sc-rf-wand", L("RF 纱布检测棒", "RF surgical-sponge detection wand"), "surgery",
   L("射频检测棒：在关闭前扫描患者全身，检出遗留的 RFID 纱布；作为计数的辅助手段，即使清点相符也要扫描（AORN）。",
     "Radio-frequency wand: swept over the patient before closure to detect a retained RFID swab — the count adjunct, used even when the counts reconcile (AORN)."),
   (0.36, 0.08, 0.06),
   [B("plastic", -0.08, 0.025, 0, 0.18, 0.04, 0.05), B("sc-robot-accent", 0.08, 0.03, 0, 0.18, 0.05, 0.07), B("led-green", -0.12, 0.048, 0, 0.03, 0.004, 0.02)],
   interaction="device", solid=False, portable="handheld", reach=1.2, prompt=L("E · RF 检测棒", "E · RF wand"), tags=["or", "count", "rfid"],
   behavior={"initial": "ready",
             "states": {"ready": st("待用", "ready"), "clear": st("扫描阴性（无遗留）", "scan clear (nothing retained)")},
             "operations": {
                 "scan": op("扫描患者", "Scan the patient", ["ready"], "clear", [IN_HAND, AT_TABLE], CIRCULATOR, 45),
                 "reset": op("复位（下一台手术）", "Reset (next case)", ["clear"], "ready", [], CIRCULATOR, 5),
             }})

# ------------------------------------------------------------------------------------------------ existing devices
attach("sc-who-checklist", {
    "initial": "pending",
    "states": {"pending": st("待核查", "pending"), "signed-in": st("麻醉前核查完成（Sign in）", "signed in (before induction)"),
               "timed-out": st("切皮前暂停核查完成（Time out）", "timed out (before incision)"), "signed-out": st("离室前核查完成（Sign out）", "signed out (before leaving)")},
    "operations": {
        "sign_in": op("Sign in：核对身份、术式、部位标记、过敏、气道与失血风险", "Sign in: identity, procedure, site marking, allergies, airway and blood-loss risk",
                      ["pending"], "signed-in", [{"actorWithin": 3}], TEAM, 60),
        "time_out": op("Time out：全员暂停，确认患者、术式、部位，预防性抗菌药与影像（需切皮前清点完成）",
                       "Time out: the whole team pauses — patient, procedure, site, antibiotic prophylaxis, imaging (needs the baseline count)",
                       ["signed-in"], "timed-out", [{"actorWithin": 3}, near("sc-count-board", ["baseline", "cavity", "closing", "reconciled"], 8)], TEAM, 60),
        "sign_out": op("Sign out：术式记录、清点相符、标本标识、设备问题（需最终清点相符）",
                       "Sign out: procedure recorded, counts reconciled, specimens labelled, equipment problems (needs the reconciled count)",
                       ["timed-out"], "signed-out", [{"actorWithin": 3}, near("sc-count-board", "reconciled", 8)], TEAM, 60),
        "reset": op("下一台手术：新的核查表", "Next case: a fresh checklist", ["signed-out"], "pending", [], TEAM, 10),
    }}, prompt=L("E · 手术安全核查", "E · Surgical safety checklist"))

attach("sc-or-control-panel", {
    "initial": "operating",
    "states": {"operating": st("手术模式：≥ 25 次/h、+15 Pa、20–24 °C、35–60 % RH", "operating mode: ≥ 25 ACH, +15 Pa, 20–24 °C, 35–60 % RH"),
               "setback": st("夜间节能模式（保持正压）", "unoccupied set-back (pressure kept)")},
    "operations": {
        "check_room": op("核对环境参数（换气、压差、温湿度、层流、气体报警）", "Check the room (air changes, pressure, temperature, humidity, laminar flow, gas alarms)",
                         ["operating", "setback"], None, [], TEAM, 10),
        "set_setback": op("切换夜间节能模式", "Switch to unoccupied set-back", ["operating"], "setback", [], TEAM, 5),
        "set_operating": op("切换手术模式（开台前至少 15 分钟）", "Switch to operating mode (at least 15 min before the case)", ["setback"], "operating", [], TEAM, 900),
    }}, prompt=L("E · 环境控制面板", "E · OR control panel"))

attach("sc-surgical-pendant", {
    "initial": "standby",
    "states": {"standby": st("电刀待机", "generator standby"), "monitored": st("负极板接触监测正常", "return electrode monitored"),
               "ready": st("电刀就绪（输出已启用）", "generator ready (output enabled)")},
    "operations": {
        "check_return_electrode": op("贴负极板并确认接触质量监测（REM/CQM）", "Place the return electrode and confirm contact-quality monitoring (REM/CQM)",
                                     ["standby"], "monitored", [AT_TABLE], TEAM, 45),
        "enable_output": op("启用电刀输出（需烟雾排除器运行）", "Enable generator output (needs the smoke evacuator running)",
                            ["monitored"], "ready", [near("sc-smoke-evacuator", "running", 4)], TEAM, 10),
        "standby": op("电刀待机", "Generator to standby", ["ready"], "monitored", [], TEAM, 5),
        "remove_return_electrode": op("移除负极板，检查皮肤", "Remove the return electrode and check the skin", ["monitored"], "standby", [AT_TABLE], TEAM, 30),
    }}, prompt=L("E · 电刀主机 / 气腹机", "E · Generator / insufflator"))

attach("sc-laparoscopy-tower", {
    "initial": "off",
    "states": {"off": st("关闭", "off"), "on": st("开机自检完成", "on (self-test passed)"), "balanced": st("已白平衡", "white-balanced"),
               "insufflating": st("气腹中（压力按术式设定）", "insufflating (pressure set for the procedure)")},
    "operations": {
        "power_on": op("开机自检", "Power on and self-test", ["off"], "on", [], TEAM, 30),
        "white_balance": op("白平衡", "White balance", ["on"], "balanced", [], TEAM, 10),
        "start_insufflation": op("开始气腹", "Start insufflation", ["balanced"], "insufflating", [AT_TABLE], SURGEON, 60),
        "stop_insufflation": op("停止气腹并排气", "Stop insufflation and desufflate", ["insufflating"], "balanced", [], TEAM, 30),
        "power_off": op("关机", "Power off", ["on", "balanced"], "off", [], TEAM, 5),
    }}, prompt=L("E · 腹腔镜系统", "E · Laparoscopy tower"))

attach("sc-lead-shield", {
    "initial": "stowed",
    "states": {"stowed": st("收起", "stowed"), "in-place": st("已就位（术者与球管之间）", "in place (between the operator and the tube)")},
    "operations": {
        "position": op("拉到术者与球管之间", "Bring between the operator and the tube", ["stowed"], "in-place", [], IMAGING + ["nurse"], 10),
        "stow": op("收起", "Stow", ["in-place"], "stowed", [], IMAGING + ["nurse"], 5),
    }}, prompt=L("E · 铅屏风", "E · Lead shield"))

attach("sc-contrast-injector", {
    "initial": "empty",
    "states": {"empty": st("未装药", "empty"), "loaded": st("已装造影剂", "loaded"), "armed": st("已排气并上锁", "air purged, armed")},
    "operations": {
        "load": op("装造影剂（无菌操作）", "Load contrast (aseptic)", ["empty"], "loaded", [{"handsClean": True}], IMAGING + ["nurse"], 60),
        "purge_and_arm": op("排气并上锁（确认管路无气泡）", "Purge air and arm (no bubbles in the line)", ["loaded"], "armed", [], IMAGING + ["nurse"], 20),
        "inject": op("透视下注射（需穿铅衣、铅屏风就位）", "Inject under fluoroscopy (lead apron on, shield in place)", ["armed"], "empty",
                     [{"actorHolding": "sc-lead-apron"}, near("sc-lead-shield", "in-place", 4)], IMAGING, 20),
    }}, prompt=L("E · 高压注射器", "E · Contrast injector"))

attach("sc-washer-disinfector", {
    "initial": "idle",
    "states": {"idle": st("空闲", "idle"), "loaded": st("已装载（去污侧）", "loaded (dirty side)"),
               "complete": st("程序完成：A0 ≥ 3000，已干燥（清洁侧）", "cycle complete: A0 ≥ 3000, dried (clean side)")},
    "operations": {
        "load": op("在去污侧装载器械", "Load instruments on the dirty side", ["idle"], "loaded", [], CSSD, 60),
        "run_cycle": op("运行清洗消毒程序（ISO 15883-1:2024）", "Run the wash–disinfect cycle (ISO 15883-1:2024)", ["loaded"], "complete", [], CSSD, 600),
        "unload": op("在清洁侧卸载", "Unload on the clean side", ["complete"], "idle", [], CSSD, 60),
    }}, prompt=L("E · 清洗消毒器", "E · Washer-disinfector"))

attach("sc-steam-steriliser", {
    "initial": "idle",
    "states": {"idle": st("空闲（待 B-D 试验）", "idle (Bowie-Dick due)"), "tested": st("B-D 试验通过", "Bowie-Dick passed"),
               "cycle-complete": st("134 °C 程序完成", "134 °C cycle complete"), "released": st("指示物合格，已放行", "indicators passed, load released")},
    "operations": {
        "bowie_dick": op("B-D 空气排除试验（每日首锅）", "Bowie-Dick air-removal test (first cycle of the day)", ["idle"], "tested", [], CSSD, 240),
        "run_cycle": op("运行 134 °C 脉动真空程序（EN 285、ISO 17665）", "Run the 134 °C pre-vacuum cycle (EN 285, ISO 17665)", ["tested"], "cycle-complete", [], CSSD, 900),
        "release": op("核对物理参数与化学/生物指示物后放行", "Check physical parameters and chemical / biological indicators, release the load", ["cycle-complete"], "released", [], CSSD, 60),
        "unload": op("卸载到无菌存放区", "Unload into sterile storage", ["released"], "tested", [], CSSD, 60),
    }}, prompt=L("E · 压力蒸汽灭菌器", "E · Steam steriliser"))
