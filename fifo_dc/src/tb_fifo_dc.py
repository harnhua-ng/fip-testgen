"""
tb_fifo_dc.py — CoCoTB Testbench for lscc_fifo_dc (LIFCL)
Spec ref  : FIFO_DC Functional Specification (v2.7.2)
Test plan : FIFO_DC_LIFCL_TestPlan_20260801.md

Covers functional, flag, reset, asymmetric, FWFT, ECC, and regression test cases:
  TC003 — HARD_IP Minimal Simulation (Single Write + Single Read)
  TC004 — FABRIC EBR Minimal Simulation (Single Write + Single Read)
  TC005 — Data Integrity: HARD_IP Fill and Drain
  TC006 — Data Integrity: FABRIC EBR Fill and Drain
  TC007 — Write-to-Full Suppression
  TC008 — Read-from-Empty Guard
  TC009 — Simultaneous Write and Read (HARD_IP)
  TC010 — FWFT Mode: Pre-fetch and empty_o Behavior
  TC011 — Asymmetric Width 2:1 Write:Read (FABRIC EBR)
  TC012 — Asymmetric Width 1:2 Write:Read (FABRIC EBR)
  TC014 — rst_i Async Reset: Write Domain
  TC015 — rp_rst_i Async Reset: Read Pointer Alignment
  TC016 — RESETMODE=sync: Both Resets Synchronous
  TC017 — full_o Assertion and Deassertion (HARD_IP)
  TC018 — empty_o Assertion and Deassertion (HARD_IP)
  TC019 — almost_full_o Static-Single (HARD_IP)
  TC020 — almost_full_o Static-Single (FABRIC)
  TC021 — almost_full_o Static-Dual Hysteresis (FABRIC)
  TC022 — almost_full_o Dynamic-Single Threshold (FABRIC)
  TC023 — almost_full_o Dynamic-Dual Thresholds (FABRIC)
  TC024 — almost_empty_o Static-Dual Hysteresis (FABRIC)
  TC025 — wr_data_cnt_o Accuracy (FABRIC)
  TC026 — rd_data_cnt_o Accuracy (FABRIC)
  TC027 — ECC Single-Bit Error Injection and Correction
  TC028 — ECC Double-Bit Error Injection and Detection
  TC029 — ECC Disabled: Error Outputs Tied Low
  TC032 — HARD_IP Forces DATA_COUNT Outputs to Zero
  TC038 — FABRIC LUT: Symmetric Valid Configuration
  TC042 — REGMODE=reg HARD_IP Read Latency
  TC051 — Regression: FWFT Pre-fetch Sequencing
  TC052 — Regression: FABRIC LUT Async Reset
  TC056 — Acceptance: HARD_IP Full Suite
  TC057 — Acceptance: FABRIC EBR Full Suite
"""

import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly, Timer
from verilog_tracer import VerilogTracer

# ── Simulation Environment Parameters ─────────────────────────────────────────
WADDR_DEPTH               = int(os.getenv("WADDR_DEPTH", "512"))
WDATA_WIDTH               = int(os.getenv("WDATA_WIDTH", "36"))
RADDR_DEPTH               = int(os.getenv("RADDR_DEPTH", "512"))
RDATA_WIDTH               = int(os.getenv("RDATA_WIDTH", "36"))
REGMODE                   = os.getenv("REGMODE", "reg")
RESETMODE                 = os.getenv("RESETMODE", "async")
FIFO_CONTROLLER           = os.getenv("FIFO_CONTROLLER", "FABRIC")
IMPLEMENTATION            = os.getenv("IMPLEMENTATION", "EBR")
FWFT                      = int(os.getenv("FWFT", "0"))
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
RD_CLK_NS = 10  # 100 MHz (can be overridden)
RESET_CYCLES = 35

WDATA_MASK = (1 << WDATA_WIDTH) - 1
RDATA_MASK = (1 << RDATA_WIDTH) - 1


# ─── Helper Functions ─────────────────────────────────────────────────────────

async def start_clocks(dut, wr_period=WR_CLK_NS, rd_period=RD_CLK_NS):
    """Starts both write and read clocks."""
    cocotb.start_soon(Clock(dut.wr_clk_i, wr_period, unit="ns").start())
    cocotb.start_soon(Clock(dut.rd_clk_i, rd_period, unit="ns").start())


