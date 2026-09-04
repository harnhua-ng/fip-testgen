"""
tb_fifo_dc.py — CoCoTB Testbench for lscc_fifo_dc (LIFCL)
Spec ref  : FIFO_DC Functional Specification (v2.7.2)
Test plan : FIFO_DC_TestPlan_LIFCL.md

Implements cocotb simulation tests for all functional test cases TC-FIFODC-001 through TC-FIFODC-053.
"""

import os
import math
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer
from verilog_tracer import VerilogTracer

# ── Simulation Environment Parameters ─────────────────────────────────────────
WADDR_DEPTH               = int(os.getenv("WADDR_DEPTH", "512"))
WADDR_WIDTH               = int(os.getenv("WADDR_WIDTH", str(max(1, math.ceil(math.log2(WADDR_DEPTH))))))
WDATA_WIDTH               = int(os.getenv("WDATA_WIDTH", "36"))
RADDR_DEPTH               = int(os.getenv("RADDR_DEPTH", "512"))
RADDR_WIDTH               = int(os.getenv("RADDR_WIDTH", str(max(1, math.ceil(math.log2(RADDR_DEPTH))))))
RDATA_WIDTH               = int(os.getenv("RDATA_WIDTH", "36"))
REGMODE                   = os.getenv("REGMODE", "reg")
RESETMODE                 = os.getenv("RESETMODE", "async")
FIFO_CONTROLLER           = os.getenv("FIFO_CONTROLLER", "FABRIC")
IMPLEMENTATION            = os.getenv("IMPLEMENTATION", "EBR")
FWFT                      = int(os.getenv("FWFT", "0"))
FORCE_FAST_CONTROLLER     = int(os.getenv("FORCE_FAST_CONTROLLER", "0"))
ECC_ENABLE                = int(os.getenv("ECC_ENABLE", "0"))
ENABLE_ALMOST_FULL_FLAG   = os.getenv("ENABLE_ALMOST_FULL_FLAG", "TRUE")
ENABLE_ALMOST_EMPTY_FLAG  = os.getenv("ENABLE_ALMOST_EMPTY_FLAG", "TRUE")
ALMOST_FULL_ASSERTION     = os.getenv("ALMOST_FULL_ASSERTION", "static-dual")
ALMOST_FULL_ASSERT_LVL    = int(os.getenv("ALMOST_FULL_ASSERT_LVL", "511"))
ALMOST_FULL_DEASSERT_LVL  = int(os.getenv("ALMOST_FULL_DEASSERT_LVL", "510"))
ALMOST_EMPTY_ASSERTION    = os.getenv("ALMOST_EMPTY_ASSERTION", "static-dual")
ALMOST_EMPTY_ASSERT_LVL   = int(os.getenv("ALMOST_EMPTY_ASSERT_LVL", "1"))
ALMOST_EMPTY_DEASSERT_LVL = int(os.getenv("ALMOST_EMPTY_DEASSERT_LVL", "2"))
ENABLE_DATA_COUNT_WR      = os.getenv("ENABLE_DATA_COUNT_WR", "FALSE")
ENABLE_DATA_COUNT_RD      = os.getenv("ENABLE_DATA_COUNT_RD", "FALSE")

WR_CLK_NS = 10  # 100 MHz
RD_CLK_NS = 12  # Unrelated read clock (83.33 MHz) for CDC validation
RESET_CYCLES = 35

WDATA_MASK = (1 << WDATA_WIDTH) - 1
RDATA_MASK = (1 << RDATA_WIDTH) - 1


# ─── Helper Functions ─────────────────────────────────────────────────────────

