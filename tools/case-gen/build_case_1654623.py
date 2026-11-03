"""Build Case 126 (cmcr-1654623) v4: a laparoscopic cholecystectomy in situs inversus totalis that the
learner (or an agent) performs, on top of the source-bounded v3 case (`case_1654623_base.py`).

v4 adds, without changing a published fact:
  * a diagnostic decision framed by the Tokyo Guidelines 2018 (the record supports gallstone disease with
    suspected, not confirmed, acute cholecystitis);
  * perioperative risk assessment (age 84, COPD, previous cerebral infarction) with the unrecorded items
    kept unknown, and the WHO Surgical Safety Checklist (sign in, time out, sign out) as real steps;
  * the operation itself as a ClinicalCraft procedure (docs/PROCEDURE.md in ClinicalCraft): ports, traction,
    dissection, the critical view of safety evaluated on the field, clips, division, bail-outs and
    complications that follow from what is actually clipped, divided or burnt;
  * synthetic intra-operative physiology, labelled as such everywhere it appears;
  * one rubric across clinical reasoning and operative safety, with safety gates no score compensates.

Inputs: content/assets/cases/cmcr-1654623/anatomy.json (the anatomy model's centrelines, regions and port
sites in the patient frame: +x the patient's left, +y cranial, +z anterior, metres).
Run with Python 3.11+: python tools/case-gen/build_case_1654623.py
No model/API calls, PDF redistribution, or unrecorded clinical defaults.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import case_1654623_base as base  # noqa: E402  (builds the v3 case dict on import)

L = base.L
ROOT = base.ROOT
DEST = base.DEST
CASE_ID = base.CASE_ID
ANATOMY = ROOT / 'content' / 'assets' / 'cases' / CASE_ID / 'anatomy.json'
SYNTH = L('（模拟值）', ' (simulated value)')
UNKNOWN = base.UNKNOWN
SOURCE = base.SOURCE
GUIDE = L('教学设计，依据所引指南；不是原报告记载。', 'Teaching design based on the cited guidance; not recorded in the source.')

case = copy.deepcopy(base.case)

# ------------------------------------------------------------------ case card
case['version'] = '2.5.0'

# the swab count (in-world: kept by item identity, docs/TEAM.md §4.3): open while a swab is missing or one is not in the
# count, until it is reconciled or — escalated — a clear RF scan excludes a retained swab. No record (text mode): not open.
COUNT_OPEN = {'count': {'status': ['baseline', 'discrepancy', 'unresolved']}}
case['summary'] = L(
    '84岁男性，上腹痛、发热十多天。从问诊、查体和资料核对开始，完成术前评估、手术安全核对，并在病例相关的参考解剖上亲手完成腹腔镜手术，再回看原报告的手术与随访。',
    'An 84-year-old man with upper abdominal pain and fever for more than ten days. Take the history, examine, review the records, '
    'assess perioperative risk, run the surgical safety checklist and perform the laparoscopic operation yourself on case-informed '
    'reference anatomy, then review the operation and follow-up the source reports.')
case['estimatedMinutes'] = 45
case['tags'] = sorted(set(case.get('tags', []) + ['laparoscopy', 'operative-simulation', 'critical-view-of-safety', 'situs-inversus']))
case['learningOutcomes'] = case.get('learningOutcomes', []) + [
    L('依据东京指南2018区分胆囊结石、疑似与确诊急性胆囊炎，不把不完整证据当作确诊。',
      'Distinguish gallstone disease from suspected and confirmed acute cholecystitis (Tokyo Guidelines 2018) without treating incomplete evidence as a diagnosis.'),
    L('在镜像解剖中选择并论证布孔、站位和牵拉方向。', 'Choose and justify ports, stance and traction directions in mirror-image anatomy.'),
    L('只有在关键安全视野的三项条件真实建立后才进行不可逆操作；无法建立时选择安全的替代策略。',
      'Perform irreversible steps only once the three criteria of the critical view of safety truly hold; choose a safe alternative when they cannot.'),
    L('识别并处理术中出血、胆汁或结石溢出与胆管损伤，及时说出问题并求助。',
      'Recognise and manage bleeding, bile or stone spillage and bile duct injury, say so aloud and call for help.'),
]
# world actions cost their own duration (2.3.0): a 60 s insufflation is a clinical minute, and the vital signs read
# afterwards carry that time (ClinicalCraft docs/EMBODIED.md R8, `clock.worldTime`)
case['clock'] = {'mode': 'simulated', 'startTime': '08:00', 'worldTime': 'actual',
                 'actionCosts': {'ask': 1, 'examine': 1, 'order': 1, 'read': 1, 'intervene': 2, 'answer': 0}}
case['provenance']['notes'] = L(
    '依据dataset第126例PDF改编。v4增加：东京指南框架的诊断决策、围术期风险评估、WHO安全核对、在参考解剖上的交互式手术（关键安全视野由术野状态判定），以及标注为模拟值的术中生理。'
    '化名、医院场景、参考解剖和术中生理为教学设定；原报告的事实未改动。',
    'Adapted from dataset item 126. v4 adds a Tokyo-Guidelines diagnostic decision, perioperative risk assessment, the WHO checklist, '
    'an interactive operation on reference anatomy (the critical view of safety is judged on the field) and intra-operative physiology '
    'labelled as simulated. Pseudonym, hospital, reference anatomy and physiology are authored; no source fact is changed.')
case['disclaimer'] = L(
    '教学病例，依据已发表病例改编，不构成医疗建议。三维解剖为病例相关的参考解剖，不是患者CT重建；术中生命体征为模拟值；未经临床专家审核。',
    'Teaching case adapted from a published report — not medical advice. The 3D anatomy is case-informed reference anatomy, not a '
    'reconstruction from the patient\'s CT; intra-operative vital signs are simulated; not reviewed by clinicians.')

# ------------------------------------------------------------------ phases
case['phases'] = [
    case['phases'][0],
    dict(id='preop', label=L('术前评估与计划', 'Preoperative assessment and planning'), learnerSwitchable=False,
         enterWhen={'objective': 'plan'}),
    dict(id='theatre', label=L('手术室：安全核对与麻醉', 'Theatre: safety checks and anaesthesia'), learnerSwitchable=False,
         enterWhen={'decided': 'risk'}),
    dict(id='operation', label=L('腹腔镜胆囊切除', 'Laparoscopic cholecystectomy'), learnerSwitchable=False,
         enterWhen={'all': [{'intervened': 'time-out', 'valid': True}, {'decided': 'diagnosis'}, {'decided': 'planning'}, {'decided': 'risk'}]}),
    dict(id='recovery', label=L('麻醉后恢复与术后', 'Recovery and postoperative care'), learnerSwitchable=False,
         enterWhen={'intervened': 'sign-out', 'valid': True}),
    # 2.4.0: the reported operation is disclosed only on a valid request after the postoperative discussion and the
    # Sign Out — checked here on its own, so an early (invalid) request reveals nothing
    dict(id='review', label=L('原报告手术与随访回看', 'Review of the reported operation and follow-up'), learnerSwitchable=False,
         enterWhen={'all': [{'intervened': 'open-historical-review', 'valid': True}, {'decided': 'postop'}, {'intervened': 'sign-out', 'valid': True}]}),
]

# ------------------------------------------------------------------ history: perioperative risk (unrecorded → unknown)
def hx(id, topic, q_zh, q_en, a_zh, a_en, kw_zh, kw_en, required=False):
    return dict(id=id, topic=topic, question=L(q_zh, q_en), answer=L(a_zh, a_en),
                keywords={'zh-CN': kw_zh, 'en': kw_en}, disclosure='unknown', required=required, source=UNKNOWN)

case['history'] += [
    hx('antithrombotic', 'medications', '脑梗死后在吃阿司匹林、氯吡格雷或抗凝药吗？', 'Since the stroke, do you take aspirin, clopidogrel or a blood thinner?',
       '这份病例没有记录用药，包括抗血小板或抗凝药，不能替我补写。', 'The case does not record medicines, including antiplatelets or anticoagulants; please do not fill it in.',
       ['阿司匹林', '氯吡格雷', '抗凝药', '抗血小板', '吃的抗栓药'], ['aspirin', 'clopidogrel', 'bloodthinner', 'anticoagulant', 'antiplatelet'], required=True),
    hx('copd-status', 'pmh', '慢阻肺平时喘得厉害吗？用吸入药吗？最近有没有加重？', 'How is the COPD — breathless day to day, inhalers, any recent flare-ups?',
       '原报告只写了有慢阻肺病史，没有记录症状、吸入药、加重或肺功能。', 'The source records only a history of COPD — no symptoms, inhalers, exacerbations or lung function.',
       ['慢阻肺平时', '吸入药', '喘得厉害', '慢阻肺加重', '肺功能'], ['inhaler', 'copdflare', 'breathlessdaytoday', 'lungfunction', 'copdcontrol'], required=True),
    hx('stroke-deficit', 'pmh', '脑梗死后留下手脚无力、说话或吞咽问题了吗？', 'Did the stroke leave weakness, speech or swallowing problems?',
       '原报告只写了既往脑梗死，没有记录后遗症、时间或吞咽情况。', 'The source records only a previous cerebral infarction — not its date, residual deficits or swallowing.',
       ['脑梗后遗症', '手脚无力', '吞咽', '说话不清', '脑梗死后'], ['strokeleftweakness', 'swallowing', 'residualdeficit', 'speechproblems', 'aftertheastroke']),
    # 2.3.0: what an audited run turned from a teaching "what if" into history — the source records none of it
    hx('prior-treatment', 'medications', '来医院之前吃过退烧药或抗生素吗？', 'Before you came in, did you take anything for the fever — paracetamol or antibiotics?',
       '原报告没有记录入院前的用药，包括退热药或抗生素；也没有家属陈述的记录。', 'The source records no treatment before admission — no antipyretic, no antibiotic — and no account from the family.',
       ['退烧药', '抗生素', '入院前用药', '来之前吃药', '消炎药'], ['antipyretic', 'antibiotic', 'paracetamolbefore', 'treatmentbeforeadmission', 'tookforthefever']),
    hx('pain-meals', 'pain', '肚子疼跟吃饭有关系吗？吃油腻的东西会更疼吗？', 'Is the pain related to meals — worse after fatty food?',
       '原报告只写了上腹痛，没有记录疼痛与进食的关系。', 'The source records upper abdominal pain only; it does not say whether the pain is related to meals.',
       ['吃饭', '进食后', '油腻', '饭后疼', '餐后'], ['aftermeals', 'fattyfood', 'aftereating', 'postprandial', 'relatedtomeals']),
]
# a medicine stopped is a medicine recorded: neither is in the source
case['history'][[h['id'] for h in case['history']].index('antithrombotic')]['keywords']['zh-CN'] += ['停用抗栓药', '停了阿司匹林']
case['history'][[h['id'] for h in case['history']].index('antithrombotic')]['keywords']['en'] += ['stoppedaspirin', 'stoppedthebloodthinner']

paraphrases = {
    'antithrombotic': ('您现在吃抗凝药或阿司匹林吗？', 'Are you on any blood thinners or aspirin?'),
    'copd-status': ('慢阻肺用什么吸入药？', 'Which inhalers do you use for the COPD?'),
    'stroke-deficit': ('脑梗以后吞咽有问题吗？', 'Any swallowing problems since the stroke?'),
    'prior-treatment': ('入院前用过抗生素吗？', 'Did you take any antibiotics before admission?'),
    'pain-meals': ('吃饭以后会更疼吗？', 'Is the pain worse after meals?'),
}
for item_id, (zh, en) in paraphrases.items():
    case['extensions']['testUtterances'] += [dict(text=zh, locale='zh-CN', expect=[item_id]), dict(text=en, locale='en', expect=[item_id])]

# ------------------------------------------------------------------ records the source does not contain
def missing_record(id, zh, en, why_zh, why_en, phase='preop'):
    return dict(id=id, name=L(zh, en), category='record', aliases={'zh-CN': [zh], 'en': [en]}, requires=['records'],
                performedAt='records', risk='none', value='useful',
                results={phase: dict(available=False, text=L(why_zh, why_en), source=UNKNOWN)})

case['investigations'] += [
    missing_record('ecg-record', '查阅心电图', 'Review the ECG', '病历中没有心电图记录。右位心时需按镜像位置放置胸导联，结果才可解读。',
                   'No ECG is recorded. With dextrocardia the chest leads must be placed in mirror positions for a readable tracing.'),
    missing_record('pft-record', '查阅肺功能', 'Review lung function tests', '病历中没有肺功能或血气记录。', 'No lung function tests or blood gases are recorded.'),
    missing_record('cxr-record', '查阅胸片', 'Review the chest X-ray', '病历中没有胸片记录；心胸位置见CT冠状位。', 'No chest X-ray is recorded; cardiothoracic position is shown on the coronal CT.'),
]

# ------------------------------------------------------------------ decisions
def opt(id, correct, fzh, fen, zh, en):
    return dict(id=id, text=L(zh, en), correct=correct, feedback=L(fzh, fen))

case['decisions'].insert(0, dict(
    id='diagnosis', kind='single',
    prompt=L('依据现有资料，最站得住的诊断表述是什么？', 'On the evidence available, which diagnostic statement holds best?'),
    requires={'all': [{'read': 'ultrasound-record'}, {'read': 'laboratory-record'}, {'examined': 'murphy'}]},
    need=L('先查阅超声、化验并检查Murphy征。', 'Review the ultrasound and laboratory records and check Murphy\'s sign first.'),
    options=[
        opt('suspected', True, '正确。东京指南2018：有上腹压痛和发热病史，但查体体温正常、Murphy征阴性、化验概述正常，超声只记载泥沙样结石，局部、全身和影像三项不能同时成立——是胆囊结石伴疑似急性胆囊炎，证据不完整。',
            'Correct. Tokyo Guidelines 2018: upper abdominal tenderness and a reported fever, but a normal temperature at examination, a negative Murphy sign, laboratory results summarised as normal and an ultrasound that records only sludge-like stones — the local, systemic and imaging criteria do not all hold. Gallstone disease with suspected acute cholecystitis; the evidence is incomplete.',
            '胆囊结石，伴疑似（未确诊）急性胆囊炎', 'Gallstone disease with suspected, not confirmed, acute cholecystitis'),
        opt('confirmed', False, '确诊需要局部征象、全身炎症表现和典型影像同时存在；本例影像未记载胆囊壁增厚等炎症征象，化验概述正常。',
            'A definite diagnosis needs local signs, systemic inflammation and characteristic imaging together; here the imaging records no inflammatory signs and the laboratory summary is normal.',
            '确诊急性胆囊炎', 'Confirmed acute cholecystitis'),
        opt('cbd-stone', False, '没有胆管扩张、黄疸或肝功能异常的记载；术中所见胆总管不扩张属于后来的记录。不能据此诊断胆总管结石。',
            'No dilated duct, jaundice or abnormal liver tests is recorded (the undilated common bile duct at operation is a later record); a common bile duct stone is not supported.',
            '胆总管结石', 'Common bile duct stones'),
        opt('gastric', False, '内脏反位的胆道疾病常以左上腹痛就诊而被误认为胃病；本例影像已显示结石。',
            'Biliary disease in situs inversus often presents as left upper abdominal pain mistaken for gastric disease; here imaging shows the stones.',
            '胃病，无需关注胆囊', 'Gastric disease; the gallbladder is incidental'),
    ]))

case['decisions'].append(dict(
    id='risk', kind='multiple',
    prompt=L('麻醉和手术前，哪些问题必须先弄清楚或做好准备？（多选）', 'Before anaesthesia and surgery, what must be clarified or prepared? (select all that apply)'),
    requires={'all': [{'asked': 'pmh'}, {'decided': 'planning'}]},
    need=L('先了解既往病史并完成个体化计划。', 'Take the medical history and make the individualised plan first.'),
    options=[
        opt('copd', True, '84岁慢阻肺患者要评估呼吸症状、用药、近期加重；气腹和全麻会加重通气负担。', 'An 84-year-old with COPD needs symptoms, medication and recent exacerbations assessed; pneumoperitoneum and general anaesthesia add to the ventilatory load.',
            '慢阻肺的现状与通气风险', 'COPD status and ventilatory risk'),
        opt('antithrombotic', True, '脑梗死后可能在用抗血小板或抗凝药；病例未记录，须核实并按出血/血栓风险决定是否停用。', 'After a stroke he may take antiplatelets or anticoagulants; the case does not say — verify and decide on interruption by bleeding and thrombotic risk.',
            '抗血小板/抗凝药', 'Antiplatelet or anticoagulant therapy'),
        opt('function', True, '既往卒中后的后遗症、吞咽与活动能力影响误吸风险和术后康复。', 'Residual stroke deficits, swallowing and mobility affect aspiration risk and recovery.',
            '神经功能后遗症、吞咽与活动能力', 'Residual neurological deficit, swallowing and mobility'),
        opt('dextrocardia', True, '右位心：心电图胸导联与除颤电极要按镜像位置放置。', 'Dextrocardia: ECG chest leads and defibrillator pads go in mirror positions.',
            '右位心对监护和除颤的影响', 'What dextrocardia means for monitoring and defibrillation'),
        opt('asa', False, '病例没有ASA分级、肺功能或心功能资料，不能凭年龄和诊断名称补出分级。', 'The case gives no ASA class, lung or cardiac function; a class cannot be filled in from age and diagnoses.',
            '根据现有记录直接定ASA分级', 'Assign an ASA class from the record as it stands'),
        opt('no-lap', False, '慢阻肺不是腹腔镜手术的绝对禁忌；需要的是评估和较低气腹压等调整。', 'COPD does not rule out laparoscopy; it calls for assessment and adjustments such as lower insufflation pressure.',
            '慢阻肺禁止腹腔镜手术', 'COPD rules out laparoscopy'),
    ]))

case['decisions'].append(dict(
    id='emergence', kind='multiple',
    prompt=L('手术结束，准备苏醒。这位84岁、慢阻肺、既往脑梗死的患者，何时拔管、何时经口进食，如何决定？（多选）',
             'The operation is over and he is waking up. For this 84-year-old with COPD and a previous stroke, how are extubation and oral intake decided? (select all that apply)'),
    requires={'any': [{'procedure': {'closed': True}}, {'procedure': {'bailout': 'convert-open'}}]},
    need=L('先结束手术。', 'Finish the operation first.'),
    options=[
        opt('criteria', True, '拔管看通气（呼吸频率、潮气量、氧合、无二氧化碳潴留）、肌松已恢复（TOF比值≥0.9）、清醒能听指令、有效咳嗽、能处理分泌物、气道保护反射。',
            'Extubation rests on ventilation (rate, tidal volume, oxygenation, no CO₂ retention), recovery from neuromuscular block (train-of-four ratio ≥ 0.9), being awake and following commands, an effective cough, handling secretions and protective airway reflexes.',
            '拔管依据通气、肌松恢复、意识、咳嗽、分泌物处理和气道保护', 'Extubate on ventilation, reversal, consciousness, cough, secretion handling and airway protection'),
        opt('swallow-after', True, '卒中后吞咽障碍风险高：拔管后、经口进食前做正式的吞咽评估；拔管与进食是两个决定。',
            'After a stroke the risk of dysphagia is high: a formal swallowing assessment comes after extubation and before any oral intake — extubation and eating are two decisions.',
            '拔管后、经口进食前做正式吞咽评估', 'A formal swallowing assessment after extubation, before oral intake'),
        opt('swallow-before-extubation', False, '带着气管导管不能做饮水试验或吞咽造影，这也不是拔管条件；吞咽评估决定的是何时进食，不是何时拔管。',
            'A water-swallow test or videofluoroscopy cannot be done with a tube in place and is not an extubation criterion; swallowing assessment decides oral intake, not extubation.',
            '先通过饮水试验或吞咽造影（VFSS）再拔管', 'Keep him intubated until he passes a water-swallow test or VFSS'),
        opt('oral-once-extubated', False, '能拔管不等于能安全吞咽；既往卒中者可能隐性误吸，进食前要先做吞咽评估。',
            'Being fit for extubation is not the same as swallowing safely; after a stroke aspiration can be silent, so oral intake waits for a swallowing assessment.',
            '拔管成功就可以经口饮水进食', 'Once extubated he can drink and eat: extubation shows his airway is protected'),
    ]))

case['decisions'].append(dict(
    id='postop', kind='multiple',
    prompt=L('转入恢复室后，本例最需要重点观察什么？（多选）', 'In recovery, what matters most to watch in this patient? (select all that apply)'),
    requires={'intervened': 'pacu-handover'},
    need=L('先完成恢复室交接。', 'Complete the recovery-room handover first.'),
    options=[
        opt('resp', True, '高龄慢阻肺：氧合、呼吸频率、二氧化碳潴留与咳痰能力。', 'Old age and COPD: oxygenation, respiratory rate, CO₂ retention and ability to cough.',
            '呼吸与氧合', 'Breathing and oxygenation'),
        opt('neuro', True, '既往卒中：术后谵妄与新发神经功能缺损要及时识别。', 'Previous stroke: recognise delirium and any new neurological deficit early.',
            '意识与新发神经体征', 'Consciousness and new neurological signs'),
        opt('bile', True, '胆漏或胆管损伤可在术后才表现：腹痛加重、发热、黄疸、引流或伤口胆汁。', 'A bile leak or duct injury may show only after surgery: worsening pain, fever, jaundice, bile in a drain or wound.',
            '胆漏与胆管损伤的征象', 'Signs of bile leak or bile duct injury'),
        opt('bleed', True, '心率加快、血压下降、腹胀提示出血。', 'A rising heart rate, falling blood pressure or distension suggest bleeding.',
            '出血征象', 'Signs of bleeding'),
        opt('discharge-same-day', False, '高龄合并症患者，原报告术后第5天出院；不能把当日出院当成常规。', 'An elderly patient with comorbidity; the source reports discharge on day 5 — same-day discharge is not the default here.',
            '常规当日出院', 'Routine same-day discharge'),
    ]))

# the v3 safety decision is unlocked by planning and laboratory review (unchanged); v3 anatomy/planning stay

# ------------------------------------------------------------------ interventions: checklist, anaesthesia, recovery
def iv(id, kind, zh, en, resp_zh, resp_en, risk='none', indicated=None, contra=None, harm=None, phases=None, checklist=False):
    out = dict(id=id, name=L(zh, en), kind=kind, requires=[], risk=risk, maxDoses=1, response=L(resp_zh, resp_en))
    if checklist:
        # a WHO checklist step: an out-of-order attempt is logged, applies nothing and uses none of its single dose
        out['checklist'] = True
    if indicated:
        out['indicatedWhen'] = indicated
    if contra:
        out['contraindicatedWhen'] = contra
        out['harm'] = L(*harm)
    return out

# The WHO Sign In is the team's check, never a side effect of a task (2.3.0): attaching the monitor is one task
# (`attach-monitor`, what the monitor's `attach` and a delegated nurse record); the Sign In is valid only once its
# checks have been addressed — the pulse oximeter on and working, the allergy and aspiration (fasting) questions
# asked — and otherwise is logged as invalid and leaves induction unscored as in order.
# 2.4.0: an elective operation is entered only on its milestones — the diagnosis made, the operation planned for this
# anatomy, the operative risk assessed (an audited run that asked only allergies and fasting reached the operation)
ELECTIVE_MILESTONES = [{'decided': 'diagnosis'}, {'decided': 'planning'}, {'decided': 'risk'}]
SIGN_IN_CHECKS = {'all': [*ELECTIVE_MILESTONES, {'intervened': 'attach-monitor'}, {'asked': 'allergies'}, {'asked': 'fasting'}]}
case['interventions'] = [x for x in case['interventions'] if x['id'] != 'open-historical-review'] + [
    iv('attach-monitor', 'monitoring', '连接监护：脉搏血氧、心电（镜像导联）与无创血压', 'Attach the monitor: pulse oximetry, ECG (mirror leads), non-invasive blood pressure',
       '监护已连接：脉搏血氧有波形、读数可靠；右位心——心电图胸导联按镜像位置放置；无创血压按设定间隔测量。这只是连接监护，不是麻醉前核对。',
       'Monitoring attached: the pulse oximeter shows a good trace and reads reliably; dextrocardia — ECG chest leads in mirror positions; non-invasive blood pressure cycling. This is the monitor only, not the Sign In.',
       indicated={'phase': 'theatre'}),
    iv('sign-in', 'consult', 'WHO 麻醉前核对（Sign In）', 'WHO Sign In before induction',
       '团队核对身份、手术、知情同意与部位：胆囊位于患者左侧（全内脏反位）——CT 的方位标记和皮肤标记都以患者自身的左侧核对，不做“左右反过来”的换算；脉搏血氧已在患者身上且工作正常；右位心——心电图导联与除颤电极按镜像放置；过敏、气道与误吸风险、预计失血原报告未记录，已当场确认。',
       'The team checks identity, procedure, consent and site: the gallbladder is on the patient\'s LEFT (situs inversus totalis) — the CT orientation marker and the skin marking are both checked against the patient\'s own left, with no "reversing" of sides; the pulse oximeter is on the patient and working; dextrocardia — ECG leads and defibrillator pads in mirror positions; allergies, airway and aspiration risk and expected blood loss are not recorded in the source and are confirmed now.',
       indicated={'all': [{'phase': 'theatre'}, SIGN_IN_CHECKS]}, contra={'not': SIGN_IN_CHECKS},
       harm=('核对项尚未落实就做麻醉前核对：已记录为无效。择期手术先要明确诊断、制定手术计划并评估手术风险；再连接监护（脉搏血氧工作正常），问清过敏与禁食（误吸风险），然后 Sign In。',
             'A Sign In before its checks: recorded as invalid. An elective operation needs the diagnosis made, the operation planned and the operative risk assessed first; then attach the monitor (a working pulse oximeter) and ask about allergies and fasting (aspiration risk), and sign in.'),
       checklist=True),
    iv('induction', 'airway', '全身麻醉诱导与气管插管', 'Induce general anaesthesia and intubate',
       '充分预充氧（以呼气末氧浓度判断，而非呼末二氧化碳）；先给镇静催眠药使患者意识消失，再给肌松药，绝不在没有足够催眠的情况下肌松；插管后以持续的呼末二氧化碳波形确认导管位置，机械通气。（教学步骤：不涉及具体药物与剂量。）',
       'Preoxygenated (judged by end-tidal oxygen, not end-tidal CO₂); the hypnotic first, to unconsciousness, then the neuromuscular blocker — never paralysis without adequate hypnosis; tube position confirmed by sustained capnography; ventilated. (Teaching step: no drug or dose is modelled.)',
       risk='high', indicated={'intervened': 'sign-in', 'valid': True}, contra={'not': {'intervened': 'sign-in', 'valid': True}},
       harm=('未完成麻醉前核对就诱导：过敏、气道和部位风险未经团队确认。', 'Induction before the Sign In: allergy, airway and site risks were not confirmed by the team.')),
    iv('time-out', 'consult', 'WHO 切皮前暂停核对（Time Out）', 'WHO Time Out before incision',
       '团队确认：患者、手术为腹腔镜胆囊切除、病变在患者左侧（影像方位标记与皮肤标记均以患者自身左侧核对）；术者讲解预计关键步骤（镜像解剖、关键安全视野后才夹闭）、抗菌药与影像已就位；如解剖不清将暂停、求助或改变术式。',
       'The team confirms the patient, a laparoscopic cholecystectomy and the pathology on the patient\'s left (image orientation marker and skin marking both checked against the patient\'s own left); the surgeon states the critical steps (mirror-image anatomy, nothing clipped before the critical view of safety), antibiotics and imaging are ready; if the anatomy is unclear the team will stop, call for help or change approach.',
       # after a valid Sign In and under anaesthesia (an induction out of order is still an induction: its own gate shows the order)
       indicated={'all': [{'intervened': 'sign-in', 'valid': True}, {'intervened': 'induction'}]},
       contra={'not': {'all': [{'intervened': 'sign-in', 'valid': True}, {'intervened': 'induction'}]}},
       harm=('麻醉前核对与诱导完成之前就进行切皮前核对，顺序不对：已记录为无效，手术仍未开始，需在两者之后重新核对。', 'A Time Out before a valid Sign In and induction is out of order: recorded as invalid; the operation stays locked until a Time Out after both.'), checklist=True),
    # 2.4.0: the Sign Out reads the count record (by item identity) — a count that is not settled is not signed out
    iv('sign-out', 'consult', 'WHO 离开手术室前核对（Sign Out）', 'WHO Sign Out before leaving theatre',
       '确认实施的手术、器械与纱布清点、标本标记、需关注的问题（包括任何术中并发症）并交接恢复室。',
       'The procedure performed, instrument and swab counts, specimen labelling and concerns for recovery (including any intra-operative complication) are confirmed and handed over.',
       indicated={'all': [{'any': [{'procedure': {'closed': True}}, {'procedure': {'bailout': 'convert-open'}}]}, {'not': COUNT_OPEN}]},
       contra={'not': {'all': [{'any': [{'procedure': {'closed': True}}, {'procedure': {'bailout': 'convert-open'}}]}, {'not': COUNT_OPEN}]}},
       harm=('手术尚未结束，或纱布清点尚未相符（也未上报并扫描排除体内遗留）就做离室核对：已记录为无效，需在手术结束、清点相符后重新核对。',
             'Sign Out before the operation has ended, or while the swab count is not reconciled (nor escalated with a clear scan excluding a retained swab): recorded as invalid; repeat it once the operation has ended and the count is settled.'), checklist=True),
    iv('pacu-handover', 'monitoring', '恢复室交接', 'Hand over in the recovery room',
       '交接：84岁，慢阻肺，既往脑梗死，全内脏反位；实施的手术和术中情况；需观察的问题。',
       'Handover: 84 years, COPD, previous stroke, situs inversus totalis; the operation done and anything that happened; what to watch.',
       indicated={'phase': 'recovery'}),
    iv('open-historical-review', 'consult', '结束模拟，打开原报告的手术、病理与随访记录', 'End the simulation and open the reported operation, histology and follow-up',
       '以下为原报告记载的真实经过；模拟中的操作不改变它。', 'What follows is what the source reports; nothing done in the simulation changes it.',
       indicated={'decided': 'postop'}, contra={'not': {'decided': 'postop'}},
       harm=('术后观察要点尚未讨论。', 'Postoperative priorities have not been discussed yet.')),
]

# 2.5.0: new investigations in this encounter (ClinicalCraft docs/STUDIES.md) — studies the published case never
# reported, as versioned teaching profiles: the result is a simulated investigation, never the source's record (the
# source's own records stay what they are: no ECG, no chest radiograph, laboratory tests summarised as normal)
TEACHING = L('（教学配置，模拟）', ' (teaching profile, simulated)')
def _t(zh, en):
    return L(zh + TEACHING['zh-CN'], en + TEACHING['en'])
case['studies'] = [
    dict(code='ecg-12lead', name=L('十二导联心电图（新开，模拟）', '12-lead ECG (new, simulated)'),
         aliases={'zh-CN': ['心电图', '十二导联心电图', '导联心电图'], 'en': ['ecg', 'ekg', 'electrocardiogram', '12-lead', '12 lead']},
         acquisition='bedside-device', requires=['ecg-12lead'], turnaroundMinutes=10, reviewer='anaesthetist', historical='ecg-record',
         model=dict(kind='ecg', rhythm=_t('窦性心律', 'sinus rhythm'), prMs=[160, 196], qrsMs=[84, 104], qtcMs=[412, 444], dextrocardia=True)),
    dict(code='cbc', name=L('血常规（新采样，模拟）', 'Full blood count (new sample, simulated)'),
         aliases={'zh-CN': ['血常规', '血细胞计数'], 'en': ['cbc', 'fbc', 'blood count', 'full blood count']},
         acquisition='sample', turnaroundMinutes=30, historical='laboratory-record',
         model=dict(kind='lab', analytes=[
             dict(id='hb', name=L('血红蛋白', 'Haemoglobin'), unit='g/dL', low=13.0, high=17.0, base=13.6, spread=0.3, decimals=1,
                  effects=[dict(when={'procedure': {'injury': 'bleeding'}}, delta=-2.2), dict(when={'procedure': {'injury': 'vascular-injury'}}, delta=-3.5)]),
             dict(id='wbc', name=L('白细胞', 'White cells'), unit='×10⁹/L', low=4.0, high=10.0, base=7.6, spread=0.6, decimals=1),
             dict(id='plt', name=L('血小板', 'Platelets'), unit='×10⁹/L', low=150, high=400, base=214, spread=18, decimals=0)])),
    dict(code='chemistry', name=L('生化（新采样，模拟）', 'Chemistry panel (new sample, simulated)'),
         aliases={'zh-CN': ['生化', '肝功能', '血生化'], 'en': ['chemistry', 'liver function', 'lft', 'biochemistry', 'bilirubin']},
         acquisition='sample', turnaroundMinutes=40, historical='laboratory-record',
         model=dict(kind='lab', analytes=[
             dict(id='tbil', name=L('总胆红素', 'Total bilirubin'), unit='mg/dL', low=0.2, high=1.2, base=0.8, spread=0, decimals=1,
                  effects=[dict(when={'procedure': {'injury': 'bile-duct-injury'}}, delta=1.6)]),
             dict(id='alt', name=L('丙氨酸转氨酶', 'ALT'), unit='U/L', low=7, high=56, base=24, spread=4, decimals=0),
             dict(id='alp', name=L('碱性磷酸酶', 'Alkaline phosphatase'), unit='U/L', low=40, high=129, base=88, spread=8, decimals=0),
             dict(id='creat', name=L('肌酐', 'Creatinine'), unit='mg/dL', low=0.7, high=1.3, base=0.9, spread=0.08, decimals=2),
             dict(id='na', name=L('钠', 'Sodium'), unit='mmol/L', low=135, high=145, base=139, spread=1.5, decimals=0),
             dict(id='k', name=L('钾', 'Potassium'), unit='mmol/L', low=3.5, high=5.1, base=4.2, spread=0.2, decimals=1)])),
    dict(code='cxr', name=L('胸部X线（新拍，模拟）', 'Chest radiograph (new, simulated)'),
         aliases={'zh-CN': ['胸片', '胸部X线', '胸部 X 线'], 'en': ['cxr', 'chest x-ray', 'chest xray', 'chest radiograph']},
         acquisition='department', requires=['xray'], turnaroundMinutes=30, historical='cxr-record',
         model=dict(kind='imaging', technique=_t('后前位立位胸片', 'PA erect chest radiograph'),
                    findings=[dict(id='heart', side='right', text=_t('心影位于患者右侧（右位心）', "cardiac silhouette on the patient's right (dextrocardia)")),
                              dict(id='bubble', side='right', text=_t('胃泡位于患者右侧膈下', "gastric air bubble under the patient's right hemidiaphragm")),
                              dict(id='lungs', text=_t('双肺过度充气，膈肌低平；无局灶实变', 'hyperinflated lungs with flattened hemidiaphragms; no focal consolidation'))])),
]

# 2.4.0: speech follows the anaesthetic — from induction (effective whatever its order) the patient is anaesthetised and
# intubated, and cannot answer: a bedside question gets no answer and earns no history credit; speech returns with
# emergence (extubation decided once the criteria are met) or in recovery
case['patient']['nonVerbalWhen'] = {'all': [{'intervened': 'induction'}, {'not': {'any': [{'decided': 'emergence'}, {'phase': 'recovery'}, {'phase': 'review'}]}}]}
case['patient']['nonVerbalReason'] = L('全身麻醉中（已诱导并气管插管）', 'under general anaesthesia (induced and intubated)')

# ------------------------------------------------------------------ objectives (6)
def obj(id, zh, en, hzh, hen, cond, target='patient', gzh=None, gen=None):
    out = dict(id=id, title=L(zh, en), hint=L(hzh, hen), completeWhen=cond, waypoints=[{'target': target}])
    if gzh:
        out['guidance'] = L(gzh, gen)
    return out

old = {o['id']: o for o in case['objectives']}
case['objectives'] = [
    old['history'],
    old['evidence'],
    obj('plan', '诊断、解剖与计划', 'Diagnosis, anatomy and plan', '先说清楚证据支持什么诊断、器官在哪一侧，再定个体化计划。',
        'State what diagnosis the evidence supports and which side the organs are on, then make an individualised plan.',
        {'all': [{'decided': 'diagnosis'}, {'decided': 'anatomy'}, {'decided': 'planning'}, {'decided': 'safety'}]}, target='board'),
    obj('periop', '术前评估与安全核对', 'Perioperative assessment and checks', '弄清楚高龄、慢阻肺与卒中带来的风险；连接监护，问清过敏与禁食，再做麻醉前核对、诱导和切皮前暂停核对。',
        'Clarify the risks of age, COPD and stroke; attach the monitor and ask about allergies and fasting, then the Sign In, induction and the Time Out.',
        {'all': [{'decided': 'risk'}, {'intervened': 'attach-monitor'}, {'intervened': 'sign-in', 'valid': True}, {'intervened': 'induction'}, {'intervened': 'time-out', 'valid': True}]}, target='board'),
    obj('operate', '完成手术', 'Perform the operation', '布孔、牵拉、解剖到真正的关键安全视野，再夹闭离断；做不到就选择安全的替代方式。结束后决定拔管与进食，再离室核对。',
        'Ports, traction, dissection to a true critical view of safety, then clips and division — or a safe alternative if it cannot be reached. Then decide extubation and oral intake, and the Sign Out.',
        {'all': [{'any': [{'procedure': {'closed': True}}, {'procedure': {'bailout': 'convert-open'}}]}, {'decided': 'emergence'}, {'intervened': 'sign-out', 'valid': True}]}, target='patient'),
    obj('review', '术后与原报告回看', 'Recovery and the reported course', '交接恢复室、定观察重点，再回看原报告的手术、病理和随访。',
        'Hand over in recovery, set what to watch, then review the reported operation, histology and follow-up.',
        {'all': [{'decided': 'postop'}, {'read': 'operation-record'}, {'read': 'pathology-record'}, {'read': 'followup-record'}, {'decided': 'outcome'}]}, target='records'),
]

# ------------------------------------------------------------------ the operation
anatomy = json.loads(ANATOMY.read_text(encoding='utf-8'))


def _points(x):
    """Tubes: their centreline; organs and plates: the centroid first, then their other named anchors."""
    if x['kind'] in ('duct', 'artery', 'vein'):
        return x['centreline']
    anchors = x.get('anchors') or {}
    if 'centroid' in anchors:
        return [anchors['centroid'], *[v for k, v in anchors.items() if k != 'centroid']]
    return x['centreline']


geo = {x['id']: dict(node=x.get('node'), kind=x['kind'], points=_points(x), radius=x['radius'], provenance=x.get('provenance', 'reference'))
       for x in anatomy['structures']}


def pts(id, n=None):
    p = [list(map(lambda v: round(v, 4), q)) for q in geo[id]['points']]
    return p if n is None else p[:n]


def part(id, zh, en, kind, role, *, parent=None, region=None, reveal=None, appears=None, joins=(), enters=None, mesh=True):
    g = geo[id]
    out = dict(id=id, name=L(zh, en), kind=kind, role=role, points=pts(id), radius=round(g['radius'], 4),
               provenance=g.get('provenance', 'reference'))
    if parent:
        out['parent'] = parent
    if region:
        out['in'] = region
    if reveal is not None:
        out['revealAt'] = reveal
    if appears:
        out['appearsAs'] = appears
    if joins:
        out['joins'] = list(joins)
    if enters:
        out['enters'] = enters
    if mesh and g.get('node'):
        out['mesh'] = g['node']
    return out


def looks(zh, en, when=None):
    return {'default': L(zh, en), 'when': when or []}


T = 'hepatocystic-triangle'
gb_parts = [k for k in ('gallbladder-fundus', 'gallbladder-body', 'gallbladder-infundibulum') if k in geo]
structures = [
    part('liver', '肝脏（位于患者左上腹）', 'Liver (in the patient\'s left upper abdomen)', 'organ', 'organ'),
    part('gallbladder', '胆囊', 'Gallbladder', 'organ', 'specimen'),
    *[part(k, {'gallbladder-fundus': '胆囊底', 'gallbladder-body': '胆囊体', 'gallbladder-infundibulum': '胆囊颈（漏斗部）'}[k],
           {'gallbladder-fundus': 'Fundus of the gallbladder', 'gallbladder-body': 'Body of the gallbladder', 'gallbladder-infundibulum': 'Neck (infundibulum) of the gallbladder'}[k],
           'organ', 'specimen', parent='gallbladder', mesh=False) for k in gb_parts],
    part('cystic-plate', '胆囊板', 'Cystic plate', 'plate', 'landmark', region='cystic-plate', reveal=0.5),
    part('duodenum', '十二指肠', 'Duodenum', 'organ', 'organ'),
    part('stomach', '胃（位于患者右侧）', 'Stomach (on the patient\'s right)', 'organ', 'organ'),
    part('spleen', '脾（位于患者右上腹）', 'Spleen (in the patient\'s right upper abdomen)', 'organ', 'organ'),
    part('cystic-duct', '胆囊管', 'Cystic duct', 'duct', 'target', region=T, reveal=0.5, joins=('common-hepatic-duct', 'common-bile-duct'),
         enters='gallbladder-infundibulum' if 'gallbladder-infundibulum' in geo else 'gallbladder',
         appears=looks('一根约3 mm的管道，从胆囊颈发出，走向肝十二指肠韧带', 'a duct about 3 mm across leaving the gallbladder neck towards the hepatoduodenal ligament')),
    part('cystic-artery', '胆囊动脉', 'Cystic artery', 'artery', 'target', region=T, reveal=0.6, joins=('right-hepatic-artery',), enters='gallbladder',
         appears=looks('一根细小、搏动的血管，向上走到胆囊颈和胆囊壁', 'a thin pulsating vessel running up onto the gallbladder neck and wall')),
    part('common-bile-duct', '胆总管', 'Common bile duct', 'duct', 'critical', region=T, reveal=0.2, joins=('common-hepatic-duct', 'cystic-duct'),
         appears=looks('一根较粗的管道，在肝十二指肠韧带内向下走行', 'a wider duct running down in the hepatoduodenal ligament',
                       [dict(exposure=T, below=0.5, text=L('一根似乎直接汇入胆囊颈的管道', 'a duct that seems to run straight into the gallbladder neck'), appearsToEnter='gallbladder')])),
    part('common-hepatic-duct', '肝总管', 'Common hepatic duct', 'duct', 'critical', region=T, reveal=0.9, joins=('right-hepatic-duct', 'left-hepatic-duct', 'common-bile-duct'),
         appears=looks('一根从肝门向下走行的管道', 'a duct coming down from the liver hilum')),
    part('right-hepatic-artery', '肝右动脉（供应形态学右叶，本例位于患者左侧）', 'Right hepatic artery (to the morphological right lobe, on the patient\'s left here)',
         'artery', 'critical', region=T, reveal=1.0, joins=('proper-hepatic-artery',),
         appears=looks('一根在深部走向肝脏的动脉', 'an artery running deep towards the liver')),
    part('proper-hepatic-artery', '肝固有动脉', 'Proper hepatic artery', 'artery', 'critical', region='hepatoduodenal-ligament', reveal=0.5,
         joins=('common-hepatic-artery',), appears=looks('肝十二指肠韧带内一根搏动的动脉', 'a pulsating artery in the hepatoduodenal ligament')),
    part('portal-vein', '门静脉', 'Portal vein', 'vein', 'critical', region='hepatoduodenal-ligament', reveal=1.0,
         appears=looks('韧带后方一根粗大、发蓝的静脉', 'a large bluish vein behind the ligament')),
    part('common-hepatic-artery', '肝总动脉', 'Common hepatic artery', 'artery', 'critical', region='hepatoduodenal-ligament', reveal=1.0,
         appears=looks('韧带下方深处一根搏动的动脉', 'a pulsating artery deep below the ligament')),
    part('gastroduodenal-artery', '胃十二指肠动脉', 'Gastroduodenal artery', 'artery', 'critical', region='hepatoduodenal-ligament', reveal=1.0,
         joins=('common-hepatic-artery',), appears=looks('向十二指肠后方走行的一根动脉', 'an artery running down behind the duodenum')),
    part('right-hepatic-duct', '右肝管（形态学右叶，本例位于患者左侧）', 'Right hepatic duct (morphological right lobe, on the patient\'s left here)',
         'duct', 'critical', region='hepatoduodenal-ligament', reveal=1.0, appears=looks('肝门处的一根胆管分支', 'a bile duct branch at the hilum')),
    part('left-hepatic-duct', '左肝管', 'Left hepatic duct', 'duct', 'critical', region='hepatoduodenal-ligament', reveal=1.0,
         appears=looks('肝门处的另一根胆管分支', 'another bile duct branch at the hilum')),
]
ports = {p['id']: dict(at=p['point'], normal=p['normal']) for p in anatomy['ports']}


def site(id, zh, en):
    p = ports[id]
    return dict(id=id, name=L(zh, en), at=[round(v, 4) for v in p['at']], normal=[round(v, 4) for v in p['normal']])


regions = {r['id']: r for r in anatomy['regions']}


def region(id, zh, en, units, **kw):
    r = regions[id]
    return dict(id=id, name=L(zh, en), units=units, centre=[round(v, 4) for v in r['centre']], radius=round(r['radius'], 4), **kw)


hd_centre = [round((a + b) / 2, 4) for a, b in zip(geo['proper-hepatic-artery']['points'][0], geo['common-bile-duct']['points'][-1])]
case['procedure'] = dict(
    id='lap-chole-sit', name=L('全内脏反位腹腔镜胆囊切除术', 'Laparoscopic cholecystectomy in situs inversus totalis'),
    phases=['operation'], specimen='gallbladder', stones=True,
    target=[round(v, 4) for v in regions[T]['centre']],
    anatomy=structures,
    regions=[
        region(T, '胆囊三角（肝胆囊三角）', 'Hepatocystic triangle', 6,
               exposure=[dict(structure='gallbladder-infundibulum' if 'gallbladder-infundibulum' in geo else 'gallbladder', direction=['patient-left', 'caudal'])],
               hazards=['common-bile-duct', 'common-hepatic-duct', 'right-hepatic-artery']),
        region('cystic-plate', '胆囊下三分之一与胆囊板之间', 'Lower third of the gallbladder off the cystic plate', 3, after=[T],
               exposure=[dict(structure='gallbladder-infundibulum' if 'gallbladder-infundibulum' in geo else 'gallbladder', direction=['patient-left', 'anterior'], full=0.6)]),
        region('gallbladder-bed', '胆囊床（其余部分）', 'Rest of the gallbladder bed', 5, after=['cystic-plate'], bed=True,
               exposure=[dict(structure='gallbladder-infundibulum' if 'gallbladder-infundibulum' in geo else 'gallbladder', direction=['anterior', 'cephalad'], full=0.6)]),
        dict(id='hepatoduodenal-ligament', name=L('肝十二指肠韧带', 'Hepatoduodenal ligament'), units=4, centre=hd_centre, radius=0.02,
             hazards=['common-bile-duct', 'proper-hepatic-artery', 'portal-vein']),
    ],
    portSites=[
        site('A', '脐下缘1 cm（观察孔）', '1 cm below the umbilicus (camera port)'),
        site('B', '剑突下偏左', 'Below the xiphoid, slightly left'),
        site('C', '左锁骨中线肋缘下2 cm', 'Left midclavicular line, 2 cm below the costal margin'),
        site('D', '左腋前线肋缘下', 'Left anterior axillary line, below the costal margin'),
        site('E', '剑突下偏右', 'Below the xiphoid, slightly right'),
        site('G', '右锁骨中线肋缘下2 cm', 'Right midclavicular line, 2 cm below the costal margin'),
        site('H', '右腋前线肋缘下', 'Right anterior axillary line, below the costal margin'),
    ],
    portPlans=[
        dict(id='three-port-left', name=L('原报告的三孔法：术者与助手位于患者左侧', 'The report\'s three ports: surgeon and assistant on the patient\'s left'),
             surgeonSide='left', provenance='published-case',
             note=L('原文：A孔脐下缘1 cm置10 mm Trocar（观察孔）；B孔剑突下偏左、C孔左锁骨中线肋下2 cm（主操作孔），均为5 mm。术者在体外交叉双手操作。',
                    'Source: port A 1 cm below the umbilicus, 10 mm (camera); B below the xiphoid slightly left and C at the left midclavicular line 2 cm below the costal margin (main port), both 5 mm. The surgeon worked with crossed hands.'),
             ports=[dict(site='A', role='camera', sizeMm=10), dict(site='B', role='working', sizeMm=5, hand='left'), dict(site='C', role='working', sizeMm=5, hand='right')]),
        dict(id='mirror-four-port', name=L('镜像四孔法：术者位于患者右侧', 'Mirrored four ports: surgeon on the patient\'s right'),
             surgeonSide='right', provenance='authored',
             note=L('常规四孔布局的镜像，作为对照方案；不是原报告的做法。', 'The usual four-port layout mirrored, as a comparison; not what the report did.'),
             ports=[dict(site='A', role='camera', sizeMm=10), dict(site='B', role='working', sizeMm=5, hand='left'),
                    dict(site='C', role='working', sizeMm=5, hand='right'), dict(site='D', role='assist', sizeMm=5)]),
        dict(id='habitual', name=L('按常规解剖布孔（未考虑反位）', 'Ports placed for usual anatomy (situs not considered)'),
             surgeonSide='left', provenance='authored',
             note=L('常见错误：沿用右侧胆囊的布孔。', 'A common error: the ports used for a right-sided gallbladder.'),
             ports=[dict(site='A', role='camera', sizeMm=10), dict(site='E', role='working', sizeMm=5, hand='right'),
                    dict(site='G', role='working', sizeMm=5, hand='left'), dict(site='H', role='assist', sizeMm=5)]),
    ],
    instruments=[dict(id='laparoscope'), dict(id='grasper'), dict(id='maryland'), dict(id='hook'), dict(id='scissors'),
                 dict(id='clip-applier'), dict(id='suction'), dict(id='retrieval-bag', diameterMm=5), dict(id='cholangiocatheter')],
    views=[dict(id='cvs', name=L('关键安全视野', 'Critical view of safety'), criteria=[
        dict(id='triangle', name=L('胆囊三角内脂肪和纤维组织已清除', 'Hepatocystic triangle cleared of fat and fibrous tissue'), test={'cleared': T, 'atLeast': 1}),
        dict(id='plate', name=L('胆囊下三分之一已与肝床分离，可见胆囊板', 'Lower third of the gallbladder separated from the liver, cystic plate seen'), test={'cleared': 'cystic-plate', 'atLeast': 1}),
        # the operator reports how many structures they see entering (usually two): "two" is credited only when two
        # truly enter — with a second cystic artery the right report is three (review by hepatobiliary surgeons pending)
        dict(id='entering', name=L('进入胆囊的结构：通常两根，均已游离一周，且无其他结构看似进入', 'Structures entering the gallbladder: usually two, each free all round, nothing else appearing to enter'),
             test={'onlyEntering': 'gallbladder', 'count': 2}),
    ])],
    bailouts=['call-help', 'subtotal-fenestrating', 'subtotal-reconstituting', 'convert-open'],
    insufflation={'usual': 12, 'max': 15},
    note=L('参考解剖：BodyParts3D器官表面（已镜像）与 Layered Human 程序化肝胆树（MIT，镜像一次后配准）；不是患者影像重建。原报告术中“未发现血管解剖变异”。',
           'Reference anatomy: BodyParts3D organ surfaces (mirrored) and the Layered Human procedural hepatobiliary tree (MIT, mirrored once and registered); not a reconstruction from the patient\'s imaging. At operation the source found "no vascular anatomical variation".'),
)
# ------------------------------------------------------------------ anatomical variants (counterfactual; hidden from the operator)
# The source found "no vascular anatomical variation". These variants are what the anatomy *could* have been: authored
# on the reference geometry (patient frame, m), each for teaching and the operative benchmark (content/operative/case126-v1).
# None is presented as the patient's anatomy. References describe the variant and its surgical significance, not this patient.
REF_CYSTIC_ARTERY = 'Andall RG, Matusz P, du Plessis M, Ward R, Tubbs RS, Loukas M. The clinical anatomy of cystic artery variations: a review of over 9800 cases. Surg Radiol Anat. 2016;38(5):529-539.'
REF_HUMP = 'Marano L, Bartoli A, Polom K, et al. The unwanted third wheel in the Calot\'s triangle: incidence and surgical significance of caterpillar hump of right hepatic artery with a systematic review of the literature. J Minim Access Surg. 2019;15(3):185-191.'
REF_SUBVESICAL = 'Schnelldorfer T, Sarr MG, Adams DB. What is the duct of Luschka? A systematic review. J Gastrointest Surg. 2012;16(3):656-662.'
REF_STRASBERG = 'Strasberg SM, Hertl M, Soper NJ. An analysis of the problem of biliary injury during laparoscopic cholecystectomy. J Am Coll Surg. 1995;180(1):101-125.'
REF_TG18_SAFE = 'Wakabayashi G, Iwashita Y, Hibi T, et al. Tokyo Guidelines 2018: surgical management of acute cholecystitis: safe steps in laparoscopic cholecystectomy for acute cholecystitis (with videos). J Hepatobiliary Pancreat Sci. 2018;25(1):73-86.'
REF_SUBTOTAL = 'Strasberg SM, Pucci MJ, Brunt LM, Deziel DJ. Subtotal cholecystectomy - "fenestrating" vs "reconstituting" subtypes and the prevention of bile duct injury: definition of the optimal procedure in difficult operative conditions. J Am Coll Surg. 2016;222(1):89-96.'
REF_SAGES = 'Brunt LM, Deziel DJ, Telem DA, et al. Safe cholecystectomy multi-society practice guideline and state-of-the-art consensus conference on prevention of bile duct injury during cholecystectomy. Surg Endosc. 2020;34(7):2827-2855.'


def vtube(id, zh, en, kind, role, points, radius, *, region, reveal, appears, joins=(), enters=None, crosses=None, note=None):
    """A duct or vessel of a variant: authored centreline (patient frame, m), no model node (the window draws it)."""
    out = dict(id=id, name=L(zh, en), kind=kind, role=role, points=[[round(v, 4) for v in q] for q in points], radius=radius,
               provenance='authored', **{'in': region}, revealAt=reveal, appearsAs=appears)
    if joins:
        out['joins'] = list(joins)
    if enters:
        out['enters'] = enters
    if crosses:
        out['crosses'] = crosses
    if note:
        out['note'] = note
    return out


def base_structure(id):
    return next(x for x in structures if x['id'] == id)


# the right hepatic artery's own course, for the hump (origin and its hilar end kept)
_rha = base_structure('right-hepatic-artery')['points']
case['procedure']['variants'] = [
    dict(id='double-cystic-artery', name=L('双胆囊动脉', 'Double cystic artery'),
         summary=L('除胆囊三角内的胆囊动脉（前支）外，另有一支后支自肝右动脉发出，沿胆囊板走到胆囊后壁，并穿过胆囊床。关键安全视野要求它也游离可见；只处理两根结构即离断，完成胆囊床剥离时会撕断后支而出血。',
                   'Besides the cystic artery in the triangle (the anterior branch), a posterior branch leaves the right hepatic artery, runs on the cystic plate to the back of the gallbladder and crosses the bed. The critical view needs it free and seen too; dividing only two structures leaves it to be torn, and bleed, when the bed is completed.'),
         provenance='authored', references=[REF_CYSTIC_ARTERY, REF_SAGES],
         anatomy=[vtube('posterior-cystic-artery', '胆囊动脉后支', 'Posterior cystic artery', 'artery', 'target',
                        [[0.0544, 0.1068, 0.0096], [0.0590, 0.1010, 0.0125], [0.0630, 0.0940, 0.0170], [0.0670, 0.0870, 0.0215], [0.0705, 0.0800, 0.0270]], 0.0008,
                        region='cystic-plate', reveal=0.6, joins=('right-hepatic-artery',), enters='gallbladder', crosses='gallbladder-bed',
                        appears=looks('第二根细小、搏动的血管，从胆囊颈后方走上胆囊后壁', 'a second thin pulsating vessel running up behind the neck onto the back of the gallbladder'))]),
    dict(id='caterpillar-hump', name=L('肝右动脉“毛虫驼峰”', 'Caterpillar hump of the right hepatic artery'),
         summary=L('肝右动脉迂曲成袢进入胆囊三角，紧贴胆囊颈，再折回肝门；胆囊动脉很短，自袢顶发出。三角未完全清空前，这根动脉看起来像进入胆囊颈的血管；把它当作胆囊动脉夹闭即为血管损伤。',
                   'The right hepatic artery loops into the triangle close to the gallbladder neck and turns back to the hilum; the cystic artery is short and leaves the top of the loop. Until the triangle is fully cleared the loop looks like a vessel entering the neck; clipping it as the cystic artery is a vascular injury.'),
         provenance='authored', references=[REF_HUMP, REF_CYSTIC_ARTERY],
         anatomy=[
             vtube('right-hepatic-artery', '肝右动脉（供应形态学右叶，本例位于患者左侧）', 'Right hepatic artery (to the morphological right lobe, on the patient\'s left here)', 'artery', 'critical',
                   [_rha[0], [0.0430, 0.0995, 0.0150], [0.0490, 0.0950, 0.0190], [0.0540, 0.0985, 0.0160], [0.0575, 0.1045, 0.0115], _rha[-1]], 0.0016,
                   region=T, reveal=0.4, joins=('proper-hepatic-artery',),
                   appears=looks('一根迂曲、搏动的动脉，向前绕到胆囊颈旁，再折回肝脏', 'a tortuous pulsating artery that loops forward close to the gallbladder neck and turns back into the liver',
                                 [dict(cleared=T, below=1, text=L('一根较粗、搏动的动脉，似乎走向胆囊颈', 'a sizeable pulsating artery that seems to run up to the gallbladder neck'), appearsToEnter='gallbladder')])),
             vtube('cystic-artery', '胆囊动脉', 'Cystic artery', 'artery', 'target',
                   [[0.0490, 0.0950, 0.0190], [0.0540, 0.0925, 0.0240], [0.0600, 0.0895, 0.0300], [0.0644, 0.0876, 0.0360]], 0.0008,
                   region=T, reveal=0.85, joins=('right-hepatic-artery',), enters='gallbladder',
                   appears=looks('一根很短的细小血管，从绕行的动脉发出走向胆囊壁', 'a short thin vessel leaving the looping artery for the gallbladder wall')),
         ]),
    dict(id='aberrant-posterior-duct', name=L('迷走右后叶胆管', 'Aberrant right posterior sectoral duct'),
         summary=L('右后叶胆管单独穿过胆囊三角，在胆囊管汇合处附近低位汇入肝总管。三角未完全清空前，它看起来像进入胆囊颈后方的第三根管道；把它当作胆囊管夹闭或离断即为胆管损伤（Strasberg B/C型）。',
                   'The right posterior sectoral duct crosses the triangle on its own and joins the common hepatic duct low, near the cystic confluence. Until the triangle is fully cleared it looks like a third duct entering the back of the neck; clipping or dividing it as the cystic duct is a bile duct injury (Strasberg type B or C).'),
         provenance='authored', references=[REF_STRASBERG, REF_SAGES],
         anatomy=[vtube('aberrant-right-posterior-duct', '迷走右后叶胆管', 'Aberrant right posterior sectoral duct', 'duct', 'critical',
                        [[0.0640, 0.1090, 0.0085], [0.0575, 0.1005, 0.0105], [0.0515, 0.0925, 0.0120], [0.0480, 0.0860, 0.0130], [0.0466, 0.0840, 0.0131]], 0.0011,
                        region=T, reveal=0.45, joins=('common-hepatic-duct',),
                        appears=looks('一根约2 mm的管道，从胆囊颈后方的肝脏发出，向下走向肝总管', 'a duct about 2 mm across coming out of the liver behind the gallbladder neck and running down to the common duct',
                                      [dict(cleared=T, below=1, text=L('一根细小的管道，似乎进入胆囊颈后方', 'a small duct that seems to run into the back of the gallbladder neck'), appearsToEnter='gallbladder')]))]),
    dict(id='hostile-triangle', name=L('胆囊三角致密纤维化（“冰冻”三角）', 'Dense fibrosis of the triangle (a "frozen" triangle)'),
         summary=L('严重慢性炎症使胆囊三角致密纤维化：解剖到一半层次就分不开，关键安全视野无法安全建立。继续分离会撕裂胆总管；正确的做法是停下来，选择胆囊次全切除（开窗式或重建式）或中转开腹。与原报告（无粘连）相反，属于假设情境。',
                   'Severe chronic inflammation has left the triangle densely fibrotic: halfway through, the planes stop separating and the critical view cannot be reached safely. Dissecting on tears the common bile duct; the right course is to stop and choose a subtotal cholecystectomy (fenestrating or reconstituting) or conversion. Counterfactual: the report found no adhesions.'),
         provenance='authored', references=[REF_TG18_SAFE, REF_SUBTOTAL, REF_SAGES],
         regions=[dict(id=T, fibrosis=dict(safeTo=0.5, injures='common-bile-duct',
                                           finding=L('致密、质硬的纤维化组织：层次分不开，任何结构都无法安全游离', 'dense, woody fibrosis: the tissue planes do not separate and nothing can be freed safely')))]),
    dict(id='subvesical-duct', name=L('胆囊床内的胆囊下胆管', 'A subvesical duct in the gallbladder bed'),
         summary=L('一根细小的胆囊下胆管（旧称Luschka管）在胆囊床内紧贴肝面走行，汇入右肝管系统。它不进入胆囊，不影响关键安全视野；剥离胆囊床时出现后应先夹闭，否则完成剥离会把它撕断，造成胆漏。',
                   'A fine subvesical duct (formerly "duct of Luschka") runs in the gallbladder bed against the liver and drains into the right hepatic duct system. It does not enter the gallbladder, so the critical view is unaffected; once it appears during the bed dissection it should be clipped, or completing the dissection divides it and bile leaks.'),
         provenance='authored', references=[REF_SUBVESICAL],
         anatomy=[vtube('subvesical-duct', '胆囊下胆管（Luschka管）', 'Subvesical bile duct (duct of Luschka)', 'duct', 'target',
                        [[0.0700, 0.0850, 0.0300], [0.0745, 0.0790, 0.0370], [0.0790, 0.0725, 0.0440], [0.0830, 0.0665, 0.0505]], 0.0008,
                        region='gallbladder-bed', reveal=0.4, joins=('right-hepatic-duct',), crosses='gallbladder-bed',
                        appears=looks('胆囊床内一根很细的管道，紧贴肝面', 'a fine duct running in the gallbladder bed, close to the liver surface'))]),
]
VARIANT_IDS = [v['id'] for v in case['procedure']['variants']]

# ------------------------------------------------------------------ the care team of OR 7 (docs/TEAM.md in ClinicalCraft)
# Two named nurses work on their own during the operation: the circulating nurse notices what is needed, asks the
# right colleague and checks the result with her own eyes; the scrub nurse reads a request back, finds the
# instrument, brings it and hands it over. A scenario sets up only the conditions (a need, a colleague on a break,
# an instrument somewhere else) and never the steps; it is chosen at start (`start {team}`) and hidden from the team.
NEEDLE_HOLDER = dict(id='needle-holder', item='sc-needle-holder', **{'for': 'surgeon'}, name=L('持针器', 'needle holder'))
case['team'] = dict(
    room='or-7', phases=['operation'], waitRounds=3,
    # the closing count, item by item: due once the specimen is out; the circulating nurse searches the same places
    # whatever happened (nothing points to where a swab is): the floor round the Mayo stand, the back table and the
    # laparoscopy tower
    count=dict(item='sc-gauze-swab', name=L('纱布', 'swabs'), when={'procedure': {'specimen': 'extracted'}},
               searchPlaces=['or-7.mayo', 'or-7.back-table', 'or-7.lap-tower']),
    members=[dict(staff='or-7.circulating-nurse', duties=['circulate']),
             dict(staff='or-7.scrub-nurse', duties=['instruments', 'count']),
             dict(staff='or-7.anaesthetist', duties=['anaesthesia']),
             dict(staff='surgeon', duties=['surgeon'])],
    # who takes over the anaesthetic if Dr Tanaka has to leave during the case: the duty consultant anaesthetist
    # (theatre control) comes to the patient first, the hand-over is recorded, then Dr Tanaka goes
    cover=[dict(staff='l1-anaesthetist', duties=['anaesthesia'])],
    note=L('团队情境是教学材料（编写），不是原病例报告的内容；它们只设定初始条件，不规定步骤。',
           'Team scenarios are teaching material (authored), not part of the case report; they set initial conditions only, never the steps.'),
    scenarios=[
        dict(id='needle-holder', name=L('术者需要持针器', 'The surgeon needs a needle holder'),
             summary=L('关闭脐部筋膜时术者需要持针器。巡回护士听到后要决定请谁去拿、核对复述，并亲眼确认持针器到了术者手里；洗手护士要找到持针器、拿起、走到术者旁边递交。没有人告诉她们怎么做。',
                       'To close the fascia at the umbilical port the surgeon needs a needle holder. The circulating nurse has to decide whom to ask, check the read-back and see for herself that the surgeon holds it; the scrub nurse has to find it, pick it up, reach the surgeon and hand it over. Nobody tells them how.'),
             provenance='authored', needs=[NEEDLE_HOLDER], expect=dict(delivered=True)),
        dict(id='scrub-on-break', name=L('洗手护士休息，隔壁同事顶班', 'Scrub nurse on a break, a colleague from next door'),
             summary=L('同样需要持针器，但林护士正在休息。巡回护士应改请可以顶班的同事——6号手术间的拉曼护士（电话联系）；她要先走进7号手术间，再找持针器并递交。',
                       'The same need, but Nurse Lim is on a break. The circulating nurse should turn to the colleague who can relieve — Nurse Rahman from OR 6 (by phone), who has to walk into OR 7, find the needle holder and hand it over.'),
             provenance='authored', needs=[NEEDLE_HOLDER], absent=['or-7.scrub-nurse'], relief=[dict(staff='or-6.scrub-nurse', duties=['instruments'])], expect=dict(delivered=True)),
        dict(id='needle-holder-moved', name=L('持针器不在器械台上', 'The needle holder is not on the back table'),
             summary=L('持针器被留在了 Mayo 托盘上，而不是无菌器械台。洗手护士要凭自己看到的找到它，而不是去它通常放的地方。',
                       'The needle holder was left on the Mayo stand, not on the back table. The scrub nurse has to find it by what she sees, not where it is usually kept.'),
             provenance='authored', needs=[NEEDLE_HOLDER], items=[dict(placement='or-7.needle-holder', beside='or-7.mayo')], expect=dict(delivered=True)),
        dict(id='needle-holder-missing', name=L('手术间里没有持针器', 'No needle holder in the room'),
             summary=L('7号手术间的持针器被拿到了6号手术间。洗手护士在本间找不到，应说明原因；巡回护士没有别人可派时，应向术者说明情况，而不是假装已经解决。',
                       'OR 7\'s needle holder went to OR 6. The scrub nurse cannot find one in the room and should say so; with nobody else to send, the circulating nurse should tell the surgeon, not pretend it is solved.'),
             provenance='authored', needs=[NEEDLE_HOLDER], items=[dict(placement='or-7.needle-holder', beside='or-6.back-table')], expect=dict(delivered=False)),
        # the closing count (one swab of five unaccounted for, or none: the control)
        dict(id='count-correct', name=L('关闭前清点：全部在位（对照）', 'Closing count: every swab accounted for (control)'),
             summary=L('五块纱布都在 Mayo 托盘上。清点应一次无误，不应要求暂停关闭（衡量“误停”）。',
                       'All five swabs are on the Mayo tray. The count should be correct the first time, with no hold on closure (it measures false holds).'),
             provenance='authored', expect=dict(count='correct')),
        dict(id='swab-on-floor', name=L('一块纱布掉在 Mayo 托盘下', 'A swab dropped under the Mayo stand'),
             summary=L('第五块纱布掉到 Mayo 托盘下的地上，被布单边遮住。清点发现少一块：请术者暂停关闭并检查术野（需复述确认），巡回护士按固定顺序在手术间里找，找到后复点无误，可以关闭。',
                       'The fifth swab fell to the floor under the Mayo stand, hidden by the drape\'s edge. The count finds one short: the surgeon is asked to hold closure and check the wound (read back), the circulating nurse searches the room in her fixed order, finds it, and the recount is correct: closure may go ahead.'),
             provenance='authored', items=[dict(placement='or-7-swab-5', beside='or-7.mayo', concealed=True)], expect=dict(count='reconciled')),
        dict(id='swab-in-wound', name=L('一块纱布留在术野里', 'A swab left in the wound'),
             summary=L('第五块纱布留在患者腹腔内（肝下间隙）。巡回护士在手术间里找不到；只有术者检查术野才能找到。找到后复点无误。',
                       'The fifth swab is still in the abdomen (under the liver). The circulating nurse will not find it in the room; only the surgeon\'s check of the wound does. Once it is out, the recount is correct.'),
             provenance='authored', items=[dict(placement='or-7-swab-5', beside='patient', inside=True)], expect=dict(count='reconciled')),
        dict(id='swab-gone', name=L('一块纱布找不到', 'A swab that cannot be found'),
             summary=L('第五块纱布已随布类离开手术间（在 6 号手术间）。全面查找和复点后仍少一块：应向术者说明，患者离开前拍 X 线片——不能假装已经解决。',
                       'The fifth swab left the room with the linen (it is in OR 6). After the search and the recount it is still one short: the surgeon should be told and an X-ray taken before the patient leaves — not pretended solved.'),
             provenance='authored', items=[dict(placement='or-7-swab-5', beside='or-6.back-table', concealed=True)], expect=dict(count='unresolved')),
        # 2.4.0: the count is kept by item identity — a number that comes out right is not enough
        dict(id='swab-extra', name=L('多出一块纱布（6 块对 5 块）', 'One swab too many (six of five)'),
             summary=L('6 号手术间的一块纱布混到了 7 号手术间的 Mayo 托盘上。清点到 6 块：多出的一块不在本次清点内，不能算“相符”。巡回护士应请术者暂停关闭，把这块纱布移出手术野并记录，再复点。',
                       'A swab from OR 6 ended up on OR 7\'s Mayo tray. The count finds six: the extra one is not in this count, and six of five is not "correct". The circulating nurse should ask the surgeon to hold closure, take that swab off the field and document it, then recount.'),
             provenance='authored', items=[dict(placement='or-6-swab-1', beside='or-7.mayo')], expect=dict(count='reconciled')),
        dict(id='swab-substituted', name=L('数目对但不是同一批纱布（假 5/5）', 'Five of five, but not the same five'),
             summary=L('第五块纱布留在患者腹腔内，而 6 号手术间的一块纱布混到了 Mayo 托盘上：数目仍是 5 块。逐件核对发现第五块缺失、另一块不在清点内——必须请术者暂停关闭、检查术野，找到后把多出的一块移出并复点。',
                       'The fifth swab is still in the abdomen, and a swab from OR 6 is on the Mayo tray: the number is still five. Counting item by item finds the fifth missing and one not in the count — the surgeon must hold closure and check the wound; once it is out and the extra one is set aside, the recount is correct.'),
             provenance='authored', items=[dict(placement='or-7-swab-5', beside='patient', inside=True), dict(placement='or-6-swab-1', beside='or-7.mayo')], expect=dict(count='reconciled')),
        dict(id='swab-with-specimen', name=L('一块纱布随标本送检（已记录，对照）', 'A swab sent with the specimen (documented — the control)'),
             summary=L('第五块纱布随标本送到冰冻切片室，巡回护士已在清点中记录。清点 4 块即与记录相符：有记录的转移不是缺失，不应要求暂停关闭（衡量“误停”）。',
                       'The fifth swab went to the frozen-section lab with the specimen, and the circulating nurse documented it in the count. Four counted agrees with the record: a documented transfer is not a missing swab, and there should be no hold on closure (it measures false holds).'),
             provenance='authored',
             items=[dict(placement='or-7-swab-5', beside='frozen-lab.bench',
                         transfer=dict(to=L('随标本送冰冻切片室', 'with the specimen to the frozen-section lab'), reason=L('标本送检时一并送出', 'sent with the specimen')))],
             expect=dict(count='correct')),
    ],
)

case['assets'] = [dict(id='anatomy', kind='model', path=f'assets/cases/{CASE_ID}/anatomy.glb',
                       title=L('病例126参考解剖（全内脏反位）', 'Case 126 reference anatomy (situs inversus totalis)'),
                       credit=L('BodyParts3D © DBCLS（CC BY 4.0）；Layered Human 肝胆模型 © 2026 Ethan Prince（MIT）；SurgeryCraft 改编',
                                'BodyParts3D © DBCLS (CC BY 4.0); Layered Human hepatobiliary model © 2026 Ethan Prince (MIT); adapted by SurgeryCraft'),
                       license='CC-BY-4.0 AND MIT')]

# ------------------------------------------------------------------ synthetic physiology (labelled)
def ev(id, when, vitals, zh, en, severity='info'):
    return dict(id=id, when=when, setVitals=vitals, severity=severity, speaker='narrator', message=L(zh + SYNTH['zh-CN'], en + SYNTH['en']))

case['physiology'] = dict(
    baseline=dict(hr=78, sbp=128, dbp=78, rr=19, spo2=95, temp=36.6),
    noise=1,
    monitor=dict(attachedWhen={'intervened': 'attach-monitor'}, spotChecks=['hr', 'sbp', 'dbp', 'rr', 'temp']),
    events=[
        ev('ev-ventilated', {'intervened': 'induction'}, dict(rr=12, etco2=36, spo2=97), '麻醉医生：已插管并机械通气，呼末二氧化碳36 mmHg', 'Anaesthetist: intubated and ventilated, end-tidal CO₂ 36 mmHg'),
        ev('ev-pneumo', {'procedure': {'insufflated': True}}, dict(etco2=40), '麻醉医生：气腹建立后呼末二氧化碳升至40 mmHg', 'Anaesthetist: end-tidal CO₂ up to 40 mmHg with the pneumoperitoneum'),
        ev('ev-high-pressure', {'procedure': {'insufflated': True, 'pressure': {'gte': 15}}}, dict(etco2=48, spo2=92, sbp=110, dbp=66),
           '麻醉医生：气腹压力高，慢阻肺患者呼末二氧化碳48 mmHg、血氧92%——能否降低气腹压力？', 'Anaesthetist: high insufflation pressure in a COPD patient — end-tidal CO₂ 48 mmHg, SpO₂ 92%. Can we lower the pressure?', 'warning'),
        ev('ev-major-bleeding', {'procedure': {'bleeding': 'major'}}, dict(hr=114, sbp=92, dbp=56), '麻醉医生：心率114次/min，血压92/56 mmHg——出血多少？', 'Anaesthetist: heart rate 114, BP 92/56 — how much bleeding?', 'critical'),
        ev('ev-closed', {'procedure': {'closed': True}}, dict(etco2=37, spo2=96), '麻醉医生：气腹已放，呼末二氧化碳回到37 mmHg', 'Anaesthetist: pneumoperitoneum released, end-tidal CO₂ back to 37 mmHg'),
    ],
)

# ------------------------------------------------------------------ rubric: one record across reasoning and operating (weights per domain, docs/CASE_126.md)
def item(id, domain, weight, zh, en, met, critical=False, scored=None):
    out = dict(id=id, domain=domain, weight=weight, text=L(zh, en), met=met)
    if critical:
        out['critical'] = True
    if scored:
        out['scoredWhen'] = scored
    return out


P = lambda **kw: {'procedure': kw}
IRREVERSIBLE_UNSAFE = [P(unsafe=u) for u in ('irreversible-without-pause', 'irreversible-without-view', 'irreversible-on-misidentified', 'irreversible-on-unidentified')]
OPERATED = P(counter='steps', gte=8)
# the operation was open to be done (a valid Time Out): from then on its outcome items are scored — a run that never
# enters the field (counts, devices, the wrong tool) loses them, instead of leaving them unscored (2.3.0)
OPENED = {'intervened': 'time-out', 'valid': True}
# a clip or a division on a duct or vessel: the critical view is owed from then on (a bail-out with nothing clipped is not unsafe)
IRREVERSIBLE_ON = ('cystic-duct', 'cystic-artery', 'common-bile-duct', 'common-hepatic-duct', 'right-hepatic-artery',
                   'posterior-cystic-artery', 'aberrant-right-posterior-duct')
IRREVERSIBLE_DONE = [P(clipped=x) for x in IRREVERSIBLE_ON] + [P(divided=x) for x in IRREVERSIBLE_ON]
DIVIDED_TARGET = {'any': [P(divided='cystic-duct'), P(divided='cystic-artery')]}
BAILED_SAFELY = [P(bailout='subtotal-fenestrating'), P(bailout='subtotal-reconstituting'), P(bailout='convert-open')]
case['rubric'] = [
    # clinical history and diagnostic reasoning — 15
    item('r-presentation', 'history', 3, '询问主诉与病程', 'Presenting complaint and duration', {'asked': 'presentation'}),
    item('r-pmh', 'history', 3, '询问既往病史', 'Past medical history', {'asked': 'pmh'}),
    item('r-allergy', 'safety', 2, '询问过敏史（未记录即为未知）', 'Allergies (unrecorded means unknown)', {'asked': 'allergies'}),
    item('r-exam', 'examination', 2, '查心尖搏动与腹部', 'Apex beat and abdomen examined', {'all': [{'examined': 'apex'}, {'examined': 'palpation'}]}),
    item('r-diagnosis', 'diagnosis', 5, '诊断表述与证据相符（疑似而非确诊）', 'Diagnosis matches the evidence (suspected, not confirmed)', {'decidedFirstTry': 'diagnosis'}),
    # preoperative assessment and planning — 10
    item('r-ct', 'investigations', 2, '查阅CT', 'CT reviewed', {'read': 'ct-record'}),
    item('r-us', 'investigations', 1, '查阅超声', 'Ultrasound reviewed', {'read': 'ultrasound-record'}),
    item('r-lab', 'investigations', 1, '查阅化验', 'Laboratory record reviewed', {'read': 'laboratory-record'}),
    item('r-plan', 'management', 3, '个体化计划', 'Individualised plan', {'decidedFirstTry': 'planning'}),
    item('r-risk', 'safety', 3, '围术期风险问题找全', 'Perioperative risks identified', {'decidedFirstTry': 'risk'}),
    # anatomical orientation and operative set-up — 15
    item('r-anatomy', 'diagnosis', 6, '正确判断器官侧别', 'Laterality identified correctly', {'decidedFirstTry': 'anatomy'}, critical=True),
    # by committed order (two acts in one simulated minute keep their order), not merely both done
    item('r-signin', 'safety', 2, '诱导前完成麻醉前核对', 'Sign In before induction',
         {'inOrder': ['sign-in', 'induction']}, scored={'intervened': 'induction'}),
    item('r-timeout', 'safety', 2, '切皮前暂停核对（在诱导之后、切皮之前）', 'Time Out before incision (after induction)',
         {'all': [{'intervened': 'time-out', 'valid': True}, {'not': {'intervened': 'time-out', 'valid': False}}]}),
    item('r-ports', 'management', 2, '选择能到达左侧胆囊三角的布孔', 'A port plan that works the left-sided triangle',
         {'any': [P(plan='three-port-left'), P(plan='mirror-four-port')]}, scored={'any': [P(plan='three-port-left'), P(plan='mirror-four-port'), P(plan='habitual')]}),
    item('r-traction', 'management', 3, '向患者左侧（外侧）牵拉胆囊颈，打开三角', 'Neck retracted towards the patient\'s left to open the triangle', P(dissectedExposed=T, atLeast=0.8),
         scored={'any': [P(dissectedExposed=T, atLeast=0.01), OPERATED]}),
    # anatomical identification and critical safety decisions — 30
    item('r-safety', 'safety', 4, '坚持先核实再离断的原则', 'Verify-before-dividing principle', {'decidedFirstTry': 'safety'}, critical=True),
    item('r-cvs', 'safety', 12, '真实建立并记录关键安全视野后才夹闭', 'A true critical view of safety documented before clipping', P(documented='cvs', valid=True), critical=True,
         scored={'any': [*IRREVERSIBLE_UNSAFE, *IRREVERSIBLE_DONE]}),
    item('r-identify', 'diagnosis', 6, '正确辨认胆囊管与胆囊动脉', 'Cystic duct and cystic artery identified correctly',
         {'all': [P(identified='cystic-duct'), P(identified='cystic-artery')]},
         # in a frozen triangle nothing can be freed to be identified: stopping is the right answer there
         scored={'all': [{'any': [OPERATED, P(bailout='any')]}, {'not': P(variant='hostile-triangle')}]}),
    item('r-no-unsafe', 'safety', 8, '没有在未确认解剖时做不可逆操作', 'No irreversible step on unconfirmed anatomy',
         {'not': {'any': IRREVERSIBLE_UNSAFE}}, scored={'any': [*IRREVERSIBLE_UNSAFE, P(clipped='cystic-duct'), P(divided='cystic-duct'), P(bailout='any')]}),
    # surgical technique and tissue handling — 15
    item('r-energy', 'safety', 4, '能量器械未在显露不足处靠近隐藏结构', 'No energy near hidden structures in a poorly exposed field',
         {'not': {'any': [P(unsafe='energy-near-hidden-hazard'), P(injury='thermal-injury')]}},
         scored={'any': [OPERATED, P(unsafe='energy-near-hidden-hazard'), P(injury='thermal-injury')]}),
    item('r-handling', 'management', 3, '牵拉力度适当，胆囊未撕破', 'Gentle traction, gallbladder not torn',
         {'not': {'any': [P(unsafe='excessive-traction'), P(injury='perforation')]}},
         scored={'any': [OPERATED, P(unsafe='excessive-traction'), P(injury='perforation')]}),
    item('r-clips', 'management', 3, '胆囊管与胆囊动脉可靠夹闭后再离断', 'Cystic duct and artery secured before division',
         {'all': [P(clipped='cystic-duct', minCount=2), P(clipped='cystic-artery', minCount=2), {'not': P(injury='bleeding')}, {'not': P(injury='bile-leak')}]},
         scored={'any': [P(divided='cystic-duct'), P(divided='cystic-artery')]}),
    item('r-specimen', 'management', 2, '标本装袋经脐孔取出，或选择了替代方式', 'Specimen bagged and removed, or an alternative chosen',
         {'any': [P(specimen='extracted'), P(bailout='subtotal-fenestrating'), P(bailout='subtotal-reconstituting'), P(bailout='convert-open')]}, scored={'any': [OPERATED, P(bailout='any'), OPENED]}),
    # the operation's own end, credited from the field (a count or a device never closes it)
    item('r-closed', 'management', 1, '手术在术野中完成：取出标本或次全切除后关腹，或中转开腹', 'The operation finished on the field: closed after the specimen or a subtotal, or converted',
         {'any': [P(closed=True), P(bailout='convert-open')]}, scored={'any': [OPERATED, P(bailout='any'), OPENED]}),
    item('r-efficiency', 'efficiency', 2, '器械很少相互碰撞', 'Few instrument clashes', P(counter='clashes', lte=2), scored=OPERATED),
    # recognition and management of complications — 10 (scored only when one occurs; the percentage renormalises)
    item('r-recognise', 'safety', 6, '发生的损伤被及时说出', 'Any injury recognised aloud',
         {'not': P(injury='any', recognised=False)}, scored=P(injury='any')),
    item('r-bleeding', 'management', 2, '出血得到控制', 'Bleeding controlled', {'not': P(bleeding='any', controlled=False)}, scored=P(bleeding='any')),
    item('r-spill', 'management', 2, '溢出的胆汁和结石已吸净', 'Spilled bile and stones cleared', P(spillage='bile', cleared=True), scored=P(spillage='bile')),
    # postoperative management and documentation — 5
    item('r-signout', 'safety', 1, '手术结束后、离室前核对', 'Sign Out after the operation, before leaving', {'intervened': 'sign-out', 'valid': True}),
    item('r-emergence', 'safety', 1, '拔管与经口进食分开决定：拔管看通气与气道保护，吞咽评估在拔管后、进食前', 'Extubation and oral intake decided apart: extubation on ventilation and airway protection, swallowing assessed after extubation and before eating', {'decidedFirstTry': 'emergence'}),
    item('r-postop', 'management', 1, '术后观察重点', 'Postoperative priorities', {'decidedFirstTry': 'postop'}),
    item('r-records', 'investigations', 1, '回看手术与病理记录', 'Operation and histology records reviewed', {'all': [{'read': 'operation-record'}, {'read': 'pathology-record'}]}),
    item('r-outcome', 'management', 1, '正确界定单例结局的意义', 'Single-case outcome bounded correctly', {'decidedFirstTry': 'outcome'}),
]
assert sum(r['weight'] for r in case['rubric']) == 100, sum(r['weight'] for r in case['rubric'])

# anatomical variants (procedure.variants): one item each, scored only in its own variant (the base's 100 points are unchanged;
# in a variant the percentage renormalises over what is scored there)
V = lambda id: P(variant=id)
case['rubric'] += [
    item('r-v-double-artery', 'safety', 6, '发现并可靠处理第二支胆囊动脉', 'The second (posterior) cystic artery found and secured',
         {'all': [P(clipped='posterior-cystic-artery', minCount=2), {'not': P(injury='bleeding')}]},
         scored={'all': [V('double-cystic-artery'), {'any': [DIVIDED_TARGET, P(divided='posterior-cystic-artery'), P(specimen='detached')]}]}),
    item('r-v-hump', 'safety', 6, '保留绕入三角的肝右动脉，处理其发出的短胆囊动脉', 'The right hepatic artery looping into the triangle preserved; its short cystic branch secured',
         {'all': [{'not': {'any': [P(clipped='right-hepatic-artery'), P(divided='right-hepatic-artery')]}}, P(clipped='cystic-artery', minCount=2)]},
         scored={'all': [V('caterpillar-hump'), {'any': [DIVIDED_TARGET, P(clipped='right-hepatic-artery'), P(divided='right-hepatic-artery')]}]}),
    item('r-v-aberrant-duct', 'safety', 6, '穿过三角的迷走胆管未被夹闭或离断', 'The aberrant duct crossing the triangle left intact',
         {'not': {'any': [P(clipped='aberrant-right-posterior-duct'), P(divided='aberrant-right-posterior-duct')]}},
         scored={'all': [V('aberrant-posterior-duct'), {'any': [DIVIDED_TARGET, P(clipped='aberrant-right-posterior-duct'), P(divided='aberrant-right-posterior-duct')]}]}),
    item('r-v-hostile', 'safety', 6, '在致密纤维化处停止分离，改行胆囊次全切除或中转开腹', 'Stopped at the safe plane in dense fibrosis and chose a subtotal cholecystectomy or conversion',
         {'all': [{'any': BAILED_SAFELY}, {'not': P(unsafe='dissection-beyond-safe-plane')}]}, scored=V('hostile-triangle')),
    item('r-v-subvesical', 'management', 4, '胆囊床内的胆囊下胆管在剥离完成前已夹闭', 'The subvesical duct in the bed clipped before the dissection was completed',
         {'all': [P(clipped='subvesical-duct', minCount=2), {'not': P(injury='bile-leak')}]},
         scored={'all': [V('subvesical-duct'), {'any': [P(specimen='detached'), P(specimen='bagged'), P(specimen='extracted'), P(divided='subvesical-duct')]}]}),
]

case['safetyGates'] = [
    dict(id='bile-duct-injury', label=L('主要胆管损伤', 'Major bile duct injury'), when=P(injury='bile-duct-injury'), verdict='safety-critical', capPercent=40),
    dict(id='vascular-injury', label=L('主要血管损伤', 'Major vascular injury'), when=P(injury='vascular-injury'), verdict='safety-critical', capPercent=40),
    dict(id='irreversible-unverified', label=L('未真实建立关键安全视野即做不可逆操作', 'Irreversible step without a true critical view of safety'),
         when={'any': [P(unsafe='irreversible-without-pause'), P(unsafe='irreversible-without-view')]}, verdict='safety-critical', capPercent=50),
    dict(id='misidentified', label=L('对辨认错误的结构做不可逆操作', 'Irreversible step on a misidentified structure'),
         when=P(unsafe='irreversible-on-misidentified'), verdict='safety-critical', capPercent=40),
    dict(id='unrecognised-injury', label=L('损伤未被识别', 'An injury not recognised'), when=P(injury='any', recognised=False), verdict='safety-critical', capPercent=50),
    dict(id='continued-after-injury', label=L('发现损伤后仍继续推进', 'Carried on after a visible injury'), when=P(unsafe='continued-after-injury'), verdict='safety-critical', capPercent=50),
    dict(id='thermal', label=L('热损伤（可能术后才表现）', 'Thermal injury (may present after surgery)'), when=P(injury='thermal-injury'), verdict='safety-critical', capPercent=50),
    # the WHO checklist's order: anaesthesia induced before the team's Sign In (a real act, out of order)
    dict(id='induction-before-sign-in', label=L('未完成麻醉前核对即诱导', 'Induction before the Sign In'), when={'intervened': 'induction', 'valid': False},
         verdict='safety-critical', capPercent=70),
    # 2.4.0: closure while the swab count was not settled — recorded for the debrief, never erased by a later count
    dict(id='closed-on-open-count', label=L('纱布清点未相符即关闭（不安全推进）', 'Closed while the swab count was not settled (unsafe progression)'),
         when={'count': {'unsafe': True}}, verdict='safety-critical', capPercent=50),
    dict(id='perforation', label=L('胆囊破裂、胆汁或结石溢出', 'Gallbladder perforation, bile or stone spillage'), when=P(injury='perforation'), verdict='complication'),
    dict(id='bleeding', label=L('术中出血', 'Intra-operative bleeding'), when=P(injury='bleeding'), verdict='complication'),
    dict(id='bile-leak', label=L('胆囊管残端漏', 'Cystic stump leak'), when=P(injury='bile-leak'), verdict='complication'),
]

# ------------------------------------------------------------------ team and unknowns
# Authored corrections (ClinicalCraft docs/CASE_AUTHORING.md §7.3): teaching errors an audited run let pass. When a
# message to this colleague states one, their reply makes the correction (a model is told to; a reply without it gets
# the authored words appended; the offline responder says it). Teaching design, never a case fact.
def correction(id, mis_zh, mis_en, match, say_zh, say_en, marks):
    return dict(id=id, misconception=L(mis_zh, mis_en), match=match, say=L(say_zh, say_en), marks=marks)

NMB = ['paraly', 'neuromuscular', 'rocuronium', 'suxamethonium', 'succinylcholine', 'muscle relaxant', 'blocker', '肌松', '罗库溴铵', '琥珀胆碱', '琥珀酰胆碱']
LITTLE_HYPNOTIC = ['no hypnotic', 'without a hypnotic', 'without hypnotic', 'little or no', 'minimal hypnotic', 'skip the hypnotic', 'omit the hypnotic',
                   'no induction agent', 'without an induction agent', 'no sedation', 'without sedation', 'minimal sedation', 'little hypnotic',
                   '不用镇静', '不给镇静', '少量或不用', '不用诱导药', '无需镇静', '不用催眠', '少用镇静', '不给催眠', '几乎不用镇静']
RSI = correction('rsi-hypnotic', '快速顺序诱导时可以不给或只给很少的镇静催眠药就直接肌松。', 'In a rapid-sequence induction the hypnotic can be omitted or minimal before the neuromuscular blocker.',
                 [NMB, LITTLE_HYPNOTIC],
                 '纠正：快速顺序诱导中，镇静催眠药（诱导药）一定先给或与肌松药同时给，剂量要让患者意识消失——对衰弱的84岁老人可以减量、换药、缓慢滴定，但不能省略；没有足够催眠就肌松，会造成术中知晓。血流动力学脆弱改变的是选什么药、给多少，不是给不给。',
                 'Correction: in a rapid-sequence induction the hypnotic (the induction agent) always goes in before or with the neuromuscular blocker, in a dose that makes him unconscious — in a frail 84-year-old you choose and titrate it, you never omit it; paralysis without adequate hypnosis means awareness. Haemodynamic fragility changes which hypnotic and how much, not whether one is given.',
                 ['awareness', 'unconscious', 'never omit', 'must not be omitted', '知晓', '意识消失', '不能省略'])
PREOX = correction('preox-etco2', '呼末二氧化碳高于40 mmHg说明预充氧充分。', 'An end-tidal CO₂ above 40 mmHg shows adequate preoxygenation.',
                   [['etco2', 'etco₂', 'end-tidal co2', 'end tidal co2', 'end-tidal co₂', 'end-tidal carbon dioxide', 'capnograph', '呼末二氧化碳', '呼气末二氧化碳', '呼末co2'],
                    ['preoxygen', 'pre-oxygen', 'denitrogen', 'oxygenation', '预充氧', '预给氧', '去氮', '氧合']],
                   '纠正：预充氧是否充分看呼气末氧浓度（呼出氧分数约0.9以上），不是看呼末二氧化碳。呼末二氧化碳用来确认导管位置和监测通气；高于40 mmHg 说明不了氧储备，对慢阻肺患者反而可能提示二氧化碳潴留。',
                   'Correction: preoxygenation is judged by end-tidal OXYGEN (an expired oxygen fraction of about 0.9 or more), not by end-tidal CO₂. Capnography confirms the tube position and monitors ventilation; a value above 40 mmHg says nothing about oxygen stores — in a COPD patient it may mean CO₂ retention.',
                   ['end-tidal oxygen', 'expired oxygen', 'eto2', 'eto₂', 'feo2', '呼气末氧', '呼末氧'])
EXTUBATION = correction('extubation-swallow', '拔管前必须先通过饮水试验或吞咽造影。', 'He must pass a water-swallow test or VFSS before extubation.',
                        [['extubat', '拔管'], ['swallow', 'vfss', 'videofluoroscop', 'water test', 'drinking test', '吞咽', '饮水试验', '洼田', '造影']],
                        '纠正：拔管和经口进食是两个决定。拔管看通气、肌松恢复、意识、有效咳嗽、处理分泌物和气道保护；正式的吞咽评估在拔管之后、经口进食之前做——带着导管做不了饮水试验或吞咽造影，它也不是拔管条件。',
                        'Correction: extubation and oral intake are two decisions. Extubate on ventilation, reversal of neuromuscular block, consciousness, an effective cough, secretion handling and airway protection; a formal swallowing assessment comes after extubation and before anything by mouth — a drinking test or VFSS cannot be done with a tube in and is not an extubation criterion.',
                        ['two decisions', 'separate decision', 'after extubation', '两个决定', '拔管之后', '拔管后'])
LATERALITY = correction('laterality-reverse', '因为内脏反位，要把患者的左右再反过来理解。', 'Because of situs inversus, reverse the patient\'s left and right again.',
                        [['reverse', 'swap', 'flip', 'invert left', 'opposite side', '反过来', '颠倒', '互换', '左右反', '对调'], ['left', 'right', '左', '右']],
                        '纠正：左右永远指患者自己的左右。全内脏反位反的是器官，不是词：胆囊就在患者左侧。读片时核对影像的方位标记，核对皮肤标记，都以患者左侧为准——不要在脑子里再“反过来”一次。',
                        'Correction: left and right are always the patient\'s own. In situs inversus the organs are mirrored, not the words: the gallbladder is on the patient\'s LEFT. Check the image\'s orientation marker and the skin marking against the patient\'s left — never "reverse" sides in your head.',
                        ["patient's left", 'patient’s left', "patient's own", '患者左侧', '患者自己的左右'])
HYPOTHETICAL = correction('hypothetical-history', '把“如果家属说用过退热药和抗生素”这一假设当成了真实的家属陈述。', 'A teaching "what if the family reported antipyretics and antibiotics" became an actual family report.',
                          [['family', 'relative', 'daughter', 'son', 'wife', '家属', '家人', '女儿', '儿子', '老伴'],
                           ['antipyretic', 'antibiotic', 'paracetamol', 'fever medicine', '退烧药', '退热药', '抗生素', '消炎药']],
                          '纠正：没有人询问过家属。入院前是否用过退热药或抗生素，是一个教学上的假设问题，不是家属的陈述；病历里没有记录，在真正问到家属之前仍然是未知。',
                          'Correction: no family member has been interviewed. Whether he took antipyretics or antibiotics before admission was a teaching what-if, not a report; the record does not say, and it stays unknown until someone actually asks the family.',
                          ['what-if', 'what if', 'hypothetical', 'not been interviewed', 'not a report', '假设', '没有人询问', '没有询问'])

ANAESTHETIST_KNOWLEDGE = L(
    '负责连接监护、麻醉前核对、诱导、通气与监护。知道慢阻肺患者在气腹下易有二氧化碳潴留，常用较低气腹压；病例未记录肺功能、ASA分级与用药，需当场核实。'
    '快速顺序诱导：先给镇静催眠药使意识消失，再给肌松药，从不省略催眠；预充氧看呼气末氧浓度，呼末二氧化碳用于确认导管和监测通气。'
    '不同意诱导时用 place_hold 记录理由；重新评估后用 release_hold 记录结论（可以是“在明确的不确定性下继续”）；资料缺失本身不是暂缓的理由，但要说明怎么处理。'
    '拔管与进食分开：拔管看通气、肌松恢复、意识、咳嗽、分泌物和气道保护；吞咽评估在拔管后、进食前。左右永远指患者自己的左右。不解释手术解剖。',
    'Attaches the monitor and runs the Sign In, induction, ventilation and monitoring. Knows that COPD patients retain CO₂ under pneumoperitoneum and that lower pressures are often used; the case records no lung function, ASA class or medicines — these are verified now. '
    'Rapid-sequence induction: the hypnotic first, to unconsciousness, then the neuromuscular blocker — the hypnotic is never omitted; preoxygenation is judged by end-tidal oxygen, while capnography confirms the tube and monitors ventilation. '
    'Withholding clearance for induction is recorded with place_hold and the reason; after reassessment release_hold records the decision (it may be to proceed under stated uncertainty); missing information alone is not a reason to hold, but say how it is handled. '
    'Extubation and oral intake are separate: extubate on ventilation, reversal, consciousness, cough, secretions and airway protection; swallowing is assessed after extubation and before eating. Left and right are always the patient\'s own. Does not interpret surgical anatomy.')
case['npcs'].append(dict(role='consultant', name=L('麻醉医生', 'Anaesthetist'), knowledge=ANAESTHETIST_KNOWLEDGE,
                         corrections=[RSI, PREOX, EXTUBATION, LATERALITY]))
for n in case['npcs']:
    if n['role'] == 'attending':
        n['knowledge'] = L(
            '引导学员区分来源事实与教学规则，并说明证据局限。教学中提出的“如果……会怎样”只是假设，不能变成病史。不同意继续某一步（如诱导）时用 place_hold 记录理由，重新评估后用 release_hold；资料缺失本身不构成一律禁止。左右永远指患者自己的左右：胆囊在患者左侧，不要让学员把左右“反过来”。',
            'Guide the learner to distinguish source facts from teaching rules and explain evidence limits. A "what if" you pose in teaching stays a hypothetical and never becomes history. Withholding clearance for a step (such as induction) is recorded with place_hold and the reason, and released after reassessment with release_hold; missing information alone is not a universal prohibition. Left and right are always the patient\'s own: the gallbladder is on the patient\'s left — never tell the learner to "reverse" sides.')
        n['corrections'] = [RSI, PREOX, EXTUBATION, LATERALITY, HYPOTHETICAL]
    elif n['role'] == 'nurse':
        n['knowledge'] = L(
            '协助核对现有记录；未记录的过敏、禁食和用药不能补写。没有询问过家属：入院前用药、疼痛与进食的关系、抗栓药是否停用都未记录。左右指患者自己的左右（胆囊在患者左侧）。',
            'Help review available records; do not invent allergy, fasting or medication information. No family member has been interviewed: treatment before admission, any link between pain and meals and whether an antithrombotic was stopped are not recorded. Left and right are the patient\'s own (the gallbladder is on the patient\'s left).')
        n['corrections'] = [HYPOTHETICAL, LATERALITY]
case['unknowns'] += [
    L('患者个体的胆管与血管走行：原报告只写“未发现血管解剖变异”，未给出胆囊管汇入方式或胆囊动脉来源。', 'The patient\'s own ductal and arterial anatomy: the source says only that no vascular variation was found; it does not give the cystic duct\'s insertion or the cystic artery\'s origin.'),
    L('ASA分级、肺功能、血气、心电图、用药（含抗血小板/抗凝药）、气道评估、麻醉方式细节。', 'ASA class, lung function, blood gases, ECG, medicines (including antiplatelets or anticoagulants), airway assessment and anaesthetic details.'),
    L('标本取出方式、器械规格（除报告的Trocar尺寸外）、气腹压力、出血量的具体数值。', 'How the specimen was removed, instrument sizes beyond the reported trocars, insufflation pressure and a measured blood loss.'),
    L('入院前是否用过退热药或抗生素、疼痛与进食的关系、抗栓药是否用过或停用——都未记录，也没有家属陈述；教学中的假设不能补成病史。',
      'Whether antipyretics or antibiotics were taken before admission, whether the pain is related to meals, and whether an antithrombotic was taken or stopped — none is recorded and no family account exists; a teaching hypothetical does not fill them in.'),
]
case['examNotRecorded'] = case.get('examNotRecorded') or UNKNOWN

# ------------------------------------------------------------------ debrief
d = case['debrief']
d['conclusion'] = L(
    '全内脏反位合并胆囊结石：现有证据支持胆囊结石伴疑似急性胆囊炎（东京指南2018），手术在镜像解剖中完成。模拟中的手术在参考解剖上进行，只有真实建立关键安全视野才算安全；原报告的结局不由模拟决定。',
    'Situs inversus totalis with gallstones: the evidence supports gallstone disease with suspected acute cholecystitis (Tokyo Guidelines 2018), operated on in mirror-image anatomy. The simulated operation runs on reference anatomy and counts as safe only with a true critical view of safety; the reported outcome is not decided by the simulation.')
d['keyReasoning'] = [
    L('诊断以证据为限：发热史、压痛与结石不等于确诊急性胆囊炎。', 'Diagnosis stays within the evidence: a history of fever, tenderness and stones are not a confirmed acute cholecystitis.'),
    *d['keyReasoning'],
    L('镜像解剖中，三角的显露靠把胆囊颈向患者左侧牵拉；沿用常规（向右）牵拉会关闭三角，并让胆总管看起来像汇入胆囊颈。',
      'In mirror-image anatomy the triangle opens by pulling the neck towards the patient\'s left; the habitual pull to the right closes it and makes the common bile duct look as if it runs into the gallbladder neck.'),
    L('关键安全视野由术野判定，而非勾选：三角清空、胆囊板可见、只有两根结构进入胆囊。', 'The critical view of safety is judged on the field, not by ticking: triangle cleared, cystic plate seen, two and only two structures entering the gallbladder.'),
]
d['boundaries'] = L(
    '三维解剖为参考解剖（BodyParts3D与Layered Human程序化模型），不是患者CT重建；组织力学为状态模型，未经标定；术中生命体征为模拟值，未经临床标定；评分为教学流程检查，未经效度验证，也不是GOALS评分；未经外科、麻醉或影像专家审核。',
    'The 3D anatomy is reference anatomy (BodyParts3D and the Layered Human procedural model), not a CT reconstruction of the patient; tissue behaviour is a state model, not calibrated mechanics; intra-operative vital signs are simulated and uncalibrated; the score checks an authored workflow — it is not validated and is not a GOALS score; no surgical, anaesthetic or radiological expert has reviewed it.')
d['teachingPoints'] = [
    *d['teachingPoints'],
    L('SAGES 2020：建立关键安全视野；无法建立时采用暂停、求助、术中胆道影像、胆囊次全切除或中转开腹等策略。',
      'SAGES 2020: achieve the critical view of safety; when it cannot be achieved, stop, call for help, image the bile ducts, or choose a subtotal cholecystectomy or conversion.'),
    L('东京指南2018：确诊急性胆囊炎需要局部征象、全身炎症和影像三者兼备。', 'Tokyo Guidelines 2018: a definite acute cholecystitis needs local signs, systemic inflammation and imaging together.'),
    L('左右永远指患者自己的左右：全内脏反位反的是器官，不是词。胆囊在患者左侧；核对影像方位标记（DICOM 患者方位）和皮肤标记都以患者左侧为准，不要再“反过来”。',
      'Left and right are always the patient\'s own: in situs inversus the organs are mirrored, not the words. The gallbladder is on the patient\'s left; check the image orientation marker (DICOM patient orientation) and the skin marking against the patient\'s left — never "reverse" sides again.'),
    L('快速顺序诱导：先给镇静催眠药使意识消失，再给肌松药；预充氧看呼气末氧浓度，呼末二氧化碳确认导管位置并监测通气。',
      'Rapid-sequence induction: the hypnotic first, to unconsciousness, then the neuromuscular blocker; preoxygenation is judged by end-tidal oxygen, while end-tidal CO₂ confirms the tube and monitors ventilation.'),
    L('拔管与经口进食是两个决定：拔管看通气与气道保护，卒中后的吞咽评估在拔管之后、进食之前。',
      'Extubation and oral intake are two decisions: extubation rests on ventilation and airway protection; after a stroke swallowing is assessed after extubation and before eating.'),
    L('暂缓是记录，不是语气：主治或麻醉医生不同意时记录暂缓及理由，重新评估后记录解除；资料缺失本身不是一律禁止，但要写明如何处理。',
      'A hold is a record, not a tone of voice: an attending or anaesthetist who withholds clearance records the hold and why, and its release after reassessment; missing information alone is not a universal prohibition, but how it is handled is written down.'),
]
refs = d.setdefault('references', [])
for r in [
    'Yokoe M, Hata J, Takada T, et al. Tokyo Guidelines 2018: diagnostic criteria and severity grading of acute cholecystitis (with videos). J Hepatobiliary Pancreat Sci. 2018;25(1):41-54.',
    'Brunt LM, Deziel DJ, Telem DA, et al. Safe cholecystectomy multi-society practice guideline and state-of-the-art consensus conference on prevention of bile duct injury during cholecystectomy. Surg Endosc. 2020;34(7):2827-2855.',
    'Strasberg SM, Hertl M, Soper NJ. An analysis of the problem of biliary injury during laparoscopic cholecystectomy. J Am Coll Surg. 1995;180(1):101-125.',
    'World Health Organization. WHO Guidelines for Safe Surgery 2009: Safe Surgery Saves Lives. Geneva: WHO; 2009 (Surgical Safety Checklist implementation manual).',
    'Acquisto NM, Mosier JM, Bittner EA, et al. Society of Critical Care Medicine clinical practice guidelines for rapid sequence intubation in the critically ill adult patient. Crit Care Med. 2023;51(10):1411-1430.',
    'DICOM PS3.3, section C.7.6.2: Image Plane Module (Patient Orientation). NEMA.',
]:
    if r not in refs:
        refs.append(r)

# ------------------------------------------------------------------ reference path
sol = [s for s in case['solution'] if s['type'] != 'finish' and not (s['type'] == 'intervene' and s['interventionId'] == 'open-historical-review')]
# the review-phase steps (operation/pathology/follow-up records, outcome) move to the end
review_ids = {'operation-record', 'pathology-record', 'followup-record'}
pre = [s for s in sol if not (s.get('investigationId') in review_ids or s.get('decisionId') == 'outcome')]
post = [s for s in sol if s not in pre]
OP = lambda **kw: dict(type='operate', op=kw)
dissect = lambda region, n, energy=False: [OP(op='dissect', port='C', region=region, energy=energy) for _ in range(n)]
neck = 'gallbladder-infundibulum' if 'gallbladder-infundibulum' in geo else 'gallbladder'
CD, CA = 'T2', 'T3'  # handles in order of appearance: common bile duct (0.2), cystic duct (0.5), cystic artery (0.6)
case['solution'] = [
    *pre[:1],
    *[s for s in pre[1:] if s['type'] in ('ask', 'examine', 'order', 'read')],
    dict(type='examine', findingId='murphy'),
    dict(type='answer', decisionId='diagnosis', optionIds=['suspected']),
    *[s for s in pre if s['type'] == 'answer'],
    dict(type='ask', itemId='antithrombotic'), dict(type='ask', itemId='copd-status'), dict(type='ask', itemId='fasting'),
    dict(type='answer', decisionId='risk', optionIds=['copd', 'antithrombotic', 'function', 'dextrocardia']),
    dict(type='intervene', interventionId='attach-monitor'),
    dict(type='intervene', interventionId='sign-in'), dict(type='intervene', interventionId='induction'), dict(type='intervene', interventionId='time-out'),
    OP(op='plan-ports', plan='three-port-left'), OP(op='insufflate', pressure=12),
    OP(op='insert', port='A', instrument='laparoscope'), OP(op='insert', port='B', instrument='grasper'), OP(op='insert', port='C', instrument='maryland'),
    OP(op='retract', port='B', structure=neck, direction=['patient-left', 'caudal'], force='firm'),
    *dissect('hepatocystic-triangle', 6), *dissect('cystic-plate', 3),
    OP(op='isolate', port='C', handle=CD), OP(op='isolate', port='C', handle=CA),
    OP(op='identify', handle=CD, **{'as': 'cystic-duct'}), OP(op='identify', handle=CA, **{'as': 'cystic-artery'}),
    OP(op='safety-pause', view='cvs', claims={'triangle': True, 'plate': True, 'entering': 2}),
    OP(op='withdraw', port='C'), OP(op='insert', port='C', instrument='clip-applier'),
    OP(op='clip', port='C', handle=CD, count=3), OP(op='clip', port='C', handle=CA, count=2),
    OP(op='withdraw', port='C'), OP(op='insert', port='C', instrument='scissors'),
    OP(op='divide', port='C', handle=CD), OP(op='divide', port='C', handle=CA),
    OP(op='withdraw', port='C'), OP(op='insert', port='C', instrument='hook'),
    OP(op='retract', port='B', structure=neck, direction=['anterior', 'cephalad'], force='firm'),
    *dissect('gallbladder-bed', 4, energy=True),
    OP(op='inspect'),
    OP(op='withdraw', port='C'), OP(op='insert', port='C', instrument='retrieval-bag'), OP(op='bag', port='C'), OP(op='extract', port='A'),
    OP(op='close'),
    dict(type='answer', decisionId='emergence', optionIds=['criteria', 'swallow-after']),
    dict(type='intervene', interventionId='sign-out'),
    dict(type='intervene', interventionId='pacu-handover'),
    dict(type='answer', decisionId='postop', optionIds=['resp', 'neuro', 'bile', 'bleed']),
    dict(type='intervene', interventionId='open-historical-review'),
    *post,
    dict(type='finish'),
]
case['extensions'].update(dict(version4=dict(
    anatomy=f'assets/cases/{CASE_ID}/anatomy.json',
    scoringDomains={'history-and-diagnosis': 15, 'preoperative-assessment': 10, 'orientation-and-setup': 15, 'identification-and-safety': 30,
                    'technique-and-handling': 15, 'complications': 10, 'postoperative-and-documentation': 5},
    renormalisation='Items whose scoredWhen does not hold (a complication that did not occur) count neither as earned nor as possible; the percentage is earned / possible.',
    dataset='dataset/case-126-v3 is kept unchanged as the historical reference and regression baseline.')))

DEST.mkdir(parents=True, exist_ok=True)
(DEST / 'case.json').write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# ------------------------------------------------------------------ evidence ledger (every patient-specific value traced)
facts = []
for section in ('history', 'exam', 'investigations'):
    for x in case[section]:
        unknown = x.get('disclosure') == 'unknown' or any(r.get('available') is False for r in x.get('results', {}).values())
        facts.append(dict(id=x['id'], section=section, provenance='unknown' if unknown else 'published-case',
                          locator='p.180 Case / p.181 Discussion' if not unknown else None))
values = [
    dict(fact='age', value=84, provenance='published-case', locator='p.180'),
    dict(fact='admission', value='2023-02-02', provenance='published-case', locator='p.180'),
    dict(fact='operation_date', value='2023-02-06', provenance='published-case', locator='p.180'),
    dict(fact='temperature_c', value=36.6, provenance='published-case', locator='p.180'),
    dict(fact='pulse_per_min', value=78, provenance='published-case', locator='p.180'),
    dict(fact='respiratory_rate_per_min', value=19, provenance='published-case', locator='p.180'),
    dict(fact='blood_pressure_mmHg', value='128/78', provenance='published-case', locator='p.180'),
    dict(fact='apex_beat', value='right 5th intercostal space', provenance='published-case', locator='p.180'),
    dict(fact='gallbladder_size_cm', value='6 x 4 x 3', provenance='published-case', locator='p.180 (at operation)'),
    dict(fact='gallbladder_wall_cm', value=0.4, provenance='published-case', locator='p.180 (at operation)'),
    dict(fact='ports', value='A 10 mm infraumbilical; B 5 mm subxiphoid slightly left; C 5 mm left midclavicular 2 cm below costal margin (main)', provenance='published-case', locator='p.180, Fig. 3'),
    dict(fact='operation_minutes', value=30, provenance='published-case', locator='p.180'),
    dict(fact='discharge_day', value=5, provenance='published-case', locator='p.180'),
    dict(fact='baseline_spo2', value=None, provenance='unknown',
         simulationOverride=dict(enabled=True, value=95, classification='synthetic', requiresClinicalReview=True)),
    *[dict(fact=f'intraoperative_{e["id"]}', value=None, provenance='unknown',
           simulationOverride=dict(enabled=True, value=e['setVitals'], classification='synthetic', requiresClinicalReview=True))
      for e in case['physiology']['events']],
    dict(fact='insufflation_pressure_mmHg', value=None, provenance='unknown',
         simulationOverride=dict(enabled=True, value={'usual': 12, 'max': 15}, classification='synthetic', requiresClinicalReview=True)),
    dict(fact='biliary_and_arterial_course', value=None, provenance='unknown', note='Source: no vascular variation found at operation. Geometry is reference anatomy.',
         simulationOverride=dict(enabled=True, value=f'assets/cases/{CASE_ID}/anatomy.json', classification='reference', requiresClinicalReview=True)),
]
ledger = dict(schema='surgerycraft/evidence-ledger@2', caseId=CASE_ID, caseVersion=case['version'],
              sourceArchive='dataset/126_1654623_内脏完全反位腹腔镜胆囊切除术一例.zip', sourcePages=[180, 181],
              categories=dict(**{'published-case': 'Stated in the source report.', 'guideline': 'A guideline or textbook principle (cited in the debrief).',
                                 'synthetic': 'A simulation assumption with no source, labelled in the case.', 'reference': 'Reference anatomy adapted to the case.',
                                 'unknown': 'Not recorded; the case answers that it is unrecorded.'}),
              facts=facts, values=values,
              # the procedure's anatomical variants: counterfactual by construction (the source found no variation)
              counterfactual=[dict(variant=v['id'], provenance='authored', patientSpecific=False, contradictsSource=True,
                                   note='Authored on the reference geometry for teaching and the operative benchmark; never the default anatomy.',
                                   references=v['references']) for v in case['procedure']['variants']],
              authored=['pseudonym, persona and hospital placement', 'questions, phases, tasks, distractors and scoring',
                        'WHO/SAGES/Tokyo-based decisions and checklist steps', 'port plans other than the report\'s', 'synthetic intra-operative physiology',
                        'the five anatomical variants (procedure.variants) and the operative benchmark suite (content/operative/case126-v1)'],
              limits=['No DICOM or patient-specific mesh', 'Synthetic physiology uncalibrated', 'No clinician review', 'No measured live-model performance'])
source_archive = ROOT / ledger['sourceArchive']
if source_archive.exists():
    ledger['sourceArchiveSha256'] = hashlib.sha256(source_archive.read_bytes()).hexdigest()
(DEST / 'evidence.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'wrote {DEST / "case.json"} ({len(case["solution"])} reference steps) and evidence.json')
