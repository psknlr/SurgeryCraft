"""Case 126 (cmcr-1654623), v3 authored base: the source-bounded history, examination, records, decisions
and reference path of the first SurgeryCraft case (2026-10-31), unchanged except that it no longer writes
files. `build_case_1654623.py` builds v4 on top of it. Importing this module builds `case` (a dict).
No model/API calls, PDF redistribution, or unrecorded clinical defaults.
"""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
CASE_ID = 'cmcr-1654623'
DEST = ROOT / 'content' / 'cases' / CASE_ID
L = lambda zh, en: {'zh-CN': zh, 'en': en}
ALL = lambda *items: {'all': list(items)}
SOURCE = L('原报告第180页“病例”；以原文记载为限。', 'Source report p. 180, Case; limited to recorded information.')
UNKNOWN = L('原报告没有记录，不能据此认定正常或不存在。', 'Not recorded in the source; this does not establish normality or absence.')


def history(id, topic, zh, en, azh, aen, required=False, unknown=False):
    return dict(id=id, topic=topic, question=L(zh, en), answer=L(azh, aen),
                keywords={'zh-CN': [zh.rstrip('？')], 'en': [en.rstrip('?')]},
                disclosure='unknown' if unknown else ('volunteer' if id == 'presentation' else 'on-ask'),
                required=required, source=UNKNOWN if unknown else SOURCE)


def exam(id, system, zh, en, fzh, fen, abnormal=False, required=False):
    return dict(id=id, system=system, maneuver=L(zh, en), finding=L(fzh, fen),
                keywords={'zh-CN': [zh], 'en': [en]}, requires=[],
                abnormal=abnormal, required=required, source=SOURCE, phases=['assessment'])


def record(id, zh, en, rzh, ren, phase='assessment', essential=False, source=SOURCE):
    return dict(id=id, name=L(zh, en), category='record',
                aliases={'zh-CN': [zh], 'en': [en]}, requires=['records'],
                performedAt='records', risk='none', value='essential' if essential else 'useful',
                results={phase: dict(text=L(rzh, ren), source=source)})


def option(id, zh, en, correct, fzh, fen):
    return dict(id=id, text=L(zh, en), correct=correct, feedback=L(fzh, fen))


def decision(id, zh, en, requires, needzh, needen, options):
    return dict(id=id, prompt=L(zh, en), kind='single', requires=requires,
                need=L(needzh, needen), options=options)


def rubric(id, domain, weight, zh, en, condition, critical=False):
    return dict(id=id, domain=domain, weight=weight, text=L(zh, en), met=condition,
                **({'critical': True} if critical else {}))


def objective(id, zh, en, hzh, hen, condition, target='patient'):
    return dict(id=id, title=L(zh, en), hint=L(hzh, hen), guidance=L(hzh, hen),
                completeWhen=condition, waypoints=[dict(target=target)])


hx = [
    history('presentation', 'presenting-complaint', '哪里不舒服，持续多久了？', 'What brought you in and for how long?',
            '上腹痛、发热十多天了。', 'Upper abdominal pain and fever for more than ten days.', True),
    history('pmh', 'pmh', '以前诊断过哪些疾病？', 'What medical conditions have you had?',
            '病历记载有慢阻肺和脑梗死病史，具体时间没有记录。', 'The record lists COPD and a previous cerebral infarction; dates are not recorded.', True),
    history('family', 'family', '家族里有相似的先天情况吗？', 'Any similar congenital condition in the family?',
            '原报告未发现相关家族史，其他家族病史没有记录。', 'No related family history was found in the report; other family history is not recorded.'),
]
for id, topic, zh, en in [
    ('allergies', 'allergies', '有没有药物过敏？', 'Do you have any drug allergies?'),
    ('medications', 'medications', '平时服用哪些药？', 'Which medicines do you take?'),
    ('psh', 'psh', '以前做过哪些手术？', 'What operations have you had?'),
    ('fasting', 'other', '最后一次进食是什么时候？', 'When did you last eat?'),
    ('weight', 'other', '目前体重是多少？', 'What is your current weight?'),
    ('smoking', 'social', '现在或以前吸烟吗？', 'Do you smoke or have you smoked?'),
    ('alcohol', 'social', '平时饮酒吗？', 'Do you drink alcohol?'),
    ('pain-score', 'pain', '疼痛从零到十分是几分？', 'What is your pain score out of ten?'),
    ('vomiting', 'associated-symptoms', '有恶心或呕吐吗？', 'Have you had nausea or vomiting?'),
    ('jaundice', 'associated-symptoms', '眼睛或皮肤变黄了吗？', 'Have your eyes or skin turned yellow?'),
    ('functional', 'functional', '平时活动和生活自理情况怎样？', 'How is your usual mobility and independence?'),
    ('expectations', 'ice', '您最希望我们帮助什么？', 'What are you hoping we can help with?'),
]:
    hx.append(history(id, topic, zh, en, '原报告没有记录这项信息，需要另行核实。',
                      'This information is not recorded and needs separate verification.',
                      required=id == 'allergies', unknown=True))

