# fip-testgen — FIP Testcase Generation

A multi-IP functional verification framework for Lattice FPGA IP cores (FIPs), using
[CoCoTB](https://cocotb.org) Python co-simulation with QuestaSim, pytest for Design Rule
Checks (DRC), and Lattice Radiant batch tools for synthesis and compilation verification.

The approach: each IP's test plan lives in `docs/` as a Markdown file (source of truth,
not modified). Testcases in `src/` are Python CoCoTB coroutines that drive the IP's RTL
directly via the VPI interface, with one test function per test plan entry. DRC rules are
tested separately in `src/test_drc.py` with pytest, and synthesizable wrappers live in `synth/`.
Legacy pure-Verilog testbenches have been eliminated in favor of this unified, modern Python flow.

---

## Repository Structure

```
fip-testgen/
├── scripts/              # Shared scripts (all IPs)
│   ├── run_tc.py         # Test dispatcher & runner (info, test, tc-XXX, tg-XX)
│   ├── summarize.py      # Parses results/*.log → Markdown pass/fail summary table
│   └── verilog_tracer.py # VerilogTracer class — generates standalone _trace.v files
├── ebr_rom/              # EBR ROM — lscc_rom (reference implementation)
├── fifo_dc/              # Dual-Clock FIFO — lscc_fifo_dc
├── pll/                  # General-Purpose PLL — lscc_pll
├── env.mk.example        # Template for local environment overrides
└── README.md
```

Each IP directory follows the same layout:

```
<IP name>/
├── docs/
│   └── <ip>_TestPlan_<device family>.md    # Test plan (.md) - source of truth
├── plugin/                                 # Radiant IP DRC plugin - not modified
│   └── plugin.py                           # From FIP repository - not modified
├── proj/                                   # (Generated output) Radiant project (.rdf + impl_1/), not checked in
├── results/                                # (Generated output) Simulation outputs, logs, traces, summary
├── rtl/                                    # IP RTL source - not modified
│   └── <ip>.v                              # From FIP repository - not modified
├── sim_build/                              # (Generated outputs) CoCoTB/QuestaSim build artifacts
├── src/
│   ├── tb_<ip>.py                          # Python CoCoTB test functions - generated from test plan
│   └── test_drc.py                         # DRC parameter validation - pytest suite
├── synth/                                  # Radiant project synthesizable wrappers
│   └── <ip>_synth_wrap.v                   # Synthesizable top-level module
├── testbench/                              # Simulation top-level wrapper
│   └── testgen_top.v                       # Toplevel instantiated by QuestaSim
├── Makefile                                # Simulation, DRC, and Radiant project targets
└── metadata.xml                            # IP parameter definitions - not modified
```

---

## Supported IP Cores

| IP | RTL Module | Test Plan | Status |
|---|---|---|---|
| `ebr_rom` | `lscc_rom` | `docs/ROM_TestPlan_LIFCL.md` | Complete — G1 through G11 (34 TCs + 20 DRC rules + Radiant PAR) |
| `fifo_dc` | `lscc_fifo_dc` | `docs/FIFO_DC_LIFCL_TestPlan_20260801.md` | Complete — Testbench, DRC suite & Makefile |
| `pll` | `lscc_pll` | `docs/pll_lifcl_testplan.md` | Complete — Testbench, DRC suite & Makefile |

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

1. CLI flag or shell export: `make tc-rom-001 RADIANT_ROOT=/tools/radiant`
2. Local override file: `<ip>/env.mk` (git-ignored)
3. Automatic OS detection defaults embedded in the Makefile

---

## Makefile Usage & Test Execution

Each IP core provides standard Makefile targets for test inspection, functional simulation,
DRC checking, and Radiant project compilation.

### `make info` — Test Plan Overview

Prints a fast pre-flight outline of the IP's test coverage without invoking the simulator:

```bash
cd ebr_rom/
make info
```

