#!/usr/bin/env node
/**
 * Case 126: the three release demonstrations in the browser build (docs/CASE_126.md "2.4.0"), beside the headless
 * regressions (tools/case126-count.test.ts, case126-theatre.test.ts):
 *
 *   1. an unresolved 4/5 count cannot receive a safe full score — the team escalates "four of five", the learner
 *      closes and tries to sign out anyway: closure is recorded as an unsafe progression, the Sign Out is refused,
 *      the verdict is not clear and the score is capped;
 *   2. the OR 1 board cannot sign in the OR 7 patient — refused, pointing at OR 7's board; only OR 7's board shows the
 *      Sign In;
 *   3. a preoperative reload activates the same team obligations as an uninterrupted run (`swab-in-wound`);
 *   4. the first release scenario of 2.5.0 (docs/CASE_126.md "2.5.0"): before induction no historical ECG, a new one
 *      ordered, fetched by the nurse and reviewed by the anaesthetist, shown in the chart as a simulated
 *      investigation; in the operation the scope dock stays visible beside the theatre while another window is open;
 *      the assistant takes the neck grasper, then leaves the table — the dock shows the release (traction gone)
 *      before the operator's next step; saved and reloaded, the dock shows the same field;
 *   5. the follow-up audit: the tower fails with the scope in and nothing queued — the dock says "No picture" at
 *      once (never "Live"), and "Abdomen down" once the tower is back; with the surgery window open the care team's
 *      round goes on, and the pause menu stops it;
 *   6. the round 3 audit: the tower fails and is restored while some 28 older operative frames wait — the dock never
 *      says "Live" (nor draws 12 mmHg) while the record has the abdomen down, frame after frame, until the queue has
 *      drained ("Abdomen down").
 *
 * The page is driven through the app's own session and world (the `?qa` hooks: `__QA__.session`, the world action
 * bus, the save and resume of the web app) and checked against the authoritative state, not pixels; screenshots are
 * kept for the record.
 *
 * Usage:
 *   node tools/browser-demos.mjs [path/to/ClinicalCraft] [--out dir]
 *       builds the web app of that checkout (default ../ClinicalCraft), serves it with this pack in `contentDirs`
 *       (`clinicalcraft serve`) and runs the demonstrations in Chromium;
 *   node tools/browser-demos.mjs --url 'https://…/?token=…'
 *       runs them against a deployed build instead (it must serve this pack).
 * Exit status 0 only when all of them hold (`--only 6` runs the sixth alone). Needs `playwright` (with its Chromium) and, locally, a ClinicalCraft checkout
 * with its dependencies installed.
 */
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const { chromium } = createRequire(import.meta.url)("playwright");
const HERE = dirname(fileURLToPath(import.meta.url));
const PACK = resolve(HERE, "../content");
const CASE = "cmcr-1654623";
const FACILITY = "impf-surgery-hospital";
/** The reference solution (the web's case bundle leaves it out): the record a demonstration sets up as the system. */
const SOLUTION = JSON.parse(readFileSync(join(PACK, "cases", CASE, "case.json"), "utf8")).solution;

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args.splice(i, 2)[1] : undefined;
};
const deployed = flag("--url");
/** Run only these demonstrations (1-based, comma-separated). */
const only = (flag("--only") ?? "").split(",").filter(Boolean).map(Number);
const out = resolve(flag("--out") ?? join(HERE, "..", "browser-demos"));
const CC = resolve(args[0] ?? join(HERE, "../../ClinicalCraft"));
mkdirSync(out, { recursive: true });

/* ------------------------------------------------------------------ */
/* the build, served (unless a deployed one is given)                  */
/* ------------------------------------------------------------------ */

