# sim.f — qrun filelist for lscc_rom CoCoTB testbench
#
# Usage (via run_qsim.sh):
#   ./run_qsim.sh -m oem_local -b <radiant_build> -f sim.f
#   REGMODE=reg ./run_qsim.sh ...
#
# Direct qrun usage:
#   qrun -f sim.f -GREGMODE=reg -GRDATA_WIDTH=36 -GRADDR_DEPTH=512 \
#        -pli <cocotb_vpi> -do "run -all; quit"

# ── RTL sources ───────────────────────────────────────────────────────────────
rtl/lscc_rom.v
testbench/testgen_top.v

# ── Top-level ─────────────────────────────────────────────────────────────────
-top testgen_top

# ── Simulation run options ────────────────────────────────────────────────────
-sv
+acc
