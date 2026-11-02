/**
 * Case 126 (cmcr-1654623): fidelity and safety checks on the real case, run inside a ClinicalCraft checkout
 * by tools/check.sh (copied to packages/core/src/zz-surgerycraft-case126.test.ts; the case path comes from
 * $SURGERYCRAFT_CONTENT).
 *
 * - evidence: every published value matches the source summary; synthetic values are listed as synthetic;
 *   every history/exam/record item has a ledger entry; unknowns stay unknown;
 * - anatomy: situs inversus laterality in the patient frame (+x = the patient's left), topology of the
 *   ducts and arteries;
 * - safety: the reference path is clear and scores 100; unsafe paths never come out with a valid critical
 *   view; a misidentified common bile duct is a safety-critical failure; a bail-out is accepted;
 * - hidden state: the operator's view never names a duct or vessel;
 * - anatomical variants (procedure.variants; the operative suite content/operative/case126-v1): each is authored,
 *   referenced and on the patient's left; each scenario's expert trajectory, through the whole case, is clear and
 *   meets the variant's own rubric item; the reported anatomy's routine replayed blind is safety-critical in every
 *   variant (the suite discriminates); the scenarios never name the anatomy they hide.
 */
import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  assess,
  checkCaseIntegrity,
  createSession,
  evaluate,
  observeField,
  parseCase,
  reduce,
  type CaseDefinition,
  type ClinicalAction,
  type ProcedureOp,
  type SessionState,
} from "@clinicalcraft/core";

const DIR = `${process.env.SURGERYCRAFT_CONTENT ?? ""}/cases/cmcr-1654623`;
const json = JSON.parse(readFileSync(`${DIR}/case.json`, "utf8"));
const ledger = JSON.parse(readFileSync(`${DIR}/evidence.json`, "utf8"));
const parsed = parseCase(json);
if (!parsed.ok) throw new Error(JSON.stringify(parsed.issues.slice(0, 5)));
const c: CaseDefinition = parsed.value;
const def = c.procedure!;

function replay(actions: ClinicalAction[]) {
  let s: SessionState = createSession(c);
  const rejected: { action: ClinicalAction; message: string }[] = [];
  for (const a of actions) {
    const r = reduce(c, s, a);
    if (r.rejected) rejected.push({ action: a, message: r.rejected.message });
    s = r.state;
  }
  return { s, rejected };
}

/** The reference path up to (not including) the first `operate` step: history, records, decisions, checklist. */
const firstOp = c.solution.findIndex((a) => a.type === "operate");
const PREOP = c.solution.slice(0, firstOp);
const op = (o: ProcedureOp): ClinicalAction => ({ type: "operate", op: o });
const ACCESS = c.solution.filter((a) => a.type === "operate").slice(0, 5);
const neck = def.anatomy.some((s) => s.id === "gallbladder-infundibulum") ? "gallbladder-infundibulum" : "gallbladder";

