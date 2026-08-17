SHELL := /bin/bash

# ==============================================================================
# CoCoTB Makefile — lscc_rom LIFCL testbench
#
# Unified cross-platform testbench for Windows (Git Bash/MSYS2) and Linux.
# Environment and license variables are auto-detected by platform and can be
# overridden via:
#   1. Environment variables (export LM_LICENSE_FILE=...)
#   2. Local override file: env.mk (see env.mk.example)
#   3. Command-line flags (make LM_LICENSE_FILE=...)
#
# Usage:
#   make                          # default: noreg / 36b×512 / sync / all_one
#   make REGMODE=reg RADDR_DEPTH=512   # override individual parameters
#   make TESTCASE=tc_01_01_sequential_read_noreg  # single test case
#   make all_configs              # run all required parameter combinations
#   make noreg_36_512_sync        # run one named configuration directly
#   make clean                    # remove sim_build/ and results/
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

ifeq ($(DETECTED_OS),Windows)
    RADIANT_ROOT        ?= C:/lscc/radiant/2026.1
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= $(RADIANT_ROOT)/license/license.dat
    SALT_LICENSE_SERVER ?= $(RADIANT_ROOT)/license/license.dat
    # Prepend QuestaSim and Radiant tools to PATH if not already in PATH
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/questasim/win64:$(RADIANT_ROOT)/bin/nt64:$(PATH)
    endif
else
    RADIANT_ROOT        ?= /opt/lscc/radiant/2026.1
    FOUNDRY             ?= $(RADIANT_ROOT)/ispfpga
    LM_LICENSE_FILE     ?= 1850@ldc-virtlic02
    SALT_LICENSE_SERVER ?= 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b
    # Prepend QuestaSim and Radiant tools to PATH if not already in PATH
    ifeq ($(findstring questasim,$(PATH)),)
        export PATH := $(RADIANT_ROOT)/questasim/linux_x86_64:$(RADIANT_ROOT)/bin/lin64:$(PATH)
    endif
endif

export FOUNDRY
export LM_LICENSE_FILE
export SALT_LICENSE_SERVER

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
INIT_MODE        ?= all_one
INIT_FILE        ?= $(CURDIR)/testbench/rom_init.hex
INIT_FILE_FORMAT ?= hex
DEVICE_FAMILY    ?= lifcl
FAMILY          ?= common
export RDATA_WIDTH RADDR_DEPTH REGMODE RESETMODE OUTPUT_CLK_EN ECC_ENABLE INIT_MODE INIT_FILE INIT_FILE_FORMAT DEVICE_FAMILY FAMILY

# Optional: run a single test case
# Example: make TESTCASE=tc_01_01_sequential_read_noreg
ifdef TESTCASE
export COCOTB_TESTCASE := $(TESTCASE)
endif

# vsim arguments
# Verilog parameter generics (-GRDATA_WIDTH=... etc.)
SIM_ARGS += -GFAMILY=$(FAMILY)
SIM_ARGS += -GRDATA_WIDTH=$(RDATA_WIDTH)
SIM_ARGS += -GRADDR_DEPTH=$(RADDR_DEPTH)
SIM_ARGS += -GREGMODE=$(REGMODE)
SIM_ARGS += -GRESETMODE=$(RESETMODE)
SIM_ARGS += -GOUTPUT_CLK_EN=$(OUTPUT_CLK_EN)
SIM_ARGS += -GECC_ENABLE=$(ECC_ENABLE)
SIM_ARGS += -GINIT_MODE=$(INIT_MODE)
SIM_ARGS += -GINIT_FILE=$(INIT_FILE)

# device simulation library (override with DEVICE_FAMILY=lfd2nx, lfcpnx, lfmxo5, etc.)
SIM_ARGS += -L $(DEVICE_FAMILY)

# Expose all ports/parameters for waveform capture in the classic format

# WLF output
RESULTS_DIR := $(CURDIR)/results
_WLF_TAG    := $(REGMODE)_$(RDATA_WIDTH)b_d$(RADDR_DEPTH)_$(RESETMODE)
_WLF_TC     := $(if $(TESTCASE),_$(TESTCASE),_all)
WLF_FILE    ?= $(RESULTS_DIR)/$(_WLF_TAG)$(_WLF_TC).wlf
SIM_ARGS    += -voptargs="-access=rw+/. +acc" -suppress 12130
SIM_ARGS    += -wlf $(WLF_FILE)

# run simulation
SIM_ARGS    += -do "log -r /*; run -all; quit"