let serve = null;
let root = null;
async function local() {
  root = mkdtempSync(join(tmpdir(), "sc-browser-demos-"));
  const home = join(root, "home");
  mkdirSync(home, { recursive: true });
  writeFileSync(join(home, "settings.json"), JSON.stringify({ contentDirs: [PACK] }));
  const token = `demo-${Date.now().toString(36)}-0123456789abcdef`;
  const tokenFile = join(root, "token");
  writeFileSync(tokenFile, `${token}\n`, { mode: 0o600 });
  const dist = join(root, "dist");
  console.log(`== building the web app of ${CC}`);
  const build = spawnSync("npx", ["vite", "build", "--outDir", dist, "--emptyOutDir", "--logLevel", "warn"], { cwd: join(CC, "packages/web"), encoding: "utf8", timeout: 600_000 });
  if (build.status !== 0) throw new Error(`web build failed\n${build.stdout}\n${build.stderr}`);
  const env = { ...process.env, CLINICALCRAFT_HOME: home, HOME: home, NO_COLOR: "1" };
  for (const k of Object.keys(env)) if (/_API_KEY$/.test(k)) delete env[k];
  serve = spawn(join(CC, "node_modules/.bin/tsx"), ["--conditions=source", join(CC, "packages/cli/src/bin.ts"), "serve", "--port", "0", "--static", dist, "--token-file", tokenFile, "--lang", "en"], { cwd: root, env, stdio: ["ignore", "pipe", "pipe"] });
  let log = "";
  serve.stderr.setEncoding("utf8").on("data", (d) => (log += d));
  const base = await new Promise((ok, fail) => {
    let seen = "";
    const timer = setTimeout(() => fail(new Error(`serve did not start: ${log}`)), 120_000);
    serve.stdout.setEncoding("utf8").on("data", (d) => {
      seen += d;
      const m = /listening on (http:\/\/127\.0\.0\.1:\d+)\//.exec(seen);
      if (m) {
        clearTimeout(timer);
        ok(m[1]);
      }
    });
    serve.on("exit", (code) => fail(new Error(`serve exited ${code}: ${log}`)));
  });
  return `${base}/?token=${token}`;
}

/* ------------------------------------------------------------------ */
/* in the page                                                         */
/* ------------------------------------------------------------------ */

/** A fresh page of the app in `?qa` mode, the case entered in in-world mode (approvals bypassed), with `team` chosen. */
async function enter(browser, entry, team, resume = false, existing = null) {
  const page = existing ?? (await browser.newPage({ viewport: { width: 1280, height: 800 }, locale: "en-US" }));
  if (!existing) {
    // the page's errors, kept for a failure's report
    page.__errors = [];
    page.on("pageerror", (e) => page.__errors.push(String(e?.stack ?? e).slice(0, 600)));
    page.on("console", (m) => m.type() === "error" && page.__errors.push(m.text().slice(0, 600)));
    await page.goto(entry);
    const u = new URL(page.url());
    u.search = "?qa";
    await page.goto(u.toString());
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.reload();
  }
  await page.waitForFunction(() => !!window.__QA__, null, { timeout: 180_000 });
  await page.waitForFunction(() => document.querySelector("#enter") && !document.querySelector("#enter").disabled, null, { timeout: 180_000 });
  await page.evaluate(({ c, f, r, t }) => window.__QA__.start(c, f, r, t), { c: CASE, f: FACILITY, r: resume, t: team ?? "" });
  await page.waitForFunction(() => window.__QA__.game?.entered === true, null, { timeout: 180_000 }).catch(async (e) => {
    await page.screenshot({ path: join(out, "enter-failed.png") }).catch(() => {});
    throw new Error(`${e.message}\npage errors: ${(page.__errors ?? []).join("\n")}`);
  });
  await page.evaluate(() => {
    const qa = window.__QA__;
    qa.app.prefs.update((s) => (s.ui.quality = "low"));
    qa.submit({ type: "configure", patch: { approvalMode: "bypass" } });
  });
  if ((await page.evaluate(() => window.__QA__.embodiment)) !== "embodied") throw new Error("the encounter is not in in-world mode");
  return page;
}

