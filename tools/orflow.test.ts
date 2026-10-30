/**
 * IMPF Surgery Hospital: the operating room's interactions on ClinicalCraft's world runtime — every act goes through
 * the action bus (authority, preconditions, reach, durations), exactly as for the learner, an agent or a colleague.
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/world/src/` for the run and removes it afterwards.
 *
 *   1. no incision before hand hygiene, gown and gloves, the WHO sign-in and time-out (which needs the baseline
 *      count) with the room in operating mode — each refusal says why and points at what to do;
 *   2. the scrub nurse passes the needle holder; only whoever holds an instrument uses it;
 *   3. energy needs the return electrode monitored and smoke evacuation running;
 *   4. the counts close the case: cavity, skin, final — the final count only after a clear RF scan — then sign-out;
 *   5. a used instrument goes down to the CSSD: washed and disinfected, sterilised and released, then sterile again;
 *   6. hybrid OR: no injection under fluoroscopy without a lead apron on and the shield in place.
 *
 * The pack directory comes from $SURGERYCRAFT_CONTENT.
 */
import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { compileFacility, parseCatalog, parseFacility, parseRoomTemplate, type FacilityDefinition, type RoomTemplate } from "@clinicalcraft/core";
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
  if (!r.ok) throw new Error(f);
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
const SCRUB = "staff:or-7.scrub-nurse";
const CIRCULATOR = "staff:or-7.circulating-nurse";
const eq = (id: string) => `eq:${id}`;
// the operating-room case of the built-in library (term pregnancy for caesarean section), in OR 7
const world = (slotId = "or-7.slot"): TestWorld => makeWorld("cmcr-1653406", { facility: F, catalogs, slotId });

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
async function refused(w: TestWorld, actorId: string, operation: string, targetId: string, code: string): Promise<WorldActionResult> {
  let r = await w.act({ actorId, operation, targetId });
  if (r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE")) {
    expect((await w.act({ actorId, operation: "navigate", goal: r.hint.goal })).status).toBe("completed");
    r = await w.act({ actorId, operation, targetId });
  }
  expect(r, r.message).toMatchObject({ status: "failed", errorCode: code });
  return r;
}

const state = (w: TestWorld, id: string) => w.runtime.inspect(A, id)?.state;

async function scrubAndGown(w: TestWorld): Promise<void> {
  await done(w, A, "wash_hands", eq("or-7.sanitizer"));
  for (const id of ["or-7.gown", "or-7.gloves"]) {
    await done(w, A, "approach", eq(id));
    await done(w, A, "pick_up", eq(id));
    await done(w, A, "equip", eq(id));
  }
}

async function timeOut(w: TestWorld): Promise<void> {
  await done(w, A, "sign_in", eq("or-7.checklist"));
  await done(w, CIRCULATOR, "baseline_count", eq("or-7.count-board"));
  await done(w, A, "time_out", eq("or-7.checklist"));
}

