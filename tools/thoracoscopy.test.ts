/**
 * IMPF Surgery Hospital: thoracoscopy on ClinicalCraft's world runtime (docs/THORACOSCOPY.md) — the thoracic theatre's
 * rules on a patient in OR 5, and the whole sequence of a thoracoscopic lobectomy on the training station in the
 * simulation OR. Every act goes through the action bus, exactly as for the learner, an agent or a colleague.
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/world/src/` for the run and removes it afterwards.
 *
 *   1. the tube's position is confirmed before the patient is turned, and one lung is ventilated only after the
 *      position has been checked — the anaesthetist at the head, the team at the table;
 *   2. no port before the time-out and before the lung is down; no picture before the white balance; no energy
 *      without smoke evacuation; a stapler fires once per reload;
 *   3. the drain: the unit primed before the tube goes in, connected only to a tube that is in, and the lung
 *      re-expanded only with the drain on its seal;
 *   4. the training station: every step in order, each with the instrument it needs in the hand, the camera
 *      white-balanced, smoke evacuation running, the drainage unit primed and the count done before closing — and
 *      its patient simulator: the world's own figure on its side, not a shape of the model;
 *   6. the 2026-11-12 audit: one view for every screen and every step under vision (the tower off, its light on
 *      standby, the scope withdrawn); a stapler fires only with a reload in, that stapler's, by the role the step is
 *      assessed for (in practice mode a stand-in is a labelled substitution); the drainage unit connected to that chest
 *      tube, by instance; each trainee's run its own — no incision before the Time Out and the count, the instructor's
 *      presets put back by the reset, a run record of who did what with which instrument; and the release scenario
 *      (a loss of view, then an empty stapler);
 *   5. what is drawn of the station follows the operation (ClinicalCraft docs/FACILITIES.md "A look for each state"):
 *      each step has a look — the simulator under a blanket or draped, ventilated on both lungs or one, the monitor
 *      dark or showing the scope's picture, the layers of the model (marks, ports, scope, drain, dressings) — the
 *      model has exactly those layers, and whoever moves the station on, the learner or a colleague, the look is the
 *      state's.
 *
 * The pack directory comes from $SURGERYCRAFT_CONTENT.
 */
import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { capabilityLabels, compileFacility, lookLayers, lookOf, parseCatalog, parseFacility, parseGlb, parseRoomTemplate, type EquipmentType, type FacilityDefinition, type RoomTemplate } from "@clinicalcraft/core";
import { PRIMARY_ACTOR, type NavGoal, type WorldActionResult } from "./contracts.js";
import { makeWorld, type TestWorld } from "./__fixtures__/world.js";

const CC = new URL("../../content/", import.meta.url).pathname;
const SC = `${process.env.SURGERYCRAFT_CONTENT ?? ""}/`;
const json = (p: string) => JSON.parse(readFileSync(p, "utf8"));
const catalogs = [
  ...["materials", "core-clinical", "core-diagnostics", "core-furniture"].map((id) => `${CC}catalogs/${id}.json`),
  `${SC}catalogs/surgerycraft-or.json`,
].map((f) => {
  const r = parseCatalog(json(f));
  if (!r.ok) throw new Error(`${f}: ${JSON.stringify(r.issues).slice(0, 400)}`);
  return r.value;
});
const templates: RoomTemplate[] = [CC, SC].flatMap((dir) =>
  readdirSync(`${dir}templates`)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const r = parseRoomTemplate(json(`${dir}templates/${f}`));
      if (!r.ok) throw new Error(f);
      return r.value;
    }),
);
const parsed = parseFacility(json(`${SC}facilities/impf-surgery-hospital.json`));
if (!parsed.ok) throw new Error(JSON.stringify(parsed.issues));
const compiled = compileFacility(parsed.value, templates);
if (!compiled.ok) throw new Error(JSON.stringify(compiled.issues));
const F: FacilityDefinition = compiled.facility;

const A = PRIMARY_ACTOR;
const ANAESTHETIST = "staff:or-5.anaesthetist";
const CIRCULATOR = "staff:or-5.circulating-nurse";
const eq = (id: string) => `eq:${id}`;
const or5 = (id: string) => eq(`or-5.${id}`);
const sim = (id: string) => eq(`l0-sim-or.${id}`);
// the operating-room case of the built-in library, its patient on the table of the thoracic theatre (or elsewhere)
const world = (slotId = "or-5.slot"): TestWorld => makeWorld("cmcr-1653406", { facility: F, catalogs, slotId });

/** An act that must complete; a refusal that is only about distance is walked first (as the browser and agents do). */
async function done(w: TestWorld, actorId: string, operation: string, targetId?: string, parameters?: Record<string, unknown>, goal?: NavGoal): Promise<WorldActionResult> {
  const request = { actorId, operation, ...(targetId ? { targetId } : {}), ...(parameters ? { parameters } : {}), ...(goal ? { goal } : {}) };
  let r = await w.act(request);
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE"); i++) {
    const walk = await w.act({ actorId, operation: "navigate", goal: r.hint.goal });
    expect(walk.status, walk.message).toBe("completed");
    r = await w.act(request);
  }
  expect(r.status, `${operation} ${targetId ?? ""}: ${r.message}`).toBe("completed");
  return r;
}

/** An act refused for a reason (after any walk it needed): its result. */
async function refused(w: TestWorld, actorId: string, operation: string, targetId: string, code = "PRECONDITION_FAILED"): Promise<WorldActionResult> {
  let r = await w.act({ actorId, operation, targetId });
  if (r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE")) {
    expect((await w.act({ actorId, operation: "navigate", goal: r.hint.goal })).status).toBe("completed");
    r = await w.act({ actorId, operation, targetId });
  }
  expect(r, r.message).toMatchObject({ status: "failed", errorCode: code });
  return r;
}

