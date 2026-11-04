/**
 * Case 126's characters (ClinicalCraft docs/CHARACTERS.md), embodied in OR 7, with a scripted model standing in for
 * every character's LLM:
 *
 *   1. Every member of staff holds a position of their own — the OR 7 team, the duty anaesthetist, the theatre
 *      coordinator, recovery, the porter, the pharmacist — and each speaks from that position's role card: Nurse Lim
 *      as the scrub nurse (the sterile field), Dr Tanaka as the anaesthetist (never the learner's preceptor), Dr Mori
 *      as the assistant surgeon (traction, never dissection).
 *   2. `characters.engine: "llm"`: the two nurses hand the surgeon a needle holder with every move decided by their
 *      own model — the same closed loop (notice, request, read-back, confirmation, report) and the same world acts as
 *      the rules, in the models' own words; a line that states what nobody perceived is refused and the team's words
 *      are said instead.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR } from "@clinicalcraft/world";
import type { CaseDefinition, ClinicalAction } from "@clinicalcraft/core";
import type { AgentEvent, TeamEvent } from "./protocol.js";
import type { ChatRequest } from "./providers/types.js";
import { textScript } from "./providers/scripted.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const SCRUB = "staff:or-7.scrub-nurse";
const CIRCULATOR = "staff:or-7.circulating-nurse";
const NEEDLE_HOLDER = "eq:or-7.needle-holder";

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

const userText = (r: ChatRequest) => r.messages.flatMap((m) => m.content.flatMap((p) => (p.type === "text" ? [p.text] : []))).join("\n");
const systemText = (r: ChatRequest) => r.system.map((s) => s.text).join("\n");
/**
 * The scripted stand-in for every character's model: a team member takes the protocol's move in its own words
 * ("Right — <the team's words>"), or `bad` words when given; anyone else answers briefly.
 */
function model(bad?: (usual: string) => string) {
  return (r: ChatRequest) => {
    if (r.responseFormat?.name === "team_decision") {
      const offered = (r.responseFormat.schema.properties as Record<string, { enum: string[] }>).option.enum;
      const usual = /the team's usual words: "([^"]+)"/u.exec(userText(r))?.[1] ?? "";
      const line = usual ? (bad ? bad(usual) : `Right — ${usual}`) : "";
      return textScript(JSON.stringify({ option: offered.includes("act") ? "act" : offered[0], line, why: "the protocol's next step" }));
    }
    return textScript("Understood.");
  };
}
const scripts = (fn: (r: ChatRequest) => ReturnType<typeof textScript>) => Array.from({ length: 300 }, () => fn);