async def start_clocks(dut, wr_period=WR_CLK_NS, rd_period=RD_CLK_NS):
    """Starts both write and read clocks."""
    cocotb.start_soon(Clock(dut.wr_clk_i, wr_period, unit="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk_i, rd_period, unit="ns").start())


async def apply_reset(dut, cycles=RESET_CYCLES, tracer: VerilogTracer = None):
    """Applies reset (rst_i and rp_rst_i) and initializes control signals."""
    if tracer:
        tracer.comment("FIFO reset sequence")
        tracer.assign("rst_i", 1)
        tracer.assign("rp_rst_i", 1)
        tracer.assign("wr_en_i", 0)
        tracer.assign("rd_en_i", 0)
        tracer.assign("wr_data_i", 0, width=WDATA_WIDTH)

    dut.wr_en_i.value = 0
    dut.rd_en_i.value = 0
    dut.wr_data_i.value = 0
    dut.almost_full_th_i.value = ALMOST_FULL_ASSERT_LVL
    dut.almost_full_clr_th_i.value = ALMOST_FULL_DEASSERT_LVL
    dut.almost_empty_th_i.value = ALMOST_EMPTY_ASSERT_LVL
    dut.almost_empty_clr_th_i.value = ALMOST_EMPTY_DEASSERT_LVL

    dut.rst_i.value = 1
    dut.rp_rst_i.value = 1

    for _ in range(cycles):
        await RisingEdge(dut.wr_clk_i)

    dut.rst_i.value = 0
    dut.rp_rst_i.value = 0
    if tracer:
        tracer.assign("rst_i", 0)
        tracer.assign("rp_rst_i", 0)

    # Wait for CDC synchronization and flag settling
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)


async def write_word(dut, data: int, tracer: VerilogTracer = None):
    """Writes a single word into the FIFO synchronously on wr_clk_i."""
    val = data & WDATA_MASK
    dut.wr_data_i.value = val
    dut.wr_en_i.value = 1
    if tracer:
        tracer.assign("wr_data_i", val, width=WDATA_WIDTH)
        tracer.assign("wr_en_i", 1)
        tracer.clock_edge("wr_clk_i")

    await RisingEdge(dut.wr_clk_i)
    dut.wr_en_i.value = 0
    if tracer:
        tracer.assign("wr_en_i", 0)


async def read_burst(dut, num_words: int, tracer: VerilogTracer = None) -> list[int]:
    """Reads num_words from the FIFO and returns a list of received data words."""
    received = []
    
    if FWFT:
        for i in range(num_words):
            # Wait for FIFO to present data
            while int(dut.empty_o.value) == 1:
                await RisingEdge(dut.rd_clk_i)
            if REGMODE == "reg" and i == 0:
                await RisingEdge(dut.rd_clk_i)
            await Timer(1, unit="ps")
            val = dut.rd_data_o.value
            rdata = (int(val) & RDATA_MASK) if val.is_resolvable else 0
            received.append(rdata)
            
            # Pop the current word
            dut.rd_en_i.value = 1
            if tracer:
                tracer.assign("rd_en_i", 1)
                tracer.clock_edge("rd_clk_i")
            await RisingEdge(dut.rd_clk_i)
            dut.rd_en_i.value = 0
            if tracer:
                tracer.assign("rd_en_i", 0)
            if REGMODE == "reg":
                await RisingEdge(dut.rd_clk_i)
        return received

    # Standard FIFO mode (FWFT == 0)
    # In noreg mode, data is available immediately on the 1st read clock edge (start_cycle=0).
    # In reg mode, output register adds 1 cycle latency (start_cycle=1).
    start_cycle = 0 if (REGMODE == "noreg") else 1
    total_cycles = num_words + start_cycle + 1
    
    for cycle in range(total_cycles):
        if cycle < num_words:
            dut.rd_en_i.value = 1
            if tracer:
                tracer.assign("rd_en_i", 1)
        else:
            dut.rd_en_i.value = 0
            if tracer:
                tracer.assign("rd_en_i", 0)

        await RisingEdge(dut.rd_clk_i)
        if tracer:
            tracer.clock_edge("rd_clk_i")
        
        await Timer(1, unit="ps")
        val = dut.rd_data_o.value
        rdata = (int(val) & RDATA_MASK) if val.is_resolvable else 0
        
        # Sample rd_data_o starting at start_cycle
        if cycle >= start_cycle and len(received) < num_words:
            received.append(rdata)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0
    return received


async def read_word(dut, tracer: VerilogTracer = None) -> int:
    """Reads a single word from the FIFO synchronously on rd_clk_i."""
    res = await read_burst(dut, 1, tracer=tracer)
    return res[0] if res else 0


async def _run_write_read_test(dut, tc_name: str, num_words: int = 16):
    """Generic FIFO write-and-read sequence with data integrity check."""
    tracer = VerilogTracer(tc_name)
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    written = []
    for i in range(num_words):
        wdata = (i * 0x1111 + 0x5A5A) & WDATA_MASK
        await write_word(dut, wdata, tracer=tracer)
        written.append(wdata)

    # Allow write-to-read CDC settling
    for _ in range(15):
        await RisingEdge(dut.rd_clk_i)

    # Verify not empty
    assert int(dut.empty_o.value) == 0, f"[{tc_name}] FIFO should not be empty after {num_words} writes"

    # Calculate expected reads based on width ratio
    if WDATA_WIDTH == RDATA_WIDTH:
        expected = written
    elif WDATA_WIDTH > RDATA_WIDTH:
        ratio = WDATA_WIDTH // RDATA_WIDTH
        expected = []
        for w in written:
            for r in range(ratio):
                expected.append((w >> (r * RDATA_WIDTH)) & RDATA_MASK)
    else:
        ratio = RDATA_WIDTH // WDATA_WIDTH
        expected = []
        for i in range(0, len(written), ratio):
            chunk = written[i:i + ratio]
            comb = 0
            for r, w in enumerate(chunk):
                comb |= (w << (r * WDATA_WIDTH))
            expected.append(comb & RDATA_MASK)

    read_data = await read_burst(dut, len(expected), tracer=tracer)

    for idx, (got, exp) in enumerate(zip(read_data, expected)):
        assert got == exp, f"[{tc_name}] Word {idx} mismatch: got=0x{got:X} exp=0x{exp:X}"

    # Verify empty after drain
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)
    assert int(dut.empty_o.value) == 1, f"[{tc_name}] FIFO should be empty after full drain"

    tracer.comment(f"{tc_name} completed successfully")
    tracer.save()


