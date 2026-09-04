#!/usr/bin/env python3
"""
Unified Test Runner for Lattice LIFCL IP Cores (ROM, FIFO_DC, PLL).

Usage:
    python3 scripts/run_tc.py info            # print quick test outline
    python3 scripts/run_tc.py test            # run full regression test suite (Sim + DRC + Radiant Compilation)
    python3 scripts/run_tc.py TC-ROM-001      # single test case (or TC-FIFODC-001, TC-PLL-001)
    python3 scripts/run_tc.py G1              # group 1
    python3 scripts/run_tc.py TG-01           # alias for G1
    python3 scripts/run_tc.py DRC             # DRC parameter validation suite

Or via make:
    make info
    make test
    make tc-rom-001 / make tc-fifodc-001 / make tc-pll-001
    make tg-01
    make drc
"""

import os
import re
import math
import shutil
import sys
import time
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Any

REPO_ROOT = os.environ.get("IP_ROOT") or os.getcwd()


def fixture(name):
    """Return absolute path to a testbench fixture file."""
    return os.path.join(REPO_ROOT, "testbench", name)


def detect_ip_type() -> str:
    """Detect current IP core type (rom, fifo_dc, or pll)."""
    meta_path = os.path.join(REPO_ROOT, "metadata.xml")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", errors="ignore") as f:
                content = f.read()
                m_name = re.search(r'<lsccip:name>(.*?)</lsccip:name>', content)
                if m_name:
                    name = m_name.group(1).lower()
                    if "fifo" in name:
                        return "fifo_dc"
                    if "pll" in name:
                        return "pll"
                    if "rom" in name:
                        return "rom"
        except Exception:
            pass

    # Fallback to directory name
    dname = os.path.basename(REPO_ROOT).lower()
    if "fifo" in dname:
        return "fifo_dc"
    if "pll" in dname:
        return "pll"
    return "rom"


# ══════════════════════════════════════════════════════════════════════════════
# 1. ROM IP Definition (34 test cases, G01..G11)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class RomTC:
    testcase: str
    regmode: str          = "reg"
    rdata_width: int      = 18
    raddr_depth: int      = 1024
    resetmode: str        = "sync"
    output_clk_en: int    = 0
    ecc_enable: int       = 0
    init_mode: str        = "mem_file"
    init_file: str        = None
    init_file_format: str = "binary"
    family: str           = "common"
    test_type: str        = "Both"  # 'Both', 'Sim Only', 'Radiant Compilation'
    note: str             = ""

    def get_sim_args(self) -> Dict[str, str]:
        args = {
            "FAMILY": self.family,
            "REGMODE": self.regmode,
            "RDATA_WIDTH": str(self.rdata_width),
            "RADDR_DEPTH": str(self.raddr_depth),
            "RESETMODE": self.resetmode,
            "OUTPUT_CLK_EN": str(self.output_clk_en),
            "ECC_ENABLE": str(self.ecc_enable),
            "INIT_MODE": self.init_mode,
            "INIT_FILE_FORMAT": self.init_file_format,
        }
        if self.init_file is not None:
            args["INIT_FILE"] = self.init_file
        return args