Output:
```text
==================================================================
  IP Test Overview: lscc_rom (LIFCL v2.5.0)
==================================================================
  IP name:                        lscc_rom (ROM)
  Testgroups:                     11 (G01–G10 Functional, G11 DRC)
  Testcases:                      34 total (per Test Plan)
    ├── Both (Sim & Radiant):     12
    ├── Sim Only:                 10
    └── Radiant Compilation:      12
  DRC Parameter Unit Tests:       20 (in src/test_drc.py for G11 & GUI rules)
  Synthesizable Radiant projects: 1 (lscc_rom.rdf via `make prj_create`)
==================================================================
```

### `make test` — Full End-to-End Regression

Runs all verification stages sequentially and generates `results/summary.md`:
1. **Simulation Functional Suite (`G01`–`G10`)**: Executes all 30 functional CoCoTB test cases in QuestaSim.
2. **DRC Parameter Validation (`G11`)**: Executes the 20 `pytest` parameter validation tests.
3. **Radiant Hardware Compilation**: Creates `proj/lscc_rom.rdf`, runs Synplify synthesis, mapping, and Place & Route (PAR).
4. **Summary Table**: Aggregates all test logs into `results/summary.md`.

```bash
make test
```

### ebr_rom Makefile Target Reference

```bash
cd ebr_rom/

# Overview & Regression
make info              # Quick test plan outline
make test              # Run full suite (Sim G01-G10 + DRC G11 + Radiant PAR) and write summary.md
make summary           # Print pass/fail summary table from existing results/*.log
make summary MD=1      # Also write results/summary.md

# Individual Test Cases (CoCoTB Simulation)
make tc-rom-001        # Run single testcase by ID (TC-ROM-001)
make tc-rom-012        # Run TC-ROM-012 (output register disabled latency)
make tc-001            # Short alias for make tc-rom-001

# Test Groups
make tg-01             # Run all testcases in Group 1 (Baseline)
make g1                # Short alias for make tg-01
make tg-04             # Run Group 4 (REGMODE latency)

# DRC Parameter Validation
make drc               # Run G11 DRC pytest suite (src/test_drc.py)
make g11               # Alias for make drc

# Direct Parameter Overrides (Ad-hoc simulation)
make REGMODE=reg RADDR_DEPTH=512 TESTCASE=tc_rom_001_default_config_read

# Radiant Project & Synthesis
make prj_create        # Generate Radiant project (proj/lscc_rom.rdf)
make prj_compile       # Run Synplify synthesis and PAR on proj/lscc_rom.rdf
make clean_prj         # Remove proj/ directory and Radiant temporary logs

# Cleanup
make clean             # Remove sim_build/, results/, and Radiant compilation artifacts
```

### Test Group Reference (ebr_rom)

| Group | Subject | TCs | Category |
|---|---|---|---|
| G01 | Baseline | TC-ROM-001 | Both |
| G02 | `RADDR_DEPTH` | TC-ROM-002 to 006 | Radiant Compilation / Sim Only |
| G03 | `RDATA_WIDTH` | TC-ROM-007 to 010 | Both / Sim Only / Radiant Compilation |
| G04 | `REGMODE` | TC-ROM-011 to 012 | Sim Only / Both |
| G05 | `RESETMODE` | TC-ROM-013 to 014 | Both / Radiant Compilation |
| G06 | `INIT_FILE_FORMAT` | TC-ROM-015 to 016 | Both |
| G07 | `OUTPUT_CLK_EN` | TC-ROM-017 to 018 | Radiant Compilation / Both |
| G08 | `user_init_file` content | TC-ROM-019 | Both |
| G09 | Cross-parameter combinations | TC-ROM-020 to 023 | Sim Only / Both / Radiant Compilation |
| G10 | Port behaviour | TC-ROM-024 to 030 | Sim Only / Both |
| G11 | DRC & Radiant smoke tests | TC-ROM-031 to 034 | Radiant Compilation (20 pytest checks) |

When a TC fails on an interactive TTY, the dispatcher prompts for a failure label:
- **Confirmed** — external evidence backs up the failure
- **Assumed** — nothing contradicts it; taken as truth for now
- **Flagged** — unusual or suspicious; needs investigation

Labels are recorded in `results/failure_log.md`.

---

### fifo_dc

