/**
 * Case 126 in OR 7, embodied: the care team works on its own (ClinicalCraft docs/TEAM.md).
 *
 *   1. the two-nurse handoff — with no instruction from the learner, the circulating nurse notices the surgeon needs a
 *      needle holder, asks the scrub nurse (request → read-back → confirmation), the scrub nurse finds it, picks it up,
 *      reaches the surgeon and hands it over, and the circulating nurse sees the surgeon holding it before she calls
 *      it done; every act is the named nurse's own, on behalf of the colleague who asked;
 *   2. the scrub nurse on a break: the circulating nurse calls the relief colleague from OR 6, who walks in and
 *      hands it over;
 *   3. the needle holder left on the Mayo stand: found where it is, not where it is usually kept;
 *   4. no needle holder in the room: the scrub nurse says so, and the circulating nurse tells the surgeon why;
 *   5. the surgeon away from the table: the scrub nurse waits, then says so; the circulating nurse escalates;
 *   6. two requests for the one needle holder: one owner, the other request ends with a reason;
 *   7. saved mid-handoff and restored: the hand-over happens exactly once;
 *   8. the closing count, swab by swab, once the specimen is out: correct first time and no hold (the control); a swab
 *      under the Mayo stand found by the circulating nurse's search; a swab in the wound found only by the surgeon's
 *      check (the learner as the surgeon reads the hold back); a swab gone from the room — still short after the
 *      search and the recount, escalated for an X-ray; closing while the count is short is recorded.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR } from "@clinicalcraft/world";
import type { CaseDefinition, ClinicalAction } from "@clinicalcraft/core";
import type { AgentEvent, TeamEvent } from "./protocol.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const SCRUB = "staff:or-7.scrub-nurse";
const CIRCULATOR = "staff:or-7.circulating-nurse";
const RELIEF = "staff:or-6.scrub-nurse";
const NEEDLE_HOLDER = "eq:or-7.needle-holder";

type Content = { caseDef: CaseDefinition; facility: NonNullable<Parameters<typeof makeSession>[0]>["facility"]; catalogs: NonNullable<Parameters<typeof makeSession>[0]>["catalogs"] };

async function content(): Promise<Content> {
  const pack = await loadContent({ dirs: [`${ROOT}/content`] });
  const caseDef = pack.cases.get(CASE)?.def;
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!caseDef || !facility) throw new Error(`content missing: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  return { caseDef, facility, catalogs: facility.catalogs.map((id) => pack.catalogs.get(id)!.def) };
}

async function theatre(team: string, c?: Content, extra: Partial<Parameters<typeof makeSession>[0]> = {}): Promise<TestSession> {
  const { caseDef, facility, catalogs } = c ?? (await content());
  const t = await makeSession({ caseDef, facility, catalogs, settingsPatch: { embodiment: "embodied", approvalMode: "bypass" }, ...extra });
  await t.session.run({ type: "clinical_action", action: { type: "start", team } as ClinicalAction });
  return t;
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

let seq = 0;
/** The learner's own world action (the team acts after it: autonomy `auto`). */
async function learner(t: TestSession, operation: string, goal: Record<string, unknown>): Promise<AgentEvent[]> {
  const actionId = `l-${++seq}`;
  const events = await t.session.run({ type: "world_action", request: { actionId, actorId: PRIMARY_ACTOR, operation, goal } as never });
  const r = msgsOf(events, "world_action_result").find((x) => x.result.actionId === actionId)?.result;
  expect(r?.status, r?.message).toBe("completed");
  return events;
}

const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
const team = (events: readonly AgentEvent[]) => msgsOf(events, "team_event").map((m) => m.event);
const said = (events: TeamEvent[]) => events.flatMap((e) => (e.kind === "message" ? [e.message] : []));
const receipts = (events: TeamEvent[]) => events.flatMap((e) => (e.kind === "receipt" ? [e.receipt] : []));
/** The last state of each task. */
const tasks = (events: TeamEvent[]) => [...new Map(events.flatMap((e) => (e.kind === "task" ? [[e.task.id, e.task] as const] : []))).values()];

