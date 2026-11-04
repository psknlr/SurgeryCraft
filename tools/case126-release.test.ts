/**
 * Case 126's first release scenario (the engineering recommendations, "first release test"), headless in OR 7:
 *
 *   1. Before induction: the published case has no ECG; a new one is ordered; the circulating nurse fetches the
 *      department's mobile ECG machine on their own; the anaesthetist reviews the report, labelled simulated.
 *   2. In the operation: the assistant surgeon (Dr Mori) is asked to hold the neck grasper — acknowledges, walks to
 *      the table and takes the instrument with its traction; the operator dissects on with the other hand.
 *   3. Saved and resumed midway: the actors' positions, the operative field, the device's custody, the report and the
 *      order of the operative steps agree with the run never interrupted.
 *   4. The assistant is called away from the table: the traction falls with their hands, the field shows the window
 *      closed before the operator's next instrument step — the tissue already cleared stays cleared — and the
 *      operator re-grasps before dissecting on. Sent on an errand instead, they let go first and say so.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal, type WorldActionRequest } from "@clinicalcraft/world";
import { observeField, procedureFor, type CaseDefinition, type ClinicalAction, type DomainEvent } from "@clinicalcraft/core";
import type { AgentEvent } from "./protocol.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const ECG = "eq:anaes-workroom-ecg";
const ASSISTANT = "staff:or-7-assistant";
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
  const events = await t.session.run({ type: "external_tool_call", callId: `r-${++n}`, tool: name, args, allowBypass: true });
  return { ...(msgsOf(events, "tool_call_end").at(-1) as { ok: boolean; output: string; data?: any }), events };
}
async function act(t: TestSession, actorId: string, operation: string, goal?: NavGoal) {
  const request = { actionId: `w-${++n}`, actorId, operation, ...(goal ? { goal } : {}) };
  // the learner's op moves only the learner's own body (PROTOCOL §12.2); a colleague's body is the scenario's to move,
  // through the world facade, as the benchmark's setup moves it
  if (actorId !== PRIMARY_ACTOR) return t.session.world()!.execute(request as WorldActionRequest);
  const events = await t.session.run({ type: "world_action", request });
  return msgsOf(events, "world_action_result").at(-1)!.result;
}
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;

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

/** The triangle as the field shows it now (dissection and exposure bins). */
function triangle(t: TestSession) {
  const def = procedureFor(t.session.caseDef, t.session.state)!;
  return observeField(def, t.session.state.procedure!).regions.find((r) => r.id === "hepatocystic-triangle")!;
}
/** The operative steps in the order the record holds them: the op and who did it (a colleague's staff id, or the operator). */
const steps = (t: TestSession) => t.session.snapshot().actions.flatMap((a) => (a.type === "operate" ? [{ op: a.op.op, actor: a.actor ?? null }] : []));
/** The procedure steps a run's events carry (their identity, order and signals). */
const stepEvents = (events: readonly AgentEvent[]) => msgsOf(events, "clinical_event").flatMap((m) => (m.event.type === "procedure.step" ? [m.event as Extract<DomainEvent, { type: "procedure.step" }>] : []));

/** Before induction: the ECG ordered, fetched, recorded, released and reviewed; then into the operation, the operator at the table. */
async function toTheTriangle(): Promise<TestSession> {
  const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  const at = recordUntil(t, isInduction);
  expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
  expect((await tool(t, "retrieve_report", { query: "ECG" })).data?.source).toBe("unavailable");
  const ordered = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "pre-induction-ecg", indication: "84 years, dextrocardia" });
  expect(ordered.output).toMatch(/Nurse Aisyah \(circulating\) will fetch the Mobile ECG machine/);
  expect(t.session.world()!.roomOf(ECG)).toBe("or-7");
  await tool(t, "wait", { minutes: 10 });
  expect(t.session.state.studies!.reviews).toMatchObject([{ accession: "ecg-12lead-1", by: "or-7.anaesthetist" }]);
  // induction and the operation up to the first dissection, then three dissection steps by the operator
  recordUntil(t, isFirstDissection, at);
  for (let i = 0; i < 3; i++) expect((await tool(t, "operate", { op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false })).ok).toBe(true);
  return t;
}

