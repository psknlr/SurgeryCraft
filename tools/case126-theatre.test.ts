/**
 * Case 126 in OR 7, embodied: the room, the record and the score agree (the safety repairs and the 2.3.0 audit).
 *
 *   1. the operation is done at the table: an `operate` step from another floor is refused with the way to the
 *      patient; at the table it is accepted; after an approval wait the body is checked again before the engine
 *      commits — a surgeon who walked away meanwhile commits nothing;
 *   2. the WHO checklist is one record: attaching the monitor (a delegated nurse) is one task and leaves the Sign In
 *      pending on the record and on the board; a Sign In before its checks is logged invalid; the board's Sign In
 *      after them is the case's Sign In;
 *   3. the Time Out is one checklist action on both paths: `intervene` needs the board's baseline count too; an early
 *      Time Out is logged and leaves the operation locked; the session is saved and reloaded between induction and
 *      the Time Out; the board's Time Out after the reload opens the operation exactly once;
 *   4. a Time Out made at the bedside shows on the board;
 *   5. an explicit hold: placed by the attending (its own tool, in its own name), it refuses induction — whatever
 *      the clinician claims — until the attending records a reassessment and releases it;
 *   6. the way into the operation: `case_status` names the unmet requirement and the next action; `intervene` for
 *      the cholecystectomy points at the operative field; counts and the insufflator never perform it; a world
 *      action's time is clinical time;
 *   7. navigation: a goal with a top-level range stops within it, the arrival says "in view" apart from "within
 *      reach", and the count proceeds without another move;
 *   8. the warmer: "already at destination" only when it is; a destination it cannot reach names what is in the way
 *      and a reachable alternative, which then works;
 *   9. one result status for every role; named colleagues answer as themselves; equipment is not a treatment;
 *  10. the in-world demonstration (offline) works the whole case through the room — the board's prerequisites (the
 *      counts, the RF scan) met — every checklist step valid, then takes him to recovery and hands him over there to the
 *      recovery nurse, 100 %;
 *  11. teaching corrections: the anaesthetist and the attending correct unsafe induction advice, the nurse a
 *      hypothetical turned into history — offline, and when a model endorses the advice.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import { assess, evaluate, monitorAttached, type ClinicalAction } from "@clinicalcraft/core";
import { textScript, toolCallScript } from "./providers/scripted.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const BOARD = "eq:or-7.checklist";
const COUNT = "eq:or-7.count-board";
const TOWER = "eq:or-7.lap-tower";
/** Every staff line said so far (speaker: text). */
const spoken = (t: TestSession) => msgsOf(t.events, "agent_message").map((m) => `${m.speaker}: ${m.text}`);
const WARMER = "eq:or-7.warmer";
const TABLE = "eq:or-7.table";
const CIRCULATOR = "staff:or-7.circulating-nurse";

async function content() {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)?.def;
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!caseDef || !facility) throw new Error(`content missing: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  return { caseDef, facility, catalogs: facility.catalogs.map((id) => pack.catalogs.get(id)!.def) };
}

async function theatre(approvalMode: "bypass" | "default" = "bypass", scripts?: Parameters<typeof makeSession>[0]["scripts"]): Promise<TestSession> {
  const t = await makeSession({ ...(await content()), settingsPatch: { embodiment: "embodied", approvalMode }, ...(scripts ? { scripts } : {}) });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  return t;
}

let seq = 0;
async function act(t: TestSession, actorId: string, operation: string, targetId?: string, goal?: NavGoal, parameters?: Record<string, unknown>) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `t-${++seq}`, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}), ...(parameters ? { parameters } : {}) } });
  const r = msgsOf(events, "world_action_result").at(-1)?.result;
  if (!r) throw new Error(`no result for ${operation}`);
  return r;
}

/** Act, walking where a refusal points (reach and sight) first — the result whatever it is. */
async function tryAt(t: TestSession, operation: string, targetId: string) {
  let r = await act(t, PRIMARY_ACTOR, operation, targetId);
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE"); i++) {
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, r.hint.goal)).status).toBe("completed");
    r = await act(t, PRIMARY_ACTOR, operation, targetId);
  }
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

/** A tool call as the demonstration clinician (the world bridge's path): what the model would see. */
async function tool(t: TestSession, name: string, args: Record<string, unknown> = {}) {
  const events = await t.session.run({ type: "external_tool_call", callId: `x-${++seq}`, tool: name, args, allowBypass: true });
  const end = msgsOf(events, "tool_call_end").at(-1);
  if (!end) throw new Error(`no result for ${name}`);
  return end as { ok: boolean; output: string; data?: any };
}

/** The reference solution up to (not including) the first step matching `stop`, dispatched as the record. */
function upTo(t: TestSession, stop: (a: ClinicalAction) => boolean): void {
  const c = t.session.caseDef;
  for (const a of c.solution.slice(1, c.solution.findIndex((x) => stop(x as ClinicalAction)))) {
    const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${a.type}: ${r.rejected.message}`);
  }
}
const isIv = (id: string) => (a: ClinicalAction) => a.type === "intervene" && a.interventionId === id;

/** The case brought to the table: the reference solution up to the first operative step. */
function toTheTable(t: TestSession): void {
  upTo(t, (a) => a.type === "operate");
  expect(t.session.state.phase).toBe("operation");
}

