#!/usr/bin/env python3
"""Quality gates. Exit code 1 fails the pipeline.

Gates (configurable via env or flags):
  GATE_MIN_PASS_RATE  % of executed (non-skipped) tests that must pass   default 100
  GATE_MIN_TESTS      minimum number of executed tests (guards against an empty/crashed run)  default 20
  --coverage-xml PATH optional Cobertura file; fails below GATE_MIN_COVERAGE (default 80)
                      NOTE: black-box API/UI tests do not measure the app's code coverage; use this only
                      if you run tests against an instrumented build of your own code.

pytest xfail (known bugs) is reported as skipped in JUnit and excluded from the pass rate, but strict xfail
turns an unexpectedly FIXED bug into a failure, forcing the marker to be removed.
"""
import argparse
import os
import sys
from pathlib import Path

import defusedxml.ElementTree as ET  # report files come from CI artifacts: parse them hardened (XXE-safe)

REPORTS = Path(__file__).resolve().parent.parent / "reports"


def tally(xml_path: Path):
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    total = fail = skip = 0
    for s in suites:
        total += int(s.get("tests", 0))
        fail += int(s.get("failures", 0)) + int(s.get("errors", 0))
        skip += int(s.get("skipped", 0))
    return total, fail, skip


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default=str(REPORTS))
    ap.add_argument("--coverage-xml")
    args = ap.parse_args()
    min_rate = float(os.environ.get("GATE_MIN_PASS_RATE", 100))
    min_tests = int(os.environ.get("GATE_MIN_TESTS", 20))
    min_cov = float(os.environ.get("GATE_MIN_COVERAGE", 80))

    files = sorted(Path(args.reports).glob("*-junit.xml"))
    if not files:
        print("GATE FAIL: no JUnit reports found in", args.reports)
        return 1
    problems = []
    t_total = t_fail = t_skip = 0
    for f in files:
        total, fail, skip = tally(f)
        executed = total - skip
        rate = 100.0 if executed == 0 else (executed - fail) / executed * 100
        print(f"{f.name}: total={total} failed={fail} skipped/xfail={skip} pass-rate={rate:.1f}%")
        t_total, t_fail, t_skip = t_total + total, t_fail + fail, t_skip + skip
    executed = t_total - t_skip
    rate = 100.0 if executed == 0 else (executed - t_fail) / executed * 100
    if rate < min_rate:
        problems.append(f"pass rate {rate:.1f}% < required {min_rate}%")
    if executed < min_tests:
        problems.append(f"only {executed} tests executed (< {min_tests})")
    if args.coverage_xml:
        line_rate = float(ET.parse(args.coverage_xml).getroot().get("line-rate", 0)) * 100
        print(f"coverage: {line_rate:.1f}%")
        if line_rate < min_cov:
            problems.append(f"coverage {line_rate:.1f}% < required {min_cov}%")
    if problems:
        print("GATE FAIL:", "; ".join(problems))
        return 1
    print(f"GATE PASS: {executed - t_fail}/{executed} executed tests passed ({t_skip} known-bug/skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
