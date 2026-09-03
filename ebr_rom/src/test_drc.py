"""
test_drc.py — G11 DRC & Parameter Validation Tests
Spec ref   : ROM_FunctionalSpec.md (v2.5.0, 2026-08-20)
Test plan  : ROM_TestPlan_LIFCL.md (2026-08-27)

Validates lscc_rom configuration parameters against LIFCL EBR DRC rules (DRC-1 through DRC-14).
Run with:
    pytest src/test_drc.py -v
"""

import math
import re
import pytest

# ─── LIFCL Constraints & Reference Limits ─────────────────────────────────────
_RADDR_DEPTH_MIN = 2
_RADDR_DEPTH_MAX = 65_536
_RDATA_WIDTH_MIN = 1
_RDATA_WIDTH_MAX = 512
_MAX_TOTAL_BITS  = 1_548_288  # 84 EBR blocks × 18,432 bits on LIFCL
_ECC_VALID_WIDTHS = frozenset({32, 64})


def clog2(n: int) -> int:
    """Calculates ceil(log2(n)) with lower bound check."""
    if n < 1:
        raise ValueError("Invalid input to clog2: value must be >= 1")
    if n == 1:
        return 1
    return (n - 1).bit_length()


def derive_total_memory_bits(depth: int, width: int) -> int:
    return depth * width


def derive_addr_width(depth: int) -> int:
    return clog2(depth)


def derive_mem_size(depth: int, width: int) -> str:
    return f"{width},{depth}"


def is_init_data_update_visible(family: str) -> bool:
    return family.upper() == "LAV-AT"


def check_lscc_rom_params(
    rdata_width: int = 18,
    raddr_depth: int = 1024,
    regmode: str = "reg",
    resetmode: str = "sync",
    output_clk_en: int = 0,
    ecc_enable: int = 0,
    init_mode: str = "mem_file",
    init_file: str = "rom_1024x18.bin",
    family: str = "LIFCL",
):
    """
    Validates lscc_rom configuration parameters against LIFCL EBR DRC rules.
    Raises ValueError with descriptive error message on violation.
    """
    if not (_RADDR_DEPTH_MIN <= raddr_depth <= _RADDR_DEPTH_MAX):
        raise ValueError("Address depth is out of range!")

    if not (_RDATA_WIDTH_MIN <= rdata_width <= _RDATA_WIDTH_MAX):
        raise ValueError("Data width is out of range!")

    total_bits = rdata_width * raddr_depth
    if total_bits > _MAX_TOTAL_BITS:
        raise ValueError(
            f"Total memory size exceeds the resource limitation! "
            f"({total_bits} bits requested, limit is {_MAX_TOTAL_BITS})"
        )

    if output_clk_en and regmode != "reg":
        raise ValueError(
            "Enable Output ClockEn is turned on, while Enable Output Register is turned off"
        )

    if resetmode == "async" and regmode != "reg":
        raise ValueError(
            "Reset assertion is set to async, while Enable Output Register is turned off"
        )

    if ecc_enable and rdata_width not in _ECC_VALID_WIDTHS:
        raise ValueError(
            f"ECC is not supported for RDATA_WIDTH={rdata_width}; "
            f"valid widths are {sorted(_ECC_VALID_WIDTHS)}"
        )

    if init_mode == "mem_file" and (not init_file or init_file.strip() in ("", "-")):
        raise ValueError("Initialization file is mandatory when INIT_MODE is mem_file")

    return True


# ─── DRC Rule Tests (DRC-1 through DRC-14) ────────────────────────────────────

def test_drc_01_total_memory_budget_limit():
    """DRC-1 / Rule 1: check_addr_depth_data_width bounds."""
    # Exact limit on LIFCL: 3024 * 512 = 1,548,288
    assert check_lscc_rom_params(raddr_depth=3024, rdata_width=512) is True
    # Over limit
    with pytest.raises(ValueError, match="Total memory size exceeds the resource limitation"):
        check_lscc_rom_params(raddr_depth=3025, rdata_width=512)


def test_drc_02_raddr_depth_range():
    """DRC-2 / Rule 2: RADDR_DEPTH must be in [2, 65536]."""
    assert check_lscc_rom_params(raddr_depth=2, rdata_width=1) is True
    assert check_lscc_rom_params(raddr_depth=65536, rdata_width=18) is True

    with pytest.raises(ValueError, match="Address depth is out of range!"):
        check_lscc_rom_params(raddr_depth=1)

    with pytest.raises(ValueError, match="Address depth is out of range!"):
        check_lscc_rom_params(raddr_depth=65537)


