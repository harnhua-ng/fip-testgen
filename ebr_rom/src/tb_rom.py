"""
tb_rom.py  —  CoCoTB testbench for lscc_rom (LIFCL)
Spec ref  : ROM_FunctionalSpec.md (v2.5.0, 2026-08-20)
Test plan : ROM_TestPlan_LIFCL.md (2026-08-27)

Test Groups & Cases:
  G1 · Baseline:
    TC-ROM-001: Default configuration generation and read (Both)
  G2 · RADDR_DEPTH — Address Depth:
    TC-ROM-002: Minimum address depth (Radiant Compilation)
    TC-ROM-003: Median address depth, full-range read (Sim Only)
    TC-ROM-004: Maximum address depth (Radiant Compilation)
    TC-ROM-005: Address depth at the exact LIFCL budget (Radiant Compilation)
    TC-ROM-006: Non-power-of-two address depth (Radiant Compilation)
  G3 · RDATA_WIDTH — Data Width:
    TC-ROM-007: Minimum data width (Both)
    TC-ROM-008: Median data width, every bit position (Sim Only)
    TC-ROM-009: Maximum data width with data-axis tiling (Both)
    TC-ROM-010: Data width 36 selects the wide LIFCL branch (Radiant Compilation)
  G4 · REGMODE — Output Register:
    TC-ROM-011: Output register enabled — two-cycle latency (Sim Only)
    TC-ROM-012: Output register disabled — one-cycle latency (Both)
  G5 · RESETMODE — Reset Assertion:
    TC-ROM-013: Synchronous reset of the output register (Both)
    TC-ROM-014: Asynchronous reset assertion (Radiant Compilation)
  G6 · INIT_FILE_FORMAT — Memory File Format:
    TC-ROM-015: Binary-format initialization (Both)
    TC-ROM-016: Hexadecimal-format initialization (Both)
  G7 · OUTPUT_CLK_EN — Output Register Clock Enable:
    TC-ROM-017: Output-register clock enable not requested (Radiant Compilation)
    TC-ROM-018: Output-register clock enable requested (Both)
  G8 · user_init_file — Memory File:
    TC-ROM-019: Comments, @address records and surplus words (Both)
  G9 · Cross-Parameter Legal Combinations:
    TC-ROM-020: Maximum depth, output register, separate enable, hex (Sim Only)
    TC-ROM-021: Maximum width, output register bypassed, hex (Both)
    TC-ROM-022: At-budget dimensions, separate enable, async reset (Radiant Compilation)
    TC-ROM-023: Minimum dimensions, output register bypassed (Both)
  G10 · Port Behaviour:
    TC-ROM-024: rd_clk_en_i freezes the memory array (Sim Only)
    TC-ROM-025: rd_out_clk_en_i freezes the output register (Sim Only)
    TC-ROM-026: rd_en_i as a second series enable (Sim Only)
    TC-ROM-027: rd_en_i ignored without the separate enable (Sim Only)
    TC-ROM-028: rst_i inert with the output register bypassed (Sim Only)
    TC-ROM-029: rd_addr_i above the configured depth (Sim Only)
    TC-ROM-030: ECC status outputs inert and dangling (Both)
  G11 · DRC and Radiant Compilation Checks:
    TC-ROM-031: Memory Initialization read-only; fill options unreachable
    TC-ROM-032: Initialization-data update control hidden on LIFCL
    TC-ROM-033: Derived read-only settings
    TC-ROM-034: Default-parameter compilation smoke test
"""

import os
import re
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer
from verilog_tracer import VerilogTracer

# ── Simulation parameters (set via env vars) ───────────────────────────────────
RDATA_WIDTH      = int(os.getenv("RDATA_WIDTH",      "18"))
RADDR_DEPTH      = int(os.getenv("RADDR_DEPTH",      "1024"))
REGMODE          =     os.getenv("REGMODE",          "reg")
RESETMODE        =     os.getenv("RESETMODE",        "sync")
OUTPUT_CLK_EN    = int(os.getenv("OUTPUT_CLK_EN",    "0"))
ECC_ENABLE       = int(os.getenv("ECC_ENABLE",       "0"))
INIT_MODE        =     os.getenv("INIT_MODE",        "mem_file")
INIT_FILE        =     os.getenv("INIT_FILE",        "")
INIT_FILE_FORMAT =     os.getenv("INIT_FILE_FORMAT", "binary")
FAMILY           =     os.getenv("FAMILY",           "LIFCL")

