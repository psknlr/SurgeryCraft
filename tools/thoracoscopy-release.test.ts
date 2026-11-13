/**
 * The thoracoscopy training station's release scenario (the 2026-11-12 audit: "loss of view followed by an empty
 * stapler"), in an in-world session of the IMPF Surgery Hospital with Case 126 upstairs in OR 7 — the station needs no
 * patient. Once through the player's interface (the world actions the browser sends) and once through an agent's
 * (its tools: `interact_object`, `approach_object`, `inspect_object`):
 *
 *   the drill to the scope in → the tower switched off: every screen of the scope's picture dark, the next step under
 *   vision refused → the team restores the view (the scope out, power, white balance, the scope back in) → an unloaded
 *   stapler presented: the division refused, nothing divided, the stapler unfired → loaded: the vein divided, that
 *   stapler's reload spent — both faults caught before the operation advanced, and the run record shows it.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards;
 * the repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type WorldActionResult } from "@clinicalcraft/world";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const A = PRIMARY_ACTOR;
const T = "eq:l0-sim-vats-trainer";
const sim = (id: string) => `eq:l0-sim-or.${id}`;
const item = (name: string) => sim(`vats-${name}`);
const NURSE = "staff:l0-sim-or.circulating-nurse";
const SCREENS = [T, sim("vats-tower"), sim("display-1"), sim("display-2")];

type Iface = "player" | "agent";
let seq = 0;

async function session(): Promise<TestSession> {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get("cmcr-1654623")!.def;
  const facility = pack.facilities.get("impf-surgery-hospital")!.def;
  const catalogs = facility.catalogs.map((id) => pack.catalogs.get(id)!.def);
  const t = await makeSession({ caseDef, facility, catalogs, settingsPatch: { embodiment: "embodied", approvalMode: "bypass" } });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  return t;
}

/** A world action as the browser sends it (`world_action`), walking first where a refusal for reach points. */
async function world(t: TestSession, actorId: string, operation: string, targetId: string, parameters?: Record<string, unknown>): Promise<WorldActionResult> {
  const send = async (request: Record<string, unknown>) => {
    const events = await t.session.run({ type: "world_action", request: { actionId: `p-${++seq}`, ...request } as never });
    return msgsOf(events, "world_action_result").at(-1)!.result;
  };
  let r = await send({ actorId, operation, targetId, ...(parameters ? { parameters } : {}) });
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE"); i++) {
    expect((await send({ actorId, operation: "navigate", goal: r.hint.goal })).status).toBe("completed");
    r = await send({ actorId, operation, targetId, ...(parameters ? { parameters } : {}) });
  }
  return r;
}

/** An agent's tool call (`external_tool_call`). */
async function tool(t: TestSession, name: string, args: Record<string, unknown>) {
  const events = await t.session.run({ type: "external_tool_call", callId: `a-${++seq}`, tool: name, args, allowBypass: true });
  return msgsOf(events, "tool_call_end").at(-1) as { ok: boolean; output: string; data?: { result?: WorldActionResult } };
}

/** The same operation by the learner's body through either interface: the agent approaches the target when told to. */
async function op(t: TestSession, iface: Iface, operation: string, targetId: string, parameters?: Record<string, unknown>): Promise<{ ok: boolean; message: string }> {
  if (iface === "player") {
    const r = await world(t, A, operation, targetId, parameters);
    return { ok: r.status === "completed", message: r.message };
  }
  let r = await tool(t, "interact_object", { target: targetId, operation, ...(parameters ? { parameters } : {}) });
  const code = r.data?.result?.errorCode;
  if (!r.ok && (code === "NOT_IN_RANGE" || code === "NOT_VISIBLE")) {
    expect((await tool(t, "approach_object", { target: targetId })).ok).toBe(true);
    r = await tool(t, "interact_object", { target: targetId, operation, ...(parameters ? { parameters } : {}) });
  }
  return { ok: r.ok, message: r.output };
}
const done = async (t: TestSession, iface: Iface, operation: string, targetId: string, parameters?: Record<string, unknown>) => {
  const r = await op(t, iface, operation, targetId, parameters);
  expect(r.ok, `${iface} ${operation} ${targetId}: ${r.message}`).toBe(true);
};
const refused = async (t: TestSession, iface: Iface, operation: string, targetId: string) => {
  const r = await op(t, iface, operation, targetId);
  expect(r.ok, `${iface} ${operation} ${targetId} should be refused`).toBe(false);
  return r.message;
};
const lifecycle = (t: TestSession, id: string) => t.session.world()!.snapshot().entities[id]?.state ?? "sterile";
const screens = (t: TestSession) => SCREENS.map((id) => t.session.world()!.screenOf(id));
const withItem = async (t: TestSession, iface: Iface, name: string, operation: string) => {
  await done(t, iface, "pick_up", item(name));
  await done(t, iface, operation, T);
  await done(t, iface, "put_down", item(name));
};

