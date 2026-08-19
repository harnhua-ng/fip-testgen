#!/usr/bin/env python3
"""
Run a specific test case or all tests in a group.

Usage:
    python3 scripts/run_tc.py TC-01-01        # single test case
    python3 scripts/run_tc.py TG-01           # all test cases in group 01
    python3 scripts/run_tc.py TG-10           # DRC tests (pytest, no simulator)

Or via make:
    make tc-01-01
    make tg-01
    make drc        # equivalent to make tg-10
"""

import os
import re
import shutil
import sys
import time
import subprocess
from dataclasses import dataclass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure local .venv is in PATH if present (prepend so it takes precedence)
for _vbin in [os.path.join(REPO_ROOT, ".venv", "bin"), os.path.join(REPO_ROOT, ".venv", "Scripts")]:
    if os.path.isdir(_vbin):
        os.environ["PATH"] = _vbin + os.pathsep + os.environ.get("PATH", "")
        break


def fixture(name):
    """Return the absolute path to a testbench fixture file."""
    return os.path.join(REPO_ROOT, "testbench", name)


@dataclass
class TC:
    testcase: str                     # CoCoTB function name in tb_rom.py
    regmode: str        = "noreg"
    rdata_width: int    = 36
    raddr_depth: int    = 512
    resetmode: str      = "sync"
    output_clk_en: int  = 0
    ecc_enable: int     = 0
    init_mode: str      = "all_one"
    init_file: str      = None        # None → Makefile default (rom_init.hex)
    init_file_format: str = "hex"
    family: str         = "LIFCL"
    note: str           = ""          # non-empty for always-skipped tests


# ─── TC lookup table ─────────────────────────────────────────────────────────