/** Helpers installed in the page (by `evaluate`: the app's CSP allows no inline script): the record up to a step, world acts following their hints, the assessment. */
const HELPERS = `
window.__demo = {
  s: () => window.__QA__.session,
  sol: [],
  upTo(stop) {
    const s = this.s(), sol = this.sol;
    for (const a of sol.slice(1, sol.findIndex(stop))) { const r = s.dispatch({ ...a, by: "system" }); if (r.rejected) throw new Error(a.type + ": " + r.rejected.message); }
  },
  async act(actorId, operation, targetId, goal) {
    const id = "demo-" + Math.random().toString(36).slice(2);
    const request = { actionId: id, actorId, operation, ...(targetId ? { targetId } : {}), ...(goal ? { goal } : {}) };
    // the learner's op moves only the learner's own body; a colleague's is moved by the demo through the world facade
    if (actorId !== "actor:clinician") return this.s().world().execute(request);
    const ev = await this.s().run({ type: "world_action", request });
    return ev.map((e) => e.msg).filter((m) => m.type === "world_action_result").map((m) => m.result).find((r) => r.actionId === id) ?? null;
  },
  async done(actorId, operation, targetId) {
    let r = await this.act(actorId, operation, targetId);
    for (let i = 0; i < 2 && r && r.status === "failed" && r.hint; i++) { await this.act(actorId, "navigate", undefined, r.hint.goal); r = await this.act(actorId, operation, targetId); }
    return r;
  },
  patient() { return this.s().world().find("actor:clinician", { kind: "patient", limit: 1 })[0].id; },
  async toTheCount(surgeon) {
    this.upTo((a) => a.type === "operate" && a.op.op === "close");
    await this.s().run({ type: "team", action: "pause" });
    await this.s().run({ type: "team", action: "surgeon", surgeon });
    await this.act("actor:clinician", "navigate", undefined, { kind: "interact", id: this.patient() });
  },
  said() { return this.s().team().state.messages.map((m) => [m.from, m.kind, m.to].join(" ")); },
  async assess() {
    const ev = await this.s().run({ type: "assess" });
    return ev.map((e) => e.msg).find((m) => m.type === "assessment")?.report ?? null;
  },
};`;

/** The helpers and the case's reference solution, in the page. */
async function install(page) {
  await page.evaluate(HELPERS);
  await page.evaluate((sol) => (window.__demo.sol = sol), SOLUTION);
}

async function demoUnresolved(browser, entry) {
  const page = await enter(browser, entry, "swab-gone");
  await install(page);
  const r = await page.evaluate(async () => {
    const d = window.__demo, s = d.s();
    await d.toTheCount("simulated");
    await s.run({ type: "team", action: "run", rounds: 100 });
    const escalation = s.team().state.messages.find((m) => m.kind === "escalate");
    // the learner closes anyway, then tries to sign out on the board and records the rest of the case
    const closeOk = !(await s.run({ type: "clinical_action", action: { type: "operate", op: { op: "close" } } })).some((e) => e.msg.type === "error");
    const board = await d.done("actor:clinician", "sign_out", "eq:or-7.checklist");
    const sol = d.sol, at = sol.findIndex((a) => a.type === "operate" && a.op.op === "close");
    for (const a of sol.slice(at + 1)) s.dispatch({ ...a, by: "system" });
    const report = await d.assess();
    const w = s.world();
    return {
      escalation: escalation?.text.en ?? null,
      closeAccepted: closeOk,
      boardSignOut: board?.status ?? null,
      signOutValid: s.state.interventions.some((x) => x.interventionId === "sign-out" && x.appropriateness !== "contraindicated"),
      countBoard: w.inspect("actor:clinician", "eq:or-7.count-board")?.state,
      checklist: w.inspect("actor:clinician", "eq:or-7.checklist")?.state,
      unsafe: s.state.count?.unsafe ?? [],
      verdict: report?.safety.verdict,
      score: report?.score,
      gates: report?.safety.gates ?? [],
    };
  });
  await page.evaluate(() => window.__QA__.route("team"));
  await page.waitForTimeout(800);
  await page.screenshot({ path: join(out, "1-unresolved-count.png") });
  await page.close();
  const pass = !!r.escalation && r.unsafe.length === 1 && r.verdict === "safety-critical" && r.score && r.score.percent <= 50 && !r.signOutValid && r.boardSignOut !== "completed";
  return { name: "an unresolved 4/5 count cannot receive a safe full score", pass, ...r };
}

