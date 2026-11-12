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
    await done(w, A, "insert", or5("vats-scope"));
    expect(lifecycle(w, or5("vats-scope"))).toBe("in-use");
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
  const item = (name: string) => sim(`vats-${name}`);
  const trainer = (): EquipmentType => catalogs.flatMap((c) => c.equipment).find((e) => e.id === "sc-vats-trainer")!;
  /** The station's steps in order, as its behaviour lists them. */
  const STEPS = ["ready", "positioned", "lung-down", "camera-port", "explored", "working-ports", "mobilised", "hilum", "vein-divided", "artery-divided", "bronchus-divided", "lobe-free", "specimen-out", "nodes", "leak-tested", "drained", "re-expanded", "closed"];

  it("stands where the simulation OR's table would, with the theatre's thoracoscopy equipment round it and no patient place", () => {
    const station = F.placements.find((p) => p.id === "l0-sim-vats-trainer");
    expect(station).toMatchObject({ type: "sc-vats-trainer", room: "l0-sim-or" });
    expect(F.placements.some((p) => p.id === "l0-sim-or.table")).toBe(false);
    expect(F.patientSlots.some((s) => s.room === "l0-sim-or")).toBe(false);
    for (const id of ["vats-tower", "chest-drain", "smoke-evac", "count-board", "vats-port", "vats-scope", "vats-stapler"]) expect(F.placements.some((p) => p.id === `l0-sim-or.${id}`), id).toBe(true);
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
    // the monitor shows the scope's picture while the scope is in the chest — from the look round to the lung re-expanded
    expect(STEPS.filter((s) => look(s).screen === "thoracoscopy")).toEqual(STEPS.slice(STEPS.indexOf("explored"), STEPS.indexOf("re-expanded") + 1));
    expect(STEPS.filter((s) => look(s).screen === "none")).toEqual(["ready", "positioned", "lung-down", "camera-port", "closed"]);
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
    await done(w, "staff:l0-sim-or.circulating-nurse", "check_position", T);
    expect(lookOf(type, w.runtime.stateOf(T))).toMatchObject({ layers: ["lines", "site-camera", "site-working"], screen: "none", manikin: { cover: "blanket", breathing: "both" } });
    await done(w, "staff:l0-sim-or.anaesthetist", "isolate_lung", T);
    expect(lookOf(type, w.runtime.stateOf(T))).toMatchObject({ screen: "none", manikin: { cover: "drapes", breathing: "one-lung" } });
    // the events a scene follows say who moved it on; the learner carries on from there
    expect(seen).toEqual(["staff:l0-sim-or.circulating-nurse: ready → positioned", "staff:l0-sim-or.anaesthetist: positioned → lung-down"]);
    await take(w, item("port"));
    await done(w, A, "place_camera_port", T);
    expect(seen.at(-1)).toBe(`${A}: lung-down → camera-port`);
    expect(lookOf(type, w.runtime.stateOf(T)).layers).toContain("camera-port");
  });

  it("the whole sequence in order — each step with its instrument in hand, the camera ready, smoke evacuated, the drain primed, the count done", async () => {
    // the case's patient is upstairs in OR 7: the station needs none
    const w = world("or-7.slot");
    // the station's state after each step, as the world has it (`stateOf`: what the scene draws) and as its inspection says
    const passed: string[] = [];
    const step = async (operation: string) => {
      await done(w, A, operation, T);
      expect(w.runtime.stateOf(T)).toBe(state(w, T));
      passed.push(w.runtime.stateOf(T)!);
    };
    expect(state(w, T)).toBe("ready");
    // a step out of order is not offered
    expect((await w.act({ actorId: A, operation: "explore", targetId: T })).status).toBe("failed");
    await step("check_position");
    await step("isolate_lung");

    // the camera port wants the port in the hand
    const bare = await refused(w, A, "place_camera_port", T);
    expect(bare.message).toMatch(/Thoracic port/);
    await take(w, item("port"));
    await step("place_camera_port");
    await putDown(w, item("port"));

    // the scope, with the camera system white-balanced
    await take(w, item("scope"));
    await done(w, A, "power_off", sim("vats-tower"));
    const dark = await refused(w, A, "explore", T);
    expect(dark.message).toMatch(/thoracoscopy tower/i);
    await done(w, A, "power_on", sim("vats-tower"));
    await done(w, A, "white_balance", sim("vats-tower"));
    await step("explore");
    await putDown(w, item("scope"));
    await step("place_working_ports");

    // energy: smoke evacuation first
    await take(w, item("shears"));
    const smoke = await refused(w, A, "free_adhesions", T);
    expect(smoke.hint?.goal).toMatchObject({ id: sim("smoke-evac") });
    await done(w, A, "switch_on", sim("smoke-evac"));
    await step("free_adhesions");

    await take(w, item("dissector"));
    await step("dissect_hilum");
    await putDown(w, item("dissector"));

    // vein, artery, bronchus, fissure: the stapler — an arterial branch may be clipped instead
    await refused(w, A, "divide_vein", T);
    await take(w, item("stapler"));
    await step("divide_vein");
    await putDown(w, item("stapler"));
    await take(w, item("clip-applier"));
    await step("divide_artery");
    await putDown(w, item("clip-applier"));
    await take(w, item("stapler"));
    await step("divide_bronchus");
    await step("complete_fissure");
    await putDown(w, item("stapler"));

    await take(w, item("bag"));
    await step("retrieve_specimen");
    await putDown(w, item("bag"));
    await step("take_nodes");
    await putDown(w, item("shears"));
    await step("leak_test");

    // the drain: the unit primed first
    await take(w, item("chest-tube"));
    const unprimed = await refused(w, A, "place_drain", T);
    expect(unprimed.hint?.goal).toMatchObject({ id: sim("chest-drain") });
    await done(w, A, "prime", sim("chest-drain"));
    await step("place_drain");
    await step("re_expand");

    // closing waits for the count
    const uncounted = await refused(w, A, "close", T);
    expect(uncounted.hint?.goal).toMatchObject({ id: sim("count-board") });
    await done(w, A, "baseline_count", sim("count-board"));
    await done(w, A, "cavity_count", sim("count-board"));
    await step("close");
    expect(state(w, T)).toBe("closed");
    // every step drawn in turn, each once
    expect(passed).toEqual(STEPS.slice(1));
    await step("reset");
    expect(state(w, T)).toBe("ready");
    // the next trainee finds it as the first did: under a blanket, nothing on the chest, the monitor dark
    expect(lookOf(trainer(), w.runtime.stateOf(T))).toMatchObject({ layers: [], screen: "none", manikin: { cover: "blanket", breathing: "both" } });
  });
});
