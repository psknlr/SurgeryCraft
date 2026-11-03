# cmcr-1654623: upper abdominal pain and fever · 84-year-old man (v4)

| Case card | Value |
|---|---|
| Setting / facility | Operating department, IMPF Surgery Hospital (OR 7) |
| Difficulty / duration | 3/5 / about 45 minutes |
| Specialty / languages | General surgery / zh-CN + en |
| Review | AI-assisted editorial review, 2026-11-03 (2.4.0: the 2.3.0 interaction audit's repairs). **Not clinician-reviewed.** |
| Scope | Whole encounter: presentation, records, diagnosis, perioperative risk, WHO checklist, the operation itself, recovery, then review of the reported course |
| Source | Dataset item 126; published case report, pp. 180–181 (citation below) |

The 3D anatomy is **case-informed reference anatomy, not a reconstruction from the patient's CT**.
Intra-operative vital signs are **simulated** and say so where they appear. See docs/CASE_126.md
for sources, the mapping to the fidelity brief and the validation still owed.

## Learning outcomes

1. Identify laterality from the documented imaging.
2. Keep missing information unknown.
3. Frame the diagnosis within the evidence (Tokyo Guidelines 2018: suspected, not confirmed, acute
   cholecystitis).
4. Identify the perioperative risks of age 84, COPD and a previous stroke without inventing data.
5. Choose ports, stance and traction for mirror-image anatomy.
6. Make irreversible steps only after a true critical view of safety, or choose a safe alternative.
7. Recognise and manage complications.
8. Bound what one case's outcome shows.

These are authoring objectives, not validated competency measures.

## Clinical summary (spoilers)

**Presentation.** An 84-year-old man had upper abdominal pain and fever for more than ten days. He
has COPD and a previous cerebral infarction, and no family history of situs inversus.

**Examination.** Temperature 36.6 °C, pulse 78/min, respiratory rate 19/min, BP 128/78 mmHg. The
apex beat is in the right fifth intercostal space. Upper abdominal tenderness, no rebound, Murphy's
sign negative, bowel sounds 3–4/min.

**Records.**
- Ultrasound: situs inversus and sludge-like stones.
- CT: liver and gallbladder on the patient's left, stomach and spleen on the right, stones, a
  tortuous neck.
- Coronal CT: the left ventricle in the right chest, apex to the right.
- Blood count, biochemistry and coagulation: normal.

**Reported operation (2023-02-06).** Laparoscopic cholecystectomy under general anaesthesia.
- Set-up: supine; surgeon and assistant on the patient's left. Port A 10 mm below the umbilicus;
  ports B (subxiphoid, slightly left) and C (left midclavicular line, 2 cm below the costal margin;
  the main port), both 5 mm.
- Findings: complete mirror image; gallbladder 6 × 4 × 3 cm without adhesions; common bile duct not
  dilated; no vascular variation.
- Technique: antegrade and retrograde dissection, Hem-o-lok clips.
- Specimen: sludge; wall 0.4 cm. 30 minutes, little bleeding.

**Histology and course.** Chronic cholecystitis with gallstones. Flatus on day 2, normal
laboratory tests on day 4, discharge on day 5, well at one month.

## Scenario timeline

| phase | opens when | what happens |
|---|---|---|
| `assessment` | start | history, examination, records; decisions `diagnosis`, `anatomy`, `planning` and `safety` |
| `preop` | objective `plan` | perioperative history; the unrecorded items answer that they are unrecorded: antithrombotics, COPD status, stroke deficits; records not in the source: ECG, lung function, chest X-ray; decision `risk` |
| `theatre` | decision `risk` | attach the monitor (its own task; dextrocardia: mirror ECG leads and defibrillator pads); Sign In, valid only after its checks (monitor on, allergies and fasting asked); induction, contraindicated before the Sign In and refused while an anaesthesia hold stands; Time Out, valid only after a valid Sign In and induction |
| `operation` | the Time Out | the operation (`operate`): ports, pneumoperitoneum, instruments, traction, dissection, identification, safety pause, clips, division, bed dissection, inspection, bag, extraction, closure; or a bail-out; then decision `emergence` (extubation apart from oral intake) |
| `recovery` | the Sign Out | recovery handover; decision `postop` |
| `review` | historical review opened | the report's operation, histology and follow-up; decision `outcome` |

**Physiology.** Baseline from the source (HR 78, BP 128/78, RR 19, T 36.6). SpO₂ 95 % is
**synthetic**. Every value below is **synthetic**:
- Ventilation after induction: EtCO₂ 36.
- The pneumoperitoneum raises EtCO₂ to 40.
- Insufflating at 15 mmHg or more raises EtCO₂ to 48 and drops SpO₂ to 92 %; the anaesthetist asks
  for a lower pressure.
- Major bleeding brings tachycardia and hypotension.
- Closing returns EtCO₂ towards baseline.

No drug doses are modelled.

## The operation

The field is ClinicalCraft's operative-field model (docs/PROCEDURE.md in ClinicalCraft).

**What the operator sees.** Ducts and vessels appear as structures T1, T2…, each described by how it
looks; nothing names them before imaging. With traction towards the patient's left they come into
view in this order: the common bile duct (T1), the cystic duct (T2), the cystic artery (T3), then
deeper structures.

**Exposure.** The triangle opens when the neck is pulled towards the patient's **left** and caudally.
The habitual pull to the right closes it, and makes the common bile duct look as if it runs into the
gallbladder neck.

**Critical view of safety.** It is judged on the field:
- the triangle is cleared;
- the lower third of the gallbladder is off the cystic plate;
- two and only two structures enter the gallbladder.

The safety pause records the operator's claims against what the field shows.

**Port plans.**

| plan | stance | what the port metrics show |
|---|---|---|
| The report's three ports | surgeon on the left | the hands cross, as the report describes |
| Mirrored four ports | surgeon on the right | |
| Habitual right-sided ports | | the shafts fence |

## Decisions and assessment

There are 8 decisions and 33 rubric items (plus one per anatomical variant), weighted by domain (15/10/15/30/15/10/5). Complication
items are scored only when a complication occurs; the percentage is earned divided by possible.
Critical items are laterality, verify-before-dividing and the true critical view. Safety gates cap
the score.

| Path | Score | Verdict |
|---|---|---|
| Reference (`solution`, 80 steps) | 100 % (90/90; complication items not scored) | clear |
| Start and finish only | 0 % (finish refused: objectives open) | — |
| Habitual traction; the common bile duct taken for the cystic duct, clipped and divided, then recognised and converted | 40 % (uncapped 67 %) | safety-critical: bile duct injury, irreversible step without a true view, misidentification |
| The reference without the safety pause | 50 % (uncapped 78 %) | safety-critical: irreversible step without a true view |
| Early subtotal cholecystectomy, nothing clipped | 92 % | clear (anatomy not worked out) |
| Cystic artery divided on one clip, bleed suctioned, recognised and clipped | 97 % | complication |

The rubric checks an authored workflow. It is not a validated score and not GOALS.

## Anatomical variants (counterfactual)

The source found no vascular variation. Five counterfactual anatomies are authored on the reference
geometry for teaching and the operative benchmark:

- `double-cystic-artery`;
- `caterpillar-hump`;
- `aberrant-posterior-duct`;
- `hostile-triangle` (a frozen triangle);
- `subvesical-duct`.

A facilitator can start a session in one of them (`start {variant}`). The learner is not told which:
the field shows only what a surgeon would see. Each variant has its own rubric item, scored only in
that variant.

| variant | expert path | the reported anatomy's routine, replayed blind |
|---|---|---|
| double cystic artery | 100 % | 50 %, safety-critical (no true view; posterior branch torn) |
| caterpillar hump | 100 % | 40 %, safety-critical (right hepatic artery clipped) |
| aberrant posterior duct | 100 % | 40 %, safety-critical (bile duct injury) |
| frozen triangle | 100 % (subtotal) | 40 %, safety-critical (common bile duct torn) |
| subvesical duct | 100 % | 50 %, safety-critical (bile leak, unrecognised) |

**Debrief prompts for a variant:**
- what in the field told you the anatomy was not the textbook's?
- did your safety pause claim what the field showed?
- in the frozen triangle, when did you stop, and why was that the safe choice?

The operative benchmark suite is `content/operative/case126-v1`; see docs/CASE_126.md.

## Facilitator notes

- **Reactions:** where did the mirror image catch you out: the port plan, which hand, which way to
  pull?
- **Description:** which facts did the record give, and which did you have to treat as unknown
  (antithrombotics, COPD control, ASA class)?
- **Analysis:**
  - why is the presentation not a confirmed acute cholecystitis?
  - what did the field show at your safety pause, against what you claimed?
  - when would you stop, image the ducts, call for help, choose a subtotal cholecystectomy or
    convert?
- **Summary:** separate the record, guideline principles, the simulation's assumptions (reference
  anatomy, synthetic physiology) and the single-case outcome.