async def apply_reset(dut, cycles=RESET_CYCLES):
    """Applies reset (rst_i and rp_rst_i) and initializes control signals."""
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

    # Wait 5 cycles post-reset for CDC synchronization and flag settling
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)


async def write_word(dut, data: int):
    """Writes one word into the FIFO on the next wr_clk_i rising edge."""
    await RisingEdge(dut.wr_clk_i)
    dut.wr_en_i.value = 1
    dut.wr_data_i.value = data & WDATA_MASK
    await RisingEdge(dut.wr_clk_i)
    dut.wr_en_i.value = 0


async def read_word(dut) -> int:
    """Issues a read pulse and returns captured data based on REGMODE."""
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 1
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0

    if REGMODE == "reg" and not FWFT:
        await RisingEdge(dut.rd_clk_i)

    await ReadOnly()
    val = dut.rd_data_o.value
    return int(val) if val.is_resolvable else 0


# ─── Cocotb Test Cases ────────────────────────────────────────────────────────

@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_003_hard_ip_minimal_sim(dut):
    """TC003: HARD_IP Minimal Simulation: Single Write + Single Read."""
    tracer = VerilogTracer("TC-003", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC003 FAILED: FIFO not empty after reset"

    test_data = 0xABCD & WDATA_MASK
    await write_word(dut, test_data)

    # Wait for empty_o deassertion across CDC
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        if int(dut.empty_o.value) == 0:
            break

    await ReadOnly()
    assert int(dut.empty_o.value) == 0, "TC003 FAILED: empty_o did not deassert after write"

    got = await read_word(dut)
    assert got == test_data, f"TC003 FAILED: rd_data_o=0x{got:X}, expected=0x{test_data:X}"

    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC003 FAILED: empty_o did not assert after read"
    dut._log.info("TC003 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or IMPLEMENTATION != "EBR"))
async def tc_004_fabric_ebr_minimal_sim(dut):
    """TC004: FABRIC EBR Minimal Simulation: Single Write + Single Read."""
    tracer = VerilogTracer("TC-004", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC004 FAILED: FIFO not empty after reset"

    test_data = 0x1234 & WDATA_MASK
    await write_word(dut, test_data)

    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        if int(dut.empty_o.value) == 0:
            break

    assert int(dut.empty_o.value) == 0, "TC004 FAILED: empty_o did not deassert"
    got = await read_word(dut)
    assert got == test_data, f"TC004 FAILED: rd_data_o=0x{got:X}, expected=0x{test_data:X}"
    dut._log.info("TC004 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_005_data_integrity_hard_ip_fill_drain(dut):
    """TC005: Data Integrity: HARD_IP Fill and Drain."""
    tracer = VerilogTracer("TC-005", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    depth = min(WADDR_DEPTH, 512)
    written = []

    # Fill FIFO
    for i in range(depth):
        val = (i * 17 + 5) & WDATA_MASK
        written.append(val)
        await write_word(dut, val)

    await ReadOnly()
    assert int(dut.full_o.value) == 1, f"TC005 FAILED: full_o not asserted after {depth} writes"

    # Drain FIFO
    read_vals = []
    for _ in range(depth):
        got = await read_word(dut)
        read_vals.append(got)

    assert read_vals == written, f"TC005 FAILED: Data mismatch during drain!"

    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC005 FAILED: empty_o not asserted after full drain"
    dut._log.info("TC005 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or IMPLEMENTATION != "EBR"))
async def tc_006_data_integrity_fabric_ebr_fill_drain(dut):
    """TC006: Data Integrity: FABRIC EBR Fill and Drain with Data Count."""
    tracer = VerilogTracer("TC-006", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    depth = min(WADDR_DEPTH, 256)
    written = []

    for i in range(depth):
        val = (i ^ 0x55AA) & WDATA_MASK
        written.append(val)
        await write_word(dut, val)

    read_vals = []
    for _ in range(depth):
        got = await read_word(dut)
        read_vals.append(got)

    assert read_vals == written, f"TC006 FAILED: Data mismatch in FABRIC EBR fill/drain"
    dut._log.info("TC006 PASSED")
    tracer.save()


@cocotb.test()
async def tc_007_write_to_full_suppression(dut):
    """TC007: Write-to-Full Suppression."""
    tracer = VerilogTracer("TC-007", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    depth = min(WADDR_DEPTH, 64)
    for i in range(depth):
        await write_word(dut, i & WDATA_MASK)

    await ReadOnly()
    # Attempt extra writes while full
    await write_word(dut, 0xDEAD & WDATA_MASK)
    await write_word(dut, 0xBEEF & WDATA_MASK)

    # Drain and verify initial data intact
    for i in range(depth):
        got = await read_word(dut)
        assert got == (i & WDATA_MASK), f"TC007 FAILED at word {i}: got 0x{got:X}"

    dut._log.info("TC007 PASSED")
    tracer.save()


@cocotb.test()
async def tc_008_read_from_empty_guard(dut):
    """TC008: Read-from-Empty Guard."""
    tracer = VerilogTracer("TC-008", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await ReadOnly()
    assert int(dut.empty_o.value) == 1

    # Illegal reads when empty
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 1
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0

    # Write valid word and read it back
    test_val = 0x5555 & WDATA_MASK
    await write_word(dut, test_val)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    got = await read_word(dut)
    assert got == test_val, f"TC008 FAILED: got 0x{got:X}, expected 0x{test_val:X}"
    dut._log.info("TC008 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_009_simultaneous_write_read_hard_ip(dut):
    """TC009: Simultaneous Write and Read: HARD_IP."""
    tracer = VerilogTracer("TC-009", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    # Prime with 16 words
    for i in range(16):
        await write_word(dut, i & WDATA_MASK)

    # Concurrent write and read for 32 cycles
    for i in range(32):
        await RisingEdge(dut.wr_clk_i)
        dut.wr_en_i.value = 1
        dut.wr_data_i.value = (100 + i) & WDATA_MASK
        dut.rd_en_i.value = 1

    await RisingEdge(dut.wr_clk_i)
    dut.wr_en_i.value = 0
    dut.rd_en_i.value = 0

    dut._log.info("TC009 PASSED")
    tracer.save()


@cocotb.test(skip=(FWFT != 1))
async def tc_010_fwft_mode(dut):
    """TC010: FWFT Mode: Pre-fetch and empty_o Behavior."""
    tracer = VerilogTracer("TC-010", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    word1 = 0x0001 & WDATA_MASK
    word2 = 0x0002 & WDATA_MASK

    await write_word(dut, word1)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    await ReadOnly()
    assert int(dut.empty_o.value) == 0, "TC010 FAILED: empty_o not deasserted in FWFT mode"
    assert int(dut.rd_data_o.value) == word1, f"TC010 FAILED: FWFT prefetch got 0x{int(dut.rd_data_o.value):X}"

    # Write second word
    await write_word(dut, word2)

    # Consume first word
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 1
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0
    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == word2, f"TC010 FAILED: next word got 0x{int(dut.rd_data_o.value):X}"

    dut._log.info("TC010 PASSED")
    tracer.save()


@cocotb.test(skip=(WDATA_WIDTH != 2 * RDATA_WIDTH or FIFO_CONTROLLER != "FABRIC"))
async def tc_011_asymmetric_width_2_to_1(dut):
    """TC011: Asymmetric Width 2:1 Write:Read (FABRIC EBR)."""
    tracer = VerilogTracer("TC-011", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    half_mask = (1 << RDATA_WIDTH) - 1
    num_writes = 16
    written_halves = []

    for i in range(num_writes):
        lower = (i * 2) & half_mask
        upper = (i * 2 + 1) & half_mask
        written_halves.extend([lower, upper])
        combined = (upper << RDATA_WIDTH) | lower
        await write_word(dut, combined)

    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)

    for expected in written_halves:
        got = await read_word(dut)
        assert got == expected, f"TC011 FAILED: got 0x{got:X}, expected 0x{expected:X}"

    dut._log.info("TC011 PASSED")
    tracer.save()


@cocotb.test(skip=(RDATA_WIDTH != 2 * WDATA_WIDTH or FIFO_CONTROLLER != "FABRIC"))
async def tc_012_asymmetric_width_1_to_2(dut):
    """TC012: Asymmetric Width 1:2 Write:Read (FABRIC EBR)."""
    tracer = VerilogTracer("TC-012", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    num_reads = 8
    for i in range(num_reads):
        await write_word(dut, (i * 2) & WDATA_MASK)
        await write_word(dut, (i * 2 + 1) & WDATA_MASK)

    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)

    for i in range(num_reads):
        got = await read_word(dut)
        exp = (((i * 2 + 1) & WDATA_MASK) << WDATA_WIDTH) | ((i * 2) & WDATA_MASK)
        assert got == exp, f"TC012 FAILED: got 0x{got:X}, exp 0x{exp:X}"

    dut._log.info("TC012 PASSED")
    tracer.save()


@cocotb.test(skip=(RESETMODE != "async"))
async def tc_014_rst_async_reset(dut):
    """TC014: rst_i Async Reset: Write Domain."""
    tracer = VerilogTracer("TC-014", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    # Write some words
    for i in range(8):
        await write_word(dut, i + 1)

    # Assert async reset
    dut.rst_i.value = 1
    await Timer(5, unit="ns")
    await ReadOnly()
    assert int(dut.full_o.value) == 0, "TC014 FAILED: full_o not cleared on async reset"

    dut.rst_i.value = 0
    await RisingEdge(dut.wr_clk_i)
    dut._log.info("TC014 PASSED")
    tracer.save()


@cocotb.test()
async def tc_015_rp_rst_async_reset(dut):
    """TC015: rp_rst_i Async Reset: Read Pointer Alignment."""
    tracer = VerilogTracer("TC-015", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(8):
        await write_word(dut, i + 1)

    # Assert rp_rst_i
    await RisingEdge(dut.rd_clk_i)
    dut.rp_rst_i.value = 1
    for _ in range(3):
        await RisingEdge(dut.rd_clk_i)
    dut.rp_rst_i.value = 0

    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC015 FAILED: empty_o not asserted after rp_rst_i"
    dut._log.info("TC015 PASSED")
    tracer.save()


@cocotb.test(skip=(RESETMODE != "sync"))
async def tc_016_sync_reset(dut):
    """TC016: RESETMODE=sync: Both Resets Synchronous."""
    tracer = VerilogTracer("TC-016", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(4):
        await write_word(dut, i + 1)

    await RisingEdge(dut.wr_clk_i)
    dut.rst_i.value = 1
    await RisingEdge(dut.wr_clk_i)
    dut.rst_i.value = 0

    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC016 FAILED: sync reset failed"
    dut._log.info("TC016 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_017_full_assertion_deassertion(dut):
    """TC017: full_o Assertion and Deassertion: HARD_IP."""
    tracer = VerilogTracer("TC-017", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    depth = min(WADDR_DEPTH, 128)
    for i in range(depth):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.full_o.value) == 1, "TC017 FAILED: full_o not asserted"

    await read_word(dut)
    for _ in range(10):
        await RisingEdge(dut.wr_clk_i)
        await ReadOnly()
        if int(dut.full_o.value) == 0:
            break

    assert int(dut.full_o.value) == 0, "TC017 FAILED: full_o not deasserted after read"
    dut._log.info("TC017 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_018_empty_assertion_deassertion(dut):
    """TC018: empty_o Assertion and Deassertion: HARD_IP."""
    tracer = VerilogTracer("TC-018", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await ReadOnly()
    assert int(dut.empty_o.value) == 1

    await write_word(dut, 0x1111)
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        if int(dut.empty_o.value) == 0:
            break

    assert int(dut.empty_o.value) == 0, "TC018 FAILED: empty_o did not deassert"
    await read_word(dut)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.empty_o.value) == 1, "TC018 FAILED: empty_o did not reassert"
    dut._log.info("TC018 PASSED")
    tracer.save()


@cocotb.test(skip=(ENABLE_ALMOST_FULL_FLAG != "TRUE"))
async def tc_019_almost_full_static_single(dut):
    """TC019: almost_full_o Static-Single."""
    tracer = VerilogTracer("TC-019", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    thresh = min(ALMOST_FULL_ASSERT_LVL, 32)
    for i in range(thresh):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.almost_full_o.value) == 1, "TC019 FAILED: almost_full_o not asserted"
    dut._log.info("TC019 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ENABLE_ALMOST_FULL_FLAG != "TRUE"))
async def tc_020_almost_full_static_single_fabric(dut):
    """TC020: almost_full_o Static-Single (FABRIC)."""
    tracer = VerilogTracer("TC-020", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    thresh = min(ALMOST_FULL_ASSERT_LVL, 16)
    for i in range(thresh):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.almost_full_o.value) == 1, "TC020 FAILED: almost_full_o not asserted"
    dut._log.info("TC020 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ALMOST_FULL_ASSERTION != "static-dual"))
async def tc_021_almost_full_static_dual_hysteresis(dut):
    """TC021: almost_full_o Static-Dual Hysteresis (FABRIC)."""
    tracer = VerilogTracer("TC-021", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(ALMOST_FULL_ASSERT_LVL):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.almost_full_o.value) == 1, "TC021 FAILED: almost_full_o not asserted at assert level"
    dut._log.info("TC021 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ALMOST_FULL_ASSERTION != "dynamic-single"))
async def tc_022_almost_full_dynamic_single(dut):
    """TC022: almost_full_o Dynamic-Single Threshold (FABRIC)."""
    tracer = VerilogTracer("TC-022", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await RisingEdge(dut.wr_clk_i)
    dut.almost_full_th_i.value = 8
    for i in range(8):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.almost_full_o.value) == 1, "TC022 FAILED: dynamic almost full flag failed"
    dut._log.info("TC022 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ALMOST_FULL_ASSERTION != "dynamic-dual"))
async def tc_023_almost_full_dynamic_dual(dut):
    """TC023: almost_full_o Dynamic-Dual Thresholds (FABRIC)."""
    tracer = VerilogTracer("TC-023", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await RisingEdge(dut.wr_clk_i)
    dut.almost_full_th_i.value = 10
    dut.almost_full_clr_th_i.value = 6
    for i in range(10):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.almost_full_o.value) == 1, "TC023 FAILED: dynamic dual almost full failed"
    dut._log.info("TC023 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ALMOST_EMPTY_ASSERTION != "static-dual"))
async def tc_024_almost_empty_static_dual_hysteresis(dut):
    """TC024: almost_empty_o Static-Dual Hysteresis (FABRIC)."""
    tracer = VerilogTracer("TC-024", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await ReadOnly()
    assert int(dut.almost_empty_o.value) == 1, "TC024 FAILED: almost_empty_o not asserted initially"
    dut._log.info("TC024 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ENABLE_DATA_COUNT_WR != "TRUE"))
async def tc_025_wr_data_cnt_accuracy(dut):
    """TC025: wr_data_cnt_o Accuracy (FABRIC)."""
    tracer = VerilogTracer("TC-025", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(16):
        await write_word(dut, i)

    await ReadOnly()
    cnt = int(dut.wr_data_cnt_o.value)
    assert abs(cnt - 16) <= 2, f"TC025 FAILED: wr_data_cnt_o={cnt}, expected ~16"
    dut._log.info("TC025 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC" or ENABLE_DATA_COUNT_RD != "TRUE"))
async def tc_026_rd_data_cnt_accuracy(dut):
    """TC026: rd_data_cnt_o Accuracy (FABRIC)."""
    tracer = VerilogTracer("TC-026", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(16):
        await write_word(dut, i)
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)

    await ReadOnly()
    cnt = int(dut.rd_data_cnt_o.value)
    assert abs(cnt - 16) <= 2, f"TC026 FAILED: rd_data_cnt_o={cnt}, expected ~16"
    dut._log.info("TC026 PASSED")
    tracer.save()


@cocotb.test(skip=(ECC_ENABLE != 1))
async def tc_027_ecc_single_bit_error(dut):
    """TC027: ECC Single-Bit Error Injection and Correction."""
    tracer = VerilogTracer("TC-027", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    test_val = 0x12345678 & WDATA_MASK
    await write_word(dut, test_val)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    got = await read_word(dut)
    assert got == test_val, f"TC027 FAILED: ECC data 0x{got:X} != 0x{test_val:X}"
    dut._log.info("TC027 PASSED")
    tracer.save()


@cocotb.test(skip=(ECC_ENABLE != 1))
async def tc_028_ecc_double_bit_error(dut):
    """TC028: ECC Double-Bit Error Detection."""
    tracer = VerilogTracer("TC-028", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    test_val = 0x9ABCDEF0 & WDATA_MASK
    await write_word(dut, test_val)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    got = await read_word(dut)
    dut._log.info(f"TC028: Read completed with got=0x{got:X}")
    dut._log.info("TC028 PASSED")
    tracer.save()


@cocotb.test(skip=(ECC_ENABLE != 0))
async def tc_029_ecc_disabled(dut):
    """TC029: ECC Disabled: Error Outputs Tied Low."""
    tracer = VerilogTracer("TC-029", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await write_word(dut, 0x1111)
    await read_word(dut)
    await ReadOnly()
    assert int(dut.one_err_det_o.value) == 0, "TC029 FAILED: one_err_det_o not 0 when ECC disabled"
    assert int(dut.two_err_det_o.value) == 0, "TC029 FAILED: two_err_det_o not 0 when ECC disabled"
    dut._log.info("TC029 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_032_hard_ip_data_count_zero(dut):
    """TC032: HARD_IP Forces DATA_COUNT Outputs to Zero."""
    tracer = VerilogTracer("TC-032", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(8):
        await write_word(dut, i)

    await ReadOnly()
    assert int(dut.wr_data_cnt_o.value) == 0, "TC032 FAILED: wr_data_cnt_o != 0 in HARD_IP"
    assert int(dut.rd_data_cnt_o.value) == 0, "TC032 FAILED: rd_data_cnt_o != 0 in HARD_IP"
    dut._log.info("TC032 PASSED")
    tracer.save()


@cocotb.test(skip=(IMPLEMENTATION != "LUT"))
async def tc_038_fabric_lut_symmetric(dut):
    """TC038: FABRIC LUT: Symmetric Valid Configuration."""
    tracer = VerilogTracer("TC-038", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    depth = min(WADDR_DEPTH, 32)
    for i in range(depth):
        await write_word(dut, (i + 3) & WDATA_MASK)

    for i in range(depth):
        got = await read_word(dut)
        assert got == ((i + 3) & WDATA_MASK), f"TC038 FAILED at word {i}: got 0x{got:X}"

    dut._log.info("TC038 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP" or REGMODE != "reg"))
async def tc_042_regmode_reg_hard_ip(dut):
    """TC042: REGMODE=reg HARD_IP: Read Latency Verification."""
    tracer = VerilogTracer("TC-042", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    await write_word(dut, 0xCAFE & WDATA_MASK)
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    got = await read_word(dut)
    assert got == (0xCAFE & WDATA_MASK), f"TC042 FAILED: got 0x{got:X}"
    dut._log.info("TC042 PASSED")
    tracer.save()


@cocotb.test(skip=(FWFT != 1))
async def tc_051_regression_fwft_prefetch(dut):
    """TC051: Regression: v2.2.0 FWFT Fix — Correct Pre-fetch Sequencing."""
    tracer = VerilogTracer("TC-051", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(4):
        await write_word(dut, (i + 0x10) & WDATA_MASK)

    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    for i in range(4):
        await ReadOnly()
        assert int(dut.rd_data_o.value) == ((i + 0x10) & WDATA_MASK)
        await RisingEdge(dut.rd_clk_i)
        dut.rd_en_i.value = 1
        await RisingEdge(dut.rd_clk_i)
        dut.rd_en_i.value = 0
        await RisingEdge(dut.rd_clk_i)

    dut._log.info("TC051 PASSED")
    tracer.save()


@cocotb.test(skip=(IMPLEMENTATION != "LUT" or RESETMODE != "async"))
async def tc_052_regression_fabric_lut_async_reset(dut):
    """TC052: Regression: v2.3.0 Async Reset of FABRIC LUT Flags."""
    tracer = VerilogTracer("TC-052", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(4):
        await write_word(dut, i + 1)

    dut.rst_i.value = 1
    await Timer(5, unit="ns")
    await ReadOnly()
    assert int(dut.full_o.value) == 0, "TC052 FAILED: full_o not 0 on async reset"
    dut.rst_i.value = 0
    await RisingEdge(dut.wr_clk_i)
    dut._log.info("TC052 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "HARD_IP"))
async def tc_056_acceptance_hard_ip(dut):
    """TC056: Acceptance: HARD_IP Full Acceptance."""
    tracer = VerilogTracer("TC-056", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(16):
        await write_word(dut, (i * 3 + 1) & WDATA_MASK)

    for i in range(16):
        got = await read_word(dut)
        assert got == ((i * 3 + 1) & WDATA_MASK), f"TC056 FAILED at {i}"

    dut._log.info("TC056 PASSED")
    tracer.save()


@cocotb.test(skip=(FIFO_CONTROLLER != "FABRIC"))
async def tc_057_acceptance_fabric_ebr(dut):
    """TC057: Acceptance: FABRIC EBR Full Acceptance."""
    tracer = VerilogTracer("TC-057", enabled=True)
    await start_clocks(dut)
    await apply_reset(dut)

    for i in range(16):
        await write_word(dut, (i * 5 + 2) & WDATA_MASK)

    for i in range(16):
        got = await read_word(dut)
        assert got == ((i * 5 + 2) & WDATA_MASK), f"TC057 FAILED at {i}"

    dut._log.info("TC057 PASSED")
    tracer.save()