const state = (w: TestWorld, id: string) => w.runtime.inspect(A, id)?.state;
const lifecycle = (w: TestWorld, id: string) => w.runtime.snapshot().entities[id]?.state;

async function take(w: TestWorld, id: string, actor = A): Promise<void> {
  await done(w, actor, "approach", id);
  await done(w, actor, "pick_up", id);
}
const putDown = (w: TestWorld, id: string, actor = A) => done(w, actor, "put_down", id);

async function scrubAndGown(w: TestWorld, room: (id: string) => string): Promise<void> {
  await done(w, A, "wash_hands", room("sanitizer"));
  for (const id of [room("gown"), room("gloves")]) {
    await take(w, id);
    await done(w, A, "equip", id);
  }
}

async function timeOut(w: TestWorld): Promise<void> {
  await done(w, A, "sign_in", or5("checklist"));
  await done(w, CIRCULATOR, "baseline_count", or5("count-board"));
  await done(w, A, "time_out", or5("checklist"));
}

/** Anaesthesia and positioning for a thoracoscopy: tube placed and confirmed, the patient turned, flexed and checked, one lung. */
async function lungDown(w: TestWorld): Promise<void> {
  await done(w, ANAESTHETIST, "place_tube", or5("lung-isolation"));
  await done(w, ANAESTHETIST, "confirm_position", or5("lung-isolation"));
  for (const op of ["turn", "flex_table", "check_position"]) await done(w, CIRCULATOR, op, or5("positioning"));
  await done(w, ANAESTHETIST, "isolate", or5("lung-isolation"));
}

