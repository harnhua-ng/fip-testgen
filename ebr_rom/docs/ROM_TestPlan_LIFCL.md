# ROM FIP — Test Plan

*lscc_rom v2.5.0 · LIFCL*

| Field | Value |
|---|---|
| IP name | ROM (`rom`) |
| VLNV | `latticesemi.com:module:rom:2.5.0` |
| Module | `lscc_rom` |
| Version | 2.5.0 |
| Target Family | `LIFCL` |
| Families normalizing to target | `LFD2NX`, `LFCPNX`, `LFMXO5`, `UT24C`, `UT24CP` — all normalize to `LIFCL` in the RTL and share the hardened 16 Kb EBR implementation path, so they are covered implicitly (per 1.2). `UT24C` and `UT24CP` carry an open plugin/RTL budget conflict — see `SPEC-GAP-05`. |
| Tool | Radiant ≥ 2022.1 |
| Source specification | `ROM_FunctionalSpec.md`, 2026-08-20 |
| Date | 2026-08-27 |

## 1. Scope & Objectives

- **Functional verification only** for ROM (`lscc_rom`) targeting the `LIFCL` device family. Performance and timing characterisation are out of scope; those are owned by the Hardware team. Every timing statement verified here is a cycle-count relationship referenced to the rising edge of `rd_clk_i` (per 1.5.7).
- **Parameters and ports are taken from the top-level RTL module declaration** in `rtl/lscc_rom.v` — the port roster from its module header at lines 208-221 and the parameter roster from lines 59-73, as tabulated in spec 1.3 and 1.4. Only user-configurable parameters (as exposed in the Radiant IP configuration GUI) are exercised. Internal-only parameters — `FAMILY`, `T_FAMILY`, `RADDR_WIDTH`, `ECC_ENABLE`, `INIT_MODE`, `INIT_FILE`, `INIT_DATA_TYPE`, `INIT_DATA_TYPE_IN`, `user_init_mode`, `Total Memory bits`, `MEM_ID`, `MEM_SIZE`, `buff_init_file`, and the 128 bulk initialization vectors — are not directly tested; their derived values are observed where a test depends on them.
- **Only legal parameter combinations** permitted by the GUI dependency rules (spec 1.6, 1.7) are used. Every configuration satisfies all visibility, editability, and DRC rules simultaneously, including the `LIFCL` total-memory budget of 1,548,288 bits imposed by Rule 1.
- **Transient-behavior rule.** Any case checking the transient behavior of a signal — asynchronous assertion edges, glitch behavior, same-cycle enable transitions — is `Radiant Compilation` and is never simulated. All enable and reset stimulus in the simulated cases changes only on cycle boundaries and is held for whole cycles.

Type legend (use these three labels verbatim on every test case):

- **Radiant Compilation** — Radiant project build only; no simulation waveform required. IP generation for a `LIFCL` device succeeds, synthesis and map complete without error, and the expected structure results (port tie-offs, dangling outputs, GUI editability, derived parameter values, EBR tiling).
- **Sim Only** — functional simulation only. The IP is generated so that the initialization image is built into the model, but no Radiant synthesis or map run is required.
- **Both** — Radiant compilation and functional simulation.

## 2. Coverage Summary

| Total TCs | Radiant Compilation | Sim Only | Both |
|---|---|---|---|
| 34 | 12 | 10 | 12 |

Parameters covered: `RADDR_DEPTH` (min `2`, median `1024`, max `65536`, plus `512`, `1000`, `2048`, `3024`); `RDATA_WIDTH` (min `1`, median `18`, max `512`, plus `8`, `36`); `REGMODE` (`True`, `False`); `RESETMODE` (`sync`, `async`, and `sync` read-only under `REGMODE=False`); `INIT_FILE_FORMAT` (`binary`, `hex`); `OUTPUT_CLK_EN` (`False`, `True`, and `False` read-only under `REGMODE=False`); `user_init_file` (a named existing file — the only legal state per Rule 9). Ports covered: `rd_clk_i`, `rst_i`, `rd_clk_en_i`, `rd_out_clk_en_i`, `rd_en_i`, `rd_addr_i`, `rd_data_o`, `one_err_det_o`, `two_err_det_o`.

Median selection for the two numeric parameters: both ranges span orders of magnitude, so the documented RTL default is taken as the representative mid-range value — `RADDR_DEPTH=1024`, a power of two that fills exactly one `LIFCL` block at the default width, and `RDATA_WIDTH=18`, the top of the narrow `LIFCL` single-port implementation-width band (per 1.5.1). The budget of 1,548,288 bits makes the two maxima jointly illegal, so each maximum is paired with a partner value that keeps the product legal: `65536 × 18 = 1,179,648`, and `3024 × 512 = 1,548,288`, exactly the budget, which Rule 1 permits since it forbids only exceeding it.

## 3. Coverage Matrix

One row per test case, one column per user-configurable parameter, in spec 1.4 order followed by `user_init_file` from spec 1.6. The value a test specifically sweeps — its subject — is set in **bold**, so each column can be scanned for its covered values.

