/**
 * IMPF Surgery Hospital: the pack's project skills (`.clinicalcraft/skills/*.json`) — loaded as ClinicalCraft loads a
 * trusted project's skills, then run in an embodied session of the operating-room case in OR 7 through the learner's
 * own tool path (authority, reach, preconditions), succeeding only when their postconditions hold in the world; and
 * "Pass me the needle holder" said to the scrub nurse by name; the thoracoscopy set-up in OR 5 and in the simulation OR
 * (docs/THORACOSCOPY.md). `tools/check.sh` copies this file into
 * `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 *
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR } from "@clinicalcraft/world";
import { builtinContent, command } from "./__fixtures__/embodied.js";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";
import { loadProjectSkills } from "./node/skills.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";

async function theatre(): Promise<TestSession> {
  const builtin = await builtinContent();
  const pack = await loadContent({ dirs: [`${ROOT}/content`], cases: false });
  const facility = pack.facilities.get("impf-surgery-hospital")?.def;
  if (!facility) throw new Error(`no IMPF facility: ${JSON.stringify(pack.issues).slice(0, 400)}`);
  const catalogs = facility.catalogs.map((id) => pack.catalogs.get(id)!.def);
  const { skills, issues } = await loadProjectSkills(ROOT, { HOME: "/nonexistent" }, { trusted: true });
  expect(issues).toEqual([]);
  return makeSession({ caseDef: builtin.cases.get("cmcr-1653406")!.def, facility, catalogs, skills, settingsPatch: { embodiment: "embodied", approvalMode: "bypass" } });
}

describe("IMPF Surgery Hospital · project skills and the OR team", () => {
  it("the WHO sign-in / time-out and the closing counts run as skills and verify against the world", async () => {
    const t = await theatre();
    const timeOut = await command(t, "skill", "project:impf_surgical_time_out");
    expect(timeOut.ok, timeOut.text).toBe(true);
    expect(timeOut.data.skill).toMatchObject({ status: "succeeded" });
    const close = await command(t, "skill", "project:impf_closing_counts");
    expect(close.ok, close.text).toBe(true);
    expect(close.data.skill).toMatchObject({ status: "succeeded" });
    const w = t.session.world()!;
    // the counts and the scan before closure; the Sign Out is the board's, after closure (not the skill's)
    expect(w.inspect(PRIMARY_ACTOR, "eq:or-7.checklist")?.state).toBe("timed-out");
    expect(w.inspect(PRIMARY_ACTOR, "eq:or-7.count-board")?.state).toBe("reconciled");
    await t.session.close();
  });

  it("the thoracoscopy set-up runs as a skill in the theatre the learner stands in: OR 5, then the simulation OR", async () => {
    const t = await theatre();
    const w = t.session.world()!;
    for (const [room, prefix] of [["or-5", "or-5"], ["l0-sim-or", "l0-sim-or"]] as const) {
      await t.session.run({ type: "world_action", request: { actionId: `wa-${room}`, actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "room", id: room } } });
      // the evacuator is off and the drainage unit still in its pack; the tower was white-balanced before the list
      expect(w.inspect(PRIMARY_ACTOR, `eq:${prefix}.smoke-evac`)?.state).toBe("off");
      expect(w.inspect(PRIMARY_ACTOR, `eq:${prefix}.chest-drain`)?.state).toBe("sealed");
      const run = await command(t, "skill", "project:impf_thoracoscopy_setup");
      expect(run.ok, run.text).toBe(true);
      expect(run.data.skill).toMatchObject({ status: "succeeded" });
      expect(w.inspect(PRIMARY_ACTOR, `eq:${prefix}.vats-tower`)?.state).toBe("balanced");
      expect(w.inspect(PRIMARY_ACTOR, `eq:${prefix}.smoke-evac`)?.state).toBe("running");
      expect(w.inspect(PRIMARY_ACTOR, `eq:${prefix}.chest-drain`)?.state).toBe("primed");
    }
    // the neighbouring theatre's evacuator was not touched: the skill works in the room it is run in
    expect(w.inspect(PRIMARY_ACTOR, "eq:or-6.smoke-evac")?.state).toBe("off");
    await t.session.close();
  });

  it("'Pass me the needle holder' to the scrub nurse by name: she picks it up and hands it over", async () => {
    const t = await theatre();
    await t.session.run({ type: "world_action", request: { actionId: "wa-go", actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "room", id: "or-7" } } });
    const out = await t.session.run({ type: "user_message", text: "Pass me the needle holder, please", to: "nurse", staff: "or-7.scrub-nurse" });
    const said = msgsOf(out, "agent_message").map((m) => m.text);
    expect(said[0]).toMatch(/needle holder.*coming/i);
    expect(said.at(-1)).toMatch(/^Here you are/);
    expect(t.session.world()!.actor(PRIMARY_ACTOR)!.holding).toContain("eq:or-7.needle-holder");
    await t.session.close();
  });
});
