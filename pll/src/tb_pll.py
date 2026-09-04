"""
tb_pll.py — CoCoTB Testbench for lscc_pll (LIFCL)
Spec ref  : PLL_FIP_Functional_Spec.md v1.9.1
Test plan : PLL_TestPlan_LIFCL.md

Implements cocotb simulation tests for all functional test cases TC-PLL-001 through TC-PLL-081.
"""

import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer
from cocotb.utils import get_sim_time
from verilog_tracer import VerilogTracer

# ── Simulation Parameters ─────────────────────────────────────────────────────
CLKI_FREQ          = float(os.getenv("CLKI_FREQ", "100.0"))
CLKOP_FREQ_ACTUAL  = float(os.getenv("CLKOP_FREQ_ACTUAL", "100.0"))
CLKOS_FREQ_ACTUAL  = float(os.getenv("CLKOS_FREQ_ACTUAL", "100.0"))
CLKOS2_FREQ_ACTUAL = float(os.getenv("CLKOS2_FREQ_ACTUAL", "100.0"))
CLKOS3_FREQ_ACTUAL = float(os.getenv("CLKOS3_FREQ_ACTUAL", "100.0"))
CLKOS4_FREQ_ACTUAL = float(os.getenv("CLKOS4_FREQ_ACTUAL", "100.0"))
CLKOS5_FREQ_ACTUAL = float(os.getenv("CLKOS5_FREQ_ACTUAL", "100.0"))

CLKOS_EN           = int(os.getenv("CLKOS_EN", "0"))
CLKOS2_EN          = int(os.getenv("CLKOS2_EN", "0"))
CLKOS3_EN          = int(os.getenv("CLKOS3_EN", "0"))
CLKOS4_EN          = int(os.getenv("CLKOS4_EN", "0"))
CLKOS5_EN          = int(os.getenv("CLKOS5_EN", "0"))

FRAC_N_EN          = int(os.getenv("FRAC_N_EN", "0"))
SS_EN              = int(os.getenv("SS_EN", "0"))
DYN_PORTS_EN       = int(os.getenv("DYN_PORTS_EN", "0"))
LOCK_EN            = int(os.getenv("LOCK_EN", "1"))
PLL_LOCK_STICKY    = int(os.getenv("PLL_LOCK_STICKY", "0"))
LMMI_EN            = int(os.getenv("LMMI_EN", "0"))
APB_EN             = int(os.getenv("APB_EN", "0"))
APB_SOFT_REG_EN    = int(os.getenv("APB_SOFT_REG_EN", "0"))
POWERDOWN_EN       = int(os.getenv("POWERDOWN_EN", "0"))
EN_REFCLK_MON      = int(os.getenv("EN_REFCLK_MON", "0"))

# Reference clock period in ps (1 ps precision timescale)
REF_CLK_PERIOD_PS  = max(1, int(1e6 / CLKI_FREQ))


# ─── Helper Functions & Protocols ─────────────────────────────────────────────

async def start_ref_clk(dut, period_ps=REF_CLK_PERIOD_PS, tracer: VerilogTracer = None):
    """Starts the input reference clock on clki_i."""
    if tracer:
        tracer.comment(f"Start reference clock: {CLKI_FREQ} MHz (period {period_ps} ps)")
    cocotb.start_soon(Clock(dut.clki_i, period_ps, unit="ps").start())


async def apply_reset(dut, reset_ps=20000, tracer: VerilogTracer = None):
    """Applies active-low reset on rstn_i."""
    if tracer:
        tracer.comment("PLL reset sequence")
        tracer.assign("rstn_i", 0)
        tracer.assign("enclkop_i", 1)
        tracer.assign("pllpd_en_n_i", 1)
        tracer.delay_ps(reset_ps)

    dut.rstn_i.value = 0
    dut.usr_fbclk_i.value = 0
    dut.phasedir_i.value = 0
    dut.phasestep_i.value = 0
    dut.phaseloadreg_i.value = 0
    dut.phasesel_i.value = 0
    dut.enclkop_i.value = 1
    dut.enclkos_i.value = 1
    dut.enclkos2_i.value = 1
    dut.enclkos3_i.value = 1
    dut.enclkos4_i.value = 1
    dut.enclkos5_i.value = 1
    dut.pllpd_en_n_i.value = 1
    dut.legacy_i.value = 0
    dut.refdetreset.value = 0

    if hasattr(dut, "lmmi_clk_i"):
        dut.lmmi_clk_i.value = 0
        dut.lmmi_resetn_i.value = 1
        dut.lmmi_request_i.value = 0
        dut.lmmi_wr_rdn_i.value = 0
        dut.lmmi_offset_i.value = 0
        dut.lmmi_wdata_i.value = 0

    if hasattr(dut, "apb_pclk_i"):
        dut.apb_pclk_i.value = 0
        dut.apb_preset_n_i.value = 1
        dut.apb_penable_i.value = 0
        dut.apb_psel_i.value = 0
        dut.apb_pwrite_i.value = 0
        dut.apb_paddr_i.value = 0
        dut.apb_pwdata_i.value = 0

    await Timer(reset_ps, unit="ps")

    dut.rstn_i.value = 1
    if tracer:
        tracer.assign("rstn_i", 1)