| TC ID | Test Name | Type | RADDR_DEPTH | RDATA_WIDTH | REGMODE | RESETMODE | INIT_FILE_FORMAT | OUTPUT_CLK_EN | user_init_file |
|---|---|---|---|---|---|---|---|---|---|
| TC-ROM-001 | Default configuration generation and read | Both | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-002 | Minimum address depth | Radiant Compilation | **2** | 1 | True | sync | binary | False | `rom_2x1.bin` |
| TC-ROM-003 | Median address depth, full-range read | Sim Only | **1024** | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-004 | Maximum address depth | Radiant Compilation | **65536** | 18 | True | sync | binary | False | `rom_65536x18.bin` |
| TC-ROM-005 | Address depth at the exact LIFCL budget | Radiant Compilation | **3024** | 512 | True | sync | hex | False | `rom_3024x512.hex` |
| TC-ROM-006 | Non-power-of-two address depth | Radiant Compilation | **1000** | 8 | True | sync | hex | False | `rom_1000x8.hex` |
| TC-ROM-007 | Minimum data width | Both | 1024 | **1** | True | sync | binary | False | `rom_1024x1.bin` |
| TC-ROM-008 | Median data width, every bit position | Sim Only | 1024 | **18** | True | sync | binary | False | `rom_1024x18_walk.bin` |
| TC-ROM-009 | Maximum data width with data-axis tiling | Both | 2048 | **512** | True | sync | hex | False | `rom_2048x512.hex` |
| TC-ROM-010 | Data width 36 selects the wide LIFCL branch | Radiant Compilation | 512 | **36** | True | sync | binary | False | `rom_512x36.bin` |
| TC-ROM-011 | Output register enabled — two-cycle latency | Sim Only | 1024 | 18 | **True** | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-012 | Output register disabled — one-cycle latency and dependent collapse | Both | 1024 | 18 | **False** | sync (read-only) | binary | False (read-only) | `rom_1024x18.bin` |
| TC-ROM-013 | Synchronous reset of the output register | Both | 1024 | 18 | True | **sync** | binary | True | `rom_1024x18.bin` |
| TC-ROM-014 | Asynchronous reset assertion | Radiant Compilation | 1024 | 18 | True | **async** | binary | False | `rom_1024x18.bin` |
| TC-ROM-015 | Binary-format initialization | Both | 1024 | 18 | True | sync | **binary** | False | `rom_1024x18.bin` |
| TC-ROM-016 | Hexadecimal-format initialization | Both | 1024 | 18 | True | sync | **hex** | False | `rom_1024x18.hex` |
| TC-ROM-017 | Output-register clock enable not requested | Radiant Compilation | 1024 | 18 | True | sync | binary | **False** | `rom_1024x18.bin` |
| TC-ROM-018 | Output-register clock enable requested | Both | 1024 | 18 | True | sync | binary | **True** | `rom_1024x18.bin` |
| TC-ROM-019 | Comments, `@address` records and surplus words | Both | 1024 | 18 | True | sync | hex | False | **`rom_sparse.hex`** |
| TC-ROM-020 | Maximum depth, output register, separate enable, hex | Sim Only | **65536** | 18 | **True** | sync | **hex** | **True** | `rom_65536x18.hex` |
| TC-ROM-021 | Maximum width, output register bypassed, hex | Both | 2048 | **512** | **False** | sync (read-only) | **hex** | False (read-only) | `rom_2048x512.hex` |
| TC-ROM-022 | At-budget dimensions, separate enable, asynchronous reset | Radiant Compilation | **3024** | **512** | **True** | **async** | binary | **True** | `rom_3024x512.bin` |
| TC-ROM-023 | Minimum dimensions, output register bypassed | Both | **2** | **1** | **False** | sync (read-only) | **hex** | False (read-only) | `rom_2x1.hex` |
| TC-ROM-024 | `rd_clk_en_i` freezes the memory array | Sim Only | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-025 | `rd_out_clk_en_i` freezes the output register | Sim Only | 1024 | 18 | True | sync | binary | True | `rom_1024x18.bin` |
| TC-ROM-026 | `rd_en_i` as a second series enable | Sim Only | 1024 | 18 | True | sync | binary | True | `rom_1024x18.bin` |
| TC-ROM-027 | `rd_en_i` ignored without the separate enable | Sim Only | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-028 | `rst_i` inert with the output register bypassed | Sim Only | 1024 | 18 | False | sync (read-only) | binary | False (read-only) | `rom_1024x18.bin` |
| TC-ROM-029 | `rd_addr_i` above the configured depth | Sim Only | 1000 | 8 | True | sync | hex | False | `rom_1000x8.hex` |
| TC-ROM-030 | ECC status outputs inert and dangling | Both | 1024 | 36 | True | sync | binary | False | `rom_1024x36.bin` |
| TC-ROM-031 | Memory Initialization read-only; fill options unreachable | Radiant Compilation | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-032 | Initialization-data update control hidden on LIFCL | Radiant Compilation | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |
| TC-ROM-033 | Derived read-only settings | Radiant Compilation | 1000 | 8 | True | sync | hex | False | `rom_1000x8.hex` |
| TC-ROM-034 | Default-parameter compilation smoke test | Radiant Compilation | 1024 | 18 | True | sync | binary | False | `rom_1024x18.bin` |

**Feature coverage** — every feature of spec 1.1 with the tests that cover it.

| Feature (spec 1.1) | Covering TC IDs |
|---|---|
| Synchronous single-port ROM in EBR, one read clock, one read address bus, one read data bus | TC-ROM-001, 003, 011, 012, 024, 029 |
| Configurable address depth, 2 to 65536, bounded by the family memory budget | TC-ROM-002, 003, 004, 005, 006, 022, 023 |
| Configurable data width, 1 to 512 bits | TC-ROM-007, 008, 009, 010, 021, 023 |
| Optional output register (`REGMODE`), one-cycle latency when disabled and two-cycle when enabled; default enabled | TC-ROM-001, 011, 012, 021, 023 |
| Optional separate output-register clock enable (`OUTPUT_CLK_EN`), editable only with the output register; default disabled | TC-ROM-017, 018, 020, 025 |
| Selectable synchronous or asynchronous reset assertion, editable only with the output register; default synchronous | TC-ROM-013, 014, 022, 028 |
| Memory initialization from a file in hexadecimal or binary format, with `//` and `/* */` comments and `@address` records | TC-ROM-015, 016, 019 |
| Automatic tiling and address cascading across multiple EBR blocks | TC-ROM-004, 005, 009, 020, 021 |
| Four implementation paths selected from the normalized architecture | TC-ROM-001 (LIFCL narrow, 1 to 18 bits), TC-ROM-010 (LIFCL wide, 32/36 bits). The `iCE40UP`, AP6, and generic paths are non-target — see Exclusions |
| Static or dynamic initialization-data handling, a user choice on `LAV-AT` only and forced to dynamic elsewhere | TC-ROM-032 |
| RTL present, not exposed: single-bit and double-bit ECC error detection | TC-ROM-010, 030 |
| RTL present, not exposed: all-zeros and all-ones memory fill | TC-ROM-031 |
| Requires Radiant 2022.1 or later | TC-ROM-001, 034 |

## Test Groups

Unless a case states otherwise, every configuration names an existing initialization file (Rule 9), every generation step targets a `LIFCL` device under Radiant 2022.1 or later, and every simulated case compares `rd_data_o` against a reference image built from the named file by the parsing rules of 1.5.3.

### G1 · Baseline

#### TC-ROM-001 — Default configuration generation and read `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin` — 1024 lines of binary digits, one 18-bit word per line, each word distinct

**Procedure**

1. Generate the IP for a `LIFCL` device under Radiant 2022.1 or later, setting `RADDR_DEPTH`, `RDATA_WIDTH` and `INIT_FILE_FORMAT` explicitly rather than accepting the values the GUI opens at (see `SPEC-GAP-06`).
2. Run synthesis and map.
3. Read the `Total Memory bits` field and inspect the generated module boundary.
4. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and present addresses 0, 1, 2, 511, 1023 on five successive cycles.

**Pass Criteria**

- Generation, synthesis and map complete with no error and no DRC violation.
- The module boundary presents one clock, one 10-bit read address bus and one 18-bit read data bus, with no write interface, the internal write path being tied inactive at elaboration (per 1.1, 1.5.1).
- `Total Memory bits` displays `18432`, the product of depth and width (per 1.7 Rule 15).
- Each addressed word appears on `rd_data_o` two cycles after its address is captured, one stage in the memory array and one in the primitive output register (per 1.5.7, `REGMODE` = `reg` with `OUTPUT_CLK_EN` = `0`).

### G2 · RADDR_DEPTH — Address Depth

Legal range 2 to 65536 (Rule 2, whose lower bound of 2 is tighter than the Rule 1 DRC bound of 1), further bounded so that `RADDR_DEPTH × RDATA_WIDTH` does not exceed 1,548,288 bits on `LIFCL` (Rule 1). Always visible, always editable (per 1.6).

#### TC-ROM-002 — Minimum address depth `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=2 — the declared minimum, paired with `RDATA_WIDTH=1` so the product is trivially legal
- RDATA_WIDTH=1
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_2x1.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the generated port widths for `rd_addr_i` and `rd_data_o`.

**Pass Criteria**