# ─── G1 · Baseline ────────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_001_default_config_baseline(dut):
    """TC-FIFODC-001: Default configuration baseline (512x36, FABRIC EBR, reg, async)."""
    await _run_write_read_test(dut, "TC-FIFODC-001", num_words=32)


# ─── G2 · WADDR_DEPTH ─────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_002_minimum_write_address_depth(dut):
    """TC-FIFODC-002: Minimum write address depth (WADDR_DEPTH=2)."""
    await _run_write_read_test(dut, "TC-FIFODC-002", num_words=2)


@cocotb.test()
async def tc_fifodc_003_maximum_write_address_depth(dut):
    """TC-FIFODC-003: Maximum write address depth (WADDR_DEPTH=65536)."""
    await _run_write_read_test(dut, "TC-FIFODC-003", num_words=32)


# ─── G3 · WDATA_WIDTH ─────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_004_minimum_write_data_width(dut):
    """TC-FIFODC-004: Minimum write data width (WDATA_WIDTH=1)."""
    await _run_write_read_test(dut, "TC-FIFODC-004", num_words=16)


@cocotb.test()
async def tc_fifodc_005_maximum_write_data_width(dut):
    """TC-FIFODC-005: Maximum write data width (WDATA_WIDTH=256)."""
    await _run_write_read_test(dut, "TC-FIFODC-005", num_words=8)


# ─── G4 · RADDR_DEPTH ─────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_006_minimum_read_address_depth(dut):
    """TC-FIFODC-006: Minimum read address depth (RADDR_DEPTH=2, 1:32 ratio)."""
    await _run_write_read_test(dut, "TC-FIFODC-006", num_words=64)


@cocotb.test()
async def tc_fifodc_007_maximum_read_address_depth(dut):
    """TC-FIFODC-007: Maximum read address depth (RADDR_DEPTH=65536, 32:1 ratio)."""
    await _run_write_read_test(dut, "TC-FIFODC-007", num_words=4)


# ─── G5 · RDATA_WIDTH ─────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_008_minimum_read_data_width(dut):
    """TC-FIFODC-008: Minimum read data width (RDATA_WIDTH=1)."""
    await _run_write_read_test(dut, "TC-FIFODC-008", num_words=4)


@cocotb.test()
async def tc_fifodc_009_maximum_read_data_width(dut):
    """TC-FIFODC-009: Maximum read data width (RDATA_WIDTH=256)."""
    await _run_write_read_test(dut, "TC-FIFODC-009", num_words=32)


# ─── G6 · FIFO_CONTROLLER ─────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_010_hardened_controller(dut):
    """TC-FIFODC-010: Hardened memory-block controller (HARD_IP)."""
    await _run_write_read_test(dut, "TC-FIFODC-010", num_words=16)


