# FIFO_DC FIP — Test Plan

*lscc_fifo_dc v2.7.2 · LIFCL*

| Field | Value |
|---|---|
| IP name | FIFO_DC |
| VLNV | `latticesemi.com:module:fifo_dc:2.7.2` |
| Module | `lscc_fifo_dc` |
| Version | 2.7.2 |
| Target Family | `LIFCL` |
| Families normalizing to target | `LFD2NX`, `LFCPNX`, `LFMXO5`, `UT24C`, `UT24CP` (spec 1.2) |
| Tool | Radiant ≥ 3.2 |
| Source specification | `FIFO_DC_Functional_Spec.md`, 2026-08-20 |
| Date | 2026-09-03 |

## 1. Scope & Objectives

- **Functional verification only** for FIFO_DC (`lscc_fifo_dc`) targeting the `LIFCL` device family. Performance and timing characterisation are out of scope; those are owned by the Hardware team. The declared families `LFD2NX`, `LFCPNX`, `LFMXO5`, `UT24C` and `UT24CP` normalize to `LIFCL` in both the plugin and the RTL (spec 1.2), so they share the implementation path this plan exercises and are covered implicitly; every test case is nonetheless written for `LIFCL`.
- **Parameters and ports are taken from the top-level RTL module declaration** in `fifo_dc/rtl/lscc_fifo_dc.v` (spec 1.3, 1.4). Only the twenty user-configurable parameters exposed in the Radiant IP configuration GUI are exercised. The internal-only parameters `WADDR_WIDTH`, `RADDR_WIDTH`, `OREG_IMPLEMENTATION`, `FAMILY`, `T_FAMILY`, `INIT_FILE`, `INIT_MODE`, `INIT_FILE_FORMAT` and `ECC_ENABLE`, and the display-only settings `Total Memory bits`, `CHECK_ASSERT_DEASSERT_FULL_LVL` and `CHECK_ASSERT_DEASSERT_EMPTY_LVL`, are **not directly tested** (spec 1.4, 1.6).
- **Only legal parameter combinations** permitted by the GUI dependency rules (spec 1.6, 1.7) are used. Every configuration in this plan satisfies Rules 1–30 simultaneously; the memory budget applied throughout is the `LIFCL` value of 1,548,288 bits and the width factor limit is 32 (spec 1.7, Per-family limits).
- **Transient-behavior rule.** Any case checking the transient behavior of a signal — asynchronous assertion edges, glitch behavior, same-cycle enable transitions — is `Radiant Compilation` and is never simulated.

**What "Radiant compilation" means here.** For a `Both` or `Radiant Compilation` case: generate the IP instance from the stated configuration, instantiate the generated wrapper in a Radiant project targeting a `LIFCL` device, and run synthesis and map to completion with no errors. `TC-FIFODC-053` extends this to place & route and bitstream generation.

**Stimulus patterns.** The IP exposes no memory-initialization setting, so the memory always elaborates uninitialized (spec 1.5.13) and there is no initialization artifact in this plan. All stimulus is testbench-driven write/read traffic drawn from three named patterns, each word truncated or zero-extended to the configured `WDATA_WIDTH`:

- `PAT-INCR` — an incrementing binary count beginning at 0, one word per accepted write.
- `PAT-WALK1` — a walking one: write word *n* carries bit (*n* mod `WDATA_WIDTH`) set and all other bits clear.
- `PAT-ALT` — alternating all-ones and all-zeros words, beginning with all-ones.

Unless a case states otherwise, `wr_clk_i` and `rd_clk_i` are driven at unrelated frequencies with no fixed phase relationship (spec 1.1), and every simulated case checks read-data integrity: the sequence observed on `rd_data_o` equals the sequence written on `wr_data_i`, in order, re-packed by the width ratio where the write and read widths differ (spec 1.5.4).

Type legend (use these three labels verbatim on every test case):

- **Radiant Compilation** — Radiant project build only; no simulation waveform required.
- **Sim Only** — functional simulation only; no Radiant synthesis required.
- **Both** — Radiant compilation and functional simulation.

## 2. Coverage Summary

| Total TCs | Radiant Compilation | Sim Only | Both |
|---|---|---|---|
| 53 | 3 | 9 | 41 |

Parameters covered: `WADDR_DEPTH` (min 2 / median 512 / max 65536, plus 64, 1000, 2048, 4096, 8192, 16383, 16384), `WDATA_WIDTH` (min 1 / median 36 / max 256, plus 8, 32, 180), `RADDR_DEPTH` (min 2 / median 512 / max 65536, plus 64, 1000, 1024, 4096, 8192, 16383, 16384), `RDATA_WIDTH` (min 1 / median 36 / max 256, plus 8, 32, 180), `FIFO_CONTROLLER` (`FABRIC`, `HARD_IP`), `FWFT` (`0`, `1`), `FORCE_FAST_CONTROLLER` (`0`, `1`), `IMPLEMENTATION` (`EBR`, `LUT`), `REGMODE` (`reg`, `noreg`), `RESETMODE` (`async`, `sync`), `ENABLE_ALMOST_FULL_FLAG` (`TRUE`, `FALSE`), `ALMOST_FULL_ASSERTION` (`static-single`, `static-dual`, `dynamic-single`, `dynamic-dual`), `ALMOST_FULL_ASSERT_LVL` (min 1 / median 256 / max 511 at depth 512, plus 400, 999, 2047, 4095, 8191, 16382, 16383, 65535), `ALMOST_FULL_DEASSERT_LVL` (min 1 / median 255 / max 510 at assert 511, plus 30, 62, 2046, 4094, 16382, 65534), `ENABLE_ALMOST_EMPTY_FLAG` (`TRUE`, `FALSE`), `ALMOST_EMPTY_ASSERTION` (`static-single`, `static-dual`, `dynamic-single`, `dynamic-dual`), `ALMOST_EMPTY_ASSERT_LVL` (min 1 / median 256 / max 511, plus 100), `ALMOST_EMPTY_DEASSERT_LVL` (min 2 / median 256 / max 511, plus 1, 257), `ENABLE_DATA_COUNT_WR` (`TRUE`, `FALSE`), `ENABLE_DATA_COUNT_RD` (`TRUE`, `FALSE`).

Ports covered: `wr_clk_i`, `rd_clk_i`, `wr_data_i`, `wr_en_i`, `rd_en_i`, `rst_i`, `rp_rst_i`, `almost_full_th_i`, `almost_full_clr_th_i`, `almost_empty_th_i`, `almost_empty_clr_th_i`, `rd_data_o`, `full_o`, `empty_o`, `almost_full_o`, `almost_empty_o`, `wr_data_cnt_o`, `rd_data_cnt_o`, `one_err_det_o`, `two_err_det_o` — all twenty declarations of spec 1.3.

**Median values.** `TC-FIFODC-001` is the all-median card: the documented spec 1.4 default of every numeric parameter is the median this plan uses, so the baseline row of the matrix carries the median of `WADDR_DEPTH` (512), `WDATA_WIDTH` (36), `RADDR_DEPTH` (512) and `RDATA_WIDTH` (36) in bold. The four almost-flag levels are the exception: at `WADDR_DEPTH` = `RADDR_DEPTH` = 512 the defaults 511, 510, 1 and 2 sit at an *end* of their legal ranges rather than the middle (Rules 15–18), so their medians (256, 255, 256, 256) are carried by dedicated cards.

## 3. Coverage Matrix

Column key — the matrix uses short column headers for width; each maps to exactly one spec 1.4 parameter:

| Column | Parameter | Column | Parameter |
|---|---|---|---|
| W_DEPTH | `WADDR_DEPTH` | RESETMODE | `RESETMODE` |
| W_WIDTH | `WDATA_WIDTH` | AF_EN | `ENABLE_ALMOST_FULL_FLAG` |
| R_DEPTH | `RADDR_DEPTH` | AF_MODE | `ALMOST_FULL_ASSERTION` |
| R_WIDTH | `RDATA_WIDTH` | AF_A | `ALMOST_FULL_ASSERT_LVL` |
| CTRL | `FIFO_CONTROLLER` | AF_D | `ALMOST_FULL_DEASSERT_LVL` |
| FWFT | `FWFT` | AE_EN | `ENABLE_ALMOST_EMPTY_FLAG` |
| FFC | `FORCE_FAST_CONTROLLER` | AE_MODE | `ALMOST_EMPTY_ASSERTION` |
| IMPL | `IMPLEMENTATION` | AE_A | `ALMOST_EMPTY_ASSERT_LVL` |
| REGMODE | `REGMODE` | AE_D | `ALMOST_EMPTY_DEASSERT_LVL` |
| — | — | CNT_WR / CNT_RD | `ENABLE_DATA_COUNT_WR` / `ENABLE_DATA_COUNT_RD` |

Assertion-mode values are abbreviated `s-1` = `static-single`, `s-2` = `static-dual`, `d-1` = `dynamic-single`, `d-2` = `dynamic-dual`. A `—` cell means the parameter is not editable in that configuration (Rules 19, 20, 22, 23, 24, 25) or is don't-care for that case; the value a case specifically sweeps is **bold**.

| TC ID | Test Name | Type | W_DEPTH | W_WIDTH | R_DEPTH | R_WIDTH | CTRL | FWFT | FFC | IMPL | REGMODE | RESETMODE | AF_EN | AF_MODE | AF_A | AF_D | AE_EN | AE_MODE | AE_A | AE_D | CNT_WR | CNT_RD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-FIFODC-001 | Default configuration baseline | Both | **512** | **36** | **512** | **36** | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-002 | Minimum write address depth | Both | **2** | 1 | 2 | 1 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 1 | 1 | TRUE | s-2 | 1 | 1 | FALSE | FALSE |
| TC-FIFODC-003 | Maximum write address depth | Both | **65536** | 1 | 65536 | 1 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 65535 | 65534 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-004 | Minimum write data width | Both | 512 | **1** | 512 | 1 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-005 | Maximum write data width | Both | 4096 | **256** | 4096 | 256 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 4095 | 4094 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-006 | Minimum read address depth | Both | 64 | 1 | **2** | 32 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 63 | 62 | TRUE | s-2 | 1 | 1 | FALSE | FALSE |
| TC-FIFODC-007 | Maximum read address depth | Both | 2048 | 32 | **65536** | 1 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 2047 | 2046 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-008 | Minimum read data width | Both | 32 | 32 | 1024 | **1** | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 31 | 30 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-009 | Maximum read data width | Both | 16384 | 8 | 512 | **256** | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 16383 | 16382 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-010 | Hardened memory-block controller | Both | 512 | 36 | 512 | 36 | **HARD_IP** | 0 | 0 | — | reg | async | TRUE | s-1 | 511 | — | TRUE | s-1 | 1 | — | — | — |
| TC-FIFODC-011 | Hardened controller, non-power-of-two depth | Both | 1000 | 36 | 1000 | 36 | **HARD_IP** | 0 | 0 | — | reg | async | TRUE | s-1 | 999 | — | TRUE | s-1 | 1 | — | — | — |
| TC-FIFODC-012 | First-word fall-through, unregistered output | Both | 512 | 36 | 512 | 36 | FABRIC | **1** | — | EBR | noreg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-013 | First-word fall-through, registered output | Both | 512 | 36 | 512 | 36 | FABRIC | **1** | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-014 | High-speed hardened controller at its depth ceiling | Both | 16383 | 36 | 16383 | 36 | HARD_IP | 0 | **1** | — | reg | async | TRUE | s-1 | 16382 | — | TRUE | s-1 | 1 | — | — | — |
| TC-FIFODC-015 | LUT-based storage | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | **LUT** | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-016 | Output register disabled | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | **noreg** | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-017 | Synchronous reset mode | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | **sync** | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-018 | Almost-full flag disabled | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | **FALSE** | — | — | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-019 | Almost-full static single threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | **s-1** | 400 | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-020 | Almost-full dynamic single threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | **d-1** | — | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-021 | Almost-full dynamic dual threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | **d-2** | — | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-022 | Almost-full assert level at minimum | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-1 | **1** | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-023 | Almost-full assert level at median | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | **256** | **255** | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-024 | Almost-full deassert level at minimum | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | **1** | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-025 | Almost-empty flag disabled | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | **FALSE** | — | — | — | FALSE | FALSE |
| TC-FIFODC-026 | Almost-empty static single threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | **s-1** | 100 | — | FALSE | FALSE |
| TC-FIFODC-027 | Almost-empty dynamic single threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | **d-1** | — | — | FALSE | FALSE |
| TC-FIFODC-028 | Almost-empty dynamic dual threshold | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | **d-2** | — | — | FALSE | FALSE |
| TC-FIFODC-029 | Almost-empty assert level at median | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | **256** | 257 | FALSE | FALSE |
| TC-FIFODC-030 | Almost-empty assert level at maximum | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-1 | **511** | — | FALSE | FALSE |
| TC-FIFODC-031 | Almost-empty deassert level at median | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 100 | **256** | FALSE | FALSE |
| TC-FIFODC-032 | Almost-empty deassert level at maximum | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | **511** | FALSE | FALSE |
| TC-FIFODC-033 | Write-side data count enabled | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | **TRUE** | FALSE |
| TC-FIFODC-034 | Read-side data count enabled | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | **TRUE** |
| TC-FIFODC-035 | Wide write to narrow read, dynamic dual flags, both counts | Both | **512** | **32** | **16384** | **1** | FABRIC | 0 | — | EBR | reg | **sync** | TRUE | **d-2** | — | — | TRUE | **d-2** | — | — | **TRUE** | **TRUE** |
| TC-FIFODC-036 | Narrow write to wide read with fall-through | Both | **16384** | **1** | **512** | **32** | FABRIC | **1** | — | EBR | **noreg** | async | TRUE | s-2 | **16383** | **16382** | TRUE | s-2 | 1 | 2 | **TRUE** | **TRUE** |
| TC-FIFODC-037 | High-speed hardened controller with fall-through and sync reset | Both | **8192** | 36 | **8192** | 36 | **HARD_IP** | **1** | **1** | — | reg | **sync** | TRUE | s-1 | **8191** | — | TRUE | s-1 | 1 | — | — | — |
| TC-FIFODC-038 | LUT storage, fall-through, flags disabled, both counts | Both | **64** | **8** | **64** | **8** | FABRIC | **1** | — | **LUT** | **noreg** | async | **FALSE** | — | — | — | **FALSE** | — | — | — | **TRUE** | **TRUE** |
| TC-FIFODC-039 | Minimum geometry on the hardened controller | Both | **2** | **1** | **2** | **1** | **HARD_IP** | **1** | 0 | — | **noreg** | async | TRUE | s-1 | 1 | — | TRUE | s-1 | 1 | — | — | — |
| TC-FIFODC-040 | Near-ceiling memory budget with dynamic dual flags | Both | **8192** | **180** | **8192** | **180** | FABRIC | 0 | — | EBR | reg | async | TRUE | **d-2** | — | — | TRUE | **d-2** | — | — | **TRUE** | **TRUE** |
| TC-FIFODC-041 | Write enable ignored while full | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-042 | Read enable ignored while empty, output hold | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-043 | Asynchronous reset structure | Radiant Compilation | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | **async** | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | TRUE | TRUE |
| TC-FIFODC-044 | Main reset clear and post-release flag state | Both | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | **sync** | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | TRUE | TRUE |
| TC-FIFODC-045 | Read-pointer reset leaves the write side intact | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | sync | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | TRUE | TRUE |
| TC-FIFODC-046 | Almost-full dynamic assert threshold port | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | d-1 | — | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-047 | Almost-full dynamic clear threshold port | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | d-2 | — | — | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-048 | Almost-empty dynamic assert threshold port | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | d-1 | — | — | FALSE | FALSE |
| TC-FIFODC-049 | Almost-empty dynamic clear threshold port | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | d-2 | — | — | FALSE | FALSE |
| TC-FIFODC-050 | Full and empty conservatism across the clock crossing | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |
| TC-FIFODC-051 | Data count conservatism on both sides | Sim Only | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | sync | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | TRUE | TRUE |
| TC-FIFODC-052 | Error-detect outputs declared and unconnected | Radiant Compilation | 512 | 36 | 512 | 36 | FABRIC / HARD_IP | 0 | — | EBR / — | reg | async | TRUE | s-2 / s-1 | 511 | 510 / — | TRUE | s-2 / s-1 | 1 | 2 / — | FALSE / — | FALSE / — |
| TC-FIFODC-053 | Default-parameter compilation smoke test | Radiant Compilation | 512 | 36 | 512 | 36 | FABRIC | 0 | — | EBR | reg | async | TRUE | s-2 | 511 | 510 | TRUE | s-2 | 1 | 2 | FALSE | FALSE |

