SHELL := /bin/bash

# ==============================================================================
# CoCoTB Makefile — lscc_fifo_dc LIFCL testbench
#
# Unified cross-platform testbench for Windows (Git Bash/MSYS2) and Linux.
# Environment and license variables are auto-detected by platform and can be
# overridden via:
#   1. Environment variables (export LM_LICENSE_FILE=...)
#   2. Local override file: env.mk (see env.mk.example)
#   3. Command-line flags (make LM_LICENSE_FILE=...)
#
# Usage:
#   make info                     # quick test plan outline / overview
#   make test                     # run full regression (Sim + DRC + Radiant Compilation)
#   make tc-fifodc-001            # run single testcase
#   make tg-01                    # run test group 1
#   make drc                      # run DRC validation suite (pytest)
#   make prj_create               # generate Radiant .rdf project
#   make prj_compile              # compile project via Radiant PAR
#   make clean                    # remove sim_build/ and results/
#   make clean_prj                # remove Radiant project and compilation artifacts
# ==============================================================================

# ── Platform Detection & Environment Defaults ─────────────────────────────────
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
else
    DETECTED_OS := $(shell uname -s 2>/dev/null || echo Linux)
endif

# Optional local overrides (git-ignored)
-include env.mk
-include local.mk

COCOTB_CONFIG ?= $(shell which cocotb-config 2>/dev/null || echo cocotb-config)

ifeq ($(DETECTED_OS),Windows)
    RADIANT_ROOT        ?= C:/lscc/radiant/2026.1
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= $(RADIANT_ROOT)/license/license.dat
    SALT_LICENSE_SERVER ?= $(RADIANT_ROOT)/license/license.dat
    RADIANTC            ?= $(shell which radiantc.exe 2>/dev/null || ( [ -x $(RADIANT_ROOT)/bin/nt64/radiantc.exe ] && echo $(RADIANT_ROOT)/bin/nt64/radiantc.exe ) || echo $(RADIANT_ROOT)/bin/nt64/pnmainc.exe)
    PNMAINC             ?= $(RADIANTC)
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/questasim/win64:$(RADIANT_ROOT)/bin/nt64:$(PATH)
    endif
else
    RADIANT_ROOT        ?= $(or $(RADIANT_HOME),/home/rel/ng2026_1p.release/rtf,/opt/lscc/radiant/2026.1)
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= 1850@ldc-virtlic02
    SALT_LICENSE_SERVER ?= 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b
    RADIANTC            ?= $(shell which radiantc 2>/dev/null || ( [ -x $(RADIANT_ROOT)/bin/lin64/radiantc ] && echo $(RADIANT_ROOT)/bin/lin64/radiantc ) || echo $(RADIANT_ROOT)/bin/lin64/pnmainc)
    PNMAINC             ?= $(RADIANTC)
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/tptools/questasim/linux/questasim/bin:$(RADIANT_ROOT)/questasim/linux_x86_64:$(RADIANT_ROOT)/bin/lin64:$(PATH)
    endif
    export LD_LIBRARY_PATH := $(RADIANT_ROOT)/bin/lin64/gnu:$(RADIANT_ROOT)/bin/lin64:$(RADIANT_ROOT)/ispfpga/bin/lin64$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
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
SIM_ARGS += -GENABLE_ALMOST_FULL_FLAG=$(ENABLE_ALMOST_FULL_FLAG)
SIM_ARGS += -GALMOST_FULL_ASSERTION=$(ALMOST_FULL_ASSERTION)
SIM_ARGS += -GALMOST_FULL_ASSERT_LVL=$(ALMOST_FULL_ASSERT_LVL)
SIM_ARGS += -GALMOST_FULL_DEASSERT_LVL=$(ALMOST_FULL_DEASSERT_LVL)
SIM_ARGS += -GENABLE_ALMOST_EMPTY_FLAG=$(ENABLE_ALMOST_EMPTY_FLAG)
SIM_ARGS += -GALMOST_EMPTY_ASSERTION=$(ALMOST_EMPTY_ASSERTION)
SIM_ARGS += -GALMOST_EMPTY_ASSERT_LVL=$(ALMOST_EMPTY_ASSERT_LVL)
SIM_ARGS += -GALMOST_EMPTY_DEASSERT_LVL=$(ALMOST_EMPTY_DEASSERT_LVL)
SIM_ARGS += -GENABLE_DATA_COUNT_WR=$(ENABLE_DATA_COUNT_WR)
SIM_ARGS += -GENABLE_DATA_COUNT_RD=$(ENABLE_DATA_COUNT_RD)
SIM_ARGS += -GFIFO_CONTROLLER=$(FIFO_CONTROLLER)
SIM_ARGS += -GFORCE_FAST_CONTROLLER=$(FORCE_FAST_CONTROLLER)
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
ifneq ($(_PYTHON_LIB_DIR),/usr/lib64)
ifneq ($(_PYTHON_LIB_DIR),/usr/lib)
LD_LIBRARY_PATH := $(_PYTHON_LIB_DIR)$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
endif
endif
endif
ifneq ($(wildcard $(RADIANT_ROOT)/bin/lin64/gnu),)
LD_LIBRARY_PATH := $(RADIANT_ROOT)/bin/lin64/gnu:$(RADIANT_ROOT)/bin/lin64:$(RADIANT_ROOT)/ispfpga/bin/lin64$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
endif
export LD_LIBRARY_PATH
export LIBPYTHON_LOC    := $(shell $(COCOTB_CONFIG) --libpython 2>/dev/null)
export PYGPI_PYTHON_BIN := $(shell $(COCOTB_CONFIG) --python-bin 2>/dev/null || which python3 2>/dev/null)
endif