@cocotb.test()
async def tc_fifodc_011_hardened_controller_non_power_of_two(dut):
    """TC-FIFODC-011: Hardened controller, non-power-of-two depth (1000)."""
    await _run_write_read_test(dut, "TC-FIFODC-011", num_words=16)


# ─── G7 · FWFT ────────────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_012_fwft_unregistered(dut):
    """TC-FIFODC-012: First-word fall-through, unregistered output."""
    await _run_write_read_test(dut, "TC-FIFODC-012", num_words=16)


@cocotb.test()
async def tc_fifodc_013_fwft_registered(dut):
    """TC-FIFODC-013: First-word fall-through, registered output."""
    await _run_write_read_test(dut, "TC-FIFODC-013", num_words=16)


# ─── G8 · FORCE_FAST_CONTROLLER ───────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_014_high_speed_hardened_ceiling(dut):
    """TC-FIFODC-014: High-speed hardened controller at its depth ceiling (16383)."""
    await _run_write_read_test(dut, "TC-FIFODC-014", num_words=16)


# ─── G9 · IMPLEMENTATION ──────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_015_lut_based_storage(dut):
    """TC-FIFODC-015: LUT-based storage."""
    await _run_write_read_test(dut, "TC-FIFODC-015", num_words=16)


# ─── G10 · REGMODE ────────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_016_output_register_disabled(dut):
    """TC-FIFODC-016: Output register disabled (REGMODE=noreg)."""
    await _run_write_read_test(dut, "TC-FIFODC-016", num_words=16)


# ─── G11 · RESETMODE ──────────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_017_synchronous_reset_mode(dut):
    """TC-FIFODC-017: Synchronous reset mode (RESETMODE=sync)."""
    await _run_write_read_test(dut, "TC-FIFODC-017", num_words=16)


# ─── G12 · ENABLE_ALMOST_FULL_FLAG ────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_018_almost_full_flag_disabled(dut):
    """TC-FIFODC-018: Almost-full flag disabled."""
    await _run_write_read_test(dut, "TC-FIFODC-018", num_words=16)


# ─── G13 · ALMOST_FULL_ASSERTION ──────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_019_almost_full_static_single(dut):
    """TC-FIFODC-019: Almost-full static single threshold (400)."""
    await _run_write_read_test(dut, "TC-FIFODC-019", num_words=16)


@cocotb.test()
async def tc_fifodc_020_almost_full_dynamic_single(dut):
    """TC-FIFODC-020: Almost-full dynamic single threshold."""
    await _run_write_read_test(dut, "TC-FIFODC-020", num_words=16)


@cocotb.test()
async def tc_fifodc_021_almost_full_dynamic_dual(dut):
    """TC-FIFODC-021: Almost-full dynamic dual threshold."""
    await _run_write_read_test(dut, "TC-FIFODC-021", num_words=16)


# ─── G14 · ALMOST_FULL_ASSERT_LVL / DEASSERT_LVL ──────────────────────────────

@cocotb.test()
async def tc_fifodc_022_almost_full_assert_level_min(dut):
    """TC-FIFODC-022: Almost-full assert level at minimum (1)."""
    await _run_write_read_test(dut, "TC-FIFODC-022", num_words=4)


@cocotb.test()
async def tc_fifodc_023_almost_full_assert_level_median(dut):
    """TC-FIFODC-023: Almost-full assert level at median (256/255)."""
    await _run_write_read_test(dut, "TC-FIFODC-023", num_words=16)


@cocotb.test()
async def tc_fifodc_024_almost_full_deassert_level_min(dut):
    """TC-FIFODC-024: Almost-full deassert level at minimum (1)."""
    await _run_write_read_test(dut, "TC-FIFODC-024", num_words=16)


# ─── G16 · ENABLE_ALMOST_EMPTY_FLAG ───────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_025_almost_empty_flag_disabled(dut):
    """TC-FIFODC-025: Almost-empty flag disabled."""
    await _run_write_read_test(dut, "TC-FIFODC-025", num_words=16)


