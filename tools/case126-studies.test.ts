/**
 * Case 126 in OR 7: investigations beyond the published case (ClinicalCraft docs/STUDIES.md; the engineering brief's
 * first release scenario, the diagnostic part).
 *
 *   - the chart's two commands apart: retrieving the historical ECG finds none ("historical material unavailable");
 *     ordering a new 12-lead ECG creates a task the simulated hospital fulfils;
 *   - the circulating nurse fetches the department's only mobile ECG machine from the anaesthesia workroom with their
 *     own body and records it (mirrored leads for dextrocardia); the report is released after its turnaround,
 *     labelled a simulated investigation; the anaesthetist reviews it in their own name;
 *   - a retried request is the same order; a deliberate repeat is a new accession; a released report survives a save,
 *     a reload and a change of language unchanged;
 *   - a cholangiogram is never ordered from the chart; a chest radiograph the hospital cannot take waits with its
 *     reason; a new sample keeps the values of the moment it was drawn.
 *
 * `tools/check.sh` copies this file into `<ClinicalCraft>/packages/agent/src/` for the run and removes it afterwards.
 * The repository root comes from $SURGERYCRAFT_ROOT.
 */
import { describe, expect, it } from "vitest";
import { PRIMARY_ACTOR } from "@clinicalcraft/world";
import type { CaseDefinition, ClinicalAction } from "@clinicalcraft/core";
import { makeSession, msgsOf, type TestSession } from "./__fixtures__/harness.js";
import { loadContent } from "./node/content.js";

const ROOT = process.env.SURGERYCRAFT_ROOT ?? "";
const CASE = "cmcr-1654623";
const ECG = "eq:anaes-workroom-ecg";
const CIRCULATOR = "staff:or-7.circulating-nurse";
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

/** The case in theatre, before induction (the reference record up to the induction), the surgeon at the patient. */
async function beforeInduction(extra: Partial<Parameters<typeof makeSession>[0]> = {}): Promise<TestSession> {
  const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS, ...extra });
  await t.session.run({ type: "clinical_action", action: { type: "start" } });
  const sol = t.session.caseDef.solution;
  for (const a of sol.slice(1, sol.findIndex((x) => x.type === "intervene" && x.interventionId === "induction"))) {
    const r = t.session.dispatch({ ...a, by: "system" } as ClinicalAction);
    if (r.rejected) throw new Error(`${a.type}: ${r.rejected.message}`);
  }
  const patient = t.session.world()!.find(PRIMARY_ACTOR, { kind: "patient" })[0]!.id;
  await t.session.run({ type: "world_action", request: { actionId: "to-patient", actorId: PRIMARY_ACTOR, operation: "navigate", goal: { kind: "interact", id: patient } } });
  return t;
}

let n = 0;
async function tool(t: TestSession, name: string, args: Record<string, unknown> = {}) {
  const events = await t.session.run({ type: "external_tool_call", callId: `s-${++n}`, tool: name, args, allowBypass: true });
  return { ...(msgsOf(events, "tool_call_end").at(-1) as { ok: boolean; output: string; data?: any }), events };
}

