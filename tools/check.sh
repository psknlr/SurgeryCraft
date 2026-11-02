#!/usr/bin/env bash
# Validate the SurgeryCraft content pack with a ClinicalCraft checkout:
#   1. `clinicalcraft facilities validate --all` with the pack in contentDirs (schemas, compiled facility,
#      room templates, catalogs, overlaps, levels/connectors/zones, case capability gaps);
#   2. the navigation & zoning test (tools/navcheck.test.ts) and the operating-room interaction test
#      (tools/orflow.test.ts) on ClinicalCraft's world model;
#   3. the project skills (.clinicalcraft/skills) and "pass me …" in an embodied session (tools/skills.test.ts);
#   4. every equipment model (content/assets/models) against its catalog reference: `clinicalcraft assets inspect --type`
#      (licence, use status, pinned hash, size against the footprint; docs/MODELS.md);
#   5. Case 126 (content/cases/cmcr-1654623): `cases validate --strict`, `cases verify` (reference path, utterance corpus),
#      the anatomy asset (tools/blender/verify_anatomy_1654623.py), the case's fidelity, safety and variant scenarios
#      (tools/case126.test.ts; docs/CASE_126.md) and, embodied in OR 7, the operating-site check and the WHO board
#      as a view of the case record, holds, the way into the operation, navigation, carts, roles and teaching corrections
#      (tools/case126-theatre.test.ts), the release acceptance run end to end (tools/case126-acceptance.test.ts), and the
#      care team working on its own — the
#      two-nurse needle-holder handoff and its perturbations, save/restore mid-handoff (tools/case126-team.test.ts);
#   6. the operative benchmark suite of Case 126 (content/operative/case126-v1): generated files up to date
#      (tools/operative/build_suite_case126.py --check), then `clinicalcraft bench operative` with the reference and
#      scripted-llm agents, both at 100 % with no hidden-state leak.
#   7. the team benchmark of Case 126 (`clinicalcraft bench team`): every team scenario passes against its `expect`.
# Usage: tools/check.sh [path/to/ClinicalCraft]   (default: ../ClinicalCraft next to this repository)
# Nothing is left behind in the ClinicalCraft checkout.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PACK="$(cd "$HERE/../content" && pwd)"
CC="$(cd "${1:-$HERE/../../ClinicalCraft}" && pwd)"
TEST="$CC/packages/world/src/zz-surgerycraft-nav.test.ts"
FLOW="$CC/packages/world/src/zz-surgerycraft-orflow.test.ts"
SKILLS="$CC/packages/agent/src/zz-surgerycraft-skills.test.ts"
CASE126="$CC/packages/core/src/zz-surgerycraft-case126.test.ts"
THEATRE="$CC/packages/agent/src/zz-surgerycraft-case126-theatre.test.ts"
TEAM="$CC/packages/agent/src/zz-surgerycraft-case126-team.test.ts"
ACCEPT="$CC/packages/agent/src/zz-surgerycraft-case126-acceptance.test.ts"
ROOT="$(cd "$HERE/.." && pwd)"
SETTINGS_HOME="$(mktemp -d)"
trap 'rm -rf "$SETTINGS_HOME"; rm -f "$TEST" "$FLOW" "$SKILLS" "$CASE126" "$THEATRE" "$TEAM" "$ACCEPT"' EXIT
printf '{"contentDirs": ["%s"]}\n' "$PACK" > "$SETTINGS_HOME/settings.json"

echo "== facilities validate (ClinicalCraft at $CC)"
(cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- facilities validate --all)

echo "== navigation & zoning, operating-room interactions"
cp "$HERE/navcheck.test.ts" "$TEST"
cp "$HERE/orflow.test.ts" "$FLOW"
(cd "$CC" && SURGERYCRAFT_CONTENT="$PACK" npx vitest run "packages/world/src/zz-surgerycraft-nav.test.ts" "packages/world/src/zz-surgerycraft-orflow.test.ts")

echo "== project skills and the OR team in a session"
cp "$HERE/skills.test.ts" "$SKILLS"
(cd "$CC" && SURGERYCRAFT_ROOT="$ROOT" npx vitest run "packages/agent/src/zz-surgerycraft-skills.test.ts")

echo "== equipment models against their catalog references"
for glb in "$PACK"/assets/models/*.glb; do
  id="$(basename "$glb" .glb)"
  (cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- assets inspect "$glb" --type "$id" --lang en --json) \
    | python3 -c 'import json, sys
r = json.load(sys.stdin)
print("%s: %d triangles, %d B" % (r["type"], r["counts"]["triangles"], r["bytes"]))
for i in r["issues"]:
    if i["severity"] != "info":
        print("    %s %s: %s" % (i["severity"], i["code"], i["message"]))'
done

echo "== Case 126: validate, verify, anatomy, fidelity and safety scenarios"
(cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- cases validate "$PACK/cases/cmcr-1654623/case.json" --strict)
(cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- cases verify cmcr-1654623)
python3 "$HERE/blender/verify_anatomy_1654623.py"
cp "$HERE/case126.test.ts" "$CASE126"
(cd "$CC" && SURGERYCRAFT_CONTENT="$PACK" npx vitest run "packages/core/src/zz-surgerycraft-case126.test.ts")
# in OR 7, embodied: the operation only at the table (re-checked after an approval wait), the WHO board = the record
cp "$HERE/case126-theatre.test.ts" "$THEATRE"
(cd "$CC" && SURGERYCRAFT_ROOT="$ROOT" npx vitest run "packages/agent/src/zz-surgerycraft-case126-theatre.test.ts")
# release acceptance, end to end in OR 7: history → monitor → hold → Sign In → release → induction → reload → the board's
# Time Out → the field → counts → the board's Sign Out → recovery handover; record, board and score agree
cp "$HERE/case126-acceptance.test.ts" "$ACCEPT"
(cd "$CC" && SURGERYCRAFT_ROOT="$ROOT" npx vitest run "packages/agent/src/zz-surgerycraft-case126-acceptance.test.ts")
# the care team of OR 7 on its own (ClinicalCraft docs/TEAM.md): request → read-back → find → hand over → verify
cp "$HERE/case126-team.test.ts" "$TEAM"
(cd "$CC" && SURGERYCRAFT_ROOT="$ROOT" npx vitest run "packages/agent/src/zz-surgerycraft-case126-team.test.ts")

echo "== Case 126: operative benchmark suite (reference and scripted-llm must be 100 %)"
python3 "$HERE/operative/build_suite_case126.py" --check
OUT="$(mktemp -d)"
trap 'rm -rf "$SETTINGS_HOME" "$OUT"; rm -f "$TEST" "$FLOW" "$SKILLS" "$CASE126" "$THEATRE" "$TEAM" "$ACCEPT"' EXIT
for agent in reference scripted-llm; do
  (cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- bench operative --suite case126-v1 --agent "$agent" --seeds 1-8 --out "$OUT/$agent" --lang en 2>/dev/null)
done

echo "== Case 126: team benchmark (every team scenario must pass)"
(cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- bench team --case cmcr-1654623 --out "$OUT/team" --lang en)
