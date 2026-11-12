/**
 * Where the body of a training station is, for the model that has to fit it.
 *
 * The thoracoscopy station's body is not part of its model: the world draws it with its own figure kit (the type's
 * `manikin`, ClinicalCraft docs/FACILITIES.md), the same figures as the people of the world. The model — table,
 * mattress, supports, and what each step of the operation puts on the chest: marks, ports, scope, drain,
 * dressings — is built in Blender round that body, so it needs to know where the body's surface and joints are.
 * This tool asks the pinned ClinicalCraft's own code and writes what it says, in the type's frame (metres; x
 * right, y up, z front; origin at the footprint centre on the floor), to tools/blender/fit/<type>.json, which
 * tools/blender/thoracic_models.py reads.
 *
 * The station's look follows its state (a state's `look`): the body is covered differently and breathes
 * differently from step to step, but it is one body in one position — measured here as it is draped — and a
 * look that turned or bent it would leave the model fitted to another body: that is refused.
 *
 *   cd <ClinicalCraft checkout> && npx tsx --conditions=source <pack>/tools/figure-fit.mts <pack> [--check]
 *
 * `--check` writes nothing and fails when the file on disk is not what the engine says now (tools/check.sh runs
 * it: a figure that changes shape upstream must not leave the model fitted to the old one).
 */
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

type V3 = readonly [number, number, number];
interface Vec { x: number; y: number; z: number; clone(): Vec; sub(v: Vec): Vec; cross(v: Vec): Vec; normalize(): Vec; dot(v: Vec): number; multiplyScalar(k: number): Vec; add(v: Vec): Vec }

const engine = process.cwd();
const pack = path.resolve(process.argv[2] ?? "");
const check = process.argv.includes("--check");
if (!process.argv[2] || !fs.existsSync(path.join(pack, "content/catalogs/surgerycraft-or.json")) || !fs.existsSync(path.join(engine, "packages/web/src/world/manikin.ts"))) {
  console.error("usage: (in a ClinicalCraft checkout) npx tsx --conditions=source <pack>/tools/figure-fit.mts <pack> [--check]");
  process.exit(2);
}
const from = (rel: string) => import(pathToFileURL(path.join(engine, rel)).href);
const { buildManikin, placedPoint, placedHeadPoint } = await from("packages/web/src/world/manikin.ts");
const { trunkPoint, limbPoint } = await from("packages/web/src/world/figure/body.ts");
const { LATERAL } = await from("packages/web/src/world/figure/anatomy.ts");
const { CHEST_FIELD } = await from("packages/web/src/world/figure/dress.ts");
const { HEAD_CENTRE, MOUTH_Y } = await from("packages/web/src/world/figure/skull.ts");
const { EquipmentManikinSchema } = await from("packages/core/src/schema/facility.ts");
const { drawnManikin } = await from("packages/core/src/engine/looks.ts");

/**
 * The sites on the chest wall of the standardized three-port anterior approach (docs/THORACOSCOPY.md), by height
 * on a standing adult of the kit's measurements (m) and by how far round the chest from the mid-axillary line
 * (radians; + towards the front): the utility incision in the 4th intercostal space just in front of latissimus
 * dorsi; the camera port low and anterior, at about the level of the top of the diaphragm; the third port at the
 * camera port's level further back, straight down from the scapula.
 */
const SITES = { utility: [1.288, 0.44], camera: [1.168, 0.62], posterior: [1.168, -0.6] } as const;
/** The anterior, mid- and posterior axillary lines (the angle of each), drawn on the skin inside the field. */
const LINES = { anterior: 0.5, mid: 0, posterior: -0.5 } as const;

const r4 = (n: number) => Math.round(n * 1e4) / 1e4;
const arr = (v: Vec): number[] => [r4(v.x), r4(v.y), r4(v.z)];

/** What a state's look may change of the body without moving it. */
const CLOTH_ONLY = new Set(["cover", "breathing", "asleep"]);

