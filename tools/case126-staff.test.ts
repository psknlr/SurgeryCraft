/**
 * Case 126's staff working on their own (ClinicalCraft docs/TEAM.md §5; the engineering recommendations, P1-12),
 * headless in OR 7. The staff's own clock is the `staff_step` op a front-end sends on a timer whatever the learner is
 * looking at — here sent directly, with no act of the learner in between:
 *
 *   1. An ECG ordered before induction: the circulating nurse has the device brought, the study is acquired at the
 *      patient, reported and reviewed by the anaesthetist while the learner only waits (real time passing).
 *   2. Hypotension under anaesthesia: the responsible anaesthetist, away from the head of the table, recognises the
 *      new critical alarm, comes to the patient and says what the monitor shows — once, not on every round.
 *   3. Saved while the nurse's fetch is blocked and reloaded: the same order, nurse and reservation — no second task;
 *      the way opened, it is fulfilled once.
 *   4. Each staff member's role state (goal, task, place, responsibility, held items, reservations, pending
 *      requests, what blocks them) is derived from the record and the world, so a reload agrees by construction.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import type { CaseDefinition, ClinicalAction } from "@clinicalcraft/core";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const ANAESTHETIST = "staff:or-7.anaesthetist";
const NURSE = "staff:or-7.circulating-nurse";
const WORKROOM_DOOR = "door:anaes-workroom:n:0";
const SETTINGS = { embodiment: "embodied", approvalMode: "bypass" } as const;

type Content = { caseDef: CaseDefinition; facility: NonNullable<Parameters<typeof makeSession>[0]>["facility"]; catalogs: NonNullable<Parameters<typeof makeSession>[0]>["catalogs"] };
let cached: Content | null = null;
async function content(): Promise<Content> {
  if (cached) return cached;
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)?.def;
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!caseDef || !facility) throw new Error(`content missing: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  cached = { caseDef, facility, catalogs: facility.catalogs.map((id) => pack.catalogs.get(id)!.def) };
  return cached;
}

let n = 0;
async function tool(t: TestSession, name: string, args: Record<string, unknown> = {}) {
  const events = await t.session.run({ type: "external_tool_call", callId: `s-${++n}`, tool: name, args, allowBypass: true });
  return { ...(msgsOf(events, "tool_call_end").at(-1) as { ok: boolean; output: string; data?: any }), events };
}
async function act(t: TestSession, actorId: string, operation: string, goal?: NavGoal) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `w-${++n}`, actorId, operation, ...(goal ? { goal } : {}) } });
  return msgsOf(events, "world_action_result").at(-1)!.result;
}
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
/** One round of the staff's own clock: what they say in it. */
async function staffStep(t: TestSession): Promise<string[]> {
  const events = await t.session.run({ type: "staff_step" } as never);
  return msgsOf(events, "agent_message").map((m) => `${m.speaker}: ${m.text}`);
}