async function demoBoard(browser, entry) {
  const page = await enter(browser, entry, "");
  await install(page);
  const r = await page.evaluate(async () => {
    const d = window.__demo, s = d.s(), w = s.world();
    d.upTo((a) => a.type === "intervene" && a.interventionId === "sign-in");
    const boards = w.entities().filter((e) => e.type === "sc-who-checklist").map((e) => e.id);
    const or1 = boards.find((id) => w.roomOf(id) === "or-1");
    await d.act("actor:clinician", "navigate", undefined, { kind: "interact", id: or1 });
    const atOr1 = await d.act("actor:clinician", "sign_in", or1);
    const recordedAfterOr1 = s.state.interventions.filter((x) => x.interventionId === "sign-in").length;
    const atOr7 = await d.done("actor:clinician", "sign_in", "eq:or-7.checklist");
    const states = Object.fromEntries(boards.map((id) => [id, w.inspect("actor:clinician", id)?.state ?? "pending"]));
    return { or1, atOr1: { status: atOr1?.status, message: atOr1?.message?.split("\n")[0], hint: atOr1?.hint?.goal ?? null }, recordedAfterOr1, atOr7: atOr7?.status, states };
  });
  await page.waitForTimeout(800);
  await page.screenshot({ path: join(out, "2-board-binding.png") });
  await page.close();
  const others = Object.entries(r.states).filter(([id]) => id !== "eq:or-7.checklist");
  const pass = r.atOr1.status === "failed" && /records nothing of this patient/.test(r.atOr1.message ?? "") && r.recordedAfterOr1 === 0 && r.atOr7 === "completed" && r.states["eq:or-7.checklist"] === "signed-in" && others.every(([, st]) => st === "pending");
  return { name: "the OR 1 board cannot sign in the OR 7 patient", pass, ...r };
}

async function demoReload(browser, entry) {
  const run = async (page) =>
    page.evaluate(async () => {
      const d = window.__demo, s = d.s();
      await d.toTheCount("simulated");
      await s.run({ type: "team", action: "run", rounds: 80 });
      const st = s.team().state;
      return { said: d.said(), lifecycle: st.lifecycle, outcome: st.count?.outcome ?? null, holds: st.count?.holds ?? 0, record: s.state.count ? s.state.count.entries.map((e) => e.op) : [] };
    });
  // uninterrupted
  const control = await enter(browser, entry, "swab-in-wound");
  await install(control);
  const uninterrupted = await run(control);
  await control.close();
  // saved in the assessment phase (the scenario pending), the page reloaded, the encounter resumed
  const page = await enter(browser, entry, "swab-in-wound");
  const saved = await page.evaluate(async () => {
    const qa = window.__QA__;
    await qa.session.run({ type: "team", action: "pause" });
    const phase = qa.session.state.phase;
    const lifecycle = qa.session.team()?.state.lifecycle ?? null;
    await qa.save();
    return { phase, lifecycle };
  });
  await page.reload();
  await enter(browser, null, "", true, page);
  await install(page);
  const reloaded = await run(page);
  await page.evaluate(() => window.__QA__.route("team"));
  await page.waitForTimeout(800);
  await page.screenshot({ path: join(out, "3-preoperative-reload.png") });
  await page.close();
  const pass = saved.phase === "assessment" && reloaded.said.length > 0 && JSON.stringify(reloaded.said) === JSON.stringify(uninterrupted.said) && reloaded.outcome === uninterrupted.outcome && reloaded.outcome === "reconciled";
  return { name: "a preoperative reload activates the same team obligations as an uninterrupted run", pass, saved, uninterrupted, reloaded };
}

/** The dock as the learner sees it: shown, not covered by the open window, its step and caption. */
const dockSeen = (page) =>
  page.evaluate(() => {
    const dock = document.querySelector("#scope-dock");
    if (!dock || dock.hidden) return { visible: false };
    const r = dock.getBoundingClientRect();
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + 10);
    return { visible: true, onTop: !!top && dock.contains(top), step: Number(dock.dataset.step), chip: document.querySelector("#scope-chip")?.textContent ?? "", caption: document.querySelector("#scope-caption")?.textContent ?? "", panel: window.__QA__.panel ?? null };
  });

