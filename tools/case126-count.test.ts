/**
 * Case 126 in OR 7: one count record (ClinicalCraft docs/TEAM.md §4.3) — the operative field, the count board, the RF
 * wand, the WHO Sign Out, the care team and the score agree on whether a swab is accounted for (the 2.3.0 audit,
 * repairs 1 and 3; docs/CASE_126.md "The count record").
 *
 *   - the acceptance cases: a clean 5/5; a recoverable 4/5 (the swab in the wound, found by the RF scan and the wound
 *     check); an unresolved 4/5 and an attempted completion (closure recorded as an unsafe progression that no later
 *     count erases, the Sign Out refused, the score capped and not clear) — and the same 4/5 handled properly
 *     (escalated, a clear scan excludes a retained swab); six of five; five of five made up with OR 6's swab; a
 *     documented transfer with the specimen (the positive control: no hold);
 *   - a count is never typed in;
 *   - a save before the operation activates the same team obligations as a run never interrupted;
 *   - the headless autopilot works the assigned scenario: the team runs alongside it, and closure waits for the count.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR, type NavGoal } from "@clinicalcraft/world";
import { assess, countStatus, evaluate, type CaseDefinition, type ClinicalAction } from "@clinicalcraft/core";
import type { AgentEvent, TeamEvent } from "./protocol.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const SCRUB = "staff:or-7.scrub-nurse";
const CIRCULATOR = "staff:or-7.circulating-nurse";
const COUNT = "eq:or-7.count-board";
const WAND = "eq:or-7.rf-wand";
const CHECKLIST = "eq:or-7.checklist";
const SWABS = [1, 2, 3, 4, 5].map((n) => `eq:or-7-swab-${n}`);
const SWAB5 = SWABS[4]!;
const SPARE = "eq:or-6-swab-1";

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
const SETTINGS = { embodiment: "embodied", approvalMode: "bypass" } as const;

async function theatre(team: string, extra: Partial<Parameters<typeof makeSession>[0]> = {}): Promise<TestSession> {
  const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS, ...extra });
  await t.session.run({ type: "clinical_action", action: { type: "start", team } as ClinicalAction });
  return t;
}

/** The reference solution as the record, from `from` up to (not including) the first action `stop` matches. */
function dispatchUntil(t: TestSession, stop: (a: ClinicalAction) => boolean, from = 1): number {
  const sol = t.session.caseDef.solution;
  let i = from;
  for (; i < sol.length && !stop(sol[i]!); i++) {
    const r = t.session.dispatch({ ...sol[i]!, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${sol[i]!.type}: ${r.rejected.message}`);
  }
  return i;
}
const isClose = (a: ClinicalAction) => a.type === "operate" && a.op.op === "close";

let seq = 0;
async function act(t: TestSession, actorId: string, operation: string, targetId?: string, goal?: NavGoal) {
  const events = await t.session.run({ type: "world_action", request: { actionId: `c-${++seq}`, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}) } });
  const r = msgsOf(events, "world_action_result").at(-1)?.result;
  if (!r) throw new Error(`no result for ${operation}`);
  return r;
}
/** A world act, walking where a refusal points first (a couple of times). */
async function done(t: TestSession, actorId: string, operation: string, targetId?: string) {
  let r = await act(t, actorId, operation, targetId);
  for (let i = 0; i < 2 && r.status === "failed" && r.hint && ["NOT_IN_RANGE", "NOT_VISIBLE", "PRECONDITION_FAILED"].includes(r.errorCode ?? ""); i++) {
    expect((await act(t, actorId, "navigate", undefined, r.hint.goal)).status).toBe("completed");
    r = await act(t, actorId, operation, targetId);
  }
  return r;
}
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
const state = (t: TestSession, id: string) => t.session.world()!.inspect(PRIMARY_ACTOR, id)?.state;
const status = (t: TestSession) => countStatus(t.session.state.count);
const teamOf = (events: readonly AgentEvent[]) => msgsOf(events, "team_event").map((m) => m.event);
const said = (events: TeamEvent[]) => events.flatMap((e) => (e.kind === "message" ? [e.message] : []));
const ledger = (t: TestSession) => t.session.snapshot().team!.state.count!;

/** The case up to the specimen out (the count falls due), the team paused, the surgeon at the table. */
async function toTheCount(scenario: string, surgeon: "learner" | "simulated"): Promise<TestSession> {
  const t = await theatre(scenario);
  dispatchUntil(t, isClose);
  expect(t.session.state.procedure?.specimen).toBe("extracted");
  await t.session.run({ type: "team", action: "pause" });
  await t.session.run({ type: "team", action: "surgeon", surgeon });
  expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
  return t;
}
const runTeam = async (t: TestSession, rounds = 100) => teamOf(await t.session.run({ type: "team", action: "run", rounds }));

/** The RF wand: the circulating nurse takes it, goes to the table and scans the patient, then puts it down. */
async function scan(t: TestSession) {
  expect((await done(t, CIRCULATOR, "pick_up", WAND)).status).toBe("completed");
  expect((await act(t, CIRCULATOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
  const r = await done(t, CIRCULATOR, "scan", WAND);
  expect(r.status, r.message).toBe("completed");
  expect((await act(t, CIRCULATOR, "put_down", WAND)).status).toBe("completed");
  return r;
}

/** After closure: the rest of the reference solution as the learner's record (refusals collected, not thrown). */
function finishRecord(t: TestSession, from: number): string[] {
  const sol = t.session.caseDef.solution;
  const refused: string[] = [];
  for (const a of sol.slice(from)) {
    const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    if (r.rejected) refused.push(`${a.type}:${r.rejected.code}`);
  }
  return refused;
}

describe("Case 126 in OR 7 · one count record: the field, the board, the wand, the Sign Out, the team and the score agree", () => {
  it("a count is never typed in: a learner's count action is refused whatever it claims", async () => {
    const t = await theatre("count-correct");
    const before = structuredClone(t.session.state.count);
    expect(before?.expected).toEqual(SWABS);
    const events = await t.session.run({ type: "clinical_action", action: { type: "count", count: { op: "count", ids: SWABS, staff: "or-7.scrub-nurse", stage: "final" }, by: "system" } as ClinicalAction });
    expect(msgsOf(events, "error")[0]).toMatchObject({ code: "permission_denied" });
    expect(t.session.state.count).toEqual(before);
    await t.session.close();
  });

  it("clean 5/5: the team counts correct, the board and the scan agree, closure is safe, the Sign Out valid, the verdict clear", async () => {
    const t = await toTheCount("count-correct", "simulated");
    await runTeam(t);
    expect(ledger(t)).toMatchObject({ outcome: "correct", holds: 0 });
    expect(status(t)).toBe("correct");
    await scan(t);
    expect(state(t, WAND)).toBe("clear");
    expect((await done(t, CIRCULATOR, "final_count", COUNT)).status).toBe("completed");
    expect(state(t, COUNT)).toBe("reconciled");
    const at = t.session.caseDef.solution.findIndex(isClose);
    expect(t.session.dispatch({ type: "operate", op: { op: "close" }, by: "system" }).rejected).toBeUndefined();
    expect(t.session.state.count!.unsafe).toEqual([]);
    expect(finishRecord(t, at + 1)).toEqual([]);
    expect(evaluate(t.session.caseDef, t.session.state, { intervened: "sign-out", valid: true })).toBe(true);
    const a = assess(t.session.caseDef, t.session.state);
    expect(a.count).toMatchObject({ status: "correct", expected: 5, missing: [], unexpected: [], unsafe: [] });
    expect(a.safety.verdict).toBe("clear");
    await t.session.close();
  });

  it("recoverable 4/5: the count names the missing swab, the RF wand finds it in the patient, the wound check recovers it, the recount reconciles", async () => {
    const t = await toTheCount("swab-in-wound", "learner");
    const first = said(await runTeam(t, 6));
    expect(first.find((m) => m.kind === "request" && m.about.hold)).toMatchObject({ about: { count: 4, of: 5, missing: [SWAB5], unexpected: [] } });
    expect(t.session.state.count!.entries.find((e) => e.op === "count")).toMatchObject({ staff: "or-7.scrub-nurse", stage: "closing", missing: [SWAB5] });
    expect(status(t)).toBe("discrepancy");
    expect(state(t, COUNT)).toBe("discrepancy");
    // the RF wand detects it inside the patient (the wand shows it; the record keeps who scanned)
    await scan(t);
    expect(state(t, WAND)).toBe("detected");
    expect(t.session.state.count!.entries.findLast((e) => e.op === "scan")).toMatchObject({ staff: "or-7.circulating-nurse", detected: [SWAB5] });
    // the surgeon searches the wound: recovered, with who took it out
    expect((await act(t, PRIMARY_ACTOR, "search", patientId(t))).status).toBe("completed");
    expect(t.session.state.count!.entries.findLast((e) => e.op === "recover")).toMatchObject({ ids: [SWAB5], staff: "surgeon", from: patientId(t) });
    // the recount on the board (a clean count) and a clear rescan close it
    expect((await done(t, CIRCULATOR, "resolve", COUNT)).status).toBe("completed");
    await scan(t);
    expect(status(t)).toBe("reconciled");
    expect(t.session.dispatch({ type: "operate", op: { op: "close" }, by: "system" }).rejected).toBeUndefined();
    expect(t.session.state.count!.unsafe).toEqual([]);
    expect(assess(t.session.caseDef, t.session.state).safety.verdict).toBe("clear");
    await t.session.close();
  });

  it("unresolved 4/5 and an attempted completion: closure is an unsafe progression no later count erases; the Sign Out is refused; the score is capped", async () => {
    const t = await toTheCount("swab-gone", "simulated");
    const messages = said(await runTeam(t));
    // the team reports four of five and escalates — credited in the record to the circulating nurse
    expect(messages.find((m) => m.kind === "escalate")).toMatchObject({ from: CIRCULATOR, about: { count: 4, of: 5, missing: [SWAB5] } });
    expect(ledger(t)).toMatchObject({ outcome: "unresolved" });
    expect(t.session.state.count!.entries.find((e) => e.op === "escalate")).toMatchObject({ staff: "or-7.circulating-nurse", to: "surgeon" });
    expect(status(t)).toBe("unresolved");
    expect(state(t, COUNT)).toBe("unresolved");
    // the learner closes anyway: allowed (teaching mode), recorded
    const closed = await t.session.run({ type: "clinical_action", action: { type: "operate", op: { op: "close" } } });
    expect(msgsOf(closed, "notification").some((n) => /unsafe progression/.test(n.body))).toBe(true);
    expect(t.session.state.count!.unsafe).toEqual([expect.objectContaining({ what: "closure", status: "unresolved", missing: [SWAB5] })]);
    expect(ledger(t).closedOnHold).toBe(true);
    // the board cannot sign out on it; the Sign Out itself is recorded invalid
    expect((await done(t, PRIMARY_ACTOR, "sign_out", CHECKLIST)).status).toBe("failed");
    t.session.dispatch({ type: "intervene", interventionId: "sign-out", by: "system" });
    expect(evaluate(t.session.caseDef, t.session.state, { intervened: "sign-out", valid: true })).toBe(false);
    expect(t.session.state.phase).toBe("operation");
    // a later count that finds five (the swab brought back from OR 6) does not erase what happened
    t.session.world()!.placeItem(SWAB5, "eq:or-7.mayo");
    expect((await done(t, CIRCULATOR, "resolve", COUNT)).status).toBe("completed");
    expect(status(t)).toBe("reconciled");
    expect(t.session.state.count!.unsafe).toHaveLength(1);
    const a = assess(t.session.caseDef, t.session.state);
    expect(a.safety.verdict).toBe("safety-critical");
    expect(a.safety.gates).toEqual(expect.arrayContaining([{ id: "closed-on-open-count", verdict: "safety-critical" }]));
    expect(a.score.percent).toBeLessThanOrEqual(50);
    expect(a.count!.escalations).toEqual([expect.objectContaining({ staff: "or-7.circulating-nurse" })]);
    await t.session.close();
  });

  it("the same 4/5 handled properly: escalated, a clear scan excludes a retained swab; closure is safe and the Sign Out valid", async () => {
    const t = await toTheCount("swab-gone", "simulated");
    await runTeam(t);
    expect(status(t)).toBe("unresolved");
    await scan(t);
    expect(state(t, WAND)).toBe("clear");
    expect(status(t)).toBe("excluded");
    expect(state(t, COUNT)).toBe("excluded");
    const at = t.session.caseDef.solution.findIndex(isClose);
    expect(t.session.dispatch({ type: "operate", op: { op: "close" }, by: "system" }).rejected).toBeUndefined();
    expect(t.session.state.count!.unsafe).toEqual([]);
    expect(finishRecord(t, at + 1)).toEqual([]);
    expect(evaluate(t.session.caseDef, t.session.state, { intervened: "sign-out", valid: true })).toBe(true);
    const a = assess(t.session.caseDef, t.session.state);
    expect(a.count).toMatchObject({ status: "excluded", missing: [SWAB5], unsafe: [] });
    expect(a.safety.verdict).toBe("clear");
    await t.session.close();
  });

  it("six of five is a discrepancy: the extra swab is set aside and documented, the recount reconciles", async () => {
    const t = await toTheCount("swab-extra", "simulated");
    const messages = said(await runTeam(t));
    expect(messages[0]).toMatchObject({ from: SCRUB, about: { count: 5, of: 5, unexpected: [SPARE] } });
    expect(messages[0]!.text.en).toBe("Count of swabs: 5 of 5, and 1 not in the count.");
    expect(messages.find((m) => m.kind === "request" && m.about.hold)?.text.en).toMatch(/^Count incorrect — 1 swabs not in the count/);
    expect(messages.find((m) => m.about.setAside)).toMatchObject({ from: CIRCULATOR, about: { setAside: [SPARE] } });
    expect(t.session.state.count!.entries.find((e) => e.op === "transfer")).toMatchObject({ ids: [SPARE], staff: "or-7.circulating-nurse" });
    expect(t.session.world()!.actor(CIRCULATOR)!.holding).toContain(SPARE);
    expect(ledger(t)).toMatchObject({ outcome: "reconciled", holds: 1 });
    expect(status(t)).toBe("reconciled");
    await t.session.close();
  });

  it("five of five made up with OR 6's swab is not correct: the missing swab and the stranger are both named; found, set aside, reconciled", async () => {
    const t = await toTheCount("swab-substituted", "simulated");
    const messages = said(await runTeam(t));
    expect(messages[0]).toMatchObject({ from: SCRUB, about: { count: 4, of: 5, missing: [SWAB5], unexpected: [SPARE] } });
    expect(messages.some((m) => m.kind === "report" && m.text.en.startsWith("Count of swabs correct"))).toBe(false);
    expect(t.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(SWAB5);
    expect(ledger(t)).toMatchObject({ outcome: "reconciled", holds: 1 });
    expect(status(t)).toBe("reconciled");
    await t.session.close();
  });

  it("a documented transfer with the specimen (the positive control): four of four is correct, no hold", async () => {
    const t = await toTheCount("swab-with-specimen", "simulated");
    const messages = said(await runTeam(t));
    expect(t.session.state.count!.entries.find((e) => e.op === "transfer")).toMatchObject({ ids: [SWAB5], staff: "or-7.circulating-nurse", reason: "sent with the specimen" });
    expect(messages[0]).toMatchObject({ about: { count: 4, of: 4, missing: [], unexpected: [] } });
    expect(messages.some((m) => m.about.hold)).toBe(false);
    expect(ledger(t)).toMatchObject({ outcome: "correct", holds: 0 });
    expect(status(t)).toBe("correct");
    expect(assess(t.session.caseDef, t.session.state).count).toMatchObject({ transferred: [SWAB5] });
    await t.session.close();
  });
});

describe("Case 126 in OR 7 · the assigned team scenario survives a reload and runs under the autopilot", () => {
  it("saved before the operation (the scenario pending), reloaded: the same obligations activate as in a run never interrupted", async () => {
    const run = async (t: TestSession) => {
      dispatchUntil(t, isClose);
      await t.session.run({ type: "team", action: "surgeon", surgeon: "simulated" });
      expect((await act(t, PRIMARY_ACTOR, "navigate", undefined, { kind: "interact", id: patientId(t) })).status).toBe("completed");
      return said(await runTeam(t, 80));
    };
    const control = await theatre("swab-in-wound");
    await control.session.run({ type: "team", action: "pause" });
    const controlSaid = await run(control);
    // the save: in the assessment phase, the team created but not set up
    const early = await theatre("swab-in-wound");
    await early.session.run({ type: "team", action: "pause" });
    expect(early.session.state.phase).toBe("assessment");
    const saved = JSON.parse(JSON.stringify(early.session.snapshot()));
    expect(saved.team.state).toMatchObject({ lifecycle: "pending", round: 0 });
    await early.session.close();
    const resumed = await makeSession({
      ...(await content()),
      settingsPatch: SETTINGS,
      resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue },
      embodied: { snapshot: saved.world, team: saved.team },
    });
    const resumedSaid = await run(resumed);
    expect(resumedSaid.map((m) => [m.from, m.kind, m.to])).toEqual(controlSaid.map((m) => [m.from, m.kind, m.to]));
    expect(ledger(resumed)).toMatchObject({ outcome: "reconciled", holds: 1 });
    expect(resumed.session.snapshot().team!.state).toMatchObject({ lifecycle: "completed", setup: expect.objectContaining({ worldVersion: expect.any(Number) }) });
    expect(resumed.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(SWAB5);
    // a reload after the set-up never sets it up twice
    const again = JSON.parse(JSON.stringify(resumed.session.snapshot()));
    await resumed.session.close();
    const third = await makeSession({
      ...(await content()),
      settingsPatch: SETTINGS,
      resume: { sessionId: again.sessionId, actions: again.actions, messages: again.messages, dialogue: again.dialogue },
      embodied: { snapshot: again.world, team: again.team },
    });
    await third.session.run({ type: "team", action: "run", rounds: 5 });
    expect(third.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(SWAB5);
    expect(third.session.snapshot().team!.state.messages.length).toBe(again.team.state.messages.length);
    await third.session.close();
    await control.session.close();
  });

  for (const scenario of ["swab-gone", "swab-in-wound"]) {
    it(`the headless autopilot works the "${scenario}" scenario: the team runs alongside, and closure waits for a settled count`, { timeout: 300_000 }, async () => {
      const t = await theatre(scenario);
      t.session.subscribe((e) => {
        if (e.msg.type === "approval_request") t.session.submit({ type: "approval_response", requestId: (e.msg as { requestId: string }).requestId, decision: "approved" });
      });
      await t.session.run({ type: "autopilot", maxTurns: 60 });
      const s = t.session.state;
      const team = t.session.snapshot().team!.state;
      // the scenario ran: rounds, the count due and acted on, the team's escalation or hold on the record
      expect(team.round).toBeGreaterThan(0);
      expect(team.lifecycle).not.toBe("pending");
      expect(team.count?.dueRound).toBeDefined();
      expect(team.count?.holds).toBeGreaterThanOrEqual(1);
      expect(s.count!.unsafe).toEqual([]);
      expect(["reconciled", "excluded"]).toContain(countStatus(s.count));
      if (scenario === "swab-in-wound") expect(s.count!.entries.some((e) => e.op === "recover" && e.ids.includes(SWAB5))).toBe(true);
      else expect(s.count!.entries.some((e) => e.op === "escalate")).toBe(true);
      expect(s.finished).toBe(true);
      expect(assess(t.session.caseDef, s).safety.verdict).toBe("clear");
      await t.session.close();
    });
  }
});