- Generation completes with no DRC violation: depth 2 is the declared minimum (per 1.7 Rule 2) and the product of 2 bits is far inside the budget (per 1.7 Rule 1).
- `rd_addr_i` is 1 bit wide, the derived address width being `clog2(2)` (per 1.7 Rule 10, 1.3).
- `rd_data_o` is 1 bit wide (per 1.3).

#### TC-ROM-003 — Median address depth, full-range read `Sim Only`

**Configuration**

- RADDR_DEPTH=1024 — the median value; see the Coverage Summary for its selection
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` high.
3. Read every address from 0 through 1023 in ascending order, one address per cycle.

**Pass Criteria**

- All 1024 words match the reference image, each two cycles after its address is captured (per 1.5.7).
- No address in the range returns a duplicated or skipped word; the sequence read back is exactly the sequence stored.

#### TC-ROM-004 — Maximum address depth `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=65536 — the declared maximum, paired with `RDATA_WIDTH=18` because pairing it with the maximum width would exceed the budget
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_65536x18.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the `rd_addr_i` width, the number of EBR blocks along the address axis, and the high-address multiplexer pipeline.

**Pass Criteria**

- Generation completes with no DRC violation: depth 65536 is the declared maximum (per 1.7 Rule 2) and the product 1,179,648 bits is within the 1,548,288-bit budget (per 1.7 Rule 1).
- `rd_addr_i` is 16 bits wide (per 1.7 Rule 10).
- The memory is more than one block deep, so the low address bits reach every block in parallel while the high address bits select the presented block through a multiplexer whose select is pipelined by two stages for `REGMODE` = `reg` (per 1.5.5).
- Read latency and the port list are unchanged from TC-ROM-001, cascading being transparent at the boundary (per 1.5.5).

#### TC-ROM-005 — Address depth at the exact LIFCL budget `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=3024 — the largest depth that keeps the product legal at the maximum width
- RDATA_WIDTH=512
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_3024x512.hex`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Read the `Total Memory bits` field and confirm no DRC error is posted.
3. Inspect the `rd_addr_i` width and the tiling along both axes.

**Pass Criteria**

- `Total Memory bits` displays `1548288`, exactly the `LIFCL` budget (per 1.7 Rule 15 and the per-family budget table).
- Generation completes with no DRC violation: `check_addr_depth_data_width` must not fire, Rule 1 forbidding only that the product *exceed* the budget (per 1.7 Rule 1).
- `rd_addr_i` is 12 bits wide, the derived width being `clog2(3024)` (per 1.7 Rule 10).
- The memory is tiled along both the address and the data axis (per 1.5.5).

#### TC-ROM-006 — Non-power-of-two address depth `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1000 — a depth that is not a power of two
- RDATA_WIDTH=8
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1000x8.hex`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the derived address width and the generated `rd_addr_i` width.

**Pass Criteria**

- Generation completes with no DRC violation; the product 8,000 bits is within the budget (per 1.7 Rule 1).
- The derived address width is 10, being `clog2(1000)`, and the setting remains hidden and read-only (per 1.7 Rule 10).
- `rd_addr_i` is 10 bits wide (per 1.3).
- No `ERROR  --  Invalid input` is posted, the depth being above the Rule 2 lower bound of 2 (per 1.7 Rules 2, 10).

### G3 · RDATA_WIDTH — Data Width

Legal range 1 to 512 (Rules 3 and 4), bounded by the same `LIFCL` budget (Rule 1). Always visible, always editable (per 1.6).

#### TC-ROM-007 — Minimum data width `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=1 — the declared minimum, isolated at the median depth so the width is the only variable against TC-ROM-001
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x1.bin` — 1024 single-bit words alternating 1 and 0

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read addresses 0 through 7 and 1020 through 1023.

**Pass Criteria**

- Generation completes with no DRC violation; width 1 is the declared minimum (per 1.7 Rules 3, 4) and the product 1,024 bits is within the budget (per 1.7 Rule 1).
- `rd_data_o` is 1 bit wide (per 1.3).
- Every word read matches the reference image two cycles after its address is captured, so the alternating pattern appears without inversion or offset (per 1.5.7).

#### TC-ROM-008 — Median data width, every bit position `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18 — the median value and the top of the narrow `LIFCL` implementation band (per 1.5.1)
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18_walk.bin` — words 0 through 17 carry a walking one, words 18 through 35 a walking zero; a separate image from `rom_1024x18.bin` so the two are never confused

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` high.
3. Read addresses 0 through 35 in ascending order.

**Pass Criteria**

- Each of the 18 bit positions of `rd_data_o` is observed both set and clear across the sequence, so no bit of the data bus is stuck or transposed.
- Every word matches the reference image two cycles after its address is captured (per 1.5.7).

#### TC-ROM-009 — Maximum data width with data-axis tiling `Both`

**Configuration**

- RADDR_DEPTH=2048
- RDATA_WIDTH=512 — the declared maximum, paired with depth 2048 for a product of 1,048,576 bits
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_2048x512.hex` — words carrying distinct values in every bit field, including the most and least significant bits

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the number of EBR blocks along the data axis.
3. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read addresses 0, 1, 1023, 1024 and 2047.

**Pass Criteria**

- Generation completes with no DRC violation: width 512 is the declared maximum (per 1.7 Rules 3, 4) and the product 1,048,576 bits is within the budget (per 1.7 Rule 1).
- `rd_data_o` is 512 bits wide and the memory is tiled across more than one EBR along the data axis, the count on that axis being the requested width divided by the chosen implementation width, rounded up (per 1.5.5).
- Each 512-bit word matches the reference image in full, every bit included, two cycles after its address is captured, so the assembly from several blocks is transparent at the boundary (per 1.5.5, 1.5.7).
- Read latency and the port list are unchanged from TC-ROM-001 (per 1.5.5).

#### TC-ROM-010 — Data width 36 selects the wide LIFCL branch `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=512
- RDATA_WIDTH=36 — the only additional width that selects the wide `LIFCL` 32/36-bit implementation branch rather than the narrow 1-to-18-bit one (per 1.5.1)
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_512x36.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the instantiated block-memory primitive and the connection of the ECC status outputs.

**Pass Criteria**

- Generation completes with no DRC violation; the product 18,432 bits is within the budget (per 1.7 Rule 1).
- At a 36-bit implementation width the `LIFCL` path instantiates the hardened 16 Kb pseudo-dual-port EBR that carries ECC status pins, not the single-port EBR used for implementation widths of 1 to 18 bits (per 1.5.1). If the tool selects a different implementation width band, re-baseline the primitive assertion rather than failing the case — see `SPEC-GAP-03`.
- `ECC_ENABLE` being hidden and false, `one_err_det_o` and `two_err_det_o` remain forced to `0` and are left dangling by the generator (per 1.5.6).

### G4 · REGMODE — Output Register

Boolean, default `True` (`reg`). Always visible, always editable, and gates the editability of `OUTPUT_CLK_EN` and `RESETMODE` (per 1.6, 1.7 Rules 6 and 8).

