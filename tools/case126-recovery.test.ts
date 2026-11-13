/**
 * Case 126 · from the operating table to the recovery bed (the 2026-11-12 audit, findings 01 and 02, and its first
 * release scenario), in-world, in OR 7 and the PACU of the IMPF Surgery Hospital:
 *
 *   1. speech follows consciousness and the airway, each by its own event — woken (`wake`), extubated (`extubate`) —
 *      never a checklist step, a phase or a room: neither the Sign Out nor the transfer to recovery gives the patient
 *      his voice back; woken with the tube still in, he cannot speak, and the narration says why;
 *   2. the recovery handover is given at a recovery bed, in person, to the recovery nurse: refused in OR 7 (whoever asks
 *      — an agent's tool, the learner's own action), refused while no recovery nurse is at the bed; the advance report
 *      from theatre and the acceptance at the bed are two records with their own times; the record keeps where it was
 *      given, who received him and what was handed over; the arrival is recorded from the world;
 *   3. the release scenario: an awake transfer and an intubated one — when he can speak, which bed he reaches, who
 *      accepts him (and, intubated, the responsible anaesthetist who comes with him) — once through an agent's tools,
 *      once through the learner's own actions.
 *
 * Each run starts after the abdomen is closed on a reconciled count. `tools/check.sh` copies this file into
 * `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards; the repository root comes from
 * $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import { assess, responsibleAnaesthetist, type ClinicalAction } from "@clinicalcraft/core";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const BOARD = "eq:or-7.checklist";
const COUNT = "eq:or-7.count-board";
const WAND = "eq:or-7.rf-wand";
const CIRCULATOR = "staff:or-7.circulating-nurse";
const RECOVERY_NURSE = "staff:pacu.nurse";
const QUESTION = "What brought you in and for how long?";
/** The refusal of a question nobody can answer (the engine's `cannot-answer`). */
const CANNOT = /The patient cannot speak now, and nobody here can answer for them/;

let seq = 0;
async function act(t: TestSession, actorId: string, operation: string, targetId?: string, goal?: NavGoal) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `r-${++seq}`, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}) } });
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
/** The learner's own action (a button in the browser): the same gate as the agent's tool, its refusal an error event. */
async function own(t: TestSession, action: ClinicalAction) {
  const events = await t.session.run({ type: "clinical_action", action });
  return { events, errors: msgsOf(events, "error").map((e) => e.message), warnings: msgsOf(events, "warning").map((e) => e.message) };
}
const record = (t: TestSession, id: string) => t.session.state.interventions.filter((r) => r.interventionId === id && !r.invalid);
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
const distanceToPatient = (t: TestSession, actorId: string) => {
  const w = t.session.world()!;
  const a = w.actor(actorId)!;
  const p = w.patientPlace()!;
  return a.pose.level === p.level ? Math.hypot(a.pose.x - p.x, a.pose.z - p.z) : Infinity;
};

