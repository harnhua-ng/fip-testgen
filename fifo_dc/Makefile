SHELL := /bin/bash

# ==============================================================================
# CoCoTB Makefile — lscc_fifo_dc LIFCL testbench
# ==============================================================================

# ── Platform Detection & Environment Defaults ─────────────────────────────────
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
    DETECTED_OS := $(shell uname -s 2>/dev/null || echo Linux)
endif

# Optional local overrides
-include env.mk
-include local.mk

COCOTB_CONFIG ?= $(shell which cocotb-config 2>/dev/null || ( [ -x $(CURDIR)/../.venv/bin/cocotb-config ] && echo $(CURDIR)/../.venv/bin/cocotb-config ) || ( [ -x $(CURDIR)/.venv/bin/cocotb-config ] && echo $(CURDIR)/.venv/bin/cocotb-config ) || ( [ -x $(CURDIR)/.venv/Scripts/cocotb-config.exe ] && echo $(CURDIR)/.venv/Scripts/cocotb-config.exe ) || echo cocotb-config)

ifeq ($(DETECTED_OS),Windows)
    RADIANT_ROOT        ?= C:/lscc/radiant/2026.1
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= $(RADIANT_ROOT)/license/license.dat
    SALT_LICENSE_SERVER ?= $(RADIANT_ROOT)/license/license.dat
    ifneq ($(wildcard $(CURDIR)/.venv/Scripts),)
        export PATH := $(CURDIR)/.venv/Scripts:$(PATH)
    endif
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/questasim/win64:$(RADIANT_ROOT)/bin/nt64:$(PATH)
    endif
else
    RADIANT_ROOT        ?= /home/rel/ng2026_2.82/rtf
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= 1717@ldc-virtlic01:1717@ldc-oemlic01
    SALT_LICENSE_SERVER ?= 1717@ldc-virtlic01:1717@ldc-oemlic
    ifneq ($(wildcard $(CURDIR)/../.venv/bin),)
        export PATH := $(CURDIR)/../.venv/bin:$(PATH)
    endif
    ifneq ($(wildcard $(CURDIR)/.venv/bin),)
        export PATH := $(CURDIR)/.venv/bin:$(PATH)
    endif
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/tptools/questasim/linux/questasim/bin:$(RADIANT_ROOT)/questasim/linux_x86_64:$(RADIANT_ROOT)/bin/lin64:$(PATH)
    endif
endif

export FOUNDRY
export LM_LICENSE_FILE
export SALT_LICENSE_SERVER

# ── Simulator Configuration ───────────────────────────────────────────────────
SIM                 ?= questa
TOPLEVEL_LANG       ?= verilog
COCOTB_TOPLEVEL     = testgen_top
COCOTB_TEST_MODULES = tb_fifo_dc

# RTL Sources
VERILOG_SOURCES  = $(CURDIR)/rtl/lscc_fifo_dc.v
VERILOG_SOURCES += $(CURDIR)/testbench/testgen_top.v

# Python testbench
PYTHONPATH := $(CURDIR)/src:$(CURDIR)/../scripts$(if $(PYTHONPATH),:$(PYTHONPATH))
export PYTHONPATH

# DUT Parameters
IMPLEMENTATION            ?= EBR
WADDR_DEPTH               ?= 512
WADDR_WIDTH               ?= 9
WDATA_WIDTH               ?= 36
RADDR_DEPTH               ?= 512
RADDR_WIDTH               ?= 9
RDATA_WIDTH               ?= 36
REGMODE                   ?= reg
OREG_IMPLEMENTATION       ?= LUT
RESETMODE                 ?= async
ENABLE_ALMOST_FULL_FLAG   ?= TRUE
ENABLE_ALMOST_EMPTY_FLAG  ?= TRUE
INIT_FILE                 ?= none
INIT_MODE                 ?= none
INIT_FILE_FORMAT          ?= binary
ALMOST_FULL_ASSERTION     ?= static-dual
ALMOST_FULL_ASSERT_LVL    ?= 511
ALMOST_FULL_DEASSERT_LVL  ?= 510
ALMOST_EMPTY_ASSERTION    ?= static-dual
ALMOST_EMPTY_ASSERT_LVL   ?= 1
ALMOST_EMPTY_DEASSERT_LVL ?= 2
ECC_ENABLE                ?= 0
ENABLE_DATA_COUNT_WR      ?= FALSE
ENABLE_DATA_COUNT_RD      ?= FALSE
FAMILY                    ?= LIFCL
FIFO_CONTROLLER           ?= FABRIC
FORCE_FAST_CONTROLLER     ?= 0
FWFT                      ?= 0
DEVICE_FAMILY             ?= lifcl

export IMPLEMENTATION WADDR_DEPTH WADDR_WIDTH WDATA_WIDTH RADDR_DEPTH RADDR_WIDTH RDATA_WIDTH
export REGMODE OREG_IMPLEMENTATION RESETMODE ENABLE_ALMOST_FULL_FLAG ENABLE_ALMOST_EMPTY_FLAG
export INIT_FILE INIT_MODE INIT_FILE_FORMAT ALMOST_FULL_ASSERTION ALMOST_FULL_ASSERT_LVL ALMOST_FULL_DEASSERT_LVL
export ALMOST_EMPTY_ASSERTION ALMOST_EMPTY_ASSERT_LVL ALMOST_EMPTY_DEASSERT_LVL ECC_ENABLE
export ENABLE_DATA_COUNT_WR ENABLE_DATA_COUNT_RD FAMILY FIFO_CONTROLLER FORCE_FAST_CONTROLLER FWFT DEVICE_FAMILY