#### TC-ROM-011 — Output register enabled — two-cycle latency `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True — the default value
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i`, raise `rd_clk_en_i` and hold it high, then present addresses `A0`, `A1`, `A2` on three successive cycles.
3. Separately drive `rd_out_clk_en_i` low for two whole cycles during the sweep.

**Pass Criteria**

- Each addressed word appears on `rd_data_o` two cycles after its address is captured, one stage in the memory array and one in the primitive output register (per 1.5.7, `REGMODE` = `reg` with `OUTPUT_CLK_EN` = `0`).
- Driving `rd_out_clk_en_i` has no effect, the generator having tied that port high in this configuration (per 1.5.7, 1.3).

#### TC-ROM-012 — Output register disabled — one-cycle latency and dependent collapse `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=False — the second enumerated value
- RESETMODE=sync — read-only in this configuration (per 1.7 Rule 8)
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False — read-only in this configuration (per 1.7 Rule 6)
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device and clear Enable Output Register.
2. Inspect the Enable Output ClockEn and Reset Assertion fields.
3. Generate, synthesize and map, then inspect the connection made to `rd_out_clk_en_i`.
4. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and present addresses `A0`, `A1`, `A2` on three successive cycles. Separately hold `rd_out_clk_en_i` low for two whole cycles, then `rd_en_i` low for two whole cycles, while the sweep continues.

**Pass Criteria**

- With `REGMODE` = `False` the Enable Output ClockEn field is not editable and holds `False`, and the Reset Assertion field is not editable and holds `sync` (per 1.6, 1.7 Rules 6, 8).
- Generation, synthesis and map complete with no DRC violation, and neither `check_output_clk_en` nor `check_resetmode` fires, neither dependent being able to reach its rejected value through the GUI (per 1.7 Rules 5, 7).
- Each addressed word appears on `rd_data_o` in the cycle after its address is captured — one-cycle read latency, the memory array being the only register stage on the data path (per 1.5.7, `noreg` case).
- Holding `rd_out_clk_en_i` low has no effect on `rd_data_o`, there being no output register for it to gate, and holding `rd_en_i` low likewise has no effect in this configuration (per 1.5.7, `noreg` bullets).

### G5 · RESETMODE — Reset Assertion — Requires REGMODE = True

String, default `sync`, options `sync` and `async`. Editable only while `REGMODE == True` (per 1.7 Rule 8); `async` is rejected by `check_resetmode` when `REGMODE` is `False` (per 1.7 Rule 7). Both values are therefore exercised with `REGMODE=True`, which is the only state in which either is selectable.

#### TC-ROM-013 — Synchronous reset of the output register `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync — the default value
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=True — legal because `REGMODE` is `True` (per 1.7 Rules 5, 6); exposes the output-register enable so that reset dominance over the enables can be observed
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, hold `rd_clk_en_i`, `rd_en_i` and `rd_out_clk_en_i` high and sweep addresses continuously.
3. Assert `rst_i` for three whole cycles mid-sweep, release it on a cycle boundary, and continue the same sweep for at least eight further cycles.
4. Separately assert `rst_i` for three whole cycles while `rd_clk_en_i`, `rd_en_i` and `rd_out_clk_en_i` are all held low.

**Pass Criteria**

- `rd_data_o` is all zeros for as long as `rst_i` is asserted and for the cycle after it is released, then follows the two-cycle pipeline normally (per 1.5.7 post-reset behaviour).
- After release, the words read from the same addresses match the reference image exactly, memory contents being established at configuration time and unaffected by reset (per 1.5.4).
- With the enables held low `rd_data_o` still goes to all zeros, reset dominating the clock enables (per 1.5.4).

#### TC-ROM-014 — Asynchronous reset assertion `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=async — the second enumerated value
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device and set Reset Assertion to `async`, confirming the field is editable.
2. Generate, synthesize and map.
3. Inspect the output-register reset structure and the reset release path in the mapped design.

**Pass Criteria**

- The Reset Assertion field is editable, `REGMODE` being `True` (per 1.7 Rule 8), and generation completes with no DRC violation, `check_resetmode` rejecting `async` only when `REGMODE` is `False` (per 1.7 Rule 7).
- The output register carries an asynchronous clear that clears it immediately rather than a synchronous one, and the register clears to all zeros (per 1.5.4).
- The reset release is synchronized to `rd_clk_i` (per 1.5.4).
- This case is not simulated: asynchronous assertion is transient behavior, which section 1 restricts to `Radiant Compilation`.

### G6 · INIT_FILE_FORMAT — Memory File Format

String, default `binary` (RTL; the metadata declares `hex` — see `SPEC-GAP-06`), options `binary` and `hex`. Editable only while `INIT_MODE == 'mem_file'` (per 1.7 Rule 12), which holds in every generated instance (per 1.7 Rule 11). The two cases below use functionally equivalent images so that the read-data comparison isolates the radix.

#### TC-ROM-015 — Binary-format initialization `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary — the default value
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin` — 1024 lines of binary digits, one 18-bit word per line, each word distinct

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read every address 0 through 1023 in order.

**Pass Criteria**

- Generation completes with no DRC violation: the named file satisfies `chk_file` (per 1.7 Rule 9), and the Memory File Format field is editable because the derived initialization mode is `mem_file` (per 1.7 Rules 11, 12).
- Every word read matches the reference image two cycles after its address is captured, each file line having been consumed right to left as binary digits (per 1.5.3, 1.5.7).

#### TC-ROM-016 — Hexadecimal-format initialization `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex — the second enumerated value
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.hex` — the same 1024 words as TC-ROM-015, written in hexadecimal digits

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read every address 0 through 1023 in order.

**Pass Criteria**

- Generation completes with no DRC violation.
- Every word read matches the same reference image as TC-ROM-015, two cycles after its address is captured, each file line having been consumed right to left as hexadecimal digits (per 1.5.3, 1.5.7).
- The two cases differ only in radix, which isolates `INIT_FILE_FORMAT` as the sole variable.

### G7 · OUTPUT_CLK_EN — Output Register Clock Enable — Requires REGMODE = True

Boolean, default `False`. Editable only while `REGMODE == True` (per 1.7 Rule 6); `True` is rejected by `check_output_clk_en` when `REGMODE` is `False` (per 1.7 Rule 5). Both values are exercised with `REGMODE=True`; the read-only collapse to `False` under `REGMODE=False` is covered structurally by TC-ROM-012.

#### TC-ROM-017 — Output-register clock enable not requested `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False — the default value
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. Inspect the instantiation of the generated module for the connection made to `rd_out_clk_en_i`, and identify which register forms the second pipeline stage.

**Pass Criteria**

- `rd_out_clk_en_i` is declared on the module boundary but tied high by the generator, `OUTPUT_CLK_EN` being false, so driving it can have no effect (per 1.3, 1.5.7).
- The second register stage is the hardened primitive internal output register (per 1.5.7, `OUTPUT_CLK_EN` = `0` case).
- Generation, synthesis and map complete with no error.