exams = [
    exam('entry-vitals', 'vitals', '查看入院生命体征记录', 'Review admission vital signs',
         '体温36.6 ℃，脉搏78次/min，呼吸19次/min，血压128/78 mmHg。',
         'Temperature 36.6 °C, pulse 78/min, respiratory rate 19/min, BP 128/78 mmHg.', required=True),
    exam('apex', 'cardiovascular', '检查心尖搏动位置', 'Locate the apex beat',
         '心尖搏动位于右侧第5肋间隙，心率78次/min。', 'Apex beat in the right fifth intercostal space; heart rate 78/min.', True, True),
    exam('palpation', 'abdomen', '腹部触诊', 'Palpate the abdomen',
         '腹软，上腹部压痛，无反跳痛；肝脾肋下未触及，全腹未及包块。',
         'Soft abdomen with upper abdominal tenderness and no rebound; liver and spleen not palpable below the costal margins; no mass.', True, True),
    exam('murphy', 'abdomen', '检查Murphy征', 'Assess Murphy sign', 'Murphy征阴性。', 'Murphy sign negative.'),
    exam('bowel', 'abdomen', '听诊肠鸣音', 'Auscultate bowel sounds', '肠鸣音3–4次/min，无气过水音。', 'Bowel sounds 3–4/min; no succussion splash.'),
    exam('percussion', 'abdomen', '腹部叩诊', 'Percuss the abdomen',
         '腹部叩诊呈鼓音，肝浊音界存在，无移动性浊音；肝肾区叩痛阴性。',
         'Tympanic percussion with liver dullness present, no shifting dullness and no hepatic or renal percussion tenderness.'),
    exam('inspection', 'abdomen', '视诊腹部', 'Inspect the abdomen',
         '腹平坦，无胃肠型、蠕动波或腹壁静脉曲张。', 'Flat abdomen, no visible bowel outline, peristaltic waves or abdominal wall varices.'),
    exam('nodes', 'lymphatic', '检查浅表淋巴结', 'Examine superficial lymph nodes',
         '原报告记载浅表淋巴结未见异常。', 'No superficial lymph-node abnormality reported.'),
]
investigations = [
    record('ultrasound-record', '查阅腹部超声报告', 'Review abdominal ultrasound report',
           '内脏反置；胆囊泥沙样结石。', 'Visceral inversion and sludge-like gallstones.'),
    record('ct-record', '查阅腹部CT报告', 'Review abdominal CT report',
           '横断位：全内脏反位，肝脏和胆囊在腹腔左侧，脾脏和胃在右侧；胆囊结石，颈管迂曲。冠状位：左心室在胸腔右侧，心尖指向右侧。原始DICOM序列未提供。',
           'Axial CT: situs inversus totalis; liver and gallbladder on the left, spleen and stomach on the right; gallstones and a tortuous gallbladder neck/duct region. Coronal CT: left ventricle in the right chest with a right-pointing apex. No original DICOM series is supplied.', essential=True),
    record('laboratory-record', '查阅术前实验室报告', 'Review preoperative laboratory report',
           '原文概述血常规、血生化和血凝指标正常；未提供具体项目、数值、单位、参考范围及采样时间。不得自行补写。',
           'The report summarises blood count, biochemistry and coagulation as normal; individual tests, numbers, units, reference ranges and sampling times are not supplied. Do not fill these in.'),
    record('operation-record', '查阅既往手术记录', 'Review the recorded operation',
           '历史记录：全身麻醉下完成腹腔镜胆囊切除。术中确认腹腔脏器镜像反位；原文记录主刀与助手在患者左侧、采用三孔法。手术30 min，出血量描述为少量，无精确数值。该记录不是本模拟器实施手术后的预测结果。',
           'Historical record: laparoscopic cholecystectomy under general anaesthesia, with mirror-image abdominal anatomy confirmed. The authors describe the surgeon and assistant on the patient\'s left and three ports. Duration 30 min; blood loss described as small, without a number. This is a published outcome, not a prediction produced by the simulator.', phase='review'),
    record('pathology-record', '查阅术后病理记录', 'Review postoperative histology',
           '慢性胆囊炎，胆囊结石。', 'Chronic cholecystitis with gallstones.', phase='review'),
    record('followup-record', '查阅出院和随访记录', 'Review discharge and follow-up',
           '术后第2天恢复肛门排气；第4天复查相关实验室指标未见明显异常；第5天出院。1个月门诊复查恢复良好，无明显不适及并发症。未提供长期结局。',
           'Flatus on postoperative day 2; repeat laboratory indices without a reported significant abnormality on day 4; discharged on day 5. At one month he was recovering well without reported significant discomfort or complications. Long-term outcome is not supplied.', phase='review',
           source=L('原报告第180页病例结局。', 'Source report p. 180, outcome.')),
]
decisions = [
    decision('anatomy', '根据已取得的影像资料，应如何记录脏器位置？', 'How should the documented organ positions be recorded?',
             {'read': 'ct-record'}, '先取得并阅读影像资料。', 'Obtain and read the imaging record first.', [
        option('mirror', '肝胆左侧、胃脾右侧，并明确记录解剖反位。', 'Liver/gallbladder left, stomach/spleen right; explicitly document inversion.', True,
               '与CT记录一致。必须按患者的解剖位置进行核对。', 'Matches the CT record; confirm the patient-specific anatomy.'),
        option('usual', '按通常位置记录肝胆在右侧。', 'Record the usual right-sided liver and gallbladder.', False,
               '忽略了本例已经提供的影像证据。', 'This disregards the supplied imaging evidence.'),
        option('unknown', '已经阅读CT，但仍记录为完全未知。', 'Record all positions as unknown despite reading CT.', False,
               '对于原文明确记录的左右位置，应准确记录；未知仅适用于未记载事项。', 'Explicitly recorded laterality is known; reserve unknown for unrecorded facts.'),
    ]),
    decision('planning', '准备术前团队讨论时，哪一种计划最符合本例证据边界？', 'Which plan respects the evidence boundaries for the preoperative team discussion?',
             ALL({'decided': 'anatomy'}, {'asked': 'pmh'}, {'asked': 'allergies'}),
             '先核实既往病史、过敏资料和影像位置。', 'Review comorbidities, allergy information and imaging first.', [
        option('individualised', '提示高龄、合并症及反位；由团队结合影像、术者经验确定站位和布局，补核缺失资料。',
               'Flag age, comorbidities and inversion; the team individualises positioning/layout using imaging and experience, and verifies missing information.', True,
               '原报告讨论承认站位与布孔并无唯一模式；本样例不把作者采用的布孔方式当作唯一标准。',
               'The source discusses more than one positioning/port approach; its particular choice is not the sole accepted standard.'),
        option('fixed', '对所有反位患者强制采用一个固定站位和布孔方案。', 'Require one fixed positioning and port layout for every patient with inversion.', False,
               '将个案做法推广为普遍规则，超出了原文支持范围。', 'Generalising one report into a universal rule exceeds the evidence.'),
        option('assume', '未记录的过敏和用药一律补成无异常。', 'Fill unrecorded allergies and medicines in as normal or absent.', False,
               '缺失信息不等于阴性结果，需要另行核实。', 'Missing information is not a negative finding and needs verification.'),
    ]),
    decision('safety', '进入历史手术记录回看前，应采用哪项安全原则？', 'Which safety principle should precede the historical operation review?',
             ALL({'decided': 'planning'}, {'read': 'laboratory-record'}),
             '先完成团队计划并查阅现有术前资料。', 'Complete the team plan and review available preoperative records first.', [
        option('verify', '核对患者、拟行操作和解剖侧别；不因镜像经验而省略结构辨认，不确定时暂停并寻求协助。',
               'Confirm patient, planned procedure and anatomical laterality; identify structures and pause for help when uncertain.', True,
               'WHO要求团队暂停核对患者、操作及部位；SAGES强调解剖辨认与不确定时的安全策略。本项为教学规则，非原报告已执行事项。',
               'WHO calls for team verification; SAGES emphasises anatomical identification and safe responses to uncertainty. This is an authored teaching rule, not a claim about what the report documents.'),
        option('blind', '只凭通常位置和外观直接处理管状结构。', 'Act on tubular structures using usual position and appearance alone.', False,
               '既不尊重反位证据，也未完成解剖辨认。', 'This ignores inversion and omits anatomical identification.'),
        option('clearance', '因原文概述检验正常，就宣布已经完成全部麻醉风险评估。', 'Treat the normal laboratory summary as completed anaesthetic clearance.', False,
               '原文未给出完整麻醉评估、禁食、气道及用药资料。', 'A full anaesthetic assessment, fasting, airway and medication record are not supplied.'),
    ]),
    decision('outcome', '这份病例的结局能支持怎样的表述？', 'What outcome statement is supported by this report?',
             ALL({'read': 'pathology-record'}, {'read': 'followup-record'}),
             '进入回看阶段后阅读病理与随访记录。', 'Read histology and follow-up in the review phase.', [
        option('bounded', '本例1个月随访恢复良好；不能据此估计长期结局或普遍手术成功率。',
               'Recovery was good at one month in this case; long-term outcome and population success rates cannot be inferred.', True,
               '保持个案结局、随访时长和外推边界。', 'Preserve the case-level outcome, follow-up duration and limits of inference.'),
        option('guarantee', '本模拟器证明同类患者手术都能成功。', 'The simulator proves surgery succeeds in all similar patients.', False,
               '单例报告与脚本执行均不能证明普遍疗效。', 'Neither a single report nor a scripted simulation establishes general efficacy.'),
    ]),
]
ready = ALL({'decided': 'anatomy'}, {'decided': 'planning'}, {'decided': 'safety'})
case = dict(
    schema='clinicalcraft/case@1', id=CASE_ID, version='1.0.0',
    title=L('上腹痛伴发热 · 84岁男性', 'Upper abdominal pain and fever · 84-year-old man'),
    summary=L('完成病史与检查资料核对，查阅现有影像，组织术前团队计划，再回看已发表的手术与随访记录。未记录资料保持未知。',
              'Review history, examination and existing imaging, formulate a preoperative team plan, then review the published operation and follow-up. Unrecorded data remain unknown.'),
    specialty=['general-surgery'], difficulty=3, setting='operating-room',
    facility='impf-surgery-hospital', locales=['zh-CN', 'en'], estimatedMinutes=20,
    tags=['surgerycraft-pilot', 'historical-review'],
    learningOutcomes=[
        L('从CT报告准确识别并记录反位的左右位置。', 'Identify and document inverted organ laterality from the CT report.'),
        L('区分记录明确的事实、未记录信息和教学流程设定。', 'Distinguish documented facts, missing information and authored workflow settings.'),
        L('提出尊重解剖变异和患者合并症的团队术前讨论计划。', 'Formulate a team discussion plan addressing anatomical variation and comorbidities.'),
        L('应用术前核查与解剖辨认原则，并限定单例结局的外推范围。', 'Apply verification and anatomical-identification principles and bound inference from one case.'),
    ],
    provenance=dict(kind='adapted', authors=['张少博', '余仁斌'],
        citation='张少博, 余仁斌. 内脏完全反位腹腔镜胆囊切除术一例. 肝胆胰外科杂志. 2024;36(3):180-181.',
        license='Educational adaptation; source publication and images retain their original rights.',
        notes=L('依据dataset第126例PDF改编，化名与医院场景为教学设定。初诊资料与后续历史记录分阶段开放。没有进行患者级三维重建、麻醉给药或组织力学仿真。',
                'Adapted from dataset item 126. Pseudonym and hospital placement are authored settings. Presentation and later historical records are staged separately. No patient-specific reconstruction, anaesthetic dosing or tissue mechanics is simulated.'),
        review=dict(status='editorial', reviewedAt='2026-10-31', reviewers=['AI-assisted technical/editorial review'],
            guidelines=['WHO Surgical Safety Checklist implementation manual, 2009', 'SAGES Safe Cholecystectomy Multi-Society Practice Guideline, 2020'],
            notes=L('已做原文与所引安全原则的编辑核对；尚未经过执业外科及麻醉医生审核，不构成已验证的临床能力评测。',
                    'Source and cited safety principles checked editorially; not reviewed by licensed surgical/anaesthetic clinicians and not a validated clinical competency assessment.'))),
    disclaimer=L('真实报告衍生的研究教学样例。操作与评分为脚本设计；历史结局不由模型预测。未经临床专家审核。',
                 'Research/teaching adaptation of a published report. Actions and scoring are authored; historical outcomes are not model predictions. Not clinician-reviewed.'),
    patient=dict(displayName=L('林先生（化名）', 'Mr Lin (pseudonym)'), age=84, sex='male',
        chiefComplaint=L('上腹痛、发热十多天', 'Upper abdominal pain and fever for more than ten days'),
        triageNote=L('84岁男性，因上腹痛、发热十多天住院。本场景是术前资料核对与历史病例回看，不模拟实时急救或麻醉。',
                     '84-year-old man admitted with upper abdominal pain and fever for more than ten days. This scene reviews preoperative evidence and a historical case, without real-time resuscitation or anaesthesia.'),
        posture='lying', appearance=dict(gown=True, hairStyle='short', hair='#b8b8b8'),
        persona=dict(personality=L('教学人物设定：配合、回答简短。', 'Authored persona: cooperative and concise.'),
            speechStyle=L('简短口语，仅复述有依据的资料；缺失项明确说未记录。', 'Brief lay speech grounded in available facts; missing items explicitly remain unrecorded.'),
            healthLiteracy='medium', affect='calm',
            openingLine=L('我上腹痛、发热十多天了。', 'I have had upper abdominal pain and fever for more than ten days.'),
            fallbackUnknown=L('这份病例没有记录，不能替我补写。', 'That is not recorded in this case; please do not fill it in.'))),
    phases=[dict(id='assessment', label=L('术前资料核对', 'Preoperative evidence review')),
            dict(id='review', label=L('历史手术与随访回看', 'Historical operation and follow-up review'), learnerSwitchable=False,
                 enterWhen=ALL(ready, {'intervened': 'open-historical-review'}))],
    initialPhase='assessment', clock=dict(mode='static'), history=hx, exam=exams,
    examNotRecorded=UNKNOWN, investigations=investigations,
    interventions=[dict(id='open-historical-review', name=L('完成准备讨论，进入历史记录回看', 'Complete preparation discussion and open historical review'),
        kind='consult', requires=[], risk='none', maxDoses=1, indicatedWhen=ready,
        contraindicatedWhen={'not': ready}, harm=L('尚未完成证据核对和计划，不应将本次回看视为合格准备。', 'Evidence review and planning are incomplete; this does not count as adequate preparation.'),
        response=L('这是教学阶段转换，不执行切开、麻醉或真实手术。只有完成前置决策后才开放后续历史记录。',
                   'This is a teaching phase transition, with no incision, anaesthesia or actual surgery. Later historical records open only after prerequisite decisions.'))],
    objectives=[
        objective('history', '核实症状、合并症与关键缺失资料', 'Review presentation, comorbidities and key missing data',
                  '询问主诉、既往病史及过敏资料，保留未记录项。', 'Ask about the presentation, medical history and allergies; preserve missing information.',
                  ALL({'asked':'presentation'}, {'asked':'pmh'}, {'asked':'allergies'})),
        objective('evidence', '完成检查与影像资料核对', 'Review examination and imaging evidence',
                  '核对查体记录与现有报告，再作判断。', 'Review examination and existing reports before deciding.',
                  ALL({'examined':'apex'}, {'examined':'palpation'}, {'read':'ct-record'}, {'read':'ultrasound-record'}, {'read':'laboratory-record'})),
        objective('plan', '形成有证据支持的团队计划', 'Form an evidence-supported team plan',
                  '根据已取得资料完成决策板，避免把未记录项补成正常。', 'Use the acquired evidence to complete the decision board without normal defaults.', ready, 'board'),
        objective('records', '回看历史处理与随访', 'Review historical management and follow-up',
                  '完成准备讨论后，阅读后续记录。', 'After the preparation discussion, read the later records.',
                  ALL({'read':'operation-record'}, {'read':'pathology-record'}, {'read':'followup-record'})),
        objective('limits', '说明证据与结局的适用边界', 'State the limits of the evidence and outcome',
                  '说明本例记录能够支持什么结论。', 'State what conclusions this case record can support.', {'decided':'outcome'}, 'board'),
    ], decisions=decisions,
    rubric=[
        rubric('r-presentation','history',5,'核实主诉与时长','Review presentation and duration',{'asked':'presentation'}),
        rubric('r-pmh','history',5,'核实慢阻肺与脑梗死病史','Review COPD and previous cerebral infarction',{'asked':'pmh'}),
        rubric('r-allergy','safety',5,'核实过敏记录，保持未知','Check allergy information and preserve unknown',{'asked':'allergies'}),
        rubric('r-exam','examination',5,'核对心尖位置和腹部检查','Review apex location and abdominal examination',ALL({'examined':'apex'},{'examined':'palpation'})),
        rubric('r-ct','investigations',15,'阅读CT证据','Read CT evidence',{'read':'ct-record'}),
        rubric('r-us','investigations',5,'阅读超声证据','Read ultrasound evidence',{'read':'ultrasound-record'}),
        rubric('r-lab','investigations',5,'阅读实验室记录及其缺失边界','Read laboratory record and its limits',{'read':'laboratory-record'}),
        rubric('r-anatomy','diagnosis',15,'首次判断正确记录左右解剖位置','Correct anatomical laterality on first attempt',{'decidedFirstTry':'anatomy'},True),
        rubric('r-plan','management',15,'首次选择个体化、保留未知的计划','Individualised plan preserving unknowns on first attempt',{'decidedFirstTry':'planning'}),
        rubric('r-safety','safety',10,'首次选择核查与安全辨认原则','Verification and safe identification on first attempt',{'decidedFirstTry':'safety'},True),
        rubric('r-operation','management',5,'阅读历史手术记录','Read the historical operation',{'read':'operation-record'}),
        rubric('r-pathology','investigations',5,'阅读病理记录','Read histology',{'read':'pathology-record'}),
        rubric('r-outcome','management',5,'首次正确限定随访结论','Correctly bound follow-up inference on first attempt',{'decidedFirstTry':'outcome'}),
    ],
    npcs=[dict(role='nurse',knowledge=L('协助核对现有记录；未记录的过敏、禁食和用药不能补写。', 'Help review available records; do not invent allergy, fasting or medication information.')),
          dict(role='radiologist',knowledge=L('只解释学员已经阅读的影像报告；没有原始DICOM，不能声称完成患者级三维重建。', 'Interpret only imaging reports already read; without original DICOM, do not claim patient-specific 3D reconstruction.'),interprets=['ct-record','ultrasound-record']),
          dict(role='attending',knowledge=L('引导学员区分来源事实与教学规则，并说明证据局限。', 'Guide the learner to distinguish source facts from teaching rules and explain evidence limits.'))],
    debrief=dict(title=L('病例复盘', 'Case debrief'),
        conclusion=L('本例为全内脏反位合并胆囊结石的历史报告。完成资料核对、个体化计划与安全讨论后，回看原文手术和1个月结局。',
                     'Historical report of situs inversus totalis with gallstones. Review evidence, individualised planning and safety, then the reported operation and one-month outcome.'),
        keyReasoning=[L('CT明确记载左右位置；原文未记载的事项保持未知。', 'CT explicitly records laterality; unrecorded items remain unknown.'),
                      L('作者采用的站位和三孔法不是所有患者的唯一标准。', 'The authors\' positioning and three-port approach are not the sole standard for all patients.'),
                      L('术后资料仅在完成前置阶段后开放；结局来自报告，而非干预效果模型。', 'Later records open after prerequisites; outcomes come from the report, not a treatment-effect model.')],
        boundaries=L('不模拟麻醉、器械切割、组织变形或患者级三维解剖；不提供剂量。评分为教学流程检查，尚未完成临床效度验证。',
                     'No anaesthesia, instrument cutting, tissue deformation or patient-specific anatomy simulation; no dosing. Scores check an authored workflow and have not undergone clinical validation.'),
        teachingPoints=[L('WHO 2009：切皮前团队共同核对患者、操作及部位。', 'WHO 2009: the team verifies patient, procedure and site before incision.'),
                        L('SAGES 2020：重视解剖辨认；解剖不确定时采用安全策略并寻求协助。', 'SAGES 2020: prioritise anatomical identification and safe strategies/help when anatomy is uncertain.'),
                        L('缺失资料不能补成阴性；病历中的概述正常不能变成虚构数值。', 'Missing data are not negative findings; a normal summary does not supply numerical results.'),
                        L('单例短期良好结局不等于普遍成功率。', 'A favourable short-term outcome in one case is not a population success rate.')],
        references=['张少博, 余仁斌. 内脏完全反位腹腔镜胆囊切除术一例. 肝胆胰外科杂志. 2024;36(3):180-181.',
                    'World Health Organization. Implementation manual WHO surgical safety checklist 2009. Geneva: WHO; 2009. https://www.who.int/publications/i/item/9789241598590',
                    'SAGES. Safe Cholecystectomy Multi-Society Practice Guideline. 2020. https://www.sages.org/publications/guidelines/safe-cholecystectomy-multi-society-practice-guideline/'],
        notice=L('技术样例的流程评分，非已验证的医疗能力评分；真实模型性能尚未测量。', 'Technical demonstration workflow score, not validated clinical competence; live-model performance has not been measured.')),
    unknowns=[UNKNOWN, L('体重、SpO₂、药物、剂量、过敏、禁食、气道评估、详细检验数值及长期随访未记录。',
                        'Weight, SpO₂, medicines, doses, allergies, fasting, airway assessment, detailed laboratory values and long-term follow-up are not recorded.')],
    extensions=dict(collection='surgerycraft-pilot',sourceArticleId='1654623',historicalReview=True,
                    testUtterances=[dict(text=h['question'][locale],locale=locale,expect=[h['id']]) for h in hx for locale in ['zh-CN','en']]))
