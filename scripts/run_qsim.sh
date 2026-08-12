#!/bin/sh
# =============================================================================
# run_qsim.sh
# Run a Lattice Radiant QuestaSim simulation on Linux.
#
# Usage:
#   ./run_qsim.sh [OPTIONS]
#
# Options:
#   -f  <file.f>          QuestaSim .f argument file (required)
#   -b  <radiant_build>   Path to local Radiant build workspace
#                         (e.g. /home/mkhor/workspace/ng2024_2.115)
#                         Omit to use the LDP wrapper instead.
#   -m  <mode>            Simulation mode: oem_local | oem_ldp | std_ldp
#                         Default: oem_ldp
#   -d  <device>          Device family for sim library compilation
#                         (e.g. lavat, lfcpnx, lav_atx). Required for std_ldp.
#   -l  <lib_output>      Directory where compiled sim library will be placed.
#                         Default: ./sim_lib
#   -g                    Launch QuestaSim GUI (adds -gui flag to qrun).
#   -a                    Add +acc flag (expose all ports and parameters).
#   -r  <run_time>        Simulation run time passed via -do (e.g. "100 ns").
#                         Default: run -all
#   -L  <license_file>    Override LM_LICENSE_FILE value.
#   -S  <salt_server>     Override SALT_LICENSE_SERVER value.
#   -R  <regmode>         REGMODE parameter: noreg | reg  (default: noreg)
#   -W  <rdata_width>     RDATA_WIDTH parameter             (default: 36)
#   -D  <raddr_depth>     RADDR_DEPTH parameter             (default: 512)
#   -M  <resetmode>       RESETMODE parameter: sync | async (default: sync)
#   -O  <output_clk_en>   OUTPUT_CLK_EN parameter: 0 | 1   (default: 0)
#   -E  <ecc_enable>      ECC_ENABLE parameter: 0 | 1      (default: 0)
#   -I  <init_mode>       INIT_MODE: all_one|all_zero|mem_file|none (default: all_one)
#   -h                    Print this help text and exit.
#
# Modes:
#   oem_local   Use the QuestaSim OEM bundled with a local Radiant build.
#               Requires -b. Sets PATH and license variables from the build.
#   oem_ldp     Use the QuestaSim OEM via LDP wrappers (default).
#               No local build required; LDP handles license and PATH.
#   std_ldp     Use standard (non-OEM) QuestaSim via LDP.
#               Requires a pre-compiled sim library. If the library directory
#               specified by -l does not exist, the script will compile it
#               automatically using cmpl_libs.tcl.
#
# Examples:
#   # OEM via LDP (simplest):
#   ./run_qsim.sh -f test_sim.f
#
#   # OEM with local build:
#   ./run_qsim.sh -m oem_local -b /home/mkhor/workspace/ng2024_2.115 -f test_sim.f
#
#   # Standard QuestaSim via LDP, auto-compile sim library for lavat device:
#   ./run_qsim.sh -m std_ldp -d lavat -f test_sim.f
#
#   # OEM via LDP, GUI mode, expose all signals:
#   ./run_qsim.sh -f test_sim.f -g -a
# =============================================================================

# exit on error
set -eu

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
F_FILE=""
BUILD_PATH=""
MODE="oem_local"
DEVICE=""
LIB_OUTPUT="./sim_lib"
GUI=0
ACC=0
RUN_TIME=""
LICENSE_FILE=""
SALT_SERVER=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# DUT parameters forwarded to run.sh / qrun via env vars
REGMODE="${REGMODE:-noreg}"
RDATA_WIDTH="${RDATA_WIDTH:-36}"
RADDR_DEPTH="${RADDR_DEPTH:-512}"
RESETMODE="${RESETMODE:-sync}"
OUTPUT_CLK_EN="${OUTPUT_CLK_EN:-0}"
ECC_ENABLE="${ECC_ENABLE:-0}"
INIT_MODE="${INIT_MODE:-all_one}"

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
log()  { printf '[run_qsim] %s\n' "$*"; }
warn() { printf '[run_qsim] WARNING: %s\n' "$*" >&2; }
die()  { printf '[run_qsim] ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
    sed -n '/^# Usage:/,/^# =====/p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while getopts "f:b:m:d:l:gar:L:S:R:W:D:M:O:E:I:h" OPT; do
    case "$OPT" in
        f) F_FILE="$OPTARG" ;;
        b) BUILD_PATH="$OPTARG" ;;
        m) MODE="$OPTARG" ;;
        d) DEVICE="$OPTARG" ;;
        l) LIB_OUTPUT="$OPTARG" ;;
        g) GUI=1 ;;
        a) ACC=1 ;;
        r) RUN_TIME="$OPTARG" ;;
        L) LICENSE_FILE="$OPTARG" ;;
        S) SALT_SERVER="$OPTARG" ;;
        R) REGMODE="$OPTARG" ;;
        W) RDATA_WIDTH="$OPTARG" ;;
        D) RADDR_DEPTH="$OPTARG" ;;
        M) RESETMODE="$OPTARG" ;;
        O) OUTPUT_CLK_EN="$OPTARG" ;;
        E) ECC_ENABLE="$OPTARG" ;;
        I) INIT_MODE="$OPTARG" ;;
        h) usage ;;
        *) die "Unknown option. Run with -h for help." ;;
    esac