#### TC-ROM-018 — Output-register clock enable requested `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=True — the second enumerated value
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i`, `rd_en_i` and `rd_out_clk_en_i` high, and present addresses `A0`, `A1`, `A2` on three successive cycles.

**Pass Criteria**

- Generation completes with no DRC violation: `OUTPUT_CLK_EN` = `True` is legal because `REGMODE` is also `True` (per 1.7 Rules 5, 6).
- The second register stage is a fabric register whose enable is exposed on `rd_out_clk_en_i` rather than the primitive internal output register (per 1.5.7).
- Read latency remains two cycles: the word for `A0` reaches `rd_data_o` two cycles after `A0` was presented, exactly as with `OUTPUT_CLK_EN` = `0` (per 1.5.7, `OUTPUT_CLK_EN` = `1` case).

### G8 · user_init_file — Memory File

Any path other than the unset placeholder `-`, which `chk_file` rejects (per 1.7 Rule 9). Always visible, always editable (per 1.6). Only one legal state exists — a file is named — so file *content* is varied here rather than the parameter value.

#### TC-ROM-019 — Comments, `@address` records and surplus words `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_sparse.hex` — see the procedure for its construction

**Procedure**

1. Build `rom_sparse.hex` containing: `//` line comments; a `/* */` block comment on one line and another spanning three lines; an `@` record jumping to location `0x100` followed by data lines; a second `@` record jumping backwards to location `0x010`; a region between records that no data line reaches; and more data words in total than 1024 locations.
2. Generate for a `LIFCL` device; run synthesis and map.
3. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read locations 0, 0x010, 0x011, 0x0FF, 0x100, 0x101 and 1023.

**Pass Criteria**

- Generation completes with no DRC violation, the named file satisfying `chk_file` (per 1.7 Rule 9).
- Comments of both forms, including the multi-line block comment, are stripped before parsing and contribute no words (per 1.5.3).
- Each `@` record sets the location at which the next data line is stored, so words appear at `0x100` and `0x010` as directed and the file may skip regions (per 1.5.3).
- Locations the file never reaches read as zero (per 1.5.3).
- Words beyond 1024 locations are discarded and do not displace earlier content (per 1.5.3). Whether a warning accompanies the discard is not asserted — see `SPEC-GAP-07`.
- Every read matches the reference image built by these rules, two cycles after its address is captured (per 1.5.7).

### G9 · Cross-Parameter Legal Combinations

Interacting parameters exercised together. Every combination below is legal per spec 1.7: each product is within the 1,548,288-bit `LIFCL` budget (Rule 1); `OUTPUT_CLK_EN=True` and `RESETMODE=async` appear only with `REGMODE=True` (Rules 5 to 8); and where `REGMODE=False` both dependents are shown at the read-only values the GUI collapses them to.

#### TC-ROM-020 — Maximum depth, output register, separate enable, hex `Sim Only`

**Configuration**

- RADDR_DEPTH=65536 — maximum
- RDATA_WIDTH=18 — median; product 1,179,648 bits, within budget
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=True
- user_init_file=`rom_65536x18.hex`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i`, `rd_en_i` and `rd_out_clk_en_i` high.
3. Sweep addresses across a block boundary on the address axis — one address in the lowest block, then one in a higher block.
4. Drive `rd_clk_en_i` low for three whole cycles across that boundary crossing, then high again, changing it only on cycle boundaries.

**Pass Criteria**

- Every word read matches the reference image two cycles after its address is captured, including the words either side of the block boundary, cascading being transparent at the boundary (per 1.5.5, 1.5.7).
- While `rd_clk_en_i` is low, `rd_data_o` holds its last value (per 1.5.2).
- When `rd_clk_en_i` returns high the multiplexer presents the block matching the frozen array output rather than a stale selection, the high-address pipeline being clocked by `rd_clk_en_i` so that the selection stays aligned with the frozen array output (per 1.5.5). This is the behaviour the 2.5.0 release note refers to (per 2.0).
- No word is corrupted or duplicated across the freeze.

#### TC-ROM-021 — Maximum width, output register bypassed, hex `Both`

**Configuration**

- RADDR_DEPTH=2048
- RDATA_WIDTH=512 — maximum; product 1,048,576 bits, within budget
- REGMODE=False
- RESETMODE=sync — read-only under `REGMODE=False` (per 1.7 Rule 8)
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False — read-only under `REGMODE=False` (per 1.7 Rule 6)
- user_init_file=`rom_2048x512.hex`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read addresses 0, 1, 1023, 1024 and 2047.

**Pass Criteria**

- Generation completes with no DRC violation, and neither `check_output_clk_en` nor `check_resetmode` fires, both dependents being collapsed to their legal values by Rules 6 and 8 (per 1.7 Rules 5 to 8).
- Each 512-bit word matches the reference image in full one cycle after its address is captured — the maximum width combined with one-cycle latency, the memory array being the only register stage (per 1.5.7, `noreg` case).
- Data-axis tiling remains transparent at the boundary with the output register bypassed (per 1.5.5).

#### TC-ROM-022 — At-budget dimensions, separate enable, asynchronous reset `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=3024
- RDATA_WIDTH=512 — product 1,548,288 bits, exactly the `LIFCL` budget
- REGMODE=True
- RESETMODE=async
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=True
- user_init_file=`rom_3024x512.bin`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device, set the dimensions, then set both Enable Output ClockEn and Reset Assertion, confirming both fields are editable.
2. Generate, synthesize and map.
3. Inspect `Total Memory bits`, the tiling on both axes, the exposed output-register enable, and the asynchronous clear on the output register.

**Pass Criteria**

- Both dependent fields are editable, `REGMODE` being `True` (per 1.7 Rules 6, 8), and the combination generates with no DRC violation: `check_addr_depth_data_width`, `check_output_clk_en` and `check_resetmode` all pass simultaneously (per 1.7 Rules 1, 5, 7).
- `Total Memory bits` displays `1548288` (per 1.7 Rule 15).
- The memory is tiled on both axes and the second register stage is a fabric register with an exposed enable carrying an asynchronous clear (per 1.5.5, 1.5.7, 1.5.4).
- This case is not simulated: `RESETMODE=async` makes it a transient-behavior case, which section 1 restricts to `Radiant Compilation`.

#### TC-ROM-023 — Minimum dimensions, output register bypassed `Both`

**Configuration**

- RADDR_DEPTH=2 — minimum
- RDATA_WIDTH=1 — minimum; product 2 bits
- REGMODE=False
- RESETMODE=sync — read-only under `REGMODE=False`
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False — read-only under `REGMODE=False`
- user_init_file=`rom_2x1.hex`

**Procedure**

1. Generate for a `LIFCL` device; run synthesis and map.
2. In simulation, release `rst_i`, hold `rd_clk_en_i` high, and read address 0, then address 1, then address 0 again on successive cycles.

**Pass Criteria**

- Generation completes with no DRC violation: both minima together are legal, and the two dependents sit at the read-only values Rules 6 and 8 impose (per 1.7 Rules 1 to 8).
- `rd_addr_i` is 1 bit wide and `rd_data_o` is 1 bit wide (per 1.3, 1.7 Rule 10).
- Both locations match the reference image one cycle after each address is captured, and the second read of address 0 returns the same value as the first (per 1.5.7, `noreg` case).

### G10 · Port Behaviour

One test per behavioral input port, plus the two ECC status outputs. `rd_clk_i` carries no independent behavior to sweep — every case in this plan clocks all synchronous logic and the memory array on its rising edge (per 1.3, 1.5.2) — and `rd_data_o` is the observed output of every simulated case.