CLK_NS   = 10    # 100 MHz clock
RST_NS   = 100   # 10 cycles reset

# Pipeline latency: 1 cycle for noreg, 2 cycles for reg
LAT = 1 if REGMODE == "noreg" else 2

DATA_MASK = (1 << RDATA_WIDTH) - 1


# ── Reference model ───────────────────────────────────────────────────────────
def _make_ref():
    """Build the expected reference memory array according to spec 1.5.3."""
    if INIT_MODE == "all_one":
        return [DATA_MASK] * RADDR_DEPTH
    if INIT_MODE == "all_zero" or INIT_MODE == "none":
        return [0] * RADDR_DEPTH

    path = INIT_FILE
    if not path or not os.path.isfile(path):
        # Default file fallbacks based on depth, width, and format
        candidate_names = [
            f"rom_{RADDR_DEPTH}x{RDATA_WIDTH}.{ 'hex' if INIT_FILE_FORMAT == 'hex' else 'bin' }",
            f"rom_init_{RDATA_WIDTH}_{RADDR_DEPTH}.{ 'hex' if INIT_FILE_FORMAT == 'hex' else 'bin' }",
            "rom_1024x18.bin",
            "rom_init.hex"
        ]
        for name in candidate_names:
            cpath = os.path.join(os.path.dirname(__file__), "..", "testbench", name)
            if os.path.isfile(cpath):
                path = cpath
                break

    if path and os.path.isfile(path):
        mem = [0] * RADDR_DEPTH
        base = 16 if INIT_FILE_FORMAT == "hex" else 2
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        # Strip block comments /* ... */
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        cur_addr = 0
        for line in content.splitlines():
            line = line.split("//")[0].strip()
            if not line:
                continue
            if line.startswith("@"):
                parts = line[1:].strip().split()
                if parts:
                    cur_addr = int(parts[0], 16)
                    tokens = parts[1:]
                else:
                    tokens = []
            else:
                tokens = line.split()

            for tok in tokens:
                try:
                    val = int(tok, base) & DATA_MASK
                    if cur_addr < RADDR_DEPTH:
                        mem[cur_addr] = val
                    cur_addr += 1
                except ValueError:
                    continue
        return mem

    return [0] * RADDR_DEPTH


REF = _make_ref()


# ── Shared Testbench Helpers ──────────────────────────────────────────────────
async def do_reset(dut, tracer: VerilogTracer = None):
    """Assert rst_i for RST_NS with all enables low, then release and sync to clock."""
    if tracer:
        tracer.comment("Reset sequence")
        tracer.assign("rst_i", 1)
        tracer.assign("rd_en_i", 0)
        tracer.assign("rd_clk_en_i", 0)
        tracer.assign("rd_out_clk_en_i", 0)
        tracer.assign("rd_addr_i", 0, width=max(1, (RADDR_DEPTH - 1).bit_length()))
        tracer.delay_ns(RST_NS)
        tracer.assign("rst_i", 0)
        tracer.clock_edge("rd_clk_i")

    dut.rst_i.value           = 1
    dut.rd_en_i.value         = 0
    dut.rd_clk_en_i.value     = 0
    dut.rd_out_clk_en_i.value = 0
    dut.rd_addr_i.value       = 0
    await Timer(RST_NS, unit="ns")
    dut.rst_i.value = 0
    await RisingEdge(dut.rd_clk_i)


async def single_read(dut, addr, tracer: VerilogTracer = None):
    """Drive addr after current clock edge, wait LAT cycles, return rd_data_o."""
    raddr_w = max(1, (RADDR_DEPTH - 1).bit_length())
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = addr
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", addr, width=raddr_w)
    for _ in range(LAT):
        await RisingEdge(dut.rd_clk_i)
        if tracer:
            tracer.clock_edge("rd_clk_i")
    await ReadOnly()
    val = dut.rd_data_o.value
    return int(val) if val.is_resolvable else 0