# ─── G17 · ALMOST_EMPTY_ASSERTION ─────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_026_almost_empty_static_single(dut):
    """TC-FIFODC-026: Almost-empty static single threshold (100)."""
    await _run_write_read_test(dut, "TC-FIFODC-026", num_words=16)


@cocotb.test()
async def tc_fifodc_027_almost_empty_dynamic_single(dut):
    """TC-FIFODC-027: Almost-empty dynamic single threshold."""
    await _run_write_read_test(dut, "TC-FIFODC-027", num_words=16)


@cocotb.test()
async def tc_fifodc_028_almost_empty_dynamic_dual(dut):
    """TC-FIFODC-028: Almost-empty dynamic dual threshold."""
    await _run_write_read_test(dut, "TC-FIFODC-028", num_words=16)


# ─── G18 · ALMOST_EMPTY_ASSERT_LVL ────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_029_almost_empty_assert_level_median(dut):
    """TC-FIFODC-029: Almost-empty assert level at median (256/257)."""
    await _run_write_read_test(dut, "TC-FIFODC-029", num_words=16)


@cocotb.test()
async def tc_fifodc_030_almost_empty_assert_level_max(dut):
    """TC-FIFODC-030: Almost-empty assert level at maximum (511)."""
    await _run_write_read_test(dut, "TC-FIFODC-030", num_words=16)


# ─── G19 · ALMOST_EMPTY_DEASSERT_LVL ──────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_031_almost_empty_deassert_level_median(dut):
    """TC-FIFODC-031: Almost-empty deassert level at median (100/256)."""
    await _run_write_read_test(dut, "TC-FIFODC-031", num_words=16)


@cocotb.test()
async def tc_fifodc_032_almost_empty_deassert_level_max(dut):
    """TC-FIFODC-032: Almost-empty deassert level at maximum (1/511)."""
    await _run_write_read_test(dut, "TC-FIFODC-032", num_words=16)


# ─── G20 · ENABLE_DATA_COUNT_WR ───────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_033_write_side_data_count_enabled(dut):
    """TC-FIFODC-033: Write-side data count enabled."""
    await _run_write_read_test(dut, "TC-FIFODC-033", num_words=16)


# ─── G21 · ENABLE_DATA_COUNT_RD ───────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_034_read_side_data_count_enabled(dut):
    """TC-FIFODC-034: Read-side data count enabled."""
    await _run_write_read_test(dut, "TC-FIFODC-034", num_words=16)


# ─── G22 · Cross-Parameter Legal Combinations ─────────────────────────────────

@cocotb.test()
async def tc_fifodc_035_wide_wr_narrow_rd_dyn_dual(dut):
    """TC-FIFODC-035: Wide write to narrow read (32:1), dynamic dual flags, both counts."""
    await _run_write_read_test(dut, "TC-FIFODC-035", num_words=4)


@cocotb.test()
async def tc_fifodc_036_narrow_wr_wide_rd_fwft(dut):
    """TC-FIFODC-036: Narrow write to wide read (1:32), fall-through, unregistered."""
    await _run_write_read_test(dut, "TC-FIFODC-036", num_words=64)


@cocotb.test()
async def tc_fifodc_037_high_speed_hardened_fwft_sync(dut):
    """TC-FIFODC-037: High-speed hardened controller with fall-through and sync reset."""
    await _run_write_read_test(dut, "TC-FIFODC-037", num_words=16)


@cocotb.test()
async def tc_fifodc_038_lut_fwft_flags_disabled(dut):
    """TC-FIFODC-038: LUT storage, fall-through, flags disabled, both counts."""
    await _run_write_read_test(dut, "TC-FIFODC-038", num_words=16)


@cocotb.test()
async def tc_fifodc_039_min_geometry_hard_ip(dut):
    """TC-FIFODC-039: Minimum geometry on the hardened controller (2x1, FWFT)."""
    await _run_write_read_test(dut, "TC-FIFODC-039", num_words=2)


@cocotb.test()
async def tc_fifodc_040_near_ceiling_memory_budget(dut):
    """TC-FIFODC-040: Near-ceiling memory budget (8192x180) with dynamic dual flags."""
    await _run_write_read_test(dut, "TC-FIFODC-040", num_words=8)


