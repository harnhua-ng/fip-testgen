# sim.f — QuestaSim argument and filelist file for lscc_rom testbench
#
# Usage (via run_qsim.sh):
#   ./run_qsim.sh -m oem_local -b <radiant_build> -f scripts/sim.f
#   REGMODE=reg ./run_qsim.sh ...
#
# Direct QuestaSim / qrun usage:
#   qrun -f scripts/sim.f -GREGMODE=reg -GRDATA_WIDTH=36 -GRADDR_DEPTH=512 \
#        -pli <cocotb_vpi> -do "run -all; quit"
#
# ── RTL and Testbench Sources ────────────────────────────────────────────────
rtl/lscc_rom.v
testbench/testgen_top.v

# ── Top-level module (for CoCoTB: testgen_top; for standalone Verilog: tb_rom) ─
-top testgen_top

# ── Simulation compilation & optimization options ─────────────────────────────
-sv
+acc