# ==============================================================================
# G1 · Baseline
# ==============================================================================

@cocotb.test()
async def tc_rom_001_default_config_read(dut):
    """TC-ROM-001: Default configuration generation and read (RADDR_DEPTH=1024, RDATA_WIDTH=18, REGMODE=reg)."""
    tracer = VerilogTracer("TC-ROM-001")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())

    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 2, 511, min(1023, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-001] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"

    tracer.save()


# ==============================================================================
# G2 · RADDR_DEPTH — Address Depth
# ==============================================================================

@cocotb.test()
async def tc_rom_002_minimum_address_depth(dut):
    """TC-ROM-002: Minimum address depth (RADDR_DEPTH=2, RDATA_WIDTH=1)."""
    tracer = VerilogTracer("TC-ROM-002")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(min(2, RADDR_DEPTH)):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-002] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_003_median_address_depth_full_range(dut):
    """TC-ROM-003: Median address depth, full-range read (RADDR_DEPTH=1024, RDATA_WIDTH=18)."""
    tracer = VerilogTracer("TC-ROM-003")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(RADDR_DEPTH):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-003] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_004_maximum_address_depth(dut):
    """TC-ROM-004: Maximum address depth (RADDR_DEPTH=65536, RDATA_WIDTH=18)."""
    tracer = VerilogTracer("TC-ROM-004")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 511, 1023, 1024, 4095, 4096, min(65535, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-004] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_005_address_depth_at_budget(dut):
    """TC-ROM-005: Address depth at exact LIFCL budget (RADDR_DEPTH=3024, RDATA_WIDTH=512)."""
    tracer = VerilogTracer("TC-ROM-005")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 1023, 1024, 2047, min(3023, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-005] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_006_non_power_of_two_depth(dut):
    """TC-ROM-006: Non-power-of-two address depth (RADDR_DEPTH=1000, RDATA_WIDTH=8)."""
    tracer = VerilogTracer("TC-ROM-006")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 500, min(999, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-006] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


# ==============================================================================
# G3 · RDATA_WIDTH — Data Width
# ==============================================================================

@cocotb.test()
async def tc_rom_007_minimum_data_width(dut):
    """TC-ROM-007: Minimum data width (RADDR_DEPTH=1024, RDATA_WIDTH=1)."""
    tracer = VerilogTracer("TC-ROM-007")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    check_addrs = list(range(8)) + [1020, 1021, 1022, min(1023, RADDR_DEPTH - 1)]
    for addr in check_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-007] addr={addr}: got={got} exp={exp}"
    tracer.save()


@cocotb.test()
async def tc_rom_008_median_data_width_walk_pattern(dut):
    """TC-ROM-008: Median data width, every bit position (RADDR_DEPTH=1024, RDATA_WIDTH=18)."""
    tracer = VerilogTracer("TC-ROM-008")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    ones_seen = [0] * RDATA_WIDTH
    zeros_seen = [0] * RDATA_WIDTH

    for addr in range(min(36, RADDR_DEPTH)):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-008] addr={addr}: got=0x{got:05X} exp=0x{exp:05X}"
        for bit in range(RDATA_WIDTH):
            if (got >> bit) & 1:
                ones_seen[bit] += 1
            else:
                zeros_seen[bit] += 1

    for bit in range(RDATA_WIDTH):
        assert ones_seen[bit] > 0, f"[TC-ROM-008] Bit {bit} never observed high"
        assert zeros_seen[bit] > 0, f"[TC-ROM-008] Bit {bit} never observed low"
    tracer.save()


@cocotb.test()
async def tc_rom_009_maximum_data_width_tiling(dut):
    """TC-ROM-009: Maximum data width with data-axis tiling (RADDR_DEPTH=2048, RDATA_WIDTH=512)."""
    tracer = VerilogTracer("TC-ROM-009")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 1023, 1024, min(2047, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-009] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_010_data_width_36_wide_branch(dut):
    """TC-ROM-010: Data width 36 selects wide LIFCL branch (RADDR_DEPTH=512, RDATA_WIDTH=36)."""
    tracer = VerilogTracer("TC-ROM-010")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    test_addrs = [0, 1, 255, min(511, RADDR_DEPTH - 1)]
    for addr in test_addrs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-010] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