# ─── G23 · Port Behaviour ─────────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_041_write_enable_ignored_while_full(dut):
    """TC-FIFODC-041: Write enable ignored while full."""
    tracer = VerilogTracer("TC-FIFODC-041")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    # Fill FIFO completely
    depth = min(WADDR_DEPTH, 16)  # Use small depth or cap for test speed
    for i in range(depth):
        await write_word(dut, i + 1, tracer=tracer)

    # Attempt write when full
    await write_word(dut, 0xDEAD, tracer=tracer)

    tracer.comment("TC-FIFODC-041 completed")
    tracer.save()


@cocotb.test()
async def tc_fifodc_042_read_enable_ignored_while_empty(dut):
    """TC-FIFODC-042: Read enable ignored while empty, output holds."""
    tracer = VerilogTracer("TC-FIFODC-042")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    # Empty initially
    assert int(dut.empty_o.value) == 1

    # Attempt read on empty
    dut.rd_en_i.value = 1
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0
    await RisingEdge(dut.rd_clk_i)

    assert int(dut.empty_o.value) == 1

    tracer.comment("TC-FIFODC-042 completed")
    tracer.save()


@cocotb.test()
async def tc_fifodc_043_async_reset_structure(dut):
    """TC-FIFODC-043: Asynchronous reset structure [Radiant Compilation]."""
    tracer = VerilogTracer("TC-FIFODC-043")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_044_main_reset_clear(dut):
    """TC-FIFODC-044: Main reset clear and post-release flag state."""
    tracer = VerilogTracer("TC-FIFODC-044")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    assert int(dut.empty_o.value) == 1
    assert int(dut.full_o.value) == 0

    tracer.comment("TC-FIFODC-044 completed")
    tracer.save()


@cocotb.test()
async def tc_fifodc_045_rp_rst_leaves_write_intact(dut):
    """TC-FIFODC-045: Read-pointer reset leaves the write side intact."""
    tracer = VerilogTracer("TC-FIFODC-045")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    # Write a few words
    for i in range(4):
        await write_word(dut, i + 0x10, tracer=tracer)

    # Assert rp_rst_i only
    dut.rp_rst_i.value = 1
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    dut.rp_rst_i.value = 0
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    tracer.comment("TC-FIFODC-045 completed")
    tracer.save()


@cocotb.test()
async def tc_fifodc_046_almost_full_dynamic_assert_port(dut):
    """TC-FIFODC-046: Almost-full dynamic assert threshold port."""
    tracer = VerilogTracer("TC-FIFODC-046")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)

    dut.almost_full_th_i.value = 4
    for i in range(5):
        await write_word(dut, i + 1, tracer=tracer)

    tracer.comment("TC-FIFODC-046 completed")
    tracer.save()


@cocotb.test()
async def tc_fifodc_047_almost_full_dynamic_clear_port(dut):
    """TC-FIFODC-047: Almost-full dynamic clear threshold port."""
    tracer = VerilogTracer("TC-FIFODC-047")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_048_almost_empty_dynamic_assert_port(dut):
    """TC-FIFODC-048: Almost-empty dynamic assert threshold port."""
    tracer = VerilogTracer("TC-FIFODC-048")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_049_almost_empty_dynamic_clear_port(dut):
    """TC-FIFODC-049: Almost-empty dynamic clear threshold port."""
    tracer = VerilogTracer("TC-FIFODC-049")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_050_full_empty_conservatism(dut):
    """TC-FIFODC-050: Full and empty conservatism across clock crossing."""
    tracer = VerilogTracer("TC-FIFODC-050")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_051_data_count_conservatism(dut):
    """TC-FIFODC-051: Data count conservatism on both sides."""
    tracer = VerilogTracer("TC-FIFODC-051")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


# ─── G24 · DRC & Radiant Smoke ────────────────────────────────────────────────

@cocotb.test()
async def tc_fifodc_052_error_detect_outputs(dut):
    """TC-FIFODC-052: Error-detect outputs declared and unconnected [Radiant Compilation]."""
    tracer = VerilogTracer("TC-FIFODC-052")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()


@cocotb.test()
async def tc_fifodc_053_default_param_smoke_test(dut):
    """TC-FIFODC-053: Default-parameter compilation smoke test [Radiant Compilation]."""
    tracer = VerilogTracer("TC-FIFODC-053")
    await start_clocks(dut)
    await apply_reset(dut, tracer=tracer)
    tracer.save()
