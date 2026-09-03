# fip-testgen — FIP Testcase Generation

A multi-IP functional verification framework for Lattice FPGA IP cores (FIPs), using
[CoCoTB](https://cocotb.org) Python co-simulation with QuestaSim.

The approach: each IP's test plan lives in `docs/` as a Markdown file (source of truth,
not modified). Testcases in `src/` are Python CoCoTB coroutines that drive the IP's RTL
directly via the VPI interface, with one test function per test plan entry.

---

## Repository Structure

```
fip-testgen/
├── scripts/              # Shared scripts (all IPs)
│   ├── run_tc.py         # Test dispatcher for ebr_rom (make tc-XX-YY / tg-XX)
│   ├── summarize.py      # Parses results/*.log → Markdown pass/fail table
│   └── verilog_tracer.py # VerilogTracer class — generates _trace.v files
├── ebr_rom/              # EBR ROM — lscc_rom (reference implementation)
├── fifo_dc/              # Dual-Clock FIFO — lscc_fifo_dc
├── pll/                  # General-Purpose PLL — lscc_pll
├── env.mk.example        # Template for local environment overrides
└── README.md
```

Each IP directory follows the same layout:

```
<ip>/
├── Makefile              # CoCoTB simulation targets
├── docs/                 # Test plan (.md) — source of truth, not modified
├── metadata.xml          # IP parameter definitions — not modified
├── plugin/               # Radiant IP DRC plugin — not modified
├── rtl/                  # IP RTL source — not modified
├── src/
│   ├── tb_<ip>.py        # CoCoTB test functions (generated from test plan)
│   └── test_drc.py       # DRC parameter validation (pytest, no simulator)
├── testbench/            # Verilog top-level testbench wrapper
├── proj/                 # Radiant project (.rdf + impl/) — created by make prj_create (git-ignored)
├── results/              # Simulation outputs (git-ignored)
└── sim_build/            # CoCoTB/QuestaSim build artifacts (git-ignored)
```

---

## Supported IP Cores

| IP | RTL Module | Test Plan | Status |
|---|---|---|---|
| `ebr_rom` | `lscc_rom` | `docs/ROM_TestPlan_LIFCL.md` | Complete — G1 through G11 (34 TCs, TC-ROM-001 through TC-ROM-034) |
| `fifo_dc` | `lscc_fifo_dc` | `docs/FIFO_DC_LIFCL_TestPlan_20260801.md` | In progress |
| `pll` | `lscc_pll` | `docs/pll_lifcl_testplan.md` | In progress |

`ebr_rom` is the reference implementation. When adding a new IP, use its Makefile,
testbench, and `src/` structure as the starting point.

---

## Prerequisites

- **Lattice Radiant** with QuestaSim OEM (tested against 2026.1+)
- **Python 3.8+** with `cocotb` and `pytest` installed
- License servers accessible, or configured locally via `env.mk`

### Environment Configuration

Copy `env.mk.example` to `<ip>/env.mk` to set machine-specific paths without editing
tracked files:

```makefile
# <ip>/env.mk  (git-ignored)
RADIANT_ROOT        = /opt/lscc/radiant/2026.1
LM_LICENSE_FILE     = 1850@my-license-server
SALT_LICENSE_SERVER = 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a
```

Settings are resolved in this order (highest to lowest priority):

1. CLI flag or shell export: `make tc-01-01 RADIANT_ROOT=/tools/radiant`
2. Local override file: `<ip>/env.mk` (git-ignored)
3. Automatic OS detection defaults embedded in the Makefile

---

## Running Simulations

### ebr_rom

Uses `scripts/run_tc.py` to map TC IDs to simulation parameters and invoke `make sim`.
Test cases are named TC-ROM-001 through TC-ROM-034, grouped into G1 through G11.

```bash
cd ebr_rom/

make test              # Run all groups G1..G11 and write results/summary.md
make tc-rom-001        # Run one test case by full ID
make tc-rom-012        # Run TC-ROM-012 (output register disabled)
make tg-01             # Run all TCs in Group 1 (Baseline)
make g1                # Alias for make tg-01
make g11               # DRC parameter checks via pytest (no simulator)
make drc               # Alias for make g11
make all_configs       # Parameter sweep across the 15 named configurations
make summary           # Print pass/fail table from results/*.log
make summary MD=1      # Also write results/summary.md
make clean             # Remove results/, sim_build/, QuestaSim artifacts
make prj_create        # Generate Radiant .rdf project in proj/
make prj_compile       # Run Radiant PAR on proj/lscc_rom.rdf
make clean_prj         # Remove the proj/ directory
```