#### TC-ROM-024 — `rd_clk_en_i` freezes the memory array `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and sweep addresses continuously.
3. Hold `rd_clk_en_i` high for four whole cycles, low for three whole cycles while the address on `rd_addr_i` keeps changing, then high again, changing the enable only on cycle boundaries.

**Pass Criteria**

- While `rd_clk_en_i` is low, neither the captured address nor the array output changes and `rd_data_o` holds its last value; the addresses presented during the freeze are ignored (per 1.5.2).
- Both register stages being clocked by `rd_clk_en_i`, the single enable freezes the whole read pipeline (per 1.5.7).
- When the enable returns high the sweep resumes from the address then presented, at two-cycle latency, with no word corrupted or duplicated (per 1.5.2, 1.5.7).

#### TC-ROM-025 — `rd_out_clk_en_i` freezes the output register `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=True — required for this port to be active (per 1.5.7)
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` and `rd_en_i` high with a continuous address sweep.
3. Hold `rd_out_clk_en_i` high for three whole cycles, low for two whole cycles, then high again, changing it only on cycle boundaries.

**Pass Criteria**

- While `rd_out_clk_en_i` is low, `rd_data_o` repeats its previous value, only the output register being frozen (per 1.5.7, `OUTPUT_CLK_EN` = `1` case).
- The word in flight through the memory array during the low window is discarded rather than presented, the array having continued to advance under `rd_clk_en_i` (per 1.5.2).
- When the enable returns high, `rd_data_o` presents the word then arriving from the array, at two-cycle latency from its address (per 1.5.7).

#### TC-ROM-026 — `rd_en_i` as a second series enable `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=True — `rd_en_i` affects the output only with `REGMODE` = `reg`, `OUTPUT_CLK_EN` true, and a target normalizing to `LIFCL` (per 1.3, 1.5.2)
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` and `rd_out_clk_en_i` high with a continuous address sweep.
3. Drive `rd_en_i` high for four whole cycles, low for two whole cycles, then high again, changing it only on cycle boundaries.

**Pass Criteria**

- While `rd_en_i` is high together with `rd_out_clk_en_i`, the output register captures and `rd_data_o` tracks the sweep at two-cycle latency (per 1.5.7).
- While `rd_en_i` is low the output register does not capture and `rd_data_o` repeats its previous value, `rd_en_i` being a second series enable on the same register on the `LIFCL` path, where both it and `rd_out_clk_en_i` must be high for a capture (per 1.5.2, 1.5.7).

#### TC-ROM-027 — `rd_en_i` ignored without the separate enable `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` high with a continuous address sweep.
3. Hold `rd_en_i` low for four whole cycles, then high for four whole cycles.

**Pass Criteria**

- `rd_data_o` continues to track the address sweep at two-cycle latency throughout, unaffected by the state of `rd_en_i`: it affects the output only when `REGMODE` is `reg`, `OUTPUT_CLK_EN` is true, and the target normalizes to `LIFCL`, and is ignored in every other configuration (per 1.3, 1.5.2).

#### TC-ROM-028 — `rst_i` inert with the output register bypassed `Sim Only`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=False
- RESETMODE=sync — read-only under `REGMODE=False`
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False — read-only under `REGMODE=False`
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, hold `rd_clk_en_i` high and sweep addresses continuously.
3. Assert `rst_i` for three whole cycles mid-sweep and release it on a cycle boundary.

**Pass Criteria**

- `rd_data_o` continues to track the sweep at one-cycle latency throughout the reset window, unaffected by `rst_i`: reset reaches only the output register, and with `REGMODE` = `noreg` there is no output register, so it has no effect on `rd_data_o` on the hardened paths (per 1.5.4, 1.5.7).
- Memory contents are unaffected: the words read after release match the reference image (per 1.5.4).

#### TC-ROM-029 — `rd_addr_i` above the configured depth `Sim Only`

**Configuration**

- RADDR_DEPTH=1000 — a depth that is not a power of two, so addresses above `RADDR_DEPTH - 1` remain representable in the 10-bit address bus
- RDATA_WIDTH=8
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1000x8.hex`

**Procedure**

1. Generate the IP for this configuration for a `LIFCL` device; no synthesis or map run is required for this case.
2. In simulation, release `rst_i` and hold `rd_clk_en_i` high.
3. Read address 999, then 1000, then 1023, then 999 and 0 again, on successive cycles.

**Pass Criteria**

- Addresses 999 and 0 match the reference image at two-cycle latency, both before and after the out-of-range accesses (per 1.5.7).
- Addresses 1000 and 1023 reach the memory array unmodified and return whatever the underlying block holds at that location, the IP performing no address-range checking (per 1.5.2).
- No error is flagged, no `X` propagates onto `rd_data_o`, and the pipeline is not disturbed. The value returned for an out-of-range address is not itself a pass criterion — see `SPEC-GAP-04`.

#### TC-ROM-030 — ECC status outputs inert and dangling `Both`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=36 — the wide `LIFCL` branch, the only `LIFCL` implementation width whose primitive carries error-detect pins (per 1.5.1, 1.5.6)
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x36.bin`

**Procedure**

1. Inspect the IP configuration GUI for any ECC control.
2. Generate for a `LIFCL` device; run synthesis and map, then inspect the instantiation site for the connection of `one_err_det_o` and `two_err_det_o`.
3. In simulation, sweep addresses for at least 64 cycles while sampling both outputs every cycle.

**Pass Criteria**

- No ECC control appears in the GUI: `ECC_ENABLE` is unconditionally hidden and defaults to `False` (per 1.5.6, 1.1).
- The generator leaves `one_err_det_o` and `two_err_det_o` unconnected at the instantiation site, both being marked dangling while ECC is off (per 1.5.6, 1.3).
- In simulation both outputs are driven to constant `0` for the entire run on this hardened `LIFCL` path (per 1.5.6). Whether this configuration tiles across more than one block is not derivable from the specification (see `SPEC-GAP-01`), so the criterion is the constant `0`, which 1.5.6 states holds both for a single block and for a cascaded array.
- The product 36,864 bits is within the budget, so generation completes with no DRC violation (per 1.7 Rule 1).

### G11 · DRC and Radiant Compilation Checks

The following spec 1.7 rules are exercised implicitly by the configurations above: no case feeds an illegal value, so each rule is confirmed by the absence of its error rather than by provoking it.

1. `DRC-1` — Rule 1, total memory budget and depth/width bounds via `check_addr_depth_data_width`: every configuration keeps `RADDR_DEPTH × RDATA_WIDTH` at or below 1,548,288 bits, with TC-ROM-005 and TC-ROM-022 sitting exactly on the limit.
2. `DRC-2` — Rule 2, `RADDR_DEPTH` in [2, 65536]: both endpoints generated by TC-ROM-002 and TC-ROM-004.
3. `DRC-3` — Rule 3, `RDATA_WIDTH` in [1, 512] via `check_data_width`: both endpoints generated by TC-ROM-007 and TC-ROM-009.
4. `DRC-4` — Rule 4, the declared `RDATA_WIDTH` value range, same endpoints.
5. `DRC-5` — Rule 5, `check_output_clk_en`: never fires, `OUTPUT_CLK_EN=True` appearing only with `REGMODE=True` (TC-ROM-013, 018, 020, 022, 025, 026).
6. `DRC-6` — Rule 6, `OUTPUT_CLK_EN` editability: the read-only collapse to `False` under `REGMODE=False` is observed by TC-ROM-012 and used by TC-ROM-021, 023, 028.
7. `DRC-7` — Rule 7, `check_resetmode`: never fires, `RESETMODE=async` appearing only with `REGMODE=True` (TC-ROM-014, 022).
8. `DRC-8` — Rule 8, `RESETMODE` editability: the read-only collapse to `sync` under `REGMODE=False` is observed by TC-ROM-012.
9. `DRC-9` — Rule 9, `chk_file`: every configuration names an existing file, so the mandatory-file check passes in all 34 cases.
10. `DRC-10` — Rule 10, address-width derivation by `clog2`: asserted at four distinct depths by TC-ROM-002, 004, 005, 006, and again by TC-ROM-023 and TC-ROM-033.
11. `DRC-11` — Rules 11 and 12, initialization-mode derivation and Memory File Format editability: observed by TC-ROM-031 and relied on by TC-ROM-015, 016.
12. `DRC-12` — Rule 15, `Total Memory bits` derivation: asserted by TC-ROM-001, 005, 022, 033.
13. `DRC-13` — Rules 17 and 18, initialization-data update control visibility and derivation: observed by TC-ROM-032.
14. `DRC-14` — Rules 13, 14, 16 and 19, the remaining derived read-only settings: observed by TC-ROM-033.

#### TC-ROM-031 — Memory Initialization read-only; fill options unreachable `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device.
2. Inspect the Memory Initialization field, the options it declares, and whether any can be selected.
3. Generate, then inspect the derived initialization mode of the generated instance, and confirm the Memory File Format field is editable.

