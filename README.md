# fip-testgen

## Quick Start

```bash
make tc-01-01          # run one specific test case
make tg-01             # run all test cases in a group
make tg-10             # run DRC tests (pytest, no simulator)
make all_configs       # run every simulation configuration
make drc               # same as make tg-10
```

Each `tc-XX-YY` target runs only that one CoCoTB function in its own
`sim_build/tc-XX-YY/` directory and writes a log to `results/tc-XX-YY.log`.
Each `tg-XX` target runs its test cases in sequence and prints a pass/fail
summary at the end.

The dispatch is handled by `scripts/run_tc.py`, which sets all simulator
parameters (`REGMODE`, `RDATA_WIDTH`, `RADDR_DEPTH`, etc.) for each TC
automatically — no need to look up Makefile config names.

---

## TG-01 — Basic Read Functionality

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-01-01 | Sequential read, noreg | `make tc-01-01` |
| TC-01-02 | Sequential read, reg | `make tc-01-02` |
| TC-01-03 | Full sweep, noreg | `make tc-01-03` |
| TC-01-04 | Full sweep, reg | `make tc-01-04` |
| TC-01-05 | Boundary addresses | `make tc-01-05` |
| TC-01-06 | Random addresses | `make tc-01-06` |
| TC-01-07 | Repeated address | `make tc-01-07` |

Run all: `make tg-01`

---

## TG-02 — Read Enable (`rd_en_i`)

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-02-01 | `rd_en_i`=0 at start | `make tc-02-01` |
| TC-02-02 | `rd_en_i` de-asserted mid-seq | `make tc-02-02` |
| TC-02-03 | `rd_en_i` toggle every cycle | `make tc-02-03` |
| TC-02-04 | `rd_en_i`=1 resumes | `make tc-02-04` |

Run all: `make tg-02`

---

## TG-03 — Read Clock Enable (`rd_clk_en_i`)

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-03-01 | `rd_clk_en_i`=0 holds output, noreg | `make tc-03-01` |
| TC-03-02 | `rd_clk_en_i`=0 holds output, reg | `make tc-03-02` |
| TC-03-03 | `rd_clk_en_i` re-assertion | `make tc-03-03` |
| TC-03-04 | `rd_clk_en_i` toggle pattern | `make tc-03-04` |
| TC-03-05 | Cascaded config + `rd_clk_en_i` | `make tc-03-05` |

Run all: `make tg-03`

---

## TG-04 — Output Clock Enable (`rd_out_clk_en_i`)

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-04-01 | `rd_out_clk_en_i`=0 freezes output | `make tc-04-01` |
| TC-04-02 | `rd_out_clk_en_i`=1 normal | `make tc-04-02` |
| TC-04-03 | `rd_out_clk_en_i` toggle mid-seq | `make tc-04-03` |
| TC-04-04 | `OUTPUT_CLK_EN`=0 — no effect | `make tc-04-04` |
| TC-04-05 | Both enables de-asserted | `make tc-04-05` |

Run all: `make tg-04`

---

## TG-05 — Reset Behavior

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-05-01 | Sync reset clears output | `make tc-05-01` |
| TC-05-02 | Sync reset during read | `make tc-05-02` |
| TC-05-03 | Sync reset release | `make tc-05-03` |
| TC-05-04 | Async reset asserted | `make tc-05-04` |
| TC-05-05 | Async reset sync release | `make tc-05-05` |
| TC-05-06 | noreg — `rst_i` has no effect | `make tc-05-06` |

Run all: `make tg-05`

---

## TG-06 — Memory Initialization

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-06-01 | `all_zero` init | `make tc-06-01` |
| TC-06-02 | `all_one` init | `make tc-06-02` |
| TC-06-03 | `mem_file` hex | `make tc-06-03` |
| TC-06-04 | `mem_file` binary | `make tc-06-04` |
| TC-06-05 | `mem_file` alternating pattern | `make tc-06-05` |
| TC-06-06 | `mem_file` addr-as-data | `make tc-06-06` |
| TC-06-07 | `all_zero`, narrow width | `make tc-06-07` |
| TC-06-08 | `mem_file` binary narrow | `make tc-06-08` |