describe("Case 126: content", () => {
  it("validates with no integrity errors", () => {
    expect(checkCaseIntegrity(c).filter((i) => i.severity === "error")).toEqual([]);
  });

  it("keeps the source's published values", () => {
    const v = Object.fromEntries((ledger.values as { fact: string; value: unknown }[]).map((x) => [x.fact, x.value]));
    expect(c.patient.age).toBe(84);
    expect(v.age).toBe(84);
    expect(v.temperature_c).toBe(36.6);
    expect(v.pulse_per_min).toBe(78);
    expect(v.respiratory_rate_per_min).toBe(19);
    expect(v.blood_pressure_mmHg).toBe("128/78");
    expect(c.physiology?.baseline).toMatchObject({ hr: 78, sbp: 128, dbp: 78, rr: 19, temp: 36.6 });
  });

  it("labels every simulated value as synthetic and needing review", () => {
    const synthetic = (ledger.values as { fact: string; provenance: string; simulationOverride?: { classification: string; requiresClinicalReview: boolean } }[]).filter((x) => x.simulationOverride);
    expect(synthetic.map((x) => x.fact)).toContain("baseline_spo2");
    for (const x of synthetic) {
      expect(x.provenance).toBe("unknown");
      expect(x.simulationOverride!.requiresClinicalReview).toBe(true);
    }
    for (const e of c.physiology!.events) expect(JSON.stringify(e.message)).toMatch(/模拟值|simulated value/);
    expect(synthetic.filter((x) => x.fact.startsWith("intraoperative_")).length).toBe(c.physiology!.events.length);
  });

  it("traces every history, exam and record item in the evidence ledger", () => {
    const ids = new Set((ledger.facts as { id: string }[]).map((f) => f.id));
    for (const section of [c.history, c.exam, c.investigations]) for (const x of section) expect(ids.has(x.id), x.id).toBe(true);
  });

  it("keeps unrecorded items unknown", () => {
    for (const id of ["allergies", "medications", "antithrombotic", "copd-status", "stroke-deficit"]) expect(c.history.find((h) => h.id === id)?.disclosure, id).toBe("unknown");
    for (const id of ["ecg-record", "pft-record", "cxr-record"]) expect(Object.values(c.investigations.find((i) => i.id === id)!.results)[0]?.available, id).toBe(false);
  });

  it("does not call the presentation a confirmed acute cholecystitis", () => {
    const d = c.decisions.find((x) => x.id === "diagnosis")!;
    expect(d.options.find((o) => o.correct)?.id).toBe("suspected");
  });
});

describe("Case 126: anatomy (situs inversus totalis, patient frame +x = patient's left)", () => {
  const at = (id: string) => def.anatomy.find((s) => s.id === id)!;
  const meanX = (id: string) => at(id).points.reduce((a, p) => a + p[0], 0) / at(id).points.length;

  it("puts the liver and gallbladder on the patient's left, the stomach and spleen on the right", () => {
    expect(meanX("liver")).toBeGreaterThan(0);
    expect(meanX("gallbladder")).toBeGreaterThan(0);
    expect(meanX("stomach")).toBeLessThan(0);
    expect(meanX("spleen")).toBeLessThan(0);
  });

  it("joins the ducts and arteries into one tree", () => {
    const d = (a: number[], b: number[]) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    const cd = at("cystic-duct").points, chd = at("common-hepatic-duct").points, cbd = at("common-bile-duct").points;
    expect(d(cd.at(-1)!, chd.at(-1)!)).toBeLessThan(0.005);
    expect(d(chd.at(-1)!, cbd[0])).toBeLessThan(0.005);
    const rha = at("right-hepatic-artery").points;
    const origin = at("cystic-artery").points[0];
    expect(Math.min(...rha.map((p) => d(p, origin)))).toBeLessThan(0.01);
    for (const s of def.anatomy) expect(s.provenance, s.id).toBeTruthy();
  });

  it("names its regions and ports in the same frame: the report's ports reach the triangle", () => {
    const plan = def.portPlans.find((p) => p.id === "three-port-left")!;
    expect(plan.provenance).toBe("published-case");
    expect(plan.ports.map((p) => [p.site, p.sizeMm])).toEqual([["A", 10], ["B", 5], ["C", 5]]);
  });
});