# ==============================================================================
# G4 · REGMODE — Output Register
# ==============================================================================

@cocotb.test()
async def tc_rom_011_output_register_enabled_latency(dut):
    """TC-ROM-011: Output register enabled — two-cycle latency (REGMODE=reg)."""
    tracer = VerilogTracer("TC-ROM-011")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Sequential presentation on 3 successive cycles
    a0, a1, a2 = 10, 20, 30
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a0, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a1, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a2
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a2, width=10)

    # Cycle 2 after A0: A0 arrives
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a0], f"A0 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a0]}"

    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a1], f"A1 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a1]}"

    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a2], f"A2 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a2]}"

    # When OUTPUT_CLK_EN=0, driving rd_out_clk_en_i low must have no effect
    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 0
    dut.rd_addr_i.value = 40
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_out_clk_en_i", 0)
        tracer.assign("rd_addr_i", 40, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = 50
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", 50, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_out_clk_en_i", 1)

    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[40], f"OUTPUT_CLK_EN=0 gating check failed: got {int(dut.rd_data_o.value)} exp {REF[40]}"

    tracer.save()


@cocotb.test()
async def tc_rom_012_output_register_disabled_latency(dut):
    """TC-ROM-012: Output register disabled — one-cycle latency (REGMODE=noreg)."""
    tracer = VerilogTracer("TC-ROM-012")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    a0, a1, a2 = 10, 20, 30
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a0, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a1, width=10)
    # 1-cycle latency: A0 arrives in the cycle immediately after capture
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a0], f"A0 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a0]}"

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a2
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", a2, width=10)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a1], f"A1 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a1]}"

    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a2], f"A2 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a2]}"

    # In noreg mode, holding rd_out_clk_en_i or rd_en_i low has no effect
    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 0
    dut.rd_en_i.value = 0
    dut.rd_addr_i.value = 40
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_out_clk_en_i", 0)
        tracer.assign("rd_en_i", 0)
        tracer.assign("rd_addr_i", 40, width=10)

    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[40], f"Addr 40 mismatch in noreg with enables low: got {int(dut.rd_data_o.value)} exp {REF[40]}"

    tracer.save()


# ==============================================================================
# G5 · RESETMODE — Reset Assertion
# ==============================================================================

@cocotb.test()
async def tc_rom_013_sync_reset_output_register(dut):
    """TC-ROM-013: Synchronous reset of the output register (RESETMODE=sync, OUTPUT_CLK_EN=1)."""
    tracer = VerilogTracer("TC-ROM-013")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Mid-sweep reset
    for addr in range(10):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)

    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 1)
    for _ in range(3):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        assert int(dut.rd_data_o.value) == 0, f"Expected rd_data_o=0 during sync reset, got {int(dut.rd_data_o.value)}"

    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 0)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == 0, f"Expected rd_data_o=0 cycle after reset release, got {int(dut.rd_data_o.value)}"

    # Continue sweep after release
    for addr in range(20, 30):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"Post-reset read addr={addr}: got {got} exp {exp}"

    # Reset dominance over enables
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value     = 0
    dut.rd_en_i.value         = 0
    dut.rd_out_clk_en_i.value = 0
    dut.rst_i.value           = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_clk_en_i", 0)
        tracer.assign("rd_en_i", 0)
        tracer.assign("rd_out_clk_en_i", 0)
        tracer.assign("rst_i", 1)
    for _ in range(3):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        assert int(dut.rd_data_o.value) == 0, "Reset did not dominate with enables de-asserted"

    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 0)
    tracer.save()


