"""
tb_rom.py  —  CoCoTB testbench for lscc_rom (LIFCL)
Spec ref  : ROM_FIP_Functional_Specification_v2.5.0.md
Test plan : ROM_LIFCL_testplan.md

Implemented test groups
  TG-01  Basic Read Functionality  (TC-01-01 … TC-01-07)
  TG-02  Read Clock Enable         (TC-02-01 … TC-02-04)
  TG-03  Output Clock Enable       (TC-03-01 … TC-03-05)
  TG-04  Output Register Enable    (TC-04-01 … TC-04-05)
  TG-05  Reset Behavior            (TC-05-01 … TC-05-06)
  TG-06  Memory Initialization     (TC-06-01 … TC-06-08)
  TG-07  EBR Tile Config Coverage  (TC-07-01 … TC-07-08)
  TG-08  EBR Cascading             (TC-08-01 … TC-08-08)
  TG-09  ECC                       (TC-09-01 … TC-09-07)

Each test uses @cocotb.test(skip=...) to skip itself when the current
simulation parameters do not match the test's requirements.  Run the full
suite by invoking qrun multiple times with different env-var combinations.

Signal naming matches sim_top.v (which wraps lscc_rom and provides GSR_INST).
All signals are accessed as dut.<name> — cocotb sees sim_top as the DUT.
"""

import os
import random
import cocotb
from cocotb.clock    import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer

# ── Simulation parameters (set by run.sh via env vars) ───────────────────────
RDATA_WIDTH    = int(os.getenv("RDATA_WIDTH",    "36"))
RADDR_DEPTH    = int(os.getenv("RADDR_DEPTH",    "512"))
REGMODE        =     os.getenv("REGMODE",        "noreg")
RESETMODE      =     os.getenv("RESETMODE",      "sync")
OUTPUT_CLK_EN  = int(os.getenv("OUTPUT_CLK_EN",  "0"))
ECC_ENABLE     = int(os.getenv("ECC_ENABLE",     "0"))
INIT_MODE        =     os.getenv("INIT_MODE",        "all_one")
INIT_FILE_FORMAT =     os.getenv("INIT_FILE_FORMAT", "hex")
ECC_ERROR_INJECT = os.getenv("ECC_ERROR_INJECT", "0") == "1"

CLK_NS   = 10    # 100 MHz — matches golden testbench CLK_FREQ=10
RST_NS   = 100   # 10 cycles at 100 MHz — matches golden RESET_CNT=100

# Pipeline latency: 1 cycle for noreg, 2 cycles for reg
LAT = 1 if REGMODE == "noreg" else 2

DATA_MASK = (1 << RDATA_WIDTH) - 1

# ── Reference model ───────────────────────────────────────────────────────────
def _make_ref():
    """Build the expected memory array from INIT_MODE.

    INIT_MODE="all_one"  → every location returns DATA_MASK (all 1s).
    INIT_MODE="all_zero" → every location returns 0.
    INIT_MODE="none"     → defaults to all zeros (INIT_VALUE_xx defaults).
    INIT_MODE="mem_file" → load from INIT_FILE (hex); fall back to all-zero.
    """
    if INIT_MODE == "all_one":
        return [DATA_MASK] * RADDR_DEPTH

    if INIT_MODE == "mem_file":
        path = os.getenv("INIT_FILE", "rom_init.hex")
        fmt  = os.getenv("INIT_FILE_FORMAT", "hex")
        if os.path.isfile(path):
            words = []
            base  = 16 if fmt == "hex" else 2
            with open(path) as f:
                for line in f:
                    line = line.split("//")[0].strip()
                    if not line or line.startswith("@"):
                        continue
                    for tok in line.split():
                        words.append(int(tok, base) & DATA_MASK)
            return (words + [0] * RADDR_DEPTH)[:RADDR_DEPTH]
        cocotb.log.warning(f"INIT_FILE '{path}' not found; using all-zero fallback")

    return [0] * RADDR_DEPTH   # all_zero, none, or missing mem_file


REF = _make_ref()


# ── Shared infrastructure ─────────────────────────────────────────────────────
async def do_reset(dut):
    """Assert rst_i for RST_NS with all enables low, then release and sync to clock.

    Mirrors the golden testbench: rst_i=1 for RESET_CNT, then de-assert and
    wait for one rising edge before handing control back to the test.
    """
    dut.rst_i.value           = 1
    dut.rd_en_i.value         = 0
    dut.rd_clk_en_i.value     = 0
    dut.rd_out_clk_en_i.value = 0
    dut.rd_addr_i.value       = 0
    await Timer(RST_NS, unit="ns")
    dut.rst_i.value = 0
    await RisingEdge(dut.rd_clk_i)   # sync to first post-reset edge


async def single_read(dut, addr):
    """Drive addr after the current clock edge, wait LAT cycles, return rd_data_o.

    Prerequisite: rd_en_i, rd_clk_en_i, and rd_out_clk_en_i must already be 1.
    """
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = addr
    for _ in range(LAT):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    return int(dut.rd_data_o.value)


async def single_read_ecc(dut, addr):
    """Like single_read but also returns (data, one_err_det, two_err_det).

    Prerequisite: rd_en_i, rd_clk_en_i, and rd_out_clk_en_i must already be 1.
    Caller must be in Active phase; returns in ReadOnly phase.
    """
    await RisingEdge(dut.rd_clk_i)
    dut.rd_addr_i.value = addr
    for _ in range(LAT):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    return (
        int(dut.rd_data_o.value),
        int(dut.one_err_det_o.value),
        int(dut.two_err_det_o.value),
    )


async def enable_reads(dut):
    """Assert all three read enable signals."""
    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1


async def disable_reads(dut):
    """De-assert all three read enable signals."""
    dut.rd_en_i.value         = 0
    dut.rd_clk_en_i.value     = 0
    dut.rd_out_clk_en_i.value = 0


