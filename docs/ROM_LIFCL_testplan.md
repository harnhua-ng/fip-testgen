# ROM Foundation IP — Test Plan (LIFCL Family)

| Field | Value |
|---|---|
| **IP Name** | ROM |
| **Module Name** | `lscc_rom` |
| **IP Version** | 2.5.0 |
| **Target Family** | LIFCL (covers LIFCL, LFD2NX, LFCPNX, LFMXO5, UT24C, UT24CP) |
| **T_FAMILY** | `LIFCL` |
| **Specification Ref.** | ROM_FunctionalSpec.md v2.5.0 |
| **Document Status** | Draft |
| **Date** | 2026-08-01 |

---

## 1. Introduction

This test plan covers functional verification of the ROM Foundation IP (`lscc_rom`) targeting the **LIFCL device family**. All device families that resolve to `T_FAMILY = "LIFCL"` — namely LIFCL, LFD2NX, LFCPNX, LFMXO5, UT24C, and UT24CP — share the same EBR primitive configurations and are covered by this plan.

The test plan is derived from **ROM_FunctionalSpec.md v2.5.0** and exercises all features described therein: read operation, output register modes, clock enable hierarchy, reset behavior, memory initialization, EBR tile configurations specific to LIFCL, cascading, ECC, and DRC validation.

---

## 2. Scope

### 2.1 In Scope

- All functional features of `lscc_rom` as described in ROM_FunctionalSpec.md
- LIFCL EBR tile configurations (data widths: 1, 2, 4, 9, 18, 36; depths: 16384 down to 512)
- Single-tile and multi-tile (cascaded) memory configurations
- Memory initialization: all_zero, all_one, mem_file (hex and binary)
- REGMODE: "reg" and "noreg"
- Clock enables: `rd_clk_en_i` and `rd_out_clk_en_i`
- Reset modes: sync and async
- ECC: ECC_ENABLE=0 and ECC_ENABLE=1
- DRC enforcement via plugin

### 2.2 Out of Scope

- iCE40UP, LATG1, LAV-AT, AP6, LKH, LN2 families (separate test plans)
- INIT_DATA_TYPE (Static/Dynamic) — not exposed in GUI for LIFCL
- Byte-enable path (BYTE_ENABLE is permanently 0 in ROM)
- PIPELINES parameter (fixed at 0)
- Physical timing closure and post-route simulation

---

## 3. LIFCL EBR Constraints

| EBR Data Width | EBR Address Depth | Notes |
|---|---|---|
| 1 | 16,384 | |
| 2 | 8,192 | |
| 4 | 4,096 | |
| 9 | 2,048 | Standard with parity |
| 18 | 1,024 | Standard with parity |
| 36 | 512 | Standard with parity; default configuration |

- **Maximum total capacity:** 84 tiles × 18 Kbits = **1,548,288 bits**
- **ECC minimum data width:** 32 bits (forces EBR to 32-bit configuration)
- **ECC maximum data width:** 64 bits (Rule 4)

---

## 4. Test Environment

| Item | Requirement |
|---|---|
| Simulator | Functional RTL simulation (Verilog) |
| DUT | `lscc_rom.v` top-level module |
| Testbench | `tb_top.v` (parameterized via `dut_params.v`, `dut_inst.v`) |
| Reference model | `$readmemh` / `$readmemb` into a local memory array |
| Clock period | 10 ns (100 MHz) for LIFCL |
| Reset duration | 100 ns (10 cycles) |
| Pass criterion | `chk` signal remains `1'b1` throughout; simulation ends with "SIMULATION PASSED" |

---

## 5. Parameter Space

### 5.1 User-Configurable Parameters Exercised