@cocotb.test()
async def tc_rom_014_async_reset_assertion(dut):
    """TC-ROM-014: Asynchronous reset assertion (RESETMODE=async)."""
    tracer = VerilogTracer("TC-ROM-014")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    got = await single_read(dut, 10, tracer)
    exp = REF[10]
    assert got == exp, f"Pre-reset read failed: got {got} exp {exp}"

    # Asynchronous reset assertion (leave ReadOnly phase)
    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 1)
    await Timer(1, unit="ns")
    await ReadOnly()
    assert int(dut.rd_data_o.value) == 0, f"Async reset did not clear rd_data_o immediately, got {int(dut.rd_data_o.value)}"

    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 0)
    await RisingEdge(dut.rd_clk_i)

    got = await single_read(dut, 20, tracer)
    exp = REF[20]
    assert got == exp, f"Post-reset read failed: got {got} exp {exp}"
    tracer.save()


# ==============================================================================
# G6 · INIT_FILE_FORMAT — Memory File Format
# ==============================================================================

@cocotb.test()
async def tc_rom_015_binary_format_initialization(dut):
    """TC-ROM-015: Binary-format initialization (INIT_FILE_FORMAT=binary)."""
    tracer = VerilogTracer("TC-ROM-015")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(RADDR_DEPTH):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-015] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_016_hex_format_initialization(dut):
    """TC-ROM-016: Hexadecimal-format initialization (INIT_FILE_FORMAT=hex)."""
    tracer = VerilogTracer("TC-ROM-016")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(RADDR_DEPTH):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-016] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


# ==============================================================================
# G7 · OUTPUT_CLK_EN — Output Register Clock Enable
# ==============================================================================

@cocotb.test()
async def tc_rom_017_output_clk_en_not_requested(dut):
    """TC-ROM-017: Output-register clock enable not requested (OUTPUT_CLK_EN=0)."""
    tracer = VerilogTracer("TC-ROM-017")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 0  # Should have no effect

    for addr in [0, 1, 2, 511, min(1023, RADDR_DEPTH - 1)]:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-017] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_018_output_clk_en_requested(dut):
    """TC-ROM-018: Output-register clock enable requested (OUTPUT_CLK_EN=1)."""
    tracer = VerilogTracer("TC-ROM-018")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    a0, a1, a2 = 5, 6, 7
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a0
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a1
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = a2
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a0], f"A0 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a0]}"
    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a1], f"A1 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a1]}"
    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    assert int(dut.rd_data_o.value) == REF[a2], f"A2 mismatch: got {int(dut.rd_data_o.value)} exp {REF[a2]}"
    tracer.save()


# ==============================================================================
# G8 · user_init_file — Memory File
# ==============================================================================

@cocotb.test()
async def tc_rom_019_comments_at_address_surplus(dut):
    """TC-ROM-019: Comments, @address records and surplus words (rom_sparse.hex)."""
    tracer = VerilogTracer("TC-ROM-019")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    check_locs = [0, 0x010, 0x011, 0x0FF, 0x100, 0x101, min(1023, RADDR_DEPTH - 1)]
    for addr in check_locs:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-019] addr=0x{addr:X}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


# ==============================================================================
# G9 · Cross-Parameter Legal Combinations
# ==============================================================================

@cocotb.test()
async def tc_rom_020_max_depth_separate_enable_hex(dut):
    """TC-ROM-020: Maximum depth, output register, separate enable, hex (RADDR_DEPTH=65536, OUTPUT_CLK_EN=1)."""
    tracer = VerilogTracer("TC-ROM-020")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Sweep across block boundary
    for addr in [511, 512, 1023, 1024]:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"addr={addr}: got {got} exp {exp}"

    # Freeze rd_clk_en_i low across boundary
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = 2048
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value = 0
    for _ in range(3):
        await RisingEdge(dut.rd_clk_i)

    dut.rd_clk_en_i.value = 1
    got = await single_read(dut, 2049, tracer)
    assert got == REF[2049], f"Post-freeze read mismatch: got {got} exp {REF[2049]}"
    tracer.save()


@cocotb.test()
async def tc_rom_021_max_width_noreg_hex(dut):
    """TC-ROM-021: Maximum width, output register bypassed, hex (RADDR_DEPTH=2048, RDATA_WIDTH=512, REGMODE=noreg)."""
    tracer = VerilogTracer("TC-ROM-021")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in [0, 1, 1023, 1024, min(2047, RADDR_DEPTH - 1)]:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-021] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_022_at_budget_separate_enable_async_reset(dut):
    """TC-ROM-022: At-budget dimensions, separate enable, async reset (RADDR_DEPTH=3024, RDATA_WIDTH=512)."""
    tracer = VerilogTracer("TC-ROM-022")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in [0, 1, 1000, min(3023, RADDR_DEPTH - 1)]:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-022] addr={addr}: got=0x{got:X} exp=0x{exp:X}"
    tracer.save()