done
export REGMODE RDATA_WIDTH RADDR_DEPTH RESETMODE OUTPUT_CLK_EN ECC_ENABLE INIT_MODE

# ---------------------------------------------------------------------------
# Validate required arguments
# ---------------------------------------------------------------------------
[ -z "$F_FILE" ] && die "-f <file.f> is required. Run with -h for help."

case "$MODE" in
    oem_local|oem_ldp|std_ldp) ;;
    *) die "Invalid mode '$MODE'. Must be one of: oem_local oem_ldp std_ldp" ;;
esac

[ "$MODE" = "oem_local" ] && [ -z "$BUILD_PATH" ] && \
    die "Mode 'oem_local' requires -b <radiant_build>."

[ "$MODE" = "std_ldp" ] && [ -z "$DEVICE" ] && \
    die "Mode 'std_ldp' requires -d <device> for sim library compilation."

[ -f "$F_FILE" ] || die ".f file not found: $F_FILE"

# ---------------------------------------------------------------------------
# Mode: oem_local — source commonenv.cshrc equivalent in sh, set OEM PATH
# ---------------------------------------------------------------------------
setup_oem_local() {
    log "Mode: oem_local — configuring environment from local Radiant build."

    BUILD_PATH=$(cd "$BUILD_PATH" && pwd)   # resolve to absolute path
    [ -d "$BUILD_PATH" ] || die "Radiant build path not found: $BUILD_PATH"

    QUESTA_BIN="$BUILD_PATH/rtf/tptools/questasim/linux/questasim/bin"
    [ -d "$QUESTA_BIN" ] || \
        die "QuestaSim OEM bin directory not found: $QUESTA_BIN"

    # Prepend OEM bin to PATH so qrun resolves to the OEM binary
    PATH="$QUESTA_BIN:$PATH"
    export PATH
    log "PATH prepended with: $QUESTA_BIN"

    # Source equivalent of commonenv.cshrc: set FOUNDRY and ENV
    FOUNDRY="$BUILD_PATH/rtf/ispfpga"
    ENV_FPGA="$BUILD_PATH/env/fpga"
    export FOUNDRY ENV_FPGA
    log "FOUNDRY set to: $FOUNDRY"

    # License — use override if provided, else set OEM defaults from document

    if [ -n "$LICENSE_FILE" ]; then
        export LM_LICENSE_FILE="$LICENSE_FILE"
    else
        export LM_LICENSE_FILE=1850@ldc-virtlic02
    fi

    if [ -n "$SALT_SERVER" ]; then
        export SALT_LICENSE_SERVER="$SALT_SERVER"
    else
        export SALT_LICENSE_SERVER=1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b
    fi

    log "LM_LICENSE_FILE  : $LM_LICENSE_FILE"
    log "SALT_LICENSE_SERVER: $SALT_LICENSE_SERVER"
}

# ---------------------------------------------------------------------------
# Mode: oem_ldp — rely on LDP wrappers; optionally override license
# ---------------------------------------------------------------------------
setup_oem_ldp() {
    log "Mode: oem_ldp — using LDP wrappers for QuestaSim OEM."

    if [ -n "$LICENSE_FILE" ]; then
        LM_LICENSE_FILE="$LICENSE_FILE"
        export LM_LICENSE_FILE
        log "LM_LICENSE_FILE overridden: $LM_LICENSE_FILE"
    fi

    if [ -n "$SALT_SERVER" ]; then
        SALT_LICENSE_SERVER="$SALT_SERVER"
        export SALT_LICENSE_SERVER
        log "SALT_LICENSE_SERVER overridden: $SALT_LICENSE_SERVER"
    fi

    # Verify the LDP vsim wrapper is reachable
    if ! command -v vsim > /dev/null 2>&1; then
        warn "'vsim' not found on PATH. Ensure the LDP environment is set up."
        warn "Check your .cshrc or equivalent shell profile for LDP setup."
    else
        log "Found vsim at: $(command -v vsim)"
    fi
}