Run all: `make tg-06`

---

## TG-07 — LIFCL EBR Tile Configuration Coverage

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-07-01 | Minimum config (1 b × 2) | `make tc-07-01` |
| TC-07-02 | 1-bit × 16 384 (max depth) | `make tc-07-02` |
| TC-07-03 | 2-bit × 8 192 | `make tc-07-03` |
| TC-07-04 | 4-bit × 4 096 | `make tc-07-04` |
| TC-07-05 | 9-bit × 2 048 (parity) | `make tc-07-05` |
| TC-07-06 | 18-bit × 1 024 (parity) | `make tc-07-06` |
| TC-07-07 | 36-bit × 512 (default) | `make tc-07-07` |
| TC-07-08 | Non-aligned width (12-bit) | `make tc-07-08` |

Run all: `make tg-07`

---

## TG-08 — EBR Cascading

| TC | Test Case Name | `make` Target |
|---|---|---|
| TC-08-01 | Addr cascade ×2 | `make tc-08-01` |
| TC-08-02 | Addr cascade ×4 | `make tc-08-02` |
| TC-08-03 | Data cascade ×2 (72-bit) | `make tc-08-03` |
| TC-08-04 | Data cascade ×4 (144-bit) | `make tc-08-04` |
| TC-08-05 | Both cascades (72-bit × 1 024) | `make tc-08-05` |
| TC-08-06 | Bank boundary read | `make tc-08-06` |
| TC-08-07 | Addr cascade + `rd_clk_en_i` toggle | `make tc-08-07` |
| TC-08-08 | Addr cascade + reg mode | `make tc-08-08` |

Run all: `make tg-08`

---

## TG-09 — ECC

| TC | Test Case Name | `make` Target | Notes |
|---|---|---|---|
| TC-09-01 | ECC disabled — outputs = 0 | `make tc-09-01` | |
| TC-09-02 | ECC enabled, clean data | `make tc-09-02` | |
| TC-09-03 | ECC, minimum width (32 b) | `make tc-09-03` | |
| TC-09-04 | ECC, maximum width (64 b) | `make tc-09-04` | |
| TC-09-05 | SEC — single-bit error | `make tc-09-05` | Always skipped; needs `ECC_ERROR_INJECT=1` + corrupted fixture |
| TC-09-06 | DED — double-bit error | `make tc-09-06` | Always skipped; needs `ECC_ERROR_INJECT=1` + corrupted fixture |
| TC-09-07 | ECC error recovery | `make tc-09-07` | Always skipped; needs `ECC_ERROR_INJECT=1` + corrupted fixture |

Run all: `make tg-09`

---

## TG-10 — DRC and Parameter Validation

All nine DRC tests run via pytest — no simulator required.

```bash
make tg-10    # or: make drc
```

| TC | Test Case Name |
|---|---|
| TC-10-01 | Depth below minimum (`RADDR_DEPTH`=1) |
| TC-10-02 | Depth above maximum (`RADDR_DEPTH`=65537) |
| TC-10-03 | Width below minimum (`RDATA_WIDTH`=0) |
| TC-10-04 | Width above maximum (`RDATA_WIDTH`=513) |
| TC-10-05 | Total bits exceed LIFCL limit (512 × 4096) |
| TC-10-06 | `OUTPUT_CLK_EN`=1 with `REGMODE`=noreg |
| TC-10-07 | `RESETMODE`=async with `REGMODE`=noreg |
| TC-10-08 | ECC with unsupported width (`RDATA_WIDTH`=65) |
| TC-10-09 | `INIT_MODE`=mem_file with no file path |

---

## Legacy: running by configuration name

The `make all_configs` target still exists and runs every configuration in
bulk. It is useful for a full regression but gives no control over which
test cases execute within each configuration.

For targeted runs, prefer `make tc-XX-YY` / `make tg-XX` instead.

The mapping between TC IDs and the underlying simulator parameters is
maintained in `scripts/run_tc.py`.