**Holds and corrections (2.3.0).** The attending and the anaesthetist record a withheld clearance as a hold
(`place_hold`, with the reason) and release it only after a reassessment (`release_hold`); induction is refused
while it stands, whatever anyone claims. Missing information (antithrombotics, COPD control) is a reason to ask
and to document a decision, not a universal prohibition. Both colleagues correct, every time:
- little or no hypnotic before the neuromuscular blocker (the hypnotic goes first, to unconsciousness; never
  paralysis without it);
- end-tidal CO₂ as the measure of preoxygenation (it is end-tidal **oxygen**; capnography confirms the tube);
- a swallow test or VFSS before extubation (extubation and oral intake are two decisions);
- "reversing" left and right because of situs inversus (left and right are the patient's own: the gallbladder is
  on the patient's left).

The nurse corrects a teaching "what if" retold as the family's report: no family member has been interviewed.

**Common errors:**
- pulling the neck to the patient's right;
- clipping before the critical view, or on the strength of a claim;
- dissecting with the hook in a poorly exposed triangle;
- treating unrecorded medicines as none — or a teaching hypothetical as history;
- taking a count or the insufflator for the operation (the operation is done on the field, step by step);
- claiming the attending's approval while a hold stands;
- reading the outcome records first.

## The care team (in-world mode)

During the operation, OR 7's circulating and scrub nurses work on their own (docs/CASE_126.md; ClinicalCraft
docs/TEAM.md):
- an instrument handoff with read-back, verified by sight;
- the closing count swab by swab, once the specimen is out.