describe("IMPF Surgery Hospital · the operating room", () => {
  it("every in-room gate (nearbyState) is met only by its own room's device — never through a wall", () => {
    const w = world();
    const room = new Map(F.placements.map((p) => [eq(p.id), p.room]));
    const byType = new Map(catalogs.flatMap((c) => c.equipment).map((e) => [e.id, e]));
    const leaves = (p: unknown): { type: string; within?: number }[] => {
      if (!p || typeof p !== "object") return [];
      const o = p as Record<string, unknown>;
      if (o.nearbyState) return [o.nearbyState as { type: string; within?: number }];
      return [...((o.all as unknown[]) ?? []), ...((o.any as unknown[]) ?? []), ...(o.not ? [o.not] : [])].flatMap(leaves);
    };
    let gates = 0;
    const crossings: string[] = [];
    for (const p of F.placements.filter((x) => /^(or-\d|l0-sim-or)/.test(x.room ?? ""))) {
      const ops = Object.values(byType.get(p.type)?.behavior?.operations ?? {});
      for (const n of ops.flatMap((o) => (o.requires ?? []).flatMap(leaves))) {
        // reprocessing is meant to happen in the CSSD, not in the room
        if (n.type === "sc-washer-disinfector" || n.type === "sc-steam-steriliser") continue;
        gates++;
        const near = w.runtime.nearby(eq(p.id), n.type, n.within);
        if (!near.length) crossings.push(`${p.id} → no ${n.type}`);
        for (const x of near) if (room.get(x.id) !== p.room) crossings.push(`${p.id} → ${x.id}`);
      }
    }
    expect(gates).toBeGreaterThan(50);
    expect(crossings).toEqual([]);
  });

  it("no incision before scrub, gown, gloves and the time-out — each refusal says what to do", async () => {
    const w = world();
    await done(w, A, "approach", eq("or-7.scalpel"));
    await done(w, A, "pick_up", eq("or-7.scalpel"));
    // not scrubbed: hand hygiene first, pointing at the nearest sink or hand-rub
    const dirty = await refused(w, A, "incise", eq("or-7.scalpel"), "PRECONDITION_FAILED");
    expect(dirty.hint?.then?.operation).toBe("wash_hands");
    await scrubAndGown(w);
    expect(w.runtime.actor(A)!.holding).toEqual([eq("or-7.scalpel"), eq("or-7.gown"), eq("or-7.gloves")]);
    expect(state(w, eq("or-7.gown"))).toBe("equipped");
    // scrubbed and gowned, but no time-out: the checklist board is the way
    const early = await refused(w, A, "incise", eq("or-7.scalpel"), "PRECONDITION_FAILED");
    expect(early.message).toMatch(/WHO Surgical Safety Checklist/);
    expect(early.hint?.goal).toMatchObject({ kind: "interact", id: eq("or-7.checklist") });
    // the time-out needs the baseline count
    await done(w, A, "sign_in", eq("or-7.checklist"));
    const noCount = await refused(w, A, "time_out", eq("or-7.checklist"), "PRECONDITION_FAILED");
    expect(noCount.hint?.goal).toMatchObject({ id: eq("or-7.count-board") });
    await done(w, CIRCULATOR, "baseline_count", eq("or-7.count-board"));
    await done(w, A, "time_out", eq("or-7.checklist"));
    // the room in set-back: no incision either
    await done(w, CIRCULATOR, "set_setback", eq("or-7.control-panel"));
    await refused(w, A, "incise", eq("or-7.scalpel"), "PRECONDITION_FAILED");
    await done(w, CIRCULATOR, "set_operating", eq("or-7.control-panel"));
    await done(w, A, "incise", eq("or-7.scalpel"));
    expect(w.runtime.snapshot().entities[eq("or-7.scalpel")]?.state).toBe("in-use");
  });

  it("the scrub nurse passes the needle holder; only whoever holds an instrument uses it", async () => {
    const w = world();
    await scrubAndGown(w);
    await done(w, SCRUB, "approach", eq("or-7.needle-holder"));
    await done(w, SCRUB, "pick_up", eq("or-7.needle-holder"));
    // in the nurse's hands: not the surgeon's to use
    await done(w, A, "navigate", undefined, undefined, { kind: "entity", id: SCRUB, range: 1 });
    expect((await w.act({ actorId: A, operation: "load_needle", targetId: eq("or-7.needle-holder") })).errorCode).toBe("DEVICE_BUSY");
    await done(w, SCRUB, "hand_over", eq("or-7.needle-holder"), { to: A });
    expect(w.runtime.actor(A)!.holding).toContain(eq("or-7.needle-holder"));
    await done(w, A, "load_needle", eq("or-7.needle-holder"));
    await done(w, A, "suture", eq("or-7.needle-holder"));
    expect(state(w, eq("or-7.needle-holder"))).toBe("held");
    expect(w.runtime.snapshot().entities[eq("or-7.needle-holder")]?.state).toBe("in-use");
  });

  it("energy needs the return electrode monitored and smoke evacuation running", async () => {
    const w = world();
    await scrubAndGown(w);
    await done(w, A, "approach", eq("or-7.esu-pencil"));
    await done(w, A, "pick_up", eq("or-7.esu-pencil"));
    const cold = await refused(w, A, "cut", eq("or-7.esu-pencil"), "PRECONDITION_FAILED");
    expect(cold.message).toMatch(/Surgical equipment pendant/);
    await done(w, CIRCULATOR, "check_return_electrode", eq("or-7.surg-pendant"));
    // the generator will not enable output without smoke evacuation
    const smoke = await refused(w, CIRCULATOR, "enable_output", eq("or-7.surg-pendant"), "PRECONDITION_FAILED");
    expect(smoke.hint?.goal).toMatchObject({ id: eq("or-7.smoke-evac") });
    await done(w, CIRCULATOR, "switch_on", eq("or-7.smoke-evac"));
    await done(w, CIRCULATOR, "enable_output", eq("or-7.surg-pendant"));
    await done(w, A, "cut", eq("or-7.esu-pencil"));
    await done(w, A, "discard", eq("or-7.esu-pencil"));
  });

  it("the counts close the case: cavity, skin, final after a clear RF scan, then sign-out", async () => {
    const w = world();
    await timeOut(w);
    await done(w, CIRCULATOR, "cavity_count", eq("or-7.count-board"));
    await done(w, CIRCULATOR, "closing_count", eq("or-7.count-board"));
    // the counts agree, but the RF adjunct has not been used: no final count, no sign-out
    const noScan = await refused(w, CIRCULATOR, "final_count", eq("or-7.count-board"), "PRECONDITION_FAILED");
    expect(noScan.hint?.goal).toMatchObject({ id: eq("or-7.rf-wand") });
    await refused(w, A, "sign_out", eq("or-7.checklist"), "PRECONDITION_FAILED");
    await done(w, CIRCULATOR, "approach", eq("or-7.rf-wand"));
    await done(w, CIRCULATOR, "pick_up", eq("or-7.rf-wand"));
    await done(w, CIRCULATOR, "scan", eq("or-7.rf-wand"));
    await done(w, CIRCULATOR, "final_count", eq("or-7.count-board"));
    await done(w, A, "sign_out", eq("or-7.checklist"));
    expect(state(w, eq("or-7.checklist"))).toBe("signed-out");
    expect(state(w, eq("or-7.count-board"))).toBe("reconciled");
  });

  it("a used instrument is sterile again only after the CSSD's washer-disinfector and steriliser", async () => {
    const w = world();
    await scrubAndGown(w);
    await timeOut(w);
    await done(w, A, "approach", eq("or-7.scalpel"));
    await done(w, A, "pick_up", eq("or-7.scalpel"));
    await done(w, A, "incise", eq("or-7.scalpel"));
    await done(w, A, "finish", eq("or-7.scalpel"));
    // in the OR: nothing to reprocess it with
    expect(await w.act({ actorId: A, operation: "reprocess", targetId: eq("or-7.scalpel") })).toMatchObject({ errorCode: "PRECONDITION_FAILED" });
    // down to the CSSD with it (a clean lift / stairs to the ground floor), the machines run their cycles
    for (const [id, ops] of [["l0-washer-2", ["load", "run_cycle"]], ["l0-steriliser-1", ["bowie_dick", "run_cycle", "release"]]] as const) {
      for (const op of ops) await done(w, A, op, eq(id));
    }
    expect(w.runtime.actor(A)!.holding).toContain(eq("or-7.scalpel"));
    // the inspection, assembly & packing room, between the washers' clean side and the sterilisers
    await done(w, A, "navigate", undefined, undefined, { kind: "point", x: 14, z: -7, level: "L0" });
    await done(w, A, "reprocess", eq("or-7.scalpel"));
    expect(w.runtime.snapshot().entities[eq("or-7.scalpel")]?.state).toBe("sterile");
  });

  it("hybrid OR: no injection under fluoroscopy without a lead apron on and the shield in place", async () => {
    const w = world("or-1.slot");
    await done(w, A, "wash_hands", eq("or-1.sanitizer"));
    await done(w, A, "load", eq("or-1.injector"));
    await done(w, A, "purge_and_arm", eq("or-1.injector"));
    const noLead = await refused(w, A, "inject", eq("or-1.injector"), "PRECONDITION_FAILED");
    expect(noLead.message).toMatch(/lead apron/i);
    await done(w, A, "approach", eq("or-1.apron-1"));
    await done(w, A, "pick_up", eq("or-1.apron-1"));
    await done(w, A, "equip", eq("or-1.apron-1"));
    await refused(w, A, "inject", eq("or-1.injector"), "PRECONDITION_FAILED");
    await done(w, A, "position", eq("or-1.shield"));
    await done(w, A, "inject", eq("or-1.injector"));
    expect(state(w, eq("or-1.injector"))).toBe("empty");
  });
});