# libpython RPATH fix (Linux only)
# RHEL8 ships libpython3.x.so.1.0 but not the unversioned .so symlink.
# Setting LD_LIBRARY_PATH at make-time propagates to vsim's subprocess.
ifneq ($(DETECTED_OS),Windows)
_PYTHON_LIB_DIR := $(shell dirname $$(cocotb-config --libpython 2>/dev/null) 2>/dev/null)
ifneq ($(_PYTHON_LIB_DIR),)
LD_LIBRARY_PATH := $(_PYTHON_LIB_DIR)$(if $(LD_LIBRARY_PATH),:$(LD_LIBRARY_PATH))
export LD_LIBRARY_PATH
endif
export LIBPYTHON_LOC    := $(shell cocotb-config --libpython 2>/dev/null)
export PYGPI_PYTHON_BIN := $(shell which python3 2>/dev/null)
endif

# vlog compile flags
COMPILE_ARGS += -sv

# Flow selection: cocotb (Python) or rtl (pure Verilog tb_rom.v)
FLOW ?= cocotb

# Tools for direct RTL simulation
VLOG := vlog
VSIM := vsim
TESTBENCH := $(CURDIR)/testbench/tb_rom.v

# Optional: test case selection for RTL (+TC=) or cocotb (TESTCASE=)
TC ?=
ifdef TC
SIM_ARGS += +TC=$(TC)
endif

# Ensure results/ exists before vsim writes the WLF
.PHONY: results_dir
results_dir:
	@mkdir -p $(RESULTS_DIR)

ifeq ($(FLOW),rtl)
# ── Direct Verilog simulation flow ────────────────────────────────────────────
.PHONY: sim
sim: results_dir
	@mkdir -p $(SIM_BUILD)
	vlib $(SIM_BUILD)/work
	$(VLOG) -work $(SIM_BUILD)/work $(COMPILE_ARGS) $(VERILOG_SOURCES) $(TESTBENCH)
	$(VSIM) -work $(SIM_BUILD)/work -c -L $(DEVICE_FAMILY) -L pmi_work \
		-GFAMILY=$(FAMILY) \
		-GRDATA_WIDTH=$(RDATA_WIDTH) -GRADDR_DEPTH=$(RADDR_DEPTH) \
		-GREGMODE=$(REGMODE) -GRESETMODE=$(RESETMODE) \
		-GOUTPUT_CLK_EN=$(OUTPUT_CLK_EN) -GECC_ENABLE=$(ECC_ENABLE) \
		-GINIT_MODE=$(INIT_MODE) -GINIT_FILE=$(INIT_FILE) \
		-GINIT_FILE_FORMAT=$(INIT_FILE_FORMAT) \
		-voptargs="+acc" -suppress 12130 \
		-wlf $(WLF_FILE) \
		$(if $(TC),+TC=$(TC),) \
		-do "log -r /*; run -all; quit" \
		tb_rom
else
# ── CoCoTB simulation flow ────────────────────────────────────────────────────
# Pull in cocotb's Questa Makefile rules (provides sim, compile, clean)
include $(shell cocotb-config --makefiles)/Makefile.sim
sim: results_dir
endif

# Override clean to also remove results/ and QuestaSim runtime artifacts
clean::
	rm -rf $(RESULTS_DIR)
	rm -rf qrun.out
	rm -rf sim_build
	rm -f  transcript modelsim.ini
	find $(CURDIR)/src $(CURDIR)/scripts -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# ==============================================================================
# all_configs — run every required parameter combination in sequence
#
# Target names encode: REGMODE_RDATA_RADDR_RESETMODE[_TOKEN...]
# Recognised 5th/6th word tokens:
#   memfile   → INIT_MODE=mem_file     (no underscore in name avoids word-split clash)
#   allzero   → INIT_MODE=all_zero     (TG-06 all-zero tests)
#   outclken  → OUTPUT_CLK_EN=1        (TG-04 tests)
#   ecc       → ECC_ENABLE=1           (TG-09 tests)
# Tokens may appear in either order (word 5 or word 6).
#
# Each config gets its own SIM_BUILD directory so parallel execution is safe
# and compile artifacts from one run do not bleed into another.
#
# Add entries here as TG-06 through TG-09 are implemented and need new combos.
# ==============================================================================
ALL_CONFIGS := \
    noreg_36_512_sync              \
    reg_36_512_sync                \
    reg_36_512_async               \
    reg_18_1024_sync               \
    noreg_9_2048_sync              \
    noreg_18_1024_sync             \
    reg_36_1024_sync               \
    noreg_36_512_sync_memfile      \
    reg_36_512_sync_outclken       \
    reg_18_1024_sync_outclken      \
    noreg_36_512_sync_allzero      \
    noreg_1_16384_sync_allzero     \
    noreg_1_2_sync_allzero         \
    noreg_32_512_sync_ecc          \
    noreg_64_512_sync_ecc

