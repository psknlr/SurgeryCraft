#!/usr/bin/env python3
"""Fail when a test of the Case 126 regression list (tools/regressions.tsv) is missing or renamed.

Each line names a fixed interaction failure and the test that keeps it fixed (file and exact title). `tools/check.sh`
runs this first, so a regression test can never disappear quietly; CI (.github/workflows/integration.yml) runs check.sh.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    problems = []
    count = 0
    for n, line in enumerate((ROOT / "tools" / "regressions.tsv").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 4:
            problems.append(f"regressions.tsv:{n}: expected 4 tab-separated columns, got {len(parts)}")
            continue
        rid, _what, file, title = parts
        path = ROOT / file
        if not path.is_file():
            problems.append(f"regressions.tsv:{n} ({rid}): no file {file}")
            continue
        if f'it("{title}"' not in path.read_text(encoding="utf-8"):
            problems.append(f'regressions.tsv:{n} ({rid}): no test "{title}" in {file}')
            continue
        count += 1
    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        return 1
    print(f"regression list: {count} tests present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
