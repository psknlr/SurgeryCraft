/**
 * Case 126 · the final acceptance scenario (the engineering recommendations, "final six-phase E2E"), headless in OR 7,
 * one session from the ward round to the conversion:
 *
 *   1. Pre-operative ECG: no historical ECG; a new one ordered; the circulating nurse fetches the device, the tracing
 *      is recorded at the patient, reported (simulated) and reviewed by the anaesthetist on the staff's own clock.
 *   2. Anaesthesia relief: asked to leave the anaesthetised patient, Dr Tanaka has Dr Wang take over in person with a
 *      structured hand-over; Dr Wang is then bound by the same rule.
 *   3. Live views and traction loss: Dr Mori holds the neck grasper; called away, the traction falls with their hands
 *      before the operator's next step; the operator re-grasps.
 *   4. Playback integrity: an operative cholangiogram is never ordered from the chart; tried at the table with the
 *      clip applier in the port it is refused ("cannot image") — and that refusal is a frame of its own; six rapid steps (two clip
 *      applications, a withdrawal, an insertion, two divisions) are each shown, in the record's order, by the one
 *      operative playback the scope dock and the surgery window share.
 *   5. Save and resume: the field, the studies, the anaesthesia responsibility, the step order and the persistent
 *      action ids agree with the run never interrupted.
 *   6. Conversion: a confirmed conversion to open surgery; pressure, instruments and traction go together, the
 *      field says the operation is open, and the views' open field shows what was done (no scope picture).
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import { observeField, procedureFor, type CaseDefinition, type ClinicalAction } from "@clinicalcraft/core";
import type { AgentEvent } from "./protocol.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";
import { OperativePlayback, type OperativeEvent, type PlaybackItem } from "../../web/src/ui/operative-playback.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const ASSISTANT = "staff:or-7-assistant";
const SETTINGS = { embodiment: "embodied", approvalMode: "bypass" } as const;

type Content = { caseDef: CaseDefinition; facility: NonNullable<Parameters<typeof makeSession>[0]>["facility"]; catalogs: NonNullable<Parameters<typeof makeSession>[0]>["catalogs"] };
async function content(): Promise<Content> {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)?.def;
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!caseDef || !facility) throw new Error(`content missing: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  return { caseDef, facility, catalogs: facility.catalogs.map((id) => pack.catalogs.get(id)!.def) };
}

let n = 0;
async function tool(t: TestSession, name: string, args: Record<string, unknown> = {}) {
  const events = await t.session.run({ type: "external_tool_call", callId: `f-${++n}`, tool: name, args, allowBypass: true });
  return { ...(msgsOf(events, "tool_call_end").at(-1) as { ok: boolean; output: string; data?: any; actionIds?: string[] }), events };
}
async function act(t: TestSession, actorId: string, operation: string, goal?: NavGoal) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `w-${++n}`, actorId, operation, ...(goal ? { goal } : {}) } });
  return msgsOf(events, "world_action_result").at(-1)!.result;
}
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
const toPatient = async (t: TestSession) => expect((await act(t, PRIMARY_ACTOR, "navigate", { kind: "interact", id: patientId(t) })).status).toBe("completed");

/** The reference record from `from` up to (not including) the first action `stop` matches. */
function recordUntil(t: TestSession, stop: (a: ClinicalAction) => boolean, from = 1): number {
  const sol = t.session.caseDef.solution;
  let i = from;
  for (; i < sol.length && !stop(sol[i]!); i++) {
    const r = t.session.dispatch({ ...sol[i]!, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${i} ${sol[i]!.type}: ${r.rejected.message}`);
  }
  return i;
}
const isInduction = (a: ClinicalAction) => a.type === "intervene" && a.interventionId === "induction";
const isFirstDissection = (a: ClinicalAction) => a.type === "operate" && a.op.op === "dissect";
const isFirstClip = (a: ClinicalAction) => a.type === "operate" && a.op.op === "clip";
/** The operative events of a run, in the order the session emitted them (what the web's store keeps). */
const operativeEvents = (events: readonly AgentEvent[]): OperativeEvent[] =>
  msgsOf(events, "clinical_event").flatMap((m) => (m.event.type === "procedure.step" || (m.event.type === "action.rejected" && m.event.action === "operate") ? [m.event as OperativeEvent] : []));
const steps = (t: TestSession) => t.session.snapshot().actions.flatMap((a) => (a.type === "operate" ? [a.op.op] : []));

describe("Case 126 · the final acceptance scenario", () => {
  it("pre-operative ECG → anaesthesia relief → traction loss → playback integrity → save and resume → conversion", { timeout: 300_000 }, async () => {
    const c = await content();
    const t = await makeSession({ ...c, settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });

    // ── 1. pre-operative ECG, on the staff's own clock ───────────────────────────────────────────────────────────
    const atInduction = recordUntil(t, isInduction);
    await toPatient(t);
    expect((await tool(t, "retrieve_report", { query: "ECG" })).data?.source).toBe("unavailable");
    expect((await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "pre-induction-ecg", indication: "84 years, dextrocardia" })).ok).toBe(true);
    for (let i = 0; i < 40 && !t.session.state.studies!.reviews.length; i++) {
      t.session.dispatch({ type: "advance-time", minutes: 0.5, by: "system" } as ClinicalAction);
      await t.session.run({ type: "staff_step" });
    }
    expect(t.session.state.studies!.reviews).toMatchObject([{ accession: "ecg-12lead-1", by: "or-7.anaesthetist" }]);
    expect((await tool(t, "read_study", { accession: "ecg-12lead-1" })).output).toMatch(/^Simulated investigation · 12-lead ECG/);

    // ── 2. anaesthesia relief, in person ─────────────────────────────────────────────────────────────────────────
    const atDissection = recordUntil(t, isFirstDissection, atInduction);
    const w = t.session.world()!;
    const relief = await t.session.run({ type: "user_message", text: "Dr Tanaka, please show me the way to theatre control.", to: "attending", staff: "or-7.anaesthetist" } as never);
    expect(msgsOf(relief, "agent_message").map((m) => m.text).join(" ")).toMatch(/I'll hand over first/);
    expect(t.session.state.anaesthesia).toMatchObject({ responsible: "l1-anaesthetist", handoverStatus: "transferred" });
    expect(t.session.state.anaesthesia!.handovers[0]).toMatchObject({ from: "or-7.anaesthetist", to: "l1-anaesthetist", accepted: true });
    expect(await act(t, "staff:l1-anaesthetist", "navigate", { kind: "room", id: "l1-control" })).toMatchObject({ status: "failed", errorCode: "NOT_AUTHORIZED" });
    expect(w.roomOf("staff:l1-anaesthetist")).toBe("or-7");
    await toPatient(t);

    // ── 3. live views and traction loss ──────────────────────────────────────────────────────────────────────────
    for (let i = 0; i < 3; i++) expect((await tool(t, "operate", { op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false })).ok).toBe(true);
    expect((await tool(t, "delegate_task", { role: ASSISTANT, task: "hold_traction", params: { port: "B" } })).output).toMatch(/Dr Mori \(assistant surgeon\) has the grasper in port B and keeps its traction/);
    const awayEvents = await t.session.run({ type: "world_action", request: { actionId: "mori-away", actorId: ASSISTANT, operation: "navigate", goal: { kind: "room", id: "l1-control" } } });
    const away = { events: awayEvents };
    expect(msgsOf(awayEvents, "world_action_result").at(-1)!.result.status).toBe("completed");
    // the traction went with their hands — recorded before any next step of the operator
    expect(steps(t).slice(-2)).toEqual(["release", "hand-over"]);
    const released = operativeEvents(away.events ?? []).find((e) => e.type === "procedure.step" && e.op === "release");
    expect(released).toMatchObject({ actor: "or-7-assistant", signals: ["exposure-lost"] });
    expect(t.session.state.procedure!.ports.find((p) => p.site === "B")!.holder).toBeUndefined();
    // the operator re-grasps and works the rest of the dissection up to the clips (the reference record)
    expect((await tool(t, "operate", { op: "retract", port: "B", structure: "gallbladder-infundibulum", direction: ["patient-left", "caudal"], force: "firm" })).ok).toBe(true);
    // (the three dissection steps done above are the reference record's first three)
    recordUntil(t, isFirstClip, atDissection + 3);

    // ── 4. playback integrity: an IOC never ordered; refused at the table; six rapid steps each shown ────────────
    const ioc = await tool(t, "order_study", { query: "intraoperative cholangiogram" });
    expect(ioc.data?.code).toBe("OPERATIVE_STUDY");
    const playback = new OperativePlayback({ now: () => 0, schedule: () => null, cancel: () => undefined });
    const def = procedureFor(t.session.caseDef, t.session.state)!;
    playback.attach(t.session.id, def);
    playback.sync([], t.session.state.procedure!);
    const run: OperativeEvent[] = [];
    const tried = await tool(t, "operate", { op: "image", modality: "ioc", port: "C" });
    expect(tried.ok).toBe(false);
    expect(tried.actionIds).toBeUndefined();
    run.push(...operativeEvents(tried.events));
    const rapid = [
      { op: "clip", port: "C", handle: "T2", count: 3 },
      { op: "clip", port: "C", handle: "T3", count: 2 },
      { op: "withdraw", port: "C" },
      { op: "insert", port: "C", instrument: "scissors" },
      { op: "divide", port: "C", handle: "T2" },
      { op: "divide", port: "C", handle: "T3" },
    ];
    const ids: string[] = [];
    for (const args of rapid) {
      const r = await tool(t, "operate", args);
      expect(r.ok, `${args.op}: ${r.output}`).toBe(true);
      ids.push(...(r.actionIds ?? []));
      run.push(...operativeEvents(r.events));
    }
    expect(ids).toHaveLength(6);
    // every frame the views draw (the first is drawn at once; the rest as each frame's time is up)
    const shown: PlaybackItem[] = [];
    playback.subscribe(() => {
      const item = playback.frame().item;
      if (item && item !== shown.at(-1)) shown.push(item);
    });
    playback.sync(run, t.session.state.procedure!);
    while (playback.next());
    expect(shown.map((x) => (x.kind === "rejected" ? `refused ${x.operation}` : x.operation))).toEqual(["refused image", "clip", "clip", "withdraw", "insert", "divide", "divide"]);
    expect(shown[0]!.rejectionReason).toMatch(/The clip-applier in port "C" cannot image/);
    expect(new Set(shown.slice(1).map((x) => x.id)).size).toBe(6);
    expect(playback.frame().state!.counters.steps).toBe(t.session.state.procedure!.counters.steps);
    const clipFeedback = (await tool(t, "get_action_feedback", { action_id: ids[0] })).output;
    expect(clipFeedback).toMatch(/operate clip/);

    // ── 5. save and resume ───────────────────────────────────────────────────────────────────────────────────────
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    const atSave = structuredClone(t.session.state);
    const order = steps(t);
    await t.session.close();
    const r = await makeSession({ ...c, settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world, team: saved.team } });
    expect(r.session.state.procedure).toEqual(atSave.procedure);
    expect(r.session.state.studies).toEqual(atSave.studies);
    expect(r.session.state.anaesthesia).toEqual(atSave.anaesthesia);
    expect(steps(r)).toEqual(order);
    expect((await tool(r, "get_action_feedback", { action_id: ids[0] })).output).toBe(clipFeedback);

    // ── 6. conversion to open surgery ────────────────────────────────────────────────────────────────────────────
    const convert = await tool(r, "operate", { op: "bailout", strategy: "convert-open" });
    expect(convert.ok, convert.output).toBe(true);
    const p = r.session.state.procedure!;
    expect(p.bailouts).toContain("convert-open");
    expect(p.insufflated).toBe(false);
    expect(p.ports.every((x) => !x.instrument)).toBe(true);
    expect((await tool(r, "observe_field")).output).toMatch(/open/i);
    // the views show the open field (no scope picture): the dissection done and the structures clipped and divided
    const open = observeField(procedureFor(r.session.caseDef, r.session.state)!, p, "open");
    expect(open.inView).toBe(false);
    expect(open.regions.find((x) => x.id === "hepatocystic-triangle")?.dissection).not.toBe("untouched");
    expect(open.tubes.filter((x) => x.divided)).toHaveLength(2);
    await r.session.close();
  });
  it("the learner keeps operating while the team works: an alarm and a hand-over with the surgery window open — who moves, who speaks, who signs the next report (the follow-up audit's acceptance test)", { timeout: 300_000 }, async () => {
    // Case 126 with hypotension once the abdomen is insufflated (a scenario variant: the rules are ClinicalCraft's)
    const c = await content();
    const caseDef = structuredClone(c.caseDef);
    const bleed = caseDef.physiology!.events!.find((e) => e.id === "ev-major-bleeding")!;
    caseDef.physiology!.events!.push({ ...structuredClone(bleed), id: "ev-test-hypotension", when: { procedure: { insufflated: true } }, setVitals: { sbp: 72, dbp: 40, hr: 112 } });
    const t = await makeSession({ ...c, caseDef, settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    let i = recordUntil(t, isFirstDissection);
    const w = t.session.world()!;
    const sol = t.session.caseDef.solution;
    const heard: AgentEvent[] = [];
    /** The learner walks to the table (what is said meanwhile is heard). */
    const toTable = async () => {
      const events = await t.session.run({ type: "world_action", request: { actionId: `w-${++n}`, actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "interact", id: patientId(t) } } });
      heard.push(...events);
      expect(msgsOf(events, "world_action_result").at(-1)!.result.status).toBe("completed");
    };
    await toTable();
    const said = () => msgsOf(heard, "agent_message").map((m) => `${m.speaker}: ${m.text}`);
    // the surgery window's picture: the one playback the web draws, fed with what the session emits
    const def = procedureFor(t.session.caseDef, t.session.state)!;
    const playback = new OperativePlayback({ now: () => 0, schedule: () => 0, cancel: () => undefined });
    playback.attach("acceptance", def);
    const drawn = () => {
      playback.sync(operativeEvents(heard), t.session.state.procedure!);
      while (playback.pending()) playback.next();
      return playback.frame().state!;
    };
    drawn();
    /** The learner's next operative step of the reference record, from the surgery window. */
    const operate = async () => {
      const a = sol[i++] as Extract<ClinicalAction, { type: "operate" }>;
      expect(a.type).toBe("operate");
      const r = await tool(t, "operate", a.op as unknown as Record<string, unknown>);
      heard.push(...r.events);
      expect(r.ok, `${a.op.op}: ${r.output}`).toBe(true);
      // the picture on screen is the session's own field after every step
      expect(drawn().counters.steps).toBe(t.session.state.procedure!.counters.steps);
    };
    const round0 = t.session.team()?.state.round ?? 0;

    // 1. the abdomen is up and the pressure falls as the learner takes the table: the responsible anaesthetist, already
    // at the patient, says so — the learner dissects on
    await operate();
    expect(t.session.state.alarms).toMatchObject([{ vital: "sbp", by: "or-7.anaesthetist", stage: "arrived" }]);
    expect(said()).toContainEqual(expect.stringMatching(/^Dr Tanaka \(anaesthesia\): Alarm: SBP 72 — I'm at the patient and checking it\.$/u));

    // 2. still operating, the learner asks Dr Tanaka to go: Dr Wang comes in and takes over first, then Dr Tanaka goes
    const asked = await t.session.run({ type: "user_message", text: "Dr Tanaka, please show me the way to theatre control.", to: "attending", staff: "or-7.anaesthetist" } as never);
    heard.push(...asked);
    expect(t.session.state.anaesthesia).toMatchObject({ responsible: "l1-anaesthetist", handoverStatus: "transferred" });
    expect(said()).toContainEqual(expect.stringMatching(/^Dr Wang \(duty consultant anaesthetist\): I've taken over the anaesthetic from Dr Tanaka \(anaesthesia\)\./u));
    expect([w.roomOf("staff:l1-anaesthetist"), w.roomOf("staff:or-7.anaesthetist")]).toEqual(["or-7", "l1-control"]);
    await toTable();
    await operate();

    // 3. a new ECG: the circulating nurse records it with her own body; Dr Wang — responsible now — signs the report
    const ordered = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "intra-op" });
    heard.push(...ordered.events);
    expect(ordered.ok, ordered.output).toBe(true);
    const waited = await tool(t, "wait", { minutes: 10 });
    heard.push(...waited.events);
    const studies = t.session.state.studies!;
    expect(studies.accessions[0]).toMatchObject({ collector: "or-7.circulating-nurse" });
    expect(studies.reviews).toEqual([expect.objectContaining({ by: "l1-anaesthetist", basis: "responsible" })]);
    expect(said()).toContainEqual(expect.stringMatching(/^Dr Wang \(duty consultant anaesthetist\): I've reviewed the simulated 12-lead ECG/u));
    // Dr Tanaka, gone to theatre control, only showed the learner the way: no alarm, no review, nothing of the patient's
    const afterHandover = said().slice(said().findIndex((x) => x.startsWith("Dr Wang (duty consultant anaesthetist): I've taken over")) + 1);
    expect(afterHandover.filter((x) => x.startsWith("Dr Tanaka"))).toEqual(["Dr Tanaka (anaesthesia): Follow me — I'll take you to Theatre control desk."]);
    await operate();

    // the team went on working with the operation (its rounds ran after the learner's steps), and the picture is the field's
    expect(t.session.team()?.state.round ?? 0).toBeGreaterThan(round0);
    expect(observeField(def, drawn()).inView).toBe(true);
    await t.session.close();
  });
});
