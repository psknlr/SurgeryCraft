/**
 * Case 126 release acceptance, end to end in OR 7 (in-world mode, docs/CASE_126.md "Release acceptance"): one run from
 * history to the recovery handover, through the tools an agent uses and the room's own equipment —
 *
 *   history at the bedside → the circulating nurse attaches the monitor (the Sign In stays pending on the record and
 *   the WHO board) → the attending places an explicit anaesthesia hold → induction is refused → the Sign In on the
 *   board → the attending's recorded reassessment releases the hold → the baseline count → induction → the session is
 *   saved and reloaded → the Time Out on the board opens the operation → the operation on the field (observe_field,
 *   operate) → before closure, the counts and the RF scan (the count record, swab by swab) → closure on a reconciled
 *   count → extubation decided apart from oral intake → the Sign Out on the board → the recovery handover;
 *
 * and at the end the clinical record, the physical board and the assessment agree. Patient following (walking with the
 * patient across rooms) is not exercised here: this case's patient stays on the OR 7 table (docs/CASE_126.md).
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal, type WorldActionRequest } from "@clinicalcraft/world";
import { assess, evaluate, type ClinicalAction } from "@clinicalcraft/core";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const BOARD = "eq:or-7.checklist";
const COUNT = "eq:or-7.count-board";
const WAND = "eq:or-7.rf-wand";
const CIRCULATOR = "staff:or-7.circulating-nurse";

let seq = 0;
async function act(t: TestSession, actorId: string, operation: string, targetId?: string, goal?: NavGoal) {
  const request = { actionId: `a-${++seq}`, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}) };
  // the learner's op moves only the learner's own body (PROTOCOL §12.2); a colleague's body is the scenario's to move,
  // through the world facade, as the benchmark's setup moves it
  if (actorId !== PRIMARY_ACTOR) return t.session.world()!.execute(request as WorldActionRequest);
  const events = await t.session.run({ type: "world_action", request });
  const r = msgsOf(events, "world_action_result").at(-1)?.result;
  if (!r) throw new Error(`no result for ${operation}`);
  return r;
}
async function done(t: TestSession, actorId: string, operation: string, targetId?: string) {
  let r = await act(t, actorId, operation, targetId);
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && (r.errorCode === "NOT_IN_RANGE" || r.errorCode === "NOT_VISIBLE" || r.errorCode === "PRECONDITION_FAILED"); i++) {
    expect((await act(t, actorId, "navigate", undefined, r.hint.goal)).status).toBe("completed");
    r = await act(t, actorId, operation, targetId);
  }
  expect(r.status, `${operation} ${targetId ?? ""}: ${r.message}`).toBe("completed");
  return r;
}
async function tool(t: TestSession, name: string, args: Record<string, unknown> = {}) {
  const events = await t.session.run({ type: "external_tool_call", callId: `c-${++seq}`, tool: name, args, allowBypass: true });
  const end = msgsOf(events, "tool_call_end").at(-1);
  if (!end) throw new Error(`no result for ${name}`);
  return end as { ok: boolean; output: string; data?: any };
}
const ok = async (t: TestSession, name: string, args: Record<string, unknown> = {}) => {
  const r = await tool(t, name, args);
  expect(r.ok, `${name} ${JSON.stringify(args)}: ${r.output}`).toBe(true);
  return r;
};
const board = (t: TestSession) => t.session.world()!.inspect(PRIMARY_ACTOR, BOARD)?.state;
const valid = (t: TestSession, id: string) => evaluate(t.session.caseDef, t.session.state, { intervened: id, valid: true });
const validCount = (t: TestSession, id: string) => t.session.state.interventions.filter((r) => r.interventionId === id && r.appropriateness !== "contraindicated").length;

describe("Case 126 · release acceptance in OR 7, history to recovery handover", () => {
  it("one run: the record, the WHO board and the score agree at every checklist step and at the end", { timeout: 300_000 }, async () => {
    const pack = await loadContent({ dirs: [`${ROOT}/content`] });
    const caseDef = pack.cases.get(CASE)!.def;
    const facility = pack.facilities.get("impf-surgery-hospital")!.def;
    const catalogs = facility.catalogs.map((id) => pack.catalogs.get(id)!.def);
    const settingsPatch = { embodiment: "embodied", approvalMode: "bypass" } as const;
    const t = await makeSession({ caseDef, facility, catalogs, settingsPatch });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });

    // ---- history at the bedside (the questions the Sign In needs among them)
    await ok(t, "navigate_to", { target: "patient" });
    for (const q of ["What brought you in and for how long?", "Do you have any drug allergies?", "When did you last eat?"]) await ok(t, "ask_patient", { question: q });
    expect(t.session.state.asked).toEqual(expect.arrayContaining(["presentation", "allergies", "fasting"]));
    // the rest of the work-up and the decisions up to theatre, as the record
    const sol = caseDef.solution;
    for (const a of sol.slice(1, sol.findIndex((x) => x.type === "intervene" && x.interventionId === "attach-monitor")))
      expect(t.session.dispatch({ ...a, by: "system" } as ClinicalAction).rejected, JSON.stringify(a)).toBeUndefined();
    expect(t.session.state.phase).toBe("theatre");
    expect(board(t)).toBe("pending");

    // ---- the monitor: one task; the Sign In pending on the record and the board
    await ok(t, "delegate_task", { role: CIRCULATOR, task: "attach_monitor" });
    expect(valid(t, "attach-monitor")).toBe(true);
    expect(valid(t, "sign-in")).toBe(false);
    expect(board(t)).toBe("pending");

    // ---- an explicit anaesthesia hold; induction refused whatever is claimed
    expect(t.session.dispatch({ type: "hold", interventionId: "induction", placedBy: "attending", reason: "Antithrombotic status unknown after the stroke: ask first.", by: "agent" }).rejected).toBeUndefined();
    await ok(t, "navigate_to", { target: "patient" });
    const refused = await tool(t, "intervene", { intervention_id: "induction" });
    expect(refused.ok).toBe(false);
    expect(refused.output).toMatch(/on hold — placed by attending/);
    expect(t.session.state.interventions.some((r) => r.interventionId === "induction")).toBe(false);

    // ---- the Sign In on the board (its checks made): the case's Sign In
    await done(t, PRIMARY_ACTOR, "sign_in", BOARD);
    expect(valid(t, "sign-in")).toBe(true);
    expect(board(t)).toBe("signed-in");

    // ---- the reassessment releases the hold; the baseline count; induction
    await ok(t, "navigate_to", { target: "patient" });
    await ok(t, "ask_patient", { question: "Since the stroke, do you take aspirin, clopidogrel or a blood thinner?" });
    expect(t.session.dispatch({ type: "release-hold", interventionId: "induction", releasedBy: "attending", reassessment: "Not recorded and he cannot say; bleeding risk accepted for a laparoscopic cholecystectomy: proceed under stated uncertainty.", by: "agent" }).rejected).toBeUndefined();
    await done(t, CIRCULATOR, "baseline_count", COUNT);
    await ok(t, "navigate_to", { target: "patient" });
    await ok(t, "intervene", { intervention_id: "induction" });
    expect((await ok(t, "case_status")).output).toMatch(/· WHO Time Out before incision — a valid attempt, in order\n\s+→ next: intervene \{intervention_id: "time-out"\}/);

    // ---- saved and reloaded between induction and the Time Out
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    await t.session.close();
    const r = await makeSession({
      caseDef,
      facility,
      catalogs,
      settingsPatch,
      resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue },
      embodied: { snapshot: saved.world, team: saved.team },
    });
    expect(board(r)).toBe("signed-in");
    expect(r.session.state.holds?.[0]?.released?.by).toBe("attending");

    // ---- the Time Out on the board opens the operation, once
    await done(r, PRIMARY_ACTOR, "time_out", BOARD);
    expect(r.session.state.phase).toBe("operation");
    expect(board(r)).toBe("timed-out");
    expect(validCount(r, "time-out")).toBe(1);
    expect((await ok(r, "case_status")).output).toMatch(/Operation under way/);

    // ---- the operation on the field, at the table
    await ok(r, "navigate_to", { target: "patient" });
    await ok(r, "observe_field");
    const steps = sol.filter((x): x is Extract<ClinicalAction, { type: "operate" }> => x.type === "operate");
    for (const s of steps.filter((x) => x.op.op !== "close")) await ok(r, "operate", { ...s.op });
    expect(r.session.state.procedure).toMatchObject({ specimen: "extracted" });

    // ---- before closure: the counts and the RF scan, swab by swab in the count record — the team counted when the
    // specimen came out (the scrub nurse, every swab by its identity); the board shows it
    expect(r.session.state.count!.entries.find((e) => e.op === "count" && e.stage === "closing")).toMatchObject({ staff: "or-7.scrub-nurse", missing: [], unexpected: [] });
    expect(r.session.world()!.inspect(PRIMARY_ACTOR, COUNT)?.state).toBe("closing");
    await done(r, CIRCULATOR, "pick_up", WAND);
    expect((await act(r, CIRCULATOR, "navigate", undefined, { kind: "interact", id: r.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id })).status).toBe("completed");
    await done(r, CIRCULATOR, "scan", WAND);
    await done(r, CIRCULATOR, "final_count", COUNT);
    expect(r.session.world()!.inspect(PRIMARY_ACTOR, COUNT)?.state).toBe("reconciled");
    expect(r.session.state.count).toMatchObject({ expected: ["eq:or-7-swab-1", "eq:or-7-swab-2", "eq:or-7-swab-3", "eq:or-7-swab-4", "eq:or-7-swab-5"], unsafe: [] });

    // ---- closure on a reconciled count, then the Sign Out on the board
    await ok(r, "navigate_to", { target: "patient" });
    await ok(r, "operate", { op: "close" });
    expect(r.session.state.procedure).toMatchObject({ specimen: "extracted", closed: true });
    expect(r.session.state.count!.unsafe).toEqual([]);
    // extubation decided apart from oral intake
    await ok(r, "answer_decision", { decision_id: "emergence", option_ids: ["criteria", "swallow-after"] });
    await done(r, PRIMARY_ACTOR, "sign_out", BOARD);
    expect(r.session.state.phase).toBe("recovery");
    expect(board(r)).toBe("signed-out");

    // ---- the recovery handover
    await ok(r, "navigate_to", { target: "patient" });
    await ok(r, "intervene", { intervention_id: "pacu-handover" });
    await ok(r, "answer_decision", { decision_id: "postop", option_ids: ["resp", "neuro", "bile", "bleed"] });

    // ---- the record, the board and the score agree
    for (const id of ["attach-monitor", "sign-in", "induction", "time-out", "sign-out", "pacu-handover"]) expect(validCount(r, id), id).toBe(1);
    expect(r.session.state.interventions.filter((x) => x.invalid)).toEqual([]);
    const a = assess(caseDef, r.session.state);
    for (const id of ["r-signin", "r-timeout", "r-signout", "r-cvs", "r-identify", "r-clips", "r-specimen", "r-closed", "r-emergence", "r-postop"]) {
      const item = a.rubric.find((x) => x.id === id);
      expect(item?.met, id).toBe(true);
      expect(item?.scored, id).not.toBe(false);
    }
    expect(a.safety.verdict).toBe("clear");
    expect(board(r)).toBe("signed-out");
    await r.session.close();
  });
});