@cocotb.test()
async def tc_rom_023_min_dimensions_noreg(dut):
    """TC-ROM-023: Minimum dimensions, output register bypassed (RADDR_DEPTH=2, RDATA_WIDTH=1, REGMODE=noreg)."""
    tracer = VerilogTracer("TC-ROM-023")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in [0, 1, 0]:
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"[TC-ROM-023] addr={addr}: got={got} exp={exp}"
    tracer.save()


# ==============================================================================
# G10 · Port Behaviour
# ==============================================================================

@cocotb.test()
async def tc_rom_024_rd_clk_en_freezes_memory_array(dut):
    """TC-ROM-024: rd_clk_en_i freezes the memory array."""
    tracer = VerilogTracer("TC-ROM-024")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Active reads for 4 cycles
    for addr in range(4):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)

    # Freeze rd_clk_en_i low for 3 cycles while address keeps changing
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_clk_en_i", 0)

    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = 100
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_addr_i", 100, width=10)
    await ReadOnly()
    frozen_val = int(dut.rd_data_o.value)

    for addr in range(101, 104):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)
        await ReadOnly()
        assert int(dut.rd_data_o.value) == frozen_val, f"rd_data_o changed while rd_clk_en_i was low: got {int(dut.rd_data_o.value)} exp {frozen_val}"

    # Resume
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_clk_en_i", 1)
    for addr in range(10, 15):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"Post-freeze read addr={addr}: got {got} exp {exp}"
    tracer.save()


@cocotb.test()
async def tc_rom_025_rd_out_clk_en_freezes_output_register(dut):
    """TC-ROM-025: rd_out_clk_en_i freezes the output register."""
    tracer = VerilogTracer("TC-ROM-025")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(3):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)

    # Freeze rd_out_clk_en_i low for 2 cycles
    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_out_clk_en_i", 0)
    await ReadOnly()
    frozen_val = int(dut.rd_data_o.value)

    for _ in range(2):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        assert int(dut.rd_data_o.value) == frozen_val, "rd_data_o changed while rd_out_clk_en_i was low"

    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_out_clk_en_i", 1)
    await RisingEdge(dut.rd_clk_i)
    tracer.save()


@cocotb.test()
async def tc_rom_026_rd_en_as_second_series_enable(dut):
    """TC-ROM-026: rd_en_i as a second series enable."""
    tracer = VerilogTracer("TC-ROM-026")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(4):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)

    # rd_en_i low for 2 cycles
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_en_i", 0)

    for _ in range(2):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        assert dut.rd_data_o.value.is_resolvable

    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_en_i", 1)
    await RisingEdge(dut.rd_clk_i)
    tracer.save()


@cocotb.test()
async def tc_rom_027_rd_en_ignored_without_separate_enable(dut):
    """TC-ROM-027: rd_en_i ignored without the separate enable (OUTPUT_CLK_EN=0)."""
    tracer = VerilogTracer("TC-ROM-027")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Drive rd_en_i low for 4 cycles, verify reads continue unaffected
    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_en_i", 0)
    for addr in range(4):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"addr={addr} read with rd_en_i=0 failed: got {got} exp {exp}"

    await RisingEdge(dut.rd_clk_i)
    dut.rd_en_i.value = 1
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rd_en_i", 1)
    for addr in range(4, 8):
        got = await single_read(dut, addr, tracer)
        exp = REF[addr]
        assert got == exp, f"addr={addr} read with rd_en_i=1 failed: got {got} exp {exp}"

    tracer.save()