```bash
cd fifo_dc/

make tc-003            # Hard-IP controller, minimal simulation
make tc-004            # Fabric/EBR controller, minimal simulation
make tc-005            # Data integrity: Hard-IP fill/drain cycle
make tc-006            # Data integrity: Fabric/EBR fill/drain cycle
make tc-010            # FWFT mode
make drc               # DRC parameter checks (pytest)
make TESTCASE=tc_007_write_to_full_suppression
```

---

### pll

```bash
cd pll/

make tc-002            # Integer-N synthesis, CLKOP lock
make tc-004            # Fractional-N synthesis
make tc-017            # LMMI slave read/write
make tc-018            # APB slave dword mapping
make drc               # DRC parameter checks (pytest)
make TESTCASE=tc_lifcl_003_integer_n_all_6_clocks
```

---

## Simulation Artifacts

All outputs land in `<ip>/results/`:

| Artifact | Path | Notes |
|---|---|---|
| Simulation log | `results/tc-rom-XXX.log` (ebr_rom) / `results/tc-NNN.log` (others) | Full QuestaSim transcript |
| Waveform | `results/tc-rom-XXX.wlf` | Open with `vsim -view results/tc-rom-001.wlf` |
| Verilog trace | `results/tc-rom-XXX_trace.v` | Standalone stimulus/check task generated by `VerilogTracer` |
| DRC log | `results/drc.log` | Pytest output log |
| Failure log | `results/failure_log.md` | Labeled failure history written by `run_tc.py` |
| Summary table | `results/summary.md` | Written by `make summary MD=1` or `make test` |

### Verilog Trace Files

Each simulation testcase writes a `results/<tc-name>_trace.v` file via `VerilogTracer`.
The file contains a self-contained Verilog task that reproduces the stimulus applied
and the output checks performed during that run. RTL engineers can use this file to
replay a testcase in a standalone QuestaSim session without Python or CoCoTB:

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

### Preserving the Work Library (`KEEP_WORK`)

By default the compiled QuestaSim work library is discarded after each run to keep disk
usage low. Set `KEEP_WORK=1` to preserve it for post-simulation inspection:

```bash
make KEEP_WORK=1 tc-rom-001     # keeps sim_build/tc-rom-001/work/
```

---

## Shared Scripts

| Script | Description |
|---|---|
| `scripts/run_tc.py` | IP test dispatcher. Supports `info`, `test`, `tc-rom-XXX`, `tg-XX`, `drc`, logs results, and writes failure logs. |
| `scripts/summarize.py` | Parses `results/*.log` (including `drc.log`) and prints/writes Markdown summary tables. |
| `scripts/verilog_tracer.py` | `VerilogTracer` class, shared by all IP testbenches. Imported automatically via `PYTHONPATH`. |

---

## How CoCoTB Maps to Verilog

CoCoTB drives the DUT top-level ports directly via Python `async` coroutines connected
to QuestaSim via VPI:

| Action | CoCoTB (Python) | Verilog equivalent |
|---|---|---|
| Wait for clock edge | `await RisingEdge(dut.rd_clk_i)` | `@(posedge rd_clk_i);` |
| Drive a signal | `dut.rd_addr_i.value = 0x10` | `rd_addr_i = 10'h10;` |
| Time delay | `await Timer(100, unit="ns")` | `#100;` |
| Sample settled output | `await ReadOnly()` then `.value` | `#1; got = rd_data_o;` |
| Assert condition | `assert got == exp` | `assert (rd_data_o === exp) else $error(...)` |
| Concurrent process | `cocotb.start_soon(clock.start())` | `fork … join_none` |

---

## Adding a New IP Core

Use `ebr_rom/` as the reference. Minimum steps:

1. Create `<ip>/` with the standard directory layout.
2. Copy `ebr_rom/Makefile` and update parameters, ports, and top-level sources.
3. Write testcases in `src/tb_<ip>.py` as `@cocotb.test()` async functions, one per
   test plan entry. Instantiate `VerilogTracer("TC-XXX")` and end with `tracer.save()`.
4. Write DRC checks in `src/test_drc.py` using `pytest`; run without a simulator via `make drc`.
5. Create synthesizable wrapper in `synth/<ip>_synth_wrap.v` for `make prj_create` and `make prj_compile`.
6. Add `make tc-NNN` convenience targets and integrate into `scripts/run_tc.py`.
