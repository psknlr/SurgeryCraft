#!/usr/bin/env bash
# Validate the SurgeryCraft content pack with a ClinicalCraft checkout:
#   1. `clinicalcraft facilities validate --all` with the pack in contentDirs (schemas, compiled facility,
#      room templates, catalogs, overlaps, levels/connectors/zones, case capability gaps);
#   2. the navigation & zoning test (tools/navcheck.test.ts) and the operating-room interaction test
#      (tools/orflow.test.ts) on ClinicalCraft's world model;
#   3. the project skills (.clinicalcraft/skills) and "pass me …" in an embodied session (tools/skills.test.ts);
#   4. every equipment model (content/assets/models) against its catalog reference: `clinicalcraft assets inspect --type`
#      (licence, use status, pinned hash, size against the footprint; docs/MODELS.md).
# Usage: tools/check.sh [path/to/ClinicalCraft]   (default: ../ClinicalCraft next to this repository)
# Nothing is left behind in the ClinicalCraft checkout.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PACK="$(cd "$HERE/../content" && pwd)"
CC="$(cd "${1:-$HERE/../../ClinicalCraft}" && pwd)"
TEST="$CC/packages/world/src/zz-surgerycraft-nav.test.ts"
FLOW="$CC/packages/world/src/zz-surgerycraft-orflow.test.ts"
SKILLS="$CC/packages/agent/src/zz-surgerycraft-skills.test.ts"
ROOT="$(cd "$HERE/.." && pwd)"
SETTINGS_HOME="$(mktemp -d)"
trap 'rm -rf "$SETTINGS_HOME"; rm -f "$TEST" "$FLOW" "$SKILLS"' EXIT
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