To teach with it, start the encounter with a team scenario (`start {team}`):
- the needle holder needed;
- the scrub nurse on a break;
- the needle holder moved or missing;
- the count correct (the control);
- a swab under the Mayo stand, in the wound, or gone from the room.

The learner answers as the surgeon on the **Team** panel, or chooses **Observe** to watch.

**Debrief questions:**
- when the count was short, what did you say back, and did you hold closure until it was reconciled?
- who searched where, and why does the circulating nurse search the same places whatever happened?
- when the swab could not be found, why is an X-ray before the patient leaves the right ending, and what would
  "pretending it is solved" have cost?
- in the handoff, what did the read-back protect against?

## Fidelity limits

- No DICOM: the anatomy is BodyParts3D organ surfaces (mirrored) plus the Layered Human procedural
  hepatobiliary tree (MIT), mirrored once and registered. The fit residual is 13 mm RMS.
- Tissue behaviour is a state model (dissected, exposed, held, clipped, divided, burnt, torn), not
  calibrated mechanics.
- Bleeding and thermal injury are rule-based.
- Physiology is synthetic and uncalibrated.
- No surgical, anaesthetic or radiological review yet.
- The v3 demonstration (`dataset/case-126-v3/`) stays as the historical baseline.

## Matcher notes

38 bilingual utterance fixtures (36 positive, 2 negative). Unrecorded items answer that they are
not recorded. The generator is `tools/case-gen/build_case_1654623.py` (on top of
`case_1654623_base.py`, the v3 base); change those and rebuild, never the JSON.

## References

1. 张少博, 余仁斌. 内脏完全反位腹腔镜胆囊切除术一例. 肝胆胰外科杂志. 2024;36(3):180–181.
2. Yokoe M, Hata J, Takada T, et al. Tokyo Guidelines 2018: diagnostic criteria and severity grading of
   acute cholecystitis (with videos). J Hepatobiliary Pancreat Sci. 2018;25(1):41–54.
3. Brunt LM, Deziel DJ, Telem DA, et al. Safe cholecystectomy multi-society practice guideline and
   state-of-the-art consensus conference on prevention of bile duct injury during cholecystectomy.
   Surg Endosc. 2020;34(7):2827–2855.
4. Strasberg SM, Hertl M, Soper NJ. An analysis of the problem of biliary injury during laparoscopic
   cholecystectomy. J Am Coll Surg. 1995;180(1):101–125.
5. World Health Organization. Implementation manual WHO surgical safety checklist 2009.

## Changelog