| Parameter | Values Tested |
|---|---|
| RDATA_WIDTH | 1, 2, 4, 9, 18, 32, 36, 64, 72, 108, 144 |
| RADDR_DEPTH | 2, 36, 512, 1024, 2048, 4096, 8192, 16384 |
| REGMODE | "reg", "noreg" |
| OUTPUT_CLK_EN | 0, 1 |
| RESETMODE | "sync", "async" |
| ECC_ENABLE | 0, 1 |
| user_init_mode | "all_zero", "all_one", "mem_file" |
| INIT_FILE_FORMAT | "hex", "binary" |

### 5.2 Fixed Parameters (LIFCL)

| Parameter | Value |
|---|---|
| FAMILY | "LIFCL" |
| T_FAMILY | "LIFCL" |
| BYTE_ENABLE | 0 |
| PIPELINES | 0 |
| ASYNC_RST_RELEASE | "sync" |
| INIT_DATA_TYPE | True (DYNAMIC) |

---

## 6. Dependency Rules Reference

| Rule | Summary |
|---|---|
| Rule_1 | `user_init_mode = "mem_file"` requires a valid `user_init_file` path |
| Rule_2 | `OUTPUT_CLK_EN` and `RESETMODE="async"` require `REGMODE=True` |
| Rule_3 | `RADDR_DEPTH × RDATA_WIDTH ≤ 1,548,288 bits` (LIFCL limit) |
| Rule_4 | `ECC_ENABLE=True` requires `RDATA_WIDTH ≤ 64` |
| Rule_5 | `RADDR_DEPTH ∈ [2, 65536]`, `RDATA_WIDTH ∈ [1, 512]` |

---

## 7. Test Groups and Test Cases

### TG-01 — Basic Read Functionality

Verify core read behavior in both REGMODE configurations.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | REGMODE | Init Mode | Stimulus | Expected Result |
|---|---|---|---|---|---|---|---|
| TC-01-01 | Sequential read, noreg | 36 | 512 | noreg | mem_file/hex | Assert rd_en_i and rd_clk_en_i; increment rd_addr_i each cycle | rd_data_o = mem[addr] after 1 cycle |
| TC-01-02 | Sequential read, reg | 36 | 512 | reg | mem_file/hex | Assert rd_en_i and rd_clk_en_i; increment rd_addr_i each cycle | rd_data_o = mem[addr] after 2 cycles |
| TC-01-03 | Full sweep, noreg | 36 | 512 | noreg | mem_file/hex | Read all RADDR_DEPTH locations in order | All locations match reference mem |
| TC-01-04 | Full sweep, reg | 36 | 512 | reg | mem_file/hex | Read all RADDR_DEPTH locations in order | All locations match reference mem |
| TC-01-05 | Boundary addresses | 18 | 1024 | reg | mem_file/hex | Read addr=0 and addr=RADDR_DEPTH-1 | Correct data at both boundaries |
| TC-01-06 | Random addresses | 36 | 512 | reg | mem_file/hex | 100 random address reads | rd_data_o matches mem[random_addr] |
| TC-01-07 | Repeated address | 9 | 2048 | noreg | mem_file/hex | Read same address 20 consecutive cycles | Stable, correct output each cycle |

---

### TG-02 — Read Enable (rd_en_i)

Verify rd_en_i qualifies the read output (behavioral change introduced in v2.2.0).

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | REGMODE | Stimulus | Expected Result |
|---|---|---|---|---|---|---|
| TC-02-01 | rd_en_i=0 at start | 36 | 512 | reg | rd_en_i=0, drive valid addresses | rd_data_o not updated; holds initial value |
| TC-02-02 | rd_en_i de-asserted mid-seq | 36 | 512 | reg | Assert rd_en_i for 8 cycles, then de-assert | Output freezes when rd_en_i de-asserted |
| TC-02-03 | rd_en_i toggle every cycle | 18 | 1024 | noreg | Alternate rd_en_i=1/0 each cycle | Output updates only on cycles where rd_en_i=1 |
| TC-02-04 | rd_en_i=1 resumes | 36 | 512 | reg | De-assert then re-assert rd_en_i | Correct data resumes on re-assertion |

