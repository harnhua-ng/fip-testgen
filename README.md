# lscc_rom (LIFCL) Verification Suite & Cocotb Testbench

This repository contains a verification environment for the Lattice LIFCL ROM IP (`lscc_rom`), built using **[Cocotb](https://www.cocotb.org/)** (Coroutine-based Co-simulation Testbench) and SystemVerilog.

---

## For the RTL Engineer: What is Cocotb & Python Co-Simulation?

If you are an RTL designer or verification engineer accustomed to SystemVerilog and UVM, **Cocotb** replaces the top-level Verilog verification code with **Python**, while keeping the standard HDL simulator (QuestaSim / ModelSim / VCS / Icarus) underneath:

```
┌────────────────────────────────────────────────────────┐
│               Python Testbench Layer                   │
│   • Test Sequences (Stimulus Generator)                │
│   • Reference Model & Scoreboard (Golden Arrays)       │
│   • Background Monitors (UVM Monitor / Scoreboard)     │
└─────────────────────────┬──────────────────────────────┘
                          │ VPI / FLI / VHPI (Co-Simulation)
┌─────────────────────────▼────────────────────────┐
│       Lattice QuestaSim / HDL Simulator          │
│   • Clock & Reset Signals                        │
│   • Testbench Verilog                            │
│   • DUT Verilog                                  │
│   • Waveforms (.wlf) & Simulation Transcripts    │
└──────────────────────────────────────────────────┘
```

### Python (Cocotb) Maps to SystemVerilog / Verilog

Cocotb uses Python `async` coroutines that interact with the simulator's event queue via standard Verilog Procedural Interface (VPI) callbacks:

| Verification Action | Cocotb (Python) | SystemVerilog / Verilog Equivalent | Simulator Event Region |
| :--- | :--- | :--- | :--- |
| **Wait for Clock Edge** | `await RisingEdge(dut.rd_clk_i)` | `@(posedge rd_clk_i);` | Active Region |
| **Drive Input Signal** | `dut.rd_addr_i.value = 0x10` | `rd_addr_i = 16'h0010;` | Active Region (NBA) |
| **Time Delay** | `await Timer(100, unit="ns")` | `#100;` | Time Advance |
| **Sample Output (Settled)**| `await ReadOnly()`<br>`got = int(dut.rd_data_o.value)` | `#1; got = rd_data_o;`<br>*(or `$strobe` / assertion)* | Postponed / ReadOnly Region |
| **Concurrent Process** | `cocotb.start_soon(monitor.run())` | `fork begin ... end join_none` | Background Thread |
| **Assertion / Check** | `assert got == exp, "Mismatch!"` | `assert (rd_data_o === exp) else $error(...);` | Immediate Assertion |

---

## Verification Architecture: UVM & Transaction-Level Modeling

The approach is actually similar to standard **UVM (Universal Verification Methodology)** and **Transaction-Level Modeling (TLM)** monitoring of cycles and signals:

```
                         ┌────────────────────────────────────────────────┐
                         │   Cocotb Test (Sequence)                       │
                         │   • Applies Reset                              │
                         │   • Drives Control signals, Addresses & Data   │
                         └──────────────┬─────────────────────────────────┘
                                        │ (Drives DUT)
                                        ▼
┌────────────────────────────────────────────────────────────────┐
│                               DUT (IP block)                   │
│   Clock ──> Input Reg ──> IP Logic ──> Output Reg ──> Output   │
└───────────────────────────────────────┬────────────────────────┘
                                        │ (Observes Pins)
                                        ▼
                         ┌───────────────────────────────┐
                         │    PipelineMatrixMonitor      │  <-- UVM Monitor / Scoreboard
                         │   • Non-intrusive Observer    │
                         │   • Cycle-Accurate Pipeline   │
                         │   • Generates Matrix .md      │
                         └───────────────────────────────┘
```

1. **Decouples Stimulus and Analysis (UVM Standard)**:
   * **Test sequences** focus only on *what scenario to stimulate* (e.g., burst reads, random addresses, toggling clock enables).
   * The **`PipelineMatrixMonitor`** runs as an observer (`cocotb.start_soon`) that monitors port signals every clock cycle, like a UVM `uvm_monitor` and `uvm_scoreboard`.
2. **Handles Dynamic Stalls and Pipeline Backpressure**:
   * Hardware memory operations may stall (e.g., `rd_clk_en_i=0` or `rd_out_clk_en_i=0`). The monitor models internal stage holding without needing complex loop arithmetic in each test.
3. **Catches Unprompted Glitches and Out-of-Spec Toggles**:
   * If `rd_data_o` or error flags change when no read was executed, the monitor catches and reports the protocol violation.

---

## Debugging Map for Each Test

| Python Code | Verilog Trace |
| :--- | :--- |
| [Python cocotb test](#python-cocotb-test) | [Verilog Trace](#corresponding-verilog-trace) |

Example for TC-01-01:

### Python cocotb Test

``` python
@cocotb.test(skip=(REGMODE != "noreg" or RDATA_WIDTH != 36 or RADDR_DEPTH != 512
                   or INIT_MODE != "mem_file"))
async def tc_01_01_sequential_read_noreg(dut):
    """TC-01-01: rd_data_o = mem[addr] after exactly 1 clock cycle (noreg, 36bx512).

    Drives 16 sequential addresses in a pipelined pattern.  At each cycle the
    address presented one cycle earlier must appear at rd_data_o, proving that
    the pipeline latency is exactly LAT=1.
    """
    tracer = VerilogTracer("TC-01-01", enabled=True)
    cocotb.start_soon(Clock(dut.rd_clk_i, CLK_NS, unit="ns").start())
    await do_reset(dut, tracer)
    await enable_reads(dut, tracer)
    await latency_check(dut, "TC-01-01", n_addrs=16, tracer=tracer)
    tracer.save()
```

### Corresponding Verilog Trace  
(automatically generated by cocotb for each test)

``` verilog
// ============================================================================
// Verilog Stimulus & Check Trace: TC-01-01
// Auto-generated at runtime from src/tb_rom.py
// ============================================================================
task automatic run_tc_01_01_trace;

    // Reset sequence
    rst_i = 1'b1;
    rd_en_i = 1'b0;
    rd_clk_en_i = 1'b0;
    rd_out_clk_en_i = 1'b0;
    rd_addr_i = 9'h0;
    #100;
    rst_i = 1'b0;
    @(posedge rd_clk_i);

    // Enable reads
    rd_en_i = 1'b1;
    rd_clk_en_i = 1'b1;
    rd_out_clk_en_i = 1'b1;

    // Prime: fill 1 pipeline stage(s)
    @(posedge rd_clk_i);
    rd_addr_i = 9'h0;

    // Steady: drive addr[i] and sample addr[i-1]
    @(posedge rd_clk_i);
    rd_addr_i = 9'h1;
    if (rd_data_o !== 36'h000000000) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000000", 1, 0, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h2;
    if (rd_data_o !== 36'h000000001) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000001", 2, 1, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h3;
    if (rd_data_o !== 36'h000000002) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000002", 3, 2, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h4;
    if (rd_data_o !== 36'h000000003) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000003", 4, 3, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h5;
    if (rd_data_o !== 36'h000000004) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000004", 5, 4, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h6;
    if (rd_data_o !== 36'h000000005) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000005", 6, 5, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h7;
    if (rd_data_o !== 36'h000000006) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000006", 7, 6, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h8;
    if (rd_data_o !== 36'h000000007) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000007", 8, 7, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'h9;
    if (rd_data_o !== 36'h000000008) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000008", 9, 8, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hA;
    if (rd_data_o !== 36'h000000009) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x000000009", 10, 9, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hB;
    if (rd_data_o !== 36'h00000000A) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000A", 11, 10, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hC;
    if (rd_data_o !== 36'h00000000B) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000B", 12, 11, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hD;
    if (rd_data_o !== 36'h00000000C) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000C", 13, 12, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hE;
    if (rd_data_o !== 36'h00000000D) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000D", 14, 13, rd_data_o);
        errors++;
    end
    @(posedge rd_clk_i);
    rd_addr_i = 9'hF;
    if (rd_data_o !== 36'h00000000E) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000E", 15, 14, rd_data_o);
        errors++;
    end

    // Drain: flush last pipeline stages
    @(posedge rd_clk_i);
    if (rd_data_o !== 36'h00000000F) begin
        $display("[TC-01-01] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x00000000F", 16, 15, rd_data_o);
        errors++;
    end
endtask
```

---

## Test Execution

### 1. Prerequisites
* **Lattice Radiant** (v2026.1 or newer) with QuestaSim OEM.
* **Python 3.8+** with `cocotb` and `pytest`.
* Environment properly configured (license and tool paths).

---

### 2. Running Simulations via Unified `make` (Linux & Windows)

The `Makefile` detects the host operating system (`Windows_NT` vs. `Linux`) and configures tool paths and license servers.

```bash
make                   # Default: noreg / 36b×512 / sync / all_one
make tc-01-01          # Run one specific test case
make tg-01             # Run all test cases in Group 01
make tg-10             # Run DRC tests (pytest, no simulator)
make drc               # Alias for make tg-10
make all_configs       # Run full parameter sweep across all configurations
make summary           # Print pass/fail summary table from results/*.log
make summary MD=1      # Also write results/summary.md
make clean             # Remove results/, sim_build/, and QuestaSim runtime artifacts
```

#### Cross-Platform Environment Configuration & Overrides

The `Makefile` resolves environment settings using a **3-tier precedence hierarchy**:

1. **CLI Flag or Shell Export (Highest Precedence)**:
   ```bash
   export LM_LICENSE_FILE="1850@my-server"
   make tc-01-01 RADIANT_ROOT=/tools/radiant/2026.1
   ```
2. **Local Configuration Files (`env.mk` and `local.mk`, both git-ignored)**:
   Copy `env.mk.example` to `env.mk` to store machine-specific paths without editing repository files. A second file `local.mk` (if present) is loaded after `env.mk` and can be used for additional per-machine overrides:
   ```makefile
   # env.mk (local to your machine)
   RADIANT_ROOT        = /opt/lscc/radiant/2026.1
   LM_LICENSE_FILE     = 1850@ldc-virtlic02
   SALT_LICENSE_SERVER = 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b
   ```
3. **Automatic OS Detection (Default Fallback)**:
   * **Windows**: Defaults `RADIANT_ROOT` to `C:/lscc/radiant/2026.1` and points license variables to `license.dat`. Adds `questasim/win64` and `bin/nt64` to `PATH`.
   * **Linux**: Defaults `RADIANT_ROOT` to `/opt/lscc/radiant/2026.1` and sets network license servers. Configures `LD_LIBRARY_PATH` for Cocotb Python VPI.

---

#### Flow Selection (`FLOW` variable)

The Makefile supports one simulation flow, selectable via `FLOW=`:

| `FLOW` | Description |
| :--- | :--- |
| `cocotb` (default) | Python co-simulation via Cocotb VPI; test functions run from `src/tb_rom.py`. |

```bash
make tc-01-01               # defaults to cocotb
make tc-01-01 FLOW=cocotb   # same as the case where FLOW is not specified.
```

---

### 3. Running via Python Test Dispatcher (`scripts/run_tc.py`)

```bash
python scripts/run_tc.py TC-01-01          # Single test case
python scripts/run_tc.py TG-01             # All tests in group 01
python scripts/run_tc.py TG-10             # DRC parameter rules (pytest)
```

When a test case fails, the dispatcher prompts interactively for a **failure label** (when connected to a terminal):

- **Confirmed** — external evidence backs up the failure.
- **Assumed** — nothing contradicts it; taken as truth for now.
- **Flagged** — unusual or suspicious; requires further investigation.

An optional free-text note may be appended. Labeled failures are written to `results/failure_log.md` in Markdown table format. In CI pipelines (non-TTY stdin) the label defaults to *Assumed*.

### 4. Generating a Pass/Fail Summary (`scripts/summarize.py`)

After running one or more test cases, parse all `results/*.log` files into a Markdown table:

```bash
make summary            # Print to terminal
make summary MD=1       # Also write results/summary.md
# or directly:
python3 scripts/summarize.py
python3 scripts/summarize.py results/summary.md
```

### 5. Direct QuestaSim Invocation (`scripts/run_qsim.sh`)

For advanced use (e.g., testing against a local Radiant build or using standard QuestaSim instead of the OEM bundle), `scripts/run_qsim.sh` wraps `qrun` directly:

```bash
# OEM via LDP (simplest):
./scripts/run_qsim.sh -f test_sim.f

# OEM with a local Radiant build:
./scripts/run_qsim.sh -m oem_local -b /path/to/radiant_build -f test_sim.f

# Standard QuestaSim via LDP, auto-compile sim library:
./scripts/run_qsim.sh -m std_ldp -d lifcl -f test_sim.f
```

Run `./scripts/run_qsim.sh -h` for the full option list.

---

## ROM Initialization Files & Fixtures (`testbench/`)

When testing `INIT_MODE = "mem_file"`, the DUT and reference model load initialization data from text files in the `testbench/` directory.

### Initialization Files Mapping

| Test Case | Geometry (`Width` × `Depth`) | Format | Fixture File Path |
| :--- | :--- | :--- | :--- |
| **TC-01-01, TC-06-03, TC-06-06** | 36b × 512 | Hex | `testbench/rom_init.hex` |
| **TC-06-04** | 18b × 1024 | Binary | `testbench/rom_init_18_1024.bin` |
| **TC-06-05, TC-07-05** | 9b × 2048 | Hex (Alternating) | `testbench/rom_init_9_2048_alt.hex` |
| **TC-06-08** | 4b × 4096 | Binary | `testbench/rom_init_4_4096.bin` |
| **TC-07-02** | 1b × 16,384 | Hex | `testbench/rom_init_1_16384.hex` |
| **TC-07-03** | 2b × 8,192 | Hex | `testbench/rom_init_2_8192.hex` |
| **TC-07-04** | 4b × 4,096 | Hex | `testbench/rom_init_4_4096.hex` |
| **TC-07-06** | 18b × 1,024 | Hex | `testbench/rom_init_18_1024.hex` |
| **TC-07-08** | 12b × 512 | Hex | `testbench/rom_init_12_512.hex` |
| **TC-08-01** | 36b × 1,024 | Hex | `testbench/rom_init_36_1024.hex` |
| **TC-08-02** | 36b × 2,048 | Hex | `testbench/rom_init_36_2048.hex` |
| **TC-08-03** | 72b × 512 | Hex | `testbench/rom_init_72_512.hex` |
| **TC-08-04** | 144b × 512 | Hex | `testbench/rom_init_144_512.hex` |
| **TC-08-05** | 72b × 1,024 | Hex | `testbench/rom_init_72_1024.hex` |

---

## Simulation Modes: Behavioral (`FAMILY=common`) vs. Primitive (`FAMILY=LIFCL`)

In `rtl/lscc_rom.v`, the IP supports two simulation paths:

1. **Behavioral Mode (`FAMILY="common"` / `BEHV_MODE`)**:
   * Implements a generic SystemVerilog memory array (`mem[(2**ADDR_WIDTH)-1:0]`).
   * Dynamically loads memory files using standard Verilog system tasks (`$readmemh` or `$readmemb`) via `-GINIT_FILE` and `-GINIT_FILE_FORMAT`.
   * Fast compilation and ideal for architectural/functional verification.
2. **Primitive Mode (`FAMILY="LIFCL"` / `PRIM_MODE`)**:
   * Instantiates target-specific hardware primitives (`lifcl.PDPSC16K`).
   * In hardware EBR primitives, memory contents are initialized via 64-character hex strings (`INIT_VALUE_00` … `INIT_VALUE_7F`).
   * Requires precompiled Lattice libraries (`-L lifcl -L pmi_work`) and `GSR` instantiation (`testgen_top.v`).

---

## Artifacts & Output Directory (`results/`)

After running tests, all logs, traces, and waveforms are placed in `results/`:

| Artifact | File Path | Description |
| :--- | :--- | :--- |
| **Simulation Log** | `results/tc-XX-YY.log` | Complete QuestaSim console transcript (plain-text ASCII/UTF-8). |
| **Waveform File** | `results/tc-XX-YY.wlf` | QuestaSim waveform database (open via `vsim -view results/tc-01-01.wlf`). |
| **Verilog Trace** | `results/tc-XX-YY_trace.v` | Pure Verilog standalone task recording exact stimulus & checks. |
| **Cycle-by-cycle Matrix**| `results/tc-XX-YY_matrix.md`| Markdown table of cycle-by-cycle transitions. |
| **Compiled Work Library** | `results/tc-XX-YY/work/` | Copied QuestaSim compiled library; allows reloading the simulation without keeping `sim_build/`. |
| **Failure Log** | `results/failure_log.md` | Appended by `run_tc.py` after any test failure; stores labeled entries (Confirmed / Assumed / Flagged) with optional notes. |
| **Summary Table** | `results/summary.md` | Written by `make summary MD=1`; Markdown pass/fail table across all logged configurations. |

---

## Test Plan & Test Group Coverage

The test suite is structured into 10 distinct Test Groups (TG-01 through TG-10):

### TG-01 — Basic Read Functionality
| TC | Test Case Name | Configuration | Target |
|---|---|---|---|
| TC-01-01 | Sequential read, noreg | 36b × 512, noreg, sync, mem_file | `make tc-01-01` |
| TC-01-02 | Sequential read, reg | 36b × 512, reg, sync, all_one | `make tc-01-02` |
| TC-01-03 | Full sweep, noreg | 36b × 512, noreg, sync, all_one | `make tc-01-03` |
| TC-01-04 | Full sweep, reg | 36b × 512, reg, sync, all_one | `make tc-01-04` |
| TC-01-05 | Boundary addresses (min/max) | 18b × 1024, reg, sync | `make tc-01-05` |
| TC-01-06 | Random address sequence | 36b × 512, reg, sync | `make tc-01-06` |
| TC-01-07 | Repeated address read | 9b × 2048, noreg, sync | `make tc-01-07` |

### TG-02 — Read Enable (`rd_en_i`)
| TC | Test Case Name | Description | Target |
|---|---|---|---|
| TC-02-01 | `rd_en_i`=0 at start | Output remains 0 / inactive | `make tc-02-01` |
| TC-02-02 | `rd_en_i` de-asserted mid-seq | Output holds previous value | `make tc-02-02` |
| TC-02-03 | `rd_en_i` toggled every cycle | Validates pipeline holding on alternating cycles | `make tc-02-03` |
| TC-02-04 | `rd_en_i` re-assertion | Resumes normal pipelined output | `make tc-02-04` |

### TG-03 — Read Clock Enable (`rd_clk_en_i`)
| TC | Test Case Name | Description | Target |
|---|---|---|---|
| TC-03-01 | `rd_clk_en_i`=0 holds output (noreg) | Address register and memory core frozen | `make tc-03-01` |
| TC-03-02 | `rd_clk_en_i`=0 holds output (reg) | Both address and output stages frozen | `make tc-03-02` |
| TC-03-03 | `rd_clk_en_i` re-assertion | Verified recovery after freeze | `make tc-03-03` |
| TC-03-04 | `rd_clk_en_i` toggle pattern | Multi-cycle stall patterns | `make tc-03-04` |
| TC-03-05 | Cascaded config with `rd_clk_en_i` | Cascaded multi-EBR array clock gating | `make tc-03-05` |

### TG-04 — Output Clock Enable (`rd_out_clk_en_i`)
| TC | Test Case Name | Description | Target |
|---|---|---|---|
| TC-04-01 | `rd_out_clk_en_i`=0 freezes output | Output register holds while core runs | `make tc-04-01` |
| TC-04-02 | `rd_out_clk_en_i`=1 normal | Normal operation with output clock enable | `make tc-04-02` |
| TC-04-03 | `rd_out_clk_en_i` toggle mid-seq | Independent gating of output register stage | `make tc-04-03` |
| TC-04-04 | `OUTPUT_CLK_EN`=0 parameter check | Port inactive when parameter is disabled | `make tc-04-04` |
| TC-04-05 | Both enables de-asserted | Simultaneous core and output register gating | `make tc-04-05` |

### TG-05 — Reset Behavior
| TC | Test Case Name | Description | Target |
|---|---|---|---|
| TC-05-01 | Synchronous reset (`RESETMODE="sync"`) | Clears output register on clock edge | `make tc-05-01` |
| TC-05-02 | Sync reset during active read | Evaluates reset priority over read enable | `make tc-05-02` |
| TC-05-03 | Sync reset release | Single-cycle recovery | `make tc-05-03` |
| TC-05-04 | Asynchronous reset assertion | Immediate output register clear | `make tc-05-04` |
| TC-05-05 | Async reset sync release | Glitch-free recovery on clock edge | `make tc-05-05` |
| TC-05-06 | `REGMODE="noreg"` reset check | Confirms reset does not affect core memory | `make tc-05-06` |

### TG-06 — Memory Initialization Modes
| TC | Test Case Name | Description | Target |
|---|---|---|---|
| TC-06-01 | `INIT_MODE="all_zero"` | All locations return 0 | `make tc-06-01` |
| TC-06-02 | `INIT_MODE="all_one"` | All locations return all 1s | `make tc-06-02` |
| TC-06-03 | `INIT_MODE="mem_file"` (Hex format) | Loads custom memory file (`.hex`) | `make tc-06-03` |
| TC-06-04 | `INIT_MODE="mem_file"` (Binary format) | Loads custom memory file (`.bin`) | `make tc-06-04` |
| TC-06-05 | Alternating checkerboard pattern | Pattern testing for adjacent bit sensitivity | `make tc-06-05` |
| TC-06-06 | Address-as-data verification | Address indexing integrity | `make tc-06-06` |
| TC-06-07 | Narrow width, `all_zero` | All-zero init on minimum-width config (1b × 16,384) | `make tc-06-07` |
| TC-06-08 | Mixed pattern verification | Boundary patterns | `make tc-06-08` |

### TG-07 — LIFCL EBR Tile Primitive Configurations
| TC | Configuration (`RDATA_WIDTH` × `RADDR_DEPTH`) | Primitive Mapping | Target |
|---|---|---|---|
| TC-07-01 | 1-bit × 2 (Minimum size) | Partial EBR allocation | `make tc-07-01` |
| TC-07-02 | 1-bit × 16,384 (Maximum single depth) | Single 16K EBR configured as 16K×1 | `make tc-07-02` |
| TC-07-03 | 2-bit × 8,192 | Single 16K EBR configured as 8K×2 | `make tc-07-03` |
| TC-07-04 | 4-bit × 4,096 | Single 16K EBR configured as 4K×4 | `make tc-07-04` |
| TC-07-05 | 9-bit × 2,048 (Parity mode) | Single 16K EBR configured as 2K×9 | `make tc-07-05` |
| TC-07-06 | 18-bit × 1,024 (Parity mode) | Single 16K EBR configured as 1K×18 | `make tc-07-06` |
| TC-07-07 | 36-bit × 512 (Standard dual-mode) | Single 16K EBR configured as 512×36 | `make tc-07-07` |
| TC-07-08 | 12-bit × 512 (Non-power-of-2 width) | Padding and masking verification | `make tc-07-08` |

### TG-08 — Multi-EBR Cascading
| TC | Cascade Topology | Effective Geometry | Target |
|---|---|---|---|
| TC-08-01 | Address Cascade ×2 | 36-bit × 1,024 (2 EBRs deep) | `make tc-08-01` |
| TC-08-02 | Address Cascade ×4 | 36-bit × 2,048 (4 EBRs deep) | `make tc-08-02` |
| TC-08-03 | Data Width Cascade ×2 | 72-bit × 512 (2 EBRs wide) | `make tc-08-03` |
| TC-08-04 | Data Width Cascade ×4 | 144-bit × 512 (4 EBRs wide) | `make tc-08-04` |
| TC-08-05 | 2D Array Cascade (2 deep × 2 wide) | 72-bit × 1,024 (4 EBRs total) | `make tc-08-05` |
| TC-08-06 | Bank Boundary Sweep | Continuous reads across EBR address transitions | `make tc-08-06` |
| TC-08-07 | Cascaded Array + Clock Enable | Gating multi-EBR cascaded structures | `make tc-08-07` |
| TC-08-08 | Cascaded Array + Reg Mode | Multi-EBR 2-stage output pipeline latency | `make tc-08-08` |

### TG-09 — Error Correction Code (ECC)
| TC | Test Description | Expected Behavior | Target |
|---|---|---|---|
| TC-09-01 | ECC Disabled (`ECC_ENABLE=0`) | `one_err_det_o` and `two_err_det_o` stay 0 | `make tc-09-01` |
| TC-09-02 | ECC Enabled, Clean Data | Zero error flags asserted on clean memory | `make tc-09-02` |
| TC-09-03 | ECC Minimum Supported Width (32 b) | Clean ECC checks on 32-bit width | `make tc-09-03` |
| TC-09-04 | ECC Maximum Supported Width (64 b) | Clean ECC checks on 64-bit width | `make tc-09-04` |
| TC-09-05 | Single-Bit Error Detection & Correction (SEC)| Detects single-bit flip, corrects data output *(always skipped — requires ECC_ERROR_INJECT=1 and a pre-corrupted fixture)* | `make tc-09-05` |
| TC-09-06 | Double-Bit Error Detection (DED) | Detects uncorrectable 2-bit error *(always skipped — requires ECC_ERROR_INJECT=1 and a pre-corrupted fixture)* | `make tc-09-06` |
| TC-09-07 | ECC Recovery Sequence | Clean data restored after error injection *(always skipped — requires ECC_ERROR_INJECT=1 and a pre-corrupted fixture)* | `make tc-09-07` |

### TG-10 — Design Rule Checks (DRC & Parameter Validation)

#### Plugin Architecture

The `lscc_rom` Lattice Radiant IP has two artifact files that define its configuration-time DRC rules:

- **`plugin/plugin.py`** — The actual Radiant IP Generator plugin Python script. Contains DRC helper functions (`check_addr_depth_data_width`, `check_data_width`, `check_output_clk_en`, `check_resetmode`, `chk_file`, etc.) that are called by the Radiant GUI when a user configures the IP. These functions rely on two Radiant-injected globals — `PluginUtil` (for emitting errors) and `runtime_info` (for device context) — which are not available outside the Radiant process.

- **`metadata.xml`** — The IP metadata file (IP version 2.5.0, minimum Radiant 2022.1). It declares all parameters, their types, default values, and `drc` expression attributes that reference functions in `plugin.py`. Critical detail: `REGMODE` has `value_type="bool"` in the metadata, so the DRC functions receive Python `True`/`False` — **not** the strings `"reg"`/`"noreg"` that the RTL simulator sees. `RADDR_DEPTH` has a separate `value_range=(2,65536)` constraint that the Radiant GUI enforces before calling any DRC function.

#### Two DRC Test Modes

| File | Drives | Use |
| :--- | :--- | :--- |
| `src/test_drc.py` | A local Python reimplementation of the constraints (`check_lscc_rom_params`) | Default for `make drc` / `make tg-10`; no plugin dependency |
| `src/test_drc_plugin.py` | The actual `plugin/plugin.py` DRC functions, with a `PluginUtil` stub injected | Validates that the real plugin enforces each rule; run explicitly with `pytest src/test_drc_plugin.py -v` |

Both files cover TC-10-01 through TC-10-09 but with different implementations and known differences documented below.

```bash
make tg-10                              # or: make drc  — runs test_drc.py
pytest src/test_drc_plugin.py -v       # runs against actual plugin.py
```

#### Known Gaps (open defects against testplan)

The testplan (`docs/ROM_LIFCL_testplan.md`) is the final authority on expected behavior. The two items below are open defects in the plugin implementation — `plugin/plugin.py` and `metadata.xml` are **not modified** in this repository; the gaps are documented here for traceability.

| TC | Testplan Requirement | Status in `test_drc_plugin.py` | Defect |
| :--- | :--- | :--- | :--- |
| **TC-10-01** | Rule_5 (§6): `RADDR_DEPTH ∈ [2, 65536]` — RADDR_DEPTH=1 must be rejected | `xfail` | `check_addr_depth_data_width` in `plugin.py` uses `min_addr_depth=1`, so RADDR_DEPTH=1 is silently accepted by the DRC expression. The Radiant GUI enforces the lower bound separately via `value_range=(2,65536)` in `metadata.xml`, but the DRC function does not. To fix: change `min_addr_depth = 1` to `min_addr_depth = 2` in `check_addr_depth_data_width`. |
| **TC-10-08** | Rule_4 (§6): `ECC_ENABLE=True` requires `RDATA_WIDTH ∈ {32, 64}` — RDATA_WIDTH=65 must be rejected | `skip` | `metadata.xml` has no `drc` attribute on the `ECC_ENABLE` setting, and `plugin.py` has no corresponding check function. To fix: add a `check_ecc_width(ECC_ENABLE, RDATA_WIDTH)` function to `plugin.py` and wire it as the `drc` expression on the `ECC_ENABLE` setting in `metadata.xml`. |

#### TC Coverage

*All DRC tests execute instantaneously using `pytest` without simulator invocation.*

* **TC-10-01**: `RADDR_DEPTH` below minimum (< 2). *(xfail in plugin test — see above)*
* **TC-10-02**: `RADDR_DEPTH` above maximum (> 65,536).
* **TC-10-03**: `RDATA_WIDTH` below minimum (< 1).
* **TC-10-04**: `RDATA_WIDTH` above maximum (> 512).
* **TC-10-05**: Total bits exceed LIFCL device limit (84 tiles × 18 Kbits = 1,548,288 bits; per testplan Section 3).
* **TC-10-06**: `OUTPUT_CLK_EN=1` specified with `REGMODE="noreg"`. *(plugin receives `True`/`False` booleans, not strings)*
* **TC-10-07**: `RESETMODE="async"` specified with `REGMODE="noreg"`. *(same bool note)*
* **TC-10-08**: ECC enabled with unsupported data width (`RDATA_WIDTH != 32, 64`). *(skip in plugin test — no check function exists in plugin.py)*
* **TC-10-09**: `INIT_MODE="mem_file"` specified without valid file path.

---

## RTL Debugging Guide: Step-by-Step

When a test fails, use this triage workflow:

1. **Review the Plain-Text Log**:
   Inspect `results/tc-XX-YY.log` for simulator warnings, EBR primitive configuration messages, or assertion failures.
2. **Open the Waveform or Simulation in QuestaSim**:
   ```bash
   vsim -view results/tc-01-01.wlf
   ```
   Add all DUT signals to the wave window (`add wave -r /*`) to inspect the hardware registers, memory primitives (`PDPSC16K`), and internal clock enable lines.