# For each config name, extract fields by splitting on underscore.
# 4-word form:  noreg_36_512_sync             → default params
# 5-word form:  noreg_36_512_sync_memfile     → INIT_MODE=mem_file
#               reg_36_512_sync_outclken      → OUTPUT_CLK_EN=1
# 6-word form:  reg_36_512_sync_memfile_outclken → both overrides
define RUN_CONFIG
.PHONY: $(1)
$(1): | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: $(1)"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=$(word 1,$(subst _, ,$(1))) \
		RDATA_WIDTH=$(word 2,$(subst _, ,$(1))) \
		RADDR_DEPTH=$(word 3,$(subst _, ,$(1))) \
		RESETMODE=$(word 4,$(subst _, ,$(1))) \
		$(if $(filter memfile,$(word 5,$(subst _, ,$(1))) $(word 6,$(subst _, ,$(1)))),INIT_MODE=mem_file,) \
		$(if $(filter allzero,$(word 5,$(subst _, ,$(1))) $(word 6,$(subst _, ,$(1)))),INIT_MODE=all_zero,) \
		$(if $(filter outclken,$(word 5,$(subst _, ,$(1))) $(word 6,$(subst _, ,$(1)))),OUTPUT_CLK_EN=1,) \
		$(if $(filter ecc,$(word 5,$(subst _, ,$(1))) $(word 6,$(subst _, ,$(1)))),ECC_ENABLE=1,) \
		SIM_BUILD=$(CURDIR)/sim_build/$(1) \
		2>&1 | tee $(CURDIR)/results/$(1).log; exit $${PIPESTATUS[0]}
endef

$(foreach cfg,$(ALL_CONFIGS),$(eval $(call RUN_CONFIG,$(cfg))))

# ── Special configs — custom INIT_FILE and/or INIT_FILE_FORMAT ───────────────
# These require a specific fixture file and cannot use the generic RUN_CONFIG macro.
# TC-06-04: 18-bit × 1024, binary format (addr-as-data in binary notation)
.PHONY: noreg_18_1024_sync_memfile_bin
noreg_18_1024_sync_memfile_bin: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_18_1024_sync_memfile_bin"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=18 RADDR_DEPTH=1024 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_18_1024.bin \
		INIT_FILE_FORMAT=binary \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_18_1024_sync_memfile_bin \
		2>&1 | tee $(CURDIR)/results/noreg_18_1024_sync_memfile_bin.log; exit $${PIPESTATUS[0]}

# TC-06-05: 9-bit × 2048, hex format, alternating 0xAA/0x55 pattern
.PHONY: noreg_9_2048_sync_memfile_alt
noreg_9_2048_sync_memfile_alt: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_9_2048_sync_memfile_alt"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=9 RADDR_DEPTH=2048 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_9_2048_alt.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_9_2048_sync_memfile_alt \
		2>&1 | tee $(CURDIR)/results/noreg_9_2048_sync_memfile_alt.log; exit $${PIPESTATUS[0]}

# TC-06-08: 4-bit × 4096, binary format (addr%16 pattern)
.PHONY: noreg_4_4096_sync_memfile_bin
noreg_4_4096_sync_memfile_bin: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_4_4096_sync_memfile_bin"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=4 RADDR_DEPTH=4096 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_4_4096.bin \
		INIT_FILE_FORMAT=binary \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_4_4096_sync_memfile_bin \
		2>&1 | tee $(CURDIR)/results/noreg_4_4096_sync_memfile_bin.log; exit $${PIPESTATUS[0]}

# ── TG-07 tile-coverage configs — custom INIT_FILE per width/depth ────────────
.PHONY: noreg_1_16384_sync_memfile
noreg_1_16384_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_1_16384_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=1 RADDR_DEPTH=16384 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_1_16384.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_1_16384_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_1_16384_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_2_8192_sync_memfile
noreg_2_8192_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_2_8192_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=2 RADDR_DEPTH=8192 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_2_8192.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_2_8192_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_2_8192_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_4_4096_sync_memfile
noreg_4_4096_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_4_4096_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=4 RADDR_DEPTH=4096 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_4_4096.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_4_4096_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_4_4096_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_18_1024_sync_memfile
noreg_18_1024_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_18_1024_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=18 RADDR_DEPTH=1024 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_18_1024.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_18_1024_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_18_1024_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_12_512_sync_memfile
noreg_12_512_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_12_512_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=12 RADDR_DEPTH=512 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_12_512.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_12_512_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_12_512_sync_memfile.log; exit $${PIPESTATUS[0]}

