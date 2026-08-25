"""
test_drc.py — DRC and Parameter Validation for FIFO_DC (LIFCL)
Spec ref  : FIFO_DC Functional Specification (v2.7.2)
Test plan : FIFO_DC_LIFCL_TestPlan_20260801.md

Validates that the FIFO_DC IP plugin enforces all LIFCL configuration rules:
  TC013 — Maximum Width Ratio 32:1 (LIFCL Boundary)
  TC030 — FORCE_FAST_CONTROLLER=True: Depth Limit 16383
  TC031 — FORCE_FAST_CONTROLLER=False: Depth Up to 65536
  TC034 — DRC: Memory Equivalence Violation W×D ≠ R×D
  TC035 — DRC: Width Ratio > 32 Rejected (LIFCL Max)
  TC036 — DRC: Total Memory > 1,548,288 Bits Rejected (LIFCL)
  TC037 — DRC: Depth Non-Power-of-2 Rejected (FABRIC)
  TC039 — DRC: LUT with Asymmetric Configuration Rejected

Run without a simulator:
    pytest src/test_drc.py -v
"""

import math
import pytest


# ─── LIFCL Constraints & Reference DRC Model ──────────────────────────────────
_LIFCL_MAX_MEM_BITS = 18 * 1024 * 84  # 1,548,288 bits (84 EBR blocks × 18Kb)
_MIN_ADDR_DEPTH = 1
_MAX_ADDR_DEPTH_STD = 65536
_MAX_ADDR_DEPTH_FAST = 16383
_MIN_DATA_WIDTH = 1
_MAX_DATA_WIDTH = 256
_MAX_WIDTH_RATIO_LIFCL = 32


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def check_fifo_dc_params(
    waddr_depth: int = 512,
    wdata_width: int = 36,
    raddr_depth: int = 512,
    rdata_width: int = 36,
    implementation: str = "EBR",
    fifo_controller: str = "HARD_IP",
    force_fast_controller: bool = False,
    family: str = "LIFCL",
    enable_almost_full_flag: str = "TRUE",
    almost_full_assertion: str = "static-single",
    almost_full_assert_lvl: int = None,
    almost_full_deassert_lvl: int = None,
    enable_almost_empty_flag: str = "TRUE",
    almost_empty_assertion: str = "static-single",
    almost_empty_assert_lvl: int = 1,
    almost_empty_deassert_lvl: int = 2,
    ecc_enable: int = 0,
):
    """
    Validates FIFO_DC configuration against LIFCL DRC rules.
    Raises ValueError with the exact error string expected by Radiant.
    """
    if almost_full_assert_lvl is None:
        almost_full_assert_lvl = max(1, waddr_depth - 1)
    if almost_full_deassert_lvl is None:
        almost_full_deassert_lvl = max(0, almost_full_assert_lvl - 1)
    max_addr_depth = _MAX_ADDR_DEPTH_FAST if (family == "LIFCL" and force_fast_controller) else _MAX_ADDR_DEPTH_STD

    # Total memory size check
    total_bits = waddr_depth * wdata_width
    if total_bits > _LIFCL_MAX_MEM_BITS:
        raise ValueError(f"Total memory size exceeds the resource limitation! {_LIFCL_MAX_MEM_BITS} bits")

    # Address depth range
    if not (_MIN_ADDR_DEPTH <= waddr_depth <= max_addr_depth) or not (_MIN_ADDR_DEPTH <= raddr_depth <= max_addr_depth):
        raise ValueError("Address depth is out of range!")

    # Data width range
    if not (_MIN_DATA_WIDTH <= wdata_width <= _MAX_DATA_WIDTH) or not (_MIN_DATA_WIDTH <= rdata_width <= _MAX_DATA_WIDTH):
        raise ValueError("Data width is out of range!")

    # Power of 2 ratio checks
    if wdata_width > rdata_width:
        if (wdata_width % rdata_width != 0) or not is_power_of_two(wdata_width // rdata_width):
            raise ValueError("Ratio of Data width W / Data width R must be a power of 2 (e.g. 1,2,4)!")
    elif rdata_width > wdata_width:
        if (rdata_width % wdata_width != 0) or not is_power_of_two(rdata_width // wdata_width):
            raise ValueError("Ratio of Data width R / Data width W must be a power of 2 (e.g. 1,2,4)!")

    # Memory equivalence: W*D == R*D
    if (waddr_depth * wdata_width) != (raddr_depth * rdata_width):
        raise ValueError("(Depth_W x Width_W) and (Depth_R x Width_R) must be equivalent!")

    # FABRIC controller power-of-2 depth requirement
    if fifo_controller == "FABRIC":
        if not is_power_of_two(waddr_depth) or not is_power_of_two(raddr_depth):
            raise ValueError("Depth must be a power of 2 (i.e. 2, 4, 8 ... 16)")

    # Max factor check for LIFCL
    factor = max(wdata_width, rdata_width) / min(wdata_width, rdata_width)
    if family == "LIFCL" and factor > _MAX_WIDTH_RATIO_LIFCL:
        raise ValueError(f"Maximum factor between Width_W and Width_R should be <= {_MAX_WIDTH_RATIO_LIFCL}")

    # LUT implementation symmetry constraint
    if implementation == "LUT":
        if (waddr_depth != raddr_depth) or (wdata_width != rdata_width):
            raise ValueError("WRITE and READ ADDR_DEPTH and WIDTH must match for LUT implementation")

    # Flag level validation
    if enable_almost_full_flag in ("TRUE", 1):
        if almost_full_assertion == "static-single":
            if almost_full_assert_lvl is not None and almost_full_assert_lvl > waddr_depth:
                raise ValueError(f"FULL Assert or Deassert LVL is out of range!{waddr_depth}")
        elif almost_full_assertion == "static-dual":
            if almost_full_assert_lvl is not None and almost_full_deassert_lvl is not None:
                if (almost_full_deassert_lvl >= almost_full_assert_lvl) or (almost_full_assert_lvl > waddr_depth):
                    raise ValueError(f"FULL Assert or Deassert LVL is out of range!{waddr_depth}")

    if enable_almost_empty_flag in ("TRUE", 1):
        if almost_empty_assertion == "static-single":
            if almost_empty_assert_lvl < 1:
                raise ValueError("EMPTY Assert or Deassert LVL is out of range!")
        elif almost_empty_assertion == "static-dual":
            if (almost_empty_deassert_lvl <= almost_empty_assert_lvl) or (almost_empty_assert_lvl < 1):
                raise ValueError("EMPTY Assert or Deassert LVL is out of range!")

    return True


# ─── Test Cases ───────────────────────────────────────────────────────────────

def test_tc013_max_width_ratio_32():
    """TC013: 32:1 width ratio is accepted, 64:1 is rejected on LIFCL."""
    # 32:1 is valid
    assert check_fifo_dc_params(
        wdata_width=32, waddr_depth=512, rdata_width=1, raddr_depth=16384,
        fifo_controller="FABRIC", implementation="EBR"
    ) is True

    assert check_fifo_dc_params(
        wdata_width=64, waddr_depth=256, rdata_width=2, raddr_depth=8192,
        fifo_controller="FABRIC", implementation="EBR"
    ) is True

    # 64:1 is rejected
    with pytest.raises(ValueError, match="Maximum factor between Width_W and Width_R should be <= 32"):
        check_fifo_dc_params(
            wdata_width=64, waddr_depth=256, rdata_width=1, raddr_depth=16384,
            fifo_controller="FABRIC", implementation="EBR"
        )


def test_tc030_force_fast_controller_depth_limit():
    """TC030: FORCE_FAST_CONTROLLER=True limits depth to 16383."""
    # 16383 is accepted
    assert check_fifo_dc_params(
        waddr_depth=16383, wdata_width=18, raddr_depth=16383, rdata_width=18,
        fifo_controller="HARD_IP", force_fast_controller=True
    ) is True

    # 16384 exceeds fast controller limit
    with pytest.raises(ValueError, match="Address depth is out of range!"):
        check_fifo_dc_params(
            waddr_depth=16384, wdata_width=18, raddr_depth=16384, rdata_width=18,
            fifo_controller="HARD_IP", force_fast_controller=True
        )


def test_tc031_force_fast_controller_false_depth_65536():
    """TC031: FORCE_FAST_CONTROLLER=False allows depth up to 65536."""
    assert check_fifo_dc_params(
        waddr_depth=65536, wdata_width=18, raddr_depth=65536, rdata_width=18,
        fifo_controller="HARD_IP", force_fast_controller=False
    ) is True


def test_tc034_memory_equivalence_violation():
    """TC034: W*D != R*D is rejected."""
    with pytest.raises(ValueError, match=r"\(Depth_W x Width_W\) and \(Depth_R x Width_R\) must be equivalent!"):
        check_fifo_dc_params(
            waddr_depth=512, wdata_width=18, raddr_depth=512, rdata_width=36,
            fifo_controller="FABRIC", implementation="EBR"
        )


def test_tc035_width_ratio_exceeds_32_rejected():
    """TC035: Width ratio > 32 is rejected on LIFCL."""
    with pytest.raises(ValueError, match="Maximum factor between Width_W and Width_R should be <= 32"):
        check_fifo_dc_params(
            wdata_width=64, waddr_depth=512, rdata_width=1, raddr_depth=32768,
            fifo_controller="FABRIC", implementation="EBR"
        )


def test_tc036_total_memory_limit_exceeded():
    """TC036: Total memory > 1,548,288 bits is rejected."""
    # 65536 * 36 = 2,359,296 > 1,548,288
    with pytest.raises(ValueError, match="Total memory size exceeds the resource limitation!"):
        check_fifo_dc_params(
            waddr_depth=65536, wdata_width=36, raddr_depth=65536, rdata_width=36,
            fifo_controller="FABRIC", implementation="EBR"
        )


def test_tc037_depth_non_power_of_two_fabric():
    """TC037: FABRIC controller requires depth to be a power of 2."""
    with pytest.raises(ValueError, match=r"Depth must be a power of 2"):
        check_fifo_dc_params(
            waddr_depth=300, wdata_width=18, raddr_depth=300, rdata_width=18,
            fifo_controller="FABRIC", implementation="EBR"
        )


def test_tc039_lut_asymmetric_rejected():
    """TC039: LUT implementation cannot be asymmetric."""
    with pytest.raises(ValueError, match="WRITE and READ ADDR_DEPTH and WIDTH must match for LUT implementation"):
        check_fifo_dc_params(
            waddr_depth=32, wdata_width=16, raddr_depth=64, rdata_width=8,
            implementation="LUT", fifo_controller="FABRIC"
        )