Test group reference:

| Group | Subject | TCs |
|---|---|---|
| G1 | Baseline | TC-ROM-001 |
| G2 | `RADDR_DEPTH` | TC-ROM-002 to 006 |
| G3 | `RDATA_WIDTH` | TC-ROM-007 to 010 |
| G4 | `REGMODE` | TC-ROM-011 to 012 |
| G5 | `RESETMODE` | TC-ROM-013 to 014 |
| G6 | `INIT_FILE_FORMAT` | TC-ROM-015 to 016 |
| G7 | `OUTPUT_CLK_EN` | TC-ROM-017 to 018 |
| G8 | `user_init_file` content | TC-ROM-019 |
| G9 | Cross-parameter combinations | TC-ROM-020 to 023 |
| G10 | Port behaviour | TC-ROM-024 to 030 |
| G11 | DRC & Radiant smoke tests | TC-ROM-031 to 034 |

When a TC fails on a TTY, the dispatcher prompts for a failure label:

- **Confirmed** — external evidence backs up the failure
- **Assumed** — nothing contradicts it; taken as truth for now
- **Flagged** — unusual or suspicious; needs investigation

Labels are appended to `results/failure_log.md`. In non-TTY environments (CI) the label
defaults to *Assumed*.

### fifo_dc

```bash
cd fifo_dc/

make tc-003            # Hard-IP controller, minimal simulation
make tc-004            # Fabric/EBR controller, minimal simulation
make tc-005            # Data integrity: Hard-IP fill/drain cycle
make tc-006            # Data integrity: Fabric/EBR fill/drain cycle
make tc-010            # FWFT mode
make drc               # DRC parameter checks (pytest)
```

To run a testcase not exposed as a named target, invoke make directly:

```bash
make TESTCASE=tc_007_write_to_full_suppression
```

### pll

```bash
cd pll/

make tc-002            # Integer-N synthesis, CLKOP lock
make tc-004            # Fractional-N synthesis
make tc-017            # LMMI slave read/write
make tc-018            # APB slave dword mapping
make drc               # DRC parameter checks (pytest)
```

To run other testcases:

```bash
make TESTCASE=tc_lifcl_003_integer_n_all_6_clocks
```

---

## Simulation Artifacts

All outputs land in `<ip>/results/`:

| Artifact | Path | Notes |
|---|---|---|
| Simulation log | `results/tc-rom-XXX.log` (ebr_rom) / `results/tc-NNN.log` (others) | Full QuestaSim transcript |
| Waveform | `results/tc-rom-XXX.wlf` | Open with `vsim -view results/tc-rom-001.wlf` |
| Verilog trace | `results/<tc-name>_trace.v` | Standalone stimulus/check task — all IPs |
| Failure log | `results/failure_log.md` | Labeled failure history written by `run_tc.py` |
| Summary table | `results/summary.md` | Written by `make summary MD=1` |

### Verilog Trace Files

Each testcase writes a `results/<tc-name>_trace.v` file at the end of simulation.
The file contains a self-contained Verilog task that reproduces the stimulus applied
and the output checks performed during that run.  RTL engineers can use this file to
replay a testcase in a standalone QuestaSim session without Python or CoCoTB.

**File naming**

| IP | Example TC | Trace file |
|---|---|---|
| `ebr_rom` | TC-ROM-001 | `results/tc-rom-001_trace.v` |
| `fifo_dc` | TC-003 | `results/tc-003_trace.v` |
| `pll` | TC-LIFCL-002 | `results/tc-lifcl-002_trace.v` |

**Trace file structure**

```verilog
// ============================================================================
// Verilog Stimulus & Check Trace: TC-ROM-001
// Auto-generated at runtime by VerilogTracer (scripts/verilog_tracer.py)
// ============================================================================
task automatic run_tc_rom_001_trace;
    // stimulus and $display checks recorded during the CoCoTB run
    @(posedge rd_clk_i);
    rd_addr_i = 10'h000;
    // ...
    if (rd_data_o !== 18'hXXXXX) begin
        $display("[TC-ROM-001] cycle N: got=0x%0X exp=0xXXX", rd_data_o);
        errors++;
    end
endtask
```