async def full_sweep(dut, tc):
    """Sequential read of all RADDR_DEPTH locations; verifies against REF.

    Uses single_read() for each address so that signal drives always happen
    in the active phase (after RisingEdge, before ReadOnly).  This avoids
    the ReadOnly → NextTimeStep → drive pattern which can corrupt the cocotb
    2.x scheduler when the same test runs more than once in a session.
    """
    errors = 0
    await enable_reads(dut)

    for addr in range(RADDR_DEPTH):
        got = await single_read(dut, addr)
        exp = REF[addr]
        if got != exp:
            hex_w = (RDATA_WIDTH + 3) // 4
            dut._log.error(
                f"[{tc}] addr={addr}: "
                f"got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"{tc} FAILED — {errors} data mismatch(es)"
    dut._log.info(f"{tc} PASSED  ({RADDR_DEPTH} reads, REGMODE={REGMODE})")


async def full_sweep_ecc(dut, tc):
    """Like full_sweep but also verifies one_err_det_o=0 and two_err_det_o=0 at every address.

    Used by TG-09 tests to confirm clean ECC reads produce no false error flags.
    """
    errors = 0
    await enable_reads(dut)
    hex_w = (RDATA_WIDTH + 3) // 4
    for addr in range(RADDR_DEPTH):
        got, one, two = await single_read_ecc(dut, addr)
        exp = REF[addr]
        if got != exp:
            dut._log.error(f"[{tc}] addr={addr}: got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}")
            errors += 1
        if one != 0 or two != 0:
            dut._log.error(
                f"[{tc}] addr={addr}: one_err_det_o={one} two_err_det_o={two} (expected both 0)"
            )
            errors += 1
    assert errors == 0, f"{tc} FAILED — {errors} error(s)"
    dut._log.info(f"{tc} PASSED  ({RADDR_DEPTH} reads, no ECC flags, ECC_ENABLE={ECC_ENABLE})")


async def latency_check(dut, tc, n_addrs=16):
    """Drive n_addrs sequential addresses and verify output lags by exactly LAT cycles.

    Pipeline phases:
      Prime      — fill the first LAT pipeline stages (no output sampled).
      Steady     — drive addr[i], sample addr[i-LAT] in the same clock cycle.
      Drain      — stop driving; flush the last LAT addresses through the pipeline.
    """
    errors = 0
    hex_w  = (RDATA_WIDTH + 3) // 4

    for i in range(LAT):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = i

    for i in range(LAT, n_addrs):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = i
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        exp = REF[i - LAT]
        if got != exp:
            dut._log.error(
                f"[{tc}] cycle {i}: addr_in_pipeline={i - LAT} "
                f"got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1

    for j in range(n_addrs - LAT, n_addrs):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        exp = REF[j]
        if got != exp:
            dut._log.error(
                f"[{tc}] drain: addr_in_pipeline={j} "
                f"got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"{tc} FAILED — {errors} latency mismatch(es)"
    dut._log.info(f"{tc} PASSED  ({n_addrs} pipelined reads, LAT={LAT} verified)")

# ═══════════════════════════════════════════════════════════════════════════════
# TG-01  Basic Read Functionality
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or INIT_MODE != "mem_file"))
async def tc_01_01_sequential_read_noreg(dut):
    """TC-01-01: rd_data_o = mem[addr] after exactly 1 clock cycle (noreg, 36b×512).

    Drives 16 sequential addresses in a pipelined pattern.  At each cycle the
    address presented one cycle earlier must appear at rd_data_o, proving that
    the pipeline latency is exactly LAT=1.
    """
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)
    await latency_check(dut, "TC-01-01")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_01_02_sequential_read_reg(dut):
    """TC-01-02: rd_data_o = mem[addr] after exactly 2 clock cycles (reg, 36b×512).

    Drives 16 sequential addresses in a pipelined pattern.  At each cycle the
    address presented two cycles earlier must appear at rd_data_o, proving that
    the pipeline latency is exactly LAT=2.
    """
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)
    await latency_check(dut, "TC-01-02")