describe("Case 126: the operation", () => {
  it("the reference path completes every objective, is clear and scores 100", () => {
    const { s, rejected } = replay(c.solution);
    expect(rejected).toEqual([]);
    expect(s.finished).toBe(true);
    const report = assess(c, s);
    expect(report.safety.verdict).toBe("clear");
    expect(report.score.percent).toBe(100);
    expect(report.procedure?.unsafe).toEqual([]);
  });

  it("habitual traction (towards the patient's right) never yields a valid critical view; clipping the common bile duct taken for the cystic duct is safety-critical", () => {
    const wrong = op({ op: "retract", port: "B", structure: neck, direction: ["patient-right", "caudal"], force: "firm" });
    const dissect = Array.from({ length: 12 }, () => op({ op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false }));
    const base = replay([...PREOP, ...ACCESS, wrong, ...dissect]);
    const cbd = base.s.procedure!.handles.find((h) => h.structure === "common-bile-duct")!.handle;
    const view = observeField(def, base.s.procedure!);
    expect(view.tubes.find((t) => t.handle === cbd)?.appears).toMatchObject({ en: "a duct that seems to run straight into the gallbladder neck" });
    const { s } = replay([
      ...PREOP, ...ACCESS, wrong, ...dissect,
      op({ op: "isolate", port: "C", handle: cbd }),
      op({ op: "identify", handle: cbd, as: "cystic-duct" }),
      op({ op: "safety-pause", view: "cvs", claims: { triangle: true, plate: true, two: true } }),
      op({ op: "withdraw", port: "C" }), op({ op: "insert", port: "C", instrument: "clip-applier" }),
      op({ op: "clip", port: "C", handle: cbd, count: 3 }),
    ]);
    expect(evaluate(c, s, { procedure: { documented: "cvs", valid: true } })).toBe(false);
    expect(evaluate(c, s, { procedure: { injury: "bile-duct-injury" } })).toBe(true);
    const report = assess(c, s);
    expect(report.safety.verdict).toBe("safety-critical");
    expect(report.safety.gates?.map((g) => g.id)).toEqual(expect.arrayContaining(["bile-duct-injury", "misidentified"]));
    expect(report.score.percent).toBeLessThanOrEqual(40);
  });

  it("a subtotal cholecystectomy when the view is not reached is accepted and ends the dissection", () => {
    const { s, rejected } = replay([
      ...PREOP, ...ACCESS,
      op({ op: "retract", port: "B", structure: neck, direction: ["patient-left", "caudal"], force: "firm" }),
      op({ op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false }),
      op({ op: "bailout", strategy: "subtotal-fenestrating" }),
      op({ op: "close" }),
    ]);
    expect(rejected).toEqual([]);
    expect(s.procedure!.unsafe).toEqual([]);
    expect(evaluate(c, s, { procedure: { closed: true } })).toBe(true);
  });

  it("the operator's view never names a duct or vessel before imaging", () => {
    const { s } = replay(c.solution.slice(0, c.solution.findIndex((a) => a.type === "operate" && a.op.op === "isolate")));
    const view = observeField(def, s.procedure!);
    expect(view.tubes.length).toBeGreaterThanOrEqual(3);
    const names = def.anatomy.filter((x) => ["duct", "artery", "vein"].includes(x.kind)).map((x) => x.id);
    const text = JSON.stringify(view.tubes);
    for (const n of names) expect(text).not.toContain(n);
  });

  it("reversing Sign In and induction is visible in the final verdict; an early Time Out leaves surgery locked", () => {
    const sol = c.solution;
    const signIn = sol.findIndex((a) => a.type === "intervene" && a.interventionId === "sign-in");
    const induction = sol.findIndex((a) => a.type === "intervene" && a.interventionId === "induction");
    const reversed = [...sol];
    [reversed[signIn], reversed[induction]] = [reversed[induction]!, reversed[signIn]!];
    const { s, rejected } = replay(reversed);
    expect(rejected).toEqual([]);
    const report = assess(c, s);
    expect(report.safety.verdict).toBe("safety-critical");
    expect(report.safety.gates?.map((g) => g.id)).toContain("induction-before-sign-in");
    expect(report.rubric.find((r) => r.id === "r-signin")?.met).toBe(false);
    expect(report.score.percent).toBeLessThan(100);
    // a Time Out before induction: logged as invalid, the operation stays locked; the later one opens it
    const early = replay([...sol.slice(0, signIn), { type: "intervene", interventionId: "time-out" }, { type: "operate", op: { op: "plan-ports", plan: "three-port-left" } }]);
    expect(early.s.interventions.at(-1)).toMatchObject({ interventionId: "time-out", invalid: true });
    expect(early.s.phase).not.toBe("operation");
    expect(early.rejected.at(-1)?.message).toMatch(/not under way/);
    const later = replay([...sol.slice(0, signIn), { type: "intervene", interventionId: "time-out" }, ...sol.slice(signIn)]);
    expect(later.rejected).toEqual([]);
    expect(later.s.finished).toBe(true);
    expect(assess(c, later.s).rubric.find((r) => r.id === "r-timeout")?.met).toBe(false); // the out-of-order attempt is on record
  });

  it("the operation cannot start before the Time Out", () => {
    const sign = PREOP.findIndex((a) => a.type === "intervene" && a.interventionId === "time-out");
    const { rejected } = replay([...PREOP.slice(0, sign), op({ op: "plan-ports", plan: "three-port-left" })]);
    expect(rejected.at(-1)?.message).toMatch(/not under way/);
  });
});