**Replaying a trace in QuestaSim**

1. Compile the IP RTL and testbench top as usual.
2. `` `include `` the trace file in a thin Verilog wrapper:

```verilog
`include "results/tc-rom-001_trace.v"

module replay_tb;
    integer errors = 0;
    // instantiate DUT here ...

    initial begin
        run_tc_rom_001_trace;
        if (errors == 0)
            $display("PASS");
        else
            $display("FAIL: %0d error(s)", errors);
        $finish;
    end
endmodule
```

3. Run `vsim replay_tb` and inspect waveforms alongside the Python simulation's
   `.wlf` file for a side-by-side comparison.

**Note:** For `fifo_dc` and `pll`, the trace task currently captures the
start/end markers but not detailed signal-level statements — those require
adding `tracer.log_stmt()` / `tracer.assign()` calls to the driver helper
functions in `src/tb_<ip>.py`, following the pattern established in
`ebr_rom/src/tb_rom.py`.

### Preserving the Work Library (`KEEP_WORK`)

By default the compiled QuestaSim work library is discarded after each run to keep disk
usage low. Set `KEEP_WORK=1` to preserve it for post-simulation inspection:

```bash
make KEEP_WORK=1 tc-01-01     # keeps results/tc-01-01/work/
```

---

## Shared Scripts

| Script | Description |
|---|---|
| `scripts/run_tc.py` | ebr_rom test dispatcher. Reads `TC_MAP`/`TG_MAP`, invokes `make sim` with the correct parameters, logs results, and writes labeled failure entries. |
| `scripts/summarize.py` | Parses all `results/*.log` files and prints a Markdown pass/fail table. Also accepts an output path to write `results/summary.md`. |
| `scripts/verilog_tracer.py` | `VerilogTracer` class, shared by all IP testbenches. Imported automatically when `$(CURDIR)/../scripts` is on `PYTHONPATH` (set by each IP's Makefile). |

---

## How CoCoTB Maps to Verilog

CoCoTB replaces the Verilog top-level testbench with Python `async` coroutines connected
to QuestaSim via VPI:

| Action | CoCoTB (Python) | Verilog equivalent |
|---|---|---|
| Wait for clock edge | `await RisingEdge(dut.clk)` | `@(posedge clk);` |
| Drive a signal | `dut.addr.value = 0x10` | `addr = 8'h10;` |
| Time delay | `await Timer(100, unit="ns")` | `#100;` |
| Sample settled output | `await ReadOnly()` then `.value` | `#1; got = out;` |
| Assert | `assert got == exp, f"got {got}"` | `assert (out === exp) else $error(...)` |
| Concurrent process | `cocotb.start_soon(monitor())` | `fork … join_none` |

Each test function is decorated with `@cocotb.test()` and uses a `skip=` condition to
self-filter based on the DUT parameters exported into the simulation environment by the
Makefile. This lets a single `make sim` invocation run the full test file and naturally
skip tests whose parameter requirements are not met.

---

## Adding a New IP Core

Use `ebr_rom/` as the reference. Minimum steps:

1. Create `<ip>/` with the standard directory layout shown above.
2. Copy `ebr_rom/Makefile` and update: `COCOTB_TOPLEVEL`, `COCOTB_TEST_MODULES`,
   `VERILOG_SOURCES`, DUT parameter variables, and `export` lines.
3. Add `KEEP_WORK ?= 0` and `export KEEP_WORK` alongside the other exports.
4. Write testcases in `src/tb_<ip>.py` as `@cocotb.test()` async functions, one per
   test plan entry, with a `skip=` guard matching the required parameter combination.
   Each test function must start with `tracer = VerilogTracer("TC-XXX", enabled=True)`
   and end with `tracer.save()` to produce a `results/<tc-name>_trace.v` file.
5. Write DRC checks in `src/test_drc.py` using `pytest`; these run without a simulator
   via `make drc`.
6. Add named `make tc-NNN` convenience targets for the most frequently run testcases.

If the IP follows the same numbered TC structure as ebr_rom, extend `scripts/run_tc.py`
with a `TC_MAP` and `TG_MAP` for the new IP and add `tc-%` / `tg-%` / `g%` wildcard
targets to its Makefile (see `ebr_rom/Makefile`, the `tc-%` / `tg-%` / `g%` pattern
rules near the bottom of the TC/TG named targets section).