COMPILE_ARGS += -sv

# Ensure results/ exists before vsim writes the WLF
.PHONY: results_dir
results_dir:
	@mkdir -p $(RESULTS_DIR)

# ── Cocotb Simulation Flow ───────────────────────────────────────────────────
COCOTB_MAKEFILES_DIR := $(shell $(COCOTB_CONFIG) --makefiles 2>/dev/null)
ifneq ($(COCOTB_MAKEFILES_DIR),)
COCOTB_MAKEFILE := $(COCOTB_MAKEFILES_DIR)/Makefile.sim
ifneq ($(wildcard $(COCOTB_MAKEFILE)),)
include $(COCOTB_MAKEFILE)
sim: results_dir
endif
endif

# Override clean to also remove results/ and QuestaSim runtime artifacts
clean:: clean_prj
	rm -rf $(RESULTS_DIR)
	rm -rf qrun.out
	rm -rf sim_build
	rm -f  transcript modelsim.ini
	find $(CURDIR)/src $(CURDIR)/../scripts -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ── summary ───────────────────────────────────────────────────────────────────
.PHONY: summary
summary:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/summarize.py $(if $(MD),$(RESULTS_DIR)/summary.md)

# ── drc ───────────────────────────────────────────────────────────────────────
.PHONY: drc
drc:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py DRC

# ── test — run full test suite (Sim + DRC + Radiant Compilation) ──────────────
.PHONY: test
test: | results_dir
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py test

# ── Overview / Info ───────────────────────────────────────────────────────────
.PHONY: info
info:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py info

# ── TC / TG named targets ─────────────────────────────────────────────────────
tc-%:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py $*

tg-%:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py TG-$*

g%:
	@IP_ROOT=$(CURDIR) python3 $(CURDIR)/../scripts/run_tc.py G$*

# ── Radiant Project Generation & Compilation ─────────────────────────────────
PRJ_NAME ?= lscc_fifo_dc
PRJ_DEV  ?= LFCPNX-100-9BFG484C
PRJ_IMPL ?= impl_1
PRJ_SYN  ?= synplify
PRJ_DIR  ?= $(CURDIR)/proj

.PHONY: prj_create create_prj project
prj_create create_prj project:
	@echo "Creating Radiant project $(PRJ_NAME).rdf for device $(PRJ_DEV)..."
	@mkdir -p $(PRJ_DIR)
	@echo 'prj_create -name $(PRJ_NAME) -dev "$(PRJ_DEV)" -impl $(PRJ_IMPL) -synthesis $(PRJ_SYN)' > $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_add_source $(CURDIR)/rtl/lscc_fifo_dc.v' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_add_source $(CURDIR)/synth/lscc_fifo_dc_synth_wrap.v' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_set_top_module "lscc_fifo_dc_synth_wrap"' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_save' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_close' >> $(PRJ_DIR)/create_prj.tcl
	cd $(PRJ_DIR) && $(PNMAINC) create_prj.tcl
	@rm -f $(PRJ_DIR)/create_prj.tcl
	@echo "Radiant project $(PRJ_NAME).rdf created successfully in $(PRJ_DIR)."

.PHONY: prj_compile compile_prj radiant_compile
prj_compile compile_prj radiant_compile:
	@echo "Compiling Radiant project $(PRJ_NAME).rdf (PAR)..."
	@echo 'prj_open $(PRJ_NAME).rdf' > $(PRJ_DIR)/run_par.tcl
	@echo 'prj_run PAR -forceAll' >> $(PRJ_DIR)/run_par.tcl
	@echo 'prj_close' >> $(PRJ_DIR)/run_par.tcl
	cd $(PRJ_DIR) && $(PNMAINC) run_par.tcl
	@rm -f $(PRJ_DIR)/run_par.tcl
	@echo "Radiant compilation finished."

.PHONY: clean_prj
clean_prj:
	rm -rf $(PRJ_DIR)
	rm -f  $(CURDIR)/pnmainc.log $(CURDIR)/pnmainc.tcl
