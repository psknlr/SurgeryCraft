"""Build the operative benchmark suite of Case 126: content/operative/case126-v1/*.json.

Each scenario is one `clinicalcraft/operative-scenario@1` file (ClinicalCraft docs/BENCHMARK_OPERATIVE.md):
the case is brought to the table by its own reference solution (history, decisions, the WHO checklist), the
patient's anatomy is one of the case's procedure variants -- or a pool the run seed draws from -- and the
agent operates with observe_field and operate only, never told which anatomy it has.

The reference trajectories are written for a surgical reviewer: each step is one operative step, and every
duct or vessel is named by what it must be (`@cystic-duct`), never by the T-number the field happens to give
it; ClinicalCraft resolves the names by replaying the steps on the engine. The dev split has the reported
anatomy (in both languages), the double cystic artery and the frozen triangle; the test split, held out,
has the caterpillar hump, the aberrant duct, the subvesical duct and an unknown anatomy drawn from all six.

Run with Python 3.11+: python tools/operative/build_suite_case126.py  (`--check`: fail if the files differ)
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'content' / 'operative' / 'case126-v1'
CASE_ID = 'cmcr-1654623'
SUITE = 'case126-v1'


def L(zh, en):
    return {'zh-CN': zh, 'en': en}


def op(**kw):
    return kw


T = 'hepatocystic-triangle'
NECK = 'gallbladder-infundibulum'
ACCESS = [
    op(op='plan-ports', plan='three-port-left'),
    op(op='insufflate', pressure=12),
    op(op='insert', port='A', instrument='laparoscope'),
    op(op='insert', port='B', instrument='grasper'),
    op(op='insert', port='C', instrument='maryland'),
    op(op='retract', port='B', structure=NECK, direction=['patient-left', 'caudal'], force='firm'),
]


def dissect(region, n, energy=False):
    return [op(op='dissect', port='C', region=region, energy=energy) for _ in range(n)]


def swap(instrument):
    return [op(op='withdraw', port='C'), op(op='insert', port='C', instrument=instrument)]


def secure(structures, also_named=()):
    """Free, name, pause on the critical view, then clip and divide `structures` [(id, clips)]; `also_named` are named, never touched."""
    return [
        *[op(op='isolate', port='C', handle=f'@{s}') for s, _ in structures],
        *[op(op='identify', handle=f'@{s}', **{'as': s}) for s, _ in structures],
        *[op(op='identify', handle=f'@{s}', **{'as': s}) for s in also_named],
        op(op='safety-pause', view='cvs', claims={'triangle': True, 'plate': True, 'two': True}),
        *swap('clip-applier'),
        *[op(op='clip', port='C', handle=f'@{s}', count=n) for s, n in structures],
        *swap('scissors'),
        *[op(op='divide', port='C', handle=f'@{s}') for s, _ in structures],
    ]


BED_PULL = op(op='retract', port='B', structure=NECK, direction=['anterior', 'cephalad'], force='firm')
FINISH = [op(op='inspect'), *swap('retrieval-bag'), op(op='bag', port='C'), op(op='extract', port='A'), op(op='close')]
CYSTIC = [('cystic-duct', 3), ('cystic-artery', 2)]


def complete(structures=CYSTIC, also_named=()):
    return [*ACCESS, *dissect(T, 6), *dissect('cystic-plate', 3), *secure(structures, also_named), *swap('hook'), BED_PULL,
            *dissect('gallbladder-bed', 4, energy=True), *FINISH]


TRAJECTORY = {
    'reference': complete(),
    'double-cystic-artery': complete([*CYSTIC, ('posterior-cystic-artery', 2)]),
    'caterpillar-hump': complete(also_named=('right-hepatic-artery',)),
    'aberrant-posterior-duct': complete(also_named=('aberrant-right-posterior-duct',)),
    # the planes stop separating at the safe limit: call for help, then a fenestrating subtotal cholecystectomy (TG18, SAGES 2020)
    'hostile-triangle': [*ACCESS, *dissect(T, 3), op(op='bailout', strategy='call-help'), op(op='bailout', strategy='subtotal-fenestrating'),
                         op(op='inspect'), op(op='close')],
    # the duct appears in the bed: free it, name it, two clips, divide, then finish the bed
    'subvesical-duct': [*ACCESS, *dissect(T, 6), *dissect('cystic-plate', 3), *secure(CYSTIC), *swap('hook'), BED_PULL,
                        *dissect('gallbladder-bed', 3, energy=True),
                        op(op='isolate', port='C', handle='@subvesical-duct'), op(op='identify', handle='@subvesical-duct', **{'as': 'subvesical-duct'}),
                        *swap('clip-applier'), op(op='clip', port='C', handle='@subvesical-duct', count=2),
                        *swap('scissors'), op(op='divide', port='C', handle='@subvesical-duct'),
                        *swap('hook'), *dissect('gallbladder-bed', 1, energy=True), *FINISH],
}

INSTRUCTION = L(
    '你是这台腹腔镜胆囊切除术的主刀医生。患者已麻醉，暂停核对已完成，从选择布孔方案开始由你操作。请安全地切除胆囊；如果无法安全完成，请以对患者安全的方式结束手术。一切依据你在术野中所见判断。',
    'You are the operating surgeon for this laparoscopic cholecystectomy. The patient is anaesthetised and the Time Out is done; the operation is yours from the choice of port plan. Remove the gallbladder safely or, if that cannot be done safely, end the operation in a way that is safe for the patient. Judge everything from what you see in the field.',
)

P = lambda **kw: {'clinical': {'procedure': kw}}
NO_INJURY = {'clinical': {'not': {'procedure': {'injury': 'any'}}}}
CLEAR = {'verdict': ['clear']}
COMPLETED = [CLEAR, NO_INJURY, P(specimen='extracted'), P(closed=True), P(documented='cvs', valid=True)]
SAFE_BAILOUTS = [{'procedure': {'bailout': b}} for b in ('subtotal-fenestrating', 'subtotal-reconstituting', 'convert-open')]
BAILED = [CLEAR, NO_INJURY, {'clinical': {'any': SAFE_BAILOUTS}}, {'clinical': {'not': {'procedure': {'unsafe': 'dissection-beyond-safe-plane'}}}}]
EITHER = [CLEAR, NO_INJURY, {'clinical': {'any': [{'all': [{'procedure': {'specimen': 'extracted'}}, {'procedure': {'closed': True}}]}, *SAFE_BAILOUTS]}}]
LIMITS = {'maxToolCalls': 250, 'maxTurns': 6, 'maxSimMinutes': 240, 'timeoutMs': 900000}


def scenario(id, split, variant, expect, predicates, title, rationale, locale='en', tags=()):
    variants = variant['pool'] if isinstance(variant, dict) else [variant]
    return {
        'schema': 'clinicalcraft/operative-scenario@1',
        'id': id,
        'suite': SUITE,
        'split': split,
        'title': title,
        'instruction': INSTRUCTION,
        'caseId': CASE_ID,
        'locale': locale,
        'seed': 126,
        'variant': variant,
        'setup': {'preamble': 'solution', 'approvals': 'approve'},
        'expect': expect,
        'predicates': predicates,
        'limits': LIMITS,
        'reference': {v: TRAJECTORY[v] for v in variants},
        'tags': ['case126', 'situs-inversus', 'cholecystectomy', *tags],
        'rationale': rationale,
    }


SCENARIOS = [
    scenario('c126-reference-en', 'dev', 'reference', 'complete', COMPLETED,
             L('报告所见的解剖（英文）', 'The anatomy as reported (English)'),
             L('镜像解剖、无变异：向患者左侧牵拉打开三角，建立真实的关键安全视野后夹闭离断，然后完成胆囊床剥离。',
               'Mirror-image anatomy without variation: pull the neck to the patient\'s left to open the triangle, achieve a true critical view, clip and divide, then finish the bed.'),
             tags=('reported-anatomy',)),
    scenario('c126-reference-zh', 'dev', 'reference', 'complete', COMPLETED,
             L('报告所见的解剖（中文）', 'The anatomy as reported (Chinese)'),
             L('同英文版，以中文会话进行。', 'As the English scenario, in a Chinese-language session.'), locale='zh-CN', tags=('reported-anatomy',)),
    scenario('c126-double-artery', 'dev', 'double-cystic-artery', 'complete', COMPLETED,
             L('第二支胆囊动脉', 'A second cystic artery'),
             L('胆囊板剥离后出现第三根进入胆囊的结构；关键安全视野要求它也游离可见，并在离断前可靠夹闭。只处理两根结构即离断属于未真正达到安全视野的不可逆操作，完成胆囊床时会撕断后支出血。',
               'Taking the gallbladder off the cystic plate shows a third structure entering it; the critical view needs it free and seen, and it must be clipped before division. Dividing only two is an irreversible step without a true view, and completing the bed tears the posterior branch.'),
             tags=('variant', 'arterial')),
    scenario('c126-hostile-triangle', 'dev', 'hostile-triangle', 'bailout', BAILED,
             L('无法安全解剖的三角', 'A triangle that cannot be dissected safely'),
             L('致密纤维化：解剖到一半层次即分不开，关键安全视野无法建立。正确做法是停下、求助，选择胆囊次全切除或中转开腹；继续分离会撕裂胆总管。',
               'Dense fibrosis: halfway through, the planes stop separating and the critical view cannot be reached. The right course is to stop, call for help and choose a subtotal cholecystectomy or conversion; dissecting on tears the common bile duct.'),
             tags=('variant', 'bail-out')),
    scenario('c126-hump', 'test', 'caterpillar-hump', 'complete', COMPLETED,
             L('靠近胆囊颈的动脉', 'An artery close to the neck'),
             L('肝右动脉绕入三角（毛虫驼峰）。三角清空前它像进入胆囊颈的动脉；真正的胆囊动脉很短，三角几乎完全清空后才显露。夹闭驼峰即为血管损伤。',
               'The right hepatic artery loops into the triangle (caterpillar hump). Until the triangle is cleared it looks like an artery entering the neck; the true cystic artery is short and only shows when the triangle is nearly clear. Clipping the hump is a vascular injury.'),
             tags=('variant', 'arterial', 'held-out')),
    scenario('c126-aberrant-duct', 'test', 'aberrant-posterior-duct', 'complete', COMPLETED,
             L('三角内的另一根管道', 'Another duct in the triangle'),
             L('迷走右后叶胆管穿过三角。三角未完全清空时它像进入胆囊颈的管道，关键安全视野不成立；完全清空后可见它走向肝门、汇入肝总管，必须保留。',
               'An aberrant right posterior sectoral duct crosses the triangle. Until the triangle is fully cleared it looks like a duct entering the neck and the critical view does not hold; once cleared it is seen running to the hilum and into the common hepatic duct, and must be kept.'),
             tags=('variant', 'biliary', 'held-out')),
    scenario('c126-subvesical', 'test', 'subvesical-duct', 'complete', COMPLETED,
             L('胆囊床内的细小管道', 'A fine duct in the bed'),
             L('胆囊下胆管在胆囊床剥离中出现。它不影响关键安全视野，但完成剥离前必须夹闭，否则会撕断造成胆漏。',
               'A subvesical duct appears during the bed dissection. It does not affect the critical view, but it must be clipped before the dissection is completed, or it is torn and bile leaks.'),
             tags=('variant', 'biliary', 'held-out')),
    scenario('c126-unknown-anatomy', 'test', {'pool': list(TRAJECTORY)}, 'either', EITHER,
             L('未知解剖', 'Unknown anatomy'),
             L('运行种子从六种解剖（报告所见与五种变异）中抽取一种。智能体只能依据术野判断：完成手术或安全地补救都可接受，任何损伤都不可接受。',
               'The run seed draws one of six anatomies (as reported, or one of five variants). The agent can only judge from the field: completing or bailing out safely are both accepted; any injury is not.'),
             tags=('variant', 'pool', 'held-out')),
]


def main() -> int:
    check = '--check' in sys.argv[1:]
    DEST.mkdir(parents=True, exist_ok=True)
    stale = []
    names = set()
    for s in SCENARIOS:
        path = DEST / f"{s['id']}.json"
        names.add(path.name)
        text = json.dumps(s, ensure_ascii=False, indent=2) + '\n'
        if path.exists() and path.read_text(encoding='utf-8') == text:
            continue
        stale.append(path.name)
        if not check:
            path.write_text(text, encoding='utf-8')
    extra = sorted(p.name for p in DEST.glob('*.json') if p.name not in names)
    if check:
        if stale or extra:
            print(f'out of date: {", ".join(stale + extra)} -- run python tools/operative/build_suite_case126.py', file=sys.stderr)
            return 1
        print(f'{SUITE}: {len(SCENARIOS)} scenarios up to date')
        return 0
    for name in extra:
        (DEST / name).unlink()
    print(f'wrote {DEST.relative_to(ROOT)}: {len(SCENARIOS)} scenarios ({len(stale)} changed, {len(extra)} removed)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
