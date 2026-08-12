#!/usr/bin/env bash
# run.sh — builds and executes the qrun command for lscc_rom CoCoTB tests.
# Called by run_qsim.sh after it has set up the environment.
# All parameters are read from environment variables; set defaults here.

run_qrun_cmd() {
    local FILE_LIST="$1"
    local DEV_LIB="${2:-lifcl}"  # Defaults to lifcl if not provided

    # Parameters with defaults. Callers set these via env before sourcing run.sh.
    : "${REGMODE:=noreg}"
    : "${RDATA_WIDTH:=36}"
    : "${RADDR_DEPTH:=512}"
    : "${RESETMODE:=sync}"
    : "${OUTPUT_CLK_EN:=0}"
    : "${ECC_ENABLE:=0}"
    : "${INIT_MODE:=all_one}"

    export COCOTB_TEST_MODULES=tb_lscc_rom
    export PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}"
    export LIBPYTHON_LOC=$(cocotb-config --libpython)
    # Point cocotb to your python binary
    export PYGPI_PYTHON_BIN=$(which python)
    # Path routing fixes for Questa simulation sandbox
    PYTHON_LIB_DIR=$(dirname "$(cocotb-config --libpython)")
    export LD_LIBRARY_PATH="${PYTHON_LIB_DIR}:${LD_LIBRARY_PATH}"

    COCOTB_VPI=$(cocotb-config --lib-name-path vpi questa)
    WLF_NAME="${COCOTB_TEST_MODULES}_${COCOTB_TEST_CASE:-all}.wlf"

    export RDATA_WIDTH RADDR_DEPTH REGMODE RESETMODE OUTPUT_CLK_EN ECC_ENABLE INIT_MODE

    qrun -f "${FILE_LIST}" \
         -L "${DEV_LIB}" \
         -wlf "${WLF_NAME}" \
         -GRDATA_WIDTH="${RDATA_WIDTH}" \
         -GRADDR_DEPTH="${RADDR_DEPTH}" \
         -GREGMODE="${REGMODE}" \
         -GRESETMODE="${RESETMODE}" \
         -GOUTPUT_CLK_EN="${OUTPUT_CLK_EN}" \
         -GECC_ENABLE="${ECC_ENABLE}" \
         -GINIT_MODE="${INIT_MODE}" \
         -pli "${COCOTB_VPI}" \
         -do "log -r /*; run -all; quit"

    #COCOTB_TEST_MODULES=tb_lscc_rom_reset \
    #qrun -f ${FILE_LIST} \
        #-GRDATA_WIDTH=36 -GRADDR_DEPTH=512 -GREGMODE=noreg \
        #-GRESETMODE=sync -GOUTPUT_CLK_EN=0 -GECC_ENABLE=0 -GINIT_MODE=all_one \
        #-pli "/lsc/scratch/sw_qor/QoR_User/hng/fip/lscc_rom/.venv/lib/python3.11/site-packages/cocotb/libs/libcocotbvpi_modelsim.so" \
        #-wlf tb_lscc_rom_reset.wlf \
        #-do "log -r /*; run -all; quit"

}