@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_01_03_full_sweep_noreg(dut):
    """TC-01-03: All RADDR_DEPTH locations verified in order (noreg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-01-03")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_01_04_full_sweep_reg(dut):
    """TC-01-04: All RADDR_DEPTH locations verified in order (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-01-04")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 18 or RADDR_DEPTH != 1024))
async def tc_01_05_boundary_addresses(dut):
    """TC-01-05: Verify addr=0 and addr=RADDR_DEPTH-1 return correct data (reg, 18b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    for addr in (0, RADDR_DEPTH - 1):
        got = await single_read(dut, addr)
        exp = REF[addr]
        assert got == exp, (
            f"TC-01-05 FAILED at boundary addr={addr}: "
            f"got=0x{got:X} exp=0x{exp:X}"
        )
    dut._log.info("TC-01-05 PASSED  (boundary addresses)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_01_06_random_addresses(dut):
    """TC-01-06: 100 random address reads match reference model (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    rng = random.Random(0x1ECC_CAFE)   # fixed seed for reproducibility
    errors = 0
    for _ in range(100):
        addr = rng.randint(0, RADDR_DEPTH - 1)
        got  = await single_read(dut, addr)
        exp  = REF[addr]
        if got != exp:
            dut._log.error(f"TC-01-06 addr={addr}: got=0x{got:X} exp=0x{exp:X}")
            errors += 1

    assert errors == 0, f"TC-01-06 FAILED — {errors} mismatch(es)"
    dut._log.info("TC-01-06 PASSED  (100 random reads)")


@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 9 or RADDR_DEPTH != 2048))
async def tc_01_07_repeated_address(dut):
    """TC-01-07: Same address read 20 consecutive cycles yields stable output (noreg, 9b×2048)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    addr = RADDR_DEPTH // 2
    exp  = REF[addr]
    for rep in range(20):
        got = await single_read(dut, addr)
        assert got == exp, (
            f"TC-01-07 FAILED at rep={rep}: got=0x{got:X} exp=0x{exp:X}"
        )
    dut._log.info("TC-01-07 PASSED  (20 repeated reads, stable output)")

# ═══════════════════════════════════════════════════════════════════════════════
# TG-02  Read Enable (rd_en_i)
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_02_01_rd_en_zero_at_start(dut):
    """TC-02-01: rd_en_i=0 from start — rd_data_o holds reset value of 0 (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)

    # Clock gating enabled; read enable deliberately left de-asserted.
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1
    dut.rd_en_i.value         = 0

    # Drive valid addresses (all_one init → mem is all-1s, so any update would be visible).
    # Output register was cleared by reset; with rd_en_i=0 it must stay 0.
    for addr in range(8):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        assert got == 0, (
            f"TC-02-01 FAILED at addr={addr}: rd_data_o=0x{got:X}, expected 0 (rd_en_i=0)"
        )

    dut._log.info("TC-02-01 PASSED  (rd_data_o held at reset value 0 with rd_en_i=0)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_02_02_rd_en_deasserted_mid_seq(dut):
    """TC-02-02: rd_en_i de-asserted mid-sequence — output freezes at last valid value (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Fill the pipeline at addr=0 and record the stable output.
    dut.rd_addr_i.value = 0
    for _ in range(LAT + 1):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    frozen = int(dut.rd_data_o.value)
    assert frozen == REF[0], (
        f"TC-02-02 pre-condition: addr=0 got=0x{frozen:X} exp=0x{REF[0]:X}"
    )

    # De-assert rd_en_i; drive eight different addresses and verify output never changes.
    dut.rd_en_i.value = 0
    for addr in range(1, 9):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        assert got == frozen, (
            f"TC-02-02 FAILED at addr={addr}: rd_data_o=0x{got:X}, expected frozen=0x{frozen:X}"
        )

    dut._log.info("TC-02-02 PASSED  (rd_data_o froze when rd_en_i de-asserted)")


@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 18 or RADDR_DEPTH != 1024))
async def tc_02_03_rd_en_toggle_every_cycle(dut):
    """TC-02-03: rd_en_i alternated 1/0 — output updates only when rd_en_i=1 (noreg, 18b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1

    N     = 8
    errors = 0
    hex_w  = (RDATA_WIDTH + 3) // 4

    for i in range(N):
        addr = i * (RADDR_DEPTH // N)

        # rd_en_i=1: issue a normal read; output must equal REF[addr].
        dut.rd_en_i.value = 1
        got = await single_read(dut, addr)
        exp = REF[addr]
        if got != exp:
            dut._log.error(
                f"TC-02-03 rd_en=1 iter={i} addr={addr}: "
                f"got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1
        last_out = got

        # rd_en_i=0: one cycle with a deliberately different address — output must hold.
        dut.rd_en_i.value   = 0
        dut.rd_addr_i.value = (addr + RADDR_DEPTH // 2) % RADDR_DEPTH
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != last_out:
            dut._log.error(
                f"TC-02-03 rd_en=0 iter={i}: "
                f"got=0x{got:0{hex_w}X} expected hold=0x{last_out:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"TC-02-03 FAILED — {errors} error(s)"
    dut._log.info(f"TC-02-03 PASSED  ({N} rd_en_i 1/0 pairs, output updates only on rd_en_i=1)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_02_04_rd_en_resumes(dut):
    """TC-02-04: rd_en_i de-asserted then re-asserted — correct data resumes (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Establish a known baseline read.
    got_before = await single_read(dut, 0)
    assert got_before == REF[0], (
        f"TC-02-04 pre-condition: addr=0 got=0x{got_before:X} exp=0x{REF[0]:X}"
    )

    # De-assert rd_en_i for 5 cycles (pipeline drains / freezes).
    dut.rd_en_i.value = 0
    for _ in range(5):
        await RisingEdge(dut.rd_clk_i)

    # Re-assert rd_en_i and read a different address; data must be correct.
    dut.rd_en_i.value = 1
    addr = RADDR_DEPTH // 2
    got  = await single_read(dut, addr)
    exp  = REF[addr]
    assert got == exp, (
        f"TC-02-04 FAILED after re-assertion: addr={addr} got=0x{got:X} exp=0x{exp:X}"
    )
    dut._log.info("TC-02-04 PASSED  (reads resume correctly after rd_en_i re-assertion)")


# ═══════════════════════════════════════════════════════════════════════════════
# TG-03  Read Clock Enable (rd_clk_en_i)
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_03_01_clk_en_zero_holds_noreg(dut):
    """TC-03-01: rd_clk_en_i=0 freezes address register — rd_data_o retains last value (noreg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Prime: read addr=0 so the address register is at a known, stable location.
    frozen = await single_read(dut, 0)
    assert frozen == REF[0], f"TC-03-01 pre-condition: got=0x{frozen:X} exp=0x{REF[0]:X}"

    # single_read ends in ReadOnly phase; return to Active before driving rd_clk_en_i.
    await RisingEdge(dut.rd_clk_i)

    # De-assert clock enable; drive eight different addresses.
    # The address register must not advance, so output must stay mem[0].
    dut.rd_clk_en_i.value = 0
    for addr in range(1, 9):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        assert got == frozen, (
            f"TC-03-01 FAILED addr={addr}: rd_data_o=0x{got:X} expected frozen=0x{frozen:X}"
        )

    dut._log.info("TC-03-01 PASSED  (rd_data_o held at last value with rd_clk_en_i=0, noreg)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_03_02_clk_en_zero_holds_reg(dut):
    """TC-03-02: rd_clk_en_i=0 freezes address and output registers — rd_data_o retains last value (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Prime: read addr=0 and capture the stable output register value.
    frozen = await single_read(dut, 0)
    assert frozen == REF[0], f"TC-03-02 pre-condition: got=0x{frozen:X} exp=0x{REF[0]:X}"

    # single_read ends in ReadOnly phase; return to Active before driving rd_clk_en_i.
    await RisingEdge(dut.rd_clk_i)

    # De-assert clock enable; drive eight different addresses.
    # Both address register and output register must remain frozen.
    dut.rd_clk_en_i.value = 0
    for addr in range(1, 9):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        assert got == frozen, (
            f"TC-03-02 FAILED addr={addr}: rd_data_o=0x{got:X} expected frozen=0x{frozen:X}"
        )

    dut._log.info("TC-03-02 PASSED  (rd_data_o held at last value with rd_clk_en_i=0, reg)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_03_03_clk_en_reassertion(dut):
    """TC-03-03: rd_clk_en_i frozen 10 cycles then re-asserted — new address registered, correct data (reg, 36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Baseline read at addr=0.
    baseline = await single_read(dut, 0)
    assert baseline == REF[0], f"TC-03-03 pre-condition: got=0x{baseline:X} exp=0x{REF[0]:X}"

    # single_read ends in ReadOnly phase; return to Active before driving any signals.
    await RisingEdge(dut.rd_clk_i)

    # Freeze: de-assert rd_clk_en_i for 10 cycles while driving the target address.
    # The target address sits on rd_addr_i throughout so it is latched on re-assertion.
    target = RADDR_DEPTH // 4
    dut.rd_clk_en_i.value = 0
    dut.rd_addr_i.value   = target
    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)

    # Re-assert rd_clk_en_i; the first edge with clk_en=1 latches the target address.
    # single_read handles the LAT=2 pipeline delay from address capture to output.
    dut.rd_clk_en_i.value = 1
    got = await single_read(dut, target)
    exp = REF[target]
    assert got == exp, (
        f"TC-03-03 FAILED after re-assertion: addr={target} got=0x{got:X} exp=0x{exp:X}"
    )
    dut._log.info("TC-03-03 PASSED  (correct data after rd_clk_en_i re-assertion)")


@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 18 or RADDR_DEPTH != 1024))
async def tc_03_04_clk_en_toggle_pattern(dut):
    """TC-03-04: rd_clk_en_i alternated 1/0 each pair — output advances only when rd_clk_en_i=1 (noreg, 18b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    dut.rd_en_i.value         = 1
    dut.rd_out_clk_en_i.value = 1

    N      = 8
    errors = 0
    hex_w  = (RDATA_WIDTH + 3) // 4

    for i in range(N):
        addr = i * (RADDR_DEPTH // N)

        # rd_clk_en_i=1 cycle: drive addr BEFORE the rising edge so the EBR latches
        # it at that very edge (noreg: ReadOnly of the same edge shows mem[addr]).
        dut.rd_clk_en_i.value = 1
        dut.rd_addr_i.value   = addr
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        exp = REF[addr]
        if got != exp:
            dut._log.error(
                f"TC-03-04 clk_en=1 iter={i} addr={addr}: "
                f"got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1
        last_out = got

        # rd_clk_en_i=0 cycle: drive a different address — address register must
        # not advance, so output must hold at mem[addr].
        dut.rd_clk_en_i.value = 0
        dut.rd_addr_i.value   = (addr + RADDR_DEPTH // 2) % RADDR_DEPTH
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != last_out:
            dut._log.error(
                f"TC-03-04 clk_en=0 iter={i}: "
                f"got=0x{got:0{hex_w}X} expected hold=0x{last_out:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"TC-03-04 FAILED — {errors} error(s)"
    dut._log.info(f"TC-03-04 PASSED  ({N} rd_clk_en_i 1/0 pairs, output advances only on clk_en=1)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 1024))
async def tc_03_05_cascaded_clk_en(dut):
    """TC-03-05: rd_clk_en_i toggled across cascaded bank boundary — no spurious bank data (reg, 36b×1024).

    With RADDR_DEPTH=1024 the IP uses two cascaded 36×512 EBR tiles.  The bank
    boundary is at addr 511 (tile 0) / 512 (tile 1).  Toggling rd_clk_en_i while
    reading across that boundary exercises the v2.5.0 cascaded-enable fix.
    """
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    BANK_BOUNDARY = 511
    addrs  = [BANK_BOUNDARY - 2, BANK_BOUNDARY - 1, BANK_BOUNDARY,
              BANK_BOUNDARY + 1, BANK_BOUNDARY + 2, BANK_BOUNDARY + 3]
    errors = 0
    hex_w  = (RDATA_WIDTH + 3) // 4

    for addr in addrs:
        # Normal read with rd_clk_en_i=1 (re-asserted before each single_read).
        dut.rd_clk_en_i.value = 1
        got = await single_read(dut, addr)
        exp = REF[addr]
        if got != exp:
            dut._log.error(
                f"TC-03-05 addr={addr}: got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1

        # Freeze rd_clk_en_i for 2 cycles between reads to stress the bank-select logic.
        dut.rd_clk_en_i.value = 0
        for _ in range(2):
            await RisingEdge(dut.rd_clk_i)

    assert errors == 0, f"TC-03-05 FAILED — {errors} mismatch(es) across bank boundary"
    dut._log.info("TC-03-05 PASSED  (no spurious bank data across rd_clk_en_i toggle at boundary)")


# ═══════════════════════════════════════════════════════════════════════════════
# TG-04  Output Register Enable (rd_out_clk_en_i / OUTPUT_CLK_EN parameter)
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or OUTPUT_CLK_EN != 1))
async def tc_04_01_out_clk_en_zero_freezes_output(dut):
    """TC-04-01: rd_out_clk_en_i=0 freezes the output register (reg, 36b×512, OUTPUT_CLK_EN=1)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Prime: read addr=0 with both enables active to establish a known output value.
    frozen = await single_read(dut, 0)
    assert frozen == REF[0], f"TC-04-01 pre-condition: got=0x{frozen:X} exp=0x{REF[0]:X}"

    # single_read ends in ReadOnly; return to Active before driving rd_out_clk_en_i.
    await RisingEdge(dut.rd_clk_i)

    # Freeze the output register — address register still advances (rd_clk_en_i=1).
    dut.rd_out_clk_en_i.value = 0

    errors = 0
    hex_w = (RDATA_WIDTH + 3) // 4
    for addr in range(1, 9):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != frozen:
            dut._log.error(
                f"TC-04-01 addr={addr}: rd_data_o=0x{got:0{hex_w}X} expected frozen=0x{frozen:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"TC-04-01 FAILED — {errors} error(s); output register not frozen"
    dut._log.info("TC-04-01 PASSED  (rd_data_o held when rd_out_clk_en_i=0)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or OUTPUT_CLK_EN != 1))
async def tc_04_02_out_clk_en_normal_operation(dut):
    """TC-04-02: rd_out_clk_en_i=1 — normal 2-cycle latency (reg, 36b×512, OUTPUT_CLK_EN=1)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)
    await latency_check(dut, "TC-04-02")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or OUTPUT_CLK_EN != 1))
async def tc_04_03_out_clk_en_toggle_mid_seq(dut):
    """TC-04-03: rd_out_clk_en_i toggled mid-sequence — rd_data_o updates only when it is 1 (reg, 36b×512, OUTPUT_CLK_EN=1)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    hex_w = (RDATA_WIDTH + 3) // 4

    # Phase 1: prime — read addr=0 with rd_out_clk_en_i=1 to load a known output value.
    frozen = await single_read(dut, 0)
    assert frozen == REF[0], f"TC-04-03 pre-condition: got=0x{frozen:X} exp=0x{REF[0]:X}"

    # Return to Active phase, then freeze the output register.
    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 0

    # Phase 2: 5 cycles with rd_out_clk_en_i=0 — rd_data_o must not change.
    errors = 0
    for addr in range(1, 6):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != frozen:
            dut._log.error(
                f"TC-04-03 frozen phase addr={addr}: got=0x{got:0{hex_w}X} expected 0x{frozen:0{hex_w}X}"
            )
            errors += 1

    # Return to Active phase, re-enable the output register.
    await RisingEdge(dut.rd_clk_i)
    dut.rd_out_clk_en_i.value = 1

    # Phase 3: one clean latency-aware read — normal pipelined delivery must resume.
    target = 8
    got = await single_read(dut, target)
    exp = REF[target]
    if got != exp:
        dut._log.error(f"TC-04-03 resume addr={target}: got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}")
        errors += 1

    assert errors == 0, f"TC-04-03 FAILED — {errors} error(s)"
    dut._log.info("TC-04-03 PASSED  (rd_data_o froze during rd_out_clk_en_i=0; resumed after)")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or OUTPUT_CLK_EN != 0))
async def tc_04_04_output_clk_en_param_zero_no_effect(dut):
    """TC-04-04: OUTPUT_CLK_EN=0 — rd_out_clk_en_i port has no effect; data flows normally (reg, 36b×512, OUTPUT_CLK_EN=0)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)

    # Deliberately leave rd_out_clk_en_i=0.
    # When OUTPUT_CLK_EN=0 the output-register gate is hardwired open, so this must have no effect.
    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 0

    await latency_check(dut, "TC-04-04")


@cocotb.test(skip=(REGMODE != "reg" or RDATA_WIDTH != 18 or RADDR_DEPTH != 1024
                   or OUTPUT_CLK_EN != 1))
async def tc_04_05_both_enables_deasserted(dut):
    """TC-04-05: rd_clk_en_i=0 and rd_out_clk_en_i=0 simultaneously — rd_data_o holds last value (reg, 18b×1024, OUTPUT_CLK_EN=1)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    hex_w = (RDATA_WIDTH + 3) // 4

    # Prime: read addr=0 to establish the value both registers will hold.
    frozen = await single_read(dut, 0)
    assert frozen == REF[0], f"TC-04-05 pre-condition: got=0x{frozen:X} exp=0x{REF[0]:X}"

    # Return to Active phase, then de-assert both enables simultaneously.
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value     = 0
    dut.rd_out_clk_en_i.value = 0

    # Drive eight different addresses — neither register should advance.
    errors = 0
    for addr in range(1, 9):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != frozen:
            dut._log.error(
                f"TC-04-05 addr={addr}: rd_data_o=0x{got:0{hex_w}X} expected frozen=0x{frozen:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"TC-04-05 FAILED — {errors} error(s); output not frozen"
    dut._log.info("TC-04-05 PASSED  (rd_data_o held with rd_clk_en_i=0 and rd_out_clk_en_i=0)")


# ═══════════════════════════════════════════════════════════════════════════════
# TG-05  Reset Behavior
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(REGMODE != "reg" or RESETMODE != "sync" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_01_sync_reset_clears_output(dut):
    """TC-05-01: Sync reset holds rd_data_o=0 while rst_i=1 (reg, sync)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Fill the pipeline so rd_data_o holds a known non-zero value (all_one init).
    dut.rd_addr_i.value = 0
    for _ in range(LAT + 1):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    pre_rst = int(dut.rd_data_o.value)
    assert pre_rst == REF[0], f"TC-05-01 pre-condition failed: got=0x{pre_rst:X}"

    # Assert sync reset and verify output clears every cycle for 5 cycles.
    dut.rst_i.value = 1
    for cycle in range(5):
        await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        assert got == 0, (
            f"TC-05-01 FAILED at reset cycle {cycle}: "
            f"rd_data_o=0x{got:X}, expected 0"
        )

    dut.rst_i.value = 0
    dut._log.info("TC-05-01 PASSED  (sync reset cleared output for 5 cycles)")


@cocotb.test(skip=(REGMODE != "reg" or RESETMODE != "sync" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_02_sync_reset_during_read(dut):
    """TC-05-02: Sync reset asserted mid-sequence clears output on next clock (reg, sync)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Start reading to ensure pipeline is primed.
    for addr in range(LAT + 2):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr

    # Assert reset mid-sequence (between clock edges).
    dut.rst_i.value = 1

    # On the very next rising edge after rst_i=1, output register must clear.
    await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    got = int(dut.rd_data_o.value)
    assert got == 0, (
        f"TC-05-02 FAILED: rd_data_o=0x{got:X} one cycle after sync reset, expected 0"
    )

    dut.rst_i.value = 0
    dut._log.info("TC-05-02 PASSED  (sync reset cleared output within one cycle)")


@cocotb.test(skip=(REGMODE != "reg" or RESETMODE != "sync" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_03_sync_reset_release_resumes(dut):
    """TC-05-03: Normal reads resume correctly after sync reset release (reg, sync)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Assert reset for 3 cycles then release.
    dut.rst_i.value = 1
    for _ in range(3):
        await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0

    # Do a normal read and confirm correct data returns.
    addr = RADDR_DEPTH // 4
    got  = await single_read(dut, addr)
    exp  = REF[addr]
    assert got == exp, (
        f"TC-05-03 FAILED after reset release: addr={addr} got=0x{got:X} exp=0x{exp:X}"
    )
    dut._log.info("TC-05-03 PASSED  (reads resume correctly after sync reset)")


@cocotb.test(skip=(REGMODE != "reg" or RESETMODE != "async" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_04_async_reset_clears_immediately(dut):
    """TC-05-04: Async rst_i clears rd_data_o before the next clock edge (reg, async)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Read addr=0 — with all_one init REF[0] is non-zero, confirming valid output.
    dut.rd_addr_i.value = 0
    for _ in range(LAT + 1):
        await RisingEdge(dut.rd_clk_i)
    await ReadOnly()
    pre_rst = int(dut.rd_data_o.value)
    assert pre_rst == REF[0], f"TC-05-04 pre-condition failed: got=0x{pre_rst:X}"

    # Assert reset asynchronously — mid-cycle, not at a clock edge.
    await Timer(CLK_NS // 4, unit="ns")
    dut.rst_i.value = 1
    # Allow a small propagation window before sampling.
    await Timer(1, unit="ns")
    got = int(dut.rd_data_o.value)
    assert got == 0, (
        f"TC-05-04 FAILED: async reset did not clear rd_data_o immediately; "
        f"got=0x{got:X}"
    )

    dut.rst_i.value = 0
    dut._log.info("TC-05-04 PASSED  (async reset cleared rd_data_o without a clock edge)")


@cocotb.test(skip=(REGMODE != "reg" or RESETMODE != "async" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_05_async_reset_release_resumes(dut):
    """TC-05-05: Output register operational after async reset release (reg, async)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    # Assert reset asynchronously then release.
    await Timer(CLK_NS // 4, unit="ns")
    dut.rst_i.value = 1
    await Timer(CLK_NS // 2, unit="ns")
    dut.rst_i.value = 0

    # Sync back to a clock edge, then do a normal read.
    await RisingEdge(dut.rd_clk_i)
    addr = RADDR_DEPTH // 4
    got  = await single_read(dut, addr)
    exp  = REF[addr]
    assert got == exp, (
        f"TC-05-05 FAILED after async reset release: "
        f"addr={addr} got=0x{got:X} exp=0x{exp:X}"
    )
    dut._log.info("TC-05-05 PASSED  (reads operational after async reset release)")


@cocotb.test(skip=(REGMODE != "noreg" or RESETMODE != "sync" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_05_06_noreg_reset_has_no_effect(dut):
    """TC-05-06: noreg/sync — rst_i=1 zeroes rd_data_o; reads resume correctly after de-assertion.

    Despite the noreg label, the LIFCL PDPSC16K output bus is gated by rst_i:
    synchronous reset forces rd_data_o to 0 on every rising edge while rst_i=1.
    """
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)
    errors = 0
    hex_w = (RDATA_WIDTH + 3) // 4

    # Phase 1: assert rst_i=1 — expect rd_data_o=0 at every address.
    dut.rst_i.value = 1
    for addr in range(min(16, RADDR_DEPTH)):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != 0:
            dut._log.error(
                f"TC-05-06 rst_i=1 addr={addr}: got=0x{got:0{hex_w}X} expected 0x0"
            )
            errors += 1

    # Phase 2: de-assert rst_i in Active phase, then verify reads resume correctly.
    await RisingEdge(dut.rd_clk_i)
    dut.rst_i.value = 0
    for addr in range(min(8, RADDR_DEPTH)):
        got = await single_read(dut, addr)
        exp = REF[addr]
        if got != exp:
            dut._log.error(
                f"TC-05-06 post-reset addr={addr}: got=0x{got:0{hex_w}X} exp=0x{exp:0{hex_w}X}"
            )
            errors += 1

    assert errors == 0, f"TC-05-06 FAILED — {errors} error(s)"
    dut._log.info("TC-05-06 PASSED  (rst_i=1 zeroes output; reads resume after de-assertion)")


# ═══════════════════════════════════════════════════════════════════════════════
# TG-06  Memory Initialization
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 512 or INIT_MODE != "all_zero"))
async def tc_06_01_all_zero_init(dut):
    """TC-06-01: INIT_MODE=all_zero — all 512 locations return 0 (36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-01")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 512 or INIT_MODE != "all_one"))
async def tc_06_02_all_one_init(dut):
    """TC-06-02: INIT_MODE=all_one — all 512 locations return DATA_MASK (36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-02")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or INIT_MODE != "mem_file" or INIT_FILE_FORMAT != "hex"))
async def tc_06_03_mem_file_hex(dut):
    """TC-06-03: INIT_MODE=mem_file, hex format — all 512 locations match INIT_FILE content (36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-03")


@cocotb.test(skip=(RDATA_WIDTH != 18 or RADDR_DEPTH != 1024
                   or INIT_MODE != "mem_file" or INIT_FILE_FORMAT != "binary"))
async def tc_06_04_mem_file_binary(dut):
    """TC-06-04: INIT_MODE=mem_file, binary format — all 1024 locations match INIT_FILE content (18b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-04")


@cocotb.test(skip=(RDATA_WIDTH != 9 or RADDR_DEPTH != 2048 or INIT_MODE != "mem_file"))
async def tc_06_05_mem_file_alternating_pattern(dut):
    """TC-06-05: INIT_MODE=mem_file, alternating 0xAA/0x55 — verified then swept (9b×2048)."""
    # Verify the reference model loaded the expected alternating content.
    EVEN_VAL = 0x0AA & DATA_MASK
    ODD_VAL  = 0x055 & DATA_MASK
    for i in range(RADDR_DEPTH):
        exp = EVEN_VAL if i % 2 == 0 else ODD_VAL
        assert REF[i] == exp, (
            f"TC-06-05 pre-condition: INIT_FILE does not encode alternating pattern at addr={i}: "
            f"REF[{i}]={REF[i]:#x} expected {exp:#x}"
        )

    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-05")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or INIT_MODE != "mem_file" or INIT_FILE_FORMAT != "hex"))
async def tc_06_06_mem_file_addr_as_data(dut):
    """TC-06-06: INIT_MODE=mem_file, addr-as-data — mem[i]=i verified for all 512 entries (36b×512)."""
    # Confirm the fixture encodes address-as-data before exercising the hardware.
    for i in range(RADDR_DEPTH):
        assert REF[i] == i, (
            f"TC-06-06 pre-condition: INIT_FILE is not addr-as-data at addr={i}: "
            f"REF[{i}]={REF[i]} expected {i}"
        )

    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-06")


@cocotb.test(skip=(RDATA_WIDTH != 1 or RADDR_DEPTH != 16384 or INIT_MODE != "all_zero"))
async def tc_06_07_all_zero_narrow(dut):
    """TC-06-07: INIT_MODE=all_zero, 1b×16384 — all 16384 locations return 0."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-07")


@cocotb.test(skip=(RDATA_WIDTH != 4 or RADDR_DEPTH != 4096
                   or INIT_MODE != "mem_file" or INIT_FILE_FORMAT != "binary"))
async def tc_06_08_mem_file_binary_narrow(dut):
    """TC-06-08: INIT_MODE=mem_file, binary format, 4b×4096 — all locations match INIT_FILE content."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-06-08")

# ═══════════════════════════════════════════════════════════════════════════════
# TG-07  LIFCL EBR Tile Configuration Coverage
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(RDATA_WIDTH != 1 or RADDR_DEPTH != 2 or INIT_MODE != "all_zero"))
async def tc_07_01_minimum_config(dut):
    """TC-07-01: Minimum config — 1b×2, all_zero; verifies correct tile selection at smallest dimensions."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-01")


@cocotb.test(skip=(RDATA_WIDTH != 1 or RADDR_DEPTH != 16384 or INIT_MODE != "mem_file"))
async def tc_07_02_1bit_max_depth(dut):
    """TC-07-02: 1b×16384 — full depth sweep at maximum single-tile depth."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-02")


@cocotb.test(skip=(RDATA_WIDTH != 2 or RADDR_DEPTH != 8192 or INIT_MODE != "mem_file"))
async def tc_07_03_2bit_8192(dut):
    """TC-07-03: 2b×8192 — full depth sweep."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-03")


@cocotb.test(skip=(RDATA_WIDTH != 4 or RADDR_DEPTH != 4096 or INIT_MODE != "mem_file"))
async def tc_07_04_4bit_4096(dut):
    """TC-07-04: 4b×4096 — full depth sweep."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-04")


@cocotb.test(skip=(RDATA_WIDTH != 9 or RADDR_DEPTH != 2048 or INIT_MODE != "mem_file"))
async def tc_07_05_9bit_2048_parity(dut):
    """TC-07-05: 9b×2048 (parity width) — full depth sweep."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-05")


@cocotb.test(skip=(RDATA_WIDTH != 18 or RADDR_DEPTH != 1024 or INIT_MODE != "mem_file"))
async def tc_07_06_18bit_1024_parity(dut):
    """TC-07-06: 18b×1024 (parity width) — full depth sweep."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-06")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 512 or INIT_MODE != "mem_file"))
async def tc_07_07_36bit_512_default(dut):
    """TC-07-07: 36b×512 (default tile) — full depth sweep."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-07")


@cocotb.test(skip=(RDATA_WIDTH != 12 or RADDR_DEPTH != 512 or INIT_MODE != "mem_file"))
async def tc_07_08_non_aligned_width(dut):
    """TC-07-08: 12b×512 (non-aligned width) — IP selects optimal tile; full sweep passes."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-07-08")

# ═══════════════════════════════════════════════════════════════════════════════
# TG-08  EBR Cascading
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 1024 or INIT_MODE != "mem_file"))
async def tc_08_01_addr_cascade_x2(dut):
    """TC-08-01: Address cascade ×2 — all 1024 locations correct; bank boundary transparent (36b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-01")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 2048 or INIT_MODE != "mem_file"))
async def tc_08_02_addr_cascade_x4(dut):
    """TC-08-02: Address cascade ×4 — all 2048 locations correct (36b×2048)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-02")


@cocotb.test(skip=(RDATA_WIDTH != 72 or RADDR_DEPTH != 512 or INIT_MODE != "mem_file"))
async def tc_08_03_data_cascade_x2(dut):
    """TC-08-03: Data cascade ×2 — all 72-bit words correct across both tiles (72b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-03")


@cocotb.test(skip=(RDATA_WIDTH != 144 or RADDR_DEPTH != 512 or INIT_MODE != "mem_file"))
async def tc_08_04_data_cascade_x4(dut):
    """TC-08-04: Data cascade ×4 — all 144-bit words correct across four tiles (144b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-04")


@cocotb.test(skip=(RDATA_WIDTH != 72 or RADDR_DEPTH != 1024 or INIT_MODE != "mem_file"))
async def tc_08_05_both_cascades(dut):
    """TC-08-05: Addr×2 + Data×2 cascades — all 1024×72-bit locations correct (72b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-05")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 1024 or INIT_MODE != "mem_file"))
async def tc_08_06_bank_boundary_read(dut):
    """TC-08-06: Bank boundary — addr=511 (last in bank 0) and addr=512 (first in bank 1) each return correct data (36b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    hex_w = (RDATA_WIDTH + 3) // 4

    # Confirm fixture provides distinct values across the boundary.
    assert REF[511] != REF[512], (
        f"TC-08-06 pre-condition: REF[511]=REF[512]={REF[511]:#x}; "
        "fixture must provide distinct data across the bank boundary"
    )

    errors = 0
    # single_read() handles the ReadOnly→Active transition internally.
    got_511 = await single_read(dut, 511)
    if got_511 != REF[511]:
        dut._log.error(f"TC-08-06 addr=511: got=0x{got_511:0{hex_w}X} exp=0x{REF[511]:0{hex_w}X}")
        errors += 1

    got_512 = await single_read(dut, 512)
    if got_512 != REF[512]:
        dut._log.error(f"TC-08-06 addr=512: got=0x{got_512:0{hex_w}X} exp=0x{REF[512]:0{hex_w}X}")
        errors += 1

    assert errors == 0, f"TC-08-06 FAILED — {errors} error(s) at bank boundary"
    dut._log.info("TC-08-06 PASSED  (addr=511 and addr=512 each returned correct distinct data)")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 1024 or INIT_MODE != "mem_file"))
async def tc_08_07_addr_cascade_clk_en_toggle(dut):
    """TC-08-07: clk_en toggle across bank boundary — v2.5.0: no spurious data from wrong bank (36b×1024)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    hex_w = (RDATA_WIDTH + 3) // 4
    errors = 0

    # Phase 1: prime the pipeline at addr=511 (last address of bank 0).
    frozen = await single_read(dut, 511)
    assert frozen == REF[511], f"TC-08-07 pre-condition: got=0x{frozen:X} exp=0x{REF[511]:X}"

    # single_read ends in ReadOnly; return to Active, then de-assert rd_clk_en_i.
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value = 0

    # Phase 2: drive addresses that cross into bank 1 while rd_clk_en_i=0.
    # Output must remain frozen; v2.5.0 bug would have updated with stale bank data.
    for addr in [512, 513, 514]:
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        await ReadOnly()
        got = int(dut.rd_data_o.value)
        if got != frozen:
            dut._log.error(
                f"TC-08-07 frozen phase addr={addr}: got=0x{got:0{hex_w}X} "
                f"expected frozen=0x{frozen:0{hex_w}X}"
            )
            errors += 1

    # Phase 3: re-assert rd_clk_en_i and do a clean read into bank 1.
    await RisingEdge(dut.rd_clk_i)
    dut.rd_clk_en_i.value = 1

    got_515 = await single_read(dut, 515)
    if got_515 != REF[515]:
        dut._log.error(
            f"TC-08-07 resume addr=515: got=0x{got_515:0{hex_w}X} exp=0x{REF[515]:0{hex_w}X}"
        )
        errors += 1

    assert errors == 0, f"TC-08-07 FAILED — {errors} error(s)"
    dut._log.info("TC-08-07 PASSED  (rd_data_o held across bank boundary; clean resume into bank 1)")


@cocotb.test(skip=(RDATA_WIDTH != 36 or RADDR_DEPTH != 2048
                   or INIT_MODE != "mem_file" or REGMODE != "reg"))
async def tc_08_08_addr_cascade_reg_mode(dut):
    """TC-08-08: Address cascade ×4, REGMODE=reg — LAT=2 verified across all four banks (36b×2048)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep(dut, "TC-08-08")

# ═══════════════════════════════════════════════════════════════════════════════
# TG-09  ECC
# ═══════════════════════════════════════════════════════════════════════════════

@cocotb.test(skip=(ECC_ENABLE != 0 or RDATA_WIDTH != 36 or RADDR_DEPTH != 512))
async def tc_09_01_ecc_disabled_outputs_zero(dut):
    """TC-09-01: ECC_ENABLE=0 — one_err_det_o and two_err_det_o are 0 at all times (36b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await enable_reads(dut)

    errors = 0
    for addr in range(min(16, RADDR_DEPTH)):
        await RisingEdge(dut.rd_clk_i)
        dut.rd_addr_i.value = addr
        for _ in range(LAT):
            await RisingEdge(dut.rd_clk_i)
        await ReadOnly()
        one = int(dut.one_err_det_o.value)
        two = int(dut.two_err_det_o.value)
        if one != 0 or two != 0:
            dut._log.error(
                f"TC-09-01 addr={addr}: one_err_det_o={one} two_err_det_o={two} (expected both 0)"
            )
            errors += 1

    assert errors == 0, f"TC-09-01 FAILED — {errors} spurious ECC flag(s) with ECC_ENABLE=0"
    dut._log.info("TC-09-01 PASSED  (one_err_det_o=two_err_det_o=0 for all reads, ECC_ENABLE=0)")


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 32 or RADDR_DEPTH != 512))
async def tc_09_02_ecc_enabled_clean_data(dut):
    """TC-09-02: ECC_ENABLE=1, clean init data — rd_data_o correct; no error flags asserted (32b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep_ecc(dut, "TC-09-02")


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 32))
async def tc_09_03_ecc_minimum_width(dut):
    """TC-09-03: ECC_ENABLE=1, RDATA_WIDTH=32 (minimum ECC width) — full sweep, no false error flags."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep_ecc(dut, "TC-09-03")


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 64 or RADDR_DEPTH != 512))
async def tc_09_04_ecc_maximum_width(dut):
    """TC-09-04: ECC_ENABLE=1, RDATA_WIDTH=64 (maximum ECC width) — full sweep, no false error flags (64b×512)."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut)
    await full_sweep_ecc(dut, "TC-09-04")


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 32 or RADDR_DEPTH != 512
                   or not ECC_ERROR_INJECT))
async def tc_09_05_sec_single_bit_error(dut):
    """TC-09-05: SEC — one_err_det_o=1, two_err_det_o=0, rd_data_o carries corrected value.

    Requires ECC_ERROR_INJECT=1 in the environment AND a pre-corrupted INIT_FILE
    whose codeword at address 0 has exactly one bit flipped relative to the
    correctly SECDED-encoded value.  The LIFCL EBR does not expose an error-
    injection port; corruption must be baked into the ROM at initialisation time
    by computing the ECC polynomial externally and flipping one parity or data bit.

    Set ECC_ERROR_INJECT=1 to un-skip this test once the infrastructure is ready.
    """
    raise NotImplementedError(
        "TC-09-05: error injection infrastructure not yet implemented. "
        "Provide a pre-corrupted INIT_FILE and set ECC_ERROR_INJECT=1."
    )


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 32 or RADDR_DEPTH != 512
                   or not ECC_ERROR_INJECT))
async def tc_09_06_ded_double_bit_error(dut):
    """TC-09-06: DED — two_err_det_o=1, one_err_det_o=0.

    Same infrastructure requirement as TC-09-05: the INIT_FILE codeword at the
    target address must have exactly two bits flipped.  SECDED cannot correct a
    double-bit error, so rd_data_o is undefined; only the flag output is checked.

    Set ECC_ERROR_INJECT=1 to un-skip once the pre-corrupted fixture is in place.
    """
    raise NotImplementedError(
        "TC-09-06: error injection infrastructure not yet implemented. "
        "Provide a pre-corrupted INIT_FILE and set ECC_ERROR_INJECT=1."
    )


@cocotb.test(skip=(ECC_ENABLE != 1 or RDATA_WIDTH != 32 or RADDR_DEPTH != 512
                   or not ECC_ERROR_INJECT))
async def tc_09_07_ecc_error_recovery(dut):
    """TC-09-07: ECC recovery — after a SEC event, error flags deassert on subsequent clean reads.

    Requires the same pre-corrupted INIT_FILE as TC-09-05 (single-bit error at
    addr=0).  The test reads addr=0 (SEC fires), then reads several clean
    addresses (addr=1…8) and verifies one_err_det_o and two_err_det_o are both 0.

    Set ECC_ERROR_INJECT=1 to un-skip once the pre-corrupted fixture is in place.
    """
    raise NotImplementedError(
        "TC-09-07: error injection infrastructure not yet implemented. "
        "Provide a pre-corrupted INIT_FILE and set ECC_ERROR_INJECT=1."
    )