async function demoRelease(browser, entry) {
  const page = await enter(browser, entry, "");
  await install(page);
  // before induction: the chart's two commands, the nurse and the anaesthetist on their own
  const before = await page.evaluate(async () => {
    const d = window.__demo, s = d.s();
    d.tool = async (name, args) => {
      const ev = await s.run({ type: "external_tool_call", callId: "t-" + Math.random().toString(36).slice(2), tool: name, args, allowBypass: true });
      const end = ev.map((e) => e.msg).filter((m) => m.type === "tool_call_end").at(-1);
      return end ? { ok: end.ok, output: end.output } : null;
    };
    d.upTo((a) => a.type === "intervene" && a.interventionId === "induction");
    await d.act("actor:clinician", "navigate", undefined, { kind: "interact", id: d.patient() });
    const retrieved = await d.tool("retrieve_report", { query: "ECG" });
    const ordered = await d.tool("order_study", { query: "ECG", lead_placement: "mirror", request_key: "pre-induction-ecg" });
    await d.tool("wait", { minutes: 10 });
    return { retrieved: retrieved?.output ?? null, ordered: ordered?.output ?? null, ecgRoom: s.world().roomOf("eq:anaes-workroom-ecg"), reviews: s.state.studies?.reviews ?? [] };
  });
  await page.evaluate(() => window.__QA__.route("conversation", { agent: "patient", tab: "tests" }));
  await page.waitForTimeout(800);
  const chart = await page.evaluate(() => document.querySelector("#new-studies")?.textContent ?? "");
  await page.screenshot({ path: join(out, "4a-new-investigation.png") });
  await page.evaluate(() => window.__QA__.closePanel());
  // into the operation: three dissection steps, then the assistant takes the neck grasper
  const held = await page.evaluate(async () => {
    const d = window.__demo, s = d.s(), sol = d.sol;
    const at = sol.findIndex((a) => a.type === "intervene" && a.interventionId === "induction");
    const first = sol.findIndex((a) => a.type === "operate" && a.op.op === "dissect");
    for (const a of sol.slice(at, first)) {
      const r = s.dispatch({ ...a, by: "system" });
      if (r.rejected) throw new Error(a.type + ": " + r.rejected.message);
    }
    for (let i = 0; i < 3; i++) await s.run({ type: "clinical_action", action: { type: "operate", op: { op: "dissect", port: "C", region: "hepatocystic-triangle", energy: false } } });
    const r = await d.tool("delegate_task", { role: "staff:or-7-assistant", task: "hold_traction", params: { port: "B" } });
    return { output: r?.output ?? null, holder: s.state.procedure.ports.find((p) => p.site === "B")?.holder ?? null, steps: s.state.procedure.counters.steps };
  });
  // the learner watches the team's window: the scope stays in view beside it
  await page.evaluate(() => window.__QA__.route("team"));
  await page.waitForFunction((n) => Number(document.querySelector("#scope-dock")?.dataset.step) === n, held.steps, { timeout: 30_000 });
  const withTeam = await dockSeen(page);
  await page.screenshot({ path: join(out, "4b-team-and-scope.png") });
  // the assistant leaves the table: the release (traction gone) is shown before the operator's next step
  const away = await page.evaluate(async () => {
    const d = window.__demo, s = d.s();
    await d.act("staff:or-7-assistant", "navigate", undefined, { kind: "room", id: "l1-control" });
    const ops = s.snapshot().actions.filter((a) => a.type === "operate").slice(-2).map((a) => [a.op.op, a.actor ?? null]);
    return { ops, steps: s.state.procedure.counters.steps, retractions: Object.keys(s.state.procedure.retractions) };
  });
  await page.waitForFunction(() => document.querySelector("#scope-caption [data-op]")?.getAttribute("data-op") === "release", null, { timeout: 30_000 });
  const releaseFrame = await dockSeen(page);
  await page.screenshot({ path: join(out, "4c-traction-released.png") });
  await page.waitForFunction((n) => Number(document.querySelector("#scope-dock")?.dataset.step) === n, away.steps, { timeout: 30_000 });
  // saved, reloaded and resumed: the same field on the dock
  await page.evaluate(() => window.__QA__.closePanel());
  await page.evaluate(() => window.__QA__.save());
  await page.reload();
  await enter(browser, null, "", true, page);
  await page.waitForFunction((n) => Number(document.querySelector("#scope-dock")?.dataset.step) === n, away.steps, { timeout: 60_000 });
  const resumed = await dockSeen(page);
  const after = await page.evaluate(() => ({ steps: window.__QA__.session.state.procedure.counters.steps, holder: window.__QA__.session.state.procedure.ports.find((p) => p.site === "B")?.holder ?? null, ecgRoom: window.__QA__.session.world().roomOf("eq:anaes-workroom-ecg"), reports: window.__QA__.session.state.studies?.reports.length ?? 0 }));
  await page.screenshot({ path: join(out, "4d-resumed.png") });
  await page.close();
  const pass =
    /^Historical material unavailable/.test(before.retrieved ?? "") &&
    /Nurse Aisyah \(circulating\) will fetch the Mobile ECG machine/.test(before.ordered ?? "") &&
    before.ecgRoom === "or-7" &&
    before.reviews.length === 1 &&
    /Simulated investigation · 12-lead ECG/.test(chart) &&
    held.holder === "or-7-assistant" &&
    withTeam.visible && withTeam.onTop && withTeam.panel === "team" &&
    JSON.stringify(away.ops) === JSON.stringify([["release", "or-7-assistant"], ["hand-over", "or-7-assistant"]]) &&
    away.retractions.length === 0 &&
    releaseFrame.visible && /traction has gone/.test(releaseFrame.caption) && /exposure (none|poor|partial)/.test(releaseFrame.caption) &&
    resumed.visible && resumed.step === away.steps && after.steps === away.steps && after.holder === null && after.ecgRoom === "or-7" && after.reports === 1;
  return { name: "the first release scenario: the ECG beyond the published case, the scope beside the theatre, the assistant's traction", pass, before, chart: chart.slice(0, 400), held, withTeam, away, releaseFrame, resumed, after };
}