describe("IMPF Surgery Hospital · thoracoscopy in the thoracic theatre (OR 5)", () => {
  it("the theatre is set up for it: the tower white-balanced, the instruments laid out, the drain and the carts in place", () => {
    const w = world();
    expect(state(w, or5("vats-tower"))).toBe("balanced");
    expect(state(w, or5("lung-isolation"))).toBe("two-lung");
    expect(state(w, or5("positioning"))).toBe("stowed");
    expect(state(w, or5("chest-drain"))).toBe("sealed");
    const laid = F.placements.filter((p) => p.room === "or-5" && p.id.startsWith("or-5.vats-")).map((p) => p.type).sort();
    expect(laid).toEqual(["sc-chest-tube", "sc-clip-applier", "sc-endo-dissector", "sc-endo-stapler", "sc-lung-forceps", "sc-specimen-bag", "sc-sterile-setup-table",
      "sc-thoracoport", "sc-thoracoscope", "sc-thoracoscopy-tower", "sc-ultrasonic-shears"]);
    // both boom displays and the tower show the camera's picture
    const byType = new Map(catalogs.flatMap((c) => c.equipment).map((e) => [e.id, e]));
    const screens = F.placements.filter((p) => p.room === "or-5" && byType.get(p.type)?.screen === "thoracoscopy").map((p) => p.id).sort();
    expect(screens).toEqual(["or-5.display-1", "or-5.display-2", "or-5.vats-tower"]);
    // what the tower gives is named for what it is — an endoscope's camera and its light, not a laparoscope's
    expect(capabilityLabels(byType.get("sc-thoracoscopy-tower")!.capabilities, "en")).toEqual(["an endoscopic camera", "a light source"]);
    expect(capabilityLabels(byType.get("sc-thoracoscopy-tower")!.capabilities, "zh-CN")).toEqual(["内镜摄像系统", "冷光源"]);
  });

  it("the tube is confirmed before the patient is turned; one lung only after the position is checked", async () => {
    const w = world();
    // on their back with no tube confirmed: no turning
    const early = await refused(w, CIRCULATOR, "turn", or5("positioning"));
    expect(early.message).toMatch(/Lung-isolation cart/);
    expect(early.hint?.goal).toMatchObject({ kind: "interact", id: or5("lung-isolation") });
    await done(w, ANAESTHETIST, "place_tube", or5("lung-isolation"));
    await refused(w, CIRCULATOR, "turn", or5("positioning"));
    await done(w, ANAESTHETIST, "confirm_position", or5("lung-isolation"));
    // confirmed, but the patient still supine: the lung is not let down yet
    const flat = await refused(w, ANAESTHETIST, "isolate", or5("lung-isolation"));
    expect(flat.message).toMatch(/Lateral-positioning aids/);
    expect(flat.hint?.goal).toMatchObject({ id: or5("positioning") });
    await done(w, CIRCULATOR, "turn", or5("positioning"));
    await done(w, CIRCULATOR, "flex_table", or5("positioning"));
    // turned and flexed, the position not yet checked (the tube moves when a patient is turned)
    await refused(w, ANAESTHETIST, "isolate", or5("lung-isolation"));
    await done(w, CIRCULATOR, "check_position", or5("positioning"));
    await done(w, ANAESTHETIST, "isolate", or5("lung-isolation"));
    expect(state(w, or5("lung-isolation"))).toBe("one-lung");
    expect(state(w, or5("positioning"))).toBe("checked");
  });

  it("no port before the time-out and the lung down; no picture before the white balance", async () => {
    const w = world();
    await scrubAndGown(w, or5);
    await take(w, or5("vats-port"));
    // scrubbed and gowned at the table, but no time-out
    const noTimeOut = await refused(w, A, "place", or5("vats-port"));
    expect(noTimeOut.message).toMatch(/WHO Surgical Safety Checklist/);
    await timeOut(w);
    // timed out, both lungs still ventilated: the port would go into an inflated lung
    const inflated = await refused(w, A, "place", or5("vats-port"));
    // (the world's own sentence, as docs/THORACOSCOPY.md quotes it)
    expect(inflated.message).toBe('Place the camera port needs the nearby "Lung-isolation cart (double-lumen tubes & flexible bronchoscope)" to be on one-lung ventilation (the operated lung down) (it is on both lungs).');
    expect(inflated.hint?.goal).toMatchObject({ id: or5("lung-isolation") });
    await lungDown(w);
    await done(w, A, "place", or5("vats-port"));
    expect(lifecycle(w, or5("vats-port"))).toBe("in-use");

    // the scope: the camera system on and white-balanced first
    await take(w, or5("vats-scope"));
    await done(w, CIRCULATOR, "power_off", or5("vats-tower"));
    const dark = await refused(w, A, "insert", or5("vats-scope"));
    expect(dark.message).toMatch(/thoracoscopy tower/i);
    await done(w, CIRCULATOR, "power_on", or5("vats-tower"));
    await refused(w, A, "insert", or5("vats-scope"));
    await done(w, CIRCULATOR, "white_balance", or5("vats-tower"));
    // the tower and both boom displays show a picture only once the scope is in the chest (one view: `screenNeeds`)
    const screens = () => [or5("vats-tower"), or5("display-1"), or5("display-2")].map((id) => w.runtime.screenOf(id));
    expect(screens()).toEqual(["none", "none", "none"]);
    await done(w, A, "insert", or5("vats-scope"));
    expect(lifecycle(w, or5("vats-scope"))).toBe("in-chest");
    expect(screens()).toEqual(["thoracoscopy", "thoracoscopy", "thoracoscopy"]);
    // withdrawn to clean the lens: every screen dark until it is back in
    await done(w, A, "withdraw", or5("vats-scope"));
    expect(screens()).toEqual(["none", "none", "none"]);
  });

  it("energy needs smoke evacuation; a stapler fires once for each reload", async () => {
    const w = world();
    await scrubAndGown(w, or5);
    await take(w, or5("vats-shears"));
    const smoke = await refused(w, A, "activate", or5("vats-shears"));
    expect(smoke.message).toMatch(/smoke evacuator/i);
    expect(smoke.hint?.goal).toMatchObject({ id: or5("smoke-evac") });
    await done(w, CIRCULATOR, "switch_on", or5("smoke-evac"));
    await done(w, A, "activate", or5("vats-shears"));
    await done(w, A, "discard", or5("vats-shears"));
    await putDown(w, or5("vats-shears"));

    await take(w, or5("vats-stapler"));
    // no reload in: nothing to fire
    expect((await w.act({ actorId: A, operation: "fire", targetId: or5("vats-stapler") })).status).toBe("failed");
    await done(w, A, "load", or5("vats-stapler"));
    await done(w, A, "fire", or5("vats-stapler"));
    expect(lifecycle(w, or5("vats-stapler"))).toBe("fired");
    expect((await w.act({ actorId: A, operation: "fire", targetId: or5("vats-stapler") })).status).toBe("failed");
    await done(w, A, "load", or5("vats-stapler"));
    expect(lifecycle(w, or5("vats-stapler"))).toBe("loaded");
  });

  it("the drain: the unit primed before the tube goes in, connected to a tube that is in, the lung re-expanded on the seal", async () => {
    const w = world();
    await lungDown(w);
    await scrubAndGown(w, or5);
    await take(w, or5("vats-chest-tube"));
    // the unit still in its pack: no tube yet
    const unprimed = await refused(w, A, "place", or5("vats-chest-tube"));
    expect(unprimed.message).toMatch(/Chest drainage unit/);
    expect(unprimed.hint?.goal).toMatchObject({ id: or5("chest-drain") });
    await done(w, CIRCULATOR, "prime", or5("chest-drain"));
    // primed, the tube not in: nothing to connect to, and the lung stays down
    const noTube = await refused(w, CIRCULATOR, "connect", or5("chest-drain"));
    expect(noTube.message).toMatch(/Chest tube/);
    const notSealed = await refused(w, ANAESTHETIST, "re_expand", or5("lung-isolation"));
    expect(notSealed.message).toMatch(/Chest drainage unit/);
    await done(w, A, "place", or5("vats-chest-tube"));
    await done(w, CIRCULATOR, "connect", or5("chest-drain"));
    expect(state(w, or5("chest-drain"))).toBe("water-seal");
    // connected by instance: the unit and the tube each name the other; disconnected, the lung stays down
    const links = (id: string) => (w.runtime.snapshot().entities[id]?.data?.links as string[] | undefined) ?? [];
    expect([links(or5("chest-drain")), links(or5("vats-chest-tube"))]).toEqual([[or5("vats-chest-tube")], [or5("chest-drain")]]);
    await done(w, CIRCULATOR, "disconnect", or5("chest-drain"));
    expect([state(w, or5("chest-drain")), links(or5("chest-drain"))]).toEqual(["primed", []]);
    await refused(w, ANAESTHETIST, "re_expand", or5("lung-isolation"));
    await done(w, CIRCULATOR, "connect", or5("chest-drain"));
    await done(w, ANAESTHETIST, "re_expand", or5("lung-isolation"));
    expect(state(w, or5("lung-isolation"))).toBe("re-expanded");
    // suction only as prescribed, and back
    await done(w, CIRCULATOR, "apply_suction", or5("chest-drain"));
    await done(w, CIRCULATOR, "to_water_seal", or5("chest-drain"));
    await done(w, CIRCULATOR, "return_supine", or5("positioning"));
    expect(state(w, or5("positioning"))).toBe("stowed");
  });
});