# ── TG-08 cascade configs — each needs a custom INIT_FILE per width/depth ─────
.PHONY: noreg_36_1024_sync_memfile
noreg_36_1024_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_36_1024_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=36 RADDR_DEPTH=1024 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_36_1024.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_36_1024_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_36_1024_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_36_2048_sync_memfile
noreg_36_2048_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_36_2048_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=36 RADDR_DEPTH=2048 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_36_2048.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_36_2048_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_36_2048_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_72_512_sync_memfile
noreg_72_512_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_72_512_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=72 RADDR_DEPTH=512 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_72_512.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_72_512_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_72_512_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_144_512_sync_memfile
noreg_144_512_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_144_512_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=144 RADDR_DEPTH=512 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_144_512.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_144_512_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_144_512_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: noreg_72_1024_sync_memfile
noreg_72_1024_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: noreg_72_1024_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=noreg RDATA_WIDTH=72 RADDR_DEPTH=1024 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_72_1024.hex \
		SIM_BUILD=$(CURDIR)/sim_build/noreg_72_1024_sync_memfile \
		2>&1 | tee $(CURDIR)/results/noreg_72_1024_sync_memfile.log; exit $${PIPESTATUS[0]}

.PHONY: reg_36_2048_sync_memfile
reg_36_2048_sync_memfile: | $(RESULTS_DIR)
	@echo ""
	@echo "================================================================"
	@echo " Config: reg_36_2048_sync_memfile"
	@echo "================================================================"
	$(MAKE) sim \
		REGMODE=reg RDATA_WIDTH=36 RADDR_DEPTH=2048 RESETMODE=sync \
		INIT_MODE=mem_file \
		INIT_FILE=$(CURDIR)/testbench/rom_init_36_2048.hex \
		SIM_BUILD=$(CURDIR)/sim_build/reg_36_2048_sync_memfile \
		2>&1 | tee $(CURDIR)/results/reg_36_2048_sync_memfile.log; exit $${PIPESTATUS[0]}

ALL_SPECIAL_CONFIGS := \
    noreg_18_1024_sync_memfile_bin \
    noreg_9_2048_sync_memfile_alt  \
    noreg_4_4096_sync_memfile_bin  \
    noreg_1_16384_sync_memfile     \
    noreg_2_8192_sync_memfile      \
    noreg_4_4096_sync_memfile      \
    noreg_18_1024_sync_memfile     \
    noreg_12_512_sync_memfile      \
    noreg_36_1024_sync_memfile     \
    noreg_36_2048_sync_memfile     \
    noreg_72_512_sync_memfile      \
    noreg_144_512_sync_memfile     \
    noreg_72_1024_sync_memfile     \
    reg_36_2048_sync_memfile

.PHONY: all_configs
all_configs: $(ALL_CONFIGS) $(ALL_SPECIAL_CONFIGS)
	@echo ""
	@echo "================================================================"
	@echo " All $(words $(ALL_CONFIGS) $(ALL_SPECIAL_CONFIGS)) configurations completed"
	@echo " Logs:     $(RESULTS_DIR)/*.log"
	@echo " WLF files: $(RESULTS_DIR)/*.wlf"
	@echo "================================================================"

# ── summary ───────────────────────────────────────────────────────────────────
# Parse all results/*.log files and write a Markdown summary table.
#   make summary            — prints to terminal
#   make summary MD=1       — also writes results/summary.md
.PHONY: summary
summary:
	@python3 scripts/summarize.py $(if $(MD),$(RESULTS_DIR)/summary.md)

# ── drc ───────────────────────────────────────────────────────────────────────
# TG-10: DRC and Parameter Validation tests.
# Exercises the Python model of the lscc_rom plugin DRC rules without a
# simulator.  Requires pytest:
#   pip install pytest
#   make drc
.PHONY: drc
drc:
	@echo ""
	@echo "================================================================"
	@echo " TG-10: DRC and Parameter Validation"
	@echo "================================================================"
	python3 -m pytest src/test_drc.py -v

# ── TC / TG named targets ─────────────────────────────────────────────────────
# Run one test case:        make tc-01-01
# Run all tests in a group: make tg-01
# TG-10 DRC:                make tg-10  (delegates to pytest via make drc)
#
# Each tc-XX-YY target runs only that function in an isolated sim_build directory
# and writes its log to results/tc-XX-YY.log.
# Each tg-XX target runs its TCs in sequence and reports a pass/fail summary.
tc-%:
	@python3 $(CURDIR)/scripts/run_tc.py tc-$*

tg-%:
	@python3 $(CURDIR)/scripts/run_tc.py tg-$*