/** The reference record from `from` up to (not including) the first action `stop` matches. */
function recordUntil(t: TestSession, stop: (a: ClinicalAction) => boolean, from = 1): number {
  const sol = t.session.caseDef.solution;
  let i = from;
  for (; i < sol.length && !stop(sol[i]!); i++) {
    const r = t.session.dispatch({ ...sol[i]!, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${sol[i]!.type}: ${r.rejected.message}`);
  }
  return i;
}
const isInduction = (a: ClinicalAction) => a.type === "intervene" && a.interventionId === "induction";
const isFirstDissection = (a: ClinicalAction) => a.type === "operate" && a.op.op === "dissect";
const isInsufflation = (a: ClinicalAction) => a.type === "operate" && a.op.op === "insufflate";

/** Case 126 with hypotension once the abdomen is insufflated (a scenario variant: the rule is ClinicalCraft's). */
async function hypotensive(): Promise<Content> {
  const base = await content();
  const caseDef = structuredClone(base.caseDef);
  const events = caseDef.physiology!.events!;
  const bleed = events.find((e) => e.id === "ev-major-bleeding")!;
  events.push({ ...structuredClone(bleed), id: "ev-test-hypotension", when: { procedure: { insufflated: true } }, setVitals: { sbp: 72, dbp: 40, hr: 112 } });
  return { ...base, caseDef };
}

describe("Case 126 · staff working on their own", () => {
  it("the ECG ordered before induction is fetched, acquired, reported and reviewed on the staff's own clock — no act of the learner in between", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isInduction);
    expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
    const ordered = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "pre-induction-ecg", indication: "84 years, dextrocardia" });
    expect(ordered.ok).toBe(true);
    // the nurse had the device at the patient and the tracing recorded; reporting and review are still to come
    expect(t.session.state.studies!.orders[0]).toMatchObject({ stage: "acquired", assignee: "or-7.circulating-nurse" });
    expect(t.session.state.studies!.reviews).toEqual([]);
    // the learner only watches: the clock moves (by the system here — in a real-time case, the clock itself), the
    // staff's own clock ticks, and nobody is asked again
    for (let i = 0; i < 40 && !t.session.state.studies!.reviews.length; i++) {
      expect(t.session.dispatch({ type: "advance-time", minutes: 0.5, by: "system" } as ClinicalAction).rejected).toBeUndefined();
      await staffStep(t);
    }
    expect(t.session.state.studies!.reviews).toMatchObject([{ accession: "ecg-12lead-1", by: "or-7.anaesthetist" }]);
    // done: nobody is still responsible for the order
    expect(t.session.staffStates().some((s) => s.responsibility.includes(t.session.state.studies!.orders[0]!.id))).toBe(false);
    await t.session.close();
  });

  it("hypotension under anaesthesia: the responsible anaesthetist answers the new critical alarm at the patient, once", async () => {
    const t = await makeSession({ ...(await hypotensive()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    const at = recordUntil(t, isInsufflation);
    const w = t.session.world()!;
    // before the pneumoperitoneum the anaesthetist steps away from the head of the table (within OR 7)
    expect((await act(t, ANAESTHETIST, "navigate", { kind: "room", id: "or-7" })).status).toBe("completed");
    expect(w.checkSpatial(ANAESTHETIST, { tool: "examine", kind: "examine" }).ok).toBe(false);
    // the abdomen is insufflated, the pressure falls: nobody has acted since
    recordUntil(t, isFirstDissection, at);
    const said = await staffStep(t);
    expect(said).toEqual([expect.stringMatching(/^Dr Tanaka \(anaesthesia\): Alarm: SBP 72 — I'm at the patient and checking it\./)]);
    expect(w.checkSpatial(ANAESTHETIST, { tool: "examine", kind: "examine" }).ok).toBe(true);
    expect(w.roomOf(ANAESTHETIST)).toBe("or-7");
    // the same alarm is not answered again on the next round
    expect(await staffStep(t)).toEqual([]);
    // their role state: the anaesthetic is theirs, at the patient in OR 7
    const role = t.session.staffStates().find((s) => s.actorId === ANAESTHETIST)!;
    expect(role).toMatchObject({ responsibility: expect.arrayContaining(["anaesthesia"]), currentGoal: "keep the anaesthetised patient safe", location: expect.objectContaining({ room: "or-7" }) });
    await t.session.close();
  });

  it("role states agree after a reload: the same responsibilities, places and holdings", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isFirstDissection);
    const before = t.session.staffStates().map((s) => ({ id: s.actorId, responsibility: s.responsibility, room: s.location?.room, held: s.heldItems, reservations: s.reservations }));
    expect(before.find((s) => s.id === ANAESTHETIST)?.responsibility).toContain("anaesthesia");
    const saved = structuredClone(t.session.snapshot());
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world!, team: saved.team } });
    const after = r.session.staffStates().map((s) => ({ id: s.actorId, responsibility: s.responsibility, room: s.location?.room, held: s.heldItems, reservations: s.reservations }));
    expect(after).toEqual(before);
    await r.session.close();
  });

  it("saved while the nurse's fetch is blocked, reloaded: the same order, the same nurse, one assignment — no second task; the way opened, fulfilled once", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isInduction);
    expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
    t.session.world()!.setDoor(WORKROOM_DOOR, { open: false, locked: true });
    expect((await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "pre-induction-ecg" })).ok).toBe(true);
    const o = t.session.state.studies!.orders[0]!;
    expect(o).toMatchObject({ stage: "blocked", assignee: "or-7.circulating-nurse" });
    const nurse = () => (x: TestSession) => x.session.staffStates().find((r) => r.actorId === NURSE)!;
    const role = nurse()(t);
    expect(role.responsibility).toEqual([o.id]);
    expect(role.blockedReason).toMatch(/could not bring the Mobile ECG machine/);

    // the save as a front-end writes it; the record and the nurse's role as they were (deep copies)
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const before = structuredClone(t.session.state.studies!);
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world!, team: saved.team } });
    expect(r.session.state.studies).toEqual(before);
    expect(nurse()(r)).toMatchObject({ responsibility: role.responsibility, reservations: role.reservations, heldItems: role.heldItems, blockedReason: role.blockedReason, location: role.location });
    // still blocked: a round of the staff's clock adds nothing — no second assignment, no second "en route"
    await staffStep(r);
    expect(r.session.state.studies!.orders[0]!.stages).toEqual(before.orders[0]!.stages);
    // the way opened: the same order is fulfilled, once
    r.session.world()!.setDoor(WORKROOM_DOOR, { open: false, locked: false });
    await staffStep(r);
    const after = r.session.state.studies!;
    expect(after.orders).toHaveLength(1);
    expect(after.orders[0]!.stages!.filter((x) => x.stage === "assigned")).toHaveLength(1);
    expect(after.accessions.map((a) => [a.order, a.collector])).toEqual([[o.id, "or-7.circulating-nurse"]]);
    expect(nurse()(r).responsibility).toEqual([]);
    await r.session.close();
  });

  it("an operative step's persistent id: on its tool result and events, resolved by get_action_feedback — the same after a reload", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isFirstDissection);
    expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
    const step = await tool(t, "operate", { op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false });
    expect(step.ok).toBe(true);
    const ids = (msgsOf(step.events, "tool_call_end").at(-1) as { actionIds?: string[] }).actionIds!;
    expect(ids).toHaveLength(1);
    const [id] = ids;
    expect(msgsOf(step.events, "clinical_event").filter((m) => m.event.type === "procedure.step").map((m) => m.actionId)).toEqual([id]);
    const fb = await tool(t, "get_action_feedback", { action_id: id });
    expect(fb.ok).toBe(true);
    expect(fb.output).toMatch(new RegExp(`^${id} · op-\\d+: operate dissect — committed at minute [\\d.]+ by agent; events: procedure.step`));
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world!, team: saved.team } });
    expect((await tool(r, "get_action_feedback", { action_id: id })).output).toBe(fb.output);
    await r.session.close();
  });

  it("an alarm while the anaesthetist is shut out: the blocked walk is said with its reason, never “at the patient”; once the way opens they arrive and say so once — also after a save and resume", async () => {
    const t = await makeSession({ ...(await hypotensive()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    const at = recordUntil(t, isInduction);
    const w = t.session.world()!;
    // before induction the anaesthetist steps into the workroom; then its door is locked
    expect((await act(t, ANAESTHETIST, "navigate", { kind: "room", id: "anaes-workroom" })).status).toBe("completed");
    w.setDoor(WORKROOM_DOOR, { open: false, locked: true });
    recordUntil(t, isFirstDissection, at);
    const atPatient = (x: TestSession) => x.session.world()!.checkSpatial(ANAESTHETIST, { tool: "examine", kind: "examine" }).ok;
    // the alarm is recognised; the way is blocked: said with why, and nobody is said to be at the patient
    const blocked = await staffStep(t);
    expect(blocked).toEqual([expect.stringMatching(/^Dr Tanaka \(anaesthesia\): Alarm: SBP 72 — I can't get to the patient: .+ I need someone at the bedside now\.$/u)]);
    expect(blocked.join(" ")).not.toMatch(/I'm at the patient/u);
    expect(atPatient(t)).toBe(false);
    expect(t.session.state.alarms).toMatchObject([{ id: "alarm-1", vital: "sbp", by: "or-7.anaesthetist", stage: "blocked", reason: expect.any(String) }]);
    // still locked: tried again, nothing new said
    expect(await staffStep(t)).toEqual([]);
    expect(w.roomOf(ANAESTHETIST)).toBe("anaes-workroom");
    // saved while blocked, resumed: the same episode, still outstanding
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const atSave = structuredClone(t.session.state.alarms);
    await t.session.close();
    const r = await makeSession({ ...(await hypotensive()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world!, team: saved.team } });
    expect(r.session.state.alarms).toEqual(atSave);
    // the way opens: the next round they get there, and only now is it said — once
    r.session.world()!.setDoor(WORKROOM_DOOR, { open: false, locked: false });
    expect(await staffStep(r)).toEqual([expect.stringMatching(/^Dr Tanaka \(anaesthesia\): Alarm: SBP 72 — I'm at the patient and checking it\.$/u)]);
    expect(atPatient(r)).toBe(true);
    expect(r.session.world()!.roomOf(ANAESTHETIST)).toBe("or-7");
    expect(r.session.state.alarms![0]!.history.map((h) => h.stage)).toEqual(["detected", "blocked", "arrived"]);
    expect(await staffStep(r)).toEqual([]);
    // and after another save and resume, the arrival is not announced again
    const again = JSON.parse(JSON.stringify(r.session.snapshot()));
    await r.session.close();
    const q = await makeSession({ ...(await hypotensive()), settingsPatch: SETTINGS, resume: { sessionId: again.sessionId, actions: again.actions, messages: again.messages, dialogue: again.dialogue }, embodied: { snapshot: again.world!, team: again.team } });
    expect(await staffStep(q)).toEqual([]);
    expect(q.session.state.alarms).toHaveLength(1);
    await q.session.close();
  });
});