### Feature coverage

| Feature (spec 1.1) | Covering TC IDs |
|---|---|
| Dual-clock FIFO with independent write and read clocks, `wr_clk_i` and `rd_clk_i`, and no required phase or frequency relationship | TC-FIFODC-001, TC-FIFODC-050; exercised by every simulated case |
| Write address depth configurable from 2 to 65536, reduced to 16383 when the high-speed hard controller option is selected on LIFCL-class devices | TC-FIFODC-002, TC-FIFODC-003, TC-FIFODC-014 |
| Write data width configurable from 1 to 256 bits | TC-FIFODC-004, TC-FIFODC-005 |
| Independent read address depth (2 to 65536) and read data width (1 to 256), permitting mixed-width operation where the write and read capacities match and the width ratio is a power of two | TC-FIFODC-006, TC-FIFODC-007, TC-FIFODC-008, TC-FIFODC-009, TC-FIFODC-035, TC-FIFODC-036 |
| Two controller implementation paths selected by `FIFO_CONTROLLER`: a fabric controller built from gray-coded pointers, or the hardened memory-block FIFO controller | TC-FIFODC-001, TC-FIFODC-010, TC-FIFODC-011 |
| Storage implemented in embedded block RAM or in LUT-based memory, selected by `IMPLEMENTATION` and available with the fabric controller | TC-FIFODC-001, TC-FIFODC-015, TC-FIFODC-038 |
| Optional read output register selected by `REGMODE`, trading one extra `rd_clk_i` cycle of read latency for a registered output | TC-FIFODC-001, TC-FIFODC-016 |
| First-word-fall-through mode selected by `FWFT`, which presents the head word on `rd_data_o` without an asserted `rd_en_i` | TC-FIFODC-012, TC-FIFODC-013, TC-FIFODC-036, TC-FIFODC-037, TC-FIFODC-038, TC-FIFODC-039 |
| Selectable asynchronous or synchronous reset behaviour through `RESETMODE`, with a separate read-pointer reset input | TC-FIFODC-017, TC-FIFODC-043, TC-FIFODC-044, TC-FIFODC-045 |
| `full_o` and `empty_o` status outputs present in every configuration | TC-FIFODC-001, TC-FIFODC-041, TC-FIFODC-042, TC-FIFODC-050 |
| Optional almost-full flag with four assertion modes — static single, static dual, dynamic single, dynamic dual — where the dynamic modes take their thresholds from `almost_full_th_i` and `almost_full_clr_th_i` | TC-FIFODC-018 through TC-FIFODC-024, TC-FIFODC-046, TC-FIFODC-047 |
| Optional almost-empty flag with the same four assertion modes, driven by `almost_empty_th_i` and `almost_empty_clr_th_i` in the dynamic modes | TC-FIFODC-025 through TC-FIFODC-032, TC-FIFODC-048, TC-FIFODC-049 |
| Optional write-side and read-side occupancy counters on `wr_data_cnt_o` and `rd_data_cnt_o`, editable only with the fabric controller | TC-FIFODC-033, TC-FIFODC-034, TC-FIFODC-044, TC-FIFODC-051 |
| High-speed hard-controller variant selectable on LIFCL-class devices through `FORCE_FAST_CONTROLLER`, which trades maximum depth for speed | TC-FIFODC-014, TC-FIFODC-037 |
| Error-correction capability exists in the RTL but is not exposed: `ECC_ENABLE` has no metadata setting, so it stays at its RTL default of 0, and the `one_err_det_o` and `two_err_det_o` outputs are unconditionally dangling | TC-FIFODC-052 (boundary declaration only); functional ECC behaviour — see Exclusions, "Unreachable RTL paths" |
| Requires Radiant 3.2 or later, with no declared maximum version | TC-FIFODC-053 |
| Fourteen declared device families, normalized to five distinct internal behaviours | `LIFCL` internal behaviour: every test case; the other four internal behaviours — see Exclusions, "Non-target device families" |

## Test Groups

Twenty-four groups: the baseline, one group per user-configurable parameter in spec 1.4 order, the cross-parameter group, the port-behaviour group, and the DRC and compilation group. Test IDs run sequentially in group order.

Where a parameter's median value is the spec 1.4 default, the median is exercised by `TC-FIFODC-001` and the group states so rather than repeating an identical card.

### G1 · Baseline

#### TC-FIFODC-001 — Default configuration baseline `Both`

**Configuration**

- `WADDR_DEPTH`=512
- `WDATA_WIDTH`=36
- `RADDR_DEPTH`=512
- `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC` — the RTL default (spec 1.4); the metadata `value_expr` presents `HARD_IP` on an eligible LIFCL device, see `SPEC-GAP-01` and `TC-FIFODC-010`
- `FWFT`=0
- `FORCE_FAST_CONTROLLER`=0 (not editable with `FABRIC`, Rule 22)
- `IMPLEMENTATION`=`EBR`
- `REGMODE`=`reg`
- `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`
- `ALMOST_FULL_ASSERTION`=`static-dual`
- `ALMOST_FULL_ASSERT_LVL`=511
- `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`
- `ALMOST_EMPTY_ASSERTION`=`static-dual`
- `ALMOST_EMPTY_ASSERT_LVL`=1
- `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`
- `ENABLE_DATA_COUNT_RD`=`FALSE`

Capacity 512 x 36 = 18,432 bits on both sides — equal (Rule 6), within the `LIFCL` budget of 1,548,288 (Rule 1), depth a power of two (Rule 7), width factor 1 (Rule 8), levels inside their ranges with 510 < 511 <= 512 and 2 > 1 (Rules 13-18).

**Procedure**

1. Generate the IP instance with the configuration above; retain the generated wrapper — `TC-FIFODC-041`, `TC-FIFODC-042` and `TC-FIFODC-050` reuse it.
2. Instantiate the generated wrapper in a Radiant project targeting a `LIFCL` device; run synthesis and map.
3. In simulation, hold `rst_i` asserted for at least four `wr_clk_i` and four `rd_clk_i` cycles, then release it. Drive `wr_clk_i` and `rd_clk_i` at unrelated frequencies.
4. Write 512 words of `PAT-INCR` with `wr_en_i`, stopping when `full_o` asserts.
5. Read all words back with `rd_en_i` until `empty_o` asserts.

**Pass Criteria**

- Generation, synthesis and map complete with no errors and no DRC violation from Rules 1-30 (spec 1.7).
- The generated wrapper declares all twenty ports of spec 1.3, with `almost_full_th_i`, `almost_full_clr_th_i`, `almost_empty_th_i` and `almost_empty_clr_th_i` each 9 bits wide, since `WADDR_WIDTH` = `RADDR_WIDTH` = `clog2(512)` = 9 (Rule 27).
- Immediately after reset release, `empty_o` and `almost_empty_o` are asserted and `full_o` and `almost_full_o` are deasserted, per 1.5.12 (Flag update delay) and 1.5.5.
- `full_o` asserts before more than 512 words are accepted, and never permits a 513th accepted write, per 1.5.5.
- Every word read back on `rd_data_o` equals the corresponding written word in order, and `rd_data_o` is valid two `rd_clk_i` cycles after each accepted read, per 1.5.12 (`REGMODE` = `reg`, `FWFT` = 0).
- `almost_full_o` asserts once write-side occupancy reaches 511 words and clears once occupancy falls below 510, per 1.5.6 (`static-dual`).
- `almost_empty_o` asserts once read-side occupancy falls to 1 word and clears once occupancy rises above 2, per 1.5.6.
- `empty_o` asserts after the last word is read and `rd_data_o` holds its last value thereafter, per 1.5.12.

### G2 · WADDR_DEPTH

Median 512 is exercised by `TC-FIFODC-001`. Both boundary cards pair the extreme depth with `WDATA_WIDTH` = 1 so that Rules 1 and 6 stay satisfied: at 65536 words the `LIFCL` budget of 1,548,288 bits allows at most 23 bits per word, so only a narrow word reaches the maximum depth.

#### TC-FIFODC-002 — Minimum write address depth `Both`

**Configuration**

- `WADDR_DEPTH`=2, `WDATA_WIDTH`=1, `RADDR_DEPTH`=2, `RDATA_WIDTH`=1 (capacity 2 = 2 bits, Rule 6)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=1, `ALMOST_FULL_DEASSERT_LVL`=1
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=1
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

All four level settings are 1 because `getLoop` collapses them at a depth of 2 (Rule 26), and Rules 13 and 14 pass unconditionally at that depth.

**Procedure**

1. Generate and build (generate, synthesize, map).
2. Reset, release, then write 2 words of `PAT-ALT`; attempt a third write while `full_o` is asserted.
3. Read both words back, then attempt a third read while `empty_o` is asserted.

**Pass Criteria**

- Generation and build complete with no error; the depth of 2 satisfies the `value_range` lower bound (Rule 10) and is a power of two (Rule 7).
- The four threshold ports are 1 bit wide, since `clog2(2)` = 1 (Rule 27).
- `full_o` asserts once 2 words are held and the third write is not accepted — the write pointer does not advance, per 1.5.4.
- Both words read back in order on `rd_data_o`, valid two `rd_clk_i` cycles after each accepted read, per 1.5.12.
- `empty_o` asserts after the second word is read and the third read is not accepted, per 1.5.4.

#### TC-FIFODC-003 — Maximum write address depth `Both`

**Configuration**

- `WADDR_DEPTH`=65536, `WDATA_WIDTH`=1, `RADDR_DEPTH`=65536, `RDATA_WIDTH`=1 (capacity 65,536 bits, within the 1,548,288-bit `LIFCL` budget, Rule 1)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=65535, `ALMOST_FULL_DEASSERT_LVL`=65534
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 65,536 words of `PAT-INCR` until `full_o` asserts.
3. Read all words back until `empty_o` asserts.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` upper bound of 65536 (Rule 10) with `FORCE_FAST_CONTROLLER` = 0.
- The four threshold ports are 16 bits wide, since `clog2(65536)` = 16 (Rule 27).
- `full_o` asserts at 65,536 held words and blocks further writes, per 1.5.5.
- Read-back sequence matches the written sequence in order, at two `rd_clk_i` cycles of latency, per 1.5.12.
- `almost_full_o` asserts at 65,535 words and clears below 65,534, per 1.5.6.
- No pass criterion asserts a memory-block count for this configuration — see `SPEC-GAP-06`.

### G3 · WDATA_WIDTH

Median 36 is exercised by `TC-FIFODC-001`. The maximum-width card pairs 256 bits with a depth of 4096 so that capacity stays inside the `LIFCL` budget (Rule 1) and matches on both sides (Rule 6).

#### TC-FIFODC-004 — Minimum write data width `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=1, `RADDR_DEPTH`=512, `RDATA_WIDTH`=1 (capacity 512 = 512 bits)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 512 single-bit words of `PAT-ALT`.
3. Read all 512 words back.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` lower bound of 1 (Rule 11); `wr_data_i` and `rd_data_o` are each 1 bit wide on the generated wrapper (spec 1.3).
- The alternating bit sequence reads back bit-for-bit in order, at two `rd_clk_i` cycles of latency, per 1.5.12.
- `full_o` and `empty_o` behave as in `TC-FIFODC-001`, per 1.5.5.

#### TC-FIFODC-005 — Maximum write data width `Both`

**Configuration**

- `WADDR_DEPTH`=4096, `WDATA_WIDTH`=256, `RADDR_DEPTH`=4096, `RDATA_WIDTH`=256 (capacity 1,048,576 = 1,048,576 bits, inside the 1,548,288-bit budget, Rule 1)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=4095, `ALMOST_FULL_DEASSERT_LVL`=4094
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 4096 words of `PAT-WALK1`, so that every one of the 256 bit positions is exercised.
3. Read all words back.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` upper bound of 256 (Rule 11); `wr_data_i` and `rd_data_o` are each 256 bits wide (spec 1.3).
- Every bit position of every word reads back unchanged and in order, at two `rd_clk_i` cycles of latency, per 1.5.12 — no bit-lane crossing.
- `almost_full_o` asserts at 4095 words and clears below 4094, per 1.5.6.
- No pass criterion asserts a memory-block count or a tiling arrangement for this configuration — see `SPEC-GAP-06`.

