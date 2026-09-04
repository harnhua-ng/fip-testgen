SHELL := /bin/bash

# ==============================================================================
# CoCoTB Makefile — lscc_pll LIFCL testbench
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
#   make tc-pll-001               # run single testcase
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
COCOTB_TEST_MODULES = tb_pll

# RTL Sources
VERILOG_SOURCES  = $(CURDIR)/rtl/lscc_pll.v
VERILOG_SOURCES += $(CURDIR)/testbench/testgen_top.v

# Python testbench
PYTHONPATH := $(CURDIR)/src:$(CURDIR)/../scripts$(if $(PYTHONPATH),:$(PYTHONPATH))
export PYTHONPATH

# DUT Parameters
FVCO                ?= 800.0
CLKI_FREQ           ?= 100.0
CLKOP_FREQ_ACTUAL   ?= 100.0
CLKOS_FREQ_ACTUAL   ?= 100.0
CLKOS2_FREQ_ACTUAL  ?= 100.0
CLKOS3_FREQ_ACTUAL  ?= 100.0
CLKOS4_FREQ_ACTUAL  ?= 100.0
CLKOS5_FREQ_ACTUAL  ?= 100.0
CLKOS_EN            ?= 0
CLKOS2_EN           ?= 0
CLKOS3_EN           ?= 0
CLKOS4_EN           ?= 0
CLKOS5_EN           ?= 0
FRAC_N_EN           ?= 0
SS_EN               ?= 0
DYN_PORTS_EN        ?= 0
PLL_RST             ?= 1
LOCK_EN             ?= 1
PLL_LOCK_STICKY     ?= 0
LEGACY_EN           ?= 0
LMMI_EN             ?= 0
APB_EN              ?= 0
APB_SOFT_REG_EN     ?= 0
POWERDOWN_EN        ?= 0
EN_REFCLK_MON       ?= 0
FAMILY              ?= LIFCL
DEVICE_FAMILY       ?= lifcl

export FVCO CLKI_FREQ CLKOP_FREQ_ACTUAL CLKOS_FREQ_ACTUAL CLKOS2_FREQ_ACTUAL CLKOS3_FREQ_ACTUAL CLKOS4_FREQ_ACTUAL CLKOS5_FREQ_ACTUAL
export CLKOS_EN CLKOS2_EN CLKOS3_EN CLKOS4_EN CLKOS5_EN FRAC_N_EN SS_EN DYN_PORTS_EN PLL_RST LOCK_EN PLL_LOCK_STICKY LEGACY_EN
export LMMI_EN APB_EN APB_SOFT_REG_EN POWERDOWN_EN EN_REFCLK_MON FAMILY DEVICE_FAMILY

ifdef TESTCASE
export COCOTB_TESTCASE := $(TESTCASE)
endif

# vsim generics
SIM_ARGS += -GCLKI_FREQ=$(CLKI_FREQ)
SIM_ARGS += -GCLKOP_FREQ_ACTUAL=$(CLKOP_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS_FREQ_ACTUAL=$(CLKOS_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS2_FREQ_ACTUAL=$(CLKOS2_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS3_FREQ_ACTUAL=$(CLKOS3_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS4_FREQ_ACTUAL=$(CLKOS4_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS5_FREQ_ACTUAL=$(CLKOS5_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS_EN=$(CLKOS_EN)
SIM_ARGS += -GCLKOS2_EN=$(CLKOS2_EN)
SIM_ARGS += -GCLKOS3_EN=$(CLKOS3_EN)
SIM_ARGS += -GCLKOS4_EN=$(CLKOS4_EN)
SIM_ARGS += -GCLKOS5_EN=$(CLKOS5_EN)
SIM_ARGS += -GFRAC_N_EN=$(FRAC_N_EN)
SIM_ARGS += -GSS_EN=$(SS_EN)
SIM_ARGS += -GDYN_PORTS_EN=$(DYN_PORTS_EN)
SIM_ARGS += -GLOCK_EN=$(LOCK_EN)
SIM_ARGS += -GPLL_LOCK_STICKY=$(PLL_LOCK_STICKY)
SIM_ARGS += -GLMMI_EN=$(LMMI_EN)
SIM_ARGS += -GAPB_EN=$(APB_EN)
SIM_ARGS += -GAPB_SOFT_REG_EN=$(APB_SOFT_REG_EN)
SIM_ARGS += -GPOWERDOWN_EN=$(POWERDOWN_EN)
SIM_ARGS += -GEN_REFCLK_MON=$(EN_REFCLK_MON)
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
PRJ_NAME ?= lscc_pll
PRJ_DEV  ?= LFCPNX-100-9BFG484C
PRJ_IMPL ?= impl_1
PRJ_SYN  ?= synplify
PRJ_DIR  ?= $(CURDIR)/proj

.PHONY: prj_create create_prj project
prj_create create_prj project:
	@echo "Creating Radiant project $(PRJ_NAME).rdf for device $(PRJ_DEV)..."
	@mkdir -p $(PRJ_DIR)
	@echo 'prj_create -name $(PRJ_NAME) -dev "$(PRJ_DEV)" -impl $(PRJ_IMPL) -synthesis $(PRJ_SYN)' > $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_add_source $(CURDIR)/rtl/lscc_pll.v' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_add_source $(CURDIR)/synth/lscc_pll_synth_wrap.v' >> $(PRJ_DIR)/create_prj.tcl
	@echo 'prj_set_top_module "lscc_pll_synth_wrap"' >> $(PRJ_DIR)/create_prj.tcl
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