const catalog = JSON.parse(fs.readFileSync(path.join(pack, "content/catalogs/surgerycraft-or.json"), "utf8")) as {
  equipment: { id: string; manikin?: unknown; behavior?: { states?: Record<string, { look?: { manikin?: Record<string, unknown> } }> } }[];
};
let stale = 0;
for (const type of catalog.equipment) {
  if (!type.manikin) continue;
  const m = EquipmentManikinSchema.parse(type.manikin);
  if (m.posture !== "lateral") throw new Error(`${type.id}: this tool fits a body on its side`);
  for (const [state, st] of Object.entries(type.behavior?.states ?? {})) {
    const moved = Object.keys(st.look?.manikin ?? {}).filter((k) => !CLOTH_ONLY.has(k));
    if (moved.length) throw new Error(`${type.id}: state "${state}" changes the manikin's ${moved.join(", ")} — the model is built round one body in one position`);
  }
  // the body as it is operated on: under the drapes (their sheet is measured too); the cloth changes with the state, the body does not
  const rig = buildManikin({ ...drawnManikin(m), cover: "drapes" }, { x: 0, y: 0, z: 0, rot: 0 }, type.id);
  const up = m.sideUp === "right" ? -1 : 1;
  const at = (p: V3): Vec => placedPoint(rig, p);
  const frame = rig.frame;

  /** A point of the bare trunk: height `y`, `d` radians round from the middle of the side that is up (+ to the front), `proud` out of the skin. */
  const skin = (y: number, d: number, proud = 0): Vec => at(trunkPoint(y, up * (Math.PI / 2 - d), frame, 0, undefined, proud));
  /** The frame of a site on the skin: where it is, the way out of the skin, the way up the body (towards the head) and the way round it (towards the front). */
  const site = (y: number, d: number) => {
    const p = skin(y, d);
    const along = skin(y + 0.01, d).sub(skin(y - 0.01, d)).normalize();
    const round = skin(y, d + 0.04).sub(skin(y, d - 0.04)).normalize();
    const n = skin(y, d, 0.02).sub(p).normalize();
    return { p: arr(p), n: arr(n), along: arr(along), round: arr(round) };
  };

  const apart = (a: Vec, b: Vec): number => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
  /**
   * The skin either way round the chest from a site, a frame every `step` metres of it: `back` frames towards the
   * back, the site itself, `front` frames towards the front — what lies along the skin (an incision's mark, a
   * dressing, a drain on its way down) is laid from these.
   */
  const strip = (y: number, d: number, back: number, front: number, step = 0.01) => {
    const walk = (dir: 1 | -1, count: number) => {
      const out: ReturnType<typeof site>[] = [];
      let a = d, gone = 0, last = skin(y, d);
      while (out.length < count) {
        a += dir * 0.001;
        const p = skin(y, a);
        gone += apart(p, last);
        last = p;
        if (gone >= (out.length + 1) * step) out.push(site(y, a));
      }
      return out;
    };
    return [...walk(-1, back).reverse(), site(y, d), ...walk(1, front)];
  };

  /** A limb's joints (the right side's are the mirror of what the skeleton holds). */
  const limb = (l: unknown, right: boolean) => {
    const pt = (t: number): Vec => {
      const q = limbPoint(l, t);
      return at([right ? -q.x : q.x, q.y, q.z]);
    };
    return { root: arr(pt(0)), mid: arr(pt(1)), end: arr(pt(2)), threeQuarters: arr(pt(1.5)) };
  };
  const upperIndex = up === 1 ? 0 : 1, lowerIndex = 1 - upperIndex;
  const arms = { upper: limb(rig.skeleton.arms[upperIndex], upperIndex === 1), lower: limb(rig.skeleton.arms[lowerIndex], lowerIndex === 1) };
  const hand = (l: { along: V3; end: V3 }, right: boolean): number[] => {
    const s = right ? -1 : 1;
    const a = l.along, n = Math.hypot(a[0], a[1], a[2]);
    return arr(at([s * (l.end[0] + (a[0] / n) * 0.09), l.end[1] + (a[1] / n) * 0.09, l.end[2] + (a[2] / n) * 0.09]));
  };

  // the head: its centre, the side it lies on, its crown (the end of the body), and the mouth (the foremost point of the lips' line)
  const head = (p: V3): Vec => placedHeadPoint(rig, p);
  const position = rig.face.geometry.getAttribute("position");
  let lips = 0;
  for (let i = 0; i < position.count; i++) {
    if (Math.abs(position.getX(i)) < 0.012 && Math.abs(position.getY(i) - (HEAD_CENTRE[1] + MOUTH_Y)) < 0.006) lips = Math.max(lips, position.getZ(i));
  }
  const mouth = head([0, HEAD_CENTRE[1] + MOUTH_Y, lips]);
  const mouthOut = head([0, HEAD_CENTRE[1] + MOUTH_Y, lips + 0.05]).sub(mouth).normalize();
  const crown = head([0, HEAD_CENTRE[1] + 0.125, HEAD_CENTRE[2]]);
  const headCentre = head(HEAD_CENTRE);
  const headUnder = head([-up * 0.0745, HEAD_CENTRE[1], HEAD_CENTRE[2]]);

  const lines: Record<string, number[][]> = {};
  for (const [name, d] of Object.entries(LINES)) {
    lines[name] = [];
    for (let y = CHEST_FIELD.low + 0.012; y <= CHEST_FIELD.high - 0.012 + 1e-9; y += 0.0165) lines[name]!.push(arr(skin(y, d, 0.0012)));
  }
  // the cloth over the hips and the legs (the drapes' sheet): how high it lies along the foot half of the table —
  // what stands over the legs (an instrument tray) has to clear it
  rig.root.updateMatrixWorld(true);
  const cloth = { hips: -Infinity, legs: -Infinity };
  rig.root.traverse((o: { isMesh?: boolean; userData: { figure?: boolean }; geometry: { getAttribute(name: string): { count: number; getX(i: number): number; getY(i: number): number; getZ(i: number): number } }; matrixWorld: { elements: number[] } }) => {
    if (!o.isMesh || !o.userData.figure) return;
    const pos = o.geometry.getAttribute("position"), e = o.matrixWorld.elements;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
      const wx = e[0]! * x + e[4]! * y + e[8]! * z + e[12]!, wy = e[1]! * x + e[5]! * y + e[9]! * z + e[13]!;
      const s = wx - m.x; // along the table from the break (towards the feet: positive)
      if (s > 0.12 && s <= 0.4) cloth.hips = Math.max(cloth.hips, wy);
      else if (s > 0.4 && s <= 1.0) cloth.legs = Math.max(cloth.legs, wy);
    }
  });
  const fit = {
    type: type.id,
    note: "written by tools/figure-fit.mts from the pinned ClinicalCraft's figure kit; do not edit by hand",
    manikin: type.manikin,
    table: {
      break: [r4(m.x), r4(m.y), r4(m.z)],
      flex: m.flex,
      half: LATERAL.tableHalf,
      // how far along its half of the table each end of the body is from the break
      crown: r4(Math.hypot(crown.x - m.x, crown.y - m.y)),
      foot: r4(LATERAL.break - LATERAL.foot),
    },
    field: { low: arr(skin(CHEST_FIELD.low, 0)), high: arr(skin(CHEST_FIELD.high, 0)) },
    // each site's frame, and the skin 5 cm either way round the chest from it (11 frames a centimetre apart: `strip[5]` is the site)
    sites: Object.fromEntries(Object.entries(SITES).map(([name, [y, d]]) => [name, { ...site(y, d), strip: strip(y, d, 5, 5) }])),
    // the way of a chest drain from the camera port's site round the front of the chest: a frame every 1.5 cm
    drain: strip(SITES.camera[0], SITES.camera[1], 0, 9, 0.015),
    lines,
    cloth: { hips: r4(cloth.hips), legs: r4(cloth.legs) },
    trunk: {
      // the body's own middle line at the break, the shoulder and the hip that lie on the mattress, the back and the front where bolsters go
      axis: arr(at([0, LATERAL.break, 0])),
      shoulderUnder: arr(at([-up * (0.172 * frame.wide * frame.shoulders + 0.047 * frame.limb), 1.386, 0])),
      hipUnder: arr(skin(0.905, Math.PI)),
      chestUnder: arr(skin(1.3, Math.PI)),
      back: { loin: arr(at(trunkPoint(1.0, Math.PI, frame, 0))), blade: arr(at(trunkPoint(1.31, Math.PI, frame, 0))) },
      front: { belly: arr(at(trunkPoint(0.98, 0, frame, 0))), breast: arr(at(trunkPoint(1.3, 0, frame, 0))) },
    },
    arms: { upper: { ...arms.upper, hand: hand(rig.skeleton.arms[upperIndex], upperIndex === 1) }, lower: { ...arms.lower, hand: hand(rig.skeleton.arms[lowerIndex], lowerIndex === 1) } },
    head: { centre: arr(headCentre), under: arr(headUnder), crown: arr(crown), mouth: arr(mouth), mouthOut: arr(mouthOut) },
  };
  // (a list of numbers on one line: the file is read by people too)
  const text = JSON.stringify(fit, null, 1).replace(/\[\n\s+(-?[\d.e+-]+(?:,\n\s+-?[\d.e+-]+)*)\n\s+\]/g, (_all, inner: string) => `[${inner.replace(/,\n\s+/g, ", ")}]`) + "\n";
  const file = path.join(pack, "tools/blender/fit", `${type.id}.json`);
  if (check) {
    const now = fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
    if (now !== text) {
      console.error(`${path.relative(pack, file)} is not what this ClinicalCraft's figure kit says: run tools/figure-fit.mts and rebuild the model (tools/blender/build.py ${type.id})`);
      stale++;
    } else console.log(`ok  ${path.relative(pack, file)}`);
  } else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, text);
    console.log(`wrote ${path.relative(pack, file)}`);
  }
}
process.exit(stale ? 1 : 0);