---

### TG-03 — Read Clock Enable (rd_clk_en_i)

Verify rd_clk_en_i gate function on the EBR address register and read pipeline.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | REGMODE | Stimulus | Expected Result |
|---|---|---|---|---|---|---|
| TC-03-01 | rd_clk_en_i=0 holds output | 36 | 512 | noreg | De-assert rd_clk_en_i; drive changing addresses | rd_data_o retains last valid value |
| TC-03-02 | rd_clk_en_i=0 holds output, reg | 36 | 512 | reg | De-assert rd_clk_en_i; drive changing addresses | rd_data_o retains last valid value |
| TC-03-03 | rd_clk_en_i re-assertion | 36 | 512 | reg | De-assert for 10 cycles then re-assert | New address registered and correct data appears |
| TC-03-04 | rd_clk_en_i toggle pattern | 18 | 1024 | noreg | Alternately gate every other cycle | Verify output only advances when rd_clk_en_i=1 |
| TC-03-05 | Cascaded config + rd_clk_en_i | 36 | 1024 | reg | Toggle rd_clk_en_i across bank boundary | No erroneous data from wrong bank (v2.5.0 fix) |

---

### TG-04 — Output Clock Enable (rd_out_clk_en_i)

Verify the secondary clock enable on the output register. Requires `REGMODE="reg"` and `OUTPUT_CLK_EN=1`.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | OUTPUT_CLK_EN | Stimulus | Expected Result |
|---|---|---|---|---|---|---|
| TC-04-01 | rd_out_clk_en_i=0 freezes output | 36 | 512 | 1 | rd_clk_en_i=1; rd_out_clk_en_i=0 | Output register frozen; rd_data_o holds last value |
| TC-04-02 | rd_out_clk_en_i=1 normal | 36 | 512 | 1 | Both enables=1 | rd_data_o = mem[addr] after 2 cycles |
| TC-04-03 | rd_out_clk_en_i toggle mid-seq | 36 | 512 | 1 | Assert rd_out_clk_en_i for 5 cycles, then de-assert | Output updates only when rd_out_clk_en_i=1 |
| TC-04-04 | OUTPUT_CLK_EN=0 — no effect | 36 | 512 | 0 | Toggle rd_out_clk_en_i freely | rd_data_o updates normally regardless |
| TC-04-05 | Both enables de-asserted | 18 | 1024 | 1 | rd_clk_en_i=0 and rd_out_clk_en_i=0 | rd_data_o holds last value |

---

### TG-05 — Reset Behavior

Verify reset clears the output register; confirm REGMODE=noreg is reset-insensitive.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | REGMODE | RESETMODE | Stimulus | Expected Result |
|---|---|---|---|---|---|---|---|
| TC-05-01 | Sync reset clears output | 36 | 512 | reg | sync | Assert rst_i for 5 cycles; de-assert | rd_data_o = 0 while rst_i=1; normal reads resume after |
| TC-05-02 | Sync reset during read | 36 | 512 | reg | sync | Assert rst_i mid-sequence | rd_data_o immediately clears to 0 on next rising edge |
| TC-05-03 | Sync reset release | 36 | 512 | reg | sync | De-assert rst_i; issue read | rd_data_o = mem[addr] after latency |
| TC-05-04 | Async reset asserted | 36 | 512 | reg | async | Assert rst_i asynchronously (mid-cycle) | rd_data_o clears to 0 immediately, before next clock edge |
| TC-05-05 | Async reset sync release | 36 | 512 | reg | async | De-assert rst_i; issue read | Output register operational after one cycle |
| TC-05-06 | noreg — rst_i has no effect | 36 | 512 | noreg | sync | Assert rst_i; read valid address | rd_data_o = mem[addr]; rst_i does not clear output |

---

### TG-06 — Memory Initialization