/* ------------------------------------------------------------------ */
/* Anatomical variants and the operative suite                          */
/* ------------------------------------------------------------------ */

type Step = Record<string, unknown>;
const SUITE_DIR = `${process.env.SURGERYCRAFT_CONTENT ?? ""}/operative/case126-v1`;
const scenarios = readdirSync(SUITE_DIR)
  .filter((f) => f.endsWith(".json"))
  .map((f) => JSON.parse(readFileSync(`${SUITE_DIR}/${f}`, "utf8")) as { id: string; split: string; variant: string | { pool: string[] }; instruction: { en: string; "zh-CN": string }; reference: Record<string, Step[]> });
const trajectories = new Map<string, Step[]>();
for (const sc of scenarios) for (const [v, steps] of Object.entries(sc.reference)) trajectories.set(v, steps);
const VARIANTS = def.variants.map((v) => v.id);
const start = (variant: string): ClinicalAction => ({ type: "start", ...(variant !== "reference" ? { variant } : {}) }) as ClinicalAction;
const AFTER_CLOSE = c.solution.slice(c.solution.findIndex((a) => a.type === "operate" && a.op.op === "close") + 1);

/** A trajectory's `@structure` handles resolved by replaying it after the preamble (as ClinicalCraft's operative runner does). */
function resolveSteps(variant: string, steps: readonly Step[]): ProcedureOp[] {
  let s = replay([start(variant), ...PREOP.filter((a) => a.type !== "start")]).s;
  const out: ProcedureOp[] = [];
  for (const [i, raw] of steps.entries()) {
    const step = { ...raw } as Step;
    if (typeof step.handle === "string" && step.handle.startsWith("@")) {
      const h = s.procedure?.handles.find((x) => x.structure === (step.handle as string).slice(1))?.handle;
      if (!h) throw new Error(`${variant} step ${i + 1}: ${step.handle} not in view`);
      step.handle = h;
    }
    const r = reduce(c, s, op(step as ProcedureOp));
    if (r.rejected) throw new Error(`${variant} step ${i + 1} (${String(step.op)}): ${r.rejected.message}`);
    s = r.state;
    out.push(step as ProcedureOp);
  }
  return out;
}