@cocotb.test()
async def tc_rom_028_rst_inert_with_output_register_bypassed(dut):
    """TC-ROM-028: rst_i inert with the output register bypassed (REGMODE=noreg)."""
    tracer = VerilogTracer("TC-ROM-028")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(10):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        if tracer:
            tracer.clock_edge("rd_clk_i")
            tracer.assign("rd_addr_i", addr, width=10)
        if addr == 4:
            dut.rst_i.value = 1
            if tracer:
                tracer.assign("rst_i", 1)
        elif addr == 7:
            dut.rst_i.value = 0
            if tracer:
                tracer.assign("rst_i", 0)
        await ReadOnly()
        if addr >= 1:
            exp = REF[addr - 1]
            got = int(dut.rd_data_o.value)
            assert got == exp, f"noreg read during rst_i window failed at addr={addr-1}: got {got} exp {exp}"

    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0
    if tracer:
        tracer.clock_edge("rd_clk_i")
        tracer.assign("rst_i", 0)
    tracer.save()


@cocotb.test()
async def tc_rom_029_rd_addr_above_configured_depth(dut):
    """TC-ROM-029: rd_addr_i above the configured depth (RADDR_DEPTH=1000)."""
    tracer = VerilogTracer("TC-ROM-029")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    # Read 999, then 1000, then 1023, then 999, then 0
    test_sequence = [999, 1000, 1023, 999, 0]
    for addr in test_sequence:
        got = await single_read(dut, addr, tracer)
        if addr in (999, 0):
            exp = REF[addr]
            assert got == exp, f"addr={addr}: got=0x{got:X} exp=0x{exp:X}"

    tracer.save()


@cocotb.test()
async def tc_rom_030_ecc_outputs_inert_and_dangling(dut):
    """TC-ROM-030: ECC status outputs inert and dangling (constant 0)."""
    tracer = VerilogTracer("TC-ROM-030")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)

    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    for addr in range(64):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr % RADDR_DEPTH
        await ReadOnly()
        one_err = int(dut.one_err_det_o.value) if dut.one_err_det_o.value.is_resolvable else 0
        two_err = int(dut.two_err_det_o.value) if dut.two_err_det_o.value.is_resolvable else 0
        assert one_err == 0, f"one_err_det_o was non-zero at cycle {addr}: {one_err}"
        assert two_err == 0, f"two_err_det_o was non-zero at cycle {addr}: {two_err}"

    tracer.save()


# ==============================================================================
# G11 · DRC & Radiant Smoke Tests (Sim wrapper stubs)
# ==============================================================================

@cocotb.test()
async def tc_rom_031_memory_init_readonly_fill_unreachable(dut):
    """TC-ROM-031: Memory Initialization read-only; fill options unreachable."""
    tracer = VerilogTracer("TC-ROM-031")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)
    dut.rd_en_i.value = 1; dut.rd_clk_en_i.value = 1; dut.rd_out_clk_en_i.value = 1
    got = await single_read(dut, 0, tracer)
    assert got == REF[0]
    tracer.save()

@cocotb.test()
async def tc_rom_032_init_data_update_control_hidden(dut):
    """TC-ROM-032: Initialization-data update control hidden on LIFCL."""
    tracer = VerilogTracer("TC-ROM-032")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)
    dut.rd_en_i.value = 1; dut.rd_clk_en_i.value = 1; dut.rd_out_clk_en_i.value = 1
    got = await single_read(dut, 0, tracer)
    assert got == REF[0]
    tracer.save()

@cocotb.test()
async def tc_rom_033_derived_readonly_settings(dut):
    """TC-ROM-033: Derived read-only settings."""
    tracer = VerilogTracer("TC-ROM-033")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)
    dut.rd_en_i.value = 1; dut.rd_clk_en_i.value = 1; dut.rd_out_clk_en_i.value = 1
    got = await single_read(dut, 0, tracer)
    assert got == REF[0]
    tracer.save()

@cocotb.test()
async def tc_rom_034_default_param_smoke_test(dut):
    """TC-ROM-034: Default-parameter compilation smoke test."""
    tracer = VerilogTracer("TC-ROM-034")
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)
    dut.rd_en_i.value = 1; dut.rd_clk_en_i.value = 1; dut.rd_out_clk_en_i.value = 1
    got = await single_read(dut, 0, tracer)
    assert got == REF[0]
    tracer.save()