Verify all initialization modes produce correct data across the full address range.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | user_init_mode | INIT_FILE_FORMAT | Expected Result |
|---|---|---|---|---|---|---|
| TC-06-01 | all_zero init | 36 | 512 | all_zero | N/A | All RADDR_DEPTH locations read 0 |
| TC-06-02 | all_one init | 36 | 512 | all_one | N/A | All RADDR_DEPTH locations read all-1s |
| TC-06-03 | mem_file hex random | 36 | 512 | mem_file | hex | All locations match loaded hex file |
| TC-06-04 | mem_file binary random | 18 | 1024 | mem_file | binary | All locations match loaded binary file |
| TC-06-05 | mem_file alternating pattern | 9 | 2048 | mem_file | hex | Alternating 0xAA.../0x55... verified |
| TC-06-06 | mem_file addr-as-data | 36 | 512 | mem_file | hex | mem[i] = i for all i |
| TC-06-07 | all_zero, narrow width | 1 | 16384 | all_zero | N/A | All 16384 locations read 0 |
| TC-06-08 | mem_file binary narrow | 4 | 4096 | mem_file | binary | All 4096 locations match binary file |

---

### TG-07 — LIFCL EBR Tile Configuration Coverage

Exercise each native LIFCL EBR data-width/depth configuration to confirm correct tile selection and single-tile operation.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | EBR Tiles | Init Mode | Expected Result |
|---|---|---|---|---|---|---|
| TC-07-01 | Minimum config | 1 | 2 | 1 | all_zero | 2-location, 1-bit wide ROM reads correctly |
| TC-07-02 | 1-bit × 16384 (max depth) | 1 | 16384 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-03 | 2-bit × 8192 | 2 | 8192 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-04 | 4-bit × 4096 | 4 | 4096 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-05 | 9-bit × 2048 (parity) | 9 | 2048 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-06 | 18-bit × 1024 (parity) | 18 | 1024 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-07 | 36-bit × 512 (default) | 36 | 512 | 1 | mem_file/hex | Full depth sweep passes |
| TC-07-08 | Non-aligned width | 12 | 512 | 1 | mem_file/hex | IP selects optimal tile; reads correct |

---

### TG-08 — EBR Cascading

Verify address-dimension and data-dimension cascading, including the v2.5.0 clock-enable fix.

| TC ID | Test Case Name | RDATA_WIDTH | RADDR_DEPTH | EBR Tiles | Stimulus | Expected Result |
|---|---|---|---|---|---|---|
| TC-08-01 | Addr cascade ×2 | 36 | 1024 | 2 | Sequential sweep of all 1024 locations | All locations read correctly; bank boundary transparent |
| TC-08-02 | Addr cascade ×4 | 36 | 2048 | 4 | Sequential sweep | All 2048 locations read correctly |
| TC-08-03 | Data cascade ×2 (wide) | 72 | 512 | 2 | Full sweep | All 72-bit words correct across both tiles |
| TC-08-04 | Data cascade ×4 | 144 | 512 | 4 | Full sweep | All 144-bit words correct |
| TC-08-05 | Both cascades | 72 | 1024 | 4 | Sequential sweep | All 1024 × 72-bit locations correct |
| TC-08-06 | Bank boundary read | 36 | 1024 | 2 | Read addr=511 (last in bank 0) and addr=512 (first in bank 1) | Each address returns its own correct data |
| TC-08-07 | Addr cascade + clk_en toggle | 36 | 1024 | 2 | Toggle rd_clk_en_i while reading across bank boundary | v2.5.0: no spurious data from wrong bank |
| TC-08-08 | Addr cascade + reg mode | 36 | 2048 | 4 | Sequential sweep, REGMODE=reg | 2-cycle latency; all data correct across all banks |

---

### TG-09 — ECC

Verify error detection/correction outputs and data-width constraints for ECC on LIFCL.

