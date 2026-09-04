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
| `ebr_rom` | `lscc_rom` | `docs/ROM_TestPlan_LIFCL.md` | Complete — G01 through G11 (34 TCs + 20 DRC rules + Radiant PAR) |
| `fifo_dc` | `lscc_fifo_dc` | `docs/FIFO_DC_TestPlan_LIFCL.md` | Complete — G01 through G24 (53 TCs + 8 DRC rules + Radiant PAR) |
| `pll` | `lscc_pll` | `docs/PLL_TestPlan_LIFCL.md` | Complete — G01 through G29 (81 TCs + 5 DRC rules + Radiant PAR) |

All IP cores implement the standardized structure: CoCoTB testbench, pytest DRC suite, synthesizable Radiant wrapper, and automated Radiant compilation flow.

---

## Prerequisites

- **Lattice Radiant** with QuestaSim OEM (tested against 2026.1+)
- **Python 3.8+** with dependencies installed: `pip install -r requirements.txt` (`cocotb`, `pytest`)
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

### fifo_dc Makefile Target Reference

```bash
cd fifo_dc/

# Overview & Regression
make info              # Quick test plan outline (53 TCs, 24 testgroups)
make test              # Run full suite (Sim G01-G23 + DRC G24 + Radiant PAR)
make summary           # Print pass/fail summary table
make drc               # Run G24 DRC pytest suite (src/test_drc.py)

# Individual Test Cases & Test Groups
make tc-fifodc-001     # Run TC-FIFODC-001 (baseline 512x36 EBR reg async)
make tc-fifodc-016     # Run TC-FIFODC-016 (output register disabled)
make tg-01             # Run all testcases in Group 1
make g1                # Short alias for make tg-01

# Radiant Project & Synthesis
make prj_create        # Generate Radiant project (proj/lscc_fifo_dc.rdf)
make prj_compile       # Run Synplify synthesis and PAR on proj/lscc_fifo_dc.rdf
make clean_prj         # Remove proj/ directory and Radiant temporary logs
make clean             # Clean all sim_build/, results/, and project artifacts
```

---

### pll Makefile Target Reference

```bash
cd pll/

# Overview & Regression
make info              # Quick test plan outline (81 TCs, 29 testgroups)
make test              # Run full suite (Sim G01-G28 + DRC G29 + Radiant PAR)
make summary           # Print pass/fail summary table
make drc               # Run G29 DRC pytest suite (src/test_drc.py)

# Individual Test Cases & Test Groups
make tc-pll-001        # Run TC-PLL-001 (default config lock)
make tc-pll-002        # Run TC-PLL-002 (integer-N all clocks)
make tg-01             # Run all testcases in Group 1
make g1                # Short alias for make tg-01

# Radiant Project & Synthesis
make prj_create        # Generate Radiant project (proj/lscc_pll.rdf)
make prj_compile       # Run Synplify synthesis and PAR on proj/lscc_pll.rdf
make clean_prj         # Remove proj/ directory and Radiant temporary logs
make clean             # Clean all sim_build/, results/, and project artifacts
```

---

## Test Output Artifacts

Artifacts are organized into two primary output directories depending on the test category:
- **`results/`**: Simulation logs, waveforms, Verilog traces, DRC reports, and summary matrix.
- **`proj/`**: Radiant FPGA project files, Synplify synthesis reports, Map resource reports, and PAR timing reports.

---

### 1. Functional Simulation Artifacts (`results/`)

Generated by `make test`, `make tc-rom-XXX`, or `make tg-XX`:

| Artifact | Location | Description & Usage |
|---|---|---|
| **Simulation Log** | `results/tc-rom-XXX.log` | Full QuestaSim transcript containing CoCoTB test setup, clock/reset actions, cycle assertions, and pass/fail summary. |
| **Waveform File** | `results/tc-rom-XXX.wlf` | QuestaSim simulation waveform database. View with `vsim -view results/tc-rom-001.wlf`. |
| **Verilog Trace** | `results/tc-rom-XXX_trace.v` | Self-contained Verilog task generated by `VerilogTracer`. Captures exact clock-cycle stimulus and output assertions for standalone replay in pure Verilog without Python. |
| **Summary Table** | `results/summary.md` | Aggregated Markdown report generated by `summarize.py` showing PASS/FAIL status for all simulated configs and DRC checks. |
| **Failure Log** | `results/failure_log.md` | Categorized issue tracking log (`Confirmed`, `Assumed`, `Flagged`) appended whenever a test case fails. |
| **Build Directory** | `sim_build/tc-rom-XXX/` | Compiler and simulation snapshot directory containing compiled work libraries and logs. Retained across runs for incremental compilation speedup; removed with `make clean`. |