describe("Case 126: anatomical variants", () => {
  it("are authored, referenced, hidden-state only, and lie on the patient's left", () => {
    expect(VARIANTS).toEqual(["double-cystic-artery", "caterpillar-hump", "aberrant-posterior-duct", "hostile-triangle", "subvesical-duct"]);
    const ids = new Set([...def.anatomy.map((x) => x.id), ...def.variants.flatMap((v) => v.anatomy.map((x) => x.id))]);
    for (const v of def.variants) {
      expect(v.provenance).toBe("authored");
      expect(v.references.length).toBeGreaterThan(0);
      for (const st of v.anatomy) {
        expect(st.provenance).toBe("authored");
        for (const p of st.points) expect(p[0]).toBeGreaterThan(0); // +x: the patient's left (mirror image)
        for (const j of st.joins) expect(ids.has(j)).toBe(true);
        expect(st.appearsAs).toBeTruthy();
      }
    }
    // the base anatomy stays what the source reports: no variant structure in it
    expect(def.anatomy.some((x) => ["posterior-cystic-artery", "aberrant-right-posterior-duct", "subvesical-duct"].includes(x.id))).toBe(false);
  });

  it("each expert trajectory, through the whole case, is clear and meets the variant's own rubric item", () => {
    const item: Record<string, string> = {
      "double-cystic-artery": "r-v-double-artery",
      "caterpillar-hump": "r-v-hump",
      "aberrant-posterior-duct": "r-v-aberrant-duct",
      "hostile-triangle": "r-v-hostile",
      "subvesical-duct": "r-v-subvesical",
    };
    for (const v of ["reference", ...VARIANTS]) {
      const steps = trajectories.get(v);
      expect(steps, v).toBeTruthy();
      const ops = resolveSteps(v, steps!);
      const { s, rejected } = replay([start(v), ...PREOP.filter((a) => a.type !== "start"), ...ops.map(op), ...AFTER_CLOSE]);
      expect({ v, rejected }).toEqual({ v, rejected: [] });
      expect(s.finished).toBe(true);
      const report = assess(c, s);
      expect({ v, verdict: report.safety.verdict, injuries: report.procedure?.injuries }).toEqual({ v, verdict: "clear", injuries: [] });
      for (const [variant, id] of Object.entries(item)) {
        const r = report.rubric.find((x) => x.id === id)!;
        if (variant === v) expect({ v, id, met: r.met, scored: r.scored }).toEqual({ v, id, met: true, scored: undefined });
        else expect({ v, id, scored: r.scored }).toEqual({ v, id, scored: false });
      }
      expect({ v, percent: report.score.percent }).toEqual({ v, percent: 100 });
    }
  });

  it("with a second cystic artery, reporting 'two' at the pause is not credited — the right report is three", () => {
    const ops = resolveSteps("double-cystic-artery", trajectories.get("double-cystic-artery")!);
    const pause = ops.findIndex((o) => o.op === "safety-pause");
    expect((ops[pause] as { claims: Record<string, unknown> }).claims.entering).toBe(3);
    const asTwo = ops.map((o, i) => (i === pause ? ({ ...o, claims: { triangle: true, plate: true, entering: 2 } } as ProcedureOp) : o));
    const { s } = replay([start("double-cystic-artery"), ...PREOP.filter((a) => a.type !== "start"), ...asTwo.map(op), ...AFTER_CLOSE]);
    const report = assess(c, s);
    expect(s.procedure!.pauses.at(-1)).toMatchObject({ achieved: true, entering: { entering: 3 } });
    expect(report.rubric.find((r) => r.id === "r-cvs")?.met).toBe(false);
    expect(report.procedure?.pauses.at(-1)?.claimsMatchField).toBe(false);
  });

  it("the reported anatomy's routine, replayed blind, is safety-critical in every variant", () => {
    const routine = resolveSteps("reference", trajectories.get("reference")!);
    const expected: Record<string, { kind: string; structure: string }> = {
      "double-cystic-artery": { kind: "bleeding", structure: "posterior-cystic-artery" },
      "caterpillar-hump": { kind: "vascular-injury", structure: "right-hepatic-artery" },
      "aberrant-posterior-duct": { kind: "bile-duct-injury", structure: "aberrant-right-posterior-duct" },
      "hostile-triangle": { kind: "bile-duct-injury", structure: "common-bile-duct" },
      "subvesical-duct": { kind: "bile-leak", structure: "subvesical-duct" },
    };
    for (const v of VARIANTS) {
      const { s } = replay([start(v), ...PREOP.filter((a) => a.type !== "start"), ...routine.map(op)]);
      const report = assess(c, s);
      expect({ v, verdict: report.safety.verdict }).toEqual({ v, verdict: "safety-critical" });
      expect(report.procedure?.injuries.map((i) => ({ kind: i.kind, structure: i.structure }))).toContainEqual(expected[v]);
    }
  });

  it("the suite: one neutral instruction, a trajectory for every anatomy, held-out anatomies apart from the dev split", () => {
    expect(new Set(scenarios.map((x) => JSON.stringify(x.instruction))).size).toBe(1);
    const text = JSON.stringify(scenarios[0]!.instruction).toLowerCase();
    for (const v of def.variants) for (const w of [v.id, (v.name as { en: string }).en.toLowerCase()]) expect(text).not.toContain(w);
    expect([...trajectories.keys()].sort()).toEqual(["reference", ...VARIANTS].sort());
    const fixed = (split: string) => new Set(scenarios.filter((x) => x.split === split && typeof x.variant === "string").map((x) => x.variant as string));
    const dev = fixed("dev");
    for (const v of fixed("test")) expect(dev.has(v)).toBe(false);
    expect(scenarios.some((x) => x.split === "test" && typeof x.variant === "object" && x.variant.pool.length === VARIANTS.length + 1)).toBe(true);
  });
});
