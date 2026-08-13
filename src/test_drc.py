"""
TG-10 — DRC and Parameter Validation  (TC-10-01 … TC-10-09)

Verify that the lscc_rom IP plugin enforces all dependency rules at
configuration time.

The Radiant IP generator runs DRC checks outside the RTL simulator, so
these tests exercise a Python model of the same constraints.  The model
is derived from the LIFCL EBR tile specification and must stay in sync
with the plugin source whenever the plugin rules change.

Run without a simulator:

    pytest src/test_drc.py -v

Pass/fail criteria (per Section 8.2 of the testplan):
    PASS — the plugin correctly rejects the invalid configuration and the
           expected error string appears in the diagnostic message.
    FAIL — the invalid configuration is accepted, or a different error
           message is emitted.
"""

import re
import pytest


# ─── LIFCL EBR tile constraints ──────────────────────────────────────────────

_RADDR_DEPTH_MIN  = 2
_RADDR_DEPTH_MAX  = 65_536
_RDATA_WIDTH_MIN  = 1
_RDATA_WIDTH_MAX  = 512
_MAX_TOTAL_BITS   = 1_548_288          # 43 LIFCL EBR tiles × 36 Kbits each
_ECC_VALID_WIDTHS = frozenset({32, 64})


def check_lscc_rom_params(
    rdata_width   = 36,
    raddr_depth   = 512,
    regmode       = "noreg",
    resetmode     = "sync",
    output_clk_en = 0,
    ecc_enable    = 0,
    init_mode     = "all_one",
    init_file     = "-",
):
    """
    Validate lscc_rom configuration parameters against LIFCL EBR DRC rules.

    Raises ValueError with the plugin error message when any rule is violated.
    Returns None when all parameters are valid.
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


# ─── TC-10-01 ────────────────────────────────────────────────────────────────

def test_tc_10_01_depth_below_minimum():
    """TC-10-01: RADDR_DEPTH=1 is below the minimum of 2."""
    with pytest.raises(ValueError, match=re.escape("Address depth is out of range!")):
        check_lscc_rom_params(raddr_depth=1)


# ─── TC-10-02 ────────────────────────────────────────────────────────────────

def test_tc_10_02_depth_above_maximum():
    """TC-10-02: RADDR_DEPTH=65537 exceeds the maximum of 65536."""
    with pytest.raises(ValueError, match=re.escape("Address depth is out of range!")):
        check_lscc_rom_params(raddr_depth=65_537)


# ─── TC-10-03 ────────────────────────────────────────────────────────────────

def test_tc_10_03_width_below_minimum():
    """TC-10-03: RDATA_WIDTH=0 is below the minimum of 1."""
    with pytest.raises(ValueError, match=re.escape("Data width is out of range!")):
        check_lscc_rom_params(rdata_width=0)


# ─── TC-10-04 ────────────────────────────────────────────────────────────────

def test_tc_10_04_width_above_maximum():
    """TC-10-04: RDATA_WIDTH=513 exceeds the maximum of 512."""
    with pytest.raises(ValueError, match=re.escape("Data width is out of range!")):
        check_lscc_rom_params(rdata_width=513)


# ─── TC-10-05 ────────────────────────────────────────────────────────────────

def test_tc_10_05_total_bits_exceed_limit():
    """TC-10-05: RDATA_WIDTH=512, RADDR_DEPTH=4096 → 2,097,152 bits > 1,548,288."""
    with pytest.raises(ValueError, match="Total memory size exceeds the resource limitation"):
        check_lscc_rom_params(rdata_width=512, raddr_depth=4_096)


# ─── TC-10-06 ────────────────────────────────────────────────────────────────

def test_tc_10_06_output_clk_en_without_reg():
    """TC-10-06: OUTPUT_CLK_EN=1 requires REGMODE=reg; rejected when REGMODE=noreg."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Enable Output ClockEn is turned on, while Enable Output Register is turned off"
        ),
    ):
        check_lscc_rom_params(output_clk_en=1, regmode="noreg")


# ─── TC-10-07 ────────────────────────────────────────────────────────────────

def test_tc_10_07_async_reset_without_reg():
    """TC-10-07: RESETMODE=async requires REGMODE=reg; rejected when REGMODE=noreg."""
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Reset assertion is set to async, while Enable Output Register is turned off"
        ),
    ):
        check_lscc_rom_params(resetmode="async", regmode="noreg")


# ─── TC-10-08 ────────────────────────────────────────────────────────────────

def test_tc_10_08_ecc_unsupported_width():
    """TC-10-08: ECC_ENABLE=1 with RDATA_WIDTH=65 is rejected (only 32 and 64 are valid)."""
    with pytest.raises(ValueError, match="ECC is not supported for RDATA_WIDTH=65"):
        check_lscc_rom_params(ecc_enable=1, rdata_width=65)


# ─── TC-10-09 ────────────────────────────────────────────────────────────────

def test_tc_10_09_mem_file_without_path():
    """TC-10-09: INIT_MODE=mem_file with no init file path ("-") is rejected."""
    with pytest.raises(ValueError, match="Initialization file is mandatory"):
        check_lscc_rom_params(init_mode="mem_file", init_file="-")


# ─── boundary / sanity checks (not in test plan, confirm model correctness) ──

class TestBoundaryValid:
    """Verify that valid edge-case configurations are accepted without error."""

    def test_depth_minimum_boundary(self):
        check_lscc_rom_params(raddr_depth=2, rdata_width=1)

    def test_depth_maximum_boundary(self):
        # 1 bit × 65536 = 65536 bits ≪ limit
        check_lscc_rom_params(raddr_depth=65_536, rdata_width=1)

    def test_width_minimum_boundary(self):
        check_lscc_rom_params(rdata_width=1, raddr_depth=2)

    def test_width_maximum_within_bit_limit(self):
        # 512 bits × 2 = 1024 bits ≪ limit
        check_lscc_rom_params(rdata_width=512, raddr_depth=2)

    def test_total_bits_at_limit(self):
        # 36 × 43008 = 1,548,288 exactly — should be accepted
        check_lscc_rom_params(rdata_width=36, raddr_depth=43_008)

    def test_output_clk_en_with_reg(self):
        check_lscc_rom_params(output_clk_en=1, regmode="reg")

    def test_async_reset_with_reg(self):
        check_lscc_rom_params(resetmode="async", regmode="reg")

    def test_ecc_width_32(self):
        check_lscc_rom_params(ecc_enable=1, rdata_width=32)

    def test_ecc_width_64(self):
        check_lscc_rom_params(ecc_enable=1, rdata_width=64)

    def test_mem_file_with_valid_path(self):
        check_lscc_rom_params(init_mode="mem_file", init_file="testbench/rom_init.hex")