#### Verilog Trace Files (`_trace.v`)

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

#### Simulation Build Directory (`sim_build/`)

Each testcase builds into its own isolated directory (`sim_build/tc-<tc_id>/`), containing the compiled QuestaSim `work/` library, compilation logs (`sim.log`), and session state. These directories are preserved across runs by default to enable incremental compilation speedup for subsequent runs.

To remove all simulation build directories and temporary outputs:

```bash
make clean
```

---

### 2. DRC Parameter Validation Artifacts (`results/`)

Generated by `make drc` (or `pytest src/test_drc.py`):

| Artifact | Location | Description & Usage |
|---|---|---|
| **DRC Execution Log** | `results/drc.log` | Detailed pytest transcript verifying each parameter validation rule (Rules 1–14: depth/width limits, memory budget constraints, editability locks, and derived properties). |
| **DRC Summary Entry** | `results/summary.md` | Recorded under the `## G11 — DRC` section in the summary matrix. |

---

### 3. Radiant Compilation Artifacts (`proj/` & `proj/impl_1/`)

Generated by `make prj_create` and `make prj_compile`:

| Artifact | Location | Description & Verification Role |
|---|---|---|
| **Radiant Project** | `proj/lscc_rom.rdf` | The Lattice Radiant XML project definition targeting `LFCPNX-100-9BFG484C`. |
| **CLI Run Log** | `proj/radiantc.log.<pid>` | Radiant tool execution transcript from project creation to PAR completion. |
| **Synthesis Report** | `proj/impl_1/lscc_rom_impl_1.srr` | Synplify Pro synthesis report. Verifies RTL elaboration, parameter propagation, clock domain detection, and primitive inferencing. |
| **Map Resource Report** | `proj/impl_1/lscc_rom_impl_1.mrp` | Radiant Map report. Verifies physical FPGA resource utilization (EBR block count, slice LUTs, PIO pin count, and primitive selection such as `SP16K`). |
| **HTML Map Report** | `proj/impl_1/lscc_rom_impl_1.mrp.html` | Interactive HTML breakdown of design resource utilization and DRC checks. |
| **Place & Route Report** | `proj/impl_1/lscc_rom_impl_1.par` | PAR router log verifying 100% routing completion and unrouted net checks. |
| **Timing & Slack Report** | `proj/impl_1/lscc_rom_impl_1.twr` | Static Timing Analysis (STA) report detailing setup/hold slacks, max operating frequency, and clock constraints. |
| **Pinout Report** | `proj/impl_1/lscc_rom_impl_1.pad` | Pin assignment and I/O standard allocation report. |
| **Design Checkpoints** | `proj/impl_1/*_syn.udb`, `*_map.udb` | Radiant Unified Database files representing synthesized and mapped design netlists. |

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

---

## Known Issues

### FIFO DC IP (`lscc_fifo_dc`)

During full test regression of `fifo_dc` against `docs/FIFO_DC_TestPlan_LIFCL.md`, 33 functional test cases fail due to two specific hardware pipeline/handshake defects in the IP core RTL (`rtl/lscc_fifo_dc.v`) when output register mode is enabled (`REGMODE="reg"`). In accordance with verification guidelines, the IP core RTL is kept unmodified, and the test suite preserves the test plan specification.

#### 1. Failure Breakdown by Root Cause