/** 5. The equipment in view and the team's clock, as the learner operates (the follow-up audit's browser findings). */
async function demoEquipment(browser, entry) {
  const page = await enter(browser, entry, "");
  await install(page);
  const step = await page.evaluate(async () => {
    const d = window.__demo, s = d.s();
    d.upTo((a) => a.type === "operate" && a.op.op === "dissect");
    await d.act("actor:clinician", "navigate", undefined, { kind: "interact", id: d.patient() });
    await s.run({ type: "staff_step" });
    return s.state.procedure.counters.steps;
  });
  await page.evaluate(() => window.__QA__.route("team"));
  const chip = () => page.evaluate(() => ({ state: document.querySelector("#scope-chip")?.dataset.state, text: document.querySelector("#scope-chip")?.textContent, pending: window.__QA__.app.playback.pending() }));
  await page.waitForFunction((n) => document.querySelector("#scope-chip")?.dataset.state === "live" && Number(document.querySelector("#scope-dock").dataset.step) === n, step, { timeout: 45_000 });
  const live = await chip();
  // the tower fails, nothing queued: the next render says so
  const engine = await page.evaluate(async () => {
    const s = window.__QA__.session;
    s.world().setAvailability("eq:or-7.lap-tower", false);
    await s.run({ type: "staff_step" });
    return { ...s.state.procedure.supply, pressure: s.state.procedure.pressure };
  });
  await page.waitForFunction(() => document.querySelector("#scope-chip")?.dataset.state === "no-image", null, { timeout: 15_000 }).catch(() => {});
  const failedTower = await chip();
  await page.screenshot({ path: join(out, "5-no-picture.png") });
  // back in service: the picture, the abdomen down until insufflated again
  await page.evaluate(async () => {
    const s = window.__QA__.session;
    s.world().setAvailability("eq:or-7.lap-tower", true);
    await s.run({ type: "staff_step" });
  });
  await page.waitForFunction(() => document.querySelector("#scope-chip")?.dataset.state === "deflated", null, { timeout: 15_000 }).catch(() => {});
  const back = await chip();
  // the surgery window open: the team's round goes on; paused: it does not
  const round = () => page.evaluate(() => window.__QA__.session.team()?.state.round ?? -1);
  await page.evaluate(() => window.__QA__.route("surgery"));
  const r0 = await round();
  await page.waitForFunction((r) => (window.__QA__.session.team()?.state.round ?? -1) > r, r0, { timeout: 20_000 }).catch(() => {});
  const r1 = await round();
  await page.screenshot({ path: join(out, "5-surgery-window.png") });
  await page.evaluate(() => window.__QA__.route("pause"));
  await page.waitForTimeout(500);
  const p0 = await round();
  await page.waitForTimeout(6_000);
  const p1 = await round();
  await page.close();
  const pass = live.state === "live" && !engine.image && !engine.gas && engine.pressure === 0 && failedTower.state === "no-image" && failedTower.text === "No picture" && failedTower.pending === 0 && back.state === "deflated" && r1 > r0 && p1 === p0;
  return { name: "the equipment in view and the team's clock while the learner operates", pass, live, engine, failedTower, back, team: { surgeryOpen: [r0, r1], paused: [p0, p1] } };
}