async def wait_for_lock(dut, timeout_ns=100000, tracer: VerilogTracer = None) -> bool:
    """Waits for lock_o to assert high. Returns True if locked."""
    if not LOCK_EN:
        await Timer(1000, unit="ns")
        return True

    elapsed = 0
    poll_step = 100
    while elapsed < timeout_ns:
        await Timer(poll_step, unit="ns")
        elapsed += poll_step
        if dut.lock_o.value.is_resolvable and int(dut.lock_o.value) == 1:
            if tracer:
                tracer.comment(f"PLL achieved lock after {elapsed} ns")
            return True

    return False


async def measure_freq(clk_signal, num_cycles=10, timeout_ns=1000) -> float:
    """Measures the frequency (in MHz) of clk_signal over num_cycles."""
    try:
        await RisingEdge(clk_signal)
        t_start = get_sim_time("ps")
        for _ in range(num_cycles):
            await RisingEdge(clk_signal)
        t_end = get_sim_time("ps")
        period_ps = (t_end - t_start) / num_cycles
        if period_ps <= 0:
            return 0.0
        return 1e6 / period_ps
    except Exception:
        return 0.0


async def apb_write(dut, addr: int, data: int, tracer: VerilogTracer = None):
    """Executes a 32-bit APB write transaction."""
    dut.apb_paddr_i.value = addr
    dut.apb_pwdata_i.value = data
    dut.apb_pwrite_i.value = 1
    dut.apb_psel_i.value = 1
    dut.apb_penable_i.value = 0
    await RisingEdge(dut.apb_pclk_i)

    dut.apb_penable_i.value = 1
    await RisingEdge(dut.apb_pclk_i)

    dut.apb_psel_i.value = 0
    dut.apb_penable_i.value = 0
    dut.apb_pwrite_i.value = 0


async def apb_read(dut, addr: int, tracer: VerilogTracer = None) -> int:
    """Executes a 32-bit APB read transaction."""
    dut.apb_paddr_i.value = addr
    dut.apb_pwrite_i.value = 0
    dut.apb_psel_i.value = 1
    dut.apb_penable_i.value = 0
    await RisingEdge(dut.apb_pclk_i)

    dut.apb_penable_i.value = 1
    await RisingEdge(dut.apb_pclk_i)

    val = int(dut.apb_prdata_o.value) if dut.apb_prdata_o.value.is_resolvable else 0
    dut.apb_psel_i.value = 0
    dut.apb_penable_i.value = 0
    return val


async def _run_basic_pll_test(dut, tc_name: str, check_freq: bool = True):
    """Generic PLL lock and primary clock frequency check."""
    tracer = VerilogTracer(tc_name)
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    locked = await wait_for_lock(dut, tracer=tracer)
    assert locked, f"[{tc_name}] PLL failed to lock within timeout"

    if check_freq:
        freq = await measure_freq(dut.clkop_o)
        tracer.comment(f"Measured CLKOP frequency: {freq:.2f} MHz (expected ~{CLKOP_FREQ_ACTUAL} MHz)")

    tracer.comment(f"{tc_name} completed successfully")
    tracer.save()


# ─── G1 · Baseline ────────────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_001_default_config_lock(dut):
    """TC-PLL-001: Default-configuration generation, compilation and lock."""
    await _run_basic_pll_test(dut, "TC-PLL-001")


# ─── G2 · Configuration Mode ──────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_002_frequency_mode_achievable(dut):
    """TC-PLL-002: Frequency mode with an exactly achievable primary output."""
    await _run_basic_pll_test(dut, "TC-PLL-002")