| Category | Failing Test Cases | Underlying RTL Defect |
|---|---|---|
| **Standard FIFO Mode (`FWFT=0`, `REGMODE="reg"`)** | **30 tests**:<br>• `TC-FIFODC-001` through `009`<br>• `TC-FIFODC-017` through `035`<br>• `TC-FIFODC-039`, `040` | **Premature `empty_r` gating on EBR chip-select**: In `lscc_fifo_dc.v`, `empty_r` asserts 1 cycle too early during a burst read drain, deasserting `rd_fifo_en_w` (`CSR=3'b000` to `PDP16K`) on the final word. The output register latches stale data, leaving `rd_data_o` frozen on the second-to-last word. |
| **First-Word Fall-Through Mode (`FWFT=1`, `REGMODE="reg"`)** | **3 tests**:<br>• `TC-FIFODC-013`<br>• `TC-FIFODC-037`<br>• `TC-FIFODC-038` | **Premature prefetch latch in FWFT fabric wrapper**: In `lscc_fifo_dc_fwft_fabric.v`, `re_r` pulses for only 1 cycle immediately when `empty_i` deasserts. Because registered memory output has multi-cycle read latency, `data_q` samples uninitialized `0x0` and locks `rd_data_o` at `0x0`. |

All configurations without the registered output path (**`REGMODE="noreg"`**, **Hardened Controller `HARD_IP`**, **`FWFT=1` with `REGMODE="noreg"`**, and all **G24 DRC parameter checks**) pass cleanly (26/59 suites/stages pass).

---

#### 2. Detailed RTL Root Cause Analysis

##### Defect A: Standard FIFO Mode (`FWFT=0`, `REGMODE="reg"`)

In `fifo_dc/rtl/lscc_fifo_dc.v`:
```verilog
// 1. Read enable is gated by empty_r
wire rd_fifo_en_w = rd_en_i & ~empty_r;

// 2. empty_cmp_w compares rd_addr_nxt_c with wr_addr
wire empty_cmp_w = (wr_cmp_rd_w == rd_cmp_rd_w);

// 3. Memory chip-select is directly driven by rd_fifo_en_w
wire [2:0] CSR = {t_rd_en_i, t_rd_en_i, t_rd_en_i}; // where t_rd_en_i = rd_fifo_en_w
```

**Cycle-by-Cycle Execution Trace (e.g. 32-word burst in `TC-FIFODC-001`)**:
1. Words 0 through 30 are read successfully.
2. During the read of Word 30 (read address 30), `rd_addr_nxt_c` advances to `31 + 1 = 32`.
3. Because 32 words were written (`wr_addr = 32`), `empty_cmp_w` evaluates to `(32 == 32) = 1`.
4. At the next `rd_clk_i` rising edge, `empty_r` asserts to `1`.
5. On the final read cycle (intended for Word 31 at address 31):
   - `rd_fifo_en_w = rd_en_i & ~empty_r` evaluates to `1 & ~1 = 0`.
   - The `PDP16K` EBR memory primitive receives `CSR = 3'b000` (chip-disabled).
   - Address 31 is never read from memory.
   - The output register `rd_data_ebr_r` latches the stale primitive output (Word 30), causing:
     ```text
     AssertionError: [TC-FIFODC-001] Word 31 mismatch: got=0x25A58 (Word 30) exp=0x26B69 (Word 31)
     ```

##### Defect B: FWFT Mode with Output Register (`FWFT=1`, `REGMODE="reg"`)

In `fifo_dc/rtl/lscc_fifo_dc_fwft_fabric.v`:
```verilog
assign rden_o = ((empty_q_r & ~empty_lat_r) | rd_en_i) & ~empty_i;

always @(posedge clk_i, posedge rst_i)
    if (rst_i)
        re_r <= 1'b0;
    else if (rden_o & ~empty_i)
        re_r <= 1'b1;
    else
        re_r <= 1'b0;

always @(posedge clk_i, posedge rst_i)
    if (rst_i)
        data_q <= {DWID{1'b0}};
    else if (re_r)
        data_q <= data_q_w;  // data_q_w = (re_r) ? d_i : data_r;
```

**Cycle-by-Cycle Execution Trace**:
1. When writes complete and CDC synchronization finishes, `empty_i` drops to `0`.
2. `rden_o` pulses `1` for one cycle, asserting `re_r <= 1`.
3. On the next clock cycle, `data_q` samples `d_i`. However, because the underlying EBR memory has registered output latency, `d_i` is still uninitialized (`0x0`).
4. On the subsequent cycle, `re_r` drops back to `0`. Because `data_q` is only updated when `re_r == 1`, `data_q` remains frozen at `0x0`.
5. When the testbench samples `rd_data_o`, it reads `0x0`:
   ```text
   AssertionError: [TC-FIFODC-013] Word 0 mismatch: got=0x0 exp=0x5A5A
   ```