# ---------------------------------------------------------------------------
# Mode: std_ldp — compile sim library if needed, then run standard qrun
# ---------------------------------------------------------------------------
setup_std_ldp() {
    log "Mode: std_ldp — standard QuestaSim via LDP with compiled sim library."

    # Locate cmpl_libs.tcl via FOUNDRY if set, else via BUILD_PATH, else LDP
    if [ -n "$BUILD_PATH" ]; then
        TCLSH_BIN="$BUILD_PATH/rtf/tcltk/linux/bin/tclsh"
        CMPL_SCRIPT="$BUILD_PATH/rtf/cae_library/simulation/scripts/cmpl_libs.tcl"
        QUESTA_BIN="$BUILD_PATH/rtf/tptools/questasim/linux/questasim/bin"
    else
        # Fall back to LDP wrappers directory as the sim_path proxy
        TCLSH_BIN="tclsh"
        LDP_LATEST="/lsc/ldp/release/latest"
        CMPL_SCRIPT="${LDP_LATEST}/wrappers/../../../rtf/cae_library/simulation/scripts/cmpl_libs.tcl"
        QUESTA_BIN="/lsc/ldp/release/latest/wrappers"
    fi

    if [ -d "$LIB_OUTPUT/$DEVICE" ]; then
        log "Sim library already exists at: $LIB_OUTPUT/$DEVICE — skipping compilation."
    else
        log "Compiling sim library for device '$DEVICE' into '$LIB_OUTPUT' ..."
        [ -f "$CMPL_SCRIPT" ] || \
            die "cmpl_libs.tcl not found at: $CMPL_SCRIPT"

        mkdir -p "$LIB_OUTPUT"

        "$TCLSH_BIN" "$CMPL_SCRIPT" \
            -sim_path "$QUESTA_BIN" \
            -sim_vendor siemens \
            -device "$DEVICE" \
            -target_path "$LIB_OUTPUT"

        log "Sim library compilation complete."

        # Check log for errors
        LIB_LOG="$LIB_OUTPUT/${DEVICE}.log"
        if [ -f "$LIB_LOG" ] && grep -qi "error" "$LIB_LOG"; then
            warn "Errors detected in library compilation log: $LIB_LOG"
            warn "Review the log before proceeding."
        fi
    fi

    # Inject -reflib into a temporary .f file wrapper so the user's
    # original .f file is not modified in place
    PATCHED_F="${F_FILE%.f}_with_reflib.f"
    {
        printf -- '-reflib %s\n' "$LIB_OUTPUT/$DEVICE"
        cat "$F_FILE"
    } > "$PATCHED_F"

    log "Patched .f file written: $PATCHED_F"
    F_FILE="$PATCHED_F"
}

# ---------------------------------------------------------------------------
# Build qrun command
# ---------------------------------------------------------------------------
build_qrun_cmd() {
    QRUN_CMD="qrun -f $F_FILE"

    #if [ "$GUI" -eq 1 ]; then
        #QRUN_CMD="$QRUN_CMD -gui"
        #log "GUI mode enabled."
    #else
        # Batch mode: suppress interactive pop-ups
        #QRUN_CMD="$QRUN_CMD -no_gui"
    #fi

    #if [ "$ACC" -eq 1 ]; then
        #QRUN_CMD="$QRUN_CMD +acc"
        #log "+acc flag enabled (all ports and parameters exposed)."
    #fi

    # Append log-all-signals and run directive
    #if [ -n "$RUN_TIME" ]; then
        #QRUN_CMD="$QRUN_CMD -do \"add log -r /*\" -do \"run $RUN_TIME\""
    #else
        #QRUN_CMD="$QRUN_CMD -do \"add log -r /*\" -do \"run -all\""
    #fi
}

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
log "========================================="
log "Lattice Radiant QuestaSim Simulation Run"
log "========================================="
log "Mode     : $MODE"
log ".f file  : $F_FILE"
#[ -n "$DEVICE"     ] && log "Device   : $DEVICE"
#[ -n "$BUILD_PATH" ] && log "Build    : $BUILD_PATH"
log ""

# Run setup for selected mode
case "$MODE" in
    oem_local) setup_oem_local ;;
    oem_ldp)   setup_oem_ldp   ;;
    std_ldp)   setup_std_ldp   ;;
esac

# Build the qrun command string
#build_qrun_cmd
. ${SCRIPT_DIR}/run.sh
export LIBPYTHON_LOC=$(cocotb-config --libpython)
run_qrun_cmd "$F_FILE"

#log ""
#log "Executing: $QRUN_CMD"
#log "-----------------------------------------"

# Use eval to correctly handle quoted -do arguments in the command string
#eval "$QRUN_CMD"
STATUS=$?

log "-----------------------------------------"
if [ "$STATUS" -eq 0 ]; then
    log "Simulation completed successfully."
else
    log "Simulation exited with status: $STATUS"
    log "Check the transcript above and any generated .log files for errors."
    log ""
    log "Common issues and fixes:"
    log "  License error  -> Verify LM_LICENSE_FILE and SALT_LICENSE_SERVER."
    log "                    Run: lmstat -a -c 1717@ldc-virtlic01 -f latticeqsim"
    log "  GSR_INST error -> Run under OEM mode, or compile device sim library."
    log "  Empty objects  -> Re-run with -a flag to add +acc."
    log "  cmpl_libs path -> Ensure FOUNDRY env variable points to rtf dir."
fi

exit "$STATUS"