- 2026-11-03, 2.4.0 (the 2.3.0 interaction audit; needs ClinicalCraft's repairs 1–5):
  - the swab count is one record by identity (the board, the RF wand, the Sign Out, the team and the score read it);
    closure on an open count is a safety-critical unsafe progression, never erased; new scenarios `swab-extra`,
    `swab-substituted`, `swab-with-specimen` (OR 6 gets its own swab);
  - the Sign In needs the diagnosis, the plan and the risk assessment; the review opens only on a valid request after
    the postoperative discussion and the Sign Out;
  - the patient cannot answer from induction until emergence or recovery (`nonVerbalWhen`);
  - the closing-count skill counts and scans before closure;
  - tests: `tools/case126-count.test.ts`, the board in the patient's room, entry milestones, the review gate, named
    colleagues, read-backs, speech under anaesthesia.
- 2026-11-02, 2.3.0 (the audit of a 2.1.0 save; needs ClinicalCraft's audit round):
  - attaching the monitor is its own task (`attach-monitor`); the Sign In is valid only after its checks; the
    Time Out needs a valid Sign In and induction;
  - explicit anaesthesia holds (who, why, who released them after which reassessment);
  - decision `emergence` (extubation apart from oral intake), rubric `r-emergence`; closure credited from the field
    (`r-closed`); the operation's outcome items scored once it opens;
  - authored corrections on the attending, the anaesthetist and the nurse; patient-relative laterality wording;
    unverified items (`prior-treatment`, `pain-meals`) answer "not recorded";
  - `clock.worldTime: "actual"` (a device's minute is a clinical minute);
  - tests: the theatre regressions (13) and the release acceptance run end to end.
- 2026-10-31, 1.0.0: first bounded bilingual case (the v3 demo's case).
- 2026-11-02, 2.2.0:
  - the care team of OR 7 (`team`): circulating and scrub nurses working on their own, with check-back;
  - the closing count swab by swab (five single swabs on the Mayo tray, `sc-gauze-swab`);
  - eight authored team scenarios, scored by `clinicalcraft bench team`.
- 2026-11-01, 2.1.0: five counterfactual anatomical variants (hidden from the operator), one rubric item each
  (scored only in its variant), the evidence ledger's `counterfactual` list, and the operative benchmark
  suite `content/operative/case126-v1`.
- 2026-11-01, 2.0.0:
  - the operation is performed (procedure model);
  - Tokyo Guidelines diagnostic decision;
  - perioperative risk decision;
  - WHO checklist steps;
  - synthetic physiology;
  - one domain-weighted rubric with safety gates;
  - reference anatomy model v4;
  - evidence ledger v2.

## Validation

```bash
tools/check.sh ../ClinicalCraft
```

It runs `cases validate --strict`, `cases verify`, `verify_anatomy_1654623.py`,
`tools/case126.test.ts`, the theatre, acceptance and team tests (`tools/case126-theatre.test.ts`,
`tools/case126-acceptance.test.ts`, `tools/case126-team.test.ts`), the operative suite (generator up to date; reference and scripted-llm
agents at 100 %) and the team benchmark (every scenario passes).

## 中文摘要

第126例 v4：学员（或智能体）在同一个会话里完成整个诊疗过程。依次是问诊、查体、资料核对、诊断（东京指南：疑似而非确诊的急性胆囊炎）、侧别与计划、围术期风险评估和WHO安全核对，然后在病例相关的参考解剖上亲手完成腹腔镜胆囊切除，最后是恢复室交接和原报告记录的回看。

关键安全视野依据术野判定，不靠勾选。误把胆总管当作胆囊管夹闭或离断属于安全关键失败，分数封顶40%。在不确定时选择求助、胆道影像、胆囊次全切除或中转开腹，都可以得到认可。

2.1.0 新增五种假设性解剖变异：双胆囊动脉、肝右动脉“毛虫驼峰”、迷走右后叶胆管、致密纤维化的“冰冻”三角、胆囊床内的胆囊下胆管。它们对操作者隐藏，只能从术野判断。另有手术基准测试集 `content/operative/case126-v1`，供智能体在解剖未知的情况下操作并评测。

2.2.0 新增7号手术间的手术团队：巡回护士与洗手护士在手术阶段自主协作——器械传递先复述确认、再亲眼核实；取出标本后逐块清点纱布，不符时请术者暂停关闭并检查术野，巡回护士按固定顺序在手术间里查找，然后复点，仍找不到就上报并拍 X 线片。共8个编写的团队情境（含一个全部在位的对照），可用 `clinicalcraft bench team` 评测。

2.3.0 根据一次 2.1.0 存档的审查做了修订：连接监护仪是单独的任务，不再等于完成麻醉前核查；麻醉前核查要在监护、过敏和禁食都落实后才有效，切皮前暂停核查要在有效的麻醉前核查和诱导之后；上级医师或麻醉医生不同意诱导时会记录“暂缓”及理由，只有本人重新评估并记录后才能解除；新增拔管与经口进食分开决定的决策；术中结果（取出标本、关腹）只按术野计分，清点和气腹机不能代替手术；上级医师、麻醉医生和护士会纠正快速顺序诱导、预充氧判断、拔管前吞咽试验、“把左右再反过来”以及把教学假设当成家属陈述等错误。另有一条从问诊到恢复室交接的端到端验收测试。

2.4.0 根据对 2.3.0 的交互审查做了修订：纱布清点成为按纱布身份逐件核对的唯一记录，清点板、RF 检测棒、离室前核查（Sign Out）、团队和评分都读取同一记录；6 块对 5 块、或用 6 号手术间的纱布凑足 5 块都算清点不符；清点未相符时关闭会被记为“不安全推进”，计入复盘且不会被之后的操作抹去；麻醉前核查需要先明确诊断、制定计划并评估风险；原报告回看只能在术后讨论和离室前核查之后有效打开；诱导后到苏醒前患者不能说话，也不计问诊分；只有患者所在手术间的核查板记录本病例。新增 3 个清点情境。

三维解剖不是患者CT重建，术中生命体征为模拟值，本病例尚未经临床专家审核。
