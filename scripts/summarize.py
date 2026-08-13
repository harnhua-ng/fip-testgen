#!/usr/bin/env python3
"""
Scan results/*.log for CoCoTB result tables and write a Markdown summary.

Usage:
    python3 scripts/summarize.py                  # prints to stdout
    python3 scripts/summarize.py results/summary.md  # writes to file
"""
import re
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"

# CoCoTB result table patterns
RE_TEST = re.compile(
    r'\*\*\s+tb_\w+\.(\w+)\s+(PASS|FAIL|SKIP)\s'
)
RE_TOTALS = re.compile(
    r'\*\*\s+TESTS=(\d+)\s+PASS=(\d+)\s+FAIL=(\d+)\s+SKIP=(\d+)'
)

STATUS_MARK = {"PASS": "✓", "FAIL": "✗", "SKIP": "—"}


def parse_log(path: Path):
    tests = []
    totals = {}
    for line in path.read_text(errors="replace").splitlines():
        m = RE_TEST.search(line)
        if m:
            tests.append((m.group(1), m.group(2)))
            continue
        m = RE_TOTALS.search(line)
        if m:
            totals = {
                "total": int(m.group(1)),
                "pass":  int(m.group(2)),
                "fail":  int(m.group(3)),
                "skip":  int(m.group(4)),
            }
    return tests, totals


def render(output):
    log_files = sorted(RESULTS_DIR.glob("*.log"))
    if not log_files:
        output.write(f"No log files found in {RESULTS_DIR}\n")
        return

    overall = []
    lines = ["# Simulation Summary\n"]

    for log in log_files:
        config = log.stem
        tests, totals = parse_log(log)

        if not tests and not totals:
            continue

        lines.append(f"\n## {config}\n")
        lines.append("| Test | Status |")
        lines.append("|------|--------|")
        for name, status in tests:
            mark = STATUS_MARK.get(status, status)
            lines.append(f"| `{name}` | {mark} {status} |")

        if totals:
            p, f, s, t = totals["pass"], totals["fail"], totals["skip"], totals["total"]
            lines.append(
                f"\n**PASS: {p} &nbsp; FAIL: {f} &nbsp; SKIP: {s} &nbsp; TOTAL: {t}**\n"
            )
            overall.append((config, p, f, s, t))

    if len(overall) > 1:
        lines.append("\n---\n\n## Overall\n")
        lines.append("| Config | PASS | FAIL | SKIP | TOTAL |")
        lines.append("|--------|-----:|-----:|-----:|------:|")
        grand = [0, 0, 0, 0]
        for config, p, f, s, t in overall:
            lines.append(f"| `{config}` | {p} | {f} | {s} | {t} |")
            grand[0] += p; grand[1] += f; grand[2] += s; grand[3] += t
        lines.append(
            f"| **Total** | **{grand[0]}** | **{grand[1]}** | **{grand[2]}** | **{grand[3]}** |"
        )

    output.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        out_path = Path(sys.argv[1])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            render(f)
        print(f"Written to {out_path}")
    else:
        render(sys.stdout)
