#!/usr/bin/env bash
# Validate the SurgeryCraft content pack with a ClinicalCraft checkout:
#   1. `clinicalcraft facilities validate --all` with the pack in contentDirs (schemas, compiled facility,
#      room templates, catalogs, overlaps, levels/connectors/zones, case capability gaps);
#   2. the navigation & zoning test (tools/navcheck.test.ts) on ClinicalCraft's world model.
# Usage: tools/check.sh [path/to/ClinicalCraft]   (default: ../ClinicalCraft next to this repository)
# Nothing is left behind in the ClinicalCraft checkout.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PACK="$(cd "$HERE/../content" && pwd)"
CC="$(cd "${1:-$HERE/../../ClinicalCraft}" && pwd)"
TEST="$CC/packages/world/src/zz-surgerycraft-nav.test.ts"
SETTINGS_HOME="$(mktemp -d)"
trap 'rm -rf "$SETTINGS_HOME"; rm -f "$TEST"' EXIT
printf '{"contentDirs": ["%s"]}\n' "$PACK" > "$SETTINGS_HOME/settings.json"

echo "== facilities validate (ClinicalCraft at $CC)"
(cd "$CC" && CLINICALCRAFT_HOME="$SETTINGS_HOME" npm run -s cc -- facilities validate --all)

echo "== navigation & zoning"
cp "$HERE/navcheck.test.ts" "$TEST"
(cd "$CC" && SURGERYCRAFT_CONTENT="$PACK" npx vitest run "packages/world/src/zz-surgerycraft-nav.test.ts")
