# ==============================================================================
# CoCoTB Makefile — lscc_rom LIFCL testbench
#
# The Radiant environment must be sourced before invoking make:
#   source ~/setup_radiant.sh ng2026_2.82
#
# Usage:
#   make                          # default: noreg / 36b×512 / sync / all_one
#   make REGMODE=reg RADDR_DEPTH=512   # override individual parameters
#   make TESTCASE=tc_01_01_sequential_read_noreg  # single test case
#   make all_configs              # run all 7 required parameter combinations
#   make noreg_36_512_sync        # run one named configuration directly
#   make clean                    # remove sim_build/ and results/
# ==============================================================================

# ── Simulator ─────────────────────────────────────────────────────────────────
# cocotb drives vlog (compile) + vsim (simulate) — functionally identical to qrun.
SIM              ?= questa
TOPLEVEL_LANG    ?= verilog
# name of toplevel module in the design
COCOTB_TOPLEVEL  = testgen_top
# basename of the Python test file(s)
COCOTB_TEST_MODULES = tb_rom

# RTL sources
VERILOG_SOURCES  = $(CURDIR)/rtl/lscc_rom.v
VERILOG_SOURCES += $(CURDIR)/testbench/testgen_top.v

# Python testbench
PYTHONPATH := $(CURDIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))
export PYTHONPATH

# DUT parameters
RDATA_WIDTH   ?= 36
RADDR_DEPTH   ?= 512
REGMODE       ?= noreg
RESETMODE     ?= sync
OUTPUT_CLK_EN ?= 0
ECC_ENABLE    ?= 0
INIT_MODE     ?= all_one
INIT_FILE     ?= $(CURDIR)/testbench/rom_init.hex
export RDATA_WIDTH RADDR_DEPTH REGMODE RESETMODE OUTPUT_CLK_EN ECC_ENABLE INIT_MODE INIT_FILE

# Optional: run a single test case
# Example: make TESTCASE=tc_01_01_sequential_read_noreg
ifdef TESTCASE
export COCOTB_TESTCASE := $(TESTCASE)
endif

# vsim arguments
# Verilog parameter generics (-GRDATA_WIDTH=... etc.)
SIM_ARGS += -GRDATA_WIDTH=$(RDATA_WIDTH)
SIM_ARGS += -GRADDR_DEPTH=$(RADDR_DEPTH)
SIM_ARGS += -GREGMODE=$(REGMODE)
SIM_ARGS += -GRESETMODE=$(RESETMODE)
SIM_ARGS += -GOUTPUT_CLK_EN=$(OUTPUT_CLK_EN)
SIM_ARGS += -GECC_ENABLE=$(ECC_ENABLE)
SIM_ARGS += -GINIT_MODE=$(INIT_MODE)
SIM_ARGS += -GINIT_FILE=$(INIT_FILE)

# device simulation library
SIM_ARGS += -L lifcl

# Expose all ports/parameters for waveform capture in the classic format

# WLF output
RESULTS_DIR := $(CURDIR)/results
_WLF_TAG    := $(REGMODE)_$(RDATA_WIDTH)b_d$(RADDR_DEPTH)_$(RESETMODE)
_WLF_TC     := $(if $(TESTCASE),_$(TESTCASE),_all)
SIM_ARGS    += -voptargs="-access=rw+/. +acc" -suppress 12130
SIM_ARGS    += -wlf $(RESULTS_DIR)/$(_WLF_TAG)$(_WLF_TC).wlf

# run simulation
SIM_ARGS    += -do "log -r /*; run -all; quit"

# libpython RPATH fix
# RHEL8 ships libpython3.x.so.1.0 but not the unversioned .so symlink.
# Setting LD_LIBRARY_PATH at make-time propagates to vsim's subprocess.
_PYTHON_LIB_DIR := $(shell dirname $(shell cocotb-config --libpython))
LD_LIBRARY_PATH := $(_PYTHON_LIB_DIR)$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
export LD_LIBRARY_PATH
export LIBPYTHON_LOC    := $(shell cocotb-config --libpython)
export PYGPI_PYTHON_BIN := $(shell which python3)

# Lattice Questa license servers
export LM_LICENSE_FILE     := 1850@ldc-virtlic02
export SALT_LICENSE_SERVER := 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b

# vlog compile flags
COMPILE_ARGS += -sv

# Pull in cocotb's Questa Makefile rules
# This provides the 'sim', 'compile', and 'clean' targets automatically.
include $(shell cocotb-config --makefiles)/Makefile.sim

# Ensure results/ exists before vsim writes the WLF
.PHONY: results_dir
sim: results_dir
results_dir:
	@mkdir -p $(RESULTS_DIR)

# Override clean to also remove results/
clean::
	rm -rf $(RESULTS_DIR)

# ==============================================================================
# all_configs — run every required parameter combination in sequence
#
# Target names encode: REGMODE_RDATA_RADDR_RESETMODE
# All other parameters default (OUTPUT_CLK_EN=0, ECC_ENABLE=0, INIT_MODE=all_one).
#
# Each config gets its own SIM_BUILD directory so parallel execution is safe
# and compile artifacts from one run do not bleed into another.
#
# Add entries here as TG-06 through TG-09 are implemented and need new combos.
# ==============================================================================
ALL_CONFIGS := \
    noreg_36_512_sync   \
    reg_36_512_sync     \
    reg_36_512_async    \
    reg_18_1024_sync    \
    noreg_9_2048_sync   \
    noreg_18_1024_sync  \
    reg_36_1024_sync

# For each config name, extract the four fields by splitting on underscore.
# noreg_36_512_sync → word1=noreg  word2=36  word3=512  word4=sync
define RUN_CONFIG
.PHONY: $(1)
$(1):
	@echo ""
	@echo "================================================================"
	@echo " Config: $(1)"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=$(word 1,$(subst _, ,$(1))) \
		RDATA_WIDTH=$(word 2,$(subst _, ,$(1))) \
		RADDR_DEPTH=$(word 3,$(subst _, ,$(1))) \
		RESETMODE=$(word 4,$(subst _, ,$(1))) \
		SIM_BUILD=$(CURDIR)/sim_build/$(1)
endef

$(foreach cfg,$(ALL_CONFIGS),$(eval $(call RUN_CONFIG,$(cfg))))

.PHONY: all_configs
all_configs: $(ALL_CONFIGS)
	@echo ""
	@echo "================================================================"
	@echo " All $(words $(ALL_CONFIGS)) configurations completed"
	@echo " WLF files are in: $(RESULTS_DIR)/"
	@echo "================================================================"