describe("IMPF Surgery Hospital · the thoracoscopy training station (simulation OR)", () => {
  const T = eq("l0-sim-vats-trainer");
  const CONSOLE = eq("l0-sim-vats-console");
  const NURSE = "staff:l0-sim-or.circulating-nurse";
  const FACULTY_ANAESTHETIST = "staff:l0-sim-or.anaesthetist";
  const item = (name: string) => sim(`vats-${name}`);
  const trainer = (): EquipmentType => catalogs.flatMap((c) => c.equipment).find((e) => e.id === "sc-vats-trainer")!;
  /** The station's steps in order, as its behaviour lists them. */
  const STEPS = ["ready", "positioned", "lung-down", "camera-port", "explored", "working-ports", "mobilised", "hilum", "vein-divided", "artery-divided", "bronchus-divided", "lobe-free", "specimen-out", "nodes", "leak-tested", "drained", "re-expanded", "closed"];
  /** Every picture of the scope in the simulation OR: the station's monitor, the tower, the two boom displays. */
  const SCREENS = [T, sim("vats-tower"), sim("display-1"), sim("display-2")];
  const screens = (w: TestWorld) => SCREENS.map((id) => w.runtime.screenOf(id));
  const LIVE = SCREENS.map(() => "thoracoscopy");
  const DARK = SCREENS.map(() => "none");

  /** The team's checks before the first incision, on the drill's own boards: the Sign In, the count before incision, the Time Out. */
  async function checks(w: TestWorld): Promise<void> {
    await done(w, A, "sign_in", sim("checklist"));
    await done(w, NURSE, "baseline_count", sim("count-board"));
    await done(w, A, "time_out", sim("checklist"));
  }
  /** The trainee scrubbed, gowned and gloved (once: the simulation OR has one gown and one pair of gloves laid out). */
  async function scrubbed(w: TestWorld): Promise<void> {
    if (w.runtime.snapshot().entities[sim("gown")]?.heldBy !== A) await scrubAndGown(w, sim);
  }
  /** An instrument's own lifecycle state (one never used is still as laid out: sterile). */
  const own = (w: TestWorld, id: string) => lifecycle(w, id) ?? "sterile";
  /** The surgeon's step with an instrument in hand (a stapler is loaded first: one reload for each firing). */
  async function withItem(w: TestWorld, name: string, operation: string, actor = A): Promise<void> {
    await take(w, item(name), actor);
    if (name === "stapler") await done(w, actor, "load", item(name));
    await done(w, actor, operation, T);
    await putDown(w, item(name), actor);
  }
  /** The canonical drill, each step leading to the station state it names (the station as found → closed). */
  const SEQUENCE: [string, (w: TestWorld) => Promise<unknown>][] = [
    ["positioned", (w) => done(w, A, "check_position", T)],
    ["lung-down", (w) => done(w, A, "isolate_lung", T)],
    ["camera-port", async (w) => {
      await scrubbed(w);
      await checks(w);
      await withItem(w, "port", "place_camera_port");
    }],
    ["explored", (w) => withItem(w, "scope", "explore")],
    ["working-ports", (w) => done(w, A, "place_working_ports", T)],
    ["mobilised", async (w) => {
      await done(w, A, "switch_on", sim("smoke-evac"));
      await withItem(w, "shears", "free_adhesions");
    }],
    ["hilum", (w) => withItem(w, "dissector", "dissect_hilum")],
    ["vein-divided", (w) => withItem(w, "stapler", "divide_vein")],
    ["artery-divided", (w) => withItem(w, "clip-applier", "divide_artery")],
    ["bronchus-divided", (w) => withItem(w, "stapler", "divide_bronchus")],
    ["lobe-free", (w) => withItem(w, "stapler", "complete_fissure")],
    ["specimen-out", (w) => withItem(w, "bag", "retrieve_specimen")],
    ["nodes", (w) => withItem(w, "shears", "take_nodes")],
    ["leak-tested", (w) => done(w, A, "leak_test", T)],
    ["drained", async (w) => {
      await done(w, A, "prime", sim("chest-drain"));
      await withItem(w, "chest-tube", "place_drain");
    }],
    ["re-expanded", async (w) => {
      await done(w, A, "connect", sim("chest-drain"));
      await done(w, A, "re_expand", T);
    }],
    ["closed", async (w) => {
      await done(w, A, "cavity_count", sim("count-board"));
      await done(w, A, "close", T);
    }],
  ];
  /** Work the drill from where the station is up to `until` (a station state). */
  async function drill(w: TestWorld, until: string): Promise<void> {
    for (const [to, run] of SEQUENCE) {
      if (STEPS.indexOf(w.runtime.stateOf(T)!) >= STEPS.indexOf(to)) continue;
      await run(w);
      expect(w.runtime.stateOf(T), `after the step to ${to}`).toBe(to);
      if (to === until) return;
    }
  }

  it("stands where the simulation OR's table would, with the theatre's thoracoscopy equipment round it, the drill's own boards and no patient place", () => {
    const station = F.placements.find((p) => p.id === "l0-sim-vats-trainer");
    expect(station).toMatchObject({ type: "sc-vats-trainer", room: "l0-sim-or" });
    expect(F.placements.some((p) => p.id === "l0-sim-or.table")).toBe(false);
    expect(F.patientSlots.some((s) => s.room === "l0-sim-or")).toBe(false);
    for (const id of ["vats-tower", "chest-drain", "smoke-evac", "count-board", "vats-port", "vats-scope", "vats-stapler", "display-1", "display-2"]) expect(F.placements.some((p) => p.id === `l0-sim-or.${id}`), id).toBe(true);
    // an isolated skills drill writes no patient's record: its checklist and count board are the training ones, with
    // the theatre's state machines and looks; the instructor's console stands beside the station
    const typeOf = (id: string) => F.placements.find((p) => p.id === id)?.type;
    expect([typeOf("l0-sim-or.checklist"), typeOf("l0-sim-or.count-board"), typeOf("l0-sim-vats-console")]).toEqual(["sc-training-checklist", "sc-training-count-board", "sc-vats-console"]);
    const byType = new Map(catalogs.flatMap((c) => c.equipment).map((e) => [e.id, e]));
    for (const [training, theatre] of [["sc-training-checklist", "sc-who-checklist"], ["sc-training-count-board", "sc-count-board"]] as const) {
      expect(byType.get(training)!.behavior!.derived).toBeUndefined();
      expect(Object.values(byType.get(training)!.behavior!.operations).some((o) => o.clinical)).toBe(false);
      expect(Object.keys(byType.get(training)!.behavior!.states)).toEqual(Object.keys(byType.get(theatre)!.behavior!.states));
      expect(byType.get(training)!.model?.uri).toBe(byType.get(theatre)!.model?.uri);
    }
  });

  it("its patient simulator is the world's own figure, not a shape of the model: on its right side over the break of the flexed table, asleep — found under a blanket, ventilated on both lungs", () => {
    const type = trainer();
    // one of the figures the people of the world are drawn as (ClinicalCraft docs/FACILITIES.md "A body drawn with equipment")
    expect(type.manikin).toMatchObject({ posture: "lateral", sideUp: "left", cover: "blanket", breathing: "both", flex: 9, asleep: true, rot: 90 });
    expect(type.manikin).not.toHaveProperty("draped");
    const m = type.manikin!;
    // on the station: inside its footprint, on the mattress, the head towards the anaesthetic end (−x of the type)
    expect(Math.abs(m.x)).toBeLessThan(type.footprint.w / 2);
    expect(Math.abs(m.z)).toBeLessThan(type.footprint.d / 2);
    expect(m.y).toBeGreaterThan(0.85);
    expect(m.y).toBeLessThan(1.05);
    // it is nobody: no particular woman or man, nothing of a case
    expect(m.appearance?.presentation).toBe("neutral");
    // and the model has no body of its own any more: no part in a manikin's material, no such material in the pack
    expect(type.parts.some((p) => /manikin/.test(p.m))).toBe(false);
    expect(catalogs.flatMap((c) => c.materials).some((mat) => /manikin/.test(mat.id))).toBe(false);
    // the station is still a device of the world, and still no patient's place
    expect(type.interaction.kind).toBe("device");
    expect(type.screen).toBe("thoracoscopy");
  });

  it("what is drawn of it follows the operation: a look for each step — the cover, the breathing, the monitor, the layers of its model", () => {
    const type = trainer();
    expect(Object.keys(type.behavior!.states)).toEqual(STEPS);
    for (const s of STEPS) expect(type.behavior!.states[s]!.look, s).toBeDefined();
    // the model has the layers the looks show, and no other (tools/blender/thoracic_models.py builds them)
    const info = parseGlb(new Uint8Array(readFileSync(`${SC}assets/${type.model!.uri}`)));
    expect(info.layers).toEqual(lookLayers(type));
    expect(info.layers).toHaveLength(12);
    const look = (s: string) => lookOf(type, s);
    // a blanket and both lungs before and after; draped from the moment the lung is let down; one lung until it is up again
    expect(STEPS.map((s) => `${look(s).manikin!.cover} ${look(s).manikin!.breathing}`)).toEqual([
      "blanket both", "blanket both",
      ...Array(14).fill("drapes one-lung"),
      "drapes both", "blanket both",
    ]);
    // the monitor may show the scope's picture while the scope is in the chest — from the look round to the lung
    // re-expanded — and does only while the view is there (`screenNeeds`: one view, below)
    expect(STEPS.filter((s) => look(s).screen === "thoracoscopy")).toEqual(STEPS.slice(STEPS.indexOf("explored"), STEPS.indexOf("re-expanded") + 1));
    expect(STEPS.filter((s) => look(s).screen === "none")).toEqual(["ready", "positioned", "lung-down", "camera-port", "closed"]);
    expect(type.screenNeeds).toEqual([
      { nearbyState: { type: "sc-thoracoscopy-tower", state: "balanced", within: 7 } },
      { nearbyState: { type: "sc-thoracoscope", state: "in-chest", within: 7 } },
    ]);
    // what a step puts on the chest stays until a later step takes it away
    const span = (layer: string) => STEPS.filter((s) => look(s).layers.includes(layer));
    const from = (a: string, b: string) => STEPS.slice(STEPS.indexOf(a), STEPS.indexOf(b) + 1);
    expect(span("lines")).toEqual(from("positioned", "closed"));
    expect(span("site-camera")).toEqual(["positioned", "lung-down"]);
    expect(span("site-working")).toEqual(from("positioned", "explored"));
    expect(span("camera-port")).toEqual(from("camera-port", "leak-tested"));
    expect(span("scope")).toEqual(from("explored", "leak-tested"));
    expect(span("working-ports")).toEqual(from("working-ports", "re-expanded"));
    expect(span("retractor")).toEqual([...from("mobilised", "lobe-free"), "nodes"]);
    expect(span("mayo")).toEqual(from("lung-down", "re-expanded"));
    expect(span("specimen")).toEqual(from("specimen-out", "re-expanded"));
    expect(span("chest-tube")).toEqual(from("drained", "closed"));
    expect(span("scope-utility")).toEqual(["drained", "re-expanded"]);
    expect(span("dressings")).toEqual(["closed"]);
    for (const s of STEPS) {
      const l = look(s).layers;
      // one scope at a time; the drain takes the camera port's incision; a site marked is a site not yet cut
      expect(l.includes("scope") && l.includes("scope-utility"), s).toBe(false);
      expect(l.includes("camera-port") && l.includes("chest-tube"), s).toBe(false);
      expect(l.includes("site-camera") && l.includes("camera-port"), s).toBe(false);
      expect(l.includes("site-working") && l.includes("working-ports"), s).toBe(false);
      // the body stays where the model was built round it: a step covers it differently and changes its breathing, never moves it
      for (const k of Object.keys(type.behavior!.states[s]!.look?.manikin ?? {})) expect(["cover", "breathing", "asleep"], `${s}.${k}`).toContain(k);
    }
  });

  it("a colleague moves it on the same way, and the look is the state's: the faculty nurse checks the position, the faculty anaesthetist lets the lung down", async () => {
    const type = trainer();
    const w = world("or-7.slot");
    const seen: string[] = [];
    w.runtime.subscribe((e) => {
      if (e.type === "entity.state" && e.entityId === T) seen.push(`${e.actorId}: ${e.from} → ${e.to}`);
    });
    expect(w.runtime.stateOf(T)).toBe("ready");
    await done(w, NURSE, "check_position", T);
    expect(lookOf(type, w.runtime.stateOf(T))).toMatchObject({ layers: ["lines", "site-camera", "site-working"], screen: "none", manikin: { cover: "blanket", breathing: "both" } });
    await done(w, FACULTY_ANAESTHETIST, "isolate_lung", T);
    expect(lookOf(type, w.runtime.stateOf(T))).toMatchObject({ screen: "none", manikin: { cover: "drapes", breathing: "one-lung" } });
    // the events a scene follows say who moved it on; the learner carries on from there, after the team's checks
    expect(seen).toEqual([`${NURSE}: ready → positioned`, `${FACULTY_ANAESTHETIST}: positioned → lung-down`]);
    await checks(w);
    await take(w, item("port"));
    await done(w, A, "place_camera_port", T);
    expect(seen.at(-1)).toBe(`${A}: lung-down → camera-port`);
    expect(lookOf(type, w.runtime.stateOf(T)).layers).toContain("camera-port");
  });

  it("the whole sequence in order — each step by the role it is assessed for, its instrument in hand, under vision, a reload for each firing, the drain connected, the counts done", async () => {
    // the case's patient is upstairs in OR 7: the station needs none
    const w = world("or-7.slot");
    // the station's state after each step, as the world has it (`stateOf`: what the scene draws) and as its inspection says
    const passed: string[] = [];
    w.runtime.subscribe((e) => {
      if (e.type === "entity.state" && e.entityId === T && e.to) passed.push(e.to);
    });
    expect(state(w, T)).toBe("ready");
    // a step out of order is not offered
    expect((await w.act({ actorId: A, operation: "explore", targetId: T })).status).toBe("failed");
    await drill(w, "lung-down");
    // the first incision waits for the team's checks: no Time Out, no port — and the Time Out waits for the count
    await scrubbed(w);
    await take(w, item("port"));
    const unchecked = await refused(w, A, "place_camera_port", T);
    expect(unchecked.message).toMatch(/WHO Surgical Safety Checklist \(training\)/);
    await done(w, A, "sign_in", sim("checklist"));
    const uncounted = await refused(w, A, "time_out", sim("checklist"));
    expect(uncounted.hint?.goal).toMatchObject({ id: sim("count-board") });
    await done(w, NURSE, "baseline_count", sim("count-board"));
    await done(w, A, "time_out", sim("checklist"));
    await done(w, A, "place_camera_port", T);
    // the port used at the station is that port, in use
    expect(lifecycle(w, item("port"))).toBe("in-use");
    await putDown(w, item("port"));

    // the scope, with the camera system white-balanced: no picture before
    await take(w, item("scope"));
    await done(w, A, "power_off", sim("vats-tower"));
    const dark = await refused(w, A, "explore", T);
    expect(dark.message).toMatch(/thoracoscopy tower/i);
    await done(w, A, "power_on", sim("vats-tower"));
    await done(w, A, "white_balance", sim("vats-tower"));
    expect(screens(w)).toEqual(DARK);
    await done(w, A, "explore", T);
    // that scope is in the chest — on its holder once put down — and every screen shows its picture
    expect(lifecycle(w, item("scope"))).toBe("in-chest");
    await putDown(w, item("scope"));
    expect(screens(w)).toEqual(LIVE);
    await drill(w, "hilum");
    // the stapler: no reload in, nothing divided; one reload for each firing, that stapler's
    await take(w, item("stapler"));
    const empty = await refused(w, A, "divide_vein", T);
    expect(empty.message).toBe('Divide the inferior pulmonary vein: a vascular reload; fire only with the vein alone in the jaws and the tip clear beyond it needs the "Endoscopic linear cutter-stapler" in your hands to be reload in (the one you hold is sterile, no reload in).');
    await putDown(w, item("stapler"));
    await drill(w, "closed");
    // every step drawn in turn, each once
    expect(passed).toEqual(STEPS.slice(1));
    await done(w, A, "reset", T);
    expect(state(w, T)).toBe("ready");
    // the next trainee finds it as the first did: under a blanket, nothing on the chest, the monitor dark
    expect(lookOf(trainer(), w.runtime.stateOf(T))).toMatchObject({ layers: [], screen: "none", manikin: { cover: "blanket", breathing: "both" } });
    expect(screens(w)).toEqual(DARK);
  });

  it("one view (the 2026-11-12 audit, finding 03): the tower switched off, its light on standby, the scope withdrawn — every screen dark and the next step under vision refused until the view is back", async () => {
    const w = world("or-7.slot");
    await drill(w, "explored");
    expect(screens(w)).toEqual(LIVE);
    const refusedUnderVision = async () => {
      const r = await refused(w, A, "place_working_ports", T);
      expect(w.runtime.stateOf(T)).toBe("explored");
      return r;
    };
    // loss of power: dark everywhere, the step refused; the view back only after a white balance with the scope out
    await done(w, A, "power_off", sim("vats-tower"));
    expect(w.runtime.stateOf(sim("vats-tower"))).toBe("off");
    expect(screens(w)).toEqual(DARK);
    expect((await refusedUnderVision()).message).toMatch(/thoracoscopy tower/i);
    await done(w, A, "power_on", sim("vats-tower"));
    expect(screens(w)).toEqual(DARK);
    const inChest = await refused(w, A, "white_balance", sim("vats-tower"));
    expect(inChest.message).toMatch(/thoracoscope/i);
    await done(w, A, "withdraw", item("scope"));
    await done(w, A, "white_balance", sim("vats-tower"));
    expect(screens(w)).toEqual(DARK);
    await refusedUnderVision();
    await take(w, item("scope"));
    await done(w, A, "reinsert_scope", T);
    await putDown(w, item("scope"));
    expect(screens(w)).toEqual(LIVE);
    // loss of illumination: the light source on standby — dark, refused; the light on again — the view back
    await done(w, A, "light_standby", sim("vats-tower"));
    expect(screens(w)).toEqual(DARK);
    await refusedUnderVision();
    await done(w, A, "light_on", sim("vats-tower"));
    expect(screens(w)).toEqual(LIVE);
    // the scope withdrawn (to clean the lens): dark, refused; back in — the next step goes ahead, the station where it was
    await done(w, A, "withdraw", item("scope"));
    expect(screens(w)).toEqual(DARK);
    await refusedUnderVision();
    await take(w, item("scope"));
    await done(w, A, "reinsert_scope", T);
    await putDown(w, item("scope"));
    expect(w.runtime.stateOf(T)).toBe("explored");
    expect(screens(w)).toEqual(LIVE);
    await done(w, A, "place_working_ports", T);
    expect(w.runtime.stateOf(T)).toBe("working-ports");
  });

  it("the stapler (finding 04): an empty stapler and a spent one divide nothing; in assessment only the surgeon divides; in practice the circulating nurse's step is done and recorded as a role substitution", async () => {
    const w = world("or-7.slot");
    await drill(w, "hilum");
    // the circulating nurse picks it up — it stays sterile, no reload in — and is not the surgeon: refused, either way
    await take(w, item("stapler"), NURSE);
    expect(own(w, item("stapler"))).toBe("sterile");
    const nurse = await refused(w, NURSE, "divide_vein", T, "NOT_AUTHORIZED");
    expect(nurse.message).toMatch(/^Only Clinician, Attending may "Divide the inferior pulmonary vein/);
    await putDown(w, item("stapler"), NURSE);
    // the surgeon: empty, refused; loaded, fired — that stapler's reload is spent
    await take(w, item("stapler"));
    await refused(w, A, "divide_vein", T);
    await done(w, A, "load", item("stapler"));
    await done(w, A, "divide_vein", T);
    expect(lifecycle(w, item("stapler"))).toBe("fired");
    // a spent cartridge divides nothing: the bronchus waits for a fresh reload
    await putDown(w, item("stapler"));
    await withItem(w, "clip-applier", "divide_artery");
    await take(w, item("stapler"));
    const spent = await refused(w, A, "divide_bronchus", T);
    expect(spent.message).toMatch(/fired \(takes a fresh reload\)/);
    expect(w.runtime.stateOf(T)).toBe("artery-divided");
    await putDown(w, item("stapler"));
    // practice mode (the faculty sets it): the surgeon loads a fresh reload and hands the stapler to the nurse, who may
    // stand in — done, and labelled a substitution, in the result and the run
    await done(w, FACULTY_ANAESTHETIST, "set_practice", CONSOLE);
    const handOver = async () => {
      await take(w, item("stapler"));
      await done(w, A, "load", item("stapler"));
      // (the surgeon walks over to the nurse first when she is out of arm's reach)
      await done(w, A, "hand_over", item("stapler"), { to: NURSE });
    };
    await handOver();
    const stand = await done(w, NURSE, "divide_bronchus", T);
    expect(stand.message).toMatch(/Done by the nurse in place of the clinician or attending this step is assessed for: recorded as a role substitution, not assessed\./);
    // each firing against that very stapler, each its own reload; the substitution named
    const run = w.runtime.runsOf(T).current!;
    const firings = run.entries.filter((e) => e.used?.some((u) => u.id === item("stapler")));
    expect(firings.map((e) => [e.op, e.actor, e.used![0]!.from, e.used![0]!.to, !!e.substitution])).toEqual([
      ["divide_vein", A, "loaded", "fired", false],
      ["divide_bronchus", NURSE, "loaded", "fired", true],
    ]);
    // back in assessment: the nurse with a loaded stapler is refused again, and the stapler stays loaded
    await done(w, FACULTY_ANAESTHETIST, "set_assessment", CONSOLE);
    await putDown(w, item("stapler"), NURSE);
    await handOver();
    await refused(w, NURSE, "complete_fissure", T, "NOT_AUTHORIZED");
    expect([w.runtime.stateOf(T), lifecycle(w, item("stapler"))]).toEqual(["bronchus-divided", "loaded"]);
  });

  it("the drain (finding 05): primed is not connected; the unit is connected to that chest tube, by instance — disconnected, refused; reconnected, the lung comes up; handed over first, the same tube", async () => {
    const w = world("or-7.slot");
    await drill(w, "leak-tested");
    await done(w, A, "prime", sim("chest-drain"));
    // the tube handed from the faculty nurse to the surgeon before it goes in: the same instance, placed and kept with the station
    await take(w, item("chest-tube"), NURSE);
    await done(w, NURSE, "hand_over", item("chest-tube"), { to: A });
    await done(w, A, "place_drain", T);
    await putDown(w, item("chest-tube"));
    const links = (id: string) => (w.runtime.snapshot().entities[id]?.data?.links as string[] | undefined) ?? [];
    expect(lifecycle(w, item("chest-tube"))).toBe("placed");
    expect(links(item("chest-tube"))).toEqual([T]);
    // primed is not connected: the lung stays down
    expect(state(w, sim("chest-drain"))).toBe("primed");
    const primed = await refused(w, A, "re_expand", T);
    expect(primed.message).toMatch(/"Chest tube \(28 Fr\)" in .* to be connected to a "Chest drainage unit/);
    // connected: to that tube, both ways
    await done(w, A, "connect", sim("chest-drain"));
    expect(links(sim("chest-drain"))).toEqual([item("chest-tube")]);
    expect(links(item("chest-tube")).sort()).toEqual([sim("chest-drain"), T].sort());
    // disconnected: primed again, connected to nothing — refused
    await done(w, A, "disconnect", sim("chest-drain"));
    expect([state(w, sim("chest-drain")), links(sim("chest-drain"))]).toEqual(["primed", []]);
    await refused(w, A, "re_expand", T);
    // reconnected: the lung comes up
    await done(w, A, "connect", sim("chest-drain"));
    await done(w, A, "re_expand", T);
    expect(w.runtime.stateOf(T)).toBe("re-expanded");
  });

  it("each trainee's run is its own (finding 06): no incision before the Time Out and the count; the reset puts back the instructor's presets; the run records who did what, with which instrument", async () => {
    const w = world("or-7.slot");
    await drill(w, "lung-down");
    // the count after the incision cannot be the baseline: the incision waits for it
    await scrubbed(w);
    await take(w, item("port"));
    await refused(w, A, "place_camera_port", T);
    await putDown(w, item("port"));
    await drill(w, "closed");
    // at the close: the count before closing the cavity done and the checklist timed out
    expect([state(w, sim("count-board")), state(w, sim("checklist")), state(w, sim("chest-drain"))]).toEqual(["cavity", "timed-out", "water-seal"]);
    // the Sign Out waits for the final count, as the theatre's does (no RF scan in the drill: the count aloud settles it)
    await refused(w, A, "sign_out", sim("checklist"));
    await done(w, NURSE, "closing_count", sim("count-board"));
    await refused(w, A, "sign_out", sim("checklist"));
    await done(w, NURSE, "final_count", sim("count-board"));
    await done(w, A, "sign_out", sim("checklist"));
    expect([state(w, sim("count-board")), state(w, sim("checklist"))]).toEqual(["reconciled", "signed-out"]);
    await done(w, NURSE, "reset", T);
    // the next trainee finds what the instructor presets: the boards cleared, a fresh drainage unit, the instruments
    // sterile (the stapler without a reload), the tower set up, the smoke evacuator off — and nothing connected
    const presets = {
      [sim("count-board")]: "not-started", [sim("checklist")]: "pending", [sim("chest-drain")]: "sealed", [sim("vats-tower")]: "balanced", [sim("smoke-evac")]: "off",
      [item("stapler")]: "sterile", [item("scope")]: "sterile", [item("chest-tube")]: "sterile", [item("port")]: "sterile", [item("shears")]: "sterile",
      [item("dissector")]: "sterile", [item("clip-applier")]: "sterile", [item("bag")]: "sterile", [item("lung-forceps")]: "sterile",
    };
    expect(Object.fromEntries(Object.keys(presets).map((id) => [id, lifecycle(w, id) ?? state(w, id)]))).toEqual(presets);
    for (const id of [T, sim("chest-drain"), item("chest-tube")]) expect(w.runtime.snapshot().entities[id]?.data?.links, id).toBeUndefined();
    // the run closed is the first trainee's: the station's steps and the drill's devices in the order done — the count
    // before the first incision, a reload before each firing — and the next run begins with the presets
    const { current, closed } = w.runtime.runsOf(T);
    expect(closed).toHaveLength(1);
    const ops = closed[0]!.entries.map((e) => (e.device ? `${e.device.replace(/^eq:l0-sim-or\./, "")}:${e.op}` : e.op));
    expect(ops.indexOf("count-board:baseline_count")).toBeLessThan(ops.indexOf("place_camera_port"));
    expect(ops.indexOf("checklist:time_out")).toBeLessThan(ops.indexOf("place_camera_port"));
    expect(ops.filter((o) => o === "vats-stapler:load")).toHaveLength(3);
    expect(ops.at(-1)).toBe("reset");
    expect(closed[0]!.entries.find((e) => e.op === "divide_vein")).toMatchObject({ actor: A, role: "clinician", used: [{ id: item("stapler"), from: "loaded", to: "fired" }] });
    expect(current).toMatchObject({ n: 2, entries: [] });
    expect(new Set(current!.presets!.map((p) => p.id))).toEqual(new Set(Object.keys(presets)));
    // the second trainee starts from the beginning, in their own run
    await done(w, A, "check_position", T);
    expect(w.runtime.runsOf(T).current!.entries.map((e) => e.op)).toEqual(["check_position"]);
  });

  it("the release scenario (loss of view, then an empty stapler): both faults stop the team before it advances; restored, the operation goes on", async () => {
    const w = world("or-7.slot");
    await drill(w, "explored");
    // the tower switched off after the scope went in: no step under vision
    await done(w, A, "power_off", sim("vats-tower"));
    await refused(w, A, "place_working_ports", T);
    // the team restores the view: the scope out, power, white balance, the scope back in
    await done(w, A, "withdraw", item("scope"));
    await done(w, A, "power_on", sim("vats-tower"));
    await done(w, A, "white_balance", sim("vats-tower"));
    await take(w, item("scope"));
    await done(w, A, "reinsert_scope", T);
    await putDown(w, item("scope"));
    expect(screens(w)).toEqual(LIVE);
    await drill(w, "hilum");
    // an unloaded stapler is presented: the division is refused, nothing is divided, the stapler stays unfired
    await take(w, item("stapler"));
    await refused(w, A, "divide_vein", T);
    expect([w.runtime.stateOf(T), own(w, item("stapler"))]).toEqual(["hilum", "sterile"]);
    // loaded: the vein is divided, the reload spent
    await done(w, A, "load", item("stapler"));
    await done(w, A, "divide_vein", T);
    expect([w.runtime.stateOf(T), lifecycle(w, item("stapler"))]).toEqual(["vein-divided", "fired"]);
  });
});