**Pass Criteria**

- The Memory Initialization field is read-only and holds `mem_file`; although it declares `Initialize to all 0s` and `Initialize to all 1s`, neither can be selected (per 1.6, 1.7 Rule 11).
- The derived `INIT_MODE` is `mem_file`, which in turn satisfies the Memory File Format editability gate (per 1.7 Rules 11, 12).
- Generation, synthesis and map complete with no error.

#### TC-ROM-032 — Initialization-data update control hidden on LIFCL `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1024
- RDATA_WIDTH=18
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=binary
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1024x18.bin`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device and look for the Allow update of initialization data field.
2. Generate, then inspect the derived initialization-data type of the generated instance.

**Pass Criteria**

- The Allow update of initialization data field is not visible, being visible only when the normalized family is `LAV-AT` (per 1.6, 1.7 Rule 17).
- The derived `INIT_DATA_TYPE` is forced to `True`, which the RTL translates to dynamic initialization data (per 1.5.3, 1.7 Rule 18).
- Generation, synthesis and map complete with no error.

#### TC-ROM-033 — Derived read-only settings `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1000 — a non-round depth and width pair, so each derivation produces a distinctive value
- RDATA_WIDTH=8
- REGMODE=True
- RESETMODE=sync
- INIT_FILE_FORMAT=hex
- OUTPUT_CLK_EN=False
- user_init_file=`rom_1000x8.hex`

**Procedure**

1. Open the IP configuration GUI for a `LIFCL` device and read the `Total Memory bits` field, confirming it cannot be edited.
2. Generate, then inspect the derived address width, the memory identity and size tags, and the initialization file path recorded on the generated instance.

**Pass Criteria**

- `Total Memory bits` displays `8000` and is read-only (per 1.6, 1.7 Rule 15).
- The derived address width is 10 and remains hidden and read-only (per 1.7 Rule 10).
- `MEM_SIZE` is the string `8,1000` and `MEM_ID` is the IP instance directory name, both hidden and read-only (per 1.7 Rule 19).
- `INIT_FILE` is the path given in `user_init_file`, passed through unchanged (per 1.7 Rule 13).
- Generation, synthesis and map complete with no error.

#### TC-ROM-034 — Default-parameter compilation smoke test `Radiant Compilation`

**Configuration**

- RADDR_DEPTH=1024 — the RTL default
- RDATA_WIDTH=18 — the RTL default
- REGMODE=True — the default
- RESETMODE=sync — the default
- INIT_FILE_FORMAT=binary — the RTL default
- OUTPUT_CLK_EN=False — the default
- user_init_file=`rom_1024x18.bin` — a file must be named; the declared default `-` is rejected by Rule 9, see `SPEC-GAP-08`

**Procedure**

1. Create a fresh IP instance for a `LIFCL` device under the minimum supported Radiant version, 2022.1.
2. Change nothing except the memory file, which Rule 9 makes mandatory, and the three settings whose GUI defaults disagree with the RTL (see `SPEC-GAP-06`).
3. Generate, synthesize and map.

**Pass Criteria**

- Generation, synthesis and map complete with no error and no DRC violation, so the documented default configuration is buildable on the minimum supported tool version (per 1.1, header).
- The generated module matches TC-ROM-001 in port list and widths, this being the same configuration reached without explicit dimension entry.

## Exclusions and Rationale