### G4 · RADDR_DEPTH

Median 512 is exercised by `TC-FIFODC-001`. `RADDR_DEPTH` cannot move on its own: Rule 6 requires `WADDR_DEPTH` x `WDATA_WIDTH` = `RADDR_DEPTH` x `RDATA_WIDTH`, so each boundary card is necessarily a mixed-width configuration whose width factor is held at the `LIFCL` maximum of 32 (Rule 8). Mixed geometry also forces `IMPLEMENTATION` = `EBR` (Rule 12).

#### TC-FIFODC-006 — Minimum read address depth `Both`

**Configuration**

- `WADDR_DEPTH`=64, `WDATA_WIDTH`=1, `RADDR_DEPTH`=2, `RDATA_WIDTH`=32 (capacity 64 = 64 bits, Rule 6; read-to-write width factor 32, at the `LIFCL` limit, Rules 5 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=63, `ALMOST_FULL_DEASSERT_LVL`=62
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=1 (collapsed by `getLoop` at `RADDR_DEPTH` = 2, Rule 26)
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 64 single-bit words of `PAT-INCR`.
3. Read the 2 read-side words back.

**Pass Criteria**

- Generation and build complete with no error; the read-to-write width factor of 32 is accepted (Rule 8) and the read depth of 2 satisfies Rule 10.
- `almost_full_th_i` is 6 bits wide (`clog2(64)`) and `almost_empty_th_i` is 1 bit wide (`clog2(2)`), per Rule 27.
- The 64 written bits appear on `rd_data_o` re-packed into 2 words of 32 bits, in write order, per 1.5.4 — the compared pointer is aligned to the narrower width, per 1.5.4.
- `full_o` asserts at 64 held write words, per 1.5.5.
- `empty_o` asserts after both read words are consumed, per 1.5.5.

#### TC-FIFODC-007 — Maximum read address depth `Both`

**Configuration**

- `WADDR_DEPTH`=2048, `WDATA_WIDTH`=32, `RADDR_DEPTH`=65536, `RDATA_WIDTH`=1 (capacity 65,536 = 65,536 bits, Rule 6; write-to-read width factor 32, Rules 4 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=2047, `ALMOST_FULL_DEASSERT_LVL`=2046
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 2048 words of 32-bit `PAT-INCR`.
3. Read all 65,536 single-bit read words back.

**Pass Criteria**

- Generation and build complete with no error at the maximum read depth (Rule 10) with a write-to-read factor of 32 (Rule 8).
- `almost_full_th_i` is 11 bits wide (`clog2(2048)`) and `almost_empty_th_i` is 16 bits wide (`clog2(65536)`), per Rule 27.
- Each 32-bit written word appears on `rd_data_o` as 32 single-bit read words in write order, per 1.5.4.
- `full_o` asserts at 2048 held write words and `empty_o` after the last read word, per 1.5.5.

### G5 · RDATA_WIDTH

Median 36 is exercised by `TC-FIFODC-001`. As in G4, each boundary card is mixed-width by Rule 6, with the width factor held at 32.

#### TC-FIFODC-008 — Minimum read data width `Both`

**Configuration**

- `WADDR_DEPTH`=32, `WDATA_WIDTH`=32, `RADDR_DEPTH`=1024, `RDATA_WIDTH`=1 (capacity 1024 = 1024 bits, Rule 6; write-to-read factor 32, Rules 4 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=31, `ALMOST_FULL_DEASSERT_LVL`=30
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 32 words of 32-bit `PAT-WALK1`.
3. Read all 1024 single-bit read words back.

**Pass Criteria**

- Generation and build complete with no error at `RDATA_WIDTH` = 1 (Rule 11) with a factor of 32 (Rule 8).
- `rd_data_o` is 1 bit wide on the generated wrapper (spec 1.3).
- The walking-one sequence reads back with exactly one asserted read word per written word, in write order, per 1.5.4.
- `almost_full_o` asserts at 31 write words and clears below 30, per 1.5.6.

#### TC-FIFODC-009 — Maximum read data width `Both`

**Configuration**

- `WADDR_DEPTH`=16384, `WDATA_WIDTH`=8, `RADDR_DEPTH`=512, `RDATA_WIDTH`=256 (capacity 131,072 = 131,072 bits, Rules 1 and 6; read-to-write factor 32, Rules 5 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=16383, `ALMOST_FULL_DEASSERT_LVL`=16382
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 16,384 words of 8-bit `PAT-INCR`.
3. Read all 512 words of 256 bits back.

**Pass Criteria**

- Generation and build complete with no error at `RDATA_WIDTH` = 256 (Rule 11) with a read-to-write factor of 32 (Rule 8).
- `almost_full_th_i` is 14 bits wide (`clog2(16384)`) and `almost_empty_th_i` is 9 bits wide (`clog2(512)`), per Rule 27.
- Each group of 32 written bytes appears as one 256-bit read word in write order, per 1.5.4.
- `full_o` asserts at 16,384 held write words, per 1.5.5.

### G6 · FIFO_CONTROLLER

`FABRIC` is exercised by `TC-FIFODC-001` and by every card that offers a storage choice, a dynamic threshold mode or a data count. The two cards here cover `HARD_IP`, where Rule 25 forces both assertion modes to `static-single`, Rule 23 withdraws the storage choice, Rule 24 withdraws both data counts, and Rule 7 no longer constrains the depth to a power of two (spec 1.5.2).

#### TC-FIFODC-010 — Hardened memory-block controller `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`HARD_IP`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0 (editable with `HARD_IP`, Rule 22)
- `IMPLEMENTATION` not editable — block RAM only (Rule 23, spec 1.5.2)
- `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single` (forced, Rule 25), `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL` not editable (Rule 20)
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single` (forced, Rule 25), `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL` not editable (Rule 20)
- `ENABLE_DATA_COUNT_WR` and `ENABLE_DATA_COUNT_RD` not editable (Rule 24)

**Procedure**

1. Generate the IP instance; retain the generated wrapper — `TC-FIFODC-052` inspects it.
2. Build (generate, synthesize, map).
3. Reset, release, then write 512 words of `PAT-INCR` until `full_o` asserts.
4. Read all words back until `empty_o` asserts.

**Pass Criteria**

- Generation and build complete with no error; the configuration GUI offers `HARD_IP` because the internal family is `LIFCL` and the device is neither LAV-AT-E30B nor LAV-AT-E70B (Rule 21).
- The GUI presents `ALMOST_FULL_ASSERTION` and `ALMOST_EMPTY_ASSERTION` as `static-single` and does not accept another value (Rule 25); `IMPLEMENTATION`, `ENABLE_DATA_COUNT_WR` and `ENABLE_DATA_COUNT_RD` are read-only (Rules 23, 24).
- After reset release `empty_o` and `almost_empty_o` are asserted and `full_o` and `almost_full_o` are deasserted, per 1.5.12 (Flag update delay).
- `full_o` asserts at 512 held words and blocks further writes; the read-back sequence matches the written sequence in order at two `rd_clk_i` cycles of latency, per 1.5.12 (Hardened-controller read path — the in-tree checker applies the same `REGMODE`/`FWFT` contract to `HARD_IP`).
- `almost_full_o` asserts once occupancy reaches 511 and clears once it falls below 511 — assert and deassert share the one threshold, per 1.5.6 (`static-single`).
- Flag deassertion is bounded only where 1.5.12 states a number: `empty_o` and `almost_empty_o` carry two register stages in the consuming domain with `REGMODE` = `reg`. No criterion asserts a cycle count for `almost_full_o` deassertion on this path — see `SPEC-GAP-05`.
- No criterion asserts a value on `wr_data_cnt_o` or `rd_data_cnt_o`; the hardened controller leaves them undriven, per 1.5.7 — see `SPEC-GAP-03`.

#### TC-FIFODC-011 — Hardened controller, non-power-of-two depth `Both`

**Configuration**

- `WADDR_DEPTH`=1000, `WDATA_WIDTH`=36, `RADDR_DEPTH`=1000, `RDATA_WIDTH`=36 (capacity 36,000 = 36,000 bits, Rules 1 and 6)
- `FIFO_CONTROLLER`=`HARD_IP`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0
- `IMPLEMENTATION` not editable; `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single`, `ALMOST_FULL_ASSERT_LVL`=999, `ALMOST_FULL_DEASSERT_LVL` not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL` not editable
- Both data counts not editable

**Procedure**

1. Generate and build.
2. Reset, release, then write 1000 words of `PAT-INCR` until `full_o` asserts.
3. Read all words back until `empty_o` asserts.

**Pass Criteria**

- Generation and build complete with no error: a depth of 1000 is accepted because the power-of-two restriction applies only to the fabric controller (Rule 7, spec 1.5.2).
- The depth lies inside the `value_range` of 2 to 65536 (Rule 10) and the assert level of 999 satisfies the almost-full cross-check, being at most `WADDR_DEPTH` (Rule 13).
- `full_o` asserts at exactly 1000 held words and never permits a 1001st accepted write, per 1.5.5.
- The read-back sequence matches the written sequence in order at two `rd_clk_i` cycles of latency, per 1.5.12.
- No criterion asserts how many primitives the capacity is met with — see `SPEC-GAP-06`.

### G7 · FWFT

`FWFT` = 0 is exercised by `TC-FIFODC-001`. Both fall-through cards are needed because `REGMODE` changes the first-word latency: 1.5.12 gives zero cycles with `noreg` and one cycle with `reg`.

#### TC-FIFODC-012 — First-word fall-through, unregistered output `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=1, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`noreg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, and hold `rd_en_i` low. Write a single word of `PAT-INCR`.
3. Observe `empty_o` and `rd_data_o` with `rd_en_i` still low.
4. Assert `rd_en_i` for one cycle to acknowledge the presented word, then write and read a further eight words.

**Pass Criteria**

- Generation and build complete with no error.
- With `rd_en_i` held low, `empty_o` deasserts after the first write and the first written word is already present on `rd_data_o` at that moment — zero-cycle first-word latency, per 1.5.12 (`FWFT` = 1, `REGMODE` = `noreg`) and 1.5.8.
- Asserting `rd_en_i` pops the presented word; the next word is presented in the following `rd_clk_i` cycle, and `empty_o` re-asserts when none remains, per 1.5.8.
- The eight further words appear on `rd_data_o` in write order, one per acknowledged cycle, per 1.5.8.
- `empty_o` is generated by the prefetch stage in this mode, so its low level means a valid word is on `rd_data_o` now, per 1.5.8.

#### TC-FIFODC-013 — First-word fall-through, registered output `Both`

**Configuration**

- As `TC-FIFODC-012`, with `REGMODE`=`reg`.

**Procedure**

1. Generate and build.
2. Reset, release, and hold `rd_en_i` low. Write a single word of `PAT-INCR`.
3. Observe the cycle in which `empty_o` deasserts and the cycle in which `rd_data_o` becomes valid.
4. Assert `rd_en_i` for one cycle, then write and read a further eight words.

**Pass Criteria**

- Generation and build complete with no error.
- The first available word reaches `rd_data_o` one `rd_clk_i` cycle after the prefetch is accepted, so `empty_o` deassertion leads the registered word by one cycle, per 1.5.12 (`FWFT` = 1, `REGMODE` = `reg`) and 1.5.8.
- The prefetch stage registers the presented word rather than driving it combinationally, per 1.5.8.
- The eight further words appear on `rd_data_o` in write order at the same one-cycle offset, per 1.5.8.

### G8 · FORCE_FAST_CONTROLLER — Requires FIFO_CONTROLLER = HARD_IP

The value 0 is exercised by `TC-FIFODC-001` (where Rule 22 makes the field read-only under `FABRIC`) and by `TC-FIFODC-010` (editable, left at 0). The card below covers the value 1 at the reduced depth ceiling `getDepthLimit` imposes.

#### TC-FIFODC-014 — High-speed hardened controller at its depth ceiling `Both`

**Configuration**

- `WADDR_DEPTH`=16383, `WDATA_WIDTH`=36, `RADDR_DEPTH`=16383, `RDATA_WIDTH`=36 (capacity 589,788 = 589,788 bits, inside the 1,548,288-bit budget, Rules 1 and 6)
- `FIFO_CONTROLLER`=`HARD_IP`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=1
- `IMPLEMENTATION` not editable; `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single`, `ALMOST_FULL_ASSERT_LVL`=16382, `ALMOST_FULL_DEASSERT_LVL` not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL` not editable
- Both data counts not editable

**Procedure**

1. Generate and build.
2. In the configuration GUI, confirm the accepted depth range with `FORCE_FAST_CONTROLLER` = 1, then set both depths to 16383.
3. Reset, release, then write 16,383 words of `PAT-INCR` until `full_o` asserts.
4. Read all words back until `empty_o` asserts.

**Pass Criteria**

- The field is offered at all because the internal family is `LIFCL`, and is editable because `FIFO_CONTROLLER` is `HARD_IP` (Rule 22).
- With `FORCE_FAST_CONTROLLER` = 1 the depth `value_range` upper bound is 16383, and 16383 is accepted while 16384 is not (Rule 10, `getDepthLimit`).
- Generation and build complete with no error at that ceiling; the assert level of 16382 satisfies Rule 13 (at most `WADDR_DEPTH`).
- `full_o` asserts at 16,383 held words, per 1.5.5, and the read-back sequence matches in order at two `rd_clk_i` cycles of latency, per 1.5.12.
- No criterion asserts a value on the data-count outputs — see `SPEC-GAP-03` — nor a cycle count for `almost_full_o` deassertion on this path — see `SPEC-GAP-05`.

### G9 · IMPLEMENTATION — Requires FIFO_CONTROLLER = FABRIC

`EBR` is exercised by `TC-FIFODC-001`. The `LUT` card must use matched write and read geometry, since Rule 12 rejects `LUT` outright for a mixed-width configuration; on `LIFCL` that storage maps to distributed RAM (spec 1.5.3).

#### TC-FIFODC-015 — LUT-based storage `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36 — depths and widths equal, as Rule 12 requires
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`LUT`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 512 words of `PAT-INCR` until `full_o` asserts.
3. Read all words back until `empty_o` asserts.

**Pass Criteria**

- `IMPLEMENTATION` is editable because `FIFO_CONTROLLER` is `FABRIC` (Rule 23), and `LUT` is accepted because the write and read geometry match (Rule 12).
- Generation and build complete with no error; the generated constraint output cuts the path from the distributed memory output to the capture register as a false path, per 1.5.12 (Constraints the IP applies) and 1.5.11.
- The read-back sequence matches the written sequence in order at two `rd_clk_i` cycles of latency, per 1.5.12 — the distributed-RAM build registers the addressed word on `rd_clk_i` and the output register adds the second stage, per 1.5.3.
- `full_o`, `empty_o`, `almost_full_o` and `almost_empty_o` behave as in `TC-FIFODC-001`, per 1.5.5 and 1.5.6.

### G10 · REGMODE

`reg` is exercised by `TC-FIFODC-001`, and both `REGMODE` values under fall-through by `TC-FIFODC-012` and `TC-FIFODC-013`. The card below isolates `noreg` without fall-through.

#### TC-FIFODC-016 — Output register disabled `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`noreg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 16 words of `PAT-INCR`.
3. Assert `rd_en_i` for a single cycle and record the cycle in which `rd_data_o` changes; then read the remaining words.
4. Deassert `rd_en_i` for four cycles and observe `rd_data_o`.

**Pass Criteria**

- Generation and build complete with no error.
- `rd_en_i` sampled high in a cycle where `empty_o` is low presents that word on `rd_data_o` in the next cycle — one-cycle read latency, per 1.5.12 (`REGMODE` = `noreg`, `FWFT` = 0).
- The full read-back sequence matches the written sequence in order at that one-cycle latency, per 1.5.12.
- While no read is accepted `rd_data_o` holds its last value: the output register is enable-gated, not cleared, per 1.5.12.

### G11 · RESETMODE

`async` is exercised by `TC-FIFODC-001`, and the reset ports themselves in G23. This card isolates `sync`.

#### TC-FIFODC-017 — Synchronous reset mode `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`sync`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 64 words of `PAT-INCR` and read 32 of them back, leaving the FIFO part full.
3. Assert `rst_i` synchronously to `wr_clk_i` for four cycles, then release it.
4. Write 8 fresh words of `PAT-ALT` and read them back.

**Pass Criteria**

- Generation and build complete with no error; every pointer, flag and counter register is built with a synchronous clear on its own clock, per 1.5.9.
- After reset release `empty_o` and `almost_empty_o` are asserted and `full_o` and `almost_full_o` are deasserted, per 1.5.12 (Flag update delay).
- No word written before the reset is returned after it: the first word read back after release is the first word of `PAT-ALT`, per 1.5.9 (both pointers cleared).
- The eight fresh words read back in order at two `rd_clk_i` cycles of latency, per 1.5.12.

### G12 · ENABLE_ALMOST_FULL_FLAG

`TRUE` is exercised by `TC-FIFODC-001`. This card covers `FALSE`, which also makes `ALMOST_FULL_ASSERTION` non-editable (Rule 25 gating in 1.6) and both almost-full levels read-only (Rules 19, 20).

#### TC-FIFODC-018 — Almost-full flag disabled `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`FALSE`; `ALMOST_FULL_ASSERTION`, `ALMOST_FULL_ASSERT_LVL` and `ALMOST_FULL_DEASSERT_LVL` not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. In the configuration GUI, confirm that the almost-full assertion type and both almost-full level fields are read-only.
3. Reset, release, then write 512 words of `PAT-INCR` until `full_o` asserts, and read them all back.

**Pass Criteria**

- Generation and build complete with no error; the almost-full assertion type and both level fields are read-only with the flag disabled (Rules 19, 20) and the almost-full cross-check passes unconditionally (Rule 13).
- `almost_full_o` is still declared at the module boundary on the generated wrapper (spec 1.3).
- `full_o`, `empty_o` and the read-back data behave exactly as in `TC-FIFODC-001`, per 1.5.5 and 1.5.12 — disabling the flag does not disturb the data path.
- `almost_empty_o` still asserts at 1 word and clears above 2 words, per 1.5.6.
- No criterion asserts a level on `almost_full_o` in this configuration: the spec describes it as driven to 0 by the controller yet dangling at the boundary — see `SPEC-GAP-02`.

### G13 · ALMOST_FULL_ASSERTION

`static-dual` is exercised by `TC-FIFODC-001`. The mode is editable only with the flag enabled and `FIFO_CONTROLLER` = `FABRIC` (Rule 25 gating in 1.6); all three cards therefore run on the fabric controller with the flag on. The four modes differ only in where the two thresholds come from (spec 1.5.6).

#### TC-FIFODC-019 — Almost-full static single threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single`, `ALMOST_FULL_ASSERT_LVL`=400, `ALMOST_FULL_DEASSERT_LVL` not editable (Rule 20)

**Procedure**

1. Generate and build.
2. Reset, release, then write words of `PAT-INCR` until occupancy reaches 400 and record the cycle in which `almost_full_o` asserts.
3. Read one word and record the cycle in which `almost_full_o` clears.

**Pass Criteria**

- Generation and build complete with no error; the assert level of 400 does not exceed `WADDR_DEPTH` = 512 (Rule 13), and the deassert field is read-only outside `static-dual` (Rule 20).
- `almost_full_o` asserts when write-side occupancy reaches 400 words, taking the pending write into account, per 1.5.6.
- `almost_full_o` clears once occupancy falls below 400 — the one assert-level parameter serves as both thresholds, so there is no hysteresis band, per 1.5.6 (`static-single`).
- Deassertion is no later than two `wr_clk_i` cycles after the freeing read is registered on the read side, per 1.5.12 (Flag update delay, fabric controller).

#### TC-FIFODC-020 — Almost-full dynamic single threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`dynamic-single`; `ALMOST_FULL_ASSERT_LVL` and `ALMOST_FULL_DEASSERT_LVL` not editable (Rules 19, 20)

**Procedure**

1. Generate the IP instance; retain the generated wrapper — `TC-FIFODC-046` reuses it.
2. Build (generate, synthesize, map).
3. Before releasing `rst_i`, drive `almost_full_th_i` = 400 and hold it constant for the whole run.
4. Reset, release, then write words of `PAT-INCR` until occupancy reaches 400; read one word back.

**Pass Criteria**

- Generation and build complete with no error; both almost-full level fields are read-only in a dynamic mode (Rules 19, 20) and `almost_full_th_i` is 9 bits wide (Rule 27).
- `almost_full_o` asserts when write-side occupancy reaches the value on `almost_full_th_i`, per 1.5.6 (`dynamic-single`).
- `almost_full_o` clears once occupancy falls below that same value — the one port serves as both thresholds, per 1.5.6.
- The threshold is held constant for the whole run; no criterion covers changing it mid-operation — see `SPEC-GAP-04`.

#### TC-FIFODC-021 — Almost-full dynamic dual threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`dynamic-dual`; both almost-full level fields not editable

**Procedure**

1. Generate the IP instance; retain the generated wrapper — `TC-FIFODC-047` reuses it.
2. Build (generate, synthesize, map).
3. Before releasing `rst_i`, drive `almost_full_th_i` = 400 and `almost_full_clr_th_i` = 380 and hold both constant for the whole run.
4. Reset, release, then write until occupancy reaches 400; read words back one at a time down to occupancy 379, recording each `almost_full_o` transition.

**Pass Criteria**

- Generation and build complete with no error; `almost_full_th_i` and `almost_full_clr_th_i` are each 9 bits wide (Rule 27).
- `almost_full_o` asserts when occupancy reaches the `almost_full_th_i` value of 400, per 1.5.6.
- `almost_full_o` stays asserted while occupancy lies between the two thresholds and clears only once occupancy falls below the `almost_full_clr_th_i` value of 380 — the dual-threshold hysteresis of 1.5.6.
- Both thresholds are held constant for the whole run — see `SPEC-GAP-04`.

### G14 · ALMOST_FULL_ASSERT_LVL

At `WADDR_DEPTH` = 512 the legal range is 1 to 511 (Rule 15). The maximum, 511, is exercised by `TC-FIFODC-001`. The minimum card must use `static-single`: with `static-dual` and an assert level of 1, Rule 16 leaves the deassert range empty, so that combination is not legal.

#### TC-FIFODC-022 — Almost-full assert level at minimum `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single`, `ALMOST_FULL_ASSERT_LVL`=1, `ALMOST_FULL_DEASSERT_LVL` not editable

**Procedure**

1. Generate and build.
2. Reset, release, then write a single word of `PAT-INCR` and record `almost_full_o`.
3. Read that word back and record `almost_full_o` again.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` lower bound of 1 (Rule 15); the level does not exceed `WADDR_DEPTH` (Rule 13).
- `almost_full_o` asserts as soon as write-side occupancy reaches 1 word, per 1.5.6.
- `almost_full_o` clears once occupancy falls below 1 word, per 1.5.6 (`static-single`).

#### TC-FIFODC-023 — Almost-full assert level at median `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=256, `ALMOST_FULL_DEASSERT_LVL`=255

This card carries the median of both almost-full levels: 256 is the midpoint of the assert range 1 to 511 (Rule 15), and 255 the midpoint of the deassert range 1 to 510 that the default assert level of 511 permits (Rule 16).

**Procedure**

1. Generate and build.
2. Reset, release, then write words of `PAT-INCR` until occupancy reaches 256.
3. Read one word back, then a second, recording each `almost_full_o` transition.

**Pass Criteria**

- Generation and build complete with no error; 255 < 256 <= 512 satisfies the almost-full cross-check (Rule 13) and 255 lies inside the deassert range of 1 to 255 (Rule 16).
- `almost_full_o` asserts when occupancy reaches 256, per 1.5.6.
- `almost_full_o` stays asserted at occupancy 255 and clears once occupancy falls below 255, per 1.5.6 (`static-dual` hysteresis).

### G15 · ALMOST_FULL_DEASSERT_LVL

The maximum, 510, is exercised by `TC-FIFODC-001` and the median, 255, by `TC-FIFODC-023`. This card covers the minimum, giving the widest legal hysteresis band.

#### TC-FIFODC-024 — Almost-full deassert level at minimum `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-empty settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=1

**Procedure**

1. Generate and build.
2. Reset, release, then write 511 words of `PAT-INCR` and record the `almost_full_o` assertion.
3. Read words back one at a time down to occupancy 0, recording the cycle in which `almost_full_o` clears.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` lower bound of 1 (Rule 16), with 1 < 511 <= 512 satisfying Rule 13.
- `almost_full_o` asserts when occupancy reaches 511, per 1.5.6.
- `almost_full_o` remains asserted through every occupancy from 510 down to 1 and clears only once occupancy falls below 1, per 1.5.6 — the widest hysteresis band the rules allow.

### G16 · ENABLE_ALMOST_EMPTY_FLAG

`TRUE` is exercised by `TC-FIFODC-001`. This card covers `FALSE`.

#### TC-FIFODC-025 — Almost-empty flag disabled `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`FALSE`; `ALMOST_EMPTY_ASSERTION`, `ALMOST_EMPTY_ASSERT_LVL` and `ALMOST_EMPTY_DEASSERT_LVL` not editable
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. In the configuration GUI, confirm that the almost-empty assertion type and both almost-empty level fields are read-only.
3. Reset, release, then write 512 words of `PAT-INCR` and read them all back.

**Pass Criteria**

- Generation and build complete with no error; the almost-empty assertion type and both level fields are read-only with the flag disabled (Rules 19, 20) and the almost-empty cross-check passes unconditionally (Rule 14).
- `almost_empty_o` is still declared at the module boundary on the generated wrapper (spec 1.3).
- `full_o`, `empty_o` and the read-back data behave exactly as in `TC-FIFODC-001`, per 1.5.5 and 1.5.12.
- `almost_full_o` still asserts at 511 words and clears below 510, per 1.5.6.
- No criterion asserts a level on `almost_empty_o` in this configuration — see `SPEC-GAP-02`.

### G17 · ALMOST_EMPTY_ASSERTION

`static-dual` is exercised by `TC-FIFODC-001`. The almost-empty flag behaves symmetrically to the almost-full flag: it asserts when read-side occupancy falls to the assert threshold and clears when occupancy rises above the deassert threshold, and it is asserted out of reset (spec 1.5.6).

#### TC-FIFODC-026 — Almost-empty static single threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single`, `ALMOST_EMPTY_ASSERT_LVL`=100, `ALMOST_EMPTY_DEASSERT_LVL` not editable (Rule 20)

**Procedure**

1. Generate and build.
2. Reset, release, then write 200 words of `PAT-INCR`, confirming that `almost_empty_o` clears.
3. Read words back until occupancy falls to 100 and record the `almost_empty_o` assertion; write one more word and record the clear.

**Pass Criteria**

- Generation and build complete with no error; the assert level of 100 is at least 1 (Rule 14) and inside the range of 1 to 511 (Rule 17).
- `almost_empty_o` is asserted immediately after reset release, per 1.5.6.
- `almost_empty_o` asserts when read-side occupancy falls to 100 words, taking the pending read into account, per 1.5.6.
- `almost_empty_o` clears once occupancy rises above 100 — the one assert-level parameter serves as both thresholds, per 1.5.6 (`static-single`).
- Assertion is no later than two `rd_clk_i` cycles after the source registration, per 1.5.12 (Flag update delay, fabric controller).

#### TC-FIFODC-027 — Almost-empty dynamic single threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`dynamic-single`; both almost-empty level fields not editable

**Procedure**

1. Generate the IP instance; retain the generated wrapper — `TC-FIFODC-048` reuses it.
2. Build (generate, synthesize, map).
3. Before releasing `rst_i`, drive `almost_empty_th_i` = 100 and hold it constant for the whole run.
4. Reset, release, write 200 words, then read back until occupancy falls to 100; write one more word.

**Pass Criteria**

- Generation and build complete with no error; both almost-empty level fields are read-only in a dynamic mode (Rules 19, 20) and `almost_empty_th_i` is 9 bits wide (Rule 27).
- `almost_empty_o` asserts when read-side occupancy falls to the value on `almost_empty_th_i`, per 1.5.6 (`dynamic-single`).
- `almost_empty_o` clears once occupancy rises above that same value, per 1.5.6.
- The threshold is held constant for the whole run — see `SPEC-GAP-04`.

#### TC-FIFODC-028 — Almost-empty dynamic dual threshold `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`dynamic-dual`; both almost-empty level fields not editable

**Procedure**

1. Generate the IP instance; retain the generated wrapper — `TC-FIFODC-049` reuses it.
2. Build (generate, synthesize, map).
3. Before releasing `rst_i`, drive `almost_empty_th_i` = 100 and `almost_empty_clr_th_i` = 120 and hold both constant for the whole run.
4. Reset, release, write 200 words, read back until occupancy falls to 100, then write words back one at a time up to occupancy 121, recording each `almost_empty_o` transition.

**Pass Criteria**

- Generation and build complete with no error; `almost_empty_th_i` and `almost_empty_clr_th_i` are each 9 bits wide (Rule 27).
- `almost_empty_o` asserts when occupancy falls to the `almost_empty_th_i` value of 100, per 1.5.6.
- `almost_empty_o` stays asserted while occupancy lies between the two thresholds and clears only once occupancy rises above the `almost_empty_clr_th_i` value of 120 — the dual-threshold hysteresis of 1.5.6.
- Both thresholds are held constant for the whole run — see `SPEC-GAP-04`.

### G18 · ALMOST_EMPTY_ASSERT_LVL

At `RADDR_DEPTH` = 512 the legal range is 1 to 511 (Rule 17). The minimum, 1, is exercised by `TC-FIFODC-001`. The maximum card must use `static-single`: with `static-dual` and an assert level of 511, Rule 18 puts the deassert lower bound at 512 while the upper bound is 511, leaving the range empty, so that combination is not legal.

#### TC-FIFODC-029 — Almost-empty assert level at median `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=256, `ALMOST_EMPTY_DEASSERT_LVL`=257

256 is the midpoint of the assert range 1 to 511 (Rule 17); 257 is the lowest legal deassert level for that assert level (Rule 18).

**Procedure**

1. Generate and build.
2. Reset, release, then write 300 words of `PAT-INCR`, confirming that `almost_empty_o` clears.
3. Read words back until occupancy falls to 256 and record the assertion; write words back up to occupancy 258, recording the clear.

**Pass Criteria**

- Generation and build complete with no error; 257 > 256 >= 1 satisfies the almost-empty cross-check (Rule 14) and 257 lies inside the deassert range of 257 to 511 (Rule 18).
- `almost_empty_o` asserts when occupancy falls to 256, per 1.5.6.
- `almost_empty_o` stays asserted at occupancy 257 and clears once occupancy rises above 257, per 1.5.6 (`static-dual` hysteresis).

#### TC-FIFODC-030 — Almost-empty assert level at maximum `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single`, `ALMOST_EMPTY_ASSERT_LVL`=511, `ALMOST_EMPTY_DEASSERT_LVL` not editable

**Procedure**

1. Generate and build.
2. Reset, release, then write 512 words of `PAT-INCR` until `full_o` asserts, recording the `almost_empty_o` clear.
3. Read one word back and record the `almost_empty_o` assertion.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` upper bound of 511 (Rule 17), with the level at least 1 (Rule 14).
- `almost_empty_o` clears only once occupancy rises above 511 — that is, at full occupancy of 512 words, per 1.5.6.
- `almost_empty_o` asserts again as soon as occupancy falls to 511, per 1.5.6 (`static-single`).

### G19 · ALMOST_EMPTY_DEASSERT_LVL

The minimum, 2, is exercised by `TC-FIFODC-001` at an assert level of 1 (Rule 18 puts the lower bound at assert + 1). The two cards below cover the median and the maximum.

#### TC-FIFODC-031 — Almost-empty deassert level at median `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=100, `ALMOST_EMPTY_DEASSERT_LVL`=256

256 is the midpoint of the deassert range 2 to 511 (Rule 18); the assert level is lowered to 100 so that 256 is inside the range that level permits.

**Procedure**

1. Generate and build.
2. Reset, release, then write 300 words of `PAT-INCR`.
3. Read words back until occupancy falls to 100 and record the assertion.
4. Write words back one at a time up to occupancy 257, recording each `almost_empty_o` transition.

**Pass Criteria**

- Generation and build complete with no error; 256 > 100 >= 1 satisfies Rule 14 and 256 lies inside the deassert range of 101 to 511 (Rule 18).
- `almost_empty_o` asserts when occupancy falls to 100, per 1.5.6.
- `almost_empty_o` remains asserted through every occupancy from 101 to 256 and clears only once occupancy rises above 256, per 1.5.6.

#### TC-FIFODC-032 — Almost-empty deassert level at maximum `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, almost-full settings and both data counts as `TC-FIFODC-001`.
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=511

**Procedure**

1. Generate and build.
2. Reset, release, then write 512 words of `PAT-INCR` until `full_o` asserts, recording the `almost_empty_o` clear.
3. Read words back down to occupancy 1, recording the assertion.

**Pass Criteria**

- Generation and build complete with no error at the `value_range` upper bound of 511 (Rule 18), with 511 > 1 >= 1 satisfying Rule 14.
- `almost_empty_o` clears only once occupancy rises above 511 — at 512 words, per 1.5.6.
- `almost_empty_o` remains deasserted only at full occupancy and asserts once occupancy falls to 1, staying asserted through every occupancy from 2 to 511, per 1.5.6 — the widest almost-empty hysteresis band the rules allow.

### G20 · ENABLE_DATA_COUNT_WR — Requires FIFO_CONTROLLER = FABRIC

`FALSE` is exercised by `TC-FIFODC-001`, and the read-only state under `HARD_IP` by `TC-FIFODC-010` (Rule 24). This card covers `TRUE`.

#### TC-FIFODC-033 — Write-side data count enabled `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, and both almost-flag groups as `TC-FIFODC-001`.
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`FALSE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 128 words of `PAT-INCR` with `rd_en_i` held low, sampling `wr_data_cnt_o` on each `wr_clk_i` edge.
3. Read 64 words back, then allow the write side to settle for at least four `wr_clk_i` cycles and sample `wr_data_cnt_o` again.

**Pass Criteria**

- `ENABLE_DATA_COUNT_WR` is editable because `FIFO_CONTROLLER` is `FABRIC` (Rule 24), and generation and build complete with no error.
- `wr_data_cnt_o` is 10 bits wide, being `WADDR_WIDTH` + 1 with `WADDR_WIDTH` = `clog2(512)` = 9 (spec 1.3, Rule 27).
- With no reads in progress, `wr_data_cnt_o` reaches 128 after the 128th accepted write, per 1.5.7.
- `wr_data_cnt_o` never over-reports occupancy: at every sample it is at most the true number of words held, because it is computed from the synchronized read pointer, per 1.5.7 and spec 1.3.
- After the 64 reads and the settling period, `wr_data_cnt_o` reads 64, per 1.5.7.
- `rd_data_cnt_o` carries no criterion here; the read counter is disabled — see `SPEC-GAP-03`.

### G21 · ENABLE_DATA_COUNT_RD — Requires FIFO_CONTROLLER = FABRIC

`FALSE` is exercised by `TC-FIFODC-001`, and the read-only state under `HARD_IP` by `TC-FIFODC-010`. This card covers `TRUE`.

#### TC-FIFODC-034 — Read-side data count enabled `Both`

**Configuration**

- Geometry, controller, storage, `REGMODE`, `RESETMODE`, and both almost-flag groups as `TC-FIFODC-001`.
- `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`TRUE`

**Procedure**

1. Generate and build.
2. Reset, release, then write 128 words of `PAT-INCR`; allow at least four `rd_clk_i` cycles of settling and sample `rd_data_cnt_o`.
3. Read 64 words back and sample `rd_data_cnt_o` on each `rd_clk_i` edge.

**Pass Criteria**

- `ENABLE_DATA_COUNT_RD` is editable because `FIFO_CONTROLLER` is `FABRIC` (Rule 24), and generation and build complete with no error.
- `rd_data_cnt_o` is 10 bits wide, being `RADDR_WIDTH` + 1 with `RADDR_WIDTH` = `clog2(512)` = 9 (spec 1.3, Rule 27).
- After the settling period `rd_data_cnt_o` reads 128, per 1.5.7.
- `rd_data_cnt_o` never over-reports occupancy at any sample, being computed from the synchronized write pointer, per 1.5.7 and spec 1.3.
- After the 64 reads, `rd_data_cnt_o` reads 64, per 1.5.7.

### G22 · Cross-Parameter Legal Combinations

Six configurations in which the interacting parameters move together. Each satisfies every rule of spec 1.7 simultaneously: capacities match (Rule 6), width factors stay at or below the `LIFCL` limit of 32 (Rule 8), fabric depths are powers of two (Rule 7), `LUT` storage is used only with matched geometry (Rule 12), and no card sets a parameter that the controller choice makes non-editable (Rules 22 to 25).

#### TC-FIFODC-035 — Wide write to narrow read, dynamic dual flags, both counts `Both`

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=32, `RADDR_DEPTH`=16384, `RDATA_WIDTH`=1 (capacity 16,384 = 16,384 bits, Rule 6; write-to-read factor 32, Rules 4 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR` (mixed geometry rules out `LUT`, Rule 12), `REGMODE`=`reg`, `RESETMODE`=`sync`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`dynamic-dual`; both almost-full level fields not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`dynamic-dual`; both almost-empty level fields not editable
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`TRUE`

**Procedure**

1. Generate and build.
2. Before releasing `rst_i`, drive `almost_full_th_i` = 400, `almost_full_clr_th_i` = 380, `almost_empty_th_i` = 4000 and `almost_empty_clr_th_i` = 6000, and hold all four constant for the run.
3. Reset, release, then write 400 words of 32-bit `PAT-INCR`, sampling `wr_data_cnt_o`.
4. Drain read-side words down through 4000 and then, by interleaving writes, back up to 6001, sampling `rd_data_cnt_o` and both almost flags.

**Pass Criteria**

- Generation and build complete with no error at a write-to-read width factor of 32 with matched capacities (Rules 4, 6, 8).
- `almost_full_th_i` and `almost_full_clr_th_i` are each 9 bits wide (`clog2(512)`); `almost_empty_th_i` and `almost_empty_clr_th_i` are each 14 bits wide (`clog2(16384)`); `wr_data_cnt_o` is 10 bits and `rd_data_cnt_o` is 15 bits (spec 1.3, Rule 27).
- Each 32-bit written word appears on `rd_data_o` as 32 single-bit read words in write order, per 1.5.4, at two `rd_clk_i` cycles of latency, per 1.5.12.
- `almost_full_o` asserts at write occupancy 400 and clears only below 380, per 1.5.6; `almost_empty_o` asserts at read occupancy 4000 and clears only above 6000, per 1.5.6.
- Neither counter over-reports occupancy at any sample, per 1.5.7.
- All four thresholds are held constant for the run — see `SPEC-GAP-04`.

#### TC-FIFODC-036 — Narrow write to wide read with fall-through `Both`

**Configuration**

- `WADDR_DEPTH`=16384, `WDATA_WIDTH`=1, `RADDR_DEPTH`=512, `RDATA_WIDTH`=32 (capacity 16,384 = 16,384 bits, Rule 6; read-to-write factor 32, Rules 5 and 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=1, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`noreg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=16383, `ALMOST_FULL_DEASSERT_LVL`=16382
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`TRUE`

**Procedure**

1. Generate and build.
2. Reset, release, and hold `rd_en_i` low. Write 32 single-bit words of `PAT-INCR` — one full read word.
3. Observe `empty_o` and `rd_data_o` with `rd_en_i` still low.
4. Acknowledge with one cycle of `rd_en_i`, then write and read a further 8 read words, sampling both counters.

**Pass Criteria**

- Generation and build complete with no error at a read-to-write factor of 32 with matched capacities (Rules 5, 6, 8).
- `empty_o` deasserts once a whole 32-bit read word is available, and that word is already present on `rd_data_o` at that moment — zero-cycle first-word latency, per 1.5.12 (`FWFT` = 1, `REGMODE` = `noreg`) and 1.5.8.
- Each group of 32 written bits appears as one 32-bit read word in write order, per 1.5.4.
- `almost_full_o` asserts at write occupancy 16,383 and clears below 16,382, per 1.5.6; `almost_empty_o` asserts at read occupancy 1 and clears above 2, per 1.5.6.
- `wr_data_cnt_o` is 15 bits and `rd_data_cnt_o` is 10 bits, and neither over-reports occupancy, per 1.5.7 and Rule 27.

#### TC-FIFODC-037 — High-speed hardened controller with fall-through and sync reset `Both`

**Configuration**

- `WADDR_DEPTH`=8192, `WDATA_WIDTH`=36, `RADDR_DEPTH`=8192, `RDATA_WIDTH`=36 (capacity 294,912 bits, Rules 1 and 6; within the reduced ceiling of 16383, Rule 10)
- `FIFO_CONTROLLER`=`HARD_IP`, `FWFT`=1, `FORCE_FAST_CONTROLLER`=1
- `IMPLEMENTATION` not editable (Rule 23); `REGMODE`=`reg`, `RESETMODE`=`sync`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single` (forced, Rule 25), `ALMOST_FULL_ASSERT_LVL`=8191, `ALMOST_FULL_DEASSERT_LVL` not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single` (forced), `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL` not editable
- Both data counts not editable (Rule 24)

**Procedure**

1. Generate and build.
2. Reset synchronously to `wr_clk_i`, release, and hold `rd_en_i` low. Write a single word of `PAT-INCR`.
3. Record the cycle in which `empty_o` deasserts and the cycle in which `rd_data_o` becomes valid.
4. Acknowledge and read a further 16 words; then fill to 8191 words and record `almost_full_o`.

**Pass Criteria**

- Generation and build complete with no error: `FORCE_FAST_CONTROLLER` is editable because the controller is `HARD_IP` (Rule 22) and 8192 is inside the reduced depth range (Rule 10).
- The first available word reaches `rd_data_o` one `rd_clk_i` cycle after the prefetch is accepted, so `empty_o` deassertion leads it by one cycle, per 1.5.12 (`FWFT` = 1, `REGMODE` = `reg`) and 1.5.8.
- The 16 further words appear on `rd_data_o` in write order at that same one-cycle offset, per 1.5.8.
- `almost_full_o` asserts at write occupancy 8191, per 1.5.6, with a single threshold serving both assert and deassert.
- No criterion asserts a value on the data-count outputs (`SPEC-GAP-03`) or a cycle count for `almost_full_o` deassertion on this path (`SPEC-GAP-05`).

#### TC-FIFODC-038 — LUT storage, fall-through, flags disabled, both counts `Both`

**Configuration**

- `WADDR_DEPTH`=64, `WDATA_WIDTH`=8, `RADDR_DEPTH`=64, `RDATA_WIDTH`=8 (capacity 512 = 512 bits; geometry matched, as Rule 12 requires)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=1, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`LUT`, `REGMODE`=`noreg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`FALSE`, `ENABLE_ALMOST_EMPTY_FLAG`=`FALSE`; all four level fields and both assertion types not editable
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`TRUE`

**Procedure**

1. Generate and build.
2. Reset, release, and hold `rd_en_i` low. Write one word of `PAT-WALK1`; observe `empty_o` and `rd_data_o`.
3. Acknowledge, then write and read all 64 words, sampling both counters.

**Pass Criteria**

- Generation and build complete with no error: `LUT` is accepted because the write and read geometry match (Rule 12), and both counters are editable because the controller is `FABRIC` (Rule 24).
- The generated constraint output cuts the distributed-memory output path as a false path, per 1.5.12 (Constraints the IP applies).
- `empty_o` deasserts after the first write with the first word already on `rd_data_o` — zero-cycle first-word latency, per 1.5.12 and 1.5.8.
- All 64 words read back in order with no bit-lane crossing, per 1.5.4.
- `wr_data_cnt_o` and `rd_data_cnt_o` are each 7 bits wide, being `clog2(64)` + 1 (spec 1.3, Rule 27), and neither over-reports occupancy, per 1.5.7.
- No criterion asserts a level on `almost_full_o` or `almost_empty_o` — see `SPEC-GAP-02`.

#### TC-FIFODC-039 — Minimum geometry on the hardened controller `Both`

**Configuration**

- `WADDR_DEPTH`=2, `WDATA_WIDTH`=1, `RADDR_DEPTH`=2, `RDATA_WIDTH`=1 (capacity 2 = 2 bits, Rule 6)
- `FIFO_CONTROLLER`=`HARD_IP`, `FWFT`=1, `FORCE_FAST_CONTROLLER`=0
- `IMPLEMENTATION` not editable; `REGMODE`=`noreg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-single` (forced, Rule 25), `ALMOST_FULL_ASSERT_LVL`=1 (collapsed by `getLoop` at depth 2, Rule 26), `ALMOST_FULL_DEASSERT_LVL` not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-single` (forced), `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL` not editable
- Both data counts not editable

**Procedure**

1. Generate and build.
2. Reset, release, and hold `rd_en_i` low. Write one word of `PAT-ALT`; observe `empty_o` and `rd_data_o`.
3. Write a second word so both storage locations are occupied, confirm `full_o`, then acknowledge and drain both words.

**Pass Criteria**

- Generation and build complete with no error at the smallest legal geometry on the hardened path, with all four level settings collapsed to 1 (Rule 26).
- `empty_o` deasserts after the first write with that word already on `rd_data_o` — zero-cycle first-word latency, per 1.5.12 and 1.5.8.
- `full_o` asserts once both locations hold data and blocks a third write, per 1.5.5 and 1.5.4.
- Both words drain in write order, per 1.5.8, with `empty_o` re-asserting when none remains, per 1.5.8.
- `almost_full_o` asserts at occupancy 1, per 1.5.6. No criterion asserts a data-count value (`SPEC-GAP-03`) or an `almost_full_o` deassert cycle count on this path (`SPEC-GAP-05`).

#### TC-FIFODC-040 — Near-ceiling memory budget with dynamic dual flags `Both`

**Configuration**

- `WADDR_DEPTH`=8192, `WDATA_WIDTH`=180, `RADDR_DEPTH`=8192, `RDATA_WIDTH`=180 (capacity 1,474,560 = 1,474,560 bits, inside but close to the 1,548,288-bit `LIFCL` budget, Rules 1 and 6; width factor 1, Rule 8)
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`dynamic-dual`; both almost-full level fields not editable
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`dynamic-dual`; both almost-empty level fields not editable
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`TRUE`

**Procedure**

1. Generate and build.
2. In the configuration GUI, confirm that the read-only capacity readout shows 1,474,560 bits (Rule 29) and that the configuration is accepted.
3. Before releasing `rst_i`, drive `almost_full_th_i` = 8000, `almost_full_clr_th_i` = 7500, `almost_empty_th_i` = 100 and `almost_empty_clr_th_i` = 200, and hold all four constant for the run.
4. Reset, release, then write 8000 words of `PAT-WALK1` and drain them, sampling both counters and both almost flags.

**Pass Criteria**

- Generation and build complete with no error: the total memory size does not exceed the `LIFCL` budget of 1,548,288 bits (Rule 1) and the depth is a power of two (Rule 7).
- The four threshold ports are each 13 bits wide (`clog2(8192)`), and both counters 14 bits (spec 1.3, Rule 27).
- Every bit position of every 180-bit word reads back unchanged and in order at two `rd_clk_i` cycles of latency, per 1.5.4 and 1.5.12.
- `almost_full_o` asserts at occupancy 8000 and clears only below 7500, per 1.5.6; `almost_empty_o` asserts at occupancy 100 and clears only above 200, per 1.5.6.
- Neither counter over-reports occupancy, per 1.5.7.
- No criterion asserts a memory-block count or a tiling arrangement for this configuration — see `SPEC-GAP-06`. All four thresholds are held constant — see `SPEC-GAP-04`.

### G23 · Port Behaviour

Four of the twenty ports have no independent behaviour of their own to sweep and are accounted for here rather than by a dedicated card. `wr_clk_i` and `rd_clk_i` are driven at unrelated frequencies by every simulated case in this plan, and the clock creation for both is emitted by the component generator (spec 1.5.11); `TC-FIFODC-050` is the case that specifically depends on their independence. `wr_data_i` and `rd_data_o` are stimulated and observed by every simulated case's read-data integrity check, and `rd_data_o` latency is asserted by `TC-FIFODC-001`, `TC-FIFODC-012`, `TC-FIFODC-013` and `TC-FIFODC-016` across all four timing-distinct read configurations of spec 1.5.12. The remaining sixteen ports are covered by the cards below and by the groups they cross-reference.

#### TC-FIFODC-041 — Write enable ignored while full `Sim Only`

Reuse the generated output of `TC-FIFODC-001` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-001` in all twenty parameters.

**Procedure**

1. Reset, release, then write 512 words of `PAT-INCR` with `rd_en_i` held low until `full_o` asserts.
2. Hold `wr_en_i` asserted for a further 16 `wr_clk_i` cycles while `full_o` is high, presenting distinct `PAT-ALT` words on `wr_data_i`.
3. Deassert `wr_en_i`, then drain all 512 words with `rd_en_i`.

**Pass Criteria**

- The 512 words read back are exactly the 512 `PAT-INCR` words in write order — none of the 16 words offered while `full_o` was high entered the FIFO, per 1.5.4.
- `full_o` remains asserted throughout step 2 and the write pointer does not advance: asserting `wr_en_i` while full is harmless, per 1.5.4.
- `empty_o` asserts after the 512th word is read, per 1.5.5.

#### TC-FIFODC-042 — Read enable ignored while empty, output hold `Sim Only`

Reuse the generated output of `TC-FIFODC-001` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-001` in all twenty parameters.

**Procedure**

1. Reset, release, then hold `rd_en_i` asserted for 16 `rd_clk_i` cycles while `empty_o` is high, and record `rd_data_o` on each edge.
2. Deassert `rd_en_i`, write 4 words of `PAT-INCR`, then read all 4 back.
3. Deassert `rd_en_i` for 8 further `rd_clk_i` cycles and record `rd_data_o`.

**Pass Criteria**

- Throughout step 1 no read is accepted, the read pointer does not advance, and `rd_data_o` does not change, per 1.5.12 (`rd_en_i` asserted while `empty_o` is high has no effect) and 1.5.4.
- The 4 words read back in step 2 are the 4 written words in order, each valid two `rd_clk_i` cycles after its accepted read, per 1.5.12.
- Throughout step 3 `rd_data_o` holds the last read word: the output register is enable-gated, not cleared, per 1.5.12.
- `empty_o` re-asserts after the 4th word is read, per 1.5.5.

#### TC-FIFODC-043 — Asynchronous reset structure `Radiant Compilation`

`rst_i` and `rp_rst_i` are applied asynchronously in this mode, so the assertion edge is transient behaviour and is checked structurally rather than in simulation, per the transient-behavior rule in section 1.

**Configuration**

- `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36
- `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`
- `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510
- `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2
- `ENABLE_DATA_COUNT_WR`=`TRUE`, `ENABLE_DATA_COUNT_RD`=`TRUE` — so that the counter registers are present and their clear can be inspected

**Procedure**

1. Generate the IP instance and inspect the generated RTL for the reset construction on the pointer, flag and counter registers.
2. Build in Radiant: synthesize and map.

**Pass Criteria**

- Generation, synthesis and map complete with no errors.
- Every pointer, flag and counter register is built with an asynchronous clear, per 1.5.9 (`RESETMODE` = `async`).
- `rst_i` reaches the read-domain registers through a two-stage reset synchronizer clocked by `rd_clk_i`, so reset release on the read side is synchronous to `rd_clk_i`, per 1.5.9.
- `rp_rst_i` reaches the read pointer, the read data counter and the read output register, and reaches no write-side register, per 1.5.9.
- The block RAM build requests synchronous reset release from the memory block regardless of `RESETMODE`, per 1.5.9.
- No pass criterion here observes a reset waveform; the asynchronous assertion edge is not simulated, per the transient-behavior rule.

#### TC-FIFODC-044 — Main reset clear and post-release flag state `Both`

**Configuration**

- As `TC-FIFODC-043`, with `RESETMODE`=`sync`. Retain the generated wrapper — `TC-FIFODC-045` and `TC-FIFODC-051` reuse it.

**Procedure**

1. Generate and build.
2. Reset synchronously to `wr_clk_i`, release, and sample `full_o`, `empty_o`, `almost_full_o`, `almost_empty_o`, `wr_data_cnt_o` and `rd_data_cnt_o`.
3. Write 200 words of `PAT-INCR` and read 100 back, leaving 100 held.
4. Assert `rst_i` for four `wr_clk_i` cycles, release it, and sample the same six outputs again.
5. Write 8 words of `PAT-ALT` and read them back.

**Pass Criteria**

- Generation and build complete with no error; every pointer, flag and counter register carries a synchronous clear on its own clock, per 1.5.9.
- Immediately after each reset release, `empty_o` and `almost_empty_o` are asserted and `full_o` and `almost_full_o` are deasserted, per 1.5.12 (Flag update delay) and 1.5.5, 1.5.6.
- After each reset release both `wr_data_cnt_o` and `rd_data_cnt_o` read 0, per 1.5.7 and 1.5.9 (both pointers cleared).
- `rst_i` clears both sides: no word written before step 4 is returned after it, and the first word read back is the first `PAT-ALT` word, per 1.5.9.
- The first write after release cannot clear `empty_o` before the crossing delay of two `rd_clk_i` cycles beyond the source registration, per 1.5.12 (Flag update delay).
- The 8 fresh words read back in order at two `rd_clk_i` cycles of latency, per 1.5.12.

#### TC-FIFODC-045 — Read-pointer reset leaves the write side intact `Sim Only`

Reuse the generated output of `TC-FIFODC-044` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-044` in all twenty parameters.

**Procedure**

1. Reset, release, then write 200 words of `PAT-INCR` and read 100 back, sampling both counters.
2. Assert `rp_rst_i` synchronously to `rd_clk_i` for four cycles, then release it.
3. Sample `rd_data_cnt_o`, `wr_data_cnt_o`, `full_o`, `empty_o` and `rd_data_o`.
4. Read words back and record the sequence returned.

**Pass Criteria**

- `rp_rst_i` clears the read pointer, the read data counter and the read output register, per 1.5.9.
- `rd_data_cnt_o` reads 0 immediately after the `rp_rst_i` release, per 1.5.9.
- The write side is not disturbed: `wr_data_cnt_o` still reports the 200 accepted writes (never over-reporting, per 1.5.7) and the write pointer is unchanged, per 1.5.9.
- Because the read pointer was cleared while the write pointer was not, the words returned after step 2 begin again at the first written word, per 1.5.9 — the read side has been flushed independently.
- `rd_data_o` is cleared by the `rp_rst_i` assertion rather than holding its pre-reset value, per 1.5.9 (the read output register is among the registers cleared).

#### TC-FIFODC-046 — Almost-full dynamic assert threshold port `Sim Only`

Reuse the generated output of `TC-FIFODC-020` — this case shares every generation-time input with it; only the constant driven on `almost_full_th_i`, a runtime port, differs.

**Configuration**

- Identical to `TC-FIFODC-020` in all twenty parameters. `almost_full_th_i` is held at 64 for the whole run, in place of the 400 that case used.

**Procedure**

1. Before releasing `rst_i`, drive `almost_full_th_i` = 64 and hold it constant.
2. Reset, release, then write words of `PAT-INCR` one at a time up to occupancy 64, recording `almost_full_o` at each occupancy.
3. Read words back one at a time down to occupancy 62, recording `almost_full_o` at each occupancy.

**Pass Criteria**

- `almost_full_o` is deasserted at every occupancy from 0 to 63 and asserts at occupancy 64 — the value on `almost_full_th_i`, not the read-only `ALMOST_FULL_ASSERT_LVL` parameter, per 1.5.6 (`dynamic-single`).
- `almost_full_o` clears once occupancy falls below 64, the same port serving as the deassert threshold, per 1.5.6.
- Deassertion is no later than two `wr_clk_i` cycles after the freeing read is registered on the read side, per 1.5.12 (Flag update delay, fabric controller).
- The threshold is constant for the whole run — see `SPEC-GAP-04`.

#### TC-FIFODC-047 — Almost-full dynamic clear threshold port `Sim Only`

Reuse the generated output of `TC-FIFODC-021` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-021` in all twenty parameters. `almost_full_th_i` is held at 64 and `almost_full_clr_th_i` at 16 for the whole run.

**Procedure**

1. Before releasing `rst_i`, drive `almost_full_th_i` = 64 and `almost_full_clr_th_i` = 16 and hold both constant.
2. Reset, release, then write up to occupancy 64.
3. Read words back one at a time from occupancy 63 down to 15, recording `almost_full_o` at each occupancy.

**Pass Criteria**

- `almost_full_o` asserts at occupancy 64, the `almost_full_th_i` value, per 1.5.6.
- `almost_full_o` remains asserted at every occupancy from 63 down to 16 and clears only once occupancy falls below 16, the `almost_full_clr_th_i` value — a 48-word hysteresis band set entirely from the ports, per 1.5.6 (`dynamic-dual`).
- Both thresholds are constant for the whole run — see `SPEC-GAP-04`.

#### TC-FIFODC-048 — Almost-empty dynamic assert threshold port `Sim Only`

Reuse the generated output of `TC-FIFODC-027` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-027` in all twenty parameters. `almost_empty_th_i` is held at 32 for the whole run, in place of the 100 that case used.

**Procedure**

1. Before releasing `rst_i`, drive `almost_empty_th_i` = 32 and hold it constant.
2. Reset, release, then write 64 words of `PAT-INCR`, recording the `almost_empty_o` clear.
3. Read words back one at a time down to occupancy 32, recording `almost_empty_o` at each occupancy; then write one word back.

**Pass Criteria**

- `almost_empty_o` is asserted immediately after reset release, per 1.5.6.
- `almost_empty_o` clears once occupancy rises above 32 — the value on `almost_empty_th_i`, not the read-only `ALMOST_EMPTY_ASSERT_LVL` parameter, per 1.5.6 (`dynamic-single`).
- `almost_empty_o` asserts again when occupancy falls to 32, the same port serving as the deassert threshold, per 1.5.6.
- Assertion is no later than two `rd_clk_i` cycles after the source registration, per 1.5.12 (Flag update delay, fabric controller).
- The threshold is constant for the whole run — see `SPEC-GAP-04`.

#### TC-FIFODC-049 — Almost-empty dynamic clear threshold port `Sim Only`

Reuse the generated output of `TC-FIFODC-028` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-028` in all twenty parameters. `almost_empty_th_i` is held at 32 and `almost_empty_clr_th_i` at 96 for the whole run.

**Procedure**

1. Before releasing `rst_i`, drive `almost_empty_th_i` = 32 and `almost_empty_clr_th_i` = 96 and hold both constant.
2. Reset, release, then write 128 words of `PAT-INCR`, recording the occupancy at which `almost_empty_o` clears.
3. Read back down to occupancy 32, then write words back one at a time up to occupancy 97, recording `almost_empty_o` at each occupancy.

**Pass Criteria**

- `almost_empty_o` clears only once occupancy rises above 96, the `almost_empty_clr_th_i` value, per 1.5.6 (`dynamic-dual`).
- `almost_empty_o` asserts when occupancy falls to 32, the `almost_empty_th_i` value, per 1.5.6.
- `almost_empty_o` remains asserted at every occupancy from 33 up to 96 — a 64-word hysteresis band set entirely from the ports, per 1.5.6.
- Both thresholds are constant for the whole run — see `SPEC-GAP-04`.

#### TC-FIFODC-050 — Full and empty conservatism across the clock crossing `Sim Only`

Reuse the generated output of `TC-FIFODC-001` — this case shares every generation-time input with it. This is the case that depends on `wr_clk_i` and `rd_clk_i` being genuinely independent.

**Configuration**

- Identical to `TC-FIFODC-001` in all twenty parameters.

**Procedure**

1. Reset, release, then fill the FIFO to 512 words with `rd_en_i` low until `full_o` asserts.
2. Accept exactly one read and count the `wr_clk_i` cycles from the read-side registration until `full_o` deasserts.
3. Drain to empty, then accept exactly one write and count the `rd_clk_i` cycles from the write-side registration until `empty_o` deasserts.
4. Repeat steps 1 to 3 with `wr_clk_i` faster than `rd_clk_i`, and again with `rd_clk_i` faster than `wr_clk_i`.

**Pass Criteria**

- `full_o` deasserts no more than two `wr_clk_i` cycles after the freeing read is registered on the read side, and `empty_o` no more than two `rd_clk_i` cycles after the filling write is registered on the write side, per 1.5.12 (Flag update delay, fabric controller) and 1.5.5.
- Neither flag ever under-reports: `full_o` is never low while 512 words are held, and `empty_o` is never low while no word is held, in either clock-ratio direction, per 1.5.5.
- No accepted write is lost and no word is returned twice in either clock-ratio direction, per 1.5.4 and 1.5.10 (gray-coded pointers with two-flop synchronizers).

#### TC-FIFODC-051 — Data count conservatism on both sides `Sim Only`

Reuse the generated output of `TC-FIFODC-044` — this case shares every generation-time input with it.

**Configuration**

- Identical to `TC-FIFODC-044` in all twenty parameters.

**Procedure**

1. Reset, release, then run continuous concurrent traffic: write `PAT-INCR` whenever `full_o` is low and read whenever `empty_o` is low, for at least 4096 accepted writes.
2. Sample `wr_data_cnt_o` on every `wr_clk_i` edge and `rd_data_cnt_o` on every `rd_clk_i` edge, comparing each against the true number of words held.
3. Stop all traffic, allow at least four cycles of settling in each domain, and sample both counters.

**Pass Criteria**

- At every sample `wr_data_cnt_o` is at most the true occupancy, and `rd_data_cnt_o` is at most the true occupancy — each counter is computed from a synchronized pointer and so lags reality by the synchronizer depth in its own domain, never over-reporting, per 1.5.7 and spec 1.3.
- Once traffic stops and both domains settle, both counters agree with the true occupancy, per 1.5.7.
- Every word read back matches the written sequence in order throughout the concurrent run, per 1.5.4.

#### TC-FIFODC-052 — Error-detect outputs declared and unconnected `Radiant Compilation`

Inspect the generated wrappers already produced by `TC-FIFODC-001` (fabric controller, `EBR` storage) and `TC-FIFODC-010` (hardened controller), the two controller paths of spec 1.5.2. Error correction is fixed off in every configuration because no `setting` declares `ECC_ENABLE` (spec 1.5.13), so there is nothing to sweep and nothing to simulate.

**Configuration**

- The configurations of `TC-FIFODC-001` and `TC-FIFODC-010`, unchanged.

**Procedure**

1. Inspect each generated wrapper's module header for the `one_err_det_o` and `two_err_det_o` declarations.
2. Inspect each generated instance for the connection state of those two ports.
3. Confirm that the configuration GUI offers no setting for `ECC_ENABLE`, `INIT_FILE`, `INIT_MODE` or `INIT_FILE_FORMAT`.

**Pass Criteria**

- Both wrappers declare `one_err_det_o` and `two_err_det_o`, each 1 bit wide, in the `rd_clk_i` domain, per spec 1.3.
- Both ports are unconditionally dangling in both configurations — not connected after generation, though the module boundary still declares them, per spec 1.3 and 1.5.13.
- The GUI exposes no setting for `ECC_ENABLE`, so error correction stays at its RTL default of 0, per 1.5.13; nor for `INIT_FILE`, `INIT_MODE` or `INIT_FILE_FORMAT`, so the memory elaborates uninitialized, per 1.5.13.
- No pass criterion asserts a value or a behaviour on either output: with error correction fixed off there is no reachable path that drives them at the boundary, per 1.5.13 — see the Exclusions entry for unreachable RTL paths.

### G24 · DRC and Radiant Compilation Checks

Every configuration in this plan is legal, so the spec 1.7 rules are exercised implicitly: each rule is satisfied by construction in the cases named, and a rule that stopped holding would surface as a generation or build failure in those cases. No rule is tested destructively.

1. **DRC-1** (Rule 1) — total memory size within the family budget. Every card's capacity is at or below the `LIFCL` limit of 1,548,288 bits; `TC-FIFODC-040` sits nearest the ceiling at 1,474,560 bits.
2. **DRC-2** (Rules 2, 10) — address depth range. `TC-FIFODC-002` and `TC-FIFODC-039` at the lower bound of 2, `TC-FIFODC-003` and `TC-FIFODC-007` at the upper bound of 65536, `TC-FIFODC-014` at the reduced bound of 16383.
3. **DRC-3** (Rules 3, 11) — data width range. `TC-FIFODC-004` and `TC-FIFODC-008` at 1, `TC-FIFODC-005` and `TC-FIFODC-009` at 256.
4. **DRC-4** (Rule 4) — write-to-read width ratio a power of two. `TC-FIFODC-007`, `TC-FIFODC-008`, `TC-FIFODC-035`.
5. **DRC-5** (Rule 5) — read-to-write width ratio a power of two. `TC-FIFODC-006`, `TC-FIFODC-009`, `TC-FIFODC-036`.
6. **DRC-6** (Rule 6) — write and read capacities equal. Every card; the mixed-width cards `TC-FIFODC-006` through `TC-FIFODC-009`, `TC-FIFODC-035` and `TC-FIFODC-036` are where it constrains the choice.
7. **DRC-7** (Rule 7) — fabric controller requires a power-of-two depth. Every `FABRIC` card; `TC-FIFODC-011` shows the hardened controller exempt at a depth of 1000 and `TC-FIFODC-014` at 16383.
8. **DRC-8** (Rule 8) — maximum width factor of 32 on `LIFCL`. `TC-FIFODC-006` through `TC-FIFODC-009`, `TC-FIFODC-035` and `TC-FIFODC-036` all sit exactly at the limit.
9. **DRC-9** (Rule 9) — the address-width derivation rejects a depth of 1 or less. Not reachable in this plan because Rule 10 holds the minimum at 2; `TC-FIFODC-002` and `TC-FIFODC-039` sit at that boundary.
10. **DRC-10** (Rule 12) — `LUT` storage requires matched geometry. `TC-FIFODC-015` and `TC-FIFODC-038` both use equal depths and equal widths.
11. **DRC-11** (Rule 13) — almost-full level cross-check. `TC-FIFODC-019` through `TC-FIFODC-024`; `TC-FIFODC-018` is the disabled-flag case that passes unconditionally, `TC-FIFODC-002` the depth-2 case that does the same.
12. **DRC-12** (Rule 14) — almost-empty level cross-check. `TC-FIFODC-026` through `TC-FIFODC-032`; `TC-FIFODC-025` and `TC-FIFODC-006` pass unconditionally.
13. **DRC-13** (Rules 15, 16) — almost-full level `value_range` bounds. `TC-FIFODC-022` at the assert lower bound, `TC-FIFODC-001` at the assert upper bound, `TC-FIFODC-024` at the deassert lower bound, `TC-FIFODC-023` at the median of both.
14. **DRC-14** (Rules 17, 18) — almost-empty level `value_range` bounds. `TC-FIFODC-001` at the assert lower bound, `TC-FIFODC-030` at the assert upper bound, `TC-FIFODC-032` at the deassert upper bound, `TC-FIFODC-029` and `TC-FIFODC-031` at the medians.
15. **DRC-15** (Rule 19) — assert levels editable only in static modes. `TC-FIFODC-020`, `TC-FIFODC-021`, `TC-FIFODC-027`, `TC-FIFODC-028`, `TC-FIFODC-035` and `TC-FIFODC-040` all leave them read-only; `TC-FIFODC-018` and `TC-FIFODC-025` do the same through the disabled flag.
16. **DRC-16** (Rule 20) — deassert levels editable only in `static-dual`. `TC-FIFODC-010`, `TC-FIFODC-019`, `TC-FIFODC-022`, `TC-FIFODC-026`, `TC-FIFODC-030` and every dynamic-mode card leave them read-only.
17. **DRC-17** (Rule 21) — controller choice is device-gated. Every card: on a `LIFCL` device the field is visible and editable, so both `FABRIC` and `HARD_IP` are offered. The LAV-AT-E30B and LAV-AT-E70B withdrawal is out of scope — see Exclusions.
18. **DRC-18** (Rule 22) — high-speed option is family- and controller-gated. `TC-FIFODC-014` and `TC-FIFODC-037` set it with `HARD_IP`; `TC-FIFODC-001` and every other `FABRIC` card find it read-only.
19. **DRC-19** (Rule 23) — storage choice requires the fabric controller. `TC-FIFODC-015` and `TC-FIFODC-038` edit it under `FABRIC`; `TC-FIFODC-010`, `TC-FIFODC-011`, `TC-FIFODC-014`, `TC-FIFODC-037` and `TC-FIFODC-039` find it read-only under `HARD_IP`.
20. **DRC-20** (Rule 24) — data counts require the fabric controller. `TC-FIFODC-033`, `TC-FIFODC-034`, `TC-FIFODC-035`, `TC-FIFODC-036`, `TC-FIFODC-038`, `TC-FIFODC-040`, `TC-FIFODC-043` and `TC-FIFODC-044` edit them under `FABRIC`; the five `HARD_IP` cards find them read-only.
21. **DRC-21** (Rule 25) — assertion mode forced to `static-single` with the hardened controller. `TC-FIFODC-010`, `TC-FIFODC-011`, `TC-FIFODC-014`, `TC-FIFODC-037`, `TC-FIFODC-039`.
22. **DRC-22** (Rule 26) — level values collapse to 1 at a governing depth of 2. `TC-FIFODC-002` on both sides, `TC-FIFODC-006` on the read side, `TC-FIFODC-039` on both.
23. **DRC-23** (Rule 27) — address widths derived from the depths. Every card asserts the resulting threshold-port and data-count widths; the extremes are `TC-FIFODC-002` at 1 bit and `TC-FIFODC-003` at 16 bits.
24. **DRC-24** (Rule 28) — family normalization. Every card runs on a `LIFCL` device, so `T_FAMILY` is `LIFCL` and the `LIFCL` depth limit, memory budget and width factor apply throughout.
25. **DRC-25** (Rule 29) — read-only capacity readout. `TC-FIFODC-040` reads it at 1,474,560 bits and `TC-FIFODC-053` at the default 18,432 bits.
26. **DRC-26** (Rule 30) — output register implementation fixed to `LUT`. Every card with `REGMODE` = `reg`; the optional output register is always built in fabric, per 1.5.13.

#### TC-FIFODC-053 — Default-parameter compilation smoke test `Radiant Compilation`

The full implementation flow on the spec 1.4 default configuration, taken further than the synthesis-and-map build every other card runs.

**Configuration**

- The twenty defaults of spec 1.4, exactly as `TC-FIFODC-001`: `WADDR_DEPTH`=512, `WDATA_WIDTH`=36, `RADDR_DEPTH`=512, `RDATA_WIDTH`=36, `FIFO_CONTROLLER`=`FABRIC`, `FWFT`=0, `FORCE_FAST_CONTROLLER`=0, `IMPLEMENTATION`=`EBR`, `REGMODE`=`reg`, `RESETMODE`=`async`, `ENABLE_ALMOST_FULL_FLAG`=`TRUE`, `ALMOST_FULL_ASSERTION`=`static-dual`, `ALMOST_FULL_ASSERT_LVL`=511, `ALMOST_FULL_DEASSERT_LVL`=510, `ENABLE_ALMOST_EMPTY_FLAG`=`TRUE`, `ALMOST_EMPTY_ASSERTION`=`static-dual`, `ALMOST_EMPTY_ASSERT_LVL`=1, `ALMOST_EMPTY_DEASSERT_LVL`=2, `ENABLE_DATA_COUNT_WR`=`FALSE`, `ENABLE_DATA_COUNT_RD`=`FALSE`.
- The GUI-presented default on an eligible `LIFCL` device differs in `FIFO_CONTROLLER` (`HARD_IP`) and, consequently, in both assertion modes; that variant is built by `TC-FIFODC-010`. See `SPEC-GAP-01`.

**Procedure**

1. On a clean install of Radiant 3.2 or later, create a new project targeting a `LIFCL` device.
2. Open the FIFO_DC IP in the configuration GUI and note the read-only capacity readout.
3. Set the twenty parameters to the spec 1.4 defaults listed above and generate.
4. Instantiate the generated wrapper as the top level and run the full flow: synthesis, map, place & route, and bitstream generation.

**Pass Criteria**

- The IP is offered by a Radiant 3.2 installation and generates with no error, consistent with the declared minimum version and the absence of a declared maximum (spec 1.1, header).
- No DRC message is raised on the default configuration; no rule of spec 1.7 is violated.
- The read-only capacity readout shows 18,432 bits, being `WADDR_DEPTH` x `WDATA_WIDTH` (Rule 29).
- Synthesis, map, place & route and bitstream generation all complete with no errors.
- The generated package contains the evaluation physical constraints emitted by `create_constraint_pdc` and the premap timing statements delivered as `constraint.sdc` for both supported synthesis flows, per 1.5.11.
- No criterion checks the assumed clock period in the generated constraints: `constraint.ldc` and `create_constraint.py` disagree for a `LIFCL` target other than `LFCPNX` (spec Appendix A) — see `SPEC-GAP-08`.
- No criterion checks where the capacity readout appears in the generated output — see `SPEC-GAP-09`.

## Exclusions and Rationale

| Excluded | Rationale |
|---|---|
| Performance and timing verification | Functional plan; fmax, setup/hold, and clock-frequency characterization are out of scope. The assumed clock periods in `constraint.ldc`, `constraint.sdc` and `create_constraint.py` (spec 1.5.12, Constraints the IP applies) are not verified here. |
| Non-target device families | `LN2-CT`, `LN2-MH`, `LKH-CT`, `LKH-MH`, `LATG1`, `LAV-AT`, `kr6a00` and `iCE40UP` (spec 1.2). Their distinct internal behaviours are out of scope: the Avant-class hardened FIFO primitive on `LATG1`, `LAV-AT` and `kr6a00` (spec 1.5.2); register-based `LUT` storage on `iCE40UP`, `LKH-CT` and `LKH-MH` (spec 1.5.3); the width factors of 64 for `LATG1`/`LAV-AT` and 8 for `iCE40UP`, and the `iCE40UP` memory budget of 122,880 bits (spec 1.7, Per-family limits); the withdrawal of `HARD_IP` on LAV-AT-E30B and LAV-AT-E70B (Rule 21); and the fabric-only GUI on `LN2-CT`/`LN2-MH` arising from the plugin-versus-RTL normalization divergence (spec 1.2, Appendix A). The `LFCPNX` memory budget of 3,760,128 bits is likewise not exercised — see `SPEC-GAP-08`. |
| Hidden, read-only, and derived parameters | `WADDR_WIDTH` and `RADDR_WIDTH` — hidden and derived as `clog2` of their depths (Rule 27); `OREG_IMPLEMENTATION` — unconditionally hidden and fixed at `LUT` (Rule 30); `FAMILY` and `T_FAMILY` — hidden and computed from the target device (Rule 28); `Total Memory bits` — display-only, computed (Rule 29); `CHECK_ASSERT_DEASSERT_FULL_LVL` and `CHECK_ASSERT_DEASSERT_EMPTY_LVL` — display-only carriers for the level cross-checks (Rules 13, 14). The parameters with no `setting` at all — `INIT_FILE`, `INIT_MODE`, `INIT_FILE_FORMAT` and `ECC_ENABLE` — are likewise not configurable (spec 1.4, 1.5.13). |
| Unreachable GUI options | With `FIFO_CONTROLLER` = `HARD_IP`: `static-dual`, `dynamic-single` and `dynamic-dual` on either assertion type, which the `value_expr` overrides to `static-single` (Rule 25); `IMPLEMENTATION` = `LUT`, not editable (Rule 23); `ENABLE_DATA_COUNT_WR` and `ENABLE_DATA_COUNT_RD` = `TRUE`, not editable (Rule 24). With `FIFO_CONTROLLER` = `FABRIC`: `FORCE_FAST_CONTROLLER` = 1, not editable (Rule 22). In every configuration: `OREG_IMPLEMENTATION` = `EBR`, unreachable because the setting is hidden and fixed to `LUT` (Rule 30, spec 1.5.13). |
| DRC-negative testing | Legal configurations only; illegal-input error messaging is not verified here. The thirty rules of spec 1.7 are exercised implicitly as `DRC-1` to `DRC-26` in G24. |
| Unreachable RTL paths | The error-correction datapath and the functional behaviour of `one_err_det_o` and `two_err_det_o` — `ECC_ENABLE` has no `setting`, so it is fixed at 0 and both outputs are unconditionally dangling (spec 1.5.13); the memory-initialization path — `INIT_FILE`, `INIT_MODE` and `INIT_FILE_FORMAT` have no `setting`, so the memory always elaborates uninitialized (spec 1.5.13); the memory-block-internal output register, unreachable because `OREG_IMPLEMENTATION` is fixed to `LUT` (Rule 30, spec 1.5.13); the Avant-class hardened primitive and register-based `LUT` storage, both reachable only on non-target families (spec 1.5.2, 1.5.3); and non-power-of-two depths on the fabric controller, which Rule 7 forbids. |

## Spec Issues and Assumptions

| ID | Missing or Ambiguous | Assumption Used | Impact | Who Should Confirm |
|---|---|---|---|---|
| `SPEC-GAP-01` | The `FIFO_CONTROLLER` default is contradictory: spec 1.4 and Appendix A record the RTL declaration as `FABRIC` while the metadata `default` and `value_expr` both evaluate to `HARD_IP` on an eligible `LIFCL` device. The spec does not say which a tester will actually see when opening the GUI on an untouched project. | The plan follows the spec's stated RTL-wins convention: `TC-FIFODC-001` and `TC-FIFODC-053` use `FABRIC` as the default, and the GUI-presented `HARD_IP` variant is built as a first-class case in `TC-FIFODC-010`, so both are covered whichever way the conflict is resolved. | `TC-FIFODC-001`, `TC-FIFODC-010`, `TC-FIFODC-053` | IP owner / metadata owner |
| `SPEC-GAP-02` | The boundary value of a disabled almost-flag output is not established. Spec 1.3 says `almost_full_o` and `almost_empty_o` are "driven to 0 by the fabric controller and left dangling at the boundary" when their enable is `FALSE`, while 1.5.6 says the output is driven to 0 rather than left floating. The two statements do not settle what the top-level port reads. The same ambiguity applies to a disabled data-count output. | No pass criterion asserts a value on `almost_full_o` or `almost_empty_o` when the corresponding enable is `FALSE`; the cards check only that the port is still declared and that the data path is undisturbed. | `TC-FIFODC-018`, `TC-FIFODC-025`, `TC-FIFODC-038` | IP owner |
| `SPEC-GAP-03` | The behaviour of `wr_data_cnt_o` and `rd_data_cnt_o` with the hardened controller, and when a counter is disabled, is stated two ways: spec 1.3 says they are driven to 0 when the counter is disabled and left undriven by the hardened controller, while 1.5.7 says they must be left unused in that configuration. | No pass criterion asserts a value on either count output in a `HARD_IP` configuration, nor on a count output whose enable is `FALSE`. | `TC-FIFODC-010`, `TC-FIFODC-011`, `TC-FIFODC-014`, `TC-FIFODC-033`, `TC-FIFODC-034`, `TC-FIFODC-037`, `TC-FIFODC-039` | IP owner |
| `SPEC-GAP-04` | Runtime reprogramming of the dynamic threshold ports is not specified. Spec 1.5.6 names `almost_full_th_i`, `almost_full_clr_th_i`, `almost_empty_th_i` and `almost_empty_clr_th_i` as the threshold source in the dynamic modes but does not say whether a threshold may change during operation, nor with what latency a change takes effect. | Every dynamic-threshold case drives each threshold to a constant before reset release and holds it for the whole run. Mid-operation threshold changes are not exercised. | `TC-FIFODC-020`, `TC-FIFODC-021`, `TC-FIFODC-027`, `TC-FIFODC-028`, `TC-FIFODC-035`, `TC-FIFODC-040`, `TC-FIFODC-046` through `TC-FIFODC-049` | IP owner / QA |
| `SPEC-GAP-05` | The hardened-controller flag latency is only partly quantified. Spec 1.5.12 gives two destination cycles for the fabric controller, and for the hardened controller "one register in the consuming domain, or two on the empty and almost-empty flags when `REGMODE` is `reg`" — leaving `full_o` and `almost_full_o` deassertion on that path without a number. | `HARD_IP` cards state a cycle bound only where 1.5.12 gives one (the empty and almost-empty stages). For `full_o` and `almost_full_o` on that path the criterion is limited to eventual correctness and never-under-reporting. | `TC-FIFODC-010`, `TC-FIFODC-011`, `TC-FIFODC-014`, `TC-FIFODC-037`, `TC-FIFODC-039` | IP owner |
| `SPEC-GAP-06` | Resource consumption is not specified. The spec states that the hardened path replicates and cascades primitives to meet a requested capacity (1.5.2) and that block RAM storage goes through the shared memory block (1.5.3), but gives no rule for how many memory blocks or primitives a given depth and width consume, nor when a configuration tiles. | No pass criterion asserts a memory-block count, a primitive count, or a tiling arrangement. Large and near-ceiling configurations are checked for functional correctness and successful build only. | `TC-FIFODC-003`, `TC-FIFODC-005`, `TC-FIFODC-011`, `TC-FIFODC-040` | IP owner / QA |
| `SPEC-GAP-07` | The value a read-only level field carries is not stated. Rules 19 and 20 make the assert and deassert level settings read-only outside the applicable static modes, but the spec does not say whether the field then holds its `default`, the `getLoop` result, or something else — nor what value is passed to the RTL parameter. | Coverage-matrix cells show `—` for a level parameter that is not editable, and no pass criterion depends on the value such a field carries. | `TC-FIFODC-010`, `TC-FIFODC-011`, `TC-FIFODC-014`, `TC-FIFODC-018` through `TC-FIFODC-022`, `TC-FIFODC-025` through `TC-FIFODC-028`, `TC-FIFODC-030`, `TC-FIFODC-035`, `TC-FIFODC-037` through `TC-FIFODC-040` | Metadata owner |
| `SPEC-GAP-08` | Two target-dependent quantities are stated inconsistently for `LIFCL`. First, the memory budget: 1,548,288 bits for `LIFCL` generally but 3,760,128 for `LFCPNX` (spec 1.7, Per-family limits), with no statement of which applies to a plan written for the family as a whole. Second, the assumed clock period: `constraint.ldc` uses 8 ns for the LIFCL-class families while `create_constraint.py` uses 10 ns for any LIFCL target other than `LFCPNX` (spec Appendix A, unresolved). | Every configuration is sized against the smaller budget of 1,548,288 bits, so all cases stay legal on any `LIFCL`-normalized device including the narrowest. No criterion checks the assumed clock period in the generated constraints. | `TC-FIFODC-005`, `TC-FIFODC-040`, `TC-FIFODC-053` | IP owner / metadata owner |
| `SPEC-GAP-09` | The display-only settings are described but not located. Spec 1.6 records `Total Memory bits`, `CHECK_ASSERT_DEASSERT_FULL_LVL` and `CHECK_ASSERT_DEASSERT_EMPTY_LVL` as GUI-only inputs, and Rule 29 gives the capacity formula, but the spec does not say whether any of them appears in the generated output. | Their values are checked in the configuration GUI only; no criterion looks for them in the generated package. | `TC-FIFODC-040`, `TC-FIFODC-053` | Metadata owner |
