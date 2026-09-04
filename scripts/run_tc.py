#!/usr/bin/env python3
"""
Run a specific test case or all tests in a group according to ROM_TestPlan_LIFCL.md.

Usage:
    python3 scripts/run_tc.py info            # print quick test outline
    python3 scripts/run_tc.py test            # run Sim Only and DRC test suite
    python3 scripts/run_tc.py TC-ROM-001      # single test case
    python3 scripts/run_tc.py G1              # group 1 (Baseline)
    python3 scripts/run_tc.py TG-01           # alias for G1
    python3 scripts/run_tc.py DRC             # DRC parameter validation suite

Or via make:
    make info
    make test
    make tc-rom-001
    make tg-01
    make drc
"""

import os
import re
import shutil
import sys
import time
import subprocess
from dataclasses import dataclass

REPO_ROOT = os.environ.get("IP_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fixture(name):
    """Return absolute path to a testbench fixture file."""
    return os.path.join(REPO_ROOT, "testbench", name)


@dataclass
class TC:
    testcase: str                     # CoCoTB function name in tb_rom.py
    regmode: str        = "reg"
    rdata_width: int    = 18
    raddr_depth: int    = 1024
    resetmode: str      = "sync"
    output_clk_en: int  = 0
    ecc_enable: int     = 0
    init_mode: str      = "mem_file"
    init_file: str      = None        # None → auto-located by testbench
    init_file_format: str = "binary"
    family: str         = "common"
    test_type: str      = "Both"      # 'Both', 'Sim Only', 'Radiant Compilation'
    note: str           = ""


# ─── Full TC lookup table (TC-ROM-001 through TC-ROM-034) ────────────────────

TC_MAP = {
    # ── G1 · Baseline ────────────────────────────────────────────────────────
    "ROM-001": TC("tc_rom_001_default_config_read",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Both"),

    # ── G2 · RADDR_DEPTH ─────────────────────────────────────────────────────
    "ROM-002": TC("tc_rom_002_minimum_address_depth",
                  raddr_depth=2, rdata_width=1, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_2x1.bin"),
                  test_type="Radiant Compilation"),
    "ROM-003": TC("tc_rom_003_median_address_depth_full_range",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-004": TC("tc_rom_004_maximum_address_depth",
                  raddr_depth=65536, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_65536x18.bin"),
                  test_type="Radiant Compilation"),
    "ROM-005": TC("tc_rom_005_address_depth_at_budget",
                  raddr_depth=3024, rdata_width=512, regmode="reg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_3024x512.hex"),
                  test_type="Radiant Compilation"),
    "ROM-006": TC("tc_rom_006_non_power_of_two_depth",
                  raddr_depth=1000, rdata_width=8, regmode="reg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_1000x8.hex"),
                  test_type="Radiant Compilation"),

    # ── G3 · RDATA_WIDTH ─────────────────────────────────────────────────────
    "ROM-007": TC("tc_rom_007_minimum_data_width",
                  raddr_depth=1024, rdata_width=1, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x1.bin"),
                  test_type="Both"),
    "ROM-008": TC("tc_rom_008_median_data_width_walk_pattern",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18_walk.bin"),
                  test_type="Sim Only"),
    "ROM-009": TC("tc_rom_009_maximum_data_width_tiling",
                  raddr_depth=2048, rdata_width=512, regmode="reg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_2048x512.hex"),
                  test_type="Both"),
    "ROM-010": TC("tc_rom_010_data_width_36_wide_branch",
                  raddr_depth=512, rdata_width=36, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_512x36.bin"),
                  test_type="Radiant Compilation"),

    # ── G4 · REGMODE ─────────────────────────────────────────────────────────
    "ROM-011": TC("tc_rom_011_output_register_enabled_latency",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-012": TC("tc_rom_012_output_register_disabled_latency",
                  raddr_depth=1024, rdata_width=18, regmode="noreg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Both"),

    # ── G5 · RESETMODE ───────────────────────────────────────────────────────
    "ROM-013": TC("tc_rom_013_sync_reset_output_register",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Both"),
    "ROM-014": TC("tc_rom_014_async_reset_assertion",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="async",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Radiant Compilation"),

    # ── G6 · INIT_FILE_FORMAT ────────────────────────────────────────────────
    "ROM-015": TC("tc_rom_015_binary_format_initialization",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Both"),
    "ROM-016": TC("tc_rom_016_hex_format_initialization",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_1024x18.hex"),
                  test_type="Both"),

    # ── G7 · OUTPUT_CLK_EN ───────────────────────────────────────────────────
    "ROM-017": TC("tc_rom_017_output_clk_en_not_requested",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Radiant Compilation"),
    "ROM-018": TC("tc_rom_018_output_clk_en_requested",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Both"),

    # ── G8 · user_init_file ──────────────────────────────────────────────────
    "ROM-019": TC("tc_rom_019_comments_at_address_surplus",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_sparse.hex"),
                  test_type="Both"),

    # ── G9 · Cross-Parameter Legal Combinations ──────────────────────────────
    "ROM-020": TC("tc_rom_020_max_depth_separate_enable_hex",
                  raddr_depth=65536, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=1, init_file_format="hex", init_file=fixture("rom_65536x18.hex"),
                  test_type="Sim Only"),
    "ROM-021": TC("tc_rom_021_max_width_noreg_hex",
                  raddr_depth=2048, rdata_width=512, regmode="noreg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_2048x512.hex"),
                  test_type="Both"),
    "ROM-022": TC("tc_rom_022_at_budget_separate_enable_async_reset",
                  raddr_depth=3024, rdata_width=512, regmode="reg", resetmode="async",
                  output_clk_en=1, init_file_format="binary", init_file=fixture("rom_3024x512.bin"),
                  test_type="Radiant Compilation"),
    "ROM-023": TC("tc_rom_023_min_dimensions_noreg",
                  raddr_depth=2, rdata_width=1, regmode="noreg", resetmode="sync",
                  init_file_format="hex", init_file=fixture("rom_2x1.hex"),
                  test_type="Both"),

    # ── G10 · Port Behaviour ─────────────────────────────────────────────────
    "ROM-024": TC("tc_rom_024_rd_clk_en_freezes_memory_array",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-025": TC("tc_rom_025_rd_out_clk_en_freezes_output_register",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-026": TC("tc_rom_026_rd_en_as_second_series_enable",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-027": TC("tc_rom_027_rd_en_ignored_without_separate_enable",
                  raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync",
                  output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-028": TC("tc_rom_028_rst_inert_with_output_register_bypassed",
                  raddr_depth=1024, rdata_width=18, regmode="noreg", resetmode="sync",
                  output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"),
                  test_type="Sim Only"),
    "ROM-029": TC("tc_rom_029_rd_addr_above_configured_depth",
                  raddr_depth=1000, rdata_width=8, regmode="reg", resetmode="sync",
                  output_clk_en=0, init_file_format="hex", init_file=fixture("rom_1000x8.hex"),
                  test_type="Sim Only"),
    "ROM-030": TC("tc_rom_030_ecc_outputs_inert_and_dangling",
                  raddr_depth=1024, rdata_width=36, regmode="reg", resetmode="sync",
                  output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x36.bin"),
                  test_type="Both"),

    # ── G11 · DRC & Radiant Smoke ────────────────────────────────────────────
    "ROM-031": TC("tc_rom_031_memory_init_readonly_fill_unreachable",
                  test_type="Radiant Compilation"),
    "ROM-032": TC("tc_rom_032_init_data_update_control_hidden",
                  test_type="Radiant Compilation"),
    "ROM-033": TC("tc_rom_033_derived_readonly_settings",
                  raddr_depth=1000, rdata_width=8, init_file_format="hex",
                  test_type="Radiant Compilation"),
    "ROM-034": TC("tc_rom_034_default_param_smoke_test",
                  test_type="Radiant Compilation"),
}

# Group mapping (G1..G11)
TG_MAP = {
    "01": ["ROM-001"],
    "02": ["ROM-002", "ROM-003", "ROM-004", "ROM-005", "ROM-006"],
    "03": ["ROM-007", "ROM-008", "ROM-009", "ROM-010"],
    "04": ["ROM-011", "ROM-012"],
    "05": ["ROM-013", "ROM-014"],
    "06": ["ROM-015", "ROM-016"],
    "07": ["ROM-017", "ROM-018"],
    "08": ["ROM-019"],
    "09": ["ROM-020", "ROM-021", "ROM-022", "ROM-023"],
    "10": ["ROM-024", "ROM-025", "ROM-026", "ROM-027", "ROM-028", "ROM-029", "ROM-030"],
    "11": ["ROM-031", "ROM-032", "ROM-033", "ROM-034"],
}


def _artifact_paths(tc_id):
    """Return relative paths for artifacts."""
    safe_id = tc_id.lower().replace("_", "-")
    log_rel   = f"results/tc-{safe_id}.log"
    wlf_rel   = f"results/tc-{safe_id}.wlf"
    trace_rel = f"results/tc-{safe_id}_trace.v"
    return log_rel, wlf_rel, trace_rel


def _parse_log(log_path):
    """Parse a test log and return (status, sim_ns, real_s)."""
    if not os.path.isfile(log_path):
        return None
    status = "FAIL"
    sim_ns = None
    real_s = None
    with open(log_path, errors="ignore") as f:
        for line in f:
            if "TESTS=" in line:
                if "FAIL=0" in line and ("PASS=1" in line or "PASS=" in line):
                    status = "PASS"
                elif "FAIL=" in line and not "FAIL=0" in line:
                    status = "FAIL"
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        sim_ns = float(parts[-2])
                        real_s = float(parts[-1])
                    except ValueError:
                        pass
            if "REAL_TIME_S=" in line:
                try:
                    real_s = float(line.split("=")[1])
                except ValueError:
                    pass
    return status, sim_ns, real_s


def run_sim(tc_id, tc):
    """Invoke make sim for one TC. Returns exit code."""
    results_dir = os.path.join(REPO_ROOT, "results")
    sim_build   = os.path.join(REPO_ROOT, "sim_build", "tc-" + tc_id.lower())
    log_file    = os.path.join(results_dir, f"tc-{tc_id.lower()}.log")

    log_rel, wlf_rel, _ = _artifact_paths(tc_id)
    cmd = [
        "make", "-C", REPO_ROOT, "sim",
        "FAMILY="           + tc.family,
        "REGMODE="          + tc.regmode,
        "RDATA_WIDTH="      + str(tc.rdata_width),
        "RADDR_DEPTH="      + str(tc.raddr_depth),
        "RESETMODE="        + tc.resetmode,
        "OUTPUT_CLK_EN="    + str(tc.output_clk_en),
        "ECC_ENABLE="       + str(tc.ecc_enable),
        "INIT_MODE="        + tc.init_mode,
        "INIT_FILE_FORMAT=" + tc.init_file_format,
        "TESTCASE="         + tc.testcase,
        "SIM_BUILD="        + sim_build,
        "WLF_FILE="         + os.path.join(REPO_ROOT, wlf_rel),
    ]
    if tc.init_file is not None:
        cmd.append("INIT_FILE=" + tc.init_file)

    os.makedirs(results_dir, exist_ok=True)
    print("")
    print("=" * 66)
    print(f"  TC-{tc_id}  {tc.testcase} [{tc.test_type}]")
    print("=" * 66)

    t0 = time.time()
    with open(log_file, "w") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        proc.wait()
    real_s = time.time() - t0

    with open(log_file, "a") as log:
        log.write(f"REAL_TIME_S={real_s:.3f}\n")

    rc = proc.returncode
    if rc == 0:
        parsed = _parse_log(log_file)
        if parsed and parsed[0] == "FAIL":
            rc = 1
    return rc


def run_drc():
    """Run G11 DRC tests via pytest, capturing output to results/drc.log."""
    print("\n" + "=" * 66)
    print("  G11: DRC & Parameter Validation (pytest)")
    print("=" * 66)
    results_dir = os.path.join(REPO_ROOT, "results")
    os.makedirs(results_dir, exist_ok=True)
    log_file = os.path.join(results_dir, "drc.log")
    drc_path = os.path.join(REPO_ROOT, "src", "test_drc.py")
    cmd = ["pytest", drc_path, "-v"]
    with open(log_file, "w") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        proc.wait()
    return proc.returncode


def print_outline():
    """Print a quick outline of the IP's test situation."""
    # Discover IP name from metadata.xml or fallback
    raw_ip_name = "rom"
    ip_display = "ROM"
    ip_version = "2.5.0"
    meta_path = os.path.join(REPO_ROOT, "metadata.xml")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", errors="ignore") as f:
                content = f.read()
                m_name = re.search(r'<lsccip:name>(.*?)</lsccip:name>', content)
                m_disp = re.search(r'<lsccip:display_name>(.*?)</lsccip:display_name>', content)
                m_ver  = re.search(r'<lsccip:version>(.*?)</lsccip:version>', content)
                if m_name: raw_ip_name = m_name.group(1)
                if m_disp: ip_display = m_disp.group(1)
                if m_ver:  ip_version = m_ver.group(1)
        except Exception:
            pass

    ip_name = f"lscc_{raw_ip_name}" if not raw_ip_name.startswith("lscc_") else raw_ip_name

    # Count test cases by category strictly per Test Plan
    total_tcs = len(TC_MAP)
    both_cnt = sum(1 for tc in TC_MAP.values() if tc.test_type == "Both")
    sim_cnt  = sum(1 for tc in TC_MAP.values() if tc.test_type == "Sim Only")
    rad_cnt  = sum(1 for tc in TC_MAP.values() if tc.test_type == "Radiant Compilation")

    # Count DRC tests in test_drc.py
    drc_path = os.path.join(REPO_ROOT, "src", "test_drc.py")
    drc_test_count = 0
    if os.path.isfile(drc_path):
        with open(drc_path, "r", errors="ignore") as f:
            drc_test_count = sum(1 for line in f if line.strip().startswith("def test_"))

    # Count synthesizable wrappers / projects
    synth_dir = os.path.join(REPO_ROOT, "synth")
    synth_wrappers = []
    if os.path.isdir(synth_dir):
        synth_wrappers = [f for f in os.listdir(synth_dir) if f.endswith(".v") or f.endswith(".sv")]
    num_projects = len(synth_wrappers) if synth_wrappers else 1

    print("=" * 66)
    print(f"  IP Test Overview: {ip_name} (LIFCL v{ip_version})")
    print("=" * 66)
    print(f"  IP name:                        {ip_name} ({ip_display})")
    print(f"  Testgroups:                     {len(TG_MAP)} (G01–G10 Functional, G11 DRC)")
    print(f"  Testcases:                      {total_tcs} total (per Test Plan)")
    print(f"    ├── Both (Sim & Radiant):     {both_cnt}")
    print(f"    ├── Sim Only:                 {sim_cnt}")
    print(f"    └── Radiant Compilation:      {rad_cnt}")
    if drc_test_count > 0:
        print(f"  DRC Parameter Unit Tests:       {drc_test_count} (in src/test_drc.py for G11 & GUI rules)")
    print(f"  Synthesizable Radiant projects: {num_projects} ({ip_name}.rdf via `make prj_create`)")
    print("=" * 66)


def run_all_tests():
    """Run all simulation testgroups G01..G10, G11 DRC, and Radiant project compilation."""
    print("\n" + "=" * 66)
    print("  Running Full Test Suite (Simulation + DRC + Radiant Compilation)")
    print("=" * 66)
    failures = []

    # 1. Run all functional simulation testcases in TG_MAP (G01 .. G10)
    for grp_num in range(1, 11):
        grp_key = f"{grp_num:02d}"
        if grp_key in TG_MAP:
            tc_ids = TG_MAP[grp_key]
            for tid in tc_ids:
                tc = TC_MAP[tid]
                rc = run_sim(tid, tc)
                if rc != 0:
                    failures.append(tid)

    # 2. Run G11 DRC
    drc_rc = run_drc()
    if drc_rc != 0:
        failures.append("G11-DRC")

    # 3. Run Radiant project creation and compilation
    print("\n" + "=" * 66)
    print("  Running Radiant Project Creation & Compilation")
    print("=" * 66)
    cmd_prj = ["make", "-C", REPO_ROOT, "prj_create", "prj_compile"]
    proc = subprocess.run(cmd_prj)
    if proc.returncode != 0:
        failures.append("Radiant-Compilation")

    total_functional = sum(len(TG_MAP[f"{g:02d}"]) for g in range(1, 11) if f"{g:02d}" in TG_MAP)
    total_stages = total_functional + 2  # DRC + Radiant Compilation
    passed_stages = total_stages - len(failures)

    print("\n" + "=" * 66)
    print(f"  Overall Summary: {passed_stages}/{total_stages} test suites/stages passed")
    if failures:
        print(f"  Failed targets: {failures}")
    print("=" * 66 + "\n")
    return 1 if failures else 0


def _normalize_tc_arg(arg: str):
    """Normalize user argument to TC ID, Group ID, or special command."""
    u = arg.upper().replace("_", "-")
    if u in ("INFO", "--INFO", "-I", "-H", "--HELP", "HELP"):
        return "INFO", "cmd"

    if u in ("TEST", "ALL", "SIM-ONLY", "SIM_ONLY", "REGRESSION"):
        return "TEST", "cmd"

    # Group pattern (e.g. TG-01, G1, G01, TG-1)
    mg = re.match(r'^(?:TG-|G)(\d+)$', u)
    if mg:
        grp_num = int(mg.group(1))
        return f"G{grp_num:02d}", "group"

    if u in ("DRC", "TG-11", "G11"):
        return "G11", "group"

    # TC pattern (e.g. TC-ROM-001, ROM-001, TC-01, 001)
    m = re.match(r'^(?:TC-)?(?:ROM-)?(\d+)$', u)
    if m:
        tc_num = int(m.group(1))
        return f"ROM-{tc_num:03d}", "tc"

    return u, "unknown"


def main():
    if len(sys.argv) < 2:
        print_outline()
        sys.exit(0)

    target, kind = _normalize_tc_arg(sys.argv[1])

    if target == "INFO" or (kind == "cmd" and target == "INFO"):
        print_outline()
        sys.exit(0)

    if target == "TEST" or (kind == "cmd" and target == "TEST"):
        rc = run_all_tests()
        sys.exit(rc)

    if target == "G11" or (kind == "group" and target == "G11"):
        rc = run_drc()
        sys.exit(rc)

    if kind == "tc":
        if target not in TC_MAP:
            print(f"Error: Unknown testcase {target}. Available: {sorted(TC_MAP.keys())}")
            sys.exit(1)
        tc = TC_MAP[target]
        rc = run_sim(target, tc)
        sys.exit(rc)

    if kind == "group":
        grp_key = target[1:]  # "01", "02", etc.
        if grp_key not in TG_MAP:
            print(f"Error: Unknown group {target}. Available: G01 .. G11")
            sys.exit(1)

        tc_ids = TG_MAP[grp_key]
        failures = []
        for tid in tc_ids:
            tc = TC_MAP[tid]
            rc = run_sim(tid, tc)
            if rc != 0:
                failures.append(tid)

        print("\n" + "=" * 66)
        print(f"  Summary for {target}: {len(tc_ids) - len(failures)}/{len(tc_ids)} PASSED")
        if failures:
            print(f"  Failed testcases: {failures}")
        print("=" * 66 + "\n")
        sys.exit(1 if failures else 0)

    print(f"Error: Unrecognized test argument {sys.argv[1]}")
    sys.exit(1)


if __name__ == "__main__":
    main()