/** The drill to the scope in the chest: the position, the lung down, scrubbed, the team's checks, the camera port. */
async function toExplored(t: TestSession, iface: Iface): Promise<void> {
  await done(t, iface, "check_position", T);
  await done(t, iface, "isolate_lung", T);
  await done(t, iface, "wash_hands", sim("sanitizer"));
  for (const id of [sim("gown"), sim("gloves")]) {
    await done(t, iface, "pick_up", id);
    await done(t, iface, "equip", id);
  }
  await done(t, iface, "sign_in", sim("checklist"));
  // the team counts before the incision (the faculty circulating nurse)
  expect((await world(t, NURSE, "baseline_count", sim("count-board"))).status).toBe("completed");
  await done(t, iface, "time_out", sim("checklist"));
  await withItem(t, iface, "port", "place_camera_port");
  await withItem(t, iface, "scope", "explore");
  expect(t.session.world()!.stateOf(T)).toBe("explored");
}

async function scenario(iface: Iface): Promise<void> {
  const t = await session();
  await toExplored(t, iface);
  expect(screens(t)).toEqual(SCREENS.map(() => "thoracoscopy"));

  // ---- loss of view: the tower switched off after the scope went in
  await done(t, iface, "power_off", sim("vats-tower"));
  expect(screens(t)).toEqual(SCREENS.map(() => "none"));
  // what the agent sees of the station's monitor, looking at it: dark
  if (iface === "agent") {
    expect((await tool(t, "look_at", { target: T })).ok).toBe(true);
    expect((await tool(t, "inspect_object", { target: T })).output).toMatch(/screen: dark — no picture/);
  }
  expect(await refused(t, iface, "place_working_ports", T)).toMatch(/thoracoscopy tower/i);
  expect(t.session.world()!.stateOf(T)).toBe("explored");
  // the team restores the view: the scope out, power, white balance, the scope back in
  await done(t, iface, "withdraw", item("scope"));
  await done(t, iface, "power_on", sim("vats-tower"));
  await done(t, iface, "white_balance", sim("vats-tower"));
  await withItem(t, iface, "scope", "reinsert_scope");
  expect(screens(t)).toEqual(SCREENS.map(() => "thoracoscopy"));
  await done(t, iface, "place_working_ports", T);
  await done(t, iface, "switch_on", sim("smoke-evac"));
  await withItem(t, iface, "shears", "free_adhesions");
  await withItem(t, iface, "dissector", "dissect_hilum");

  // ---- an empty stapler presented: the division refused, nothing divided, the stapler unfired
  await done(t, iface, "pick_up", item("stapler"));
  expect(await refused(t, iface, "divide_vein", T)).toMatch(/reload in/);
  expect([t.session.world()!.stateOf(T), lifecycle(t, item("stapler"))]).toEqual(["hilum", "sterile"]);
  // loaded: divided, that stapler's reload spent
  await done(t, iface, "load", item("stapler"));
  await done(t, iface, "divide_vein", T);
  expect([t.session.world()!.stateOf(T), lifecycle(t, item("stapler"))]).toEqual(["vein-divided", "fired"]);

  // the run record: the tower's loss and its restoration, the refused step never entered, one firing with a reload in
  const run = t.session.world()!.runsOf(T).current!;
  const ops = run.entries.map((e) => (e.device ? `${e.device.replace(/^eq:l0-sim-or\./, "")}:${e.op}` : e.op));
  expect(ops.indexOf("vats-tower:power_off")).toBeLessThan(ops.indexOf("vats-tower:white_balance"));
  expect(ops.indexOf("reinsert_scope")).toBeLessThan(ops.indexOf("place_working_ports"));
  expect(ops.filter((o) => o === "divide_vein")).toHaveLength(1);
  expect(run.entries.find((e) => e.op === "divide_vein")).toMatchObject({ actor: A, used: [{ id: item("stapler"), from: "loaded", to: "fired" }] });
  await t.session.close();
}

describe("thoracoscopy training · the release scenario: a loss of view, then an empty stapler", () => {
  it("through the player's interface (the world actions the browser sends)", { timeout: 300_000 }, () => scenario("player"));
  it("through an agent's interface (its tools)", { timeout: 300_000 }, () => scenario("agent"));
});
