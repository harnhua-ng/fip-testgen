# lscc_rom (LIFCL) Verification Suite & Cocotb Testbench

This repository contains a comprehensive verification environment for the Lattice LIFCL ROM IP (`lscc_rom`), built using **[Cocotb](https://www.cocotb.org/)** (Coroutine-based Co-simulation Testbench) and SystemVerilog.

---

## 📖 For the RTL Engineer: What is Cocotb & Python Co-Simulation?

If you are an RTL designer or verification engineer accustomed to SystemVerilog and UVM, **Cocotb** replaces the top-level Verilog verification code with **Python**, while keeping the standard HDL simulator (QuestaSim / ModelSim / VCS / Icarus) running underneath:

```
┌────────────────────────────────────────────────────────┐
│               Python Testbench Layer                   │
│   • Test Sequences (Stimulus Generator)                │
│   • Reference Model & Scoreboard (Golden Arrays)       │
│   • Background Monitors (UVM Monitor / Scoreboard)     │
└─────────────────────────┬──────────────────────────────┘
                          │ VPI / FLI / VHPI (Co-Simulation)
┌─────────────────────────▼──────────────────────────────┐
│             Lattice QuestaSim / HDL Simulator          │
│   • Clock & Reset Signals                              │
│   • testgen_top.v / tb_rom.v                           │
│   • DUT: lscc_rom.v (EBR Primitives / PDPSC16K)        │
│   • Waveforms (.wlf) & Simulation Transcripts          │
└────────────────────────────────────────────────────────┘
```

### Python (Cocotb) to SystemVerilog / Verilog Rosetta Stone

Cocotb uses Python `async` coroutines that interact with the simulator's stratified event queue via standard VPI callbacks:

| Verification Action | Cocotb (Python) | SystemVerilog / Verilog Equivalent | Simulator Event Region |
| :--- | :--- | :--- | :--- |
| **Wait for Clock Edge** | `await RisingEdge(dut.rd_clk_i)` | `@(posedge rd_clk_i);` | Active Region |
| **Drive Input Signal** | `dut.rd_addr_i.value = 0x10` | `rd_addr_i = 16'h0010;` | Active Region (NBA) |
| **Time Delay** | `await Timer(100, unit="ns")` | `#100;` | Time Wheel Advance |
| **Sample Output (Settled)**| `await ReadOnly()`<br>`got = int(dut.rd_data_o.value)` | `#1; got = rd_data_o;`<br>*(or `$strobe` / assertion)* | Postponed / ReadOnly Region |
| **Concurrent Process** | `cocotb.start_soon(monitor.run())` | `fork begin ... end join_none` | Background Thread |
| **Assertion / Check** | `assert got == exp, "Mismatch!"` | `assert (rd_data_o === exp) else $error(...);` | Immediate Assertion |

---

## 🏛️ Verification Architecture: UVM & Transaction-Level Modeling (Approach A)

This testbench adheres to industry-standard **UVM (Universal Verification Methodology)** and **Transaction-Level Modeling (TLM)** principles through **Approach A: Passive Background Monitoring**:

```
                         ┌─────────────────────────────┐
                         │   Cocotb Test (Sequence)    │
                         │   • Applies Reset           │
                         │   • Drives Addresses        │
                         └──────────────┬──────────────┘
                                        │ (Drives DUT)
                                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                               DUT (lscc_rom)                             │
│   rd_clk_i ──> [Addr Reg] ──> [EBR Core Matrix] ──> [Output Reg] ──> rd_data_o│
└───────────────────────────────────────┬──────────────────────────────────┘
                                        │ (Passively Observes Pins)
                                        ▼
                         ┌─────────────────────────────┐
                         │    PipelineMatrixMonitor    │  <-- UVM Monitor / Scoreboard
                         │   • Non-intrusive Observer  │
                         │   • Cycle-Accurate Pipeline │
                         │   • Generates Matrix .md    │
                         └─────────────────────────────┘
```

### Why Approach A (Passive Monitor) Over Inline Test Checking (Approach B)?

1. **Strict Decoupling of Stimulus and Analysis (UVM Standard)**:
   * **Test sequences** focus solely on *what scenario to stimulate* (e.g., burst reads, random addresses, toggling clock enables).
   * The **`PipelineMatrixMonitor`** runs as an independent concurrent observer (`cocotb.start_soon`) that passively observes port signals every clock cycle, exactly like a UVM `uvm_monitor` and `uvm_scoreboard`.
2. **Handles Dynamic Stalls and Pipeline Backpressure**:
   * Hardware memory operations may stall (e.g., `rd_clk_en_i=0` or `rd_out_clk_en_i=0`). The passive monitor automatically models internal stage holding without requiring complex loop arithmetic in each test.
3. **Catches Unprompted Glitches and Out-of-Spec Toggles**:
   * If `rd_data_o` or error flags change when no read was executed, the background monitor catches and reports the protocol violation immediately.

---

## 📊 Cycle-by-Cycle Pipeline Alignment Matrix

Every test run automatically captures and generates an **Alignment Matrix Report** (`results/<tc_name>_matrix.md`), giving RTL engineers instant cycle-by-cycle visibility into the pipeline without needing to open the waveform viewer:

| Time (ns) | Cycle | RST | Enables (E/C/O) | `rd_addr_i` | Latched Addr | `rd_data_o` | Expected (`REF`) | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 105.00 | 11 | 0 | E:1 C:1 O:1 | `0x0` | `--` | `0x000000000` | `--` | IDLE/PRIME |
| 115.00 | 12 | 0 | E:1 C:1 O:1 | `0x1` | `0x0` | `0x000000001` | `0x000000001` | **PASS** |
| 125.00 | 13 | 0 | E:1 C:1 O:1 | `0x2` | `0x1` | `0x000000002` | `0x000000002` | **PASS** |
| 135.00 | 14 | 0 | E:1 C:1 O:1 | `0x3` | `0x2` | `0x000000003` | `0x000000003` | **PASS** |

* **Enables**: `E` = `rd_en_i`, `C` = `rd_clk_en_i`, `O` = `rd_out_clk_en_i`.
* **Latched Addr**: The address currently emerging at the output stage given the configuration's pipeline latency (`LAT=1` for `noreg`, `LAT=2` for `reg`).

---

## 🚀 Quick Start & Test Execution

### 1. Prerequisites
* **Lattice Radiant** (v2024.1 / v2026.1 or newer) with QuestaSim OEM.
* **Python 3.8+** with `cocotb` and `pytest`.
* Environment properly configured (license and tool paths).

---

### 2. Running Simulations via PowerShell (`scripts/run_tc.ps1`)

`scripts/run_tc.ps1` runs tests directly in native Windows PowerShell using QuestaSim:

```powershell
# Run a specific test case (e.g. TC-01-01)
.\scripts\run_tc.ps1 -tc "01-01"

# Run an entire test group (e.g. all 7 test cases in TG-01)
.\scripts\run_tc.ps1 -tg "01"

# Launch QuestaSim GUI with waveforms for interactive debug
.\scripts\run_tc.ps1 -tc "01-01" -gui

# Custom Lattice Radiant installation path
.\scripts\run_tc.ps1 -tg "01" -radiant_root "C:\lscc\radiant\2026.1"
```

#### What `run_tc.ps1` Does Under the Hood:
1. Sets up environment variables (`LM_LICENSE_FILE`, `SALT_LICENSE_SERVER`, `FOUNDRY`, `PATH`).
2. Maps Lattice Radiant precompiled simulation libraries (`lifcl` and `pmi_work`).
3. Compiles `rtl/lscc_rom.v`, `testbench/testgen_top.v`, and `testbench/tb_rom.v` into `sim_build/work`.
4. Executes `vsim` with `-l results/tc-01-01.log` (plain text log) and `-wlf results/tc-01-01.wlf` (waveform).

---

### 3. Running Simulations via Unified `make` (Linux, macOS & Windows Git-Bash / MSYS2)

The `Makefile` automatically detects the host operating system (`Windows_NT` vs. `Linux`) and configures appropriate paths and license servers.

```bash
make tc-01-01          # Run one specific test case
make tg-01             # Run all test cases in Group 01
make tg-10             # Run DRC tests (pytest, no simulator)
make all_configs       # Run full parameter sweep across all configurations
```

#### Cross-Platform Environment Configuration & Overrides

The `Makefile` resolves environment settings using a **3-tier precedence hierarchy**:

1. **CLI Flag or Shell Export (Highest Precedence)**:
   ```bash
   export LM_LICENSE_FILE="1850@my-server"
   make tc-01-01 RADIANT_ROOT=/tools/radiant/2026.1
   ```
2. **Local Configuration File (`env.mk`, git-ignored)**:
   Copy `env.mk.example` to `env.mk` to store machine-specific paths without editing repository files:
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

### 4. Running via Python Test Dispatcher (`scripts/run_tc.py`)

```bash
python scripts/run_tc.py TC-01-01          # Single test case
python scripts/run_tc.py TG-01             # All tests in group 01
python scripts/run_tc.py TG-10             # DRC parameter rules (pytest)
```

---

## 🗄️ ROM Initialization Files & Fixtures (`testbench/`)

When testing `INIT_MODE = "mem_file"`, the DUT and reference model load initialization data from formatted text files located in the `testbench/` directory.

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

## ⚙️ Simulation Modes: Behavioral (`FAMILY=common`) vs. Primitive (`FAMILY=LIFCL`)

In `rtl/lscc_rom.v`, the IP supports two distinct simulation paths:

1. **Behavioral Mode (`FAMILY="common"` / `BEHV_MODE`)**:
   * Implements a generic SystemVerilog memory array (`mem[(2**ADDR_WIDTH)-1:0]`).
   * Dynamically loads memory files using standard Verilog system tasks (`$readmemh` or `$readmemb`) via `-GINIT_FILE` and `-GINIT_FILE_FORMAT`.
   * Fast compilation and ideal for architectural/functional verification.
2. **Primitive Mode (`FAMILY="LIFCL"` / `PRIM_MODE`)**:
   * Instantiates target-specific hardware primitives (`lifcl.PDPSC16K`).
   * In hardware EBR primitives, memory contents are initialized via 64-character hex strings (`INIT_VALUE_00` … `INIT_VALUE_7F`).
   * Requires precompiled Lattice libraries (`-L lifcl -L pmi_work`) and `GSR` instantiation (`testgen_top.v`).

---

## 📁 Artifacts & Output Directory (`results/`)

After running tests, all logs, traces, and waveform databases are placed in `results/`:

| Artifact | File Path | Description |
| :--- | :--- | :--- |
| **Simulation Log** | `results/tc-XX-YY.log` | Complete QuestaSim console transcript (plain-text ASCII/UTF-8). |
| **Waveform File** | `results/tc-XX-YY.wlf` | QuestaSim waveform database (open via `vsim -view results/tc-01-01.wlf`). |
| **Verilog Trace** | `results/tc-XX-YY_trace.v` | Pure Verilog standalone task recording exact stimulus & checks. |
| **Pipeline Matrix**| `results/tc-XX-YY_matrix.md`| Markdown table of cycle-by-cycle pipeline transitions. |

---

## 🧪 Test Plan & Test Group Coverage

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
| TC-06-07 | Narrow width initialization | 1-bit and 2-bit wide memory files | `make tc-06-07` |
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
| TC-09-05 | Single-Bit Error Detection & Correction (SEC)| Detects single-bit flip, corrects data output | `make tc-09-05` |
| TC-09-06 | Double-Bit Error Detection (DED) | Detects uncorrectable 2-bit error | `make tc-09-06` |
| TC-09-07 | ECC Recovery Sequence | Clean data restored after error injection | `make tc-09-07` |

### TG-10 — Design Rule Checks (DRC & Parameter Validation)
*All DRC tests execute instantaneously using `pytest` without simulator invocation:*
```bash
make tg-10    # or: make drc
```
* **TC-10-01**: `RADDR_DEPTH` below minimum (< 2).
* **TC-10-02**: `RADDR_DEPTH` above maximum (> 65,536).
* **TC-10-03**: `RDATA_WIDTH` below minimum (< 1).
* **TC-10-04**: `RDATA_WIDTH` above maximum (> 512).
* **TC-10-05**: Total bits exceed device limit (512 × 4096).
* **TC-10-06**: `OUTPUT_CLK_EN=1` specified with `REGMODE="noreg"`.
* **TC-10-07**: `RESETMODE="async"` specified with `REGMODE="noreg"`.
* **TC-10-08**: ECC enabled with unsupported data width (`RDATA_WIDTH != 32, 64`).
* **TC-10-09**: `INIT_MODE="mem_file"` specified without valid file path.

---

## 🔍 RTL Debugging Guide: Step-by-Step

When a test fails, use this 3-step triage workflow:

1. **Check the Pipeline Alignment Matrix**:
   Open `results/tc-XX-YY_matrix.md`. Look for rows marked with **`MISMATCH`** to see the exact simulation timestamp, the address in flight, and the expected vs. sampled data.
2. **Review the Plain-Text Log**:
   Inspect `results/tc-XX-YY.log` for simulator warnings, EBR primitive configuration messages, or assertion failures.
3. **Open the Waveform in QuestaSim**:
   ```bash
   vsim -view results/tc-01-01.wlf
   ```
   Add all DUT signals to the wave window (`add wave -r /*`) to inspect the hardware registers, memory primitives (`PDPSC16K`), and internal clock enable lines.