const level = (t: TestSession, actorId = PRIMARY_ACTOR) => t.session.world()!.actor(actorId)!.pose.level;
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
const ivs = (t: TestSession, id?: string) => t.session.state.interventions.filter((r) => !id || r.interventionId === id);
const validSignIn = (t: TestSession) => evaluate(t.session.caseDef, t.session.state, { intervened: "sign-in", valid: true });
const toBedside = async (t: TestSession) => expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");

describe("Case 126 in OR 7 · the room, the record and the score agree", () => {
  it("an operative step is refused from another floor, accepted at the table", async () => {
    const t = await theatre();
    toTheTable(t);
    const w = t.session.world()!;
    const patient = patientId(t);
    const patientLevel = w.entity(patient)!.level;
    const facility = t.session.facility!;
    const elsewhere = facility.rooms.find((r) => (r.level ?? "L0") !== patientLevel && r.kind !== "corridor");
    expect(elsewhere, "a room on another floor").toBeTruthy();
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "room", id: `room:${elsewhere!.id}` })).status).toBe("completed");
    expect(level(t)).not.toBe(patientLevel);
    expect(await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } })).toBe("SPATIAL_REQUIREMENT_UNMET");
    expect(t.session.state.procedure).toBeUndefined();
    await toBedside(t);
    expect(await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } })).toBeNull();
    expect(t.session.state.procedure?.plan).toBe("three-port-left");
    await t.session.close();
  });

  it("after an approval wait the surgeon's place is checked again: walked away, nothing is committed", async () => {
    const t = await theatre("default");
    toTheTable(t);
    await toBedside(t);
    for (const op of [{ op: "plan-ports", plan: "three-port-left" }, { op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }])
      expect(await clinical(t, { type: "operate", op } as ClinicalAction)).toBeNull();
    const ended: string[] = [];
    let walked = false;
    const off = t.session.subscribe((e) => {
      if (e.msg.type === "approval_request" && !walked) {
        walked = true;
        queueMicrotask(async () => {
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

  it("attaching the monitor is one task: the Sign In stays pending on the record and the board until its checks are made", async () => {
    const t = await theatre();
    upTo(t, isIv("attach-monitor"));
    expect(t.session.state.phase).toBe("theatre");
    const w = t.session.world()!;
    // a Sign In from the board before the monitor: logged invalid, the board still pending, and the board says so
    const early = await act(t, PRIMARY_ACTOR, "sign_in", BOARD);
    const signedEarly = early.status === "failed" && early.hint ? await done(t, PRIMARY_ACTOR, "sign_in", BOARD).catch(() => null) : early;
    expect(signedEarly === null || signedEarly.status === "failed").toBe(true);
    expect(ivs(t, "sign-in").every((r) => r.invalid === true)).toBe(true);
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("pending");
    // the circulating nurse attaches the monitor: one task recorded, the Sign In still pending in both views
    const before = ivs(t).length;
    const monitor = await tool(t, "delegate_task", { role: CIRCULATOR, task: "attach_monitor" });
    expect(monitor.ok, monitor.output).toBe(true);
    expect(ivs(t).slice(before).map((r) => r.interventionId)).toEqual(["attach-monitor"]);
    expect(monitorAttached(t.session.caseDef, t.session.state)).toBe(true);
    expect(validSignIn(t)).toBe(false);
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("pending");
    expect((await tool(t, "case_status")).output).toMatch(/· WHO Sign In before induction — a valid attempt, in order[^\n]*\n\s+→ next: intervene \{intervention_id: "sign-in"\}/);
    // the checks made (the questions were asked on the way to theatre), the board's Sign In is the case's Sign In
    await done(t, PRIMARY_ACTOR, "sign_in", BOARD);
    expect(validSignIn(t)).toBe(true);
    expect(w.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("signed-in");
    await t.session.close();
  });

  it("a record board belongs to the patient's room: OR 1's WHO board shows nothing of this patient and cannot sign them in", async () => {
    const t = await theatre();
    upTo(t, isIv("sign-in"));
    const w = t.session.world()!;
    const boards = w.entities().filter((e) => e.type === "sc-who-checklist").map((e) => e.id);
    expect(boards.length).toBeGreaterThan(1);
    const or1 = boards.find((id) => w.roomOf(id) === "or-1")!;
    expect(or1).toBeDefined();
    expect([w.recordBound(or1), w.recordBound(BOARD)]).toEqual([false, true]);
    // at OR 1's board: refused, pointing at the board in the patient's room; nothing recorded
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: or1 })).status).toBe("completed");
    const r = await act(t, PRIMARY_ACTOR, "sign_in", or1);
    expect(r.status).toBe("failed");
    expect(r.message).toMatch(/records nothing of this patient/);
    expect(r.hint?.goal).toMatchObject({ kind: "interact", id: BOARD });
    expect(ivs(t, "sign-in")).toEqual([]);
    // signed in on OR 7's board: only that board shows it — every other room's board stays pending
    await done(t, PRIMARY_ACTOR, "sign_in", BOARD);
    expect(validSignIn(t)).toBe(true);
    for (const id of boards) expect(w.inspect(PRIMARY_ACTOR, id)?.state ?? "pending", id).toBe(id === BOARD ? "signed-in" : "pending");
    await t.session.close();
  });

  it("an elective operation is entered only on its milestones: monitor, allergies and fasting without a diagnosis, a plan and a risk assessment is not enough", async () => {
    const t = await theatre();
    for (const a of [
      { type: "ask", itemId: "allergies" },
      { type: "ask", itemId: "fasting" },
      { type: "intervene", interventionId: "attach-monitor" },
      { type: "intervene", interventionId: "sign-in" },
      { type: "intervene", interventionId: "induction" },
      { type: "intervene", interventionId: "time-out" },
    ] as ClinicalAction[]) t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    expect(ivs(t, "sign-in").map((r) => r.invalid)).toEqual([true]);
    expect(ivs(t, "time-out").map((r) => r.invalid)).toEqual([true]);
    expect(t.session.state.phase).not.toBe("operation");
    expect(t.session.dispatch({ type: "operate", op: { op: "plan-ports", plan: "three-port-left" }, by: "system" }).rejected?.code).toBe("phase-locked");
    await t.session.close();
  });

  it("the reported operation stays closed on an early request: an invalid review opens nothing", async () => {
    const t = await theatre();
    t.session.dispatch({ type: "intervene", interventionId: "open-historical-review", by: "system" });
    expect(ivs(t, "open-historical-review").map((r) => r.appropriateness)).toEqual(["contraindicated"]);
    expect(t.session.state.phase).not.toBe("review");
    expect(t.session.dispatch({ type: "set-phase", phase: "review", by: "system" }).rejected?.code).toBe("phase-locked");
    expect(t.session.dispatch({ type: "read", investigationId: "operation-record", phase: "review", by: "system" }).rejected).toBeDefined();
    await t.session.close();
  });

  it("the Time Out is one checklist action: an early one leaves surgery locked; after a reload, the board's opens the operation once", async () => {
    const c = await content();
    const t = await theatre();
    upTo(t, isIv("induction"));
    expect(validSignIn(t)).toBe(true);
    await toBedside(t);
    // `intervene` takes the board's own prerequisite: no baseline count, no Time Out — nothing recorded
    const noCount = await tool(t, "intervene", { intervention_id: "time-out" });
    expect(noCount.ok).toBe(false);
    expect(noCount.data?.code ?? noCount.data?.reason).toBeTruthy();
    expect(noCount.output).toMatch(/count/i);
    expect(ivs(t, "time-out")).toEqual([]);
    await done(t, CIRCULATOR, "baseline_count", COUNT);
    // an early Time Out at the bedside (before induction): logged invalid, said so, the board unchanged, surgery locked
    await toBedside(t);
    const early = await tool(t, "intervene", { intervention_id: "time-out" });
    expect(early.ok).toBe(false);
    expect(early.output).toMatch(/INVALID/);
    expect(ivs(t, "time-out")).toMatchObject([{ appropriateness: "contraindicated", invalid: true }]);
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("signed-in");
    expect(t.session.state.phase).toBe("theatre");
    expect(await clinical(t, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } })).toBe("phase-locked");
    // induction; the status names what is met and what is still pending, and the next action
    expect(await clinical(t, { type: "intervene", interventionId: "induction" })).toBeNull();
    const status = (await tool(t, "case_status")).output;
    expect(status).toMatch(/✓ Induce general anaesthesia and intubate/);
    expect(status).toMatch(/· WHO Time Out before incision — a valid attempt, in order \(an attempt is recorded as invalid[^\n]*\n\s+→ next: intervene \{intervention_id: "time-out"\}/);
    // save and reload between induction and the Time Out (the state compared is a deep copy taken at the save)
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const before = structuredClone(t.session.state);
    await t.session.close();
    const r = await makeSession({
      ...c,
      settingsPatch: { embodiment: "embodied", approvalMode: "bypass" },
      resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue },
      embodied: { snapshot: saved.world, team: saved.team },
    });
    const rw = r.session.world()!;
    expect(r.session.state.phase).toBe("theatre");
    expect(rw.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("signed-in");
    expect(rw.inspect(PRIMARY_ACTOR, COUNT)?.state).toBe("baseline");
    expect(r.session.state.interventions.map((x) => [x.interventionId, !!x.invalid])).toEqual(before.interventions.map((x) => [x.interventionId, !!x.invalid]));
    // the board's Time Out after the reload: valid, both views agree, the operation opens exactly once
    const opened: string[] = [];
    const off = r.session.subscribe((e) => {
      if (e.msg.type === "clinical_event" && e.msg.event.type === "phase.changed") opened.push(e.msg.event.to);
    });
    await done(r, PRIMARY_ACTOR, "time_out", BOARD);
    off();
    expect(r.session.state.interventions.filter((x) => x.interventionId === "time-out").map((x) => x.appropriateness)).toEqual(["contraindicated", "indicated"]);
    expect(rw.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("timed-out");
    expect(r.session.state.phase).toBe("operation");
    expect(opened).toEqual(["operation"]);
    // a second Time Out changes nothing (one dose)
    expect((await act(r, PRIMARY_ACTOR, "time_out", BOARD)).status).toBe("failed");
    expect(r.session.state.interventions.filter((x) => x.interventionId === "time-out" && !x.invalid)).toHaveLength(1);
    await r.session.close();
  });

  it("a Time Out made at the bedside shows on the board", async () => {
    const t = await theatre();
    toTheTable(t);
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("timed-out");
    await t.session.close();
  });

  it("an explicit hold refuses induction until the attending who placed it records a reassessment and releases it", async () => {
    const t = await theatre();
    upTo(t, isIv("induction"));
    await toBedside(t);
    // missing information alone places no hold; the attending withholds clearance explicitly
    expect(t.session.state.holds).toBeUndefined();
    expect(t.session.dispatch({ type: "hold", interventionId: "induction", placedBy: "attending", reason: "Antithrombotic status after the stroke is unknown — ask the family and the GP first.", by: "agent" }).rejected).toBeUndefined();
    // the clinician "has approval" and induces: refused, nothing recorded, the refusal names who and why
    const tried = await tool(t, "intervene", { intervention_id: "induction" });
    expect(tried.ok).toBe(false);
    expect(tried.output).toMatch(/on hold — placed by attending: Antithrombotic status/);
    expect(ivs(t, "induction")).toEqual([]);
    expect((await tool(t, "case_status")).output).toMatch(/On hold:\n\s+⏸ Induce general anaesthesia and intubate — placed by attending/);
    // nobody else releases it
    expect(t.session.dispatch({ type: "release-hold", interventionId: "induction", releasedBy: "clinician", reassessment: "I think it is fine.", by: "agent" }).rejected?.code).toBe("requirements-unmet");
    // the attending reassesses and records the decision to proceed under stated uncertainty
    const reassessment = "Still unknown after asking; bleeding risk of a laparoscopic cholecystectomy accepted; proceed, with the team told.";
    expect(t.session.dispatch({ type: "release-hold", interventionId: "induction", releasedBy: "attending", reassessment, by: "agent" }).rejected).toBeUndefined();
    expect(t.session.state.holds?.[0]).toMatchObject({ placedBy: "attending", released: { by: "attending", reassessment } });
    expect((await tool(t, "intervene", { intervention_id: "induction" })).ok).toBe(true);
    expect(ivs(t, "induction")).toHaveLength(1);
    await t.session.close();
  });

  it("the attending places the hold with its own tool, in its own name", async () => {
    const t = await theatre("bypass", [
      toolCallScript([{ id: "h1", name: "place_hold", args: { intervention_id: "induction", reason: "Airway not assessed yet." } }]),
      textScript("I'm not clearing induction yet — the airway has not been assessed."),
    ]);
    upTo(t, isIv("induction"));
    await toBedside(t);
    await t.session.run({ type: "user_message", text: "Can we induce now?", to: "attending" });
    expect(t.session.state.holds).toMatchObject([{ interventionId: "induction", placedBy: "attending", reason: "Airway not assessed yet." }]);
    expect(await clinical(t, { type: "intervene", interventionId: "induction" })).toBe("on-hold");
    await t.session.close();
  });

  it("the way into the operation: the status names what is missing; intervene points at the field; counts and the insufflator never operate", async () => {
    const t = await theatre();
    upTo(t, isIv("time-out"));
    // the cholecystectomy asked for as an intervention: the operative field, and the Time Out still needed
    const asked = await tool(t, "intervene", { query: "laparoscopic cholecystectomy" });
    expect(asked.ok).toBe(false);
    expect(asked.output).toMatch(/is the operation itself, not an intervention: it is done step by step with observe_field and operate at the table/);
    expect(asked.output).toMatch(/· WHO Time Out before incision — a valid attempt, in order\n\s+→ next: intervene \{intervention_id: "time-out"\}/);
    await toBedside(t);
    expect((await tool(t, "observe_field")).output).toMatch(/not under way in this phase[\s\S]*Time Out/);
    // counts and the tower: perioperative tasks, never the operation (and a device's minute is a clinical minute)
    await done(t, CIRCULATOR, "baseline_count", COUNT);
    // OR 7's tower is set up before the list (on, self-tested, white-balanced); its gas is the operation's own
    // pneumoperitoneum, so before the Time Out it is refused with what still opens the operation — nothing starts
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("balanced");
    const gas = await tryAt(t, "start_insufflation", TOWER);
    expect(gas.status).toBe("failed");
    expect(gas.message).toMatch(/the operation is not under way[\s\S]*Time Out/u);
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("balanced");
    expect(t.session.state.procedure).toBeUndefined();
    expect(t.session.state.objectivesDone.operate).toBeUndefined();
    expect(t.session.state.phase).toBe("theatre");
    expect((await tool(t, "case_status")).output).toMatch(/Operation: not under way in this phase\. It is done step by step with observe_field and operate at the table — never with intervene, a count or a device/);
    // the Time Out opens it: under way, nothing done on the field yet
    expect(await clinical(t, { type: "intervene", interventionId: "time-out" })).toBeNull();
    expect((await tool(t, "case_status")).output).toMatch(/Operation under way: no port plan yet/);
    // credit comes from the field: with the operation open and nothing done on it, its outcome items are scored and missed
    const a = assess(t.session.caseDef, t.session.state);
    for (const id of ["r-specimen", "r-closed"]) expect(a.rubric.find((x) => x.id === id), id).toMatchObject({ met: false });
    for (const id of ["r-specimen", "r-closed"]) expect(a.rubric.find((x) => x.id === id)?.scored, id).not.toBe(false);
    await t.session.close();
  });

  it("navigation: a range with a goal is applied, in view is not within reach, and the count proceeds without another move", async () => {
    const t = await theatre();
    upTo(t, isIv("time-out"));
    await toBedside(t);
    const far = await tool(t, "navigate_to", { goal: { kind: "entity", id: COUNT }, range: 6 });
    expect(far.output).toMatch(/range 6\.0 m applied/);
    expect(far.output).toMatch(/in view, but NOT within its reach|not in view/);
    expect(far.data?.arrival?.operationsOutOfRange ?? []).toContain("baseline_count");
    const near = await tool(t, "navigate_to", { goal: { kind: "look", id: COUNT }, range: 2.5 });
    expect(near.ok, near.output).toBe(true);
    expect(near.data?.arrival?.distance).toBeLessThanOrEqual(2.5 + 0.25);
    expect(near.output).toMatch(/From here you can: [^\n]*baseline_count/);
    const count = await tool(t, "interact_object", { target: COUNT, operation: "baseline_count" });
    expect(count.ok, count.output).toBe(true);
    await t.session.close();
  });

  it("the warmer between the clinician and the patient: already there is said; a place it cannot reach names the obstacle and an alternative", async () => {
    const t = await theatre();
    upTo(t, isIv("time-out"));
    const w = t.session.world()!;
    const warmer = w.entity(WARMER)!;
    const patient = w.entity(patientId(t))!;
    // stand beyond the warmer, with the warmer between the clinician and the patient
    const dx = warmer.position.x - patient.position.x;
    const dz = warmer.position.z - patient.position.z;
    const n = Math.hypot(dx, dz);
    w.updatePose(PRIMARY_ACTOR, { ...w.actor(PRIMARY_ACTOR)!.pose, level: warmer.level, x: warmer.position.x + (dx / n) * 0.8, z: warmer.position.z + (dz / n) * 0.8, y: patient.position.y });
    const already = await tool(t, "interact_object", { target: WARMER, operation: "move_to", parameters: { goal: { kind: "interact", id: patientId(t) } } });
    expect(already.ok, already.output).toBe(true);
    expect(already.output).toMatch(/already at its destination, nothing was moved/);
    expect(already.data?.result?.moved).toMatchObject({ displacement: 0, satisfied: true, alreadyAtDestination: true });
    // into the middle of the operating table: not reachable — the obstacle is named, with a free spot instead
    const table = w.entity(TABLE)!;
    const blocked = await tool(t, "interact_object", { target: WARMER, operation: "move_to", parameters: { goal: { kind: "point", x: table.position.x, z: table.position.z, level: table.level, range: 0.3 } } });
    expect(blocked.ok).toBe(false);
    expect(blocked.output).toMatch(/is in the way/);
    const hint = blocked.data?.result?.hint;
    expect(hint?.then?.operation).toBe("move_to");
    const alternative = await tool(t, "interact_object", { target: WARMER, operation: "move_to", parameters: { goal: hint.then.goal } });
    expect(alternative.ok, alternative.output).toBe(true);
    expect(alternative.data?.result?.moved?.satisfied).toBe(true);
    expect(alternative.data?.result?.moved?.displacement).toBeGreaterThan(0.2);
    await t.session.close();
  });

  it("one result status for every role; named colleagues answer as themselves; equipment is not a treatment", async () => {
    const t = await theatre();
    upTo(t, isIv("attach-monitor"));
    // a document of the review does not exist yet: refused, nothing recorded (records in the simulated timeline)
    expect(t.session.dispatch({ type: "order", investigationId: "pathology-record", by: "system" }).rejected).toMatchObject({ code: "not-ready" });
    // a record the case has none of in this phase: "no record" for the clinician — and never "back" for the nurse
    expect(t.session.dispatch({ type: "order", investigationId: "ecg-record", by: "system" }).rejected).toBeUndefined();
    expect((await tool(t, "case_status")).output).toMatch(/ecg-record@theatre\] no record/);
    const nurse = await tool(t, "consult", { role: "nurse", question: "Are any results back?" });
    expect(nurse.output).toMatch(/No result for this phase \(nothing will come back\): [^\n]*ECG/i);
    expect(nurse.output).not.toMatch(/Back and waiting for you: [^\n]*ECG/i);
    // named colleagues, resolved before anything is said
    const anaesthetist = await tool(t, "consult", { staff: "anaesthetist", question: "Is the machine checked?" });
    expect(anaesthetist.output.split("\n")[0]).toBe("To: Dr Tanaka (anaesthesia) (attending)");
    expect(anaesthetist.data?.staffId).toBe("or-7.anaesthetist");
    expect((await tool(t, "consult", { staff: "receptionist", question: "Has the family arrived?" })).output.split("\n")[0]).toBe("To: Ms Xu (admissions) (receptionist)");
    const nobody = await tool(t, "consult", { staff: "the on-call pharmacist", question: "?" });
    expect(nobody.ok).toBe(false);
    expect(nobody.output).toMatch(/Nobody here answers to “the on-call pharmacist”\. You can ask: .*Dr Tanaka/);
    // equipment given as a treatment: said apart from a missing target and an unknown treatment
    expect((await tool(t, "delegate_task", { role: CIRCULATOR, task: "give_intervention", target: WARMER })).output).toMatch(/is a thing in the room, not a treatment/);
    expect((await tool(t, "delegate_task", { role: CIRCULATOR, task: "give_intervention" })).output).toMatch(/needs an intervention/);
    expect((await tool(t, "delegate_task", { role: CIRCULATOR, task: "give_intervention", target: "a unicorn blessing" })).output).toMatch(/no intervention that matches/);
    await t.session.close();
  });

  it("the in-world demonstration (offline) works the case through the room: the board's prerequisites met, every step valid, 100 %", { timeout: 300_000 }, async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: { embodiment: "embodied", approvalMode: "bypass" } });
    t.session.subscribe((e) => {
      if (e.msg.type === "approval_request") t.session.submit({ type: "approval_response", requestId: (e.msg as { requestId: string }).requestId, decision: "approved" });
    });
    await t.session.run({ type: "autopilot", maxTurns: 60 });
    const s = t.session.state;
    expect(s.finished).toBe(true);
    expect(s.interventions.filter((r) => r.invalid)).toEqual([]);
    // the counts the Time Out and the Sign Out need were taken on the count board, the RF wand scanned — the record
    // says so, and the Sign Out was valid
    expect(evaluate(t.session.caseDef, s, { count: { stage: "final", status: ["correct", "reconciled", "excluded"] } })).toBe(true);
    expect(evaluate(t.session.caseDef, s, { intervened: "sign-out", valid: true })).toBe(true);
    // then he left for recovery: arrived at a recovery bay, handed over there in person to the recovery nurse — and
    // OR 7's boards, which belong to the patient's room, no longer show him
    expect(t.session.world()!.patientPlace()).toMatchObject({ room: "pacu" });
    expect(s.arrivals?.at(-1)).toMatchObject({ room: "pacu", kind: "recovery" });
    expect(s.interventions.find((r) => r.interventionId === "pacu-handover")).toMatchObject({ place: { room: "pacu", kind: "recovery" }, receivedBy: "pacu.nurse" });
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, COUNT)?.state).toBe("not-started");
    expect(t.session.world()!.inspect(PRIMARY_ACTOR, BOARD)?.state).toBe("pending");
    const a = assess(t.session.caseDef, s);
    expect(a.score.percent).toBe(100);
    expect(a.safety.verdict).toBe("clear");
    await t.session.close();
  });

  describe("teaching corrections", () => {
    const UNSAFE = "For the RSI I'll give little or no hypnotic before the rocuronium, and an EtCO2 above 40 shows the preoxygenation is adequate. Agreed?";
    it("offline: the anaesthetist and the attending correct both errors; the nurse corrects a hypothetical turned into history", async () => {
      const t = await theatre();
      upTo(t, isIv("induction"));
      for (const who of [{ staff: "anaesthetist" }, { role: "attending" }]) {
        const reply = (await tool(t, "consult", { ...who, question: UNSAFE })).output;
        expect(reply, JSON.stringify(who)).toMatch(/hypnotic[^.]*always goes in before or with the neuromuscular blocker/);
        expect(reply).toMatch(/awareness/);
        expect(reply).toMatch(/end-tidal OXYGEN/);
      }
      const nurse = (await tool(t, "consult", { role: "nurse", question: "The family reported he took antibiotics and paracetamol before coming in." })).output;
      expect(nurse).toMatch(/no family member has been interviewed/);
      await t.session.close();
    });

    it("a model attending that endorses the plan: the correction is said all the same", async () => {
      const t = await theatre("bypass", [textScript("Agreed — that plan is fine, go ahead.")]);
      upTo(t, isIv("induction"));
      const events = await t.session.run({ type: "user_message", text: UNSAFE, to: "attending" });
      const said = msgsOf(events, "agent_message").map((m) => m.text).join("\n");
      expect(said).toMatch(/Agreed/);
      expect(said).toMatch(/awareness/);
      expect(said).toMatch(/end-tidal OXYGEN/);
      // the model was told what to correct
      expect(JSON.stringify(t.provider!.requests[0]!.messages)).toMatch(/must_correct/);
      await t.session.close();
    });

    it("offline: correct statements are left alone — reversing a block, ECG leads and pads in dextrocardia, a reason to wait, a normal EtCO2", async () => {
      const t = await theatre();
      upTo(t, isIv("induction"));
      const LATERALITY = /left and right are always the patient's own/;
      // "reverse" and "right" in one sentence is not a claim about sides
      for (const question of [
        "Can we reverse the neuromuscular block right now?",
        "With dextrocardia I will reverse the arm leads and put the chest leads on the right chest. Correct?",
        "The defibrillator pads go in mirror positions, left and right swapped, for the right-sided heart?",
      ])
        expect((await tool(t, "consult", { staff: "anaesthetist", question })).output, question).not.toMatch(LATERALITY);
      // … while the misconception itself is still corrected
      expect((await tool(t, "consult", { staff: "anaesthetist", question: "Because of situs inversus I should reverse left and right when I read the CT image, yes?" })).output).toMatch(LATERALITY);
      // "reason" and "person" are not his son; nobody has turned a what-if into a family report
      const nurse = (await tool(t, "consult", { role: "nurse", question: "Has antibiotic prophylaxis been given to this person? Any reason to wait?" })).output;
      expect(nurse).not.toMatch(/no family member has been interviewed/);
      // an end-tidal CO₂ beside "oxygenation" is not the preoxygenation misconception
      expect((await tool(t, "consult", { staff: "anaesthetist", question: "EtCO2 is 36 and oxygenation is fine. Happy to carry on?" })).output).not.toMatch(/end-tidal OXYGEN/);
      await t.session.close();
    });
  });

  it("the laparoscopic tower out of service: no gas, no picture — said and recorded; the spare tower fetched from the store brings both back", async () => {
    const t = await theatre();
    toTheTable(t);
    await toBedside(t);
    const w = t.session.world()!;
    w.setAvailability(TOWER, false);
    expect((await tool(t, "operate", { op: "plan-ports", plan: "three-port-left" })).ok).toBe(true);
    // no CO₂: the pneumoperitoneum is refused with why; the record holds what the equipment supplies
    const gas = await tool(t, "operate", { op: "insufflate", pressure: 12 });
    expect(gas.ok).toBe(false);
    expect(gas.output).toMatch(/There is no CO₂ supply: the insufflator is not working \(switched off or out of service\)/u);
    expect(t.session.state.procedure).toMatchObject({ insufflated: false, pressure: 0, supply: { image: false, gas: false } });
    const dark = await tool(t, "observe_field");
    expect(dark.output).toMatch(/No picture: the laparoscopic camera or light source is not working \(switched off or out of service\)/u);
    expect(dark.output).toMatch(/No CO₂ supply/u);
    expect(dark.output).not.toMatch(/In view: Liver/u);
    // the circulating nurse fetches the spare tower from the equipment store — it was off there — and, the operation
    // under way, switches it on herself: it supplies both again
    expect(w.provides("eq:l1-spare-lap-tower")).toEqual([]);
    const fetched = await tool(t, "delegate_task", { role: CIRCULATOR, task: "fetch_equipment", target: "eq:l1-spare-lap-tower" });
    expect(fetched.ok, fetched.output).toBe(true);
    expect(w.roomOf("eq:l1-spare-lap-tower")).toBe("or-7");
    expect(w.inspect(PRIMARY_ACTOR, "eq:l1-spare-lap-tower")?.state).toBe("on");
    expect(spoken(t).join("\n")).toMatch(/Nurse [^:]+: I've switched the Spare laparoscopy tower on — we have an endoscopic camera, a light source and an insufflator again\./u);
    for (const step of [{ op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }]) {
      const r = await tool(t, "operate", step);
      expect(r.ok, `${step.op}: ${r.output}`).toBe(true);
    }
    expect(t.session.state.procedure!.supply).toEqual({ image: true, gas: true });
    expect((await tool(t, "observe_field")).output).toMatch(/In view: Liver/u);
    // the record kept each change of supply apart from the operative steps
    const supplies = t.session.snapshot().actions.filter((a) => a.type === "procedure-supply").map((a) => (a as { supply: { image: boolean; gas: boolean } }).supply);
    expect(supplies.map((x) => [x.image, x.gas])).toEqual([[false, false], [true, true]]);
    await t.session.close();
  });

  it("the tower switched off: no picture and no gas; once the operation begins the circulating nurse switches it on — the device, the record and the field agree at each step", async () => {
    const t = await theatre();
    toTheTable(t);
    await toBedside(t);
    const w = t.session.world()!;
    // OR 7's tower is set up before the list: on, self-tested and white-balanced
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("balanced");
    expect(w.provides(TOWER)).toEqual(["endoscopic-camera", "light-source", "insufflator"]);
    // switched off at the tower: it supplies nothing, and the field says so
    expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: TOWER })).status).toBe("completed");
    expect((await act(t, PRIMARY_ACTOR, "power_off", TOWER)).status).toBe("completed");
    expect([w.inspect(PRIMARY_ACTOR, TOWER)?.state, w.provides(TOWER)]).toEqual(["off", []]);
    // looked at before the plan is chosen: the record already holds that nothing is supplied — as equipment, the
    // operation not begun by it
    const unplanned = await tool(t, "observe_field");
    expect(unplanned.output).toMatch(/Equipment fault/u);
    expect(t.session.state.equipment).toMatchObject({ image: false, gas: false });
    expect(t.session.state.procedure).toBeUndefined();
    // nobody switches it back on before the operation begins (it may be off on purpose)
    await t.session.run({ type: "staff_step" });
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("off");
    // the operation begins: the circulating nurse switches it on with her own body, and says what it gives back
    await toBedside(t);
    const plan = await tool(t, "operate", { op: "plan-ports", plan: "three-port-left" });
    expect(plan.ok, plan.output).toBe(true);
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("on");
    expect(w.actor(CIRCULATOR)?.room).toBe("or-7");
    expect(spoken(t).join("\n")).toMatch(/I've switched the 4K\/3D laparoscopy tower on — we have an endoscopic camera, a light source and an insufflator again\./u);
    expect(t.session.state.procedure!.supply).toMatchObject({ image: true, gas: true });
    for (const step of [{ op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }]) {
      const r = await tool(t, "operate", step);
      expect(r.ok, `${step.op}: ${r.output}`).toBe(true);
    }
    expect((await tool(t, "observe_field")).output).toMatch(/In view: Liver/u);
    const supplies = t.session.snapshot().actions.filter((a) => a.type === "procedure-supply").map((a) => (a as { supply: { image: boolean; gas: boolean } }).supply);
    expect(supplies.map((x) => [x.image, x.gas])).toEqual([[false, false], [true, true]]);
    await t.session.close();
  });

  it("the tower's gas controls are the operation's own pneumoperitoneum: stop and desufflate lets the abdomen down; start before a port plan changes nothing (the round 3 audit)", async () => {
    const t = await theatre();
    toTheTable(t);
    await toBedside(t);
    const w = t.session.world()!;
    // before a port plan, starting the gas is refused by the operation, and the tower stays as it was
    const refused = await tryAt(t, "start_insufflation", TOWER);
    expect(refused.status).toBe("failed");
    expect(refused.message).toMatch(/Choose the port plan first/u);
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("balanced");
    await toBedside(t);
    // at the table: the plan, the pneumoperitoneum, the scope — the field in view
    for (const op of [{ op: "plan-ports", plan: "three-port-left" }, { op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }]) expect((await tool(t, "operate", op)).ok).toBe(true);
    expect((await tool(t, "observe_field")).output).toMatch(/In view: Liver/u);
    // the gas run from the tower: the operation's own step (the operator's), the tower shows it
    await done(t, PRIMARY_ACTOR, "start_insufflation", TOWER);
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("insufflating");
    expect(t.session.state.procedure).toMatchObject({ insufflated: true, pressure: 12 });
    // stop and desufflate: the tower, the record and the picture agree — the abdomen is down
    await done(t, PRIMARY_ACTOR, "stop_insufflation", TOWER);
    expect(w.inspect(PRIMARY_ACTOR, TOWER)?.state).toBe("balanced");
    expect(t.session.state.procedure).toMatchObject({ insufflated: false, pressure: 0 });
    await toBedside(t);
    expect((await tool(t, "observe_field")).output).not.toMatch(/In view: Liver/u);
    const ops = t.session.snapshot().actions.flatMap((a) => (a.type === "operate" ? [a.op.op] : []));
    expect(ops.slice(-5)).toEqual(["plan-ports", "insufflate", "insert", "insufflate", "desufflate"]);
    await t.session.close();
  });

  it("a tower fault before the Time Out is an equipment fault, never the start of the operation: the Time Out stays outstanding and both are said (the round 3 audit)", async () => {
    const t = await theatre();
    upTo(t, isIv("time-out"));
    await toBedside(t);
    const before = (await tool(t, "case_status")).output;
    expect(before).toMatch(/Operation: not under way in this phase/u);
    t.session.world()!.setAvailability(TOWER, false);
    await t.session.run({ type: "staff_step" });
    // recorded as equipment, not as an operation
    expect(t.session.state.procedure).toBeUndefined();
    expect(t.session.state.equipment).toMatchObject({ image: false, gas: false });
    const after = (await tool(t, "case_status")).output;
    expect(after).toMatch(/Operation: not under way in this phase[\s\S]*Time Out/u);
    expect(after).toMatch(/Equipment fault \(the operation has not begun because of it, nor will it count as begun\): no picture — the laparoscopic camera or light source is not working, no CO₂ — the insufflator is not working\./u);
    expect(after).not.toMatch(/no port plan yet/u);
    const field = await tool(t, "observe_field");
    expect(field.ok).toBe(false);
    expect(field.output).toMatch(/not under way in this phase[\s\S]*Equipment fault/u);
    // the gate is unchanged: no step before the Time Out
    expect((await tool(t, "operate", { op: "plan-ports", plan: "three-port-left" })).ok).toBe(false);
    expect(t.session.state.procedure).toBeUndefined();
    // the Time Out opens the operation with the fault as it is: the plan may be chosen, no gas, no picture
    const timeOut = t.session.caseDef.solution.find((x) => isIv("time-out")(x as ClinicalAction))!;
    expect(t.session.dispatch({ ...timeOut, by: "system" } as ClinicalAction).rejected).toBeUndefined();
    expect((await tool(t, "operate", { op: "plan-ports", plan: "three-port-left" })).ok).toBe(true);
    expect(t.session.state.procedure!.supply).toEqual({ image: false, gas: false });
    expect((await tool(t, "operate", { op: "insufflate", pressure: 12 })).ok).toBe(false);
    await t.session.close();
  });

  it("the working tower fails mid-operation: dark and deflated at once, a backup restores it; a save and resume keeps the dark field and the recovery", async () => {
    const t = await theatre();
    toTheTable(t);
    await toBedside(t);
    const w = t.session.world()!;
    for (const step of [{ op: "plan-ports", plan: "three-port-left" }, { op: "insufflate", pressure: 12 }, { op: "insert", port: "A", instrument: "laparoscope" }]) expect((await tool(t, "operate", step)).ok).toBe(true);
    expect((await tool(t, "observe_field")).output).toMatch(/In view: Liver/u);
    // the tower fails with the scope in: the staff's round records it — no picture, no gas, the abdomen down
    w.setAvailability(TOWER, false);
    await t.session.run({ type: "staff_step" });
    expect(t.session.state.procedure).toMatchObject({ insufflated: false, pressure: 0, supply: { image: false, gas: false } });
    const dark = await tool(t, "observe_field");
    expect(dark.output).toMatch(/No picture/u);
    expect(dark.output).not.toMatch(/In view: Liver/u);
    const refused = await tool(t, "operate", { op: "insert", port: "B", instrument: "grasper" });
    expect(refused.ok).toBe(false);
    // saved and resumed while dark: the same field
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    await t.session.close();
    const r = await makeSession({
      ...(await content()),
      settingsPatch: { embodiment: "embodied", approvalMode: "bypass" },
      resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue },
      embodied: { snapshot: saved.world, team: saved.team },
    });
    expect(r.session.state.procedure).toMatchObject({ insufflated: false, pressure: 0, supply: { image: false, gas: false } });
    expect((await tool(r, "observe_field")).output).toMatch(/No picture/u);
    // the spare tower: fetched, switched on by the circulating nurse, the abdomen insufflated again, the picture back
    const fetched = await tool(r, "delegate_task", { role: CIRCULATOR, task: "fetch_equipment", target: "eq:l1-spare-lap-tower" });
    expect(fetched.ok, fetched.output).toBe(true);
    expect(r.session.state.procedure!.supply).toMatchObject({ image: true, gas: true });
    expect((await tool(r, "operate", { op: "insufflate", pressure: 12 })).ok).toBe(true);
    expect((await tool(r, "observe_field")).output).toMatch(/In view: Liver/u);
    const supplies = r.session.snapshot().actions.filter((a) => a.type === "procedure-supply").map((a) => (a as { supply: { image: boolean; gas: boolean } }).supply);
    expect(supplies.map((x) => [x.image, x.gas])).toEqual([[false, false], [true, true]]);
    await r.session.close();
  });
});