---

### General-Purpose PLL IP (`lscc_pll`)

During full test regression of `pll` against `docs/PLL_TestPlan_LIFCL.md`, 73 out of 82 test suites/stages pass (including all 5 DRC parameter checks and Radiant FPGA compilation). 9 functional test cases fail due to two specific hardware primitive simulation constraints when optional hardware features are enabled in standalone RTL simulation without GUI-derived binary string parameters:

#### 1. Failure Breakdown by Root Cause

| Category | Failing Test Cases | Underlying Root Cause in Standalone Simulation |
|---|---|---|
| **Spread Spectrum Modulation (`SS_EN=1`)** | **6 tests**:<br>• `TC-PLL-006` (down spread)<br>• `TC-PLL-007` (centre spread)<br>• `TC-PLL-008` (min mod freq)<br>• `TC-PLL-009` (median mod freq)<br>• `TC-PLL-010` (max mod freq)<br>• `TC-PLL-067` (pin refclk + 6 freqs) | **Unconfigured Spread Spectrum Timebase String**: In `lscc_pll.v`, enabling `SS_EN=1` requires `SSC_TBASE_STR`, `SSC_STEP_IN_STR`, and `SSC_N_CODE_STR` (normally computed by the Radiant GUI/IP generator). In direct RTL simulation, `SSC_TBASE_STR` defaults to `"0b000000000000"` (`0`), causing a divide-by-zero (`lmmi_ssc_tbase=0`) in the `PLLA` simulation model, which halts loop filter convergence and prevents lock. |
| **Reference Clock Monitor (`EN_REFCLK_MON=1`)** | **3 tests**:<br>• `TC-PLL-019` (3.2 MHz monitor)<br>• `TC-PLL-066` (frac-N + monitor + APB)<br>• `TC-PLL-071` (1.0 MHz monitor + internal path) | **Default Reference Count Limit**: In `lscc_pll.v`, enabling `EN_REFCLK_MON=1` requires `REF_COUNTS` (normally computed by the Radiant GUI/IP generator from `CLKI_FREQ` and `REF_OSC_CTRL`). With default `REF_COUNTS="0000"`, the `PLLA` monitor model triggers loss-of-reference-clock detection (`refdetlos=1`), holding the PLL core in an unlocked state. |

---

#### 2. Detailed RTL Root Cause Analysis

##### Defect A: Spread Spectrum Modulation (`SS_EN=1`)

In `pll/rtl/lscc_pll.v`:
```verilog
parameter SS_EN             = 0,
parameter SSC_TBASE_STR     = "0b000000000000",
parameter SSC_STEP_IN_STR   = "0b0000000",
...
localparam SSC_TBASE        = (SS_EN)? SSC_TBASE_STR : "0b000000000000";
```

**Simulation Behavior**:
1. Top-level testbench overrides generic `SS_EN=1`.
2. `lscc_pll` passes unconfigured `SSC_TBASE="0b000000000000"` (value 0) to `PLLA`.
3. The primitive simulation model encounters a divide-by-zero:
   ```text
   WARNING: lmmi_ssc_tbase=0 while SSC is enabled can lead to division by 0
   ** Warning: (vsim-8630) Infinity results from division operation.
   ```
4. The internal VCO frequency calculation fails to settle, and `lock_o` fails to assert before timeout:
   ```text
   AssertionError: [TC-PLL-006] PLL failed to lock within timeout
   ```

##### Defect B: Reference Clock Monitor (`EN_REFCLK_MON=1`)

In `pll/rtl/lscc_pll.v`:
```verilog
parameter EN_REFCLK_MON     = 0,
parameter REF_COUNTS        = "0000",
...
PLLA #(
    .REF_COUNTS (REF_COUNTS),
    ...
) u_PLL ( ... );
```

**Simulation Behavior**:
1. When `EN_REFCLK_MON=1`, the reference monitor circuit monitors `clki_i` against internal oscillator `REF_OSC_CTRL`.
2. Because `REF_COUNTS` defaults to `"0000"`, the reference clock cycle counter overflows immediately on every cycle.
3. `refdetlos` asserts high, reporting a false loss-of-clock condition and inhibiting PLL lock.