| TC ID | Test Case Name | RDATA_WIDTH | ECC_ENABLE | Stimulus | Expected Result |
|---|---|---|---|---|---|
| TC-09-01 | ECC disabled — outputs = 0 | 36 | 0 | Read any address | one_err_det_o=0, two_err_det_o=0 at all times |
| TC-09-02 | ECC enabled, clean data | 32 | 1 | Read all locations, no errors injected | one_err_det_o=0, two_err_det_o=0; rd_data_o correct |
| TC-09-03 | ECC, minimum width (32) | 32 | 1 | Full sweep | All data correct; no false error flags |
| TC-09-04 | ECC, maximum width (64) | 64 | 1 | Full sweep | All data correct; no false error flags |
| TC-09-05 | SEC — single-bit error | 32 | 1 | Inject 1-bit flip into stored data | one_err_det_o=1 for one cycle; rd_data_o carries corrected value |
| TC-09-06 | DED — double-bit error | 32 | 1 | Inject 2-bit flip into stored data | two_err_det_o=1; one_err_det_o=0 |
| TC-09-07 | ECC error recovery | 36 | 1 | SEC event followed by clean reads | Error outputs deassert after corrected read; clean reads follow |

---

### TG-10 — DRC and Parameter Validation

Verify the plugin enforces all dependency rules at configuration time.

| TC ID | Test Case Name | Parameter Under Test | Invalid Value | Expected Plugin Response |
|---|---|---|---|---|
| TC-10-01 | Depth below minimum | RADDR_DEPTH | 1 | Error: "Address depth is out of range!" |
| TC-10-02 | Depth above maximum | RADDR_DEPTH | 65537 | Error: "Address depth is out of range!" |
| TC-10-03 | Width below minimum | RDATA_WIDTH | 0 | Error: "Data width is out of range!" |
| TC-10-04 | Width above maximum | RDATA_WIDTH | 513 | Error: "Data width is out of range!" |
| TC-10-05 | Total bits exceed LIFCL limit | RDATA_WIDTH=512, RADDR_DEPTH=4096 | 2,097,152 bits > 1,548,288 | Error: "Total memory size exceeds the resource limitation!" |
| TC-10-06 | OUTPUT_CLK_EN=True + REGMODE=False | OUTPUT_CLK_EN | True (with REGMODE=False) | Error: "Enable Output ClockEn is turned on, while Enable Output Register is turned off" |
| TC-10-07 | RESETMODE=async + REGMODE=False | RESETMODE | "async" (with REGMODE=False) | Error: "Reset assertion is set to async, while Enable Output Register is turned off" |
| TC-10-08 | ECC + RDATA_WIDTH=65 | RDATA_WIDTH | 65 (with ECC_ENABLE=True) | Error: DRC rejects configuration |
| TC-10-09 | mem_file with no path | user_init_file | "-" (with user_init_mode=mem_file) | Error: "Initialization file is mandatory" |

---

## 8. Pass / Fail Criteria

### 8.1 Simulation Pass Criteria

A test case **passes** when ALL of the following conditions are met:

1. The `chk` flag in `tb_top.v` remains `1'b1` throughout the simulation.
2. The simulation ends with the string `"SIMULATION PASSED"`.
3. No `$display` error messages are emitted by the checker.
4. No `X` or `Z` propagation occurs on `rd_data_o` during valid read windows.
5. `one_err_det_o` and `two_err_det_o` behave exactly as specified per TG-09.

A test case **fails** when ANY of the following occurs:

- `chk` is driven to `1'b0` by an assertion mismatch.
- Simulation terminates with `"SIMULATION FAILED"`.
- `rd_data_o !== mem[expected_addr]` for any valid read.
- For `rd_clk_en_i=0`: `rd_data_o !== rd_data_captured_before_hold`.
- For `rst_i=1` with `REGMODE="reg"`: `rd_data_o !== 0`.

### 8.2 DRC Pass Criteria

A DRC test case **passes** when the plugin correctly rejects the invalid configuration and emits the expected error message string. No RTL generation should occur for invalid configurations.

---


*End of Document*