describe("Case 126 · the first release scenario", () => {
  it("the assistant takes the grasper with its traction; saved and resumed, everything agrees; called away, the window closes before the next step", async () => {
    const t = await toTheTriangle();
    const before = triangle(t);
    expect(before.exposure).toBe("good");
    // the assistant is asked to hold the neck grasper: walks to the table, takes it, keeps the traction
    const atTable = (s: TestSession) => s.session.world()!.checkSpatial(ASSISTANT, { tool: "operate", kind: "operate" }).ok;
    expect(atTable(t)).toBe(false);
    const held = await tool(t, "delegate_task", { role: ASSISTANT, task: "hold_traction", params: { port: "B" } });
    expect(held.ok, held.output).toBe(true);
    expect(held.output).toMatch(/Dr Mori \(assistant surgeon\) has the grasper in port B and keeps its traction/);
    expect(atTable(t)).toBe(true);
    expect(t.session.state.procedure!.ports.find((p) => p.site === "B")).toMatchObject({ instrument: "grasper", holder: "or-7-assistant" });
    expect(triangle(t).exposure).toBe("good");
    expect((await tool(t, "observe_field")).output).toMatch(/grasper — held by Dr Mori \(assistant surgeon\)/);
    // the operator cannot work the port the assistant holds; dissects on with port C
    expect((await tool(t, "operate", { op: "retract", port: "B", structure: "gallbladder-infundibulum", direction: ["patient-left", "caudal"] })).output).toMatch(/or-7-assistant holds the grasper in port "B"/);
    expect((await tool(t, "operate", { op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false })).ok).toBe(true);
    // a hand-entered step in the assistant's name is refused
    const forged = await t.session.run({ type: "clinical_action", action: { type: "operate", op: { op: "release", structure: "gallbladder-infundibulum" }, actor: "or-7-assistant" } as ClinicalAction });
    expect(msgsOf(forged, "error")[0]).toMatchObject({ code: "permission_denied" });

    // save and resume midway: positions, field, custody, report, step order
    // the save as a front-end writes it (a deep copy, through JSON), and the state it was taken from (a deep copy too:
    // nothing later can change what is compared)
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const atSave = structuredClone(t.session.state);
    const w0 = t.session.world()!;
    const where = (w: typeof w0, id: string) => {
      const p = w.actor(id)?.pose ?? w.entity(id)!.position;
      return { room: w.roomOf(id), x: Math.round(p.x * 100) / 100, z: Math.round(p.z * 100) / 100 };
    };
    const bodies = [ASSISTANT, PRIMARY_ACTOR, "staff:or-7.circulating-nurse", "staff:or-7.anaesthetist", ECG];
    const positions = bodies.map((id) => where(w0, id));
    const order = steps(t);
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world, team: saved.team } });
    expect(atSave.procedure).toBeDefined();
    expect(r.session.state.procedure).toEqual(atSave.procedure);
    expect(r.session.state.procedure!.ports.find((p) => p.site === "B")!.holder).toBe("or-7-assistant");
    expect(atSave.studies?.reports.length).toBeGreaterThan(0);
    expect(r.session.state.studies).toEqual(atSave.studies);
    expect(bodies.map((id) => where(r.session.world()!, id))).toEqual(positions);
    expect(steps(r)).toEqual(order);
    expect(r.session.state.procedure!.counters.steps).toBe(atSave.procedure!.counters.steps);
    expect(r.session.state.anaesthesia).toEqual(atSave.anaesthesia);
    expect(r.session.state.clock).toBe(atSave.clock);
    expect((await tool(r, "read_study", { query: "ECG" })).output).toMatch(/^Simulated investigation · 12-lead ECG/);

    // the assistant is called away: the traction goes with their hands, before the operator's next instrument step
    const cleared = triangle(r).dissection;
    // (the scenario moves the assistant's body, through the world facade)
    const from = r.events.length;
    expect((await r.session.world()!.execute({ actionId: "away", actorId: ASSISTANT, operation: "navigate", goal: { kind: "room", id: "l1-control" } })).status).toBe("completed");
    const awayEvents = r.events.slice(from);
    expect(steps(r).slice(-2)).toEqual([
      { op: "release", actor: "or-7-assistant" },
      { op: "hand-over", actor: "or-7-assistant" },
    ]);
    const [release, handBack] = stepEvents(awayEvents);
    expect(release).toMatchObject({ op: "release", actor: "or-7-assistant", signals: ["exposure-lost"] });
    expect(handBack!.seq!).toBeGreaterThan(release!.seq!);
    expect(msgsOf(awayEvents, "agent_message").map((m) => `${m.speaker}: ${m.text}`)).toContainEqual(expect.stringMatching(/^Dr Mori \(assistant surgeon\): Dr Mori \(assistant surgeon\) let go of the grasper in port B: they are no longer at the table\. The traction has gone/));
    const now = triangle(r);
    expect(now.exposure).not.toBe("good");
    expect(now.dissection).toBe(cleared);
    expect(r.session.state.procedure!.ports.find((p) => p.site === "B")).toMatchObject({ instrument: "grasper" });
    expect(r.session.state.procedure!.ports.find((p) => p.site === "B")!.holder).toBeUndefined();
    // the operator re-grasps, and the window opens again
    expect((await tool(r, "operate", { op: "retract", port: "B", structure: "gallbladder-infundibulum", direction: ["patient-left", "caudal"] })).ok).toBe(true);
    expect(triangle(r).exposure).toBe("good");
    await r.session.close();
  });

  it("asked to leave the anaesthetised patient, the anaesthetist first has the duty anaesthetist take over and records it", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isFirstDissection);
    expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
    const w = t.session.world()!;
    expect(w.roomOf("staff:l1-anaesthetist")).toBe("l1-control");
    const events = await t.session.run({ type: "user_message", text: "Dr Tanaka, please show me the way to theatre control.", to: "attending", staff: "or-7.anaesthetist" } as never);
    const said = msgsOf(events, "agent_message").map((m) => `${m.speaker}: ${m.text}`);
    expect(said[0]).toMatch(/^Dr Tanaka \(anaesthesia\): The patient is under anaesthesia: I'll hand over first\. Calling Dr Wang \(duty consultant anaesthetist\) to take over\./);
    expect(said).toContainEqual(expect.stringMatching(/^Dr Wang \(duty consultant anaesthetist\): I've taken over the anaesthetic from Dr Tanaka \(anaesthesia\)\./));
    // the colleague came to the patient before Dr Tanaka went; the hand-over is in the record
    expect(w.roomOf("staff:l1-anaesthetist")).toBe("or-7");
    expect(t.session.state.anaesthesia).toMatchObject({ responsible: "l1-anaesthetist", handoverStatus: "transferred" });
    const h = t.session.state.anaesthesia!.handovers[0]!;
    expect(h).toMatchObject({ from: "or-7.anaesthetist", to: "l1-anaesthetist", accepted: true });
    // the hand-over carries what the record holds: the vitals now, the drugs given
    expect(Object.keys(h.haemodynamics)).toEqual(expect.arrayContaining(["hr", "sbp"]));
    expect(said.find((l) => l.startsWith("Dr Wang"))).toMatch(/Hand-over — airway: .+; ventilation: .+; haemodynamics: HR \d+/);
    expect(w.roomOf("staff:or-7.anaesthetist")).toBe("l1-control");
    // Dr Wang is now bound by the same rule: a fetch, or a direct move out of OR 7, is refused
    const fetch = await t.session.run({ type: "user_message", text: "Dr Wang, please fetch the ECG machine.", to: "attending", staff: "l1-anaesthetist" } as never);
    expect(msgsOf(fetch, "agent_message").map((m) => m.text).join(" ")).toMatch(/Continuous anaesthesia responsibility is required\. Arrange relief before leaving the patient/);
    const away = await act(t, "staff:l1-anaesthetist", "navigate", { kind: "room", id: "l1-control" });
    expect(away).toMatchObject({ status: "failed", errorCode: "NOT_AUTHORIZED" });
    expect(w.roomOf("staff:l1-anaesthetist")).toBe("or-7");
    // a hand-over is never typed in
    const forged = await t.session.run({ type: "clinical_action", action: { type: "anaesthesia", anaesthesia: { op: "request-relief", from: "l1-anaesthetist", to: "or-7.anaesthetist" } } as ClinicalAction });
    expect(msgsOf(forged, "error")[0]).toMatchObject({ code: "permission_denied" });
    await t.session.close();
  });

  it("after the hand-over a new ECG is reviewed by the anaesthetist who took over, not the one who left; a reviewer named on the order stays theirs; both kept after a save and resume (the follow-up audit)", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isFirstDissection);
    const toPatient = async (x: TestSession) => expect((await act(x, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(x) })).status).toBe("completed");
    await toPatient(t);
    await t.session.run({ type: "user_message", text: "Dr Tanaka, please show me the way to theatre control.", to: "attending", staff: "or-7.anaesthetist" } as never);
    expect(t.session.state.anaesthesia).toMatchObject({ responsible: "l1-anaesthetist", handoverStatus: "transferred" });
    await toPatient(t);
    // a new ECG for the anaesthetist (the study's default reviewer): resolved when the report is ready
    const ordered = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "post-handover" });
    expect(ordered.ok, ordered.output).toBe(true);
    // a second one that names its reviewer: Dr Tanaka, asked to look at it from theatre control
    const named = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "for-tanaka", reviewer: "Dr Tanaka" });
    expect(named.ok, named.output).toBe(true);
    await tool(t, "wait", { minutes: 12 });
    const reviews = () => t.session.state.studies!.reviews.map((r) => ({ by: r.by, basis: r.basis }));
    expect(reviews()).toEqual([
      { by: "l1-anaesthetist", basis: "responsible" },
      { by: "or-7.anaesthetist", basis: "named" },
    ]);
    // the outgoing anaesthetist is in theatre control: never the default reviewer of what came after
    expect(t.session.world()!.roomOf("staff:or-7.anaesthetist")).toBe("l1-control");
    const read = await tool(t, "read_study", { order: "ord-1" });
    expect(read.output).toMatch(/Dr Wang \(duty consultant anaesthetist\) \(the anaesthetist responsible now\) reviewed the 12-lead ECG/u);
    expect((await tool(t, "read_study", { order: "ord-2" })).output).toMatch(/Dr Tanaka \(anaesthesia\) \(the reviewer named on the order\) reviewed/u);
    // saved and resumed: who reviewed, and why, unchanged
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const before = reviews();
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world!, team: saved.team } });
    expect(r.session.state.studies!.reviews.map((x) => ({ by: x.by, basis: x.basis }))).toEqual(before);
    await r.session.close();
  });

  it("no relief arranged: the anaesthetist of an induced patient may not leave — by a request to fetch, a direct move or a delegated task (every path goes through the one world-action guard)", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isFirstDissection);
    const w = t.session.world()!;
    const fetch = await t.session.run({ type: "user_message", text: "Dr Tanaka, please fetch the ECG machine.", to: "attending", staff: "or-7.anaesthetist" } as never);
    expect(msgsOf(fetch, "agent_message").map((m) => m.text).join(" ")).toMatch(/Continuous anaesthesia responsibility is required\. Arrange relief before leaving the patient/);
    expect(w.roomOf("staff:or-7.anaesthetist")).toBe("or-7");
    expect(w.roomOf(ECG)).toBe("anaes-workroom");
    expect(await act(t, "staff:or-7.anaesthetist", "navigate", { kind: "room", id: "anaes-workroom" })).toMatchObject({ status: "failed", errorCode: "NOT_AUTHORIZED" });
    const delegated = await tool(t, "delegate_task", { role: "staff:or-7.anaesthetist", task: "fetch_equipment", target: ECG });
    expect(delegated.ok).toBe(false);
    expect(delegated.output).toMatch(/Continuous anaesthesia responsibility is required/);
    // within OR 7 they move freely
    expect((await act(t, "staff:or-7.anaesthetist", "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");
    expect(t.session.state.anaesthesia).toBeUndefined();
    await t.session.close();
  });

  it("before induction nobody needs to take over: the anaesthetist just goes", async () => {
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    recordUntil(t, isInduction);
    const events = await t.session.run({ type: "user_message", text: "Dr Tanaka, please show me the way to theatre control.", to: "attending", staff: "or-7.anaesthetist" } as never);
    expect(msgsOf(events, "agent_message").map((m) => m.text).join(" ")).not.toMatch(/hand over/);
    expect(t.session.world()!.roomOf("staff:l1-anaesthetist")).toBe("l1-control");
    expect(t.session.state.notes.some((n) => /Anaesthesia handed over/.test(n.text))).toBe(false);
    await t.session.close();
  });

  it("case_status recommends only what would run: with the specimen still in, closure, emergence and the Sign Out are not 'next'", async () => {
    const t = await toTheTriangle();
    const st = await tool(t, "case_status");
    const recs = st.data.recommendations as { action: string; available: boolean; blockedBy: string[] }[];
    const of = (re: RegExp) => recs.find((r) => re.test(r.action));
    expect(of(/op: "close"/)).toMatchObject({ available: false, blockedBy: [expect.stringMatching(/specimen is still inside/)] });
    expect(of(/"emergence"/)).toMatchObject({ available: false, blockedBy: ["Finish the operation first."] });
    expect(of(/"sign-out"/)).toMatchObject({ available: false, blockedBy: [expect.stringMatching(/^out of order — first: /)] });
    expect(st.output).toMatch(/→ not yet: at the table: observe_field, then operate \{op: "close"\} — The specimen is still inside/);
    expect(st.output).not.toMatch(/→ next: [^\n]*(op: "close"|"emergence"|"sign-out")/);
    await t.session.close();
  });

  it("a consultation is not a hint: Dr Tanaka answers from the anaesthetic side, the hint count unchanged", async () => {
    const t = await toTheTriangle();
    const hints = t.session.state.hints;
    const events = await t.session.run({ type: "user_message", text: "Dr Tanaka, what are your anaesthetic concerns?", to: "attending", staff: "or-7.anaesthetist" } as never);
    const reply = msgsOf(events, "agent_message").find((m) => /Tanaka/.test(m.speaker))!;
    expect(reply.text).toMatch(/^From the anaesthetic side: the patient is under general anaesthesia\./);
    expect(reply.text).toMatch(/Allergy status remains unknown \(asked; not recorded\)\. Fasting status remains unknown/);
    expect(reply.text).not.toMatch(/\/hint|objective/i);
    // the same through consult, and words that sound like a request for help: still a consultation
    await tool(t, "consult", { staff: "Dr Tanaka", question: "I'm stuck — can you help me with the ventilation?" });
    expect(t.session.state.hints).toBe(hints);
    await t.session.close();
  });

  it("the Sign In states the unknowns as unknown — never 'confirmed'", async () => {
    const c = (await content()).caseDef;
    const t = await makeSession({ ...(await content()), settingsPatch: { embodiment: "clinical", approvalMode: "bypass" } });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    const at = c.solution.findIndex((a) => a.type === "intervene" && a.interventionId === "sign-in");
    for (const a of c.solution.slice(1, at)) t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    expect(t.session.state.asked).toEqual(expect.arrayContaining(["allergies", "fasting"]));
    const signIn = await tool(t, "intervene", { intervention_id: "sign-in" });
    expect(signIn.ok, signIn.output).toBe(true);
    expect(signIn.output).not.toMatch(/confirmed now/);
    expect(signIn.output).toMatch(/Allergy status remains unknown \(asked; not recorded\)\.\n {2}Fasting status remains unknown \(asked; not recorded\)\.\n {2}The team has acknowledged these unresolved items\./);
    expect(signIn.data.safetyData).toEqual({ allergy: "asked-unknown", fasting: "asked-unknown" });
    await t.session.close();
  });

  it("sent on an errand while holding traction, the assistant lets go first and says so; the operator sees the window close", async () => {
    const t = await toTheTriangle();
    expect((await tool(t, "delegate_task", { role: ASSISTANT, task: "hold_traction", params: { port: "B" } })).ok).toBe(true);
    const errand = await tool(t, "delegate_task", { role: ASSISTANT, task: "fetch_equipment", params: { capability: "ultrasound" } });
    expect(errand.output).toMatch(/Dr Mori \(assistant surgeon\) let go of the grasper in port B to fetch equipment to the bedside/);
    const release = stepEvents(errand.events).find((s) => s.op === "release" && s.actor === "or-7-assistant")!;
    expect(release.signals).toContain("exposure-lost");
    expect(triangle(t).exposure).not.toBe("good");
    // withdrawn before anyone takes it: there is nothing to hold, and the window had already fallen
    expect((await tool(t, "operate", { op: "withdraw", port: "B" })).ok).toBe(true);
    const late = await tool(t, "delegate_task", { role: ASSISTANT, task: "hold_traction", params: { port: "B" } });
    expect(late.ok).toBe(false);
    expect(late.output).toMatch(/nothing to hand over/);
    await t.session.close();
  });
});