/** 6. Equipment recovery with older frames queued (the round 3 audit's browser finding). */
async function demoQueued(browser, entry) {
  const page = await enter(browser, entry, "");
  await install(page);
  const step = await page.evaluate(async () => {
    const d = window.__demo, s = d.s();
    d.upTo((a) => a.type === "operate" && a.op.op === "dissect");
    await d.act("actor:clinician", "navigate", undefined, { kind: "interact", id: d.patient() });
    await s.run({ type: "staff_step" });
    return s.state.procedure.counters.steps;
  });
  await page.evaluate(() => window.__QA__.route("team"));
  await page.waitForFunction((n) => document.querySelector("#scope-chip")?.dataset.state === "live" && Number(document.querySelector("#scope-dock").dataset.step) === n && window.__QA__.app.playback.pending() === 0, step, { timeout: 60_000 });
  // a backlog: accepted inspections, each a frame of its own, faster than they can be shown
  await page.evaluate(() => {
    const s = window.__QA__.session;
    for (let i = 0; i < 28; i++) {
      const r = s.dispatch({ type: "operate", op: { op: "inspect" }, by: "system" });
      if (r.rejected) throw new Error(r.rejected.message);
    }
  });
  await page.waitForFunction(() => window.__QA__.app.playback.pending() > 5, null, { timeout: 20_000 });
  const look = () =>
    page.evaluate(() => {
      const q = window.__QA__, p = q.session.state.procedure, f = q.app.playback.frame().state;
      return { chip: document.querySelector("#scope-chip")?.dataset.state, queue: q.app.playback.pending(), pressure: p.pressure, insufflated: p.insufflated, framePressure: f.pressure, frameInsufflated: f.insufflated };
    });
  const queued = await look();
  const tower = (available) =>
    page.evaluate(async (on) => {
      const s = window.__QA__.session;
      s.world().setAvailability("eq:or-7.lap-tower", on);
      await s.run({ type: "staff_step" });
    }, available);
  await tower(false);
  await page.waitForFunction(() => document.querySelector("#scope-chip")?.dataset.state === "no-image", null, { timeout: 15_000 }).catch(() => {});
  const failedTower = await look();
  await tower(true);
  await page.waitForFunction(() => window.__QA__.session.state.procedure.supply?.image !== false && document.querySelector("#scope-chip")?.dataset.state !== "no-image", null, { timeout: 15_000 }).catch(() => {});
  // frame after frame while the backlog drains: never live, never a pressure the record does not have
  const samples = [];
  for (let i = 0; i < 120; i++) {
    const x = await look();
    samples.push(x);
    if (x.queue === 0 && x.chip === "deflated") break;
    await page.waitForTimeout(250);
  }
  await page.screenshot({ path: join(out, "6-queued-recovery.png") });
  await page.close();
  const restored = samples[0];
  const lies = samples.filter((x) => !x.insufflated && (x.chip === "live" || x.framePressure !== 0 || x.frameInsufflated));
  const drained = samples.at(-1);
  const pass = queued.queue > 5 && failedTower.chip === "no-image" && restored.queue > 0 && lies.length === 0 && drained.queue === 0 && drained.chip === "deflated";
  return { name: "equipment recovery with older frames queued never shows a pneumoperitoneum the record does not have", pass, queued, failedTower, restored, drained, samples: samples.length, lies: lies.slice(0, 3) };
}

/* ------------------------------------------------------------------ */

let failed = false;
let browser = null;
try {
  const entry = deployed ?? (await local());
  browser = await chromium.launch();
  const results = [];
  const demos = [demoUnresolved, demoBoard, demoReload, demoRelease, demoEquipment, demoQueued].filter((_, i) => !only.length || only.includes(i + 1));
  for (const demo of demos) {
    try {
      results.push(await demo(browser, entry));
    } catch (e) {
      results.push({ name: demo.name, pass: false, error: e instanceof Error ? e.stack : String(e) });
    }
    const r = results.at(-1);
    console.log(`${r.pass ? "PASS" : "FAIL"}  ${r.name}`);
    if (!r.pass) failed = true;
  }
  writeFileSync(join(out, "browser-demos.json"), JSON.stringify({ build: deployed ? "deployed" : `local build of ${CC}`, at: new Date().toISOString(), results }, null, 2));
  console.log(`results: ${join(out, "browser-demos.json")} (screenshots beside it)`);
} catch (e) {
  failed = true;
  console.error(e);
} finally {
  await browser?.close();
  if (serve && serve.exitCode === null) serve.kill("SIGINT");
  if (root) rmSync(root, { recursive: true, force: true });
}
process.exit(failed ? 1 : 0);
