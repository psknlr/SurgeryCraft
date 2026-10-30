/**
 * SurgeryCraft surgical centre: navigation and zoning on the compiled facility, run with ClinicalCraft's own
 * world model. `tools/check.sh` copies this file into `<ClinicalCraft>/packages/world/src/` for the run and
 * removes it afterwards (ClinicalCraft's vitest only includes `packages/*\/src/**`).
 *
 * The pack directory comes from $SURGERYCRAFT_CONTENT.
 */
import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { compileFacility, parseCase, parseCatalog, parseFacility, parseRoomTemplate, type FacilityDefinition, type RoomTemplate } from "@clinicalcraft/core";
import { buildCollisionModel } from "./collision.js";
import type { NavGoal, NavPlan, Pose } from "./contracts.js";
import { GridAStarBackend } from "./nav/backend.js";
import { buildRegistry } from "./registry.js";

const CC = new URL("../../content/", import.meta.url).pathname;
const SC = `${process.env.SURGERYCRAFT_CONTENT ?? ""}/`;
const json = (p: string) => JSON.parse(readFileSync(p, "utf8"));
const catalogs = [
  ...["materials", "core-clinical", "core-diagnostics", "core-furniture"].map((id) => `${CC}catalogs/${id}.json`),
  `${SC}catalogs/surgerycraft-or.json`,
].map((f) => {
  const r = parseCatalog(json(f));
  if (!r.ok) throw new Error(f);
  return r.value;
});
const templates: RoomTemplate[] = [CC, SC].flatMap((dir) =>
  readdirSync(`${dir}templates`)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const r = parseRoomTemplate(json(`${dir}templates/${f}`));
      if (!r.ok) throw new Error(f);
      return r.value;
    }),
);
const parsed = parseFacility(json(`${SC}facilities/surgical-centre.json`));
if (!parsed.ok) throw new Error(JSON.stringify(parsed.issues));
const compiled = compileFacility(parsed.value, templates);
if (!compiled.ok) throw new Error(JSON.stringify(compiled.issues));
const F: FacilityDefinition = compiled.facility;
// the operating-room case of the built-in library (term pregnancy for caesarean section)
const cr = parseCase(json(`${CC}cases/cmcr-1653406/case.json`));
if (!cr.ok) throw new Error("case");
const caseDef = cr.value;

const world = (slotId = F.patientSlots[0].id) => {
  const collision = buildCollisionModel(F, catalogs, { patients: [{ slotId, posture: "lying" }] });
  const registry = buildRegistry(F, catalogs, { caseDef, slotId, locale: "en" }, collision);
  const backend = new GridAStarBackend({ facility: F, collision, registry, locale: "en" });
  const spawn: Pose = { x: F.spawn.x, y: 0, z: F.spawn.z, yaw: 0, pitch: 0, level: "L0" };
  const plan = (goal: NavGoal, opts: { from?: Pose; role?: Parameters<typeof backend.plan>[0]["role"]; accessibleOnly?: boolean } = {}) =>
    backend.plan({ actorId: "actor:clinician", from: opts.from ?? spawn, goal, role: opts.role ?? "clinician", ...(opts.accessibleOnly ? { accessibleOnly: true } : {}) });
  return { registry, plan };
};
const ok = (p: NavPlan) => {
  if (!p.ok) throw new Error(`${p.code}: ${p.message} ${JSON.stringify(p.details ?? {})}`);
  return p;
};
const vias = (p: Extract<NavPlan, { ok: true }>) => p.path.filter((x) => x.via).map((x) => x.via);
const w = world();

describe("SurgeryCraft surgical centre", () => {
  it("an operating-room case starts in OR 7 (emergency & obstetric), one storey up", () => {
    expect(F.patientSlots[0].id).toBe("or-7.slot");
    const p = ok(w.plan({ kind: "interact", id: "patient" }));
    expect(p.target.level).toBe("L1");
    expect(vias(p)).toHaveLength(1);
  });

  it("a bed (accessible route) takes a bed lift, never the stairs", () => {
    const p = ok(w.plan({ kind: "interact", id: "patient" }, { accessibleOnly: true }));
    expect(vias(p).length).toBeGreaterThan(0);
    expect(vias(p).every((v) => String(v).startsWith("connector:bed-lift"))).toBe(true);
  });

  it("every interactive placement is reachable by a clinician from the spawn", () => {
    const fails = w.registry
      .ofKind("equipment")
      .filter((e) => e.interaction !== "none")
      .filter((e) => !w.plan({ kind: "interact", id: e.id }).ok)
      .map((e) => e.id);
    expect(fails).toEqual([]);
  });

  it("every patient slot (8 ORs, 8 PACU bays, 5 pre-op bays) is reachable", () => {
    expect(F.patientSlots).toHaveLength(21);
    const fails = F.patientSlots.filter((s) => !world(s.id).plan({ kind: "interact", id: "patient" }).ok).map((s) => s.id);
    expect(fails).toEqual([]);
  });

  it("zoning: porters stay out of the sterile core, non-clinical roles out of the ORs, radiology only in the hybrid OR", () => {
    expect(w.plan({ kind: "interact", id: "eq:l1-iuss" }, { role: "porter" })).toMatchObject({ ok: false, code: "ACCESS_DENIED" });
    expect(w.plan({ kind: "interact", id: "eq:or-3.anaesthesia" }, { role: "receptionist" })).toMatchObject({ ok: false, code: "ACCESS_DENIED" });
    expect(w.plan({ kind: "interact", id: "eq:or-3.anaesthesia" }, { role: "lab-tech" })).toMatchObject({ ok: false, code: "ACCESS_DENIED" });
    ok(w.plan({ kind: "interact", id: "eq:or-1.c-arm" }, { role: "radiologist" }));
    expect(w.plan({ kind: "interact", id: "eq:or-3.anaesthesia" }, { role: "radiologist" })).toMatchObject({ ok: false, code: "ACCESS_DENIED" });
    ok(w.plan({ kind: "interact", id: "eq:l0-reception-records" }, { role: "receptionist" }));
  });
});