# Set KEEP_WORK=1 to preserve results/tc-XX-YY/work after each run (large; off by default).
KEEP_WORK ?= 0
export KEEP_WORK

ifdef TESTCASE
export COCOTB_TESTCASE := $(TESTCASE)
endif

# vsim generics
SIM_ARGS += -GFAMILY=$(FAMILY)
SIM_ARGS += -GIMPLEMENTATION=$(IMPLEMENTATION)
SIM_ARGS += -GWADDR_DEPTH=$(WADDR_DEPTH)
SIM_ARGS += -GWADDR_WIDTH=$(WADDR_WIDTH)
SIM_ARGS += -GWDATA_WIDTH=$(WDATA_WIDTH)
SIM_ARGS += -GRADDR_DEPTH=$(RADDR_DEPTH)
SIM_ARGS += -GRADDR_WIDTH=$(RADDR_WIDTH)
SIM_ARGS += -GRDATA_WIDTH=$(RDATA_WIDTH)
SIM_ARGS += -GREGMODE=$(REGMODE)
SIM_ARGS += -GRESETMODE=$(RESETMODE)
SIM_ARGS += -GFIFO_CONTROLLER=$(FIFO_CONTROLLER)
SIM_ARGS += -GECC_ENABLE=$(ECC_ENABLE)
SIM_ARGS += -GFWFT=$(FWFT)
SIM_ARGS += -L $(DEVICE_FAMILY)

RESULTS_DIR := $(CURDIR)/results
WLF_FILE    ?= $(RESULTS_DIR)/sim.wlf
SIM_ARGS    += -voptargs="-access=rw+/. +acc" -suppress 12130
SIM_ARGS    += -wlf $(WLF_FILE)
SIM_ARGS    += -do "log -r /*; run -all; quit"

ifneq ($(DETECTED_OS),Windows)
_PYTHON_LIB_DIR := $(shell dirname $$($(COCOTB_CONFIG) --libpython 2>/dev/null) 2>/dev/null)
ifneq ($(_PYTHON_LIB_DIR),)
LD_LIBRARY_PATH := $(_PYTHON_LIB_DIR)$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
export LD_LIBRARY_PATH
endif
export LIBPYTHON_LOC    := $(shell $(COCOTB_CONFIG) --libpython 2>/dev/null)
export PYGPI_PYTHON_BIN := $(shell $(COCOTB_CONFIG) --python-bin 2>/dev/null || which python3 2>/dev/null)
endif

COMPILE_ARGS += -sv

# ── Cocotb Simulation Flow ───────────────────────────────────────────────────
COCOTB_MAKEFILE := $(shell $(COCOTB_CONFIG) --makefiles 2>/dev/null)/Makefile.sim
include $(COCOTB_MAKEFILE)

# ── Test Runner Targets ───────────────────────────────────────────────────────
.PHONY: drc clean_results all_sim_tests

drc:
	pytest $(CURDIR)/src/test_drc.py -v

clean_results:
	rm -rf $(RESULTS_DIR)/*.wlf $(RESULTS_DIR)/*.log $(RESULTS_DIR)/*.xml

# Convenience targets
tc-003:
	$(MAKE) FIFO_CONTROLLER=HARD_IP WADDR_DEPTH=512 WDATA_WIDTH=18 RADDR_DEPTH=512 RDATA_WIDTH=18 TESTCASE=tc_003_hard_ip_minimal_sim

tc-004:
	$(MAKE) FIFO_CONTROLLER=FABRIC IMPLEMENTATION=EBR WADDR_DEPTH=512 WDATA_WIDTH=18 RADDR_DEPTH=512 RDATA_WIDTH=18 TESTCASE=tc_004_fabric_ebr_minimal_sim

tc-005:
	$(MAKE) FIFO_CONTROLLER=HARD_IP WADDR_DEPTH=512 WDATA_WIDTH=18 RADDR_DEPTH=512 RDATA_WIDTH=18 TESTCASE=tc_005_data_integrity_hard_ip_fill_drain

tc-006:
	$(MAKE) FIFO_CONTROLLER=FABRIC IMPLEMENTATION=EBR WADDR_DEPTH=512 WDATA_WIDTH=18 RADDR_DEPTH=512 RDATA_WIDTH=18 ENABLE_DATA_COUNT_WR=TRUE ENABLE_DATA_COUNT_RD=TRUE TESTCASE=tc_006_data_integrity_fabric_ebr_fill_drain

tc-010:
	$(MAKE) FIFO_CONTROLLER=HARD_IP FWFT=1 WADDR_DEPTH=512 WDATA_WIDTH=18 RADDR_DEPTH=512 RDATA_WIDTH=18 REGMODE=reg TESTCASE=tc_010_fwft_mode