TC_MAP = {
    # ── TG-01  Basic Read ────────────────────────────────────────────────────
    "01-01": TC("tc_01_01_sequential_read_noreg",
                regmode="noreg", rdata_width=36, raddr_depth=512,
                init_mode="mem_file", family="common"),
    "01-02": TC("tc_01_02_sequential_read_reg",
                regmode="reg", rdata_width=36, raddr_depth=512),
    "01-03": TC("tc_01_03_full_sweep_noreg",
                regmode="noreg", rdata_width=36, raddr_depth=512),
    "01-04": TC("tc_01_04_full_sweep_reg",
                regmode="reg", rdata_width=36, raddr_depth=512),
    "01-05": TC("tc_01_05_boundary_addresses",
                regmode="reg", rdata_width=18, raddr_depth=1024),
    "01-06": TC("tc_01_06_random_addresses",
                regmode="reg", rdata_width=36, raddr_depth=512),
    "01-07": TC("tc_01_07_repeated_address",
                regmode="noreg", rdata_width=9, raddr_depth=2048),

    # ── TG-02  Read Enable ───────────────────────────────────────────────────
    "02-01": TC("tc_02_01_rd_en_zero_at_start",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),
    "02-02": TC("tc_02_02_rd_en_deasserted_mid_seq",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),
    "02-03": TC("tc_02_03_rd_en_toggle_every_cycle",
                regmode="noreg", rdata_width=18, raddr_depth=1024),
    "02-04": TC("tc_02_04_rd_en_resumes",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),

    # ── TG-03  Read Clock Enable ─────────────────────────────────────────────
    "03-01": TC("tc_03_01_clk_en_zero_holds_noreg",
                regmode="noreg", rdata_width=36, raddr_depth=512),
    "03-02": TC("tc_03_02_clk_en_zero_holds_reg",
                regmode="reg", rdata_width=36, raddr_depth=512),
    "03-03": TC("tc_03_03_clk_en_reassertion",
                regmode="reg", rdata_width=36, raddr_depth=512),
    "03-04": TC("tc_03_04_clk_en_toggle_pattern",
                regmode="noreg", rdata_width=18, raddr_depth=1024),
    "03-05": TC("tc_03_05_cascaded_clk_en",
                regmode="reg", rdata_width=36, raddr_depth=1024),

    # ── TG-04  Output Clock Enable ───────────────────────────────────────────
    "04-01": TC("tc_04_01_out_clk_en_zero_freezes_output",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),
    "04-02": TC("tc_04_02_out_clk_en_normal_operation",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),
    "04-03": TC("tc_04_03_out_clk_en_toggle_mid_seq",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=1),
    "04-04": TC("tc_04_04_output_clk_en_param_zero_no_effect",
                regmode="reg", rdata_width=36, raddr_depth=512, output_clk_en=0),
    "04-05": TC("tc_04_05_both_enables_deasserted",
                regmode="reg", rdata_width=18, raddr_depth=1024, output_clk_en=1),

    # ── TG-05  Reset Behavior ────────────────────────────────────────────────
    "05-01": TC("tc_05_01_sync_reset_clears_output",
                regmode="reg", rdata_width=36, raddr_depth=512, resetmode="sync"),
    "05-02": TC("tc_05_02_sync_reset_during_read",
                regmode="reg", rdata_width=36, raddr_depth=512, resetmode="sync"),
    "05-03": TC("tc_05_03_sync_reset_release_resumes",
                regmode="reg", rdata_width=36, raddr_depth=512, resetmode="sync"),
    "05-04": TC("tc_05_04_async_reset_clears_immediately",
                regmode="reg", rdata_width=36, raddr_depth=512, resetmode="async"),
    "05-05": TC("tc_05_05_async_reset_release_resumes",
                regmode="reg", rdata_width=36, raddr_depth=512, resetmode="async"),
    "05-06": TC("tc_05_06_noreg_reset_has_no_effect",
                regmode="noreg", rdata_width=36, raddr_depth=512, resetmode="sync"),

    # ── TG-06  Memory Initialization ─────────────────────────────────────────
    "06-01": TC("tc_06_01_all_zero_init",
                regmode="noreg", rdata_width=36, raddr_depth=512, init_mode="all_zero"),
    "06-02": TC("tc_06_02_all_one_init",
                regmode="noreg", rdata_width=36, raddr_depth=512, init_mode="all_one"),
    "06-03": TC("tc_06_03_mem_file_hex",
                regmode="noreg", rdata_width=36, raddr_depth=512,
                init_mode="mem_file", init_file_format="hex"),
    "06-04": TC("tc_06_04_mem_file_binary",
                regmode="noreg", rdata_width=18, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_18_1024.bin"),
                init_file_format="binary"),
    "06-05": TC("tc_06_05_mem_file_alternating_pattern",
                regmode="noreg", rdata_width=9, raddr_depth=2048,
                init_mode="mem_file",
                init_file=fixture("rom_init_9_2048_alt.hex")),
    "06-06": TC("tc_06_06_mem_file_addr_as_data",
                regmode="noreg", rdata_width=36, raddr_depth=512,
                init_mode="mem_file", init_file_format="hex"),
    "06-07": TC("tc_06_07_all_zero_narrow",
                regmode="noreg", rdata_width=1, raddr_depth=16384, init_mode="all_zero"),
    "06-08": TC("tc_06_08_mem_file_binary_narrow",
                regmode="noreg", rdata_width=4, raddr_depth=4096,
                init_mode="mem_file",
                init_file=fixture("rom_init_4_4096.bin"),
                init_file_format="binary"),

    # ── TG-07  LIFCL EBR Tile Configuration Coverage ─────────────────────────
    "07-01": TC("tc_07_01_minimum_config",
                regmode="noreg", rdata_width=1, raddr_depth=2, init_mode="all_zero"),
    "07-02": TC("tc_07_02_1bit_max_depth",
                regmode="noreg", rdata_width=1, raddr_depth=16384,
                init_mode="mem_file",
                init_file=fixture("rom_init_1_16384.hex")),
    "07-03": TC("tc_07_03_2bit_8192",
                regmode="noreg", rdata_width=2, raddr_depth=8192,
                init_mode="mem_file",
                init_file=fixture("rom_init_2_8192.hex")),
    "07-04": TC("tc_07_04_4bit_4096",
                regmode="noreg", rdata_width=4, raddr_depth=4096,
                init_mode="mem_file",
                init_file=fixture("rom_init_4_4096.hex")),
    "07-05": TC("tc_07_05_9bit_2048_parity",
                regmode="noreg", rdata_width=9, raddr_depth=2048,
                init_mode="mem_file",
                init_file=fixture("rom_init_9_2048_alt.hex")),
    "07-06": TC("tc_07_06_18bit_1024_parity",
                regmode="noreg", rdata_width=18, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_18_1024.hex")),
    "07-07": TC("tc_07_07_36bit_512_default",
                regmode="noreg", rdata_width=36, raddr_depth=512,
                init_mode="mem_file"),
    "07-08": TC("tc_07_08_non_aligned_width",
                regmode="noreg", rdata_width=12, raddr_depth=512,
                init_mode="mem_file",
                init_file=fixture("rom_init_12_512.hex")),

    # ── TG-08  EBR Cascading ─────────────────────────────────────────────────
    "08-01": TC("tc_08_01_addr_cascade_x2",
                regmode="noreg", rdata_width=36, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_36_1024.hex")),
    "08-02": TC("tc_08_02_addr_cascade_x4",
                regmode="noreg", rdata_width=36, raddr_depth=2048,
                init_mode="mem_file",
                init_file=fixture("rom_init_36_2048.hex")),
    "08-03": TC("tc_08_03_data_cascade_x2",
                regmode="noreg", rdata_width=72, raddr_depth=512,
                init_mode="mem_file",
                init_file=fixture("rom_init_72_512.hex")),
    "08-04": TC("tc_08_04_data_cascade_x4",
                regmode="noreg", rdata_width=144, raddr_depth=512,
                init_mode="mem_file",
                init_file=fixture("rom_init_144_512.hex")),
    "08-05": TC("tc_08_05_both_cascades",
                regmode="noreg", rdata_width=72, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_72_1024.hex")),
    "08-06": TC("tc_08_06_bank_boundary_read",
                regmode="noreg", rdata_width=36, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_36_1024.hex")),
    "08-07": TC("tc_08_07_addr_cascade_clk_en_toggle",
                regmode="noreg", rdata_width=36, raddr_depth=1024,
                init_mode="mem_file",
                init_file=fixture("rom_init_36_1024.hex")),
    "08-08": TC("tc_08_08_addr_cascade_reg_mode",
                regmode="reg", rdata_width=36, raddr_depth=2048,
                init_mode="mem_file",
                init_file=fixture("rom_init_36_2048.hex")),

    # ── TG-09  ECC ───────────────────────────────────────────────────────────
    "09-01": TC("tc_09_01_ecc_disabled_outputs_zero",
                regmode="noreg", rdata_width=36, raddr_depth=512, ecc_enable=0),
    "09-02": TC("tc_09_02_ecc_enabled_clean_data",
                regmode="noreg", rdata_width=32, raddr_depth=512, ecc_enable=1),
    "09-03": TC("tc_09_03_ecc_minimum_width",
                regmode="noreg", rdata_width=32, raddr_depth=512, ecc_enable=1),
    "09-04": TC("tc_09_04_ecc_maximum_width",
                regmode="noreg", rdata_width=64, raddr_depth=512, ecc_enable=1),
    "09-05": TC("tc_09_05_sec_single_bit_error",
                regmode="noreg", rdata_width=32, raddr_depth=512, ecc_enable=1,
                note="Always skipped — set ECC_ERROR_INJECT=1 and supply a pre-corrupted fixture"),
    "09-06": TC("tc_09_06_ded_double_bit_error",
                regmode="noreg", rdata_width=32, raddr_depth=512, ecc_enable=1,
                note="Always skipped — set ECC_ERROR_INJECT=1 and supply a pre-corrupted fixture"),
    "09-07": TC("tc_09_07_ecc_error_recovery",
                regmode="noreg", rdata_width=32, raddr_depth=512, ecc_enable=1,
                note="Always skipped — set ECC_ERROR_INJECT=1 and supply a pre-corrupted fixture"),
}

# Ordered TC IDs per group
TG_MAP = {
    "01": ["01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07"],
    "02": ["02-01", "02-02", "02-03", "02-04"],
    "03": ["03-01", "03-02", "03-03", "03-04", "03-05"],
    "04": ["04-01", "04-02", "04-03", "04-04", "04-05"],
    "05": ["05-01", "05-02", "05-03", "05-04", "05-05", "05-06"],
    "06": ["06-01", "06-02", "06-03", "06-04", "06-05", "06-06", "06-07", "06-08"],
    "07": ["07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07", "07-08"],
    "08": ["08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08"],
    "09": ["09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07"],
    "10": [],   # DRC — handled via pytest, not make sim
}


# ─── simulator invocation ────────────────────────────────────────────────────

def run_sim(tc_id, tc):
    """Invoke make sim with the parameters for one TC. Returns the exit code."""
    results_dir = os.path.join(REPO_ROOT, "results")
    sim_build   = os.path.join(REPO_ROOT, "sim_build", "tc-" + tc_id)
    log_file    = os.path.join(results_dir, "tc-" + tc_id + ".log")

    log_rel, wlf_rel, _, _ = _artifact_paths(tc_id)
    tc_plusarg = tc_id.replace("-", "_")
    flow = os.getenv("FLOW", "cocotb")
    cmd = [
        "make", "-C", REPO_ROOT, "sim",
        "FLOW="            + flow,
        "FAMILY="          + tc.family,
        "REGMODE="         + tc.regmode,
        "RDATA_WIDTH="     + str(tc.rdata_width),
        "RADDR_DEPTH="     + str(tc.raddr_depth),
        "RESETMODE="       + tc.resetmode,
        "OUTPUT_CLK_EN="   + str(tc.output_clk_en),
        "ECC_ENABLE="      + str(tc.ecc_enable),
        "INIT_MODE="       + tc.init_mode,
        "INIT_FILE_FORMAT=" + tc.init_file_format,
        "TESTCASE="        + tc.testcase,
        "TC="              + tc_plusarg,
        "SIM_BUILD="       + sim_build,
        "WLF_FILE="        + os.path.join(REPO_ROOT, wlf_rel),
    ]
    if tc.init_file is not None:
        cmd.append("INIT_FILE=" + tc.init_file)

    os.makedirs(results_dir, exist_ok=True)
    print("")
    print("=" * 66)
    print(f"  TC-{tc_id}  {tc.testcase} (FLOW={flow})")
    print("=" * 66)

    t0 = time.time()
    with open(log_file, "w") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        proc.wait()
    real_s = time.time() - t0

    with open(log_file, "a") as log:
        log.write(f"REAL_TIME_S={real_s:.3f}\n")

    # Copy compiled work library to results/ so the engineer can reload
    # the simulation in QuestaSim without keeping sim_build/ around.
    work_src = os.path.join(sim_build, "work")
    work_dst = os.path.join(results_dir, "tc-" + tc_id, "work")
    if os.path.isdir(work_src):
        if os.path.exists(work_dst):
            shutil.rmtree(work_dst)
        shutil.copytree(work_src, work_dst)

    rc = proc.returncode
    if rc == 0:
        parsed = _parse_log(log_file)
        if parsed and parsed[0] == "FAIL":
            rc = 1
    return rc


def run_drc():
    """Run TG-10 DRC tests via pytest."""
    cmd = ["make", "-C", REPO_ROOT, "drc"]
    print("")
    print("=" * 66)
    print("  TG-10  DRC and Parameter Validation  (pytest)")
    print("=" * 66)
    return subprocess.run(cmd).returncode


# ─── log parsing and group summary ──────────────────────────────────────────

# Matches CoCoTB result rows: ** <testname>  PASS|FAIL|SKIP  sim_ns  real_s  ratio **
_RESULT_RE = re.compile(
    r'\*\*\s+(\S+)\s+(PASS|FAIL|SKIP)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\*\*'
)
_PASS_RE = re.compile(r'SIMULATION PASSED')
_FAIL_RE = re.compile(r'SIMULATION FAILED')
_SIM_TIME_RE = re.compile(r'#\s+Time:\s+([\d.]+)\s+ns', re.IGNORECASE)
_REAL_TIME_RE = re.compile(r'REAL_TIME_S=([\d.]+)')


def _parse_log(log_file):
    """Return (status, sim_ns, real_s, ratio) from CoCoTB or Verilog testbench log, or None."""
    status = None
    sim_ns = None
    real_s = None
    try:
        with open(log_file) as f:
            for line in f:
                # Check cocotb table first
                m = _RESULT_RE.search(line)
                if m and m.group(1) != "TEST":
                    return m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5))
                # Check Verilog displays
                if _PASS_RE.search(line):
                    status = "PASS"
                elif _FAIL_RE.search(line):
                    status = "FAIL"
                m_sim = _SIM_TIME_RE.search(line)
                if m_sim:
                    sim_ns = float(m_sim.group(1))
                m_real = _REAL_TIME_RE.search(line)
                if m_real:
                    real_s = float(m_real.group(1))
    except OSError:
        pass
    if status is not None:
        return status, sim_ns, real_s, None
    return None


def _artifact_paths(tc_id):
    """Return (log_relpath, wlf_relpath, work_relpath, trace_relpath) relative to REPO_ROOT."""
    stem = "tc-" + tc_id
    trace_path = os.path.join("results", stem + "_trace.v")
    trace_display = trace_path if os.path.isfile(os.path.join(REPO_ROOT, trace_path)) else "--"
    work_path = os.path.join("results", stem, "work")
    work_display = work_path if os.path.isdir(os.path.join(REPO_ROOT, work_path)) else "--"
    return (
        os.path.join("results", stem + ".log"),
        os.path.join("results", stem + ".wlf"),
        work_display,
        trace_display,
    )


def _print_group_summary(tg_id, tc_ids, failures):
    results_dir = os.path.join(REPO_ROOT, "results")

    rows = []
    for tc_id in tc_ids:
        tc     = TC_MAP[tc_id]
        log    = os.path.join(results_dir, "tc-" + tc_id + ".log")
        parsed = _parse_log(log)
        if parsed:
            status, sim_ns, real_s, _ = parsed
        else:
            status = "FAIL" if tc_id in failures else "SKIP"
            sim_ns = real_s = None
        log_rel, wlf_rel, work_rel, trace_rel = _artifact_paths(tc_id)
        rows.append((tc_id, status, sim_ns, real_s, log_rel, wlf_rel, work_rel, trace_rel))

    # ── Artifacts table ───────────────────────────────────────────────────
    log_w  = max(len(r[4]) for r in rows)
    wlf_w  = max(len(r[5]) for r in rows)
    work_w = max(max(len(r[6]) for r in rows), len("WORK DIR"))
    trc_w  = max(max(len(r[7]) for r in rows), len("VERILOG TRACE"))
    art_W  = 10 + 2 + log_w + 2 + wlf_w + 2 + work_w + 2 + trc_w + 2
    print("")
    print("=" * art_W)
    print(f"  TG-{tg_id} — Artifacts")
    print("=" * art_W)
    print(f"  {'TC':<10}  {'LOG':<{log_w}}  {'WAVEFORM':<{wlf_w}}  {'WORK DIR':<{work_w}}  {'VERILOG TRACE':<{trc_w}}")
    print("  " + "-" * (art_W - 2))
    for tc_id, status, sim_ns, real_s, log_rel, wlf_rel, work_rel, trace_rel in rows:
        print(f"  {'TC-' + tc_id:<10}  {log_rel:<{log_w}}  {wlf_rel:<{wlf_w}}  {work_rel:<{work_w}}  {trace_rel:<{trc_w}}")

    # ── Results table ─────────────────────────────────────────────────────
    res_W = 58
    print("")
    print("=" * res_W)
    print(f"  TG-{tg_id} — Results")
    print("=" * res_W)
    print(f"  {'TC':<10}  {'STATUS':>6}  {'SIM TIME (ns)':>13}  {'REAL TIME (s)':>13}")
    print("  " + "-" * (res_W - 2))

    pass_c = fail_c = skip_c = 0
    total_ns = total_real = 0.0
    for tc_id, status, sim_ns, real_s, log_rel, wlf_rel, work_rel, trace_rel in rows:
        if   status == "PASS": pass_c += 1
        elif status == "FAIL": fail_c += 1
        else:                  skip_c += 1
        if sim_ns is not None:
            total_ns   += sim_ns
            total_real += real_s
        ns_s    = f"{sim_ns:>13.2f}" if sim_ns is not None else f"{'--':>13}"
        real_s2 = f"{real_s:>13.2f}" if real_s is not None else f"{'--':>13}"
        print(f"  {'TC-' + tc_id:<10}  {status:>6}  {ns_s}  {real_s2}")

    n = len(rows)
    print("  " + "-" * (res_W - 2))
    print(f"  TESTS={n}  PASS={pass_c}  FAIL={fail_c}  SKIP={skip_c}  {total_ns:>13.2f}  {total_real:>13.2f}")
    print("=" * res_W)
    if failures:
        print(f"  TG-{tg_id}: {len(failures)} FAILED — {', '.join('TC-' + f for f in failures)}")
    else:
        print(f"  TG-{tg_id}: all {n} passed")
    print("=" * res_W)


# ─── parsing ─────────────────────────────────────────────────────────────────

def _strip_prefix(s, prefix):
    """Python 3.8-compatible str.removeprefix."""
    return s[len(prefix):] if s.startswith(prefix) else s


def parse_arg(arg):
    """Return ("tc", "XX-YY") or ("tg", "XX") from any reasonable spelling."""
    upper = arg.upper()
    if upper.startswith("TC-"):
        return "tc", _strip_prefix(upper, "TC-")
    if upper.startswith("TG-"):
        return "tg", _strip_prefix(upper, "TG-").zfill(2)
    # bare forms: "01-01" → tc, "01" → tg
    if "-" in upper:
        return "tc", upper
    if upper.isdigit():
        return "tg", upper.zfill(2)
    return None, None


# ─── entry point ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: run_tc.py TC-XX-YY | TG-XX")

    kind, ident = parse_arg(sys.argv[1])
    if kind is None:
        sys.exit("Unrecognised argument: " + repr(sys.argv[1]) +
                 "\nExpected TC-XX-YY or TG-XX")

    if kind == "tc":
        if ident not in TC_MAP:
            sys.exit("Unknown test case: TC-" + ident +
                     "\nAvailable: " + ", ".join("TC-" + k for k in sorted(TC_MAP)))
        tc = TC_MAP[ident]
        if tc.note:
            print("NOTE  TC-" + ident + ": " + tc.note)
        sys.exit(run_sim(ident, tc))

    else:  # tg
        if ident not in TG_MAP:
            sys.exit("Unknown test group: TG-" + ident +
                     "\nAvailable: TG-01 … TG-10")
        if ident == "10":
            sys.exit(run_drc())

        tc_ids   = TG_MAP[ident]
        failures = []
        for tc_id in tc_ids:
            tc = TC_MAP[tc_id]
            if tc.note:
                print("NOTE  TC-" + tc_id + ": " + tc.note)
            rc = run_sim(tc_id, tc)
            if rc != 0:
                failures.append(tc_id)

        _print_group_summary(ident, tc_ids, set(failures))
        if failures:
            sys.exit(1)


if __name__ == "__main__":
    main()
