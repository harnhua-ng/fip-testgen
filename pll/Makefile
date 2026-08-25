SHELL := /bin/bash

# ==============================================================================
# CoCoTB Makefile — lscc_pll LIFCL testbench
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

# Set KEEP_WORK=1 to preserve results/tc-XX-YY/work after each run (large; off by default).
KEEP_WORK ?= 0
export KEEP_WORK

ifdef TESTCASE
export COCOTB_TESTCASE := $(TESTCASE)
endif

# vsim generics
SIM_ARGS += -GCLKI_FREQ=$(CLKI_FREQ)
SIM_ARGS += -GCLKOP_FREQ_ACTUAL=$(CLKOP_FREQ_ACTUAL)
SIM_ARGS += -GCLKOS_EN=$(CLKOS_EN)
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

# ── Test Targets ──────────────────────────────────────────────────────────────
.PHONY: drc clean_results

drc:
	pytest $(CURDIR)/src/test_drc.py -v

clean_results:
	rm -rf $(RESULTS_DIR)/*.wlf $(RESULTS_DIR)/*.log $(RESULTS_DIR)/*.xml

tc-002:
	$(MAKE) CLKI_FREQ=100.0 CLKOP_FREQ_ACTUAL=125.0 LOCK_EN=1 TESTCASE=tc_lifcl_002_integer_n_lock_clkop_freq

tc-004:
	$(MAKE) FRAC_N_EN=1 CLKI_FREQ=100.0 CLKOP_FREQ_ACTUAL=133.333 LOCK_EN=1 TESTCASE=tc_lifcl_004_fractional_n_synthesis

tc-017:
	$(MAKE) LMMI_EN=1 TESTCASE=tc_lifcl_017_lmmi_slave_read_write

tc-018:
	$(MAKE) APB_EN=1 TESTCASE=tc_lifcl_018_apb_slave_dword_mapping