def test_drc_03_04_rdata_width_range():
    """DRC-3 / DRC-4 / Rules 3, 4: RDATA_WIDTH must be in [1, 512]."""
    assert check_lscc_rom_params(rdata_width=1, raddr_depth=1024) is True
    assert check_lscc_rom_params(rdata_width=512, raddr_depth=2048) is True

    with pytest.raises(ValueError, match="Data width is out of range!"):
        check_lscc_rom_params(rdata_width=0)

    with pytest.raises(ValueError, match="Data width is out of range!"):
        check_lscc_rom_params(rdata_width=513)


def test_drc_05_06_output_clk_en_dependency():
    """DRC-5 / DRC-6 / Rules 5, 6: OUTPUT_CLK_EN=True requires REGMODE=reg."""
    assert check_lscc_rom_params(output_clk_en=1, regmode="reg") is True
    with pytest.raises(ValueError, match="Enable Output ClockEn is turned on, while Enable Output Register is turned off"):
        check_lscc_rom_params(output_clk_en=1, regmode="noreg")


def test_drc_07_08_resetmode_dependency():
    """DRC-7 / DRC-8 / Rules 7, 8: RESETMODE=async requires REGMODE=reg."""
    assert check_lscc_rom_params(resetmode="async", regmode="reg") is True
    with pytest.raises(ValueError, match="Reset assertion is set to async, while Enable Output Register is turned off"):
        check_lscc_rom_params(resetmode="async", regmode="noreg")


def test_drc_09_chk_file_mandatory():
    """DRC-9 / Rule 9: chk_file requires a named file when init_mode=mem_file."""
    assert check_lscc_rom_params(init_mode="mem_file", init_file="rom_1024x18.bin") is True
    with pytest.raises(ValueError, match="Initialization file is mandatory"):
        check_lscc_rom_params(init_mode="mem_file", init_file="-")
    with pytest.raises(ValueError, match="Initialization file is mandatory"):
        check_lscc_rom_params(init_mode="mem_file", init_file="")


def test_drc_10_addr_width_derivation():
    """DRC-10 / Rule 10: Derived address width by clog2."""
    assert derive_addr_width(2) == 1
    assert derive_addr_width(1000) == 10
    assert derive_addr_width(1024) == 10
    assert derive_addr_width(2048) == 11
    assert derive_addr_width(3024) == 12
    assert derive_addr_width(65536) == 16


def test_drc_12_total_memory_bits_derivation():
    """DRC-12 / Rule 15: Total Memory bits derivation."""
    assert derive_total_memory_bits(1024, 18) == 18432
    assert derive_total_memory_bits(3024, 512) == 1548288
    assert derive_total_memory_bits(1000, 8) == 8000
    assert derive_total_memory_bits(2, 1) == 2


def test_drc_13_init_data_update_visibility():
    """DRC-13 / Rules 17, 18: Initialization data update visibility."""
    assert is_init_data_update_visible("LIFCL") is False
    assert is_init_data_update_visible("LFCPNX") is False
    assert is_init_data_update_visible("LAV-AT") is True


def test_drc_14_derived_readonly_settings():
    """DRC-14 / Rules 13, 14, 16, 19: Derived read-only settings."""
    assert derive_mem_size(1000, 8) == "8,1000"
    assert derive_mem_size(1024, 18) == "18,1024"
    assert derive_mem_size(512, 36) == "36,512"


# ─── Boundary Validation Class ────────────────────────────────────────────────

class TestBoundaryValid:
    """Verify that all legal configurations in the testplan pass DRC."""

    def test_tc_rom_001_params(self):
        check_lscc_rom_params(raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_002_params(self):
        check_lscc_rom_params(raddr_depth=2, rdata_width=1, regmode="reg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_005_params(self):
        check_lscc_rom_params(raddr_depth=3024, rdata_width=512, regmode="reg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_007_params(self):
        check_lscc_rom_params(raddr_depth=1024, rdata_width=1, regmode="reg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_009_params(self):
        check_lscc_rom_params(raddr_depth=2048, rdata_width=512, regmode="reg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_012_params(self):
        check_lscc_rom_params(raddr_depth=1024, rdata_width=18, regmode="noreg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_013_params(self):
        check_lscc_rom_params(raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="sync", output_clk_en=1)

    def test_tc_rom_014_params(self):
        check_lscc_rom_params(raddr_depth=1024, rdata_width=18, regmode="reg", resetmode="async", output_clk_en=0)

    def test_tc_rom_021_params(self):
        check_lscc_rom_params(raddr_depth=2048, rdata_width=512, regmode="noreg", resetmode="sync", output_clk_en=0)

    def test_tc_rom_023_params(self):
        check_lscc_rom_params(raddr_depth=2, rdata_width=1, regmode="noreg", resetmode="sync", output_clk_en=0)
