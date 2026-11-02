/**
 * Case 126 in OR 7, embodied: the room, the record and the score agree (the safety repairs).
 *
 *   1. the operation is done at the table: an `operate` step from another floor is refused with the way to the
 *      patient; at the table it is accepted; after an approval wait the body is checked again before the engine
 *      commits — a surgeon who walked away meanwhile commits nothing;
 *   2. the WHO board shows the case record in both directions: a Sign In on the board is the case's Sign In; a
 *      Time Out made at the bedside shows on the board;
 *   3. an early Time Out is logged, leaves the board as it was and the operation locked; a later Time Out, after
 *      induction, opens it.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import type { ClinicalAction } from "@clinicalcraft/core";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const BOARD = "eq:or-7.checklist";
const COUNT = "eq:or-7.count-board";
const CIRCULATOR = "staff:or-7.circulating-nurse";

async function theatre(approvalMode: "bypass" | "default" = "bypass"): Promise<TestSession> {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)?.def;
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!caseDef || !facility) throw new Error(`content missing: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  const catalogs = facility.catalogs.map((id) => pack.catalogs.get(id)!.def);
  const t = await makeSession({ caseDef, facility, catalogs, settingsPatch: { embodiment: "embodied", approvalMode } });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  return t;
}

let seq = 0;
async function act(t: TestSession, actorId: string, operation: string, targetId?: string, goal?: NavGoal) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `t-${++seq}`, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}) } });
  const r = msgsOf(events, "world_action_result").at(-1)?.result;
  if (!r) throw new Error(`no result for ${operation}`);
  return r;
}

/** Walk where a refusal points (reach and sight), then act — as the browser and agents do. */
async function done(t: TestSession, actorId: string, operation: string, targetId?: string) {
  let r = await act(t, actorId, operation, targetId);
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE"); i++) {
    expect((await act(t, actorId, "navigate", undefined, r.hint.goal)).status).toBe("completed");
    r = await act(t, actorId, operation, targetId);
  }
  expect(r.status, `${operation} ${targetId ?? ""}: ${r.message}`).toBe("completed");
  return r;
}

/** A learner clinical act: its error code (spatial refusal), or the engine's rejection, or null when accepted. */
async function clinical(t: TestSession, action: ClinicalAction): Promise<string | null> {
  const events = await t.session.run({ type: "clinical_action", action });
  const error = msgsOf(events, "error")[0];
  if (error) return error.code ?? "error";
  const rejected = msgsOf(events, "clinical_event").find((e) => e.event.type === "action.rejected");
  return rejected && rejected.event.type === "action.rejected" ? rejected.event.code : null;
}