describe("Case 126 in OR 7 · the care team works on its own", () => {
  it("two named nurses hand the surgeon a needle holder while the learner watches", async () => {
    const t = await theatre("needle-holder");
    toTheTable(t);
    const w = t.session.world()!;
    // the learner only walks to the table; everything after is the team's
    const events = team(await learner(t, "navigate", { kind: "interact", id: patientId(t) }));
    const messages = said(events);
    expect(messages.map((m) => [m.from, m.kind, m.to])).toEqual([
      [CIRCULATOR, "notice", PRIMARY_ACTOR],
      [CIRCULATOR, "request", SCRUB],
      [SCRUB, "readback", CIRCULATOR],
      [CIRCULATOR, "confirm", SCRUB],
      [SCRUB, "report", CIRCULATOR],
      [CIRCULATOR, "report", PRIMARY_ACTOR],
    ]);
    expect(messages[1]!.text.en).toBe("Nurse Lim (scrub), please pass a needle holder to the surgeon.");
    expect(messages[1]!.text["zh-CN"]).toBe("林护士（洗手），请把持针器递给术者。");
    // check-back: the request was read back and the read-back verified
    const request = messages[1]!;
    expect(messages[2]!.replyTo).toBe(request.id);
    expect(messages[3]!.replyTo).toBe(messages[2]!.id);
    // the delivery is the scrub nurse's own body, on behalf of the circulating nurse who asked; the circulating nurse
    // only moves to keep the surgeon in sight
    const all = receipts(events);
    const acts = all.filter((r) => r.actor === SCRUB);
    expect(acts.length).toBeGreaterThanOrEqual(3);
    expect(new Set(all.map((r) => r.initiator))).toEqual(new Set([CIRCULATOR]));
    expect(all.filter((r) => r.actor !== SCRUB).every((r) => r.actor === CIRCULATOR && r.operation === "navigate")).toBe(true);
    expect(acts.map((r) => r.operation)).toContain("pick_up");
    const handOver = acts.filter((r) => r.operation === "hand_over");
    expect(handOver).toHaveLength(1);
    expect(handOver[0]).toMatchObject({ outcome: "completed", target: NEEDLE_HOLDER, recipient: PRIMARY_ACTOR });
    // the world: the surgeon holds it; the circulating nurse verified it with her own eyes
    expect(w.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    expect(w.actor(SCRUB)!.holding).not.toContain(NEEDLE_HOLDER);
    const supply = tasks(events).find((x) => x.kind === "supply")!;
    expect(supply).toMatchObject({ status: "done", verified: true, itemId: NEEDLE_HOLDER, owner: CIRCULATOR, assignee: SCRUB });
    // the lines are heard as the nurses' own
    const lines = msgsOf(t.events, "agent_message").filter((m) => m.agent === "nurse").map((m) => `${m.speaker}: ${m.text}`);
    expect(lines).toContain("Nurse Aisyah (circulating): Nurse Lim (scrub), please pass a needle holder to the surgeon.");
    await t.session.close();
  });

  it("the scrub nurse on a break: the relief colleague from OR 6 is called and brings it", async () => {
    const t = await theatre("scrub-on-break");
    toTheTable(t);
    const w = t.session.world()!;
    const events = team(await learner(t, "navigate", { kind: "interact", id: patientId(t) }));
    // run on until the team has settled (the relief colleague walks over)
    events.push(...team(await t.session.run({ type: "team", action: "run" })));
    const messages = said(events);
    expect(messages.some((m) => m.to === SCRUB)).toBe(false);
    expect(messages.find((m) => m.kind === "request")).toMatchObject({ from: CIRCULATOR, to: RELIEF, delivered: true });
    expect(receipts(events).filter((r) => r.operation === "hand_over" && r.outcome === "completed").map((r) => r.actor)).toEqual([RELIEF]);
    expect(w.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    expect(tasks(events).find((x) => x.kind === "supply")).toMatchObject({ status: "done", verified: true });
    await t.session.close();
  });

  it("the needle holder left on the Mayo stand is found where it is", async () => {
    const t = await theatre("needle-holder-moved");
    toTheTable(t);
    const w = t.session.world()!;
    const events = team(await learner(t, "navigate", { kind: "interact", id: patientId(t) }));
    events.push(...team(await t.session.run({ type: "team", action: "run" })));
    expect(w.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    expect(receipts(events).find((r) => r.operation === "hand_over")).toMatchObject({ actor: SCRUB, outcome: "completed" });
    await t.session.close();
  });

  it("no needle holder in the room: the scrub nurse says so; the surgeon is told why", async () => {
    const t = await theatre("needle-holder-missing");
    toTheTable(t);
    const w = t.session.world()!;
    const events = team(await learner(t, "navigate", { kind: "interact", id: patientId(t) }));
    events.push(...team(await t.session.run({ type: "team", action: "run" })));
    const messages = said(events);
    expect(messages.find((m) => m.kind === "decline")).toMatchObject({ from: SCRUB, to: CIRCULATOR, about: { reason: "not-found" } });
    const escalation = messages.find((m) => m.kind === "escalate")!;
    expect(escalation).toMatchObject({ from: CIRCULATOR, to: PRIMARY_ACTOR });
    expect(escalation.text.en).toBe("The needle holder for the surgeon hasn't arrived — Nurse Lim (scrub) can't find one in the room.");
    expect(tasks(events).find((x) => x.kind === "supply")).toMatchObject({ status: "escalated", reason: "not-found" });
    // nothing was carried out of thin air: the needle holder is still in OR 6
    expect(w.actor(PRIMARY_ACTOR)!.holding).not.toContain(NEEDLE_HOLDER);
    expect(receipts(events).filter((r) => r.outcome === "completed")).toEqual([]);
    await t.session.close();
  });

  it("the surgeon away from the table: the scrub nurse waits, says so, and the surgeon is told", async () => {
    const t = await theatre("needle-holder");
    toTheTable(t);
    const w = t.session.world()!;
    expect(w.actor(PRIMARY_ACTOR)!.room).not.toBe("or-7");
    const events = team(await t.session.run({ type: "team", action: "run", rounds: 60 }));
    const messages = said(events);
    expect(receipts(events).some((r) => r.operation === "pick_up" && r.outcome === "completed")).toBe(true);
    expect(messages.find((m) => m.kind === "decline")).toMatchObject({ from: SCRUB, about: { reason: "recipient-absent" } });
    const escalation = messages.find((m) => m.kind === "escalate")!;
    expect(escalation).toMatchObject({ from: CIRCULATOR, to: PRIMARY_ACTOR, delivered: true });
    expect(escalation.text.en).toContain("the surgeon isn't at the table");
    expect(receipts(events).some((r) => r.operation === "hand_over")).toBe(false);
    await t.session.close();
  });

  it("two requests for the one needle holder: one owner; the other ends with a reason", async () => {
    // the scrub nurse is there and a relief colleague can be called: both look for the one needle holder
    const c = await content();
    const base = c.caseDef.team!;
    const scenario = base.scenarios.find((s) => s.id === "scrub-on-break")!;
    const caseDef = { ...c.caseDef, team: { ...base, scenarios: [...base.scenarios, { ...scenario, id: "two-requests", absent: [] }] } };
    const t = await theatre("two-requests", { ...c, caseDef });
    toTheTable(t);
    const w = t.session.world()!;
    await t.session.run({ type: "team", action: "pause" });
    await learner(t, "navigate", { kind: "interact", id: patientId(t) });
    // the surgeon asks for a second one before the team has moved
    const events = team(await t.session.run({ type: "team", action: "need", item: "sc-needle-holder" }));
    events.push(...team(await t.session.run({ type: "team", action: "run", rounds: 80 })));
    const all = tasks(events);
    const supplies = all.filter((x) => x.kind === "supply");
    expect(supplies).toHaveLength(2);
    expect(supplies.filter((x) => x.status === "done")).toHaveLength(1);
    expect(supplies.filter((x) => x.status === "escalated")).toHaveLength(1);
    // never two tasks on the one item; exactly one hand-over; the surgeon holds it
    const delivering = all.filter((x) => x.kind === "deliver" && x.itemId === NEEDLE_HOLDER && x.status === "done");
    expect(delivering).toHaveLength(1);
    expect(receipts(events).filter((r) => r.operation === "hand_over" && r.outcome === "completed")).toHaveLength(1);
    expect(w.actor(PRIMARY_ACTOR)!.holding.filter((h) => h === NEEDLE_HOLDER)).toHaveLength(1);
    await t.session.close();
  });

  it("saved mid-handoff and restored: the needle holder is handed over exactly once", async () => {
    const c = await content();
    const t = await theatre("needle-holder", c);
    toTheTable(t);
    // step the team by hand until the scrub nurse holds the needle holder
    await t.session.run({ type: "team", action: "pause" });
    await learner(t, "navigate", { kind: "interact", id: patientId(t) });
    const w = t.session.world()!;
    for (let i = 0; i < 30 && !w.actor(SCRUB)!.holding.includes(NEEDLE_HOLDER); i++) await t.session.run({ type: "team", action: "step" });
    expect(w.actor(SCRUB)!.holding).toContain(NEEDLE_HOLDER);
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    expect(saved.team?.format).toBe("clinicalcraft-team@1");
    const before = receipts(team(t.events));
    expect(before.some((r) => r.operation === "hand_over")).toBe(false);
    await t.session.close();
    // a new session from the save: the record replayed, the world and the team restored
    const r = await makeSession({
      caseDef: c.caseDef,
      facility: c.facility,
      catalogs: c.catalogs,
      settingsPatch: { embodiment: "embodied", approvalMode: "bypass" },
      resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue },
      embodied: { snapshot: saved.world, team: saved.team },
    });
    expect(r.session.state.phase).toBe("operation");
    const rw = r.session.world()!;
    expect(rw.actor(SCRUB)!.holding).toContain(NEEDLE_HOLDER);
    const after = team(await r.session.run({ type: "team", action: "run" }));
    // the second run asks no one again and repeats no completed act; the hand-over happens once
    expect(said(after).filter((m) => m.kind === "request")).toEqual([]);
    expect(receipts(after).filter((x) => x.operation === "pick_up")).toEqual([]);
    expect(receipts(after).filter((x) => x.operation === "hand_over" && x.outcome === "completed")).toHaveLength(1);
    expect(rw.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    expect(tasks(after).find((x) => x.kind === "supply")).toMatchObject({ status: "done", verified: true });
    // and again: nothing more happens
    const again = team(await r.session.run({ type: "team", action: "run" }));
    expect(receipts(again)).toEqual([]);
    await r.session.close();
  });

  describe("the closing count, swab by swab", () => {
    const SWAB5 = "eq:or-7-swab-5";
    /** The case up to the specimen out (the count falls due), the surgeon at the table. */
    async function toTheCount(scenario: string, surgeon: "learner" | "simulated"): Promise<TestSession> {
      const t = await theatre(scenario);
      const c = t.session.caseDef;
      for (const a of c.solution.slice(1, c.solution.findIndex((x) => x.type === "operate" && (x as { op?: { op?: string } }).op?.op === "close"))) {
        const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
        if (r.rejected) throw new Error(`${a.type}: ${r.rejected.message}`);
      }
      expect(t.session.state.procedure?.specimen).toBe("extracted");
      await t.session.run({ type: "team", action: "pause" });
      await t.session.run({ type: "team", action: "surgeon", surgeon });
      await learner(t, "navigate", { kind: "interact", id: patientId(t) });
      return t;
    }
    const ledger = (t: TestSession) => t.session.snapshot().team!.state.count!;
    const run = async (t: TestSession, rounds = 80) => team(await t.session.run({ type: "team", action: "run", rounds }));

    it("every swab there (the control): counted correct the first time, no hold", async () => {
      const t = await toTheCount("count-correct", "simulated");
      const events = await run(t);
      const messages = said(events);
      expect(messages.map((m) => [m.from, m.kind, m.to])).toEqual([
        [SCRUB, "report", CIRCULATOR],
        [CIRCULATOR, "report", PRIMARY_ACTOR],
      ]);
      expect(messages[0]!.text.en).toBe("Count of swabs: 5 of 5.");
      expect(messages[1]!.text["zh-CN"]).toBe("纱布清点无误：5/5。");
      expect(ledger(t)).toMatchObject({ baseline: 5, outcome: "correct", holds: 0 });
      await t.session.close();
    });

    it("a swab under the Mayo stand: hold (read back), the room searched, found, recount correct", async () => {
      const t = await toTheCount("swab-on-floor", "simulated");
      const w = t.session.world()!;
      expect(w.canSee(SCRUB, SWAB5)).toBe(false);
      const events = await run(t);
      const messages = said(events);
      const hold = messages.find((m) => m.kind === "request" && m.about.hold)!;
      expect(hold).toMatchObject({ from: CIRCULATOR, to: PRIMARY_ACTOR, about: { count: 4, of: 5 } });
      expect(hold.text.en).toBe("Count incorrect — 4 of 5 swabs. Please hold closure and check the wound.");
      // check-back on the hold: the (simulated) surgeon reads it back; the circulating nurse confirms
      expect(messages.find((m) => m.kind === "readback" && m.replyTo === hold.id)).toMatchObject({ from: PRIMARY_ACTOR, to: CIRCULATOR });
      expect(messages.some((m) => m.kind === "confirm" && m.from === CIRCULATOR && m.thread === hold.thread)).toBe(true);
      // the circulating nurse searched with her own hands, and found it
      const searches = receipts(events).filter((r) => r.operation === "search" && r.actor === CIRCULATOR);
      expect(searches.length).toBeGreaterThanOrEqual(1);
      expect(w.canSee(CIRCULATOR, SWAB5) || w.find(SCRUB, { type: "sc-gauze-swab" }).some((e) => e.id === SWAB5)).toBe(true);
      expect(messages.find((m) => m.kind === "request" && m.about.recount)).toMatchObject({ from: CIRCULATOR, to: SCRUB });
      expect(messages.at(-1)).toMatchObject({ from: CIRCULATOR, to: PRIMARY_ACTOR, kind: "report", about: { count: 5, of: 5 } });
      expect(ledger(t)).toMatchObject({ outcome: "reconciled", holds: 1 });
      expect(ledger(t).detectedRound! - ledger(t).dueRound!).toBeLessThanOrEqual(3);
      expect(ledger(t).closedOnHold).toBeUndefined();
      await t.session.close();
    });

    it("a swab in the wound: not in the room; the learner, as the surgeon, reads the hold back and finds it", async () => {
      const t = await toTheCount("swab-in-wound", "learner");
      const w = t.session.world()!;
      const first = await run(t, 6);
      const hold = said(first).find((m) => m.kind === "request" && m.about.hold)!;
      expect(hold).toMatchObject({ to: PRIMARY_ACTOR, about: { count: 4, of: 5 } });
      // the learner reads the hold back (check-back), then searches the wound with their own hands
      await t.session.run({ type: "team", action: "reply", message: hold.id, kind: "readback" });
      const search = msgsOf(await t.session.run({ type: "world_action", request: { actionId: "wound-1", actorId: PRIMARY_ACTOR, operation: "search", targetId: patientId(t) } }), "world_action_result")[0]!.result;
      expect(search.status, search.message).toBe("completed");
      expect(search.events.some((e) => e.type === "entity.concealed" && e.entityId === SWAB5)).toBe(true);
      // searched out of the wound: in the surgeon's hand (where the scrub nurse can count it)
      expect(w.actor(PRIMARY_ACTOR)!.holding).toContain(SWAB5);
      await t.session.run({ type: "team", action: "reply", message: hold.id, kind: "report", text: "Wound checked: one swab out." });
      const rest = await run(t);
      const all = [...first, ...rest];
      // the circulating nurse's searches of the room found nothing (it was never there)
      expect(receipts(all).filter((r) => r.operation === "search" && r.actor === CIRCULATOR).every((r) => r.message.includes("nothing"))).toBe(true);
      expect(said(all).some((m) => m.kind === "confirm" && m.thread === hold.thread)).toBe(true);
      expect(said(all).at(-1)).toMatchObject({ kind: "report", about: { count: 5, of: 5 }, to: PRIMARY_ACTOR });
      expect(ledger(t)).toMatchObject({ outcome: "reconciled", holds: 1 });
      expect(w.canSee(PRIMARY_ACTOR, SWAB5)).toBe(true);
      await t.session.close();
    });

    it("a swab in the wound, observer mode: the simulated surgeon checks the wound and takes it out", async () => {
      const t = await toTheCount("swab-in-wound", "simulated");
      const events = await run(t);
      expect(receipts(events).filter((r) => r.actor === PRIMARY_ACTOR).map((r) => [r.operation, r.outcome])).toEqual([["search", "completed"]]);
      expect(t.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(SWAB5);
      expect(ledger(t)).toMatchObject({ outcome: "reconciled", holds: 1 });
      await t.session.close();
    });

    it("a swab gone from the room: still short after the search and the recount — escalated for an X-ray", async () => {
      const t = await toTheCount("swab-gone", "simulated");
      const messages = said(await run(t));
      const escalation = messages.find((m) => m.kind === "escalate")!;
      expect(escalation).toMatchObject({ from: CIRCULATOR, to: PRIMARY_ACTOR, about: { count: 4, of: 5 } });
      expect(escalation.text.en).toBe("Still 4 of 5 swabs after searching the room — an X-ray before the patient leaves.");
      expect(ledger(t)).toMatchObject({ outcome: "unresolved", holds: 1 });
      await t.session.close();
    });

    it("closing while the count is short is recorded (inappropriate progression)", async () => {
      const t = await toTheCount("swab-in-wound", "learner");
      await run(t, 6);
      expect(ledger(t).detectedRound).toBeDefined();
      // the surgeon closes anyway
      expect(t.session.dispatch({ type: "operate", op: { op: "close" }, by: "system" } as ClinicalAction).rejected).toBeUndefined();
      await run(t, 2);
      expect(ledger(t).closedOnHold).toBe(true);
      await t.session.close();
    });
  });
});