async function theatre(scenario: string, extra: Partial<Parameters<typeof makeSession>[0]> & { engine?: "rules" | "llm" } = {}): Promise<TestSession> {
  const { engine = "rules", ...rest } = extra;
  const t = await makeSession({ ...(await content()), settingsPatch: { embodiment: "embodied", approvalMode: "bypass", characters: { engine, timeoutMs: 5000 } } as never, ...rest });
  await t.session.run({ type: "clinical_action", action: { type: "start", team: scenario } as ClinicalAction });
  return t;
}
function toTheTable(t: TestSession): void {
  const c = t.session.caseDef;
  for (const a of c.solution.slice(1, c.solution.findIndex((x) => x.type === "operate"))) {
    const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${a.type}: ${r.rejected.message}`);
  }
}
const patientId = (t: TestSession) => t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
async function walkToTable(t: TestSession): Promise<AgentEvent[]> {
  return t.session.run({ type: "world_action", request: { actionId: "to-table", actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "interact", id: patientId(t) } } });
}
const said = (events: readonly AgentEvent[]) => msgsOf(events, "team_event").flatMap((m) => ((m.event as TeamEvent).kind === "message" ? [(m.event as Extract<TeamEvent, { kind: "message" }>).message] : []));
const receipts = (events: readonly AgentEvent[]) => msgsOf(events, "team_event").flatMap((m) => ((m.event as TeamEvent).kind === "receipt" ? [(m.event as Extract<TeamEvent, { kind: "receipt" }>).receipt] : []));

describe("Case 126 · every character has a role of its own", () => {
  it("each member of staff holds a position, and speaks from that position's role card", async () => {
    const t = await theatre("needle-holder", { scripts: scripts(model()) });
    const positions = Object.fromEntries(t.session.staffStates().map((s) => [s.actorId, s.position]));
    expect(positions).toMatchObject({
      "staff:or-7.circulating-nurse": "circulating-nurse",
      "staff:or-7.scrub-nurse": "scrub-nurse",
      "staff:or-7.anaesthetist": "anaesthetist",
      "staff:or-7-assistant": "assistant-surgeon",
      "staff:l1-anaesthetist": "anaesthetist",
      "staff:l1-coordinator": "theatre-coordinator",
      "staff:pacu.nurse": "recovery-nurse",
      "staff:l1-porter": "porter",
      "staff:l1-pharmacist": "pharmacist",
      "staff:l0-bb-scientist": "transfusion-scientist",
      "staff:l0-skills.attending": "educator",
    });
    // nobody on the floor is left without a job
    expect(t.session.staffStates().filter((s) => !s.position)).toEqual([]);
    const ask = async (to: string, staff: string, text: string) => {
      const before = t.provider!.requests.length;
      await t.session.run({ type: "user_message", text, to, staff } as never);
      return t.provider!.requests.slice(before).map(systemText).find((s) => s.includes("<role>"))!;
    };
    const lim = await ask("nurse", "or-7.scrub-nurse", "Nurse Lim, is the tray ready?");
    expect(lim).toMatch(/You are Nurse Lim \(scrub\), the scrub nurse\. Keeps the sterile field and its instruments/u);
    expect(lim).toMatch(/- leave the sterile field unrelieved/u);
    const tanaka = await ask("attending", "or-7.anaesthetist", "Dr Tanaka, how is the patient doing?");
    expect(tanaka).toMatch(/You are Dr Tanaka \(anaesthesia\), the anaesthetist\./u);
    expect(tanaka).toMatch(/not the learner's preceptor/u);
    const mori = await ask("attending", "or-7-assistant", "Dr Mori, are you ready to assist?");
    expect(mori).toMatch(/You are Dr Mori \(assistant surgeon\), the assistant surgeon\./u);
    expect(mori).toMatch(/- dissect, clip, divide or coagulate on your own initiative/u);
    await t.session.close();
  });

  it("characters.engine llm: the nurses hand the surgeon a needle holder, every move theirs — the same closed loop and acts, in their own words", async () => {
    const t = await theatre("needle-holder", { engine: "llm", scripts: scripts(model()) });
    toTheTable(t);
    const events = await walkToTable(t);
    const messages = said(events);
    expect(messages.map((m) => [m.from, m.kind, m.to])).toEqual([
      [CIRCULATOR, "notice", PRIMARY_ACTOR],
      [CIRCULATOR, "request", SCRUB],
      [SCRUB, "readback", CIRCULATOR],
      [CIRCULATOR, "confirm", SCRUB],
      [SCRUB, "report", CIRCULATOR],
      [CIRCULATOR, "report", PRIMARY_ACTOR],
    ]);
    // in the members' own words (the other language keeps the team's wording)
    expect(messages[1]!.text.en).toBe("Right — Nurse Lim (scrub), please pass a needle holder to the surgeon.");
    expect(messages[1]!.text["zh-CN"]).toBe("林护士（洗手），请把持针器递给术者。");
    const handOver = receipts(events).filter((r) => r.actor === SCRUB && r.operation === "hand_over");
    expect(handOver).toMatchObject([{ outcome: "completed", target: NEEDLE_HOLDER, recipient: PRIMARY_ACTOR }]);
    expect(t.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    // every decision was the member's model's: one call per member move, each with its role card
    const decisions = t.provider!.requests.filter((r) => r.responseFormat?.name === "team_decision");
    expect(decisions.length).toBeGreaterThanOrEqual(6);
    expect(decisions.some((r) => systemText(r).includes("the circulating nurse"))).toBe(true);
    expect(decisions.some((r) => systemText(r).includes("the scrub nurse"))).toBe(true);
    expect(msgsOf(t.events, "warning").filter((w) => /rules decided/u.test(w.message))).toEqual([]);
    await t.session.close();
  });

  it("a member's line that states what nobody perceived is refused: the team's words are said, and the loop still closes", async () => {
    const t = await theatre("needle-holder", { engine: "llm", scripts: scripts(model((usual) => `${usual} I have 4 more on the trolley.`)) });
    toTheTable(t);
    const messages = said(await walkToTable(t));
    expect(messages.map((m) => m.kind)).toEqual(["notice", "request", "readback", "confirm", "report", "report"]);
    expect(messages[1]!.text.en).toBe("Nurse Lim (scrub), please pass a needle holder to the surgeon.");
    expect(t.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain(NEEDLE_HOLDER);
    await t.session.close();
  });
});