describe("Case 126 in OR 7 · investigations beyond the published case", () => {
  it("no historical ECG; a new one ordered, fetched by the nurse, recorded, reported (simulated) and reviewed by the anaesthetist", async () => {
    const t = await beforeInduction();
    const w = t.session.world()!;
    expect(t.session.state.phase).toBe("theatre");
    // retrieve: the published case has no ECG
    const retrieved = await tool(t, "retrieve_report", { query: "ECG" });
    expect(retrieved.output).toMatch(/^Historical material unavailable — .+: No ECG is recorded/);
    expect(retrieved.data?.source).toBe("unavailable");
    // order: a new study, fulfilled by the hospital
    const deviceFrom = w.roomOf(ECG);
    expect(deviceFrom).toBe("anaes-workroom");
    const ordered = await tool(t, "order_study", { query: "ECG", indication: "pre-induction ECG: 84 years, dextrocardia", lead_placement: "mirror", request_key: "pre-induction-ecg" });
    expect(ordered.ok, ordered.output).toBe(true);
    expect(ordered.output).toMatch(/^Simulated investigation: 12-lead ECG \(new, simulated\) ordered \(ord-1\)\. Nurse Aisyah \(circulating\) will fetch the Mobile ECG machine to the patient/);
    // the nurse walked to the workroom and wheeled the machine to the patient, with their own body
    expect(w.roomOf(ECG)).toBe("or-7");
    expect(t.session.world()!.atBedside(ECG)).toBe(true);
    const nurseActs = msgsOf(ordered.events, "world_action_result").filter((m) => m.result.status === "completed");
    expect(nurseActs.length).toBeGreaterThan(0);
    const a = t.session.state.studies!.accessions[0]!;
    expect(a).toMatchObject({ id: "ecg-12lead-1", order: "ord-1", collector: "or-7.circulating-nurse", configuration: "mirror" });
    expect(a.observations.map((o) => o.id)).toEqual(expect.arrayContaining(["rate", "rhythm", "pr", "qrs", "qtc", "leads", "morphology"]));
    // the same request again: the same order
    const again = await tool(t, "order_study", { query: "ECG", request_key: "pre-induction-ecg" });
    expect(again.output).toMatch(/already ordered \(ord-1\)/);
    expect(t.session.state.studies!.orders).toHaveLength(1);
    // not yet reported; after the turnaround: released, labelled, reviewed by the anaesthetist in their own name
    expect((await tool(t, "read_study", { query: "ECG" })).output).toMatch(/acquired by Nurse Aisyah \(circulating\) at .* the report is due/);
    const waited = await tool(t, "wait", { minutes: 10 });
    const said = msgsOf(waited.events, "agent_message").map((m) => `${m.speaker}: ${m.text}`);
    expect(said.some((l) => /^Dr Tanaka \(anaesthesia\): I've reviewed the simulated 12-lead ECG/.test(l))).toBe(true);
    const report = await tool(t, "read_study", { query: "ECG" });
    expect(report.output).toMatch(/^Simulated investigation · 12-lead ECG \(new, simulated\) · ecg-12lead-1\n/);
    expect(report.output).toMatch(/leads mirrored for dextrocardia/);
    expect(report.output).toMatch(/Impression: with the leads mirrored, the tracing reads as a normally placed heart/);
    expect(report.output).toMatch(/\nDr Tanaka \(anaesthesia\) reviewed the 12-lead ECG/);
    expect(t.session.state.studies!.reviews).toMatchObject([{ accession: "ecg-12lead-1", by: "or-7.anaesthetist" }]);
    expect((await tool(t, "case_status")).output).toMatch(/New investigations \(simulated\):\n {2}Simulated investigation · 12-lead ECG/);

    // a save and a reload, then a change of language: the same report, the device where it was left
    const saved = JSON.parse(JSON.stringify(t.session.snapshot()));
    await t.session.close();
    const r = await makeSession({ ...(await content()), settingsPatch: SETTINGS, resume: { sessionId: saved.sessionId, actions: saved.actions, messages: saved.messages, dialogue: saved.dialogue }, embodied: { snapshot: saved.world, team: saved.team } });
    expect(r.session.state.studies).toEqual(saved.state?.studies ?? t.session.state.studies);
    expect(r.session.world()!.roomOf(ECG)).toBe("or-7");
    expect((await tool(r, "read_study", { query: "ECG" })).output).toBe(report.output);
    await r.session.run({ type: "configure", patch: { locale: "zh-CN" } });
    const zh = await tool(r, "read_study", { query: "心电图" });
    expect(zh.output).toMatch(/^模拟检查 · 十二导联心电图（新开，模拟） · ecg-12lead-1/);
    for (const o of a.observations) if (o.value != null) expect(zh.output).toContain(String(o.value));
    await r.session.close();
  });

  it("a deliberate repeat is a new accession; a sample keeps the values of the moment it was drawn", async () => {
    const t = await beforeInduction();
    await tool(t, "order_study", { code: "ecg-12lead", lead_placement: "standard", request_key: "k1" });
    await tool(t, "order_study", { code: "ecg-12lead", lead_placement: "mirror", request_key: "k2" });
    expect(t.session.state.studies!.accessions.map((x) => [x.id, x.configuration])).toEqual([
      ["ecg-12lead-1", "standard"],
      ["ecg-12lead-2", "mirror"],
    ]);
    // standard leads with dextrocardia: the tracing shows it, and the impression says to repeat mirrored
    expect(t.session.state.studies!.accessions[0]!.observations.map((o) => o.id)).toEqual(expect.arrayContaining(["lead-i", "progression"]));
    await tool(t, "order_study", { query: "bilirubin", request_key: "chem-1" });
    const chem = t.session.state.studies!.accessions.find((x) => x.code === "chemistry")!;
    expect(chem.observations.find((o) => o.id === "tbil")).toMatchObject({ value: 0.8, unit: "mg/dL", flag: "normal" });
    await tool(t, "wait", { minutes: 40 });
    expect((await tool(t, "read_study", { code: "chemistry" })).output).toMatch(/Total bilirubin 0\.8 mg\/dL \(0\.2–1\.2\)/);
    await t.session.close();
  });

  it("the second run: the only machine out of service waits with its reason, the order and its requester kept; back in service, it is fulfilled", async () => {
    const t = await beforeInduction();
    t.session.world()!.setAvailability(ECG, false);
    const ordered = await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "k" });
    expect(ordered.ok).toBe(true);
    const o = t.session.state.studies!.orders[0]!;
    expect(o).toMatchObject({ code: "ecg-12lead", requester: expect.any(String), waiting: { reason: "the Mobile ECG machine is out of service" } });
    expect(t.session.state.studies!.accessions).toEqual([]);
    expect((await tool(t, "read_study", { query: "ECG" })).output).toMatch(/waiting — the Mobile ECG machine is out of service/);
    // back in service: the next act fulfils the same order (no second order), the requester unchanged
    t.session.world()!.setAvailability(ECG, true);
    await tool(t, "case_status");
    expect(t.session.state.studies!.orders).toHaveLength(1);
    expect(t.session.state.studies!.orders[0]).toMatchObject({ id: o.id, requester: o.requester });
    expect(t.session.state.studies!.accessions.map((a) => a.order)).toEqual([o.id]);
    await t.session.close();
  });

  it("the second run: the way to the machine blocked (the workroom door locked), the order waits with the nurse's reason; the door opened, it is fulfilled", async () => {
    const t = await beforeInduction();
    const w = t.session.world()!;
    w.setDoor("door:anaes-workroom:n:0", { open: false, locked: true });
    await tool(t, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "k" });
    const o = t.session.state.studies!.orders[0]!;
    expect(o.waiting?.reason).toMatch(/^Nurse Aisyah \(circulating\) could not bring the Mobile ECG machine: /);
    expect(t.session.state.studies!.accessions).toEqual([]);
    expect(w.roomOf(ECG)).toBe("anaes-workroom");
    w.setDoor("door:anaes-workroom:n:0", { open: false, locked: false });
    await tool(t, "case_status");
    expect(t.session.state.studies!.orders).toHaveLength(1);
    expect(t.session.state.studies!.accessions.map((a) => a.order)).toEqual([o.id]);
    expect(w.roomOf(ECG)).toBe("or-7");
    await t.session.close();
  });

  it("the nurse shut out of OR 7: a blood count is assigned, blocked with the reason, no specimen and no result; the door opened, the same order is collected once and reported once", async () => {
    const t = await beforeInduction();
    const w = t.session.world()!;
    const NURSE = "staff:or-7.circulating-nurse";
    // the nurse steps out to theatre control, and OR 7's doors are locked behind them
    expect((await t.session.run({ type: "world_action", request: { actionId: "out", actorId: NURSE, operation: "navigate", goal: { kind: "room", id: "l1-control" } } })).length).toBeGreaterThan(0);
    expect(w.roomOf(NURSE)).toBe("l1-control");
    // every door on OR 7's walls (its own, and the scrub bays' and set-up rooms' into it): x 2–11, z −2–7 on L1
    const doors = w.entities().filter((e) => e.kind === "door" && e.level === "L1" && e.position.x >= 1.9 && e.position.x <= 11.1 && e.position.z >= -2.1 && e.position.z <= 7.1).map((e) => e.id);
    expect(doors.length).toBeGreaterThan(0);
    for (const d of doors) w.setDoor(d, { open: false, locked: true });
    await tool(t, "order_study", { query: "blood count", request_key: "cbc-1" });
    const o = t.session.state.studies!.orders[0]!;
    expect(o).toMatchObject({ code: "cbc", assignee: "or-7.circulating-nurse", stage: "blocked", waiting: { reason: expect.stringMatching(/^Nurse Aisyah \(circulating\) could not reach the patient: /) } });
    expect(o.stages!.map((x) => x.stage)).toEqual(["ordered", "assigned", "en-route", "blocked"]);
    expect(t.session.state.studies!.accessions).toEqual([]);
    expect((await tool(t, "read_study", { query: "blood count" })).output).toMatch(/waiting — Nurse Aisyah \(circulating\) could not reach the patient/);
    await tool(t, "wait", { minutes: 30 });
    expect(t.session.state.studies!.accessions).toEqual([]);
    expect(t.session.state.studies!.reports).toEqual([]);
    // unlocked: the same order resumes, one specimen, one report
    for (const d of doors) w.setDoor(d, { locked: false });
    await tool(t, "case_status");
    expect(t.session.state.studies!.orders).toHaveLength(1);
    expect(t.session.state.studies!.accessions.map((a) => [a.order, a.collector])).toEqual([[o.id, "or-7.circulating-nurse"]]);
    expect(w.roomOf(NURSE)).toBe("or-7");
    await tool(t, "wait", { minutes: 30 });
    await tool(t, "case_status");
    expect(t.session.state.studies!.accessions).toHaveLength(1);
    expect(t.session.state.studies!.reports).toHaveLength(1);
    expect(t.session.state.studies!.orders[0]!.stages!.map((x) => x.stage)).toEqual(["ordered", "assigned", "en-route", "blocked", "en-route", "at-patient", "acquisition-started", "acquired", "reported"]);
    await t.session.close();
  });

  it("the second run: a reporting agent that times out, or writes what the tracing does not show, is replaced by the template — never an invented report", async () => {
    // a writer that never answers
    const stuck = await beforeInduction({ reportWriter: () => new Promise(() => {}), reportWriterTimeoutMs: 50 });
    await tool(stuck, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "k" });
    await tool(stuck, "wait", { minutes: 10 });
    expect(stuck.session.state.studies!.reports).toMatchObject([{ accession: "ecg-12lead-1", generator: "template" }]);
    expect(stuck.session.state.studies!.reviews).toHaveLength(1);
    await stuck.session.close();
    // a writer that invents a number and a side the observations do not have
    const wrong = await beforeInduction({
      reportWriter: async () => ({
        findings: { en: "Rate 190/min, ST elevation in the left chest leads.", "zh-CN": "心率 190 次/分，左胸导联 ST 段抬高。" },
        impression: { en: "Acute infarction.", "zh-CN": "急性心肌梗死。" },
        generator: "a-model",
      }),
    });
    await tool(wrong, "order_study", { query: "ECG", lead_placement: "mirror", request_key: "k" });
    await tool(wrong, "wait", { minutes: 10 });
    const report = wrong.session.state.studies!.reports[0]!;
    expect(report.generator).toBe("template");
    expect(report.findings.en).not.toMatch(/190|infarction/);
    await wrong.session.close();
  });

  it("records in the simulated timeline: before the review the operation record, the histology and the follow-up do not exist yet — no text from a later phase; in the review they do", async () => {
    const c = (await content()).caseDef;
    const t = await makeSession({ ...(await content()), settingsPatch: SETTINGS });
    await t.session.run({ type: "clinical_action", action: { type: "start" } });
    expect(t.session.state.phase).toBe("assessment");
    const text = (id: string) => (c.investigations.find((i) => i.id === id)!.results.review!.text as { en: string }).en;
    for (const [query, id] of [["operation record", "operation-record"], ["pathology", "pathology-record"], ["follow-up", "followup-record"]] as const) {
      const r = await tool(t, "retrieve_report", { query });
      expect(r.data, query).toMatchObject({ source: "not-yet", investigationId: id });
      expect(r.output).toMatch(/^Record not yet created — /);
      expect(r.output).not.toContain(text(id).slice(0, 40));
      // ordered or read directly: refused, nothing recorded
      const ordered = await tool(t, "order_test", { investigation_id: id });
      expect(ordered.ok).toBe(false);
      expect(t.session.state.orders.some((o) => o.investigationId === id)).toBe(false);
      const read = await tool(t, "read_result", { investigation_id: id, phase: "review" });
      expect(read.ok).toBe(false);
      expect(read.output).not.toContain(text(id).slice(0, 40));
    }
    // the source's preoperative reports are there
    expect((await tool(t, "retrieve_report", { query: "CT" })).data).toMatchObject({ source: "record", investigationId: "ct-record" });
    await t.session.close();
    // in the review the records exist (a clinical-mode run of the reference record: in OR 7 the Sign Out also waits
    // for the swab count, which tools/case126-count.test.ts works through)
    const r = await makeSession({ ...(await content()), settingsPatch: { embodiment: "clinical", approvalMode: "bypass" } });
    await r.session.run({ type: "clinical_action", action: { type: "start" } });
    const sol = c.solution;
    const at = sol.findIndex((a) => a.type === "order" && a.investigationId === "operation-record");
    for (const a of sol.slice(1, at)) {
      const x = r.session.dispatch({ ...a, by: "system" } as ClinicalAction);
      if (x.rejected) throw new Error(`${a.type}: ${x.rejected.message}`);
    }
    expect(r.session.state.phase).toBe("review");
    for (const [query, id] of [["operation record", "operation-record"], ["pathology", "pathology-record"], ["follow-up", "followup-record"]] as const) {
      const got = await tool(r, "retrieve_report", { query });
      expect(got.data, query).toMatchObject({ source: "record", investigationId: id });
      expect(got.output).toContain(text(id).slice(0, 40));
    }
    await r.session.close();
  });

  it("never invented: a cholangiogram is acquired at the table, not ordered; a chest radiograph the hospital cannot take waits with its reason", async () => {
    const t = await beforeInduction();
    const ioc = await tool(t, "order_study", { query: "intraoperative cholangiogram" });
    expect(ioc.ok).toBe(false);
    expect(ioc.output).toMatch(/done at the table, not ordered from the chart/);
    expect(t.session.state.studies?.orders ?? []).toEqual([]);
    const cxr = await tool(t, "order_study", { query: "chest x-ray" });
    expect(cxr.ok).toBe(true);
    expect(t.session.state.studies!.orders[0]).toMatchObject({ code: "cxr", waiting: { reason: expect.stringMatching(/no device in this hospital provides xray/) } });
    expect(t.session.state.studies!.accessions).toEqual([]);
    expect((await tool(t, "read_study", { query: "chest x-ray" })).output).toMatch(/waiting — no device in this hospital provides xray/);
    // a hand-entered report is refused
    const forged = await t.session.run({ type: "clinical_action", action: { type: "study", study: { op: "release", accession: "cxr-1", findings: { en: "x", "zh-CN": "x" }, impression: { en: "x", "zh-CN": "x" }, generator: "me" } } as ClinicalAction });
    expect(msgsOf(forged, "error")[0]).toMatchObject({ code: "permission_denied" });
    expect(t.session.state.studies!.reports).toEqual([]);
    await t.session.close();
  });
});
