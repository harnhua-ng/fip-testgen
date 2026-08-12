"""
tb_rom_reset.py — Minimal smoke test for lscc_rom end-to-end simulation flow.

What it does
  1. Starts a 100 MHz clock on rd_clk_i.
  2. Holds rst_i=1 (all enables low) for 10 clock cycles.
  3. Releases reset, enables reads.
  4. Drives rd_addr_i=0 and runs 20 more clock cycles.
  5. Passes unconditionally — the purpose is to verify the flow and
     produce a WLF file with all signals visible for manual inspection.

Run
  COCOTB_TEST_MODULES=tb_lscc_rom_reset \
  qrun -f sim.f \
       -GRDATA_WIDTH=36 -GRADDR_DEPTH=512 -GREGMODE=noreg \
       -GRESETMODE=sync -GOUTPUT_CLK_EN=0 -GECC_ENABLE=0 -GINIT_MODE=all_one \
       -pli "$(cocotb-config --lib-name-path vpi questa)" \
       -wlf tb_lscc_rom_reset.wlf \
       -do "log -r /*; run -all; quit"

View waveforms (Questa GUI)
  vsim -view tb_lscc_rom_reset.wlf
  # In the Wave window: Edit → Select All → Add to Wave
"""

import os
import cocotb
from cocotb.clock    import Clock
from cocotb.triggers import RisingEdge

CLK_NS = 10   # 100 MHz


@cocotb.test()
async def tc_smoke_reset(dut):
    """Smoke: assert reset for 10 cycles, release, observe 20 more cycles."""
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())

    # ── Assert reset (all enables low) ────────────────────────────────────────
    dut.rst_i.value           = 1
    dut.rd_en_i.value         = 0
    dut.rd_clk_en_i.value     = 0
    dut.rd_out_clk_en_i.value = 0
    dut.rd_addr_i.value       = 0

    for _ in range(10):
        await RisingEdge(dut.rd_clk_i)

    # ── Release reset, enable reads ───────────────────────────────────────────
    dut.rst_i.value           = 0
    dut.rd_en_i.value         = 1
    dut.rd_clk_en_i.value     = 1
    dut.rd_out_clk_en_i.value = 1
    dut.rd_addr_i.value       = 0

    for _ in range(20):
        await RisingEdge(dut.rd_clk_i)

    dut._log.info("Smoke test complete — open tb_lscc_rom_reset.wlf in Questa to inspect signals")