/** The case brought to the table: the reference solution up to the first operative step, dispatched as the record. */
function toTheTable(t: TestSession): void {
  const c = t.session.caseDef;
  for (const a of c.solution.slice(1, c.solution.findIndex((x) => x.type === "operate"))) {
    const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${a.type}: ${r.rejected.message}`);
  }
  expect(t.session.state.phase).toBe("operation");
}

const level = (t: TestSession, actorId = PRIMARY_ACTOR) => t.session.world()!.actor(actorId)!.pose.level;
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;

describe("Case 126 in OR 7 · the room, the record and the score agree", () => {
  it("an operative step is refused from another floor, accepted at the table", async () => {
    const t = await theatre();
    toTheTable(t);
    const w = t.session.world()!;
    const patient = patientId(t);
    const patientLevel = w.entity(patient)!.level;
    // walk to a room on another floor
    const facility = t.session.facility!;
    const elsewhere = facility.rooms.find((r) => (r.level ?? "L0") !== patientLevel && r.kind !== "corridor");
    expect(elsewhere, "a room on another floor").toBeTruthy();
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "room", id: `room:${elsewhere!.id}` })).status).toBe("completed");
    expect(level(t)).not.toBe(patientLevel);
    const away = await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } });
    expect(away).toBe("SPATIAL_REQUIREMENT_UNMET");
    expect(t.session.state.procedure).toBeUndefined();
    // at the table
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patient })).status).toBe("completed");
    expect(await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } })).toBeNull();
    expect(t.session.state.procedure?.plan).toBe("three-port-left");
    await t.session.close();
  });

  it("after an approval wait the surgeon's place is checked again: walked away, nothing is committed", async () => {
    const t = await theatre("default");
    toTheTable(t);
    const patient = patientId(t);
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patient })).status).toBe("completed");
    for (const op of [{ op: "plan-ports", plan: "three-port-left" }, { op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }])
      expect(await clinical(t, { type: "operate", op } as ClinicalAction)).toBeNull();
    // an agent's high-risk step (a bail-out) waits for approval; meanwhile the body leaves the theatre
    const ended: string[] = [];
    let walked = false;
    const off = t.session.subscribe((e) => {
      if (e.msg.type === "approval_request" && !walked) {
        walked = true;
        queueMicrotask(async () => {
          // the body walks out on the world's action bus while the approval is pending (the browser does this)
          const outside = t.session.facility!.rooms.find((r) => r.id !== "or-7" && r.kind !== "corridor" && (r.level ?? "L0") === level(t))!;
          const walk = await t.session.world()!.execute({ actionId: "walk-out", actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "room", id: `room:${outside.id}` } });
          expect(walk.status).toBe("completed");
          t.session.submit({ type: "approval_response", requestId: (e.msg as { requestId: string }).requestId, decision: "approved" });
        });
      }
      if (e.msg.type === "tool_call_end") ended.push(String((e.msg.data as { code?: string } | undefined)?.code ?? (e.msg.ok ? "ok" : "failed")));
    });
    await t.session.run({ type: "external_tool_call", callId: "x-1", tool: "operate", args: { op: "bailout", strategy: "call-help" } });
    off();
    expect(walked).toBe(true);
    expect(ended).toContain("SPATIAL_PRECONDITION_CHANGED");
    expect(t.session.state.procedure?.bailouts).toEqual([]);
    await t.session.close();
  });

  it("the WHO board and the record agree both ways; an early Time Out is logged and leaves surgery locked", async () => {
    const t = await theatre();
    const c = t.session.caseDef;
    // the case up to the theatre: history, decisions, risk (the solution before the Sign In)
    const signIn = c.solution.findIndex((a) => a.type === "intervene" && a.interventionId === "sign-in");
    for (const a of c.solution.slice(1, signIn)) expect(t.session.dispatch({ ...a, by: "system" } as ClinicalAction).rejected).toBeUndefined();
    expect(t.session.state.phase).toBe("theatre");
    const w = t.session.world()!;
    // the board's Sign In IS the case's Sign In
    await done(t, PRIMARY_ACTOR, "sign_in", BOARD);
    expect(t.session.state.interventions.map((r) => r.interventionId)).toEqual(["sign-in"]);
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("signed-in");
    // an early Time Out at the bedside (before induction): logged, the board unchanged, the operation locked
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
    expect(await clinical(t, { type: "intervene", interventionId: "time-out" })).toBeNull();
    expect(t.session.state.interventions.at(-1)).toMatchObject({ interventionId: "time-out", appropriateness: "contraindicated", invalid: true });
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("signed-in");
    expect(t.session.state.phase).toBe("theatre");
    expect(await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } })).toBe("phase-locked");
    // induction, the baseline count, then the Time Out on the board: valid, and the operation opens
    expect(await clinical(t, { type: "intervene", interventionId: "induction" })).toBeNull();
    await done(t, CIRCULATOR, "baseline_count", COUNT);
    await done(t, PRIMARY_ACTOR, "time_out", BOARD);
    const timeOuts = t.session.state.interventions.filter((r) => r.interventionId === "time-out");
    expect(timeOuts.map((r) => r.appropriateness)).toEqual(["contraindicated", "indicated"]);
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("timed-out");
    expect(t.session.state.phase).toBe("operation");
    await t.session.close();
  });

  it("a Time Out made at the bedside shows on the board", async () => {
    const t = await theatre();
    const c = t.session.caseDef;
    toTheTable(t); // the solution's own Sign In, induction and Time Out, all at the bedside path
    expect(c.solution.some((a) => a.type === "intervene" && a.interventionId === "time-out")).toBe(true);
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("timed-out");
    await t.session.close();
  });
});