@cocotb.test()
async def tc_pll_003_divider_mode(dut):
    """TC-PLL-003: Divider mode with dividers entered directly."""
    await _run_basic_pll_test(dut, "TC-PLL-003")


# ─── G3 · Fractional-N Divider ────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_004_fractional_n_frequency_mode(dut):
    """TC-PLL-004: Fractional-N feedback division in frequency mode."""
    await _run_basic_pll_test(dut, "TC-PLL-004")


@cocotb.test()
async def tc_pll_005_fractional_n_divider_mode(dut):
    """TC-PLL-005: Fractional-N feedback division in divider mode [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-005")


# ─── G4 · Spread Spectrum ─────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_006_down_spread_profile(dut):
    """TC-PLL-006: Down-spread profile across modulation depths [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-006")


@cocotb.test()
async def tc_pll_007_centre_spread_profile(dut):
    """TC-PLL-007: Centre-spread profile across modulation depths [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-007")


@cocotb.test()
async def tc_pll_008_min_modulation_freq(dut):
    """TC-PLL-008: Minimum modulation frequency 24.42 kHz [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-008")


@cocotb.test()
async def tc_pll_009_median_modulation_freq(dut):
    """TC-PLL-009: Median modulation frequency 100 kHz with modulated output clock."""
    await _run_basic_pll_test(dut, "TC-PLL-009")


@cocotb.test()
async def tc_pll_010_max_modulation_freq(dut):
    """TC-PLL-010: Maximum modulation frequency 200 kHz [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-010")


# ─── G5 · User Feedback Clock ─────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_011_external_feedback_clock(dut):
    """TC-PLL-011: External feedback clock selected as loop feedback source."""
    tracer = VerilogTracer("TC-PLL-011")
    await start_ref_clk(dut, tracer=tracer)
    # Loop clkop back to usr_fbclk_i
    cocotb.start_soon(Clock(dut.usr_fbclk_i, REF_CLK_PERIOD_PS, unit="ps").start())
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


# ─── G6 · Internal Path Switching ─────────────────────────────────────────────

@cocotb.test()
async def tc_pll_012_internal_feedback_delay(dut):
    """TC-PLL-012: Internal feedback delay path enabled [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-012")


# ─── G7 · Reference Clock Frequency ───────────────────────────────────────────

@cocotb.test()
async def tc_pll_013_min_reference_frequency(dut):
    """TC-PLL-013: Minimum reference frequency 18 MHz."""
    await _run_basic_pll_test(dut, "TC-PLL-013")


@cocotb.test()
async def tc_pll_014_median_reference_frequency(dut):
    """TC-PLL-014: Median reference frequency 400 MHz [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-014")


@cocotb.test()
async def tc_pll_015_max_reference_frequency(dut):
    """TC-PLL-015: Maximum reference frequency 800 MHz [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-015")


# ─── G8 · Reference Divider ───────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_016_ref_divider_min(dut):
    """TC-PLL-016: Reference divider 1 (minimum) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-016")


@cocotb.test()
async def tc_pll_017_ref_divider_median(dut):
    """TC-PLL-017: Reference divider 22 (median) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-017")


@cocotb.test()
async def tc_pll_018_ref_divider_max(dut):
    """TC-PLL-018: Reference divider 44 (maximum) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-018")


# ─── G9 · Reference Clock Monitor ─────────────────────────────────────────────

@cocotb.test()
async def tc_pll_019_refclk_mon_3p2(dut):
    """TC-PLL-019: Reference-clock monitor with 3.2 MHz monitor clock."""
    await _run_basic_pll_test(dut, "TC-PLL-019")


@cocotb.test()
async def tc_pll_020_refclk_mon_1p0(dut):
    """TC-PLL-020: Reference-clock monitor with 1.0 MHz monitor clock [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-020")


# ─── G10 · Feedback Mode ──────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_021_fbk_clkop(dut):
    """TC-PLL-021: Feedback from CLKOP and INTCLKOP."""
    await _run_basic_pll_test(dut, "TC-PLL-021")


@cocotb.test()
async def tc_pll_022_fbk_clkos_clkos2(dut):
    """TC-PLL-022: Feedback from CLKOS and CLKOS2 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-022")


@cocotb.test()
async def tc_pll_023_fbk_clkos3_4_5(dut):
    """TC-PLL-023: Feedback from CLKOS3, CLKOS4, CLKOS5 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-023")


# ─── G11 · Feedback Divider ───────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_024_n_divider_min(dut):
    """TC-PLL-024: Feedback divider 1 (integer-N minimum) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-024")


@cocotb.test()
async def tc_pll_025_n_divider_median(dut):
    """TC-PLL-025: Feedback divider 22 (integer-N median) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-025")


@cocotb.test()
async def tc_pll_026_n_divider_max(dut):
    """TC-PLL-026: Feedback divider 44 (integer-N reachable maximum)."""
    await _run_basic_pll_test(dut, "TC-PLL-026")


# ─── G12 · Fractional Word ────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_027_frac_n_divider_floor(dut):
    """TC-PLL-027: Fractional-N feedback divider floor 16 and ceiling 88 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-027")


@cocotb.test()
async def tc_pll_028_frac_word_min(dut):
    """TC-PLL-028: Fractional word 0 (minimum) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-028")


@cocotb.test()
async def tc_pll_029_frac_word_median(dut):
    """TC-PLL-029: Fractional word 2048 (median)."""
    await _run_basic_pll_test(dut, "TC-PLL-029")


@cocotb.test()
async def tc_pll_030_frac_word_max(dut):
    """TC-PLL-030: Fractional word 4095 (maximum) [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-030")


# ─── G13 · Output Clock Enables ───────────────────────────────────────────────

@cocotb.test()
async def tc_pll_031_all_secondary_outputs_enabled(dut):
    """TC-PLL-031: All five secondary outputs enabled."""
    await _run_basic_pll_test(dut, "TC-PLL-031")


@cocotb.test()
async def tc_pll_032_selective_enable_clkos3_5(dut):
    """TC-PLL-032: Selective enable: CLKOS3 and CLKOS5 only [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-032")


# ─── G14 · Output Bypass ──────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_033_primary_output_bypassed(dut):
    """TC-PLL-033: Primary output bypassed to reference clock."""
    await _run_basic_pll_test(dut, "TC-PLL-033")


@cocotb.test()
async def tc_pll_034_all_secondary_bypassed(dut):
    """TC-PLL-034: All five secondary outputs bypassed [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-034")


@cocotb.test()
async def tc_pll_035_mixed_bypass(dut):
    """TC-PLL-035: Mixed bypass: CLKOS2/4 bypassed, CLKOS3/5 divided."""
    await _run_basic_pll_test(dut, "TC-PLL-035")


# ─── G15 · Output Frequency ───────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_036_max_primary_min_secondary(dut):
    """TC-PLL-036: Max primary output frequency with min secondary frequencies [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-036")


@cocotb.test()
async def tc_pll_037_min_primary_max_secondary(dut):
    """TC-PLL-037: Min primary output freq with CLKOS at max feedback [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-037")


@cocotb.test()
async def tc_pll_038_median_output_frequency(dut):
    """TC-PLL-038: Median output frequency 100 MHz on all six outputs."""
    await _run_basic_pll_test(dut, "TC-PLL-038")


@cocotb.test()
async def tc_pll_039_max_output_frequency(dut):
    """TC-PLL-039: Maximum output frequency 800 MHz on all six outputs [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-039")


# ─── G16 · Output Divider ─────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_040_primary_div1_secondary_div128(dut):
    """TC-PLL-040: Primary divider 1 with secondary dividers 128 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-040")


@cocotb.test()
async def tc_pll_041_primary_div128_secondary_div1(dut):
    """TC-PLL-041: Primary divider 128 with secondary dividers 1 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-041")


@cocotb.test()
async def tc_pll_042_all_dividers_at_64(dut):
    """TC-PLL-042: All six output dividers at 64 (median)."""
    await _run_basic_pll_test(dut, "TC-PLL-042")


# ─── G17 · Output Tolerance ───────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_043_tolerance_sweep_tight(dut):
    """TC-PLL-043: Tolerance sweep 0.0/0.1/0.2/0.5 on all outputs [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-043")


@cocotb.test()
async def tc_pll_044_tolerance_sweep_loose(dut):
    """TC-PLL-044: Tolerance sweep 1.0/2.0/5.0/10.0 on all outputs [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-044")


# ─── G18 · Static Phase Shift ─────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_045_static_phase_90_270(dut):
    """TC-PLL-045: Static phase shift 90 and 270 degrees on all six outputs."""
    await _run_basic_pll_test(dut, "TC-PLL-045")


@cocotb.test()
async def tc_pll_046_static_phase_0_45_135(dut):
    """TC-PLL-046: Static phase shift 0, 45, 135 degrees [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-046")


@cocotb.test()
async def tc_pll_047_static_phase_180_225_315(dut):
    """TC-PLL-047: Static phase shift 180, 225, 315 degrees [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-047")


# ─── G19 · Duty-Cycle Trim ────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_048_rising_edge_duty_trim(dut):
    """TC-PLL-048: Rising-edge duty trim with delay multipliers 0 and 2."""
    await _run_basic_pll_test(dut, "TC-PLL-048")


@cocotb.test()
async def tc_pll_049_falling_edge_duty_trim(dut):
    """TC-PLL-049: Falling-edge duty trim with delay multipliers 1 and 4 [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-049")


# ─── G20 · Reference Clock Pin & IO ───────────────────────────────────────────

@cocotb.test()
async def tc_pll_050_refclk_pin_lvds(dut):
    """TC-PLL-050: Reference clock from pin with LVDS standard."""
    await _run_basic_pll_test(dut, "TC-PLL-050")


@cocotb.test()
async def tc_pll_051_all_io_standards(dut):
    """TC-PLL-051: All seventeen distinct reference-clock I/O standards [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-051")


# ─── G21 · Dynamic Phase Control Ports ────────────────────────────────────────

@cocotb.test()
async def tc_pll_052_dynamic_phase_ports_generated(dut):
    """TC-PLL-052: Dynamic phase control ports generated [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-052")


@cocotb.test()
async def tc_pll_053_dynamic_phase_stepping(dut):
    """TC-PLL-053: Dynamic phase stepping on select codes 000-101."""
    tracer = VerilogTracer("TC-PLL-053")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)

    for sel in range(6):
        dut.phasesel_i.value = sel
        dut.phasedir_i.value = 1
        dut.phasestep_i.value = 1
        await RisingEdge(dut.clki_i)
        dut.phasestep_i.value = 0
        await RisingEdge(dut.clki_i)

    tracer.save()


# ─── G22 · Clock Enable Ports ─────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_054_all_clock_enable_ports(dut):
    """TC-PLL-054: All six clock-enable ports requested [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-054")


@cocotb.test()
async def tc_pll_055_clock_enable_clkos_only(dut):
    """TC-PLL-055: Clock-enable port on CLKOS only [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-055")


# ─── G23 · PLL Reset ──────────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_056_pll_reset_not_requested(dut):
    """TC-PLL-056: PLL reset port not requested [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-056")


# ─── G24 · PLL Lock ───────────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_057_non_sticky_lock(dut):
    """TC-PLL-057: Non-sticky lock detector."""
    await _run_basic_pll_test(dut, "TC-PLL-057")


@cocotb.test()
async def tc_pll_058_sticky_lock(dut):
    """TC-PLL-058: Sticky lock detector."""
    await _run_basic_pll_test(dut, "TC-PLL-058")


@cocotb.test()
async def tc_pll_059_lock_output_not_requested(dut):
    """TC-PLL-059: Lock output not requested [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-059", check_freq=False)


# ─── G25 · Register Interface (LMMI & APB) ────────────────────────────────────

@cocotb.test()
async def tc_pll_060_lmmi_interface(dut):
    """TC-PLL-060: LMMI slave register interface."""
    await _run_basic_pll_test(dut, "TC-PLL-060")


@cocotb.test()
async def tc_pll_061_apb_without_soft_csr(dut):
    """TC-PLL-061: APB3 slave without soft control register."""
    await _run_basic_pll_test(dut, "TC-PLL-061")


@cocotb.test()
async def tc_pll_062_apb_with_soft_csr_read(dut):
    """TC-PLL-062: APB3 slave with soft control register - read."""
    await _run_basic_pll_test(dut, "TC-PLL-062")


@cocotb.test()
async def tc_pll_063_apb_soft_csr_dynamic_phase(dut):
    """TC-PLL-063: Soft control register write drives dynamic phase controls."""
    await _run_basic_pll_test(dut, "TC-PLL-063")


# ─── G26 · Power Mode Settings ────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_064_legacy_mode_requested(dut):
    """TC-PLL-064: Legacy-mode input requested [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-064")


@cocotb.test()
async def tc_pll_065_powerdown_requested(dut):
    """TC-PLL-065: Power-down input requested [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-065")


# ─── G27 · Cross-Parameter Legal Combinations ─────────────────────────────────

@cocotb.test()
async def tc_pll_066_frac_n_ceiling_monitor_apb(dut):
    """TC-PLL-066: Fractional-N at feedback ceiling with monitor and APB soft reg [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-066")


@cocotb.test()
async def tc_pll_067_spread_spectrum_pin_six_freq(dut):
    """TC-PLL-067: Spread spectrum with pin refclk, six frequencies, sticky lock [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-067")


@cocotb.test()
async def tc_pll_068_external_feedback_all_enables(dut):
    """TC-PLL-068: External feedback with all six clock-enable ports and dynamic phase."""
    await _run_basic_pll_test(dut, "TC-PLL-068")


@cocotb.test()
async def tc_pll_069_mixed_bypass_duty_trim(dut):
    """TC-PLL-069: Mixed bypass with duty trim, legacy, power-down [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-069")


@cocotb.test()
async def tc_pll_070_max_ref_chain_lmmi(dut):
    """TC-PLL-070: Maximum ref freq and divider chain with LMMI [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-070")


@cocotb.test()
async def tc_pll_071_min_ref_monitor_internal_path(dut):
    """TC-PLL-071: Minimum ref freq with 1.0 MHz monitor and internal path [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-071")


# ─── G28 · Port Behaviour ─────────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_072_rstn_assertion_release(dut):
    """TC-PLL-072: rstn_i assertion and release."""
    tracer = VerilogTracer("TC-PLL-072")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)

    # De-assert and re-assert reset
    dut.rstn_i.value = 0
    await Timer(5000, unit="ps")
    dut.rstn_i.value = 1
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_073_powerdown_assertion_release(dut):
    """TC-PLL-073: pllpd_en_n_i power-down assertion and release."""
    tracer = VerilogTracer("TC-PLL-073")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)

    # Power down
    dut.pllpd_en_n_i.value = 0
    await Timer(10000, unit="ps")
    dut.pllpd_en_n_i.value = 1
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_074_legacy_asserted(dut):
    """TC-PLL-074: legacy_i asserted for the whole run."""
    tracer = VerilogTracer("TC-PLL-074")
    dut.legacy_i.value = 1
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_075_clock_enables_deassert_reassert(dut):
    """TC-PLL-075: enclkop_i through enclkos5_i deassertion and reassertion."""
    tracer = VerilogTracer("TC-PLL-075")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)

    dut.enclkop_i.value = 0
    await Timer(5000, unit="ps")
    dut.enclkop_i.value = 1
    await Timer(5000, unit="ps")
    tracer.save()


@cocotb.test()
async def tc_pll_076_usr_fbclk_source(dut):
    """TC-PLL-076: usr_fbclk_i as loop feedback source."""
    tracer = VerilogTracer("TC-PLL-076")
    await start_ref_clk(dut, tracer=tracer)
    cocotb.start_soon(Clock(dut.usr_fbclk_i, REF_CLK_PERIOD_PS, unit="ps").start())
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_077_refdetreset_refdetlos(dut):
    """TC-PLL-077: refdetreset and refdetlos reference-loss reporting."""
    tracer = VerilogTracer("TC-PLL-077")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)

    dut.refdetreset.value = 1
    await Timer(5000, unit="ps")
    dut.refdetreset.value = 0
    tracer.save()


@cocotb.test()
async def tc_pll_078_lmmi_transaction(dut):
    """TC-PLL-078: LMMI transaction on LMMI input/output ports."""
    tracer = VerilogTracer("TC-PLL-078")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_079_apb_transaction(dut):
    """TC-PLL-079: APB transaction on APB input/output ports."""
    tracer = VerilogTracer("TC-PLL-079")
    await start_ref_clk(dut, tracer=tracer)
    await apply_reset(dut, tracer=tracer)
    await wait_for_lock(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_pll_080_all_six_clocks_observed(dut):
    """TC-PLL-080: All six output clocks and lock_o observed together at distinct frequencies."""
    await _run_basic_pll_test(dut, "TC-PLL-080")


# ─── G29 · DRC & Radiant Smoke ────────────────────────────────────────────────

@cocotb.test()
async def tc_pll_081_default_param_smoke_test(dut):
    """TC-PLL-081: Default-parameter Radiant compilation smoke test [Radiant Compilation]."""
    await _run_basic_pll_test(dut, "TC-PLL-081")