| Excluded | Rationale |
|---|---|
| Performance and timing verification | Functional plan; fmax, setup/hold, and clock-frequency characterization are out of scope. The IP contains no constraint file of any supported type and applies no timing exceptions, so every path through it is timed by the enclosing design clock definition on `rd_clk_i` (per 1.5.7, 1.5.8). |
| Non-target device families | `iCE40UP` — hardened 4 Kb pseudo-dual-port EBR, `rd_en_i` without effect, no ECC status (per 1.2, 1.5.1). The AP6 group `LATG1`, `LAV-AT`, `ap6a00`, `ap6a00b`, `ap6a400`, `LN2-CT`, `LN2-MH` — hardened AP6 EBR, `rd_en_i` ignored, and the only families on which the initialization-data update control is user-visible (per 1.2, 1.7 Rule 17). `LKH-CT` and `LKH-MH` — generic inferred block-RAM array, `rd_en_i` ignored, ECC status outputs left undriven (per 1.2, 1.5.6, 1.5.8). The five families that normalize to `LIFCL` in the RTL are covered implicitly and are named in the Document Header. |
| Hidden, read-only, and derived parameters | `ECC_ENABLE` — unconditionally hidden and fixed to `False` (per 1.5.6); unreachability verified by TC-ROM-030 rather than swept. `user_init_mode` — read-only at `mem_file` (per 1.6, 1.7 Rule 11); verified by TC-ROM-031. `Total Memory bits` — display-only (per 1.6, 1.7 Rule 15); observed by TC-ROM-033. `INIT_DATA_TYPE_IN` — visible only when the normalized family is `LAV-AT`, so hidden on the target family (per 1.7 Rule 17); verified by TC-ROM-032. `RADDR_WIDTH`, `INIT_MODE`, `INIT_FILE`, `INIT_DATA_TYPE`, `FAMILY`, `T_FAMILY`, `MEM_ID`, `MEM_SIZE`, `buff_init_file`, and the 128 bulk initialization vectors — hidden read-only derived settings (per 1.6, 1.7 Rules 10, 11, 13, 14, 16, 18, 19); their derived values are observed where a case depends on them, but none is swept. |
| Unreachable GUI options | `Initialize to all 0s` and `Initialize to all 1s` on the Memory Initialization field: declared by the metadata but unselectable, the field being read-only and every non-`none` value deriving to `mem_file` (per 1.6, 1.7 Rule 11). Their unreachability is verified by TC-ROM-031 instead of being tested as configurations. |
| DRC-negative testing | Legal configurations only; illegal-input error messaging is not verified here. The error paths not exercised are `check_addr_depth_data_width` on a product above the budget or a dimension out of range (Rules 1, 3), `check_output_clk_en` with `OUTPUT_CLK_EN` true while `REGMODE` is false (Rule 5), `check_resetmode` with `async` while `REGMODE` is false (Rule 7), `chk_file` on the unset placeholder `-` (Rule 9), and the `clog2` `ERROR  --  Invalid input` path (Rule 10). Rules 5 and 7 are in any case unreachable through the GUI, editability Rules 6 and 8 collapsing both dependents to their legal values. |
| Jointly illegal parameter extremes | `RADDR_DEPTH=65536` with `RDATA_WIDTH=512` is a product of 33,554,432 bits, far beyond the 1,548,288-bit `LIFCL` budget (per 1.7 Rule 1). Legality is per combination, so each maximum is paired with a partner value that keeps the product legal, as recorded in the Coverage Summary. |
| Unreachable RTL paths | The all-zeros and all-ones initialization fill branches — the GUI field that would choose them is read-only and the derivation collapses every non-`none` value to `mem_file` (per 1.5.8, 1.7 Rule 11). The no-initialization branch, on which `rd_en_i` is not connected through to the implementation logic — unreachable through the GUI because the derivation never returns anything but `mem_file` for a generated instance, and reachable only by direct RTL instantiation at the declared defaults (per 1.5.8, Appendix A). The port-A-versus-port-B ratio and product checks inside `check_addr_depth_data_width` and `check_data_width`, which cannot fire because each function receives the same value for both of its arguments (per 1.7 Rules 1, 3 notes). The file-existence and mode-consistency checks the plugin defines but no metadata attribute names, so neither runs (per 1.7 Rule 9 notes). |
| Direct RTL instantiation outside the generator | Every case verifies the IP as generated by Radiant. The floating `one_err_det_o` and `two_err_det_o` an integrator would see by instantiating the RTL directly on `LKH-CT` or `LKH-MH` is a non-target-family, non-generated scenario and remains an open item in the specification (per 1.5.8, Appendix A). |

## Spec Issues and Assumptions

| ID | Missing or Ambiguous | Assumption Used | Impact | Who Should Confirm |
|---|---|---|---|---|
| `SPEC-GAP-01` | The EBR block depth for each implementation width is not tabulated. Section 1.5.5 gives the tiling formula and 1.5.1 names the block size as 16 Kb for `LIFCL`, but neither states the block depth per implementation width, so an exact EBR count for a configuration cannot be derived. | Tiling is asserted qualitatively: that more than one block is used on the relevant axis, that the pipelined high-address multiplexer is present when the tiling is more than one block deep, and that read latency and the port list are unchanged. No case asserts a specific EBR count. | TC-ROM-004, 005, 009, 020, 021, 022 | IP owner |
| `SPEC-GAP-02` | The `clog2` convention for the derived address width is ambiguous. Rule 10 states the derived width is `clog2(RADDR_DEPTH)`, while the same rule expresses its error condition over `RADDR_DEPTH - 1`, leaving the width for a power-of-two depth open between two readings — 10 or 11 bits at depth 1024. | The width is the ceiling of the base-2 logarithm of `RADDR_DEPTH`: 1 bit at depth 2, 10 bits at 1000 and at 1024, 12 bits at 3024, 16 bits at 65536. Every case inspecting the `rd_addr_i` width uses these figures. | TC-ROM-002, 004, 005, 006, 023, 033 | IP owner |
| `SPEC-GAP-03` | The implementation-width selection rule is not given. Section 1.5.5 states only that the implementation width is chosen to minimize the number of blocks, and 1.5.1 lists which primitive each width band selects, so which band a given depth and width pair lands in is not fully derivable. | A requested `RDATA_WIDTH` of 36 selects the wide `LIFCL` 32/36-bit pseudo-dual-port branch and a requested width of 18 or less the narrow single-port branch. If the tool selects another band, re-baseline the primitive assertion against the tool output rather than treating it as a functional failure. | TC-ROM-010, 030 | IP owner |
| `SPEC-GAP-04` | The value returned for an address above `RADDR_DEPTH - 1` is not defined. Section 1.5.2 states only that the address reaches the array unmodified and returns whatever the underlying block holds. | The returned value is not a pass criterion. TC-ROM-029 checks only that no error is flagged, that no `X` propagates onto `rd_data_o`, and that in-range reads before and after are correct. | TC-ROM-029 | IP owner |
| `SPEC-GAP-05` | `UT24C` and `UT24CP` rest on an open conflict. Per 1.2 and Appendix A the RTL normalizes both to `LIFCL` and builds the 16 Kb EBR implementation, while the plugin spells them `UTC24C` and `UTC24CP` and so applies the 1,073,741,824-bit default budget instead of the `LIFCL` budget. A configuration exceeding the `LIFCL` budget would pass DRC on those two families while the hardware built is `LIFCL`. | Budget-boundary coverage is claimed only for `LIFCL`, `LFD2NX`, `LFCPNX` and `LFMXO5`. TC-ROM-005 and TC-ROM-022 run on a `LIFCL` device. The implicit coverage claimed in the Document Header for `UT24C` and `UT24CP` is limited to functional behaviour and excludes the budget boundary until the plugin spelling is corrected. | TC-ROM-005, TC-ROM-022, and the implicit-coverage claim in the Document Header | IP owner and metadata owner |
| `SPEC-GAP-06` | Three defaults disagree between RTL and metadata. Per 1.4 and Appendix A, `RADDR_DEPTH` is `1024` against `512`, `RDATA_WIDTH` is `18` against `36`, and `INIT_FILE_FORMAT` is `binary` against `hex`; the specification resolves all three to the RTL value and records a pending metadata correction. | The plan takes the RTL values as the defaults, per the specification precedence rule. Until the metadata is corrected the GUI opens at depth 512, width 36 and hex, so the default-configuration cases must set all three fields explicitly rather than accept what the GUI presents. | TC-ROM-001, TC-ROM-015, TC-ROM-034 | Metadata owner |
| `SPEC-GAP-07` | Whether discarding memory-file words beyond `RADDR_DEPTH` locations produces a warning is not stated. Section 1.5.3 states only that such words are discarded. | The discard is silent. TC-ROM-019 requires that surplus words do not displace earlier content, and neither requires nor forbids a warning. | TC-ROM-019 | IP owner |
| `SPEC-GAP-08` | The declared default of `user_init_file` is the unset placeholder `-`, which Rule 9 rejects, so the documented default configuration is not itself legal and no instance can be generated without changing that one field. The specification does not say whether the default or the DRC is intended. | A named existing file is treated as the only legal state, and every case including the default-parameter smoke test names one. TC-ROM-034 states explicitly that the memory file is the one field that must be changed from its default. | TC-ROM-034, and every case in the plan | IP owner and metadata owner |