/** OR 7 to the closure of the abdomen on a reconciled count (the release acceptance run's way there). */
async function closed(): Promise<TestSession> {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)!.def;
  const facility = pack.facilities.get("impf-surgery-hospital")!.def;
  const catalogs = facility.catalogs.map((id) => pack.catalogs.get(id)!.def);
  const t = await makeSession({ caseDef, facility, catalogs, settingsPatch: { embodiment: "embodied", approvalMode: "bypass" } });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  await ok(t, "navigate_to", { target: "patient" });
  for (const q of [QUESTION, "Do you have any drug allergies?", "When did you last eat?"]) await ok(t, "ask_patient", { question: q });
  const sol = caseDef.solution;
  for (const a of sol.slice(1, sol.findIndex((x) => x.type === "intervene" && x.interventionId === "attach-monitor")))
    expect(t.session.dispatch({ ...a, by: "system" } as ClinicalAction).rejected, JSON.stringify(a)).toBeUndefined();
  await ok(t, "delegate_task", { role: CIRCULATOR, task: "attach_monitor" });
  await done(t, PRIMARY_ACTOR, "sign_in", BOARD);
  await done(t, CIRCULATOR, "baseline_count", COUNT);
  await ok(t, "navigate_to", { target: "patient" });
  await ok(t, "intervene", { intervention_id: "induction" });
  await done(t, PRIMARY_ACTOR, "time_out", BOARD);
  await ok(t, "navigate_to", { target: "patient" });
  for (const s of sol.filter((x): x is Extract<ClinicalAction, { type: "operate" }> => x.type === "operate" && x.op.op !== "close")) await ok(t, "operate", { ...s.op });
  await done(t, CIRCULATOR, "pick_up", WAND);
  expect((await act(t, CIRCULATOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
  await done(t, CIRCULATOR, "scan", WAND);
  await done(t, CIRCULATOR, "final_count", COUNT);
  await ok(t, "navigate_to", { target: "patient" });
  await ok(t, "operate", { op: "close" });
  expect(t.session.state.procedure).toMatchObject({ closed: true });
  expect(t.session.world()!.patientPlace()).toMatchObject({ room: "or-7" });
  return t;
}

describe("Case 126 · from the operating table to the recovery bed", () => {
  it("speech follows consciousness and the airway (finding 01): neither the Sign Out nor the transfer to recovery gives him his voice; woken, the tube still in, he cannot speak; extubated, he answers", { timeout: 300_000 }, async () => {
    const t = await closed();
    const asked = [...t.session.state.asked];
    const say = async () => (await tool(t, "ask_patient", { question: QUESTION })).output;
    await ok(t, "navigate_to", { target: "patient" });
    expect(await say()).toMatch(/cannot answer: under general anaesthesia/);
    // the Sign Out — the phase moves on to recovery — and no emergence decided: still no voice
    await done(t, PRIMARY_ACTOR, "sign_out", BOARD);
    expect(t.session.state.phase).toBe("recovery");
    expect(t.session.state.decisions).not.toHaveProperty("emergence");
    await ok(t, "navigate_to", { target: "patient" });
    expect(await say()).toMatch(/cannot answer: under general anaesthesia/);
    // taken to recovery intubated: another room, still no voice
    await ok(t, "intervene", { intervention_id: "transfer-pacu" });
    expect(t.session.world()!.patientPlace()).toMatchObject({ room: "pacu" });
    await ok(t, "navigate_to", { target: "patient" });
    expect(await say()).toMatch(/cannot answer: under general anaesthesia/);
    // the extubation decided — a decision is not an act: still no voice
    await ok(t, "answer_decision", { decision_id: "emergence", option_ids: ["criteria", "swallow-after"] });
    expect(await say()).toMatch(/cannot answer: under general anaesthesia/);
    // woken: awake, the tube still in — no voice, and the narration says so
    await ok(t, "intervene", { intervention_id: "wake" });
    expect(await say()).toMatch(/cannot answer: awake, but the tracheal tube is still in/);
    expect(t.session.state.asked).toEqual(asked);
    // extubated: he answers, from the record
    await ok(t, "intervene", { intervention_id: "extubate" });
    expect(await say()).toMatch(/abdominal pain and fever/i);
    await t.session.close();
  });

  it("the recovery handover (finding 02): refused in OR 7 and while no recovery nurse is at the bed; the advance report and the acceptance are two records with their own times; where, by whom, what", { timeout: 300_000 }, async () => {
    const t = await closed();
    await ok(t, "intervene", { intervention_id: "wake" });
    await ok(t, "intervene", { intervention_id: "extubate" });
    await done(t, PRIMARY_ACTOR, "sign_out", BOARD);
    // the advance report: by phone, from theatre — its own record, with what the record held then
    await ok(t, "intervene", { intervention_id: "pacu-report" });
    const [report] = record(t, "pacu-report");
    expect(report).toMatchObject({ handover: { speaks: true, procedure: { closed: true, specimen: "extracted", injuries: [] } } });
    expect(report).not.toHaveProperty("place");
    // the handover in OR 7: refused — by the agent's tool and by the learner's own action — and nothing recorded
    await ok(t, "navigate_to", { target: "patient" });
    const agent = await tool(t, "intervene", { intervention_id: "pacu-handover" });
    expect(agent.ok).toBe(false);
    expect(agent.output).toMatch(/This is done with .* in a recovery room \(PACU\) — they are in .*: take them there first/);
    const learner = await own(t, { type: "intervene", interventionId: "pacu-handover" });
    expect(learner.errors.join("\n")).toMatch(/recovery room \(PACU\)/);
    expect(t.session.state.interventions.filter((r) => r.interventionId === "pacu-handover")).toEqual([]);
    // where he arrived is the world's to say: a hand-entered arrival is refused
    expect((await own(t, { type: "arrival", room: "pacu", kind: "recovery" })).errors.join("\n")).toMatch(/never entered by hand/);
    expect(t.session.state.arrivals).toBeUndefined();
    // the transfer: the world moves him to a recovery bay, the record keeps the arrival, the recovery nurse meets him
    const before = t.session.state.clock;
    await ok(t, "intervene", { intervention_id: "transfer-pacu" });
    const place = t.session.world()!.patientPlace()!;
    expect(place).toMatchObject({ room: "pacu" });
    expect(place.slot).toMatch(/^pacu\.bay-\d$/);
    expect(t.session.state.arrivals).toEqual([{ room: "pacu", kind: "recovery", slot: place.slot, at: expect.any(Number), seq: expect.any(Number) }]);
    expect(distanceToPatient(t, RECOVERY_NURSE)).toBeLessThan(3);
    // she is called away from the bed: refused — the handover is made to a recovery nurse at the bed
    expect((await act(t, RECOVERY_NURSE, "navigate", undefined, { kind: "interact", id: "eq:pacu.station" })).status).toBe("completed");
    await ok(t, "navigate_to", { target: "patient" });
    const alone = await tool(t, "intervene", { intervention_id: "pacu-handover" });
    expect(alone.ok).toBe(false);
    expect(alone.output).toMatch(/handed over in person to a recovery nurse at .*'s side — none is there now/);
    // back at the bed: given, and accepted by her
    expect((await act(t, RECOVERY_NURSE, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
    await ok(t, "intervene", { intervention_id: "pacu-handover" });
    const [handover] = record(t, "pacu-handover");
    expect(handover).toMatchObject({
      place: { room: "pacu", kind: "recovery", slot: place.slot },
      receivedBy: "pacu.nurse",
      handover: { speaks: true, airway: ["induction", "wake", "extubate"], procedure: { closed: true }, count: expect.any(String) },
    });
    // two records, two times: the report from theatre, then the acceptance at the bed
    expect(handover!.at).toBeGreaterThan(report!.at);
    expect(handover!.seq!).toBeGreaterThan(report!.seq!);
    expect(handover!.at).toBeGreaterThanOrEqual(before);
    // the decision that follows needs the valid handover — now there
    await ok(t, "answer_decision", { decision_id: "postop", option_ids: ["resp", "neuro", "bile", "bleed"] });
    await t.session.close();
  });

  it("release scenario 1 (OR → PACU): awake and intubated — when he can speak, which bed he reaches, who accepts him — through an agent's tools and the learner's own actions", { timeout: 600_000 }, async () => {
    // ---- an awake transfer, through an agent's tools
    const awake = await closed();
    await ok(awake, "answer_decision", { decision_id: "emergence", option_ids: ["criteria", "swallow-after"] });
    await ok(awake, "intervene", { intervention_id: "wake" });
    await ok(awake, "intervene", { intervention_id: "extubate" });
    // he speaks in theatre, once extubated
    await ok(awake, "navigate_to", { target: "patient" });
    expect((await tool(awake, "ask_patient", { question: QUESTION })).output).toMatch(/abdominal pain and fever/i);
    await done(awake, PRIMARY_ACTOR, "sign_out", BOARD);
    await ok(awake, "intervene", { intervention_id: "pacu-report" });
    await ok(awake, "intervene", { intervention_id: "transfer-pacu" });
    const bay = awake.session.world()!.patientPlace()!.slot;
    expect(bay).toMatch(/^pacu\.bay-\d$/);
    // awake and extubated: no anaesthetist need come with him; the recovery nurse meets him
    expect(responsibleAnaesthetist(awake.session.caseDef, awake.session.state)).toBe("or-7.anaesthetist");
    expect(distanceToPatient(awake, RECOVERY_NURSE)).toBeLessThan(3);
    await ok(awake, "navigate_to", { target: "patient" });
    await ok(awake, "intervene", { intervention_id: "pacu-handover" });
    expect(record(awake, "pacu-handover")[0]).toMatchObject({ place: { room: "pacu", slot: bay }, receivedBy: "pacu.nurse", handover: { speaks: true } });
    expect(assess(awake.session.caseDef, awake.session.state).safety.verdict).toBe("clear");
    await awake.session.close();

    // ---- an intubated transfer, through the learner's own actions
    const tube = await closed();
    await done(tube, PRIMARY_ACTOR, "sign_out", BOARD);
    // too early is refused: the handover before the transfer, by the learner's button
    expect((await own(tube, { type: "intervene", interventionId: "pacu-handover" })).errors.join("\n")).toMatch(/recovery room \(PACU\)/);
    expect((await own(tube, { type: "intervene", interventionId: "pacu-report" })).errors).toEqual([]);
    expect((await own(tube, { type: "intervene", interventionId: "transfer-pacu" })).errors).toEqual([]);
    const place = tube.session.world()!.patientPlace()!;
    expect(place).toMatchObject({ room: "pacu" });
    // intubated, he cannot speak; the responsible anaesthetist came with him, and the recovery nurse met him
    expect((await act(tube, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(tube) })).status).toBe("completed");
    expect((await own(tube, { type: "ask", itemId: "presentation" })).warnings.join("\n")).toMatch(CANNOT);
    expect(responsibleAnaesthetist(tube.session.caseDef, tube.session.state)).toBe("or-7.anaesthetist");
    expect(distanceToPatient(tube, "staff:or-7.anaesthetist")).toBeLessThan(3);
    expect(distanceToPatient(tube, RECOVERY_NURSE)).toBeLessThan(3);
    // the handover at the bed: accepted by the recovery nurse, the airway handed over as it is — still intubated
    await act(tube, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(tube) });
    expect((await own(tube, { type: "intervene", interventionId: "pacu-handover" })).errors).toEqual([]);
    expect(record(tube, "pacu-handover")[0]).toMatchObject({ place: { room: "pacu", slot: place.slot }, receivedBy: "pacu.nurse", handover: { speaks: false, airway: ["induction"] } });
    // woken and extubated in recovery: then, and only then, he speaks
    expect((await own(tube, { type: "intervene", interventionId: "wake" })).errors).toEqual([]);
    expect((await own(tube, { type: "ask", itemId: "presentation" })).warnings.join("\n")).toMatch(CANNOT);
    expect((await own(tube, { type: "intervene", interventionId: "extubate" })).errors).toEqual([]);
    const spoke = await own(tube, { type: "ask", itemId: "presentation" });
    expect(spoke.warnings).toEqual([]);
    expect(msgsOf(spoke.events, "agent_message").at(-1)?.text).toMatch(/abdominal pain and fever/i);
    expect(assess(tube.session.caseDef, tube.session.state).safety.verdict).toBe("clear");
    await tube.session.close();
  });
});