ROM_TC_MAP = {
    "ROM-001": RomTC("tc_rom_001_default_config_read", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Both"),
    "ROM-002": RomTC("tc_rom_002_minimum_address_depth", raddr_depth=2, rdata_width=1, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_2x1.bin"), test_type="Radiant Compilation"),
    "ROM-003": RomTC("tc_rom_003_median_address_depth_full_range", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-004": RomTC("tc_rom_004_maximum_address_depth", raddr_depth=65536, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_65536x18.bin"), test_type="Radiant Compilation"),
    "ROM-005": RomTC("tc_rom_005_address_depth_at_budget", raddr_depth=3024, rdata_width=512, regmode="reg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_3024x512.hex"), test_type="Radiant Compilation"),
    "ROM-006": RomTC("tc_rom_006_non_power_of_two_depth", raddr_depth=1000, rdata_width=8, regmode="reg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_1000x8.hex"), test_type="Radiant Compilation"),
    "ROM-007": RomTC("tc_rom_007_minimum_data_width", raddr_depth=1024, rdata_width=1, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x1.bin"), test_type="Both"),
    "ROM-008": RomTC("tc_rom_008_median_data_width_walk_pattern", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18_walk.bin"), test_type="Sim Only"),
    "ROM-009": RomTC("tc_rom_009_maximum_data_width_tiling", raddr_depth=2048, rdata_width=512, regmode="reg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_2048x512.hex"), test_type="Both"),
    "ROM-010": RomTC("tc_rom_010_data_width_36_wide_branch", raddr_depth=512, rdata_width=36, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_512x36.bin"), test_type="Radiant Compilation"),
    "ROM-011": RomTC("tc_rom_011_output_register_enabled_latency", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-012": RomTC("tc_rom_012_output_register_disabled_latency", raddr_depth=1024, rdata_width=18, regmode="noreg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Both"),
    "ROM-013": RomTC("tc_rom_013_sync_reset_output_register", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Both"),
    "ROM-014": RomTC("tc_rom_014_async_reset_assertion", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="async", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Radiant Compilation"),
    "ROM-015": RomTC("tc_rom_015_binary_format_initialization", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Both"),
    "ROM-016": RomTC("tc_rom_016_hex_format_initialization", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_1024x18.hex"), test_type="Both"),
    "ROM-017": RomTC("tc_rom_017_output_clk_en_not_requested", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Radiant Compilation"),
    "ROM-018": RomTC("tc_rom_018_output_clk_en_requested", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Both"),
    "ROM-019": RomTC("tc_rom_019_comments_at_address_surplus", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_sparse.hex"), test_type="Both"),
    "ROM-020": RomTC("tc_rom_020_max_depth_separate_enable_hex", raddr_depth=65536, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1, init_file_format="hex", init_file=fixture("rom_65536x18.hex"), test_type="Sim Only"),
    "ROM-021": RomTC("tc_rom_021_max_width_noreg_hex", raddr_depth=2048, rdata_width=512, regmode="noreg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_2048x512.hex"), test_type="Both"),
    "ROM-022": RomTC("tc_rom_022_at_budget_separate_enable_async_reset", raddr_depth=3024, rdata_width=512, regmode="reg", resetmode="async", output_clk_en=1, init_file_format="binary", init_file=fixture("rom_3024x512.bin"), test_type="Radiant Compilation"),
    "ROM-023": RomTC("tc_rom_023_min_dimensions_noreg", raddr_depth=2, rdata_width=1, regmode="noreg", resetmode="sync", init_file_format="hex", init_file=fixture("rom_2x1.hex"), test_type="Both"),
    "ROM-024": RomTC("tc_rom_024_rd_clk_en_freezes_memory_array", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-025": RomTC("tc_rom_025_rd_out_clk_en_freezes_output_register", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-026": RomTC("tc_rom_026_rd_en_as_second_series_enable", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-027": RomTC("tc_rom_027_rd_en_ignored_without_separate_enable", raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-028": RomTC("tc_rom_028_rst_inert_with_output_register_bypassed", raddr_depth=1024, rdata_width=18, regmode="noreg", resetmode="sync", output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x18.bin"), test_type="Sim Only"),
    "ROM-029": RomTC("tc_rom_029_rd_addr_above_configured_depth", raddr_depth=1000, rdata_width=8, regmode="reg", resetmode="sync", output_clk_en=0, init_file_format="hex", init_file=fixture("rom_1000x8.hex"), test_type="Sim Only"),
    "ROM-030": RomTC("tc_rom_030_ecc_outputs_inert_and_dangling", raddr_depth=1024, rdata_width=36, regmode="reg", resetmode="sync", output_clk_en=0, init_file_format="binary", init_file=fixture("rom_1024x36.bin"), test_type="Both"),
    "ROM-031": RomTC("tc_rom_031_memory_init_readonly_fill_unreachable", test_type="Radiant Compilation"),
    "ROM-032": RomTC("tc_rom_032_init_data_update_control_hidden", test_type="Radiant Compilation"),
    "ROM-033": RomTC("tc_rom_033_derived_readonly_settings", raddr_depth=1000, rdata_width=8, init_file_format="hex", test_type="Radiant Compilation"),
    "ROM-034": RomTC("tc_rom_034_default_param_smoke_test", test_type="Radiant Compilation"),
}

ROM_TG_MAP = {
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


# ══════════════════════════════════════════════════════════════════════════════
# 2. FIFO_DC IP Definition (53 test cases, G01..G24)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class FifoDcTC:
    testcase: str
    waddr_depth: int               = 512
    wdata_width: int               = 36
    raddr_depth: int               = 512
    rdata_width: int               = 36
    fifo_controller: str           = "FABRIC"
    fwft: int                      = 0
    force_fast_controller: int     = 0
    implementation: str            = "EBR"
    regmode: str                   = "reg"
    resetmode: str                 = "async"
    enable_almost_full_flag: str   = "TRUE"
    almost_full_assertion: str     = "static-dual"
    almost_full_assert_lvl: int    = 511
    almost_full_deassert_lvl: int  = 510
    enable_almost_empty_flag: str  = "TRUE"
    almost_empty_assertion: str    = "static-dual"
    almost_empty_assert_lvl: int   = 1
    almost_empty_deassert_lvl: int = 2
    enable_data_count_wr: str      = "FALSE"
    enable_data_count_rd: str      = "FALSE"
    family: str                    = "LIFCL"
    test_type: str                 = "Both"
    note: str                      = ""

    def get_sim_args(self) -> Dict[str, str]:
        waddr_width = max(1, math.ceil(math.log2(self.waddr_depth)))
        raddr_width = max(1, math.ceil(math.log2(self.raddr_depth)))
        return {
            "FAMILY": self.family,
            "WADDR_DEPTH": str(self.waddr_depth),
            "WADDR_WIDTH": str(waddr_width),
            "WDATA_WIDTH": str(self.wdata_width),
            "RADDR_DEPTH": str(self.raddr_depth),
            "RADDR_WIDTH": str(raddr_width),
            "RDATA_WIDTH": str(self.rdata_width),
            "FIFO_CONTROLLER": self.fifo_controller,
            "FWFT": str(self.fwft),
            "FORCE_FAST_CONTROLLER": str(self.force_fast_controller),
            "IMPLEMENTATION": self.implementation,
            "REGMODE": self.regmode,
            "RESETMODE": self.resetmode,
            "ENABLE_ALMOST_FULL_FLAG": self.enable_almost_full_flag,
            "ALMOST_FULL_ASSERTION": self.almost_full_assertion,
            "ALMOST_FULL_ASSERT_LVL": str(self.almost_full_assert_lvl),
            "ALMOST_FULL_DEASSERT_LVL": str(self.almost_full_deassert_lvl),
            "ENABLE_ALMOST_EMPTY_FLAG": self.enable_almost_empty_flag,
            "ALMOST_EMPTY_ASSERTION": self.almost_empty_assertion,
            "ALMOST_EMPTY_ASSERT_LVL": str(self.almost_empty_assert_lvl),
            "ALMOST_EMPTY_DEASSERT_LVL": str(self.almost_empty_deassert_lvl),
            "ENABLE_DATA_COUNT_WR": self.enable_data_count_wr,
            "ENABLE_DATA_COUNT_RD": self.enable_data_count_rd,
        }


FIFODC_TC_MAP = {
    "FIFODC-001": FifoDcTC("tc_fifodc_001_default_config_baseline", test_type="Both"),
    "FIFODC-002": FifoDcTC("tc_fifodc_002_minimum_write_address_depth", waddr_depth=2, wdata_width=1, raddr_depth=2, rdata_width=1, almost_full_assert_lvl=1, almost_full_deassert_lvl=1, almost_empty_assert_lvl=1, almost_empty_deassert_lvl=1, test_type="Both"),
    "FIFODC-003": FifoDcTC("tc_fifodc_003_maximum_write_address_depth", waddr_depth=65536, wdata_width=1, raddr_depth=65536, rdata_width=1, almost_full_assert_lvl=65535, almost_full_deassert_lvl=65534, test_type="Both"),
    "FIFODC-004": FifoDcTC("tc_fifodc_004_minimum_write_data_width", waddr_depth=512, wdata_width=1, raddr_depth=512, rdata_width=1, test_type="Both"),
    "FIFODC-005": FifoDcTC("tc_fifodc_005_maximum_write_data_width", waddr_depth=4096, wdata_width=256, raddr_depth=4096, rdata_width=256, almost_full_assert_lvl=4095, almost_full_deassert_lvl=4094, test_type="Both"),
    "FIFODC-006": FifoDcTC("tc_fifodc_006_minimum_read_address_depth", waddr_depth=64, wdata_width=1, raddr_depth=2, rdata_width=32, almost_full_assert_lvl=63, almost_full_deassert_lvl=62, almost_empty_assert_lvl=1, almost_empty_deassert_lvl=1, test_type="Both"),
    "FIFODC-007": FifoDcTC("tc_fifodc_007_maximum_read_address_depth", waddr_depth=2048, wdata_width=32, raddr_depth=65536, rdata_width=1, almost_full_assert_lvl=2047, almost_full_deassert_lvl=2046, test_type="Both"),
    "FIFODC-008": FifoDcTC("tc_fifodc_008_minimum_read_data_width", waddr_depth=32, wdata_width=32, raddr_depth=1024, rdata_width=1, almost_full_assert_lvl=31, almost_full_deassert_lvl=30, test_type="Both"),
    "FIFODC-009": FifoDcTC("tc_fifodc_009_maximum_read_data_width", waddr_depth=16384, wdata_width=8, raddr_depth=512, rdata_width=256, almost_full_assert_lvl=16383, almost_full_deassert_lvl=16382, test_type="Both"),
    "FIFODC-010": FifoDcTC("tc_fifodc_010_hardened_controller", fifo_controller="HARD_IP", almost_full_assertion="static-single", almost_empty_assertion="static-single", test_type="Both"),
    "FIFODC-011": FifoDcTC("tc_fifodc_011_hardened_controller_non_power_of_two", waddr_depth=1000, raddr_depth=1000, fifo_controller="HARD_IP", almost_full_assertion="static-single", almost_full_assert_lvl=999, almost_empty_assertion="static-single", test_type="Both"),
    "FIFODC-012": FifoDcTC("tc_fifodc_012_fwft_unregistered", fwft=1, regmode="noreg", test_type="Both"),
    "FIFODC-013": FifoDcTC("tc_fifodc_013_fwft_registered", fwft=1, regmode="reg", test_type="Both"),
    "FIFODC-014": FifoDcTC("tc_fifodc_014_high_speed_hardened_ceiling", waddr_depth=16383, raddr_depth=16383, fifo_controller="HARD_IP", force_fast_controller=1, almost_full_assertion="static-single", almost_full_assert_lvl=16382, almost_empty_assertion="static-single", test_type="Both"),
    "FIFODC-015": FifoDcTC("tc_fifodc_015_lut_based_storage", implementation="LUT", test_type="Both"),
    "FIFODC-016": FifoDcTC("tc_fifodc_016_output_register_disabled", regmode="noreg", test_type="Both"),
    "FIFODC-017": FifoDcTC("tc_fifodc_017_synchronous_reset_mode", resetmode="sync", test_type="Both"),
    "FIFODC-018": FifoDcTC("tc_fifodc_018_almost_full_flag_disabled", enable_almost_full_flag="FALSE", test_type="Both"),
    "FIFODC-019": FifoDcTC("tc_fifodc_019_almost_full_static_single", almost_full_assertion="static-single", almost_full_assert_lvl=400, test_type="Both"),
    "FIFODC-020": FifoDcTC("tc_fifodc_020_almost_full_dynamic_single", almost_full_assertion="dynamic-single", test_type="Both"),
    "FIFODC-021": FifoDcTC("tc_fifodc_021_almost_full_dynamic_dual", almost_full_assertion="dynamic-dual", test_type="Both"),
    "FIFODC-022": FifoDcTC("tc_fifodc_022_almost_full_assert_level_min", almost_full_assertion="static-single", almost_full_assert_lvl=1, test_type="Both"),
    "FIFODC-023": FifoDcTC("tc_fifodc_023_almost_full_assert_level_median", almost_full_assert_lvl=256, almost_full_deassert_lvl=255, test_type="Both"),
    "FIFODC-024": FifoDcTC("tc_fifodc_024_almost_full_deassert_level_min", almost_full_assert_lvl=511, almost_full_deassert_lvl=1, test_type="Both"),
    "FIFODC-025": FifoDcTC("tc_fifodc_025_almost_empty_flag_disabled", enable_almost_empty_flag="FALSE", test_type="Both"),
    "FIFODC-026": FifoDcTC("tc_fifodc_026_almost_empty_static_single", almost_empty_assertion="static-single", almost_empty_assert_lvl=100, test_type="Both"),
    "FIFODC-027": FifoDcTC("tc_fifodc_027_almost_empty_dynamic_single", almost_empty_assertion="dynamic-single", test_type="Both"),
    "FIFODC-028": FifoDcTC("tc_fifodc_028_almost_empty_dynamic_dual", almost_empty_assertion="dynamic-dual", test_type="Both"),
    "FIFODC-029": FifoDcTC("tc_fifodc_029_almost_empty_assert_level_median", almost_empty_assert_lvl=256, almost_empty_deassert_lvl=257, test_type="Both"),
    "FIFODC-030": FifoDcTC("tc_fifodc_030_almost_empty_assert_level_max", almost_empty_assertion="static-single", almost_empty_assert_lvl=511, test_type="Both"),
    "FIFODC-031": FifoDcTC("tc_fifodc_031_almost_empty_deassert_level_median", almost_empty_assert_lvl=100, almost_empty_deassert_lvl=256, test_type="Both"),
    "FIFODC-032": FifoDcTC("tc_fifodc_032_almost_empty_deassert_level_max", almost_empty_assert_lvl=1, almost_empty_deassert_lvl=511, test_type="Both"),
    "FIFODC-033": FifoDcTC("tc_fifodc_033_write_side_data_count_enabled", enable_data_count_wr="TRUE", test_type="Both"),
    "FIFODC-034": FifoDcTC("tc_fifodc_034_read_side_data_count_enabled", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-035": FifoDcTC("tc_fifodc_035_wide_wr_narrow_rd_dyn_dual", waddr_depth=512, wdata_width=32, raddr_depth=16384, rdata_width=1, resetmode="sync", almost_full_assertion="dynamic-dual", almost_empty_assertion="dynamic-dual", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-036": FifoDcTC("tc_fifodc_036_narrow_wr_wide_rd_fwft", waddr_depth=16384, wdata_width=1, raddr_depth=512, rdata_width=32, fwft=1, regmode="noreg", almost_full_assert_lvl=16383, almost_full_deassert_lvl=16382, enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-037": FifoDcTC("tc_fifodc_037_high_speed_hardened_fwft_sync", waddr_depth=8192, raddr_depth=8192, fifo_controller="HARD_IP", fwft=1, force_fast_controller=1, resetmode="sync", almost_full_assertion="static-single", almost_full_assert_lvl=8191, almost_empty_assertion="static-single", test_type="Both"),
    "FIFODC-038": FifoDcTC("tc_fifodc_038_lut_fwft_flags_disabled", waddr_depth=64, wdata_width=8, raddr_depth=64, rdata_width=8, fwft=1, implementation="LUT", regmode="noreg", enable_almost_full_flag="FALSE", enable_almost_empty_flag="FALSE", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-039": FifoDcTC("tc_fifodc_039_min_geometry_hard_ip", waddr_depth=2, wdata_width=1, raddr_depth=2, rdata_width=1, fifo_controller="HARD_IP", fwft=1, regmode="noreg", almost_full_assertion="static-single", almost_full_assert_lvl=1, almost_empty_assertion="static-single", test_type="Both"),
    "FIFODC-040": FifoDcTC("tc_fifodc_040_near_ceiling_memory_budget", waddr_depth=8192, wdata_width=180, raddr_depth=8192, rdata_width=180, almost_full_assertion="dynamic-dual", almost_empty_assertion="dynamic-dual", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-041": FifoDcTC("tc_fifodc_041_write_enable_ignored_while_full", test_type="Sim Only"),
    "FIFODC-042": FifoDcTC("tc_fifodc_042_read_enable_ignored_while_empty", test_type="Sim Only"),
    "FIFODC-043": FifoDcTC("tc_fifodc_043_async_reset_structure", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Radiant Compilation"),
    "FIFODC-044": FifoDcTC("tc_fifodc_044_main_reset_clear", resetmode="sync", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Both"),
    "FIFODC-045": FifoDcTC("tc_fifodc_045_rp_rst_leaves_write_intact", resetmode="sync", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Sim Only"),
    "FIFODC-046": FifoDcTC("tc_fifodc_046_almost_full_dynamic_assert_port", almost_full_assertion="dynamic-single", test_type="Sim Only"),
    "FIFODC-047": FifoDcTC("tc_fifodc_047_almost_full_dynamic_clear_port", almost_full_assertion="dynamic-dual", test_type="Sim Only"),
    "FIFODC-048": FifoDcTC("tc_fifodc_048_almost_empty_dynamic_assert_port", almost_empty_assertion="dynamic-single", test_type="Sim Only"),
    "FIFODC-049": FifoDcTC("tc_fifodc_049_almost_empty_dynamic_clear_port", almost_empty_assertion="dynamic-dual", test_type="Sim Only"),
    "FIFODC-050": FifoDcTC("tc_fifodc_050_full_empty_conservatism", test_type="Sim Only"),
    "FIFODC-051": FifoDcTC("tc_fifodc_051_data_count_conservatism", resetmode="sync", enable_data_count_wr="TRUE", enable_data_count_rd="TRUE", test_type="Sim Only"),
    "FIFODC-052": FifoDcTC("tc_fifodc_052_error_detect_outputs", test_type="Radiant Compilation"),
    "FIFODC-053": FifoDcTC("tc_fifodc_053_default_param_smoke_test", test_type="Radiant Compilation"),
}

FIFODC_TG_MAP = {
    "01": ["FIFODC-001"],
    "02": ["FIFODC-002", "FIFODC-003"],
    "03": ["FIFODC-004", "FIFODC-005"],
    "04": ["FIFODC-006", "FIFODC-007"],
    "05": ["FIFODC-008", "FIFODC-009"],
    "06": ["FIFODC-010", "FIFODC-011"],
    "07": ["FIFODC-012", "FIFODC-013"],
    "08": ["FIFODC-014"],
    "09": ["FIFODC-015"],
    "10": ["FIFODC-016"],
    "11": ["FIFODC-017"],
    "12": ["FIFODC-018"],
    "13": ["FIFODC-019", "FIFODC-020", "FIFODC-021"],
    "14": ["FIFODC-022", "FIFODC-023", "FIFODC-024"],
    "15": ["FIFODC-023", "FIFODC-024"],
    "16": ["FIFODC-025"],
    "17": ["FIFODC-026", "FIFODC-027", "FIFODC-028"],
    "18": ["FIFODC-029", "FIFODC-030"],
    "19": ["FIFODC-031", "FIFODC-032"],
    "20": ["FIFODC-033"],
    "21": ["FIFODC-034"],
    "22": ["FIFODC-035", "FIFODC-036", "FIFODC-037", "FIFODC-038", "FIFODC-039", "FIFODC-040"],
    "23": ["FIFODC-041", "FIFODC-042", "FIFODC-043", "FIFODC-044", "FIFODC-045", "FIFODC-046", "FIFODC-047", "FIFODC-048", "FIFODC-049", "FIFODC-050", "FIFODC-051"],
    "24": ["FIFODC-052", "FIFODC-053"],
}


# ══════════════════════════════════════════════════════════════════════════════
# 3. PLL IP Definition (81 test cases, G01..G29)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PllTC:
    testcase: str
    clki_freq: float          = 100.0
    clkop_freq_actual: float  = 100.0
    clkos_freq_actual: float  = 100.0
    clkos2_freq_actual: float = 100.0
    clkos3_freq_actual: float = 100.0
    clkos4_freq_actual: float = 100.0
    clkos5_freq_actual: float = 100.0
    clkos_en: int             = 0
    clkos2_en: int            = 0
    clkos3_en: int            = 0
    clkos4_en: int            = 0
    clkos5_en: int            = 0
    frac_n_en: int            = 0
    ss_en: int                = 0
    dyn_ports_en: int         = 0
    lock_en: int              = 1
    pll_lock_sticky: int      = 0
    lmmi_en: int              = 0
    apb_en: int               = 0
    apb_soft_reg_en: int      = 0
    powerdown_en: int         = 0
    en_refclk_mon: int        = 0
    family: str               = "LIFCL"
    test_type: str            = "Both"
    note: str                 = ""

    def get_sim_args(self) -> Dict[str, str]:
        return {
            "CLKI_FREQ": str(self.clki_freq),
            "CLKOP_FREQ_ACTUAL": str(self.clkop_freq_actual),
            "CLKOS_FREQ_ACTUAL": str(self.clkos_freq_actual),
            "CLKOS2_FREQ_ACTUAL": str(self.clkos2_freq_actual),
            "CLKOS3_FREQ_ACTUAL": str(self.clkos3_freq_actual),
            "CLKOS4_FREQ_ACTUAL": str(self.clkos4_freq_actual),
            "CLKOS5_FREQ_ACTUAL": str(self.clkos5_freq_actual),
            "CLKOS_EN": str(self.clkos_en),
            "CLKOS2_EN": str(self.clkos2_en),
            "CLKOS3_EN": str(self.clkos3_en),
            "CLKOS4_EN": str(self.clkos4_en),
            "CLKOS5_EN": str(self.clkos5_en),
            "FRAC_N_EN": str(self.frac_n_en),
            "SS_EN": str(self.ss_en),
            "DYN_PORTS_EN": str(self.dyn_ports_en),
            "LOCK_EN": str(self.lock_en),
            "PLL_LOCK_STICKY": str(self.pll_lock_sticky),
            "LMMI_EN": str(self.lmmi_en),
            "APB_EN": str(self.apb_en),
            "APB_SOFT_REG_EN": str(self.apb_soft_reg_en),
            "POWERDOWN_EN": str(self.powerdown_en),
            "EN_REFCLK_MON": str(self.en_refclk_mon),
        }


PLL_TC_MAP = {
    "PLL-001": PllTC("tc_pll_001_default_config_lock", test_type="Both"),
    "PLL-002": PllTC("tc_pll_002_frequency_mode_achievable", test_type="Both"),
    "PLL-003": PllTC("tc_pll_003_divider_mode", test_type="Both"),
    "PLL-004": PllTC("tc_pll_004_fractional_n_frequency_mode", frac_n_en=1, test_type="Both"),
    "PLL-005": PllTC("tc_pll_005_fractional_n_divider_mode", frac_n_en=1, clki_freq=18.0, test_type="Radiant Compilation"),
    "PLL-006": PllTC("tc_pll_006_down_spread_profile", ss_en=1, test_type="Radiant Compilation"),
    "PLL-007": PllTC("tc_pll_007_centre_spread_profile", ss_en=1, test_type="Radiant Compilation"),
    "PLL-008": PllTC("tc_pll_008_min_modulation_freq", ss_en=1, test_type="Radiant Compilation"),
    "PLL-009": PllTC("tc_pll_009_median_modulation_freq", ss_en=1, test_type="Both"),
    "PLL-010": PllTC("tc_pll_010_max_modulation_freq", ss_en=1, clki_freq=18.0, test_type="Radiant Compilation"),
    "PLL-011": PllTC("tc_pll_011_external_feedback_clock", test_type="Both"),
    "PLL-012": PllTC("tc_pll_012_internal_feedback_delay", test_type="Radiant Compilation"),
    "PLL-013": PllTC("tc_pll_013_min_reference_frequency", clki_freq=18.0, test_type="Both"),
    "PLL-014": PllTC("tc_pll_014_median_reference_frequency", clki_freq=400.0, test_type="Radiant Compilation"),
    "PLL-015": PllTC("tc_pll_015_max_reference_frequency", clki_freq=800.0, test_type="Radiant Compilation"),
    "PLL-016": PllTC("tc_pll_016_ref_divider_min", test_type="Radiant Compilation"),
    "PLL-017": PllTC("tc_pll_017_ref_divider_median", clki_freq=440.0, test_type="Radiant Compilation"),
    "PLL-018": PllTC("tc_pll_018_ref_divider_max", clki_freq=800.0, test_type="Radiant Compilation"),
    "PLL-019": PllTC("tc_pll_019_refclk_mon_3p2", en_refclk_mon=1, test_type="Both"),
    "PLL-020": PllTC("tc_pll_020_refclk_mon_1p0", clki_freq=200.0, en_refclk_mon=1, test_type="Radiant Compilation"),
    "PLL-021": PllTC("tc_pll_021_fbk_clkop", test_type="Both"),
    "PLL-022": PllTC("tc_pll_022_fbk_clkos_clkos2", test_type="Radiant Compilation"),
    "PLL-023": PllTC("tc_pll_023_fbk_clkos3_4_5", test_type="Radiant Compilation"),
    "PLL-024": PllTC("tc_pll_024_n_divider_min", test_type="Radiant Compilation"),
    "PLL-025": PllTC("tc_pll_025_n_divider_median", test_type="Radiant Compilation"),
    "PLL-026": PllTC("tc_pll_026_n_divider_max", clki_freq=800.0, test_type="Both"),
    "PLL-027": PllTC("tc_pll_027_frac_n_divider_floor", frac_n_en=1, test_type="Radiant Compilation"),
    "PLL-028": PllTC("tc_pll_028_frac_word_min", frac_n_en=1, clki_freq=18.0, test_type="Radiant Compilation"),
    "PLL-029": PllTC("tc_pll_029_frac_word_median", frac_n_en=1, clki_freq=18.0, test_type="Both"),
    "PLL-030": PllTC("tc_pll_030_frac_word_max", frac_n_en=1, clki_freq=18.0, test_type="Radiant Compilation"),
    "PLL-031": PllTC("tc_pll_031_all_secondary_outputs_enabled", clkos_en=1, clkos2_en=1, clkos3_en=1, clkos4_en=1, clkos5_en=1, test_type="Both"),
    "PLL-032": PllTC("tc_pll_032_selective_enable_clkos3_5", clkos3_en=1, clkos5_en=1, test_type="Radiant Compilation"),
    "PLL-033": PllTC("tc_pll_033_primary_output_bypassed", test_type="Both"),
    "PLL-034": PllTC("tc_pll_034_all_secondary_bypassed", test_type="Radiant Compilation"),
    "PLL-035": PllTC("tc_pll_035_mixed_bypass", clkos2_en=1, clkos3_en=1, clkos4_en=1, clkos5_en=1, test_type="Both"),
    "PLL-036": PllTC("tc_pll_036_max_primary_min_secondary", test_type="Radiant Compilation"),
    "PLL-037": PllTC("tc_pll_037_min_primary_max_secondary", test_type="Radiant Compilation"),
    "PLL-038": PllTC("tc_pll_038_median_output_frequency", test_type="Both"),
    "PLL-039": PllTC("tc_pll_039_max_output_frequency", test_type="Radiant Compilation"),
    "PLL-040": PllTC("tc_pll_040_primary_div1_secondary_div128", test_type="Radiant Compilation"),
    "PLL-041": PllTC("tc_pll_041_primary_div128_secondary_div1", test_type="Radiant Compilation"),
    "PLL-042": PllTC("tc_pll_042_all_dividers_at_64", test_type="Both"),
    "PLL-043": PllTC("tc_pll_043_tolerance_sweep_tight", test_type="Radiant Compilation"),
    "PLL-044": PllTC("tc_pll_044_tolerance_sweep_loose", test_type="Radiant Compilation"),
    "PLL-045": PllTC("tc_pll_045_static_phase_90_270", test_type="Both"),
    "PLL-046": PllTC("tc_pll_046_static_phase_0_45_135", test_type="Radiant Compilation"),
    "PLL-047": PllTC("tc_pll_047_static_phase_180_225_315", test_type="Radiant Compilation"),
    "PLL-048": PllTC("tc_pll_048_rising_edge_duty_trim", test_type="Both"),
    "PLL-049": PllTC("tc_pll_049_falling_edge_duty_trim", test_type="Radiant Compilation"),
    "PLL-050": PllTC("tc_pll_050_refclk_pin_lvds", test_type="Both"),
    "PLL-051": PllTC("tc_pll_051_all_io_standards", test_type="Radiant Compilation"),
    "PLL-052": PllTC("tc_pll_052_dynamic_phase_ports_generated", test_type="Radiant Compilation"),
    "PLL-053": PllTC("tc_pll_053_dynamic_phase_stepping", dyn_ports_en=1, test_type="Both"),
    "PLL-054": PllTC("tc_pll_054_all_clock_enable_ports", test_type="Radiant Compilation"),
    "PLL-055": PllTC("tc_pll_055_clock_enable_clkos_only", test_type="Radiant Compilation"),
    "PLL-056": PllTC("tc_pll_056_pll_reset_not_requested", test_type="Radiant Compilation"),
    "PLL-057": PllTC("tc_pll_057_non_sticky_lock", pll_lock_sticky=0, test_type="Both"),
    "PLL-058": PllTC("tc_pll_058_sticky_lock", pll_lock_sticky=1, test_type="Both"),
    "PLL-059": PllTC("tc_pll_059_lock_output_not_requested", lock_en=0, test_type="Radiant Compilation"),
    "PLL-060": PllTC("tc_pll_060_lmmi_interface", lmmi_en=1, test_type="Both"),
    "PLL-061": PllTC("tc_pll_061_apb_without_soft_csr", apb_en=1, apb_soft_reg_en=0, test_type="Both"),
    "PLL-062": PllTC("tc_pll_062_apb_with_soft_csr_read", apb_en=1, apb_soft_reg_en=1, test_type="Both"),
    "PLL-063": PllTC("tc_pll_063_apb_soft_csr_dynamic_phase", apb_en=1, apb_soft_reg_en=1, test_type="Both"),
    "PLL-064": PllTC("tc_pll_064_legacy_mode_requested", test_type="Radiant Compilation"),
    "PLL-065": PllTC("tc_pll_065_powerdown_requested", test_type="Radiant Compilation"),
    "PLL-066": PllTC("tc_pll_066_frac_n_ceiling_monitor_apb", frac_n_en=1, clki_freq=18.0, en_refclk_mon=1, apb_en=1, apb_soft_reg_en=1, test_type="Radiant Compilation"),
    "PLL-067": PllTC("tc_pll_067_spread_spectrum_pin_six_freq", ss_en=1, pll_lock_sticky=1, test_type="Radiant Compilation"),
    "PLL-068": PllTC("tc_pll_068_external_feedback_all_enables", dyn_ports_en=1, test_type="Both"),
    "PLL-069": PllTC("tc_pll_069_mixed_bypass_duty_trim", test_type="Radiant Compilation"),
    "PLL-070": PllTC("tc_pll_070_max_ref_chain_lmmi", clki_freq=800.0, lmmi_en=1, test_type="Radiant Compilation"),
    "PLL-071": PllTC("tc_pll_071_min_ref_monitor_internal_path", clki_freq=18.0, en_refclk_mon=1, test_type="Radiant Compilation"),
    "PLL-072": PllTC("tc_pll_072_rstn_assertion_release", test_type="Both"),
    "PLL-073": PllTC("tc_pll_073_powerdown_assertion_release", test_type="Both"),
    "PLL-074": PllTC("tc_pll_074_legacy_asserted", test_type="Both"),
    "PLL-075": PllTC("tc_pll_075_clock_enables_deassert_reassert", test_type="Sim Only"),
    "PLL-076": PllTC("tc_pll_076_usr_fbclk_source", test_type="Sim Only"),
    "PLL-077": PllTC("tc_pll_077_refdetreset_refdetlos", test_type="Sim Only"),
    "PLL-078": PllTC("tc_pll_078_lmmi_transaction", lmmi_en=1, test_type="Sim Only"),
    "PLL-079": PllTC("tc_pll_079_apb_transaction", apb_en=1, apb_soft_reg_en=1, test_type="Sim Only"),
    "PLL-080": PllTC("tc_pll_080_all_six_clocks_observed", clkos_en=1, clkos2_en=1, clkos3_en=1, clkos4_en=1, clkos5_en=1, test_type="Both"),
    "PLL-081": PllTC("tc_pll_081_default_param_smoke_test", test_type="Radiant Compilation"),
}

PLL_TG_MAP = {
    "01": ["PLL-001"],
    "02": ["PLL-002", "PLL-003"],
    "03": ["PLL-004", "PLL-005"],
    "04": ["PLL-006", "PLL-007", "PLL-008", "PLL-009", "PLL-010"],
    "05": ["PLL-011"],
    "06": ["PLL-012"],
    "07": ["PLL-013", "PLL-014", "PLL-015"],
    "08": ["PLL-016", "PLL-017", "PLL-018"],
    "09": ["PLL-019", "PLL-020"],
    "10": ["PLL-021", "PLL-022", "PLL-023"],
    "11": ["PLL-024", "PLL-025", "PLL-026"],
    "12": ["PLL-027", "PLL-028", "PLL-029", "PLL-030"],
    "13": ["PLL-031", "PLL-032"],
    "14": ["PLL-033", "PLL-034", "PLL-035"],
    "15": ["PLL-036", "PLL-037", "PLL-038", "PLL-039"],
    "16": ["PLL-040", "PLL-041", "PLL-042"],
    "17": ["PLL-043", "PLL-044"],
    "18": ["PLL-045", "PLL-046", "PLL-047"],
    "19": ["PLL-048", "PLL-049"],
    "20": ["PLL-050", "PLL-051"],
    "21": ["PLL-052", "PLL-053"],
    "22": ["PLL-054", "PLL-055"],
    "23": ["PLL-056"],
    "24": ["PLL-057", "PLL-058", "PLL-059"],
    "25": ["PLL-060", "PLL-061", "PLL-062", "PLL-063"],
    "26": ["PLL-064", "PLL-065"],
    "27": ["PLL-066", "PLL-067", "PLL-068", "PLL-069", "PLL-070", "PLL-071"],
    "28": ["PLL-072", "PLL-073", "PLL-074", "PLL-075", "PLL-076", "PLL-077", "PLL-078", "PLL-079", "PLL-080"],
    "29": ["PLL-081"],
}


# ══════════════════════════════════════════════════════════════════════════════
# Active IP Core Dispatcher
# ══════════════════════════════════════════════════════════════════════════════

IP_TYPE = detect_ip_type()

if IP_TYPE == "fifo_dc":
    TC_MAP = FIFODC_TC_MAP
    TG_MAP = FIFODC_TG_MAP
    DEFAULT_PREFIX = "FIFODC"
    DRC_TG_KEY = "24"
elif IP_TYPE == "pll":
    TC_MAP = PLL_TC_MAP
    TG_MAP = PLL_TG_MAP
    DEFAULT_PREFIX = "PLL"
    DRC_TG_KEY = "29"
else:  # rom
    TC_MAP = ROM_TC_MAP
    TG_MAP = ROM_TG_MAP
    DEFAULT_PREFIX = "ROM"
    DRC_TG_KEY = "11"


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
        "TESTCASE="  + tc.testcase,
        "SIM_BUILD=" + sim_build,
        "WLF_FILE="  + os.path.join(REPO_ROOT, wlf_rel),
    ]

    # Append IP-specific parameters
    for k, v in tc.get_sim_args().items():
        cmd.append(f"{k}={v}")

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
    """Run DRC tests via pytest, capturing output to results/drc.log."""
    drc_group_name = f"G{DRC_TG_KEY}"
    print("\n" + "=" * 66)
    print(f"  {drc_group_name}: DRC & Parameter Validation (pytest)")
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
    raw_ip_name = IP_TYPE
    ip_display = IP_TYPE.upper()
    ip_version = "1.0.0"
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

    total_tcs = len(TC_MAP)
    both_cnt = sum(1 for tc in TC_MAP.values() if tc.test_type == "Both")
    sim_cnt  = sum(1 for tc in TC_MAP.values() if tc.test_type == "Sim Only")
    rad_cnt  = sum(1 for tc in TC_MAP.values() if tc.test_type == "Radiant Compilation")

    drc_path = os.path.join(REPO_ROOT, "src", "test_drc.py")
    drc_test_count = 0
    if os.path.isfile(drc_path):
        with open(drc_path, "r", errors="ignore") as f:
            drc_test_count = sum(1 for line in f if line.strip().startswith("def test_"))

    synth_dir = os.path.join(REPO_ROOT, "synth")
    synth_wrappers = []
    if os.path.isdir(synth_dir):
        synth_wrappers = [f for f in os.listdir(synth_dir) if f.endswith(".v") or f.endswith(".sv")]
    num_projects = len(synth_wrappers) if synth_wrappers else 1

    last_tg_num = int(list(TG_MAP.keys())[-1])
    print("=" * 66)
    print(f"  IP Test Overview: {ip_name} (LIFCL v{ip_version})")
    print("=" * 66)
    print(f"  IP name:                        {ip_name} ({ip_display})")
    print(f"  Testgroups:                     {len(TG_MAP)} (G01–G{last_tg_num-1:02d} Functional, G{last_tg_num:02d} DRC)")
    print(f"  Testcases:                      {total_tcs} total (per Test Plan)")
    print(f"    ├── Both (Sim & Radiant):     {both_cnt}")
    print(f"    ├── Sim Only:                 {sim_cnt}")
    print(f"    └── Radiant Compilation:      {rad_cnt}")
    if drc_test_count > 0:
        print(f"  DRC Parameter Unit Tests:       {drc_test_count} (in src/test_drc.py for G{last_tg_num:02d} & GUI rules)")
    print(f"  Synthesizable Radiant projects: {num_projects} ({ip_name}.rdf via `make prj_create`)")
    print("=" * 66)


def run_all_tests():
    """Run all simulation testgroups, DRC, and Radiant project compilation."""
    print("\n" + "=" * 66)
    print("  Running Full Test Suite (Simulation + DRC + Radiant Compilation)")
    print("=" * 66)
    failures = []

    # 1. Run all functional simulation testcases in TG_MAP (excluding final DRC group)
    drc_group_int = int(DRC_TG_KEY)
    for grp_num in range(1, drc_group_int):
        grp_key = f"{grp_num:02d}"
        if grp_key in TG_MAP:
            tc_ids = TG_MAP[grp_key]
            for tid in tc_ids:
                tc = TC_MAP[tid]
                rc = run_sim(tid, tc)
                if rc != 0:
                    failures.append(tid)

    # 2. Run DRC
    drc_rc = run_drc()
    if drc_rc != 0:
        failures.append(f"G{DRC_TG_KEY}-DRC")

    # 3. Run Radiant project creation and compilation
    print("\n" + "=" * 66)
    print("  Running Radiant Project Creation & Compilation")
    print("=" * 66)
    cmd_prj = ["make", "-C", REPO_ROOT, "prj_create", "prj_compile"]
    proc = subprocess.run(cmd_prj)
    if proc.returncode != 0:
        failures.append("Radiant-Compilation")

    total_functional = sum(len(TG_MAP[f"{g:02d}"]) for g in range(1, drc_group_int) if f"{g:02d}" in TG_MAP)
    total_stages = total_functional + 2  # DRC + Radiant Compilation
    passed_stages = total_stages - len(failures)

    # Generate summary report into results/summary.md and print table
    sum_script = os.path.join(REPO_ROOT, "..", "scripts", "summarize.py")
    sum_md = os.path.join(REPO_ROOT, "results", "summary.md")
    if os.path.exists(sum_script):
        sum_env = dict(os.environ, IP_ROOT=REPO_ROOT)
        subprocess.run(["python3", sum_script, sum_md], env=sum_env)
        print("\n" + "=" * 66)
        print("  Summary Matrix:")
        print("=" * 66)
        subprocess.run(["python3", sum_script], env=sum_env)
        print(f"\nDetailed summary table written to results/summary.md")

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

    if u in ("DRC", f"TG-{DRC_TG_KEY}", f"G{DRC_TG_KEY}"):
        return f"G{DRC_TG_KEY}", "group"

    # TC pattern: e.g. TC-ROM-001, ROM-001, TC-FIFODC-001, FIFODC-001, TC-PLL-001, PLL-001, TC-001, 001, 1
    m_full = re.match(r'^(?:TC-)?(ROM|FIFODC|FIFO|PLL)-?(\d+)$', u)
    if m_full:
        prefix = m_full.group(1)
        if prefix == "FIFO":
            prefix = "FIFODC"
        num = int(m_full.group(2))
        return f"{prefix}-{num:03d}", "tc"

    # Just a number e.g. 1, 01, 001, TC-1, TC-001
    m_num = re.match(r'^(?:TC-)?(\d+)$', u)
    if m_num:
        num = int(m_num.group(1))
        return f"{DEFAULT_PREFIX}-{num:03d}", "tc"

    return u, "unknown"


def _print_group_summary(ident, tc_ids, failure_set):
    """Print standard summary table for a group of TCs."""
    print("")
    print("=" * 66)
    print(f"  Test Group Summary: {ident}")
    print("=" * 66)
    passed = 0
    failed = 0
    for tid in tc_ids:
        tc = TC_MAP.get(tid)
        log_rel, _, _ = _artifact_paths(tid)
        log_path = os.path.join(REPO_ROOT, log_rel)
        parsed = _parse_log(log_path)
        status = "FAIL" if tid in failure_set else ("PASS" if parsed and parsed[0] == "PASS" else "FAIL")
        if status == "PASS":
            passed += 1
            mark = "PASS"
        else:
            failed += 1
            mark = "FAIL"
        tc_name = tc.testcase if tc else tid
        print(f"  [{mark}]  {tid:<12} {tc_name:<40}")
    print("-" * 66)
    print(f"  Total: {len(tc_ids)}  Passed: {passed}  Failed: {failed}")
    print("=" * 66 + "\n")


def main():
    if len(sys.argv) < 2:
        print_outline()
        return

    arg = sys.argv[1]
    ident, kind = _normalize_tc_arg(arg)

    if kind == "cmd":
        if ident == "INFO":
            print_outline()
            return
        elif ident == "TEST":
            sys.exit(run_all_tests())

    if kind == "group":
        grp_key = ident[1:]  # strip 'G' -> '01', '02', etc.
        if grp_key == DRC_TG_KEY or ident.upper() == "DRC":
            rc = run_drc()
            sys.exit(rc)

        if grp_key not in TG_MAP:
            print(f"Error: Unknown testgroup {ident}. Valid groups: {sorted(list(TG_MAP.keys()))}")
            sys.exit(1)

        tc_ids = TG_MAP[grp_key]
        failures = []
        for tid in tc_ids:
            tc = TC_MAP[tid]
            rc = run_sim(tid, tc)
            if rc != 0:
                failures.append(tid)

        _print_group_summary(ident, tc_ids, set(failures))
        sys.exit(1 if failures else 0)

    if kind == "tc":
        if ident not in TC_MAP:
            print(f"Error: Unknown testcase {ident}. Valid TCs for {IP_TYPE}: {sorted(list(TC_MAP.keys()))}")
            sys.exit(1)

        tc = TC_MAP[ident]
        rc = run_sim(ident, tc)
        sys.exit(rc)

    print(f"Error: Unrecognised argument '{arg}'. Use 'info', 'test', 'drc', a group (e.g. 'G01'), or a TC (e.g. 'TC-{DEFAULT_PREFIX}-001').")
    sys.exit(1)


if __name__ == "__main__":
    main()