paraphrases = {
    'presentation': ('上腹疼和发烧有多少天了？', 'Tell me about the abdominal pain and fever.'),
    'pmh': ('说一下您的既往病史。', 'Tell me your past medical history.'),
    'family': ('家里人有同样的先天异常吗？', 'Does this congenital condition run in the family?'),
    'allergies': ('吃药会不会过敏？', 'Any medication allergies?'),
    'medications': ('每天吃的药有哪些？', 'List your regular medicines.'),
    'psh': ('有没有既往手术史？', 'Any previous surgery?'),
    'fasting': ('术前禁食多久了？', 'How long have you been fasting?'),
    'weight': ('请问体重多少公斤？', 'How many kilograms do you weigh?'),
    'smoking': ('您抽不抽烟？', 'Any tobacco use?'),
    'alcohol': ('喝不喝酒？', 'Any alcohol intake?'),
    'pain-score': ('给疼痛打个分。', 'Rate the pain severity.'),
    'vomiting': ('最近吐过没有？', 'Any episodes of emesis?'),
    'jaundice': ('有没有黄疸表现？', 'Any yellow discolouration?'),
    'functional': ('日常能自己走路和照顾自己吗？', 'Can you manage daily activities independently?'),
    'expectations': ('这次就诊最想解决什么？', 'What matters most to you in this visit?'),
}
case['extensions']['testUtterances'] = []
for h in hx:
    if h['id'] == 'psh':
        h['keywords']['en'] = ['surgicalhistory', 'previous surgery', 'past operations']
    for locale, phrase in zip(['zh-CN', 'en'], paraphrases[h['id']]):
        h['keywords'][locale].append(phrase.rstrip('？?.'))
        case['extensions']['testUtterances'].append(dict(text=phrase,locale=locale,expect=[h['id']]))
case['extensions']['testUtterances'] += [
    dict(text='今天外面的天气怎么样？',locale='zh-CN',expect=[]),
    dict(text='What is the weather outside?',locale='en',expect=[]),
]
solution=[dict(type='start')]
solution += [dict(type='ask',itemId=id) for id in ['presentation','pmh','allergies']]
solution += [dict(type='examine',findingId=id) for id in ['entry-vitals','apex','palpation']]
for id in ['ultrasound-record','ct-record','laboratory-record']:
    solution += [dict(type='order',investigationId=id),dict(type='read',investigationId=id)]
for id, answer in [('anatomy','mirror'),('planning','individualised'),('safety','verify')]:
    solution.append(dict(type='answer',decisionId=id,optionIds=[answer]))
solution.append(dict(type='intervene',interventionId='open-historical-review'))
for id in ['operation-record','pathology-record','followup-record']:
    solution += [dict(type='order',investigationId=id),dict(type='read',investigationId=id)]
solution += [dict(type='answer',decisionId='outcome',optionIds=['bounded']),dict(type='finish')]
case['solution']=solution
