# PLL FIP — Test Plan

*`lscc_pll` v1.9.1 · LIFCL*

| Field | Value |
|---|---|
| IP name | PLL |
| VLNV | `latticesemi.com:module:pll:1.9.1` |
| Module | `lscc_pll` |
| Version | 1.9.1 |
| Target Family | `LIFCL` |
| Families normalizing to target | `LFD2NX`, `LFCPNX`, `jd5d00`, `LFMXO5`, `UT24C`, `UT24CP` — spec 1.2 records that the plugin performs **no** family normalization and holds no family lookup table, so all seven declared families share one implementation path. The only device-dependent branch is a test on the device *name*, not the family. Test cases are written for `LIFCL` (device `LIFCL-40`). |
| Tool | Radiant ≥ 2025.1 |
| Source specification | `PLL_FIP_Functional_Spec.md`, 2026-08-20 (Draft — reverse-engineered from implementation source) |
| Date | 2026-09-03 |

## 1. Scope & Objectives

- **Functional verification only** for PLL (`lscc_pll`) targeting the `LIFCL` device family. Performance and timing characterisation — VCO jitter, phase noise, lock time, output duty accuracy, fmax and setup/hold — are out of scope; those are owned by the Hardware team. Absolute lock, enable-response and power-down response figures are in any case marked `[UNRESOLVED]` by the specification because the hard PLL block is outside the IP tree (spec 1.5.13).
- **Parameters and ports are taken from the top-level RTL module declaration** in `rtl/lscc_pll.v` (spec 1.3, 1.4). Spec 1.4 records that **this IP has no user-configurable RTL top-module parameters**: all 95 module parameters are either auto-calculated and unconditionally hidden or have no matching setting. The user-configurable surface is therefore the set of `type="input"` and `type="command"` settings in spec 1.6, and those are what this plan sweeps. Because spec 1.4 is empty by design, the per-parameter test groups below follow **spec 1.6 group order** (General, Reference Clock, Feedback, Spread Spectrum, Primary Clock Output, Secondary Clock Outputs, then the Optional Ports page) in place of a 1.4 order that does not exist.
- **Internal-only parameters are not directly tested.** These are the 94 auto-calculated `type="param"` settings, each carrying `editable="False"` and `hidden="True"` — for example `CLKI_FREQ`, `FVCO`, `FVCO_STR`, `CLKI_DIVIDER_ACTUAL_STR`, `FBCLK_DIVIDER_ACTUAL_STR`, `DIVOP_ACTUAL_STR` … `DIVOS5_ACTUAL_STR`, `SSC_N_CODE_STR`, `SSC_F_CODE_STR`, `SSC_TBASE_STR`, `SSC_STEP_IN_STR`, `SSC_REG_WEIGHTING_SEL_STR`, `SSC_PROFILE`, `CLKOP_TRIM`, `CLKOS_TRIM`, `DELA`–`DELF`, `PHIA`–`PHIF`, `REF_COUNTS`, `REF_OSC_CTRL`, `PMU_WAITFORLOCK`, `INTFBKDEL_SEL`, `FBK_MODE`, `FRAC_N_EN`, `SS_EN`, `IO_TYPE`, `LMMI_EN`, `APB_EN`, `APB_SOFT_REG_EN`, `DYN_PORTS_EN`, `PLL_RST`, `LOCK_EN`, `PLL_LOCK_STICKY`, `LEGACY_EN`, `POWERDOWN_EN`, `EN_REFCLK_MON`, `PLL_REFCLK_FROM_PIN`, `ENCLKOP_EN` … `ENCLKOS5_EN`, `CLKOP_BYPASS` … `CLKOS5_BYPASS`, `CLKOP_EN` … `CLKOS5_EN` — plus `SIM_FLOAT_PRECISION`, which has no matching setting at all (spec 1.4), and the hidden `IS_JP_DEVICE` Verilog macro. They are *observed* as evidence in Pass Criteria — the generated parameter list is the visible result of the plugin derivation described in spec 1.5.9 — but no test enters a value for one.
- **Display-only and permanently read-only GUI fields are not directly tested** either: `gui_optim_prio`, `gui_en_pmu_wait_lock`, `gui_vco_freq`, `gui_m_div_disp`, `gui_phasedet_freq`, `gui_fbk_mode_disp`, `gui_n_div_disp`, `gui_frac_n_div_disp`, `fbclk_divider_decimal_disp`, `gui_clk_*_freq_disp`, `gui_clk_*_div_disp`, `gui_clk_*_ppm`, and the four never-displayed calculation hooks `set_attributes`, `gui_clkout`, `print_attributes` and `gui_sim_type` (spec 1.6 preamble). Several of them are read as evidence in Pass Criteria; none is set by a test.
- **Only legal parameter combinations** permitted by the GUI dependency rules (spec 1.6, 1.7) are used. Every configuration in this plan was checked field by field against the Visible When / Editable When conditions of spec 1.6 and against all 28 rules of spec 1.7 simultaneously. Where a rule silently *corrects* a field rather than rejecting it (Rules 13, 14, 27), the corrected value is the one recorded in the Coverage Matrix, and the field is shown as `—` because the user cannot set it in that configuration.
- **The `Calculate` command (`RUN_CALC`) is exercised, not swept.** It is a `type="command"` setting, not a value (spec 1.6 General). Every frequency-mode test runs it as a procedure step, because in frequency mode the divider and analog search is what produces the parameter list under test (spec 1.5.9); divider-mode tests run it as well so the analog optimizer executes.
- **Transient-behavior rule.** Any case checking the transient behavior of a signal — asynchronous assertion edges, glitch behavior, same-cycle enable transitions — is `Radiant Compilation` and is never simulated. Concretely: `rstn_i`, `pllpd_en_n_i`, `legacy_i`, `refdetreset` and the six `enclko*_i` inputs all reach the hard block with no synchronizer and no release sequencing (spec 1.5.8, 1.5.13), so the simulated cases in `G28` check only *steady-state* outcomes either side of a transition — never the edge itself, and never a cycle count on any of those paths.

Type legend (use these three labels verbatim on every test case):

- **Radiant Compilation** — Radiant project build only; no simulation waveform required.
- **Sim Only** — functional simulation only; no Radiant synthesis required.
- **Both** — Radiant compilation and functional simulation.

## 2. Coverage Summary

| Total TCs | Radiant Compilation | Sim Only | Both |
|---|---|---|---|
| 81 | 45 | 5 | 31 |

**Parameters covered** (all values are GUI field values per spec 1.6; numeric fields list min / median / max):

| Field | Values tested |
|---|---|
| `gui_config_mode` | `FREQUENCY`, `DIVIDER` |
| `gui_en_frac_n` | `False`, `True` |
| `gui_en_ssc` | `False`, `True` |
| `gui_en_usr_fbk` | `False`, `True` |
| `gui_en_int_fbkdel_sel` | `False`, `True` |
| `gui_refclk_freq` | 18.0 / 400.0 / 800.0 MHz (plus the 100.0 MHz default and 200.0, 440.0 as carriers) |
| `gui_m_div` | 1 / 22 / 44 |
| `gui_en_refclk_mon` | `False`, `True` |
| `gui_refclk_mon_freq` | `3P2`, `1P0` |
| `gui_fbk_mode` | all 12: `CLKOP`, `CLKOS`, `CLKOS2`, `CLKOS3`, `CLKOS4`, `CLKOS5`, `INTCLKOP`, `INTCLKOS`, `INTCLKOS2`, `INTCLKOS3`, `INTCLKOS4`, `INTCLKOS5` |
| `gui_n_div` | integer-N 1 / 22 / 44; fractional-N 16 / 45 / 88 (see `SPEC-GAP-07` on the declared ceiling of 128) |
| `gui_frac_n_div` | 0 / 2048 / 4095 |
| `gui_ssc_profile` | `DOWN`, `CENTER` |
| `gui_ssc_mod_depth` | all 8: 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00 |
| `gui_ssc_mod_freq` | 24.42 / 100.0 / 200.0 kHz |
| `gui_clk_op_byp` … `gui_clk_s5_byp` | `False`, `True` (all six outputs) |
| `gui_clk_os_en` … `gui_clk_s5_en` | `False`, `True` (all five secondary outputs) |
| `gui_clk_op_freq` … `gui_clk_s5_freq` | 6.25 / 100 / 800 MHz (all six outputs) |
| `gui_clk_op_div` … `gui_clk_s5_div` | 1 / 64 / 128 (all six outputs) |
| `gui_clk_op_tol` … `gui_clk_s5_tol` | all 8: 0.0, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0 (all six outputs) |
| `gui_clk_op_phase` … `gui_clk_s5_phase` | all 8: 0, 45, 90, 135, 180, 225, 270, 315 (all six outputs) |
| `gui_clk_op_trim_en`, `gui_clk_os_trim_en` | `False`, `True` |
| `gui_clk_op_trim_mode`, `gui_clk_os_trim_mode` | `Rising`, `Falling` |
| `gui_clk_op_trim_mult`, `gui_clk_os_trim_mult` | all 4: `0`, `1`, `2`, `4` |
| `gui_en_refclk_pin` | `False`, `True` |
| `gui_refclk_io_type` | all 17 distinct: `LVDS`, `SUBLVDS`, `SLVS`, `HSTL15_I`, `HSTL15D_I`, `LVTTL33`, `LVCMOS33`, `LVCMOS25`, `LVCMOS18`, `LVCMOS18H`, `LVCMOS15`, `LVCMOS15H`, `LVCMOS12`, `LVCMOS12H`, `LVCMOS10H`, `LVCMOS10`, `LVCMOS10R` |
| `gui_en_dyn_phase` | `False`, `True` |
| `gui_en_clken_op` … `gui_en_clken_s5` | `False`, `True` (all six) |
| `gui_en_pll_reset` | `True`, `False` |
| `gui_en_pll_lock` | `True`, `False` |
| `gui_pll_lock_sticky` | `False`, `True` |
| `gui_reg_interface` | `None`, `APB`, `LMMI` |
| `gui_en_csr` | `False`, `True` |
| `gui_en_legacy` | `False`, `True` |
| `gui_en_powerdown` | `False`, `True` |

**Ports covered** — all 43 ports of spec 1.3, verbatim RTL names.

*Inputs (29):* `rstn_i` (TC-PLL-056, TC-PLL-070, TC-PLL-072), `clki_i` (every test; frequency and I/O standard swept in TC-PLL-013 – TC-PLL-015, TC-PLL-050, TC-PLL-051), `usr_fbclk_i` (TC-PLL-011, TC-PLL-045 – TC-PLL-047, TC-PLL-054, TC-PLL-068, TC-PLL-076), `phasedir_i` / `phasestep_i` / `phaseloadreg_i` / `phasesel_i` (TC-PLL-052, TC-PLL-053, TC-PLL-068), `enclkop_i` / `enclkos_i` / `enclkos2_i` / `enclkos3_i` / `enclkos4_i` / `enclkos5_i` (TC-PLL-054, TC-PLL-055, TC-PLL-068, TC-PLL-075), `pllpd_en_n_i` (TC-PLL-065, TC-PLL-069, TC-PLL-073), `legacy_i` (TC-PLL-064, TC-PLL-069, TC-PLL-074), `refdetreset` (TC-PLL-019, TC-PLL-020, TC-PLL-066, TC-PLL-071, TC-PLL-077), `lmmi_clk_i` / `lmmi_resetn_i` / `lmmi_request_i` / `lmmi_wr_rdn_i` / `lmmi_offset_i` / `lmmi_wdata_i` (TC-PLL-060, TC-PLL-070, TC-PLL-078), `apb_pclk_i` / `apb_preset_n_i` / `apb_penable_i` / `apb_psel_i` / `apb_pwrite_i` / `apb_paddr_i` / `apb_pwdata_i` (TC-PLL-061 – TC-PLL-063, TC-PLL-066, TC-PLL-079).

*Outputs (14):* `clkop_o` (every test), `clkos_o` / `clkos2_o` / `clkos3_o` / `clkos4_o` / `clkos5_o` (TC-PLL-031, TC-PLL-034, TC-PLL-035, TC-PLL-038 – TC-PLL-047, TC-PLL-053, TC-PLL-054, TC-PLL-067, TC-PLL-068, TC-PLL-080), `lock_o` (TC-PLL-001, TC-PLL-057 – TC-PLL-059, TC-PLL-062, TC-PLL-072, TC-PLL-073, TC-PLL-080), `refdetlos` (TC-PLL-019, TC-PLL-020, TC-PLL-066, TC-PLL-071, TC-PLL-077), `lmmi_ready_o` / `lmmi_rdata_valid_o` / `lmmi_rdata_o` (TC-PLL-060, TC-PLL-078), `apb_pready_o` / `apb_pslverr_o` / `apb_prdata_o` (TC-PLL-061 – TC-PLL-063, TC-PLL-079).

## 3. Coverage Matrix

One row per test case; one column per user-configurable GUI field. Because this IP exposes 60 user-configurable fields, the matrix is split into seven sub-tables by spec 1.6 group — the row set is identical in each, so a reader scans one column at a time and sees every value covered. A cell carries the value that test uses; the value a test specifically sweeps (its subject) is in **bold**; `—` marks a field that is inapplicable or don't-care for that test.

`—` also covers the two cases the GUI creates for itself, both of which mean *the user cannot set this field in this configuration*:

- **Hidden by mode.** In `FREQUENCY` mode the reference, feedback, fractional and output *divider* fields are read-only and replaced by their Actual Value displays; in `DIVIDER` mode the *frequency* and *tolerance* fields are (Rule 15).
- **Forced or locked by another field.** `gui_fbk_mode` reads `—` whenever fractional-N, spread spectrum or the user feedback clock is enabled, because the feedback source is then forced — to `INTCLKOP` for the first two (spec 1.5.4), to `USERFBCLK` for the third (spec 1.6 General) — and the field is not editable. The same applies to the bypass field of an output that is the feedback source or is in a fractional / spread-spectrum configuration (Rules 13, 14), to the phase-shift and clock-enable-port fields of the feedback output (Rule 23), to trim mode and multiplier while trim is off (Rule 24), to every field of a disabled secondary output, to `gui_refclk_io_type` without the pin option (Rule 19), to `gui_en_csr` without the APB slave (Rule 21), to `gui_pll_lock_sticky` without the lock output (Rule 20), and to `gui_en_dyn_phase` when the APB slave carries the soft control register (Rule 22).

Where a cell holds several values separated by ` / `, that test iterates the listed values over an otherwise identical configuration; its card gives one row per iteration with its own expected result.
### Test index

The row set of every matrix below. The parameter sub-tables are keyed by TC ID and Type rather than repeating the name seven times.

| TC ID | Test Name | Type |
|---|---|---|
| TC-PLL-001 | Default-configuration generation, compilation and lock | Both |
| TC-PLL-002 | Frequency mode with an exactly achievable primary output | Both |
| TC-PLL-003 | Divider mode with dividers entered directly | Both |
| TC-PLL-004 | Fractional-N feedback division in frequency mode | Both |
| TC-PLL-005 | Fractional-N feedback division in divider mode | Radiant Compilation |
| TC-PLL-006 | Down-spread profile across modulation depths 0.25 / 0.75 / 1.25 / 1.75 | Radiant Compilation |
| TC-PLL-007 | Centre-spread profile across modulation depths 0.50 / 1.00 / 1.50 / 2.00 | Radiant Compilation |
| TC-PLL-008 | Minimum modulation frequency 24.42 kHz | Radiant Compilation |
| TC-PLL-009 | Median modulation frequency 100 kHz with a modulated output clock | Both |
| TC-PLL-010 | Maximum modulation frequency 200 kHz driving the weighting shift | Radiant Compilation |
| TC-PLL-011 | External feedback clock selected as the loop feedback source | Both |
| TC-PLL-012 | Internal feedback delay path enabled | Radiant Compilation |
| TC-PLL-013 | Minimum reference frequency 18 MHz | Both |
| TC-PLL-014 | Median reference frequency 400 MHz | Radiant Compilation |
| TC-PLL-015 | Maximum reference frequency 800 MHz | Radiant Compilation |
| TC-PLL-016 | Reference divider 1 (minimum) | Radiant Compilation |
| TC-PLL-017 | Reference divider 22 (median) | Radiant Compilation |
| TC-PLL-018 | Reference divider 44 (maximum) | Radiant Compilation |
| TC-PLL-019 | Reference-clock monitor with the 3.2 MHz monitor clock | Both |
| TC-PLL-020 | Reference-clock monitor with the 1.0 MHz monitor clock | Radiant Compilation |
| TC-PLL-021 | Feedback from CLKOP and from INTCLKOP | Both |
| TC-PLL-022 | Feedback from CLKOS / INTCLKOS and CLKOS2 / INTCLKOS2 | Radiant Compilation |
| TC-PLL-023 | Feedback from CLKOS3 / INTCLKOS3, CLKOS4 / INTCLKOS4 and CLKOS5 / INTCLKOS5 | Radiant Compilation |
| TC-PLL-024 | Feedback divider 1 (integer-N minimum) | Radiant Compilation |
| TC-PLL-025 | Feedback divider 22 (integer-N median) | Radiant Compilation |
| TC-PLL-026 | Feedback divider 44 (integer-N reachable maximum) | Both |
| TC-PLL-027 | Fractional-N feedback divider floor 16 and reachable ceiling 88 | Radiant Compilation |
| TC-PLL-028 | Fractional word 0 (minimum) | Radiant Compilation |
| TC-PLL-029 | Fractional word 2048 (median) | Both |
| TC-PLL-030 | Fractional word 4095 (maximum) | Radiant Compilation |
| TC-PLL-031 | All five secondary outputs enabled | Both |
| TC-PLL-032 | Selective enable: CLKOS3 and CLKOS5 only | Radiant Compilation |
| TC-PLL-033 | Primary output bypassed to the reference clock | Both |
| TC-PLL-034 | All five secondary outputs bypassed | Radiant Compilation |
| TC-PLL-035 | Mixed bypass: CLKOS2 and CLKOS4 bypassed, CLKOS3 and CLKOS5 divided | Both |
| TC-PLL-036 | Maximum primary output frequency with minimum secondary frequencies | Radiant Compilation |
| TC-PLL-037 | Minimum primary output frequency with CLKOS at maximum as feedback source | Radiant Compilation |
| TC-PLL-038 | Median output frequency 100 MHz on all six outputs | Both |
| TC-PLL-039 | Maximum output frequency 800 MHz on all six outputs | Radiant Compilation |
| TC-PLL-040 | Primary divider 1 with all secondary dividers 128 | Radiant Compilation |
| TC-PLL-041 | Primary divider 128 with all secondary dividers 1 | Radiant Compilation |
| TC-PLL-042 | All six output dividers at 64 (median) | Both |
| TC-PLL-043 | Tolerance sweep 0.0 / 0.1 / 0.2 / 0.5 on all six outputs | Radiant Compilation |
| TC-PLL-044 | Tolerance sweep 1.0 / 2.0 / 5.0 / 10.0 on all six outputs | Radiant Compilation |
| TC-PLL-045 | Static phase shift 90 and 270 degrees on all six outputs | Both |
| TC-PLL-046 | Static phase shift 0, 45 and 135 degrees on all six outputs | Radiant Compilation |
| TC-PLL-047 | Static phase shift 180, 225 and 315 degrees on all six outputs | Radiant Compilation |
| TC-PLL-048 | Rising-edge duty trim with delay multipliers 0 and 2 | Both |
| TC-PLL-049 | Falling-edge duty trim with delay multipliers 1 and 4 | Radiant Compilation |
| TC-PLL-050 | Reference clock taken from a device pin with the default LVDS standard | Both |
| TC-PLL-051 | All seventeen distinct reference-clock I/O standards | Radiant Compilation |
| TC-PLL-052 | Dynamic phase control ports generated | Radiant Compilation |
| TC-PLL-053 | Dynamic phase stepping on every output select code 000-101 | Both |
| TC-PLL-054 | All six clock-enable ports requested | Radiant Compilation |
| TC-PLL-055 | Clock-enable port on CLKOS only | Radiant Compilation |
| TC-PLL-056 | PLL reset port not requested | Radiant Compilation |
| TC-PLL-057 | Non-sticky lock detector | Both |
| TC-PLL-058 | Sticky lock detector | Both |
| TC-PLL-059 | Lock output not requested | Radiant Compilation |
| TC-PLL-060 | LMMI slave register interface | Both |
| TC-PLL-061 | APB3 slave without the soft control register | Both |
| TC-PLL-062 | APB3 slave with the soft control register - read | Both |
| TC-PLL-063 | Soft control register write drives the dynamic phase controls | Both |
| TC-PLL-064 | Legacy-mode input requested | Radiant Compilation |
| TC-PLL-065 | Power-down input requested | Radiant Compilation |
| TC-PLL-066 | Fractional-N at the feedback-divider ceiling with the monitor and APB soft registers | Radiant Compilation |
| TC-PLL-067 | Spread spectrum with a pin reference clock, six distinct output frequencies and sticky lock | Radiant Compilation |
| TC-PLL-068 | External feedback with all six clock-enable ports and the dynamic phase ports | Both |
| TC-PLL-069 | Mixed bypass with duty trim on both trim-capable outputs, legacy and power-down | Radiant Compilation |
| TC-PLL-070 | Maximum reference frequency and divider chain with LMMI, no reset and no lock | Radiant Compilation |
| TC-PLL-071 | Minimum reference frequency with the 1.0 MHz monitor, internal path switching and per-output phase shifts | Radiant Compilation |
| TC-PLL-072 | rstn_i assertion and release | Both |
| TC-PLL-073 | pllpd_en_n_i power-down assertion and release | Both |
| TC-PLL-074 | legacy_i asserted for the whole run | Both |
| TC-PLL-075 | enclkop_i through enclkos5_i deassertion and reassertion | Sim Only |
| TC-PLL-076 | usr_fbclk_i as the loop feedback source | Sim Only |
| TC-PLL-077 | refdetreset and refdetlos reference-loss reporting | Sim Only |
| TC-PLL-078 | LMMI transaction on the six LMMI input ports and three LMMI output ports | Sim Only |
| TC-PLL-079 | APB transaction on the seven APB input ports and three APB output ports | Sim Only |
| TC-PLL-080 | All six output clocks and lock_o observed together at distinct frequencies | Both |
| TC-PLL-081 | Default-parameter Radiant compilation smoke test | Radiant Compilation |

### Matrix A - General and Reference Clock fields

| TC ID | Type | `gui_config_mode` | `gui_en_frac_n` | `gui_en_ssc` | `gui_en_usr_fbk` | `gui_en_int_fbkdel_sel` | `gui_refclk_freq` | `gui_m_div` | `gui_en_refclk_mon` | `gui_refclk_mon_freq` |
|---|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-002 | Both | **FREQUENCY** | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-003 | Both | **DIVIDER** | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-004 | Both | FREQUENCY | **True** | False | False | False | 100.0 | — | False | — |
| TC-PLL-005 | Radiant Compilation | DIVIDER | **True** | False | False | False | 18.0 | 1 | False | — |
| TC-PLL-006 | Radiant Compilation | DIVIDER | False | **True** | False | False | 100.0 | 1 | False | — |
| TC-PLL-007 | Radiant Compilation | DIVIDER | False | True | False | False | 100.0 | 1 | False | — |
| TC-PLL-008 | Radiant Compilation | DIVIDER | False | True | False | False | 100.0 | 1 | False | — |
| TC-PLL-009 | Both | DIVIDER | False | True | False | False | 100.0 | 1 | False | — |
| TC-PLL-010 | Radiant Compilation | DIVIDER | False | True | False | False | 18.0 | 1 | False | — |
| TC-PLL-011 | Both | DIVIDER | False | False | **True** | False | 100.0 | 1 | False | — |
| TC-PLL-012 | Radiant Compilation | FREQUENCY | False | False | False | **True** | 100.0 | — | False | — |
| TC-PLL-013 | Both | DIVIDER | False | False | False | False | **18.0** | 1 | False | — |
| TC-PLL-014 | Radiant Compilation | DIVIDER | False | False | False | False | **400.0** | 1 | False | — |
| TC-PLL-015 | Radiant Compilation | DIVIDER | False | False | False | False | **800.0** | 2 | False | — |
| TC-PLL-016 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | **1** | False | — |
| TC-PLL-017 | Radiant Compilation | DIVIDER | False | False | False | False | 440.0 | **22** | False | — |
| TC-PLL-018 | Radiant Compilation | DIVIDER | False | False | False | False | 800.0 | **44** | False | — |
| TC-PLL-019 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | **True** | **3P2** |
| TC-PLL-020 | Radiant Compilation | DIVIDER | False | False | False | False | 200.0 | 2 | True | **1P0** |
| TC-PLL-021 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-022 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-023 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-024 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-025 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 4 | False | — |
| TC-PLL-026 | Both | DIVIDER | False | False | False | False | 800.0 | 44 | False | — |
| TC-PLL-027 | Radiant Compilation | DIVIDER | True | False | False | False | 100.0 / 18.0 | 1 | False | — |
| TC-PLL-028 | Radiant Compilation | DIVIDER | True | False | False | False | 18.0 | 1 | False | — |
| TC-PLL-029 | Both | DIVIDER | True | False | False | False | 18.0 | 1 | False | — |
| TC-PLL-030 | Radiant Compilation | DIVIDER | True | False | False | False | 18.0 | 1 | False | — |
| TC-PLL-031 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-032 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-033 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-034 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-035 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-036 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-037 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-038 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-039 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-040 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-041 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-042 | Both | DIVIDER | False | False | False | False | 100.0 | 4 | False | — |
| TC-PLL-043 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-044 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-045 | Both | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-046 | Radiant Compilation | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-047 | Radiant Compilation | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-048 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-049 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-050 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-051 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-052 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-053 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-054 | Radiant Compilation | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-055 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-056 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-057 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-058 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-059 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-060 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-061 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-062 | Both | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-063 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-064 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-065 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-066 | Radiant Compilation | DIVIDER | **True** | False | False | False | 18.0 | 1 | **True** | 3P2 |
| TC-PLL-067 | Radiant Compilation | DIVIDER | False | **True** | False | False | 100.0 | 1 | False | — |
| TC-PLL-068 | Both | DIVIDER | False | False | **True** | False | 100.0 | 1 | False | — |
| TC-PLL-069 | Radiant Compilation | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-070 | Radiant Compilation | DIVIDER | False | False | False | False | **800.0** | **44** | False | — |
| TC-PLL-071 | Radiant Compilation | FREQUENCY | False | False | False | **True** | **18.0** | — | **True** | **1P0** |
| TC-PLL-072 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-073 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-074 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-075 | Sim Only | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-076 | Sim Only | DIVIDER | False | False | True | False | 100.0 | 1 | False | — |
| TC-PLL-077 | Sim Only | DIVIDER | False | False | False | False | 100.0 | 1 | True | 3P2 |
| TC-PLL-078 | Sim Only | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-079 | Sim Only | FREQUENCY | False | False | False | False | 100.0 | — | False | — |
| TC-PLL-080 | Both | DIVIDER | False | False | False | False | 100.0 | 1 | False | — |
| TC-PLL-081 | Radiant Compilation | FREQUENCY | False | False | False | False | 100.0 | — | False | — |

### Matrix B - Feedback and Spread Spectrum fields

| TC ID | Type | `gui_fbk_mode` | `gui_n_div` | `gui_frac_n_div` | `gui_ssc_profile` | `gui_ssc_mod_depth` | `gui_ssc_mod_freq` |
|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-002 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-003 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-004 | Both | — | — | — | — | — | — |
| TC-PLL-005 | Radiant Compilation | — | 45 | 2048 | — | — | — |
| TC-PLL-006 | Radiant Compilation | — | 16 | — | **DOWN** | **0.25 / 0.75 / 1.25 / 1.75** | 100.0 |
| TC-PLL-007 | Radiant Compilation | — | 16 | — | **CENTER** | **0.50 / 1.00 / 1.50 / 2.00** | 100.0 |
| TC-PLL-008 | Radiant Compilation | — | 16 | — | DOWN | 1.00 | **24.42** |
| TC-PLL-009 | Both | — | 16 | — | DOWN | 1.00 | **100.0** |
| TC-PLL-010 | Radiant Compilation | — | 45 | — | CENTER | 2.00 | **200.0** |
| TC-PLL-011 | Both | — | 8 | — | — | — | — |
| TC-PLL-012 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-013 | Both | INTCLKOP | 44 | — | — | — | — |
| TC-PLL-014 | Radiant Compilation | INTCLKOP | 2 | — | — | — | — |
| TC-PLL-015 | Radiant Compilation | INTCLKOP | 2 | — | — | — | — |
| TC-PLL-016 | Radiant Compilation | INTCLKOP | 8 | — | — | — | — |
| TC-PLL-017 | Radiant Compilation | INTCLKOP | 40 | — | — | — | — |
| TC-PLL-018 | Radiant Compilation | INTCLKOP | 44 | — | — | — | — |
| TC-PLL-019 | Both | INTCLKOP | 3 | — | — | — | — |
| TC-PLL-020 | Radiant Compilation | INTCLKOP | 3 | — | — | — | — |
| TC-PLL-021 | Both | **CLKOP / INTCLKOP** | 1 | — | — | — | — |
| TC-PLL-022 | Radiant Compilation | **CLKOS / INTCLKOS / CLKOS2 / INTCLKOS2** | 1 | — | — | — | — |
| TC-PLL-023 | Radiant Compilation | **CLKOS3 / INTCLKOS3 / CLKOS4 / INTCLKOS4 / CLKOS5 / INTCLKOS5** | 1 | — | — | — | — |
| TC-PLL-024 | Radiant Compilation | INTCLKOP | **1** | — | — | — | — |
| TC-PLL-025 | Radiant Compilation | INTCLKOP | **22** | — | — | — | — |
| TC-PLL-026 | Both | INTCLKOP | **44** | — | — | — | — |
| TC-PLL-027 | Radiant Compilation | — | **16 / 88** | 0 | — | — | — |
| TC-PLL-028 | Radiant Compilation | — | 45 | **0** | — | — | — |
| TC-PLL-029 | Both | — | 45 | **2048** | — | — | — |
| TC-PLL-030 | Radiant Compilation | — | 45 | **4095** | — | — | — |
| TC-PLL-031 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-032 | Radiant Compilation | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-033 | Both | INTCLKOS | 1 | — | — | — | — |
| TC-PLL-034 | Radiant Compilation | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-035 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-036 | Radiant Compilation | CLKOP | — | — | — | — | — |
| TC-PLL-037 | Radiant Compilation | CLKOS | — | — | — | — | — |
| TC-PLL-038 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-039 | Radiant Compilation | CLKOP | — | — | — | — | — |
| TC-PLL-040 | Radiant Compilation | INTCLKOP | 8 | — | — | — | — |
| TC-PLL-041 | Radiant Compilation | INTCLKOS | 8 | — | — | — | — |
| TC-PLL-042 | Both | INTCLKOS | 1 | — | — | — | — |
| TC-PLL-043 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-044 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-045 | Both | — | 8 | — | — | — | — |
| TC-PLL-046 | Radiant Compilation | — | 8 | — | — | — | — |
| TC-PLL-047 | Radiant Compilation | — | 8 | — | — | — | — |
| TC-PLL-048 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-049 | Radiant Compilation | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-050 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-051 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-052 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-053 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-054 | Radiant Compilation | — | 8 | — | — | — | — |
| TC-PLL-055 | Radiant Compilation | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-056 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-057 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-058 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-059 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-060 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-061 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-062 | Both | INTCLKOP | — | — | — | — | — |
| TC-PLL-063 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-064 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-065 | Radiant Compilation | INTCLKOP | — | — | — | — | — |
| TC-PLL-066 | Radiant Compilation | — | **88** | 0 | — | — | — |
| TC-PLL-067 | Radiant Compilation | — | 16 | — | CENTER | 1.50 | 150.0 |
| TC-PLL-068 | Both | — | 8 | — | — | — | — |
| TC-PLL-069 | Radiant Compilation | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-070 | Radiant Compilation | INTCLKOP | **44** | — | — | — | — |
| TC-PLL-071 | Radiant Compilation | CLKOS | — | — | — | — | — |
| TC-PLL-072 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-073 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-074 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-075 | Sim Only | — | 8 | — | — | — | — |
| TC-PLL-076 | Sim Only | — | 8 | — | — | — | — |
| TC-PLL-077 | Sim Only | INTCLKOP | 3 | — | — | — | — |
| TC-PLL-078 | Sim Only | INTCLKOP | — | — | — | — | — |
| TC-PLL-079 | Sim Only | INTCLKOP | — | — | — | — | — |
| TC-PLL-080 | Both | INTCLKOP | 1 | — | — | — | — |
| TC-PLL-081 | Radiant Compilation | INTCLKOP | — | — | — | — | — |

### Matrix C - Primary Clock Output (CLKOP) fields

| TC ID | Type | `gui_clk_op_byp` | `gui_clk_op_freq` | `gui_clk_op_div` | `gui_clk_op_tol` | `gui_clk_op_phase` | `gui_clk_op_trim_en` | `gui_clk_op_trim_mode` | `gui_clk_op_trim_mult` |
|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-002 | Both | — | **100** | — | 0.0 | — | False | — | — |
| TC-PLL-003 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-004 | Both | — | 101.25 | — | 0.1 | — | False | — | — |
| TC-PLL-005 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-006 | Radiant Compilation | — | — | 16 | — | — | False | — | — |
| TC-PLL-007 | Radiant Compilation | — | — | 16 | — | — | False | — | — |
| TC-PLL-008 | Radiant Compilation | — | — | 16 | — | — | False | — | — |
| TC-PLL-009 | Both | — | — | 16 | — | — | False | — | — |
| TC-PLL-010 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-011 | Both | — | — | 1 | — | 0 | False | — | — |
| TC-PLL-012 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-013 | Both | — | — | 2 | — | — | False | — | — |
| TC-PLL-014 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-015 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-016 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-017 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-018 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-019 | Both | — | — | 3 | — | — | False | — | — |
| TC-PLL-020 | Radiant Compilation | — | — | 3 | — | — | False | — | — |
| TC-PLL-021 | Both | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-022 | Radiant Compilation | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-023 | Radiant Compilation | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-024 | Radiant Compilation | — | — | 8 | — | — | False | — | — |
| TC-PLL-025 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-026 | Both | — | — | 1 | — | — | False | — | — |
| TC-PLL-027 | Radiant Compilation | — | — | 16 / 2 | — | — | False | — | — |
| TC-PLL-028 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-029 | Both | — | — | 2 | — | — | False | — | — |
| TC-PLL-030 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-031 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-032 | Radiant Compilation | — | — | 8 | — | — | False | — | — |
| TC-PLL-033 | Both | **True** | — | — | — | — | — | — | — |
| TC-PLL-034 | Radiant Compilation | — | — | 8 | — | — | False | — | — |
| TC-PLL-035 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-036 | Radiant Compilation | — | **800** | — | 0.0 | — | False | — | — |
| TC-PLL-037 | Radiant Compilation | False | **6.25** | — | 0.0 | 0 | False | — | — |
| TC-PLL-038 | Both | — | **100** | — | 0.0 | — | False | — | — |
| TC-PLL-039 | Radiant Compilation | — | **800** | — | 0.0 | — | False | — | — |
| TC-PLL-040 | Radiant Compilation | — | — | **1** | — | — | False | — | — |
| TC-PLL-041 | Radiant Compilation | False | — | **128** | — | 0 | False | — | — |
| TC-PLL-042 | Both | False | — | **64** | — | 0 | False | — | — |
| TC-PLL-043 | Radiant Compilation | — | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | — | False | — | — |
| TC-PLL-044 | Radiant Compilation | — | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | — | False | — | — |
| TC-PLL-045 | Both | — | — | 1 | — | **90 / 270** | False | — | — |
| TC-PLL-046 | Radiant Compilation | — | — | 1 | — | **0 / 45 / 135** | False | — | — |
| TC-PLL-047 | Radiant Compilation | — | — | 1 | — | **180 / 225 / 315** | False | — | — |
| TC-PLL-048 | Both | — | — | 8 | — | — | **True** | **Rising** | **0 / 2** |
| TC-PLL-049 | Radiant Compilation | — | — | 8 | — | — | **True** | **Falling** | **1 / 4** |
| TC-PLL-050 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-051 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-052 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-053 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-054 | Radiant Compilation | — | — | 1 | — | 0 | False | — | — |
| TC-PLL-055 | Radiant Compilation | — | — | 8 | — | — | False | — | — |
| TC-PLL-056 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-057 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-058 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-059 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-060 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-061 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-062 | Both | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-063 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-064 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-065 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-066 | Radiant Compilation | — | — | 2 | — | — | False | — | — |
| TC-PLL-067 | Radiant Compilation | — | — | 16 | — | — | False | — | — |
| TC-PLL-068 | Both | — | — | 1 | — | 0 | False | — | — |
| TC-PLL-069 | Radiant Compilation | — | — | 8 | — | — | **True** | Falling | 2 |
| TC-PLL-070 | Radiant Compilation | — | — | 1 | — | — | False | — | — |
| TC-PLL-071 | Radiant Compilation | False | 396 | — | 0.0 | **45** | False | — | — |
| TC-PLL-072 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-073 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-074 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-075 | Sim Only | — | — | 1 | — | 0 | False | — | — |
| TC-PLL-076 | Sim Only | — | — | 1 | — | 0 | False | — | — |
| TC-PLL-077 | Sim Only | — | — | 3 | — | — | False | — | — |
| TC-PLL-078 | Sim Only | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-079 | Sim Only | — | 100 | — | 0.0 | — | False | — | — |
| TC-PLL-080 | Both | — | — | 8 | — | — | False | — | — |
| TC-PLL-081 | Radiant Compilation | — | 100 | — | 0.0 | — | False | — | — |

### Matrix D - Secondary Clock Output (CLKOS) fields

| TC ID | Type | `gui_clk_os_en` | `gui_clk_os_byp` | `gui_clk_os_freq` | `gui_clk_os_div` | `gui_clk_os_tol` | `gui_clk_os_phase` | `gui_clk_os_trim_en` | `gui_clk_os_trim_mode` | `gui_clk_os_trim_mult` |
|---|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-002 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-003 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-004 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-005 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-006 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-007 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-008 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-009 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-010 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-011 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-012 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-013 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-014 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-015 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-016 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-017 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-018 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-019 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-020 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-021 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-022 | Radiant Compilation | True | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-023 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-024 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-025 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-026 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-027 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-028 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-029 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-030 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-031 | Both | **True** | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-032 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-033 | Both | True | — | — | 8 | — | — | False | — | — |
| TC-PLL-034 | Radiant Compilation | True | **True** | — | — | — | — | — | — | — |
| TC-PLL-035 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-036 | Radiant Compilation | True | False | **6.25** | — | 0.0 | 0 | False | — | — |
| TC-PLL-037 | Radiant Compilation | True | — | **800** | — | 0.0 | — | False | — | — |
| TC-PLL-038 | Both | True | False | **100** | — | 0.0 | 0 | False | — | — |
| TC-PLL-039 | Radiant Compilation | True | False | **800** | — | 0.0 | 0 | False | — | — |
| TC-PLL-040 | Radiant Compilation | True | False | — | **128** | — | 0 | False | — | — |
| TC-PLL-041 | Radiant Compilation | True | — | — | **1** | — | — | False | — | — |
| TC-PLL-042 | Both | True | — | — | **64** | — | — | False | — | — |
| TC-PLL-043 | Radiant Compilation | True | False | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | 0 | False | — | — |
| TC-PLL-044 | Radiant Compilation | True | False | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | 0 | False | — | — |
| TC-PLL-045 | Both | True | False | — | 1 | — | **90 / 270** | False | — | — |
| TC-PLL-046 | Radiant Compilation | True | False | — | 1 | — | **0 / 45 / 135** | False | — | — |
| TC-PLL-047 | Radiant Compilation | True | False | — | 1 | — | **180 / 225 / 315** | False | — | — |
| TC-PLL-048 | Both | True | False | — | 8 | — | 0 | **True** | **Rising** | **0 / 2** |
| TC-PLL-049 | Radiant Compilation | True | False | — | 8 | — | 0 | **True** | **Falling** | **1 / 4** |
| TC-PLL-050 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-051 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-052 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-053 | Both | True | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-054 | Radiant Compilation | True | False | — | 1 | — | 0 | False | — | — |
| TC-PLL-055 | Radiant Compilation | True | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-056 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-057 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-058 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-059 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-060 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-061 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-062 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-063 | Both | True | False | — | 8 | — | 0 | False | — | — |
| TC-PLL-064 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-065 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-066 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-067 | Radiant Compilation | True | — | — | 8 | — | 0 | False | — | — |
| TC-PLL-068 | Both | True | False | — | 1 | — | 0 | False | — | — |
| TC-PLL-069 | Radiant Compilation | True | False | — | 8 | — | 0 | **True** | Rising | 1 |
| TC-PLL-070 | Radiant Compilation | False | — | — | — | — | — | — | — | — |
| TC-PLL-071 | Radiant Compilation | True | — | 792 | — | 0.0 | — | False | — | — |
| TC-PLL-072 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-073 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-074 | Both | False | — | — | — | — | — | — | — | — |
| TC-PLL-075 | Sim Only | True | False | — | 1 | — | 0 | False | — | — |
| TC-PLL-076 | Sim Only | False | — | — | — | — | — | — | — | — |
| TC-PLL-077 | Sim Only | False | — | — | — | — | — | — | — | — |
| TC-PLL-078 | Sim Only | False | — | — | — | — | — | — | — | — |
| TC-PLL-079 | Sim Only | False | — | — | — | — | — | — | — | — |
| TC-PLL-080 | Both | True | False | — | 4 | — | 0 | False | — | — |
| TC-PLL-081 | Radiant Compilation | False | — | — | — | — | — | — | — | — |

### Matrix E - Secondary Clock Output 2 and 3 (CLKOS2, CLKOS3) fields

| TC ID | Type | `gui_clk_s2_en` | `gui_clk_s2_byp` | `gui_clk_s2_freq` | `gui_clk_s2_div` | `gui_clk_s2_tol` | `gui_clk_s2_phase` | `gui_clk_s3_en` | `gui_clk_s3_byp` | `gui_clk_s3_freq` | `gui_clk_s3_div` | `gui_clk_s3_tol` | `gui_clk_s3_phase` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-002 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-003 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-004 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-005 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-006 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-007 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-008 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-009 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-010 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-011 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-012 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-013 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-014 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-015 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-016 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-017 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-018 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-019 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-020 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-021 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-022 | Radiant Compilation | True | False | — | 8 | — | 0 | False | — | — | — | — | — |
| TC-PLL-023 | Radiant Compilation | False | — | — | — | — | — | True | False | — | 8 | — | 0 |
| TC-PLL-024 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-025 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-026 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-027 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-028 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-029 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-030 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-031 | Both | **True** | False | — | 8 | — | 0 | **True** | False | — | 8 | — | 0 |
| TC-PLL-032 | Radiant Compilation | False | — | — | — | — | — | **True** | False | — | 8 | — | 0 |
| TC-PLL-033 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-034 | Radiant Compilation | True | **True** | — | — | — | — | True | **True** | — | — | — | — |
| TC-PLL-035 | Both | True | **True** | — | — | — | — | True | False | — | 4 | — | 0 |
| TC-PLL-036 | Radiant Compilation | True | False | **6.25** | — | 0.0 | 0 | True | False | **6.25** | — | 0.0 | 0 |
| TC-PLL-037 | Radiant Compilation | True | False | 6.25 | — | 0.0 | 0 | True | False | 6.25 | — | 0.0 | 0 |
| TC-PLL-038 | Both | True | False | **100** | — | 0.0 | 0 | True | False | **100** | — | 0.0 | 0 |
| TC-PLL-039 | Radiant Compilation | True | False | **800** | — | 0.0 | 0 | True | False | **800** | — | 0.0 | 0 |
| TC-PLL-040 | Radiant Compilation | True | False | — | **128** | — | 0 | True | False | — | **128** | — | 0 |
| TC-PLL-041 | Radiant Compilation | True | False | — | **1** | — | 0 | True | False | — | **1** | — | 0 |
| TC-PLL-042 | Both | True | False | — | **64** | — | 0 | True | False | — | **64** | — | 0 |
| TC-PLL-043 | Radiant Compilation | True | False | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | 0 | True | False | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | 0 |
| TC-PLL-044 | Radiant Compilation | True | False | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | 0 | True | False | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | 0 |
| TC-PLL-045 | Both | True | False | — | 1 | — | **90 / 270** | True | False | — | 1 | — | **90 / 270** |
| TC-PLL-046 | Radiant Compilation | True | False | — | 1 | — | **0 / 45 / 135** | True | False | — | 1 | — | **0 / 45 / 135** |
| TC-PLL-047 | Radiant Compilation | True | False | — | 1 | — | **180 / 225 / 315** | True | False | — | 1 | — | **180 / 225 / 315** |
| TC-PLL-048 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-049 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-050 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-051 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-052 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-053 | Both | True | False | — | 8 | — | 0 | True | False | — | 8 | — | 0 |
| TC-PLL-054 | Radiant Compilation | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-055 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-056 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-057 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-058 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-059 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-060 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-061 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-062 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-063 | Both | True | False | — | 8 | — | 0 | True | False | — | 8 | — | 0 |
| TC-PLL-064 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-065 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-066 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-067 | Radiant Compilation | True | — | — | 4 | — | 0 | True | — | — | 2 | — | 0 |
| TC-PLL-068 | Both | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-069 | Radiant Compilation | True | True | — | — | — | — | True | True | — | — | — | — |
| TC-PLL-070 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-071 | Radiant Compilation | True | False | 264 | — | 0.0 | 90 | True | False | 198 | — | 0.0 | 135 |
| TC-PLL-072 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-073 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-074 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-075 | Sim Only | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-076 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-077 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-078 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-079 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-080 | Both | True | False | — | 2 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-081 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |

### Matrix F - Secondary Clock Output 4 and 5 (CLKOS4, CLKOS5) fields

| TC ID | Type | `gui_clk_s4_en` | `gui_clk_s4_byp` | `gui_clk_s4_freq` | `gui_clk_s4_div` | `gui_clk_s4_tol` | `gui_clk_s4_phase` | `gui_clk_s5_en` | `gui_clk_s5_byp` | `gui_clk_s5_freq` | `gui_clk_s5_div` | `gui_clk_s5_tol` | `gui_clk_s5_phase` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-002 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-003 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-004 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-005 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-006 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-007 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-008 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-009 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-010 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-011 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-012 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-013 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-014 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-015 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-016 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-017 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-018 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-019 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-020 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-021 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-022 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-023 | Radiant Compilation | True | False | — | 8 | — | 0 | True | False | — | 8 | — | 0 |
| TC-PLL-024 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-025 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-026 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-027 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-028 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-029 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-030 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-031 | Both | **True** | False | — | 8 | — | 0 | **True** | False | — | 8 | — | 0 |
| TC-PLL-032 | Radiant Compilation | False | — | — | — | — | — | **True** | False | — | 8 | — | 0 |
| TC-PLL-033 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-034 | Radiant Compilation | True | **True** | — | — | — | — | True | **True** | — | — | — | — |
| TC-PLL-035 | Both | True | **True** | — | — | — | — | True | False | — | 16 | — | 0 |
| TC-PLL-036 | Radiant Compilation | True | False | **6.25** | — | 0.0 | 0 | True | False | **6.25** | — | 0.0 | 0 |
| TC-PLL-037 | Radiant Compilation | True | False | 6.25 | — | 0.0 | 0 | True | False | 6.25 | — | 0.0 | 0 |
| TC-PLL-038 | Both | True | False | **100** | — | 0.0 | 0 | True | False | **100** | — | 0.0 | 0 |
| TC-PLL-039 | Radiant Compilation | True | False | **800** | — | 0.0 | 0 | True | False | **800** | — | 0.0 | 0 |
| TC-PLL-040 | Radiant Compilation | True | False | — | **128** | — | 0 | True | False | — | **128** | — | 0 |
| TC-PLL-041 | Radiant Compilation | True | False | — | **1** | — | 0 | True | False | — | **1** | — | 0 |
| TC-PLL-042 | Both | True | False | — | **64** | — | 0 | True | False | — | **64** | — | 0 |
| TC-PLL-043 | Radiant Compilation | True | False | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | 0 | True | False | 100 | — | **0.0 / 0.1 / 0.2 / 0.5** | 0 |
| TC-PLL-044 | Radiant Compilation | True | False | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | 0 | True | False | 100 | — | **1.0 / 2.0 / 5.0 / 10.0** | 0 |
| TC-PLL-045 | Both | True | False | — | 1 | — | **90 / 270** | True | False | — | 1 | — | **90 / 270** |
| TC-PLL-046 | Radiant Compilation | True | False | — | 1 | — | **0 / 45 / 135** | True | False | — | 1 | — | **0 / 45 / 135** |
| TC-PLL-047 | Radiant Compilation | True | False | — | 1 | — | **180 / 225 / 315** | True | False | — | 1 | — | **180 / 225 / 315** |
| TC-PLL-048 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-049 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-050 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-051 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-052 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-053 | Both | True | False | — | 8 | — | 0 | True | False | — | 8 | — | 0 |
| TC-PLL-054 | Radiant Compilation | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-055 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-056 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-057 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-058 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-059 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-060 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-061 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-062 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-063 | Both | True | False | — | 8 | — | 0 | True | False | — | 8 | — | 0 |
| TC-PLL-064 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-065 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-066 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-067 | Radiant Compilation | True | — | — | 32 | — | 0 | True | — | — | 128 | — | 0 |
| TC-PLL-068 | Both | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-069 | Radiant Compilation | True | True | — | — | — | — | True | True | — | — | — | — |
| TC-PLL-070 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-071 | Radiant Compilation | True | False | 99 | — | 0.0 | 180 | True | False | 49.5 | — | 0.0 | 225 |
| TC-PLL-072 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-073 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-074 | Both | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-075 | Sim Only | True | False | — | 1 | — | 0 | True | False | — | 1 | — | 0 |
| TC-PLL-076 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-077 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-078 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-079 | Sim Only | False | — | — | — | — | — | False | — | — | — | — | — |
| TC-PLL-080 | Both | True | False | — | 16 | — | 0 | True | False | — | 128 | — | 0 |
| TC-PLL-081 | Radiant Compilation | False | — | — | — | — | — | False | — | — | — | — | — |

### Matrix G - Optional Ports fields

| TC ID | Type | `gui_en_refclk_pin` | `gui_refclk_io_type` | `gui_en_dyn_phase` | `gui_en_clken_op` | `gui_en_clken_os` | `gui_en_clken_s2` | `gui_en_clken_s3` | `gui_en_clken_s4` | `gui_en_clken_s5` | `gui_en_pll_reset` | `gui_en_pll_lock` | `gui_pll_lock_sticky` | `gui_reg_interface` | `gui_en_csr` | `gui_en_legacy` | `gui_en_powerdown` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-PLL-001 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-002 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-003 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-004 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-005 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-006 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-007 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-008 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-009 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-010 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-011 | Both | False | — | False | False | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-012 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-013 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-014 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-015 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-016 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-017 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-018 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-019 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-020 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-021 | Both | False | — | False | False | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-022 | Radiant Compilation | False | — | False | False | False | False | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-023 | Radiant Compilation | False | — | False | False | — | — | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-024 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-025 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-026 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-027 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-028 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-029 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-030 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-031 | Both | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-032 | Radiant Compilation | False | — | False | — | — | — | False | — | False | True | True | False | None | — | False | False |
| TC-PLL-033 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-034 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-035 | Both | False | — | False | — | — | — | False | — | False | True | True | False | None | — | False | False |
| TC-PLL-036 | Radiant Compilation | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-037 | Radiant Compilation | False | — | False | False | — | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-038 | Both | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-039 | Radiant Compilation | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-040 | Radiant Compilation | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-041 | Radiant Compilation | False | — | False | False | — | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-042 | Both | False | — | False | False | — | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-043 | Radiant Compilation | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-044 | Radiant Compilation | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-045 | Both | False | — | False | False | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-046 | Radiant Compilation | False | — | False | False | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-047 | Radiant Compilation | False | — | False | False | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-048 | Both | False | — | False | — | False | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-049 | Radiant Compilation | False | — | False | — | False | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-050 | Both | **True** | **LVDS** | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-051 | Radiant Compilation | True | **all 17 distinct values** | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-052 | Radiant Compilation | False | — | **True** | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-053 | Both | False | — | **True** | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-054 | Radiant Compilation | False | — | False | **True** | **True** | **True** | **True** | **True** | **True** | True | True | False | None | — | False | False |
| TC-PLL-055 | Radiant Compilation | False | — | False | — | **True** | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-056 | Radiant Compilation | False | — | False | — | — | — | — | — | — | **False** | True | False | None | — | False | False |
| TC-PLL-057 | Both | False | — | False | — | — | — | — | — | — | True | **True** | **False** | None | — | False | False |
| TC-PLL-058 | Both | False | — | False | — | — | — | — | — | — | True | True | **True** | None | — | False | False |
| TC-PLL-059 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | **False** | — | None | — | False | False |
| TC-PLL-060 | Both | False | — | False | — | — | — | — | — | — | True | True | False | **LMMI** | — | False | False |
| TC-PLL-061 | Both | False | — | False | — | — | — | — | — | — | True | True | False | **APB** | **False** | False | False |
| TC-PLL-062 | Both | False | — | — | — | — | — | — | — | — | True | True | False | APB | **True** | False | False |
| TC-PLL-063 | Both | False | — | — | — | False | False | False | False | False | True | True | False | APB | **True** | False | False |
| TC-PLL-064 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | **True** | False |
| TC-PLL-065 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | **True** |
| TC-PLL-066 | Radiant Compilation | False | — | — | — | — | — | — | — | — | True | True | False | **APB** | **True** | False | False |
| TC-PLL-067 | Radiant Compilation | **True** | **SLVS** | False | — | False | False | False | False | False | True | True | **True** | None | — | False | False |
| TC-PLL-068 | Both | False | — | **True** | **True** | True | True | True | True | True | True | True | False | None | — | False | False |
| TC-PLL-069 | Radiant Compilation | False | — | False | — | False | — | — | — | — | True | True | False | None | — | **True** | **True** |
| TC-PLL-070 | Radiant Compilation | False | — | False | — | — | — | — | — | — | **False** | **False** | — | **LMMI** | — | False | False |
| TC-PLL-071 | Radiant Compilation | False | — | False | False | — | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-072 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-073 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | True |
| TC-PLL-074 | Both | False | — | False | — | — | — | — | — | — | True | True | False | None | — | True | False |
| TC-PLL-075 | Sim Only | False | — | False | True | True | True | True | True | True | True | True | False | None | — | False | False |
| TC-PLL-076 | Sim Only | False | — | False | False | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-077 | Sim Only | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |
| TC-PLL-078 | Sim Only | False | — | False | — | — | — | — | — | — | True | True | False | LMMI | — | False | False |
| TC-PLL-079 | Sim Only | False | — | False | — | — | — | — | — | — | True | True | False | APB | False | False | False |
| TC-PLL-080 | Both | False | — | False | — | False | False | False | False | False | True | True | False | None | — | False | False |
| TC-PLL-081 | Radiant Compilation | False | — | False | — | — | — | — | — | — | True | True | False | None | — | False | False |

### Feature coverage

One row per feature in spec 1.1.

| Feature (spec 1.1) | Covering TC IDs |
|---|---|
| Hardened PLL wrapper with reference divider 1–44, integer feedback divider 1–128, six output dividers 1–128, and a VCO constrained to 800–1600 MHz | TC-PLL-016 – TC-PLL-018 (reference divider), TC-PLL-025 – TC-PLL-027 (feedback divider), TC-PLL-040 – TC-PLL-042 (output dividers), TC-PLL-013 – TC-PLL-015 and TC-PLL-070 (VCO window at the reference-frequency extremes). Declared feedback-divider ceiling 128: see `SPEC-GAP-07` and Exclusions |
| Up to six output clocks — one primary and five secondary — each independently enabled, with the primary always present | TC-PLL-001 (primary alone), TC-PLL-031, TC-PLL-032, TC-PLL-080 |
| Output frequency range 10–800 MHz for a clock used as the feedback source and 6.25–800 MHz otherwise | TC-PLL-036 (primary as feedback at 800), TC-PLL-037 (feedback CLKOS at 800, primary at the 6.25 floor), TC-PLL-039 (all six at 800), TC-PLL-040 (secondaries at 6.25) |
| Phase-detector frequency range 18–500 MHz for integer-N, 18–100 MHz for fractional-N or spread-spectrum operation, and 10–160 MHz on a device whose name ends in `p` | TC-PLL-013 (18 MHz floor), TC-PLL-014, TC-PLL-015, TC-PLL-018 (18.18 MHz at the reference-divider ceiling), TC-PLL-005 – TC-PLL-010 and TC-PLL-027 – TC-PLL-030 (fractional / spread-spectrum sub-range). The 10–160 MHz device path is excluded — see Exclusions and `SPEC-GAP-02` |
| Fractional-N feedback division with a 12-bit fractional word over a 4096 denominator, feedback divider 16–128, selected by the Enable Fractional-N Divider field | TC-PLL-004, TC-PLL-005, TC-PLL-027 – TC-PLL-030, TC-PLL-066 |
| Spread-spectrum clock generation with down or centre triangular profile, modulation depth 0.25–2.00 % in 0.25 % steps and modulation frequency 24.42–200 kHz | TC-PLL-006 – TC-PLL-010, TC-PLL-067 |
| Per-output bypass that routes the reference clock to the output without passing through the loop | TC-PLL-033 – TC-PLL-035, TC-PLL-069 |
| Static phase shift on any output that is not the feedback source, in eight 45° steps, resolved into a delay and phase code pair per output | TC-PLL-045 – TC-PLL-047, TC-PLL-071 |
| Dynamic phase control ports — direction, step, load and a 3-bit output select — enabled by the Enable Dynamic Phase Ports field | TC-PLL-052, TC-PLL-053, TC-PLL-068 |
| Duty-cycle trim on the primary and first secondary output, rising or falling edge, with a delay multiplier of 0, 1, 2 or 4 | TC-PLL-048, TC-PLL-049, TC-PLL-069 |
| Optional per-output clock-enable input for any output that is neither bypassed nor the feedback source | TC-PLL-054, TC-PLL-055, TC-PLL-068, TC-PLL-075 |
| Feedback from any enabled output clock, from its internal divider tap, or from an externally supplied user feedback clock | TC-PLL-021 – TC-PLL-023 (all 12 output and tap selections), TC-PLL-011 and TC-PLL-076 (external feedback clock) |
| Reference clock optionally taken from a device pin through a bidirectional buffer, with a choice of 18 I/O standards applied as a physical constraint | TC-PLL-050, TC-PLL-051 (all 17 distinct standards; the list's duplicate `HSTL15D_I` entry is tested once — see Exclusions), TC-PLL-067 |
| Reference-clock loss monitor with a 3.2 MHz or 1.0 MHz monitor clock and a loss-of-signal output, unavailable on a device whose name ends in `p` | TC-PLL-019, TC-PLL-020, TC-PLL-066, TC-PLL-071, TC-PLL-077. The device-name restriction itself is excluded — see Exclusions and `SPEC-GAP-02` |
| Optional lock output, selectable between a sticky and a non-sticky lock detector | TC-PLL-057 – TC-PLL-059, TC-PLL-067, TC-PLL-070 |
| Optional reset, power-down and legacy-mode inputs, each of which also arms the corresponding attribute on the hard block | TC-PLL-056, TC-PLL-064, TC-PLL-065, TC-PLL-069, TC-PLL-070, TC-PLL-072 – TC-PLL-074 |
| Optional register access as an LMMI slave (8-bit data, 7-bit offset) or an APB3 slave (32-bit bus, DWORD-addressed, 8 bits of data used) | TC-PLL-060, TC-PLL-061, TC-PLL-070, TC-PLL-078, TC-PLL-079 |
| Optional soft control register, available only with the APB3 slave, exposing PLL lock status and the dynamic phase controls at one register offset | TC-PLL-062, TC-PLL-063, TC-PLL-066 |
| Verilog-macro selection between two hard-primitive families, evaluated from the target device name | Excluded — the `IS_JP_DEVICE` branch is not reachable on the target family's devices and the device set is `[UNRESOLVED]`. See Exclusions ("Non-target device paths") and `SPEC-GAP-02`, `SPEC-GAP-12`. The macro-undefined branch that *is* taken is covered by every test, and its two sub-branches by TC-PLL-001 (base primitive, monitor off) and TC-PLL-019 (monitor-capable primitive, monitor on) |
| Requires Radiant 2025.1 or later; no upper Radiant bound is declared | TC-PLL-081 (and implicitly every test — the plan is executed on Radiant 2025.1) |

## Test Groups

Groups follow spec 1.6 group order, as explained in section 1. Test IDs are numbered sequentially across the whole plan in group order.

Configuration bullets list every field a test sets or relies on, plus the loop values the chosen fields imply. Fields not listed are at their spec 1.6 defaults. Unless a card says otherwise, every test targets device **`LIFCL-40`** on Radiant 2025.1, and the shared procedure is:

1. Create a Radiant 2025.1 project for `LIFCL-40`.
2. Instantiate `latticesemi.com:module:pll:1.9.1` and set the fields listed under **Configuration**.
3. Press **Calculate** so the divider and analog optimizer runs (spec 1.5.9), then generate the IP instance.
4. For a `Radiant Compilation` or `Both` test: run synthesis and map on the generated instance.
5. For a `Sim Only` or `Both` test: elaborate the generated RTL with the IP's testbench and run the functional simulation described under **Procedure**.

A card's **Procedure** lists only what differs from or adds to those steps.

### G1 · Baseline

#### TC-PLL-001 — Default-configuration generation, compilation and lock `Both`

**Configuration**

- All fields at their spec 1.6 defaults. Explicitly: `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0 MHz, `gui_clk_op_freq`=100, `gui_clk_op_tol`=0.0, `gui_clk_os_en` … `gui_clk_s5_en`=`False`, `gui_en_frac_n`=`False`, `gui_en_ssc`=`False`, `gui_en_usr_fbk`=`False`, `gui_en_int_fbkdel_sel`=`False`, `gui_en_refclk_mon`=`False`, `gui_en_refclk_pin`=`False`, `gui_en_dyn_phase`=`False`, `gui_en_pll_reset`=`True`, `gui_en_pll_lock`=`True`, `gui_pll_lock_sticky`=`False`, `gui_reg_interface`=`None`, `gui_en_legacy`=`False`, `gui_en_powerdown`=`False`
- Feedback source: whichever default the dialog presents — see `SPEC-GAP-01`

**Procedure**

1. Generate with no field changed from the dialog's initial state.
2. Record the generated parameter list and the values shown in the read-only display fields (`gui_vco_freq`, `gui_m_div_disp`, `gui_n_div_disp`, `gui_clk_op_div_disp`, `gui_phasedet_freq`).
3. Simulate: release `rstn_i` and observe `clkop_o` and `lock_o` for at least 700 µs of simulation time (the bound the IP's own testbench uses, spec 1.5.13).

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKI_FREQ` is 100.0 and the emitted constraint contains a `create_clock` on `clki_i` with period `round(1000000 / 100.0) / 1000` = 10.0 ns, per 1.5.13 *Constraints applied*; no I/O-standard assignment is emitted, because the reference clock is not taken from a pin (per 1.5.5).
- `gui_vco_freq` reads a value inside 800–1600 MHz (Rule 9) and `clkop_o` measures 100 MHz ± the 0.0 % tolerance, i.e. exactly, per Rule 1 with the internal 1e-6 % substitution.
- The generated output divider parameter `DIVOP_ACTUAL_STR` equals the chosen primary divider **minus one**, per 1.5.2; `CLKI_DIVIDER_ACTUAL_STR` and `FBCLK_DIVIDER_ACTUAL_STR` are plain integers, per 1.5.2.
- `EN_REFCLK_MON` is 0 and `REF_COUNTS` is `0000`, per 1.5.6; the base (non-monitor) primitive is instantiated, per 1.5.1.
- Every spread-spectrum attribute is at its zero encoding, per 1.5.4 (the wrapper forces them regardless of the parameters when neither fractional-N nor spread spectrum is enabled).
- `PLL_RST` is 1 and `LOCK_EN` is 1, so `rstn_i` is connected and `lock_o` is driven rather than dangling, per 1.3 and 1.5.8; `PLL_LOCK_STICKY` is 0, selecting the non-sticky detector, per 1.5.8.
- `LMMI_EN`, `APB_EN` and `APB_SOFT_REG_EN` are all 0, so no bus port is connected, per 1.5.11.
- In simulation `lock_o` asserts and remains asserted for the rest of the run.
- The `gpll_cfg_upd` component generator has run: the instance directory holds the preserved tool-written configuration file under its fixed name and the promoted file the Calculate command wrote, per 1.5.12.

### G2 · Configuration Mode — `gui_config_mode`

#### TC-PLL-002 — Frequency mode with an exactly achievable primary output `Both`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, `gui_clk_op_freq`=100, `gui_clk_op_tol`=0.0

**Procedure**

1. Confirm before generating that the reference, feedback and output *divider* fields are read-only and replaced by their Actual Value displays, and that the frequency and tolerance fields are editable (Rule 15).
2. Generate, compile, and simulate `clkop_o`.

**Pass Criteria**

- The divider fields are read-only and the frequency and tolerance fields editable, per Rule 15.
- No Rule 1 DRC error is raised, and `gui_clk_op_ppm` reads 0 — the request is exactly achievable.
- `clkop_o` measures 100 MHz in simulation, and `CLKOP_FREQ_ACTUAL` reports 100, per 1.5.2.
- `gui_m_div_disp`, `gui_n_div_disp` and `gui_clk_op_div_disp` show the divider set the optimizer chose, and the VCO those three imply lies inside 800–1600 MHz, per 1.5.2 and Rule 9.

#### TC-PLL-003 — Divider mode with dividers entered directly `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8
- Implied loop: phase-detector frequency 100 MHz, feedback output divider 8, VCO 800 MHz, `clkop_o` 100 MHz

**Procedure**

1. Confirm before generating that the frequency and tolerance fields are read-only and the divider fields editable (Rule 15).
2. Generate, compile, and simulate `clkop_o`.

**Pass Criteria**

- The frequency and tolerance fields are read-only and the divider fields editable, per Rule 15.
- `CLKI_DIVIDER_ACTUAL_STR` is `1` and `FBCLK_DIVIDER_ACTUAL_STR` is `1` — plain integers, per 1.5.2.
- `DIVOP_ACTUAL_STR` is `7`, i.e. the entered divider 8 minus one, per 1.5.2.
- The reported VCO is 800 MHz (100 MHz × 1 × 8), inside 800–1600 MHz, per 1.5.2 and Rule 9.
- `clkop_o` measures 100 MHz in simulation (800 ÷ 8), per 1.5.2.

### G3 · Fractional-N Divider — `gui_en_frac_n`

Enabling this field forces the feedback source to the primary internal tap and locks the feedback-mode field, forces every output bypass off, and narrows the phase-detector range to 18–100 MHz and the feedback-divider range to 16–128 (spec 1.5.4; Rules 4, 5, 14).

#### TC-PLL-004 — Fractional-N feedback division in frequency mode `Both`

**Configuration**

- `gui_en_frac_n`=`True`, `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, `gui_clk_op_freq`=101.25, `gui_clk_op_tol`=0.1
- Reference divider is preset to 1 because 100.0 MHz does not exceed the 500 MHz threshold for a device whose name does not end in `p` (Rule 28), giving a phase-detector frequency of 100 MHz — inside the 18–100 MHz fractional-N range (Rule 4)

**Procedure**

1. Confirm the feedback-mode field is hidden and the display field `gui_fbk_mode_disp` shows the forced selection (Rule 14, spec 1.5.4).
2. Confirm every output bypass field is read-only (Rule 14).
3. Press **Calculate**, generate, compile, and simulate `clkop_o` and `lock_o`.

**Pass Criteria**

- `FRAC_N_EN` is 1 and the feedback divider is switched out of integer mode with the primitive's sigma-delta modulator enabled, per 1.5.4.
- `FBK_MODE` is the primary internal tap and the feedback-mode field is not editable, per 1.5.4.
- Every `CLKO*_BYPASS` parameter is 0, per 1.5.4 and Rule 14.
- No Rule 1 DRC error is raised, and `gui_clk_op_ppm` reports an error within the configured 0.1 % tolerance.
- `SSC_F_CODE_STR` is non-zero — a fractional feedback word was selected — and is a 15-bit value whose low three bits are zero, per 1.5.4.
- `SSC_N_CODE_STR` carries the integer part of the feedback divider as a 9-bit binary attribute, and `FBCLK_DIVIDER_ACTUAL_STR` carries the same integer as a decimal string, per 1.5.4.
- Every spread-spectrum-specific attribute (`SSC_TBASE_STR`, `SSC_STEP_IN_STR`, `SSC_REG_WEIGHTING_SEL_STR`, `SSC_PROFILE`) is at its zero encoding, because spread spectrum is not enabled, per 1.5.4.
- In simulation `lock_o` asserts and `clkop_o` measures 101.25 MHz within the reported PPM error.

#### TC-PLL-005 — Fractional-N feedback division in divider mode `Radiant Compilation`

**Configuration**

- `gui_en_frac_n`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=18.0, `gui_m_div`=1, `gui_n_div`=45, `gui_frac_n_div`=2048, `gui_clk_op_div`=2
- Implied loop: phase-detector frequency 18 MHz (inside 18–100, Rule 4), effective feedback divider 45 + 2048/4096 = 45.5, VCO 819 MHz (inside 800–1600, Rule 9), `clkop_o` 409.5 MHz (inside 6.25–800, Rule 10)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `FRAC_N_EN` is 1, per 1.5.4.
- `SSC_F_CODE_STR` is `2048` packed into 15 bits by appending three zero bits — decimal 16384 — per 1.5.4.
- `SSC_N_CODE_STR` is the 9-bit binary form of 45 and `FBCLK_DIVIDER_ACTUAL_STR` is `45`, per 1.5.4.
- `DIVOP_ACTUAL_STR` is `1`, i.e. 2 − 1, per 1.5.2.
- `gui_vco_freq` reads 819.0 MHz, inside 800–1600, per Rule 9.
- Every output bypass parameter is 0, per Rule 14.

### G4 · Spread Spectrum — `gui_en_ssc`, `gui_ssc_profile`, `gui_ssc_mod_depth`, `gui_ssc_mod_freq`

Spread spectrum imposes the same feedback and bypass restrictions as fractional-N and the same 18–100 MHz phase-detector range (spec 1.5.4; Rules 4, 14, 17). The three spread-spectrum fields are editable only while this field is on (Rule 17).

The derivation these tests check is the one stated in spec 1.5.4: time base = round(1000 × phase-detector frequency ÷ modulation frequency); amplitude = depth ÷ 100 for a down profile and depth ÷ 200 for a centre profile; depth code = amplitude × feedback divider × 262144 ÷ time base, scaled down by a power of two with the weighting selector recording the shift when the code would exceed 127, and the weighting selector 0 otherwise. The rounding rule for the depth code itself is not stated — see `SPEC-GAP-04` — so the criteria below assert the time base, the weighting selector and the code's relation to 127, not an exact code.

#### TC-PLL-006 — Down-spread profile across modulation depths 0.25 / 0.75 / 1.25 / 1.75 `Radiant Compilation`

**Configuration**

- `gui_en_ssc`=`True`, `gui_ssc_profile`=`DOWN`, `gui_ssc_mod_freq`=100.0 kHz
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=16, `gui_clk_op_div`=16
- Implied loop: phase-detector frequency 100 MHz (the top of the 18–100 MHz spread-spectrum range, Rule 4), VCO 1600 MHz, `clkop_o` 100 MHz. The feedback divider is 16 because that is the only value satisfying both the 16–128 spread-spectrum floor (Rule 5) and the 800–1600 MHz VCO window at a 100 MHz phase-detector frequency (Rule 9)
- Iterate `gui_ssc_mod_depth` over 0.25, 0.75, 1.25, 1.75; everything else identical

**Procedure**

1. Confirm the profile, depth and modulation-frequency fields are editable and the feedback-mode field is not (Rules 14, 17).
2. For each depth in the table, set the field, press **Calculate**, generate and compile.

| Iteration | `gui_ssc_mod_depth` | Amplitude (depth ÷ 100, per 1.5.4) | Expected weighting selector |
|---|---|---|---|
| 1 | 0.25 | 0.0025 | `0` — the computed code does not exceed 127 |
| 2 | 0.75 | 0.0075 | `0` |
| 3 | 1.25 | 0.0125 | `0` |
| 4 | 1.75 | 0.0175 | `0` |

**Pass Criteria**

- All four iterations generate and compile with no DRC error.
- `SS_EN` is 1 and the primitive's spread-spectrum generator is enabled with the **down**-triangular profile selected, per 1.5.4; `SSC_PROFILE` is `DOWN`.
- The feedback divider is switched out of integer mode with the sigma-delta modulator enabled and `FBK_MODE` is the primary internal tap, per 1.5.4.
- `SSC_TBASE_STR` is `1000` in every iteration — round(1000 × 100 ÷ 100) — per 1.5.4.
- `SSC_STEP_IN_STR` increases monotonically across the four iterations and in each is at most 127, and `SSC_REG_WEIGHTING_SEL_STR` is `0` in all four, per 1.5.4.
- `DIVOP_ACTUAL_STR` is `15` (16 − 1) in every iteration, per 1.5.2.
- Every output bypass parameter is 0, per Rule 14.

#### TC-PLL-007 — Centre-spread profile across modulation depths 0.50 / 1.00 / 1.50 / 2.00 `Radiant Compilation`

**Configuration**

- Identical to TC-PLL-006 except `gui_ssc_profile`=`CENTER`
- Iterate `gui_ssc_mod_depth` over 0.50, 1.00, 1.50, 2.00

**Procedure**

1. For each depth in the table, set the field, press **Calculate**, generate and compile.

| Iteration | `gui_ssc_mod_depth` | Amplitude (depth ÷ 200, per 1.5.4) | Expected weighting selector |
|---|---|---|---|
| 1 | 0.50 | 0.0025 | `0` |
| 2 | 1.00 | 0.0050 | `0` |
| 3 | 1.50 | 0.0075 | `0` |
| 4 | 2.00 | 0.0100 | `0` |

**Pass Criteria**

- All four iterations generate and compile with no DRC error.
- `SSC_PROFILE` is `CENTER` and the primitive's centre-triangular profile is selected, per 1.5.4.
- `SSC_TBASE_STR` is `1000` in every iteration, per 1.5.4.
- For the same numeric depth field value, the centre-profile amplitude is half the down-profile amplitude — iteration 2 here (depth 1.00, amplitude 0.0050) yields the same amplitude as, and therefore a `SSC_STEP_IN_STR` equal to, TC-PLL-006 iteration 2 (depth 0.50 would be 0.0050 under a down profile) — per the depth ÷ 100 versus depth ÷ 200 split in 1.5.4.
- `SSC_STEP_IN_STR` is at most 127 and `SSC_REG_WEIGHTING_SEL_STR` is `0` in all four iterations, per 1.5.4.

#### TC-PLL-008 — Minimum modulation frequency 24.42 kHz `Radiant Compilation`

**Configuration**

- `gui_en_ssc`=`True`, `gui_ssc_profile`=`DOWN`, `gui_ssc_mod_depth`=1.00, `gui_ssc_mod_freq`=24.42 kHz — the bottom of the 24.42–200 kHz range, which spec 1.7 Rule 11 records as 100 ÷ 4.095 rounded to two decimals
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=16, `gui_clk_op_div`=16 — phase-detector frequency 100 MHz, VCO 1600 MHz, `clkop_o` 100 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error; 24.42 is accepted by the field's declared range, per Rule 11.
- `SSC_TBASE_STR` is `4095` — round(1000 × 100 ÷ 24.42) — per 1.5.4. This is the largest time base the field's lower bound admits, which is why Rule 11 derives that bound from 4.095.
- `SS_EN` is 1 and `SSC_PROFILE` is `DOWN`, per 1.5.4.
- `SSC_REG_WEIGHTING_SEL_STR` is `0` and `SSC_STEP_IN_STR` is at most 127, per 1.5.4.

#### TC-PLL-009 — Median modulation frequency 100 kHz with a modulated output clock `Both`

**Configuration**

- `gui_en_ssc`=`True`, `gui_ssc_profile`=`DOWN`, `gui_ssc_mod_depth`=1.00, `gui_ssc_mod_freq`=100.0 kHz — the field default and the mid-range value of 24.42–200 kHz
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=16, `gui_clk_op_div`=16 — phase-detector frequency 100 MHz, VCO 1600 MHz, `clkop_o` 100 MHz nominal

**Procedure**

1. Generate, compile, then simulate for at least 700 µs and additionally for at least three modulation periods (30 µs at 100 kHz).
2. Measure the `clkop_o` period continuously over the observation window and record its minimum, maximum and mean.

**Pass Criteria**

- `SSC_TBASE_STR` is `1000` — round(1000 × 100 ÷ 100) — per 1.5.4.
- `SS_EN` is 1, `SSC_PROFILE` is `DOWN`, `SSC_REG_WEIGHTING_SEL_STR` is `0`, per 1.5.4.
- `lock_o` asserts and stays asserted for the rest of the run.
- The measured `clkop_o` period varies over the run rather than being constant, and the variation repeats with a period of 10 µs (the reciprocal of the 100 kHz modulation frequency), per the time-base derivation in 1.5.4.
- The measured mean `clkop_o` frequency is at or below the 100 MHz nominal — a **down**-spread profile modulates downward from nominal, per 1.5.4.

#### TC-PLL-010 — Maximum modulation frequency 200 kHz driving the weighting shift `Radiant Compilation`

**Configuration**

- `gui_en_ssc`=`True`, `gui_ssc_profile`=`CENTER`, `gui_ssc_mod_depth`=2.00, `gui_ssc_mod_freq`=200.0 kHz — the top of the range, per Rule 11
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=18.0, `gui_m_div`=1, `gui_n_div`=45, `gui_clk_op_div`=2
- Implied loop: phase-detector frequency 18 MHz (the floor of the 18–100 MHz range, Rule 4), effective feedback divider 45, VCO 810 MHz (Rule 9), `clkop_o` 405 MHz (Rule 10). The feedback divider 45 satisfies the 16–128 spread-spectrum floor (Rule 5)
- This combination is chosen because it is the one in this plan whose depth code exceeds 127 and therefore exercises the power-of-two scaling path of 1.5.4

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `SSC_TBASE_STR` is `90` — round(1000 × 18 ÷ 200) — per 1.5.4.
- The unscaled depth code implied by 1.5.4 (amplitude 2.00 ÷ 200 = 0.01, times feedback divider 45, times 262144, divided by time base 90) exceeds 127, so `SSC_REG_WEIGHTING_SEL_STR` is **non-zero** and `SSC_STEP_IN_STR` is at most 127, per the scaling rule in 1.5.4.
- `SSC_PROFILE` is `CENTER`, per 1.5.4.
- `DIVOP_ACTUAL_STR` is `1` (2 − 1), per 1.5.2.

### G5 · User Feedback Clock — `gui_en_usr_fbk`

This field is visible and editable only when neither fractional-N nor spread spectrum is enabled (Rule 16), and enabling it forces the primary output's bypass off (Rule 14) and selects `USERFBCLK` as the feedback source (spec 1.5.3).

#### TC-PLL-011 — External feedback clock selected as the loop feedback source `Both`

**Configuration**

- `gui_en_usr_fbk`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 100 MHz, feedback divider 8, VCO 800 MHz, `clkop_o` 800 MHz. The primary divider is 1 so that the VCO is 800 MHz under either reading of the loop equation in 1.5.2 — see `SPEC-GAP-03`
- Stimulus: drive `usr_fbclk_i` at 800 MHz, which is the phase-detector frequency times the feedback divider — see `SPEC-GAP-13`

**Procedure**

1. Confirm the feedback-mode field is hidden and `gui_fbk_mode_disp` shows the forced external selection (spec 1.6 Feedback group).
2. Generate, compile, then simulate driving `clki_i` at 100 MHz and `usr_fbclk_i` at 800 MHz.

**Pass Criteria**

- `FBK_MODE` is `USERFBCLK`, per 1.5.3 and spec 1.6 General.
- `CLKOP_BYPASS` is 0 — the primary output's bypass is forced off — per Rule 14.
- `usr_fbclk_i` is connected rather than tied low, because the Enable User Feedback Clock field is true, per 1.3.
- The wrapper's feedback multiplexer selects the `usr_fbclk_i` arm, per 1.5.3.
- In simulation `lock_o` asserts and `clkop_o` measures 800 MHz.

### G6 · Internal Path Switching — `gui_en_int_fbkdel_sel`

#### TC-PLL-012 — Internal feedback delay path enabled `Radiant Compilation`

**Configuration**

- `gui_en_int_fbkdel_sel`=`True`; all other fields at their defaults (as TC-PLL-001)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `INTFBKDEL_SEL` is `ENABLED`, per spec 1.6 General; with the field at its `False` default in TC-PLL-001 the same parameter is `DISABLED`, so both values of the field are distinguished by this pair.
- No other generated parameter differs from TC-PLL-001's list — this field selects the hard block's internal feedback delay path and nothing else, per spec 1.6 General.
### G7 · Reference Clock Frequency — `gui_refclk_freq`

Legal range 18.0–800.0 MHz (Rule 3). The median value tested is **400.0 MHz**, chosen as a representative mid-range value that is also the largest reference frequency the reference divider can pass through undivided while keeping the phase-detector frequency at or below the 500 MHz integer-N ceiling (Rules 4, 28).

#### TC-PLL-013 — Minimum reference frequency 18 MHz `Both`

**Configuration**

- `gui_refclk_freq`=18.0 — the bottom of the range, which Rule 3 records as set by device characterization rather than architecture
- `gui_config_mode`=`DIVIDER`, `gui_m_div`=1, `gui_n_div`=44, `gui_clk_op_div`=2
- Implied loop: phase-detector frequency 18 MHz (the integer-N floor, Rule 4), feedback output divider 2, VCO 1584 MHz (Rule 9), `clkop_o` 792 MHz. `clkop_o` is the feedback source, so its legal range is the widened 10–800 MHz (Rule 10)

**Pass Criteria**

- Generation and compilation complete with no DRC error; 18.0 is accepted, per Rule 3.
- `CLKI_FREQ` is 18.0 and the emitted `create_clock` on `clki_i` has period `round(1000000 / 18.0) / 1000` = 55.556 ns, per 1.5.13 *Constraints applied*.
- `gui_phasedet_freq` reads 18.0 MHz, at the floor of the 18–500 MHz integer-N range, per Rule 4.
- `gui_vco_freq` reads 1584.0 MHz, inside 800–1600, per Rule 9.
- `DIVOP_ACTUAL_STR` is `1` (2 − 1), per 1.5.2.
- In simulation `lock_o` asserts and `clkop_o` measures 792 MHz.

#### TC-PLL-014 — Median reference frequency 400 MHz `Radiant Compilation`

**Configuration**

- `gui_refclk_freq`=400.0
- `gui_config_mode`=`DIVIDER`, `gui_m_div`=1, `gui_n_div`=2, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 400 MHz (inside 18–500, Rule 4), VCO 800 MHz, `clkop_o` 800 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKI_FREQ` is 400.0 and the emitted `create_clock` period is `round(1000000 / 400.0) / 1000` = 2.5 ns, per 1.5.13.
- `gui_phasedet_freq` reads 400.0 MHz, inside the 18–500 MHz integer-N range, per Rule 4.
- `gui_vco_freq` reads 800.0 MHz, at the floor of 800–1600, per Rule 9.
- `CLKI_DIVIDER_ACTUAL_STR` is `1`, per 1.5.2.

#### TC-PLL-015 — Maximum reference frequency 800 MHz `Radiant Compilation`

**Configuration**

- `gui_refclk_freq`=800.0 — the top of the range, per Rule 3
- `gui_config_mode`=`DIVIDER`, `gui_m_div`=2, `gui_n_div`=2, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 400 MHz, VCO 800 MHz, `clkop_o` 800 MHz. A reference divider of 2 is required here: 800 MHz exceeds the 500 MHz phase-detector ceiling for a device whose name does not end in `p`, and Rule 28 accordingly presets the reference divider to 2

**Pass Criteria**

- Generation and compilation complete with no DRC error; 800.0 is accepted, per Rule 3.
- `CLKI_FREQ` is 800.0 and the emitted `create_clock` period is `round(1000000 / 800.0) / 1000` = 1.25 ns, per 1.5.13.
- `CLKI_DIVIDER_ACTUAL_STR` is `2`, and `gui_phasedet_freq` reads 400.0 MHz — inside 18–500, per Rules 4 and 28.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

### G8 · Reference Divider — `gui_m_div`

Declared range 1–44 in divider mode (Rule 7). The reference frequency is varied alongside the divider so that each divider value keeps the phase-detector frequency inside 18–500 MHz: Rule 7's effective bounds are exactly those that keep the phase-detector frequency in range, and 44 is annotated in the source as the value that holds it at or above 18 MHz.

#### TC-PLL-016 — Reference divider 1 (minimum) `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 100 MHz, VCO 800 MHz, `clkop_o` 800 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKI_DIVIDER_ACTUAL_STR` is `1` — a plain integer, not offset — per 1.5.2.
- `gui_phasedet_freq` reads 100.0 MHz (100.0 ÷ 1), per 1.5.2 and Rule 4.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

#### TC-PLL-017 — Reference divider 22 (median) `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=440.0, `gui_m_div`=22, `gui_n_div`=40, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 20 MHz, VCO 800 MHz, `clkop_o` 800 MHz. The reference frequency is raised to 440 MHz because a divider of 22 needs at least 396 MHz to keep the phase-detector frequency at or above 18 MHz (Rules 4, 7)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKI_DIVIDER_ACTUAL_STR` is `22`, per 1.5.2.
- `gui_phasedet_freq` reads 20.0 MHz (440.0 ÷ 22), inside 18–500, per Rule 4.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

#### TC-PLL-018 — Reference divider 44 (maximum) `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=800.0, `gui_m_div`=44, `gui_n_div`=44, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 18.182 MHz, VCO 800 MHz, `clkop_o` 800 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error; 44 is accepted, per Rule 7.
- `CLKI_DIVIDER_ACTUAL_STR` is `44`, per 1.5.2.
- `gui_phasedet_freq` reads 18.18 MHz (800.0 ÷ 44) — at or above the 18 MHz floor, which Rule 7 records as the reason the declared maximum is 44.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

### G9 · Reference Clock Monitor — `gui_en_refclk_mon`, `gui_refclk_mon_freq`

The enable field is editable here because `LIFCL-40` does not end in `p` (Rule 18; see `SPEC-GAP-02`). The monitor-clock field is editable only while the monitor is on (spec 1.6 Reference Clock). Both tests avoid the ratios 0.3, 0.125, 0.06 and 0.03, which the `REF_COUNTS` table of spec 1.5.6 assigns to two rows at once — see `SPEC-GAP-08`.

#### TC-PLL-019 — Reference-clock monitor with the 3.2 MHz monitor clock `Both`

**Configuration**

- `gui_en_refclk_mon`=`True`, `gui_refclk_mon_freq`=`3P2`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=3, `gui_clk_op_div`=3
- Implied loop: phase-detector frequency 100 MHz, VCO 900 MHz, `clkop_o` 300 MHz. Division ratio (reference divider ÷ (feedback divider × feedback output divider)) = 1 ÷ (3 × 3) = 0.111, which falls strictly inside the 0.06 … 0.125 row of the `REF_COUNTS` table in 1.5.6

**Procedure**

1. Generate, compile, then simulate: release `rstn_i`, wait for `lock_o`, hold `refdetreset` low, and observe `refdetlos` while `clki_i` runs normally.

**Pass Criteria**

- `EN_REFCLK_MON` is 1 and the **monitor-capable** primitive is instantiated, per 1.5.1 and 1.5.6.
- `refdetreset` and `refdetlos` are connected rather than tied off and dangling, per 1.3 and 1.5.6.
- `REF_OSC_CTRL` selects the 3.2 MHz monitor oscillator, per 1.5.6.
- `REF_COUNTS` is `2`, the value the 0.06 … 0.125 row of the table in 1.5.6 assigns to the ratio 0.111.
- In simulation, with `clki_i` running, `refdetlos` stays deasserted for the rest of the run after lock — the reference is present, per 1.5.6.

#### TC-PLL-020 — Reference-clock monitor with the 1.0 MHz monitor clock `Radiant Compilation`

**Configuration**

- `gui_en_refclk_mon`=`True`, `gui_refclk_mon_freq`=`1P0`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=200.0, `gui_m_div`=2, `gui_n_div`=3, `gui_clk_op_div`=3
- Implied loop: phase-detector frequency 100 MHz, VCO 900 MHz, `clkop_o` 300 MHz. Division ratio = 2 ÷ (3 × 3) = 0.222, strictly inside the 0.125 … 0.3 row of the `REF_COUNTS` table in 1.5.6

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `REF_OSC_CTRL` selects the 1.0 MHz monitor oscillator, per 1.5.6.
- `REF_COUNTS` is `1`, the value the 0.125 … 0.3 row of the table in 1.5.6 assigns to the ratio 0.222 — a different row from TC-PLL-019, so the pair exercises two rows of that derivation.
- `EN_REFCLK_MON` is 1 and the monitor-capable primitive is instantiated, per 1.5.1.

### G10 · Feedback Mode — `gui_fbk_mode` — Requires fractional-N, spread spectrum and the user feedback clock all disabled

Twelve options, `CLKOP` … `CLKOS5` and `INTCLKOP` … `INTCLKOS5` (spec 1.6 Feedback). The offered list is rebuilt from the outputs that are enabled and not bypassed (Rule 12), so each test enables the outputs its selections need. All three tests share one loop arithmetic: reference frequency 100 MHz, reference divider 1, feedback divider 1 and **every** output divider 8. Because the output divider of whichever output is selected sits inside the loop (spec 1.5.2, 1.5.3), that single divider set yields a 100 MHz feedback clock and an 800 MHz VCO for *any* of the twelve selections, so the iterations differ only in the field under test.

#### TC-PLL-021 — Feedback from CLKOP and from INTCLKOP `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8
- Implied loop: phase-detector frequency 100 MHz, feedback clock 100 MHz, VCO 800 MHz, `clkop_o` 100 MHz — inside the widened 10–800 MHz feedback-source range (Rule 10)
- Iterate `gui_fbk_mode` over `CLKOP`, `INTCLKOP`

**Procedure**

1. For each selection, set the field, press **Calculate**, generate, compile and simulate `clkop_o` and `lock_o`.

| Iteration | `gui_fbk_mode` | Expected feedback source (1.5.3) |
|---|---|---|
| 1 | `CLKOP` | `clkop_o`, taken after the output divider |
| 2 | `INTCLKOP` | the primary internal divider tap of the primitive |

**Pass Criteria**

- Both iterations generate and compile with no DRC error, and `lock_o` asserts in both.
- `FBK_MODE` equals the selected option in each iteration, and the wrapper's feedback multiplexer selects the matching arm, per 1.5.3.
- In both iterations the primary output's enable is forced on and its bypass off, and its static phase-shift and clock-enable-port fields are read-only, per 1.5.3 and Rules 13, 23.
- The internal feedback delay code is derived from the feedback output's divider value — 8 in both iterations — per 1.5.3.
- `clkop_o` measures 100 MHz in both iterations, per 1.5.2.

#### TC-PLL-022 — Feedback from CLKOS / INTCLKOS and CLKOS2 / INTCLKOS2 `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1
- `gui_clk_os_en`=`True`, `gui_clk_s2_en`=`True`; `gui_clk_op_div`=8, `gui_clk_os_div`=8, `gui_clk_s2_div`=8
- Implied loop: VCO 800 MHz, all three outputs 100 MHz
- Iterate `gui_fbk_mode` over `CLKOS`, `INTCLKOS`, `CLKOS2`, `INTCLKOS2`

**Procedure**

1. Before each iteration, confirm the offered option list contains only selections for outputs that are enabled and not bypassed (Rule 12).
2. For each selection, generate and compile.

| Iteration | `gui_fbk_mode` | Expected feedback source (1.5.3) |
|---|---|---|
| 1 | `CLKOS` | `clkos_o` after its output divider |
| 2 | `INTCLKOS` | the CLKOS internal divider tap |
| 3 | `CLKOS2` | `clkos2_o` after its output divider |
| 4 | `INTCLKOS2` | the CLKOS2 internal divider tap |

**Pass Criteria**

- All four iterations generate and compile with no DRC error.
- `FBK_MODE` equals the selected option in each iteration, per 1.5.3.
- In each iteration the selected output's enable parameter is 1 and its bypass parameter 0, and that output's static phase-shift and clock-enable-port fields are read-only while the other outputs' remain editable, per 1.5.3 and Rules 13, 23.
- The offered option list excludes any disabled output — with only CLKOS and CLKOS2 enabled alongside the always-present primary, no `CLKOS3` … `CLKOS5` selection is offered, per Rule 12.
- `DIVOP_ACTUAL_STR`, `DIVOS_ACTUAL_STR` and `DIVOS2_ACTUAL_STR` are all `7` (8 − 1), per 1.5.2.

#### TC-PLL-023 — Feedback from CLKOS3 / INTCLKOS3, CLKOS4 / INTCLKOS4 and CLKOS5 / INTCLKOS5 `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1
- `gui_clk_s3_en`=`True`, `gui_clk_s4_en`=`True`, `gui_clk_s5_en`=`True`; `gui_clk_op_div`=8, `gui_clk_s3_div`=8, `gui_clk_s4_div`=8, `gui_clk_s5_div`=8
- Implied loop: VCO 800 MHz, all four enabled outputs 100 MHz
- Iterate `gui_fbk_mode` over `CLKOS3`, `INTCLKOS3`, `CLKOS4`, `INTCLKOS4`, `CLKOS5`, `INTCLKOS5`

**Procedure**

1. For each selection, generate and compile.

| Iteration | `gui_fbk_mode` | Expected feedback source (1.5.3) |
|---|---|---|
| 1 | `CLKOS3` | `clkos3_o` after its output divider |
| 2 | `INTCLKOS3` | the CLKOS3 internal divider tap |
| 3 | `CLKOS4` | `clkos4_o` after its output divider |
| 4 | `INTCLKOS4` | the CLKOS4 internal divider tap |
| 5 | `CLKOS5` | `clkos5_o` after its output divider |
| 6 | `INTCLKOS5` | the CLKOS5 internal divider tap |

**Pass Criteria**

- All six iterations generate and compile with no DRC error.
- `FBK_MODE` equals the selected option in each iteration, per 1.5.3.
- In each iteration the selected output's enable parameter is 1 and its bypass parameter 0, and its phase-shift and clock-enable-port fields are read-only, per 1.5.3 and Rules 13, 23.
- Taken with TC-PLL-021 and TC-PLL-022, all twelve declared options of `gui_fbk_mode` have been generated and compiled.

### G11 · Feedback Divider — `gui_n_div`

Declared 1–128 for integer-N and 16–128 for fractional-N or spread spectrum, narrowed so the VCO stays inside 800–1600 MHz (Rule 5). On this target the narrowing is the binding constraint and the declared ceiling of 128 is unreachable: with an output-derived feedback source the feedback clock equals phase-detector frequency × feedback divider and must not exceed 800 MHz (Rule 10), which caps the divider at 44 when the phase-detector frequency is at its 18 MHz floor. The reachable maxima are therefore **44** in integer-N and **88** in fractional-N. See `SPEC-GAP-07`.

#### TC-PLL-024 — Feedback divider 1 (integer-N minimum) `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8
- Implied loop: phase-detector frequency 100 MHz, feedback clock 100 MHz, VCO 800 MHz, `clkop_o` 100 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error; 1 is accepted, per Rule 5.
- `FBCLK_DIVIDER_ACTUAL_STR` is `1` — a plain integer, not offset — per 1.5.2.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

#### TC-PLL-025 — Feedback divider 22 (integer-N median) `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=4, `gui_n_div`=22, `gui_clk_op_div`=2
- Implied loop: phase-detector frequency 25 MHz, feedback clock 550 MHz, VCO 1100 MHz, `clkop_o` 550 MHz — inside the widened 10–800 MHz feedback-source range (Rule 10)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `FBCLK_DIVIDER_ACTUAL_STR` is `22`, per 1.5.2.
- `gui_vco_freq` reads 1100.0 MHz — mid-window in 800–1600 — per Rule 9.
- `DIVOP_ACTUAL_STR` is `1` (2 − 1), per 1.5.2.

#### TC-PLL-026 — Feedback divider 44 (integer-N reachable maximum) `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=800.0, `gui_m_div`=44, `gui_n_div`=44, `gui_clk_op_div`=1
- Implied loop: phase-detector frequency 18.182 MHz, feedback clock 800 MHz — exactly the ceiling of the widened feedback-source range (Rule 10) — VCO 800 MHz, `clkop_o` 800 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `FBCLK_DIVIDER_ACTUAL_STR` is `44`, per 1.5.2.
- `gui_vco_freq` reads 800.0 MHz, at the floor of 800–1600, per Rule 9.
- `clkop_o` measures 800 MHz in simulation and `lock_o` asserts.
- Raising the field above 44 with this reference frequency is not offered, because the narrowed range of Rule 5 and the 800 MHz output ceiling of Rule 10 both bind here.

#### TC-PLL-027 — Fractional-N feedback divider floor 16 and reachable ceiling 88 `Radiant Compilation`

**Configuration**

- `gui_en_frac_n`=`True`, `gui_config_mode`=`DIVIDER`, `gui_frac_n_div`=0
- Iterate the two rows below

| Iteration | `gui_refclk_freq` | `gui_m_div` | `gui_n_div` | `gui_clk_op_div` | Phase detector | VCO | `clkop_o` |
|---|---|---|---|---|---|---|---|
| 1 | 100.0 | 1 | **16** | 16 | 100 MHz | 1600 MHz | 100 MHz |
| 2 | 18.0 | 1 | **88** | 2 | 18 MHz | 1584 MHz | 792 MHz |

**Pass Criteria**

- Both iterations generate and compile with no DRC error.
- Iteration 1: `FBCLK_DIVIDER_ACTUAL_STR` is `16` — the fractional-N floor of Rule 5 — and `gui_vco_freq` reads 1600.0 MHz, the ceiling of Rule 9.
- Iteration 2: `FBCLK_DIVIDER_ACTUAL_STR` is `88` and `gui_vco_freq` reads 1584.0 MHz, inside Rule 9.
- In both iterations `FRAC_N_EN` is 1, `SSC_F_CODE_STR` is 0 (the fractional word is 0), and `SSC_N_CODE_STR` is the 9-bit binary form of the integer divider, per 1.5.4.
- In both iterations the phase-detector frequency shown by `gui_phasedet_freq` lies inside the narrowed 18–100 MHz fractional-N range, per Rule 4.

### G12 · Fractional Word — `gui_frac_n_div` — Requires `gui_en_frac_n` = `True` and divider mode

Declared 0–4095 over a denominator of 4096, narrowed at the extremes of the feedback-divider range so the VCO stays in window (Rule 8). All three tests use feedback divider 45 at an 18 MHz phase-detector frequency, where the whole 0–4095 span keeps the VCO between 810 and 828 MHz and no narrowing applies.

#### TC-PLL-028 — Fractional word 0 (minimum) `Radiant Compilation`

**Configuration**

- `gui_en_frac_n`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=18.0, `gui_m_div`=1, `gui_n_div`=45, `gui_frac_n_div`=0, `gui_clk_op_div`=2
- Implied loop: phase-detector frequency 18 MHz, effective feedback divider 45.000, VCO 810 MHz, `clkop_o` 405 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error; 0 is accepted, per Rule 8.
- `SSC_F_CODE_STR` is `0`, per 1.5.4.
- `gui_vco_freq` reads 810.0 MHz, inside 800–1600, per Rule 9.
- `fbclk_divider_decimal_disp` shows the feedback divider including its fractional part, i.e. 45.0, per spec 1.6 Feedback.

#### TC-PLL-029 — Fractional word 2048 (median) `Both`

**Configuration**

- As TC-PLL-028 but `gui_frac_n_div`=2048
- Implied loop: effective feedback divider 45.500, VCO 819 MHz, `clkop_o` 409.5 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `SSC_F_CODE_STR` is 2048 packed into 15 bits by appending three zero bits — decimal 16384 — per 1.5.4.
- `gui_vco_freq` reads 819.0 MHz, per Rule 9.
- `fbclk_divider_decimal_disp` shows 45.5, per spec 1.6 Feedback.
- In simulation `lock_o` asserts and `clkop_o` measures 409.5 MHz — evidence that a fractional feedback divider is in force, since no integer divider at this phase-detector frequency and output divider produces that frequency, per 1.5.2 and 1.5.4.

#### TC-PLL-030 — Fractional word 4095 (maximum) `Radiant Compilation`

**Configuration**

- As TC-PLL-028 but `gui_frac_n_div`=4095
- Implied loop: effective feedback divider 45.99976, VCO 827.996 MHz, `clkop_o` 413.998 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error; 4095 is accepted as the top of the declared span, per Rule 8.
- `SSC_F_CODE_STR` is 4095 packed into 15 bits by appending three zero bits — decimal 32760 — per 1.5.4.
- `gui_vco_freq` reads 827.99 MHz (to the precision the field displays), inside 800–1600, per Rule 9.
- `SSC_N_CODE_STR` is the 9-bit binary form of 45 — the integer part is unchanged by the fractional word, per 1.5.4.

### G13 · Output Clock Enables — `gui_clk_os_en` … `gui_clk_s5_en`

The primary output has no enable field: spec 1.1 records it as always present. The five secondary enables default to `False`, and TC-PLL-001 covers that value for all five.

#### TC-PLL-031 — All five secondary outputs enabled `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1
- `gui_clk_os_en`=`gui_clk_s2_en`=`gui_clk_s3_en`=`gui_clk_s4_en`=`gui_clk_s5_en`=`True`
- `gui_clk_op_div`=`gui_clk_os_div`=`gui_clk_s2_div`=`gui_clk_s3_div`=`gui_clk_s4_div`=`gui_clk_s5_div`=8
- Implied loop: VCO 800 MHz, all six outputs 100 MHz

**Procedure**

1. Generate, compile, then simulate all six output clocks and `lock_o`.

**Pass Criteria**

- `CLKOS_EN` … `CLKOS5_EN` are all 1, so `clkos_o` … `clkos5_o` are real outputs rather than dangling, per 1.3 and spec 1.6 Secondary Clock Output.
- All six output-divider parameters are `7` (8 − 1), per 1.5.2.
- In simulation all six output clocks measure 100 MHz and `lock_o` asserts.
- With no enable port requested, each secondary output's internal enable attribute is armed — the requirement being that the output is enabled at all, per the asymmetry stated in 1.5.7 — so each clock runs continuously with no external enable.

#### TC-PLL-032 — Selective enable: CLKOS3 and CLKOS5 only `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1
- `gui_clk_s3_en`=`gui_clk_s5_en`=`True`; `gui_clk_os_en`=`gui_clk_s2_en`=`gui_clk_s4_en`=`False`
- `gui_clk_op_div`=`gui_clk_s3_div`=`gui_clk_s5_div`=8 — VCO 800 MHz, three outputs at 100 MHz

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKOS3_EN` and `CLKOS5_EN` are 1; `CLKOS_EN`, `CLKOS2_EN` and `CLKOS4_EN` are 0, per spec 1.6.
- `clkos_o`, `clkos2_o` and `clkos4_o` are dangling and `clkos3_o`, `clkos5_o` are driven, per 1.3.
- The whole 43-port boundary is still declared on the generated module — the ports of unselected features are tied off or left dangling rather than removed, per 1.1 and 1.3.
- No field of a disabled output is editable in the dialog: the divider, frequency, tolerance, phase, bypass and clock-enable-port fields of CLKOS, CLKOS2 and CLKOS4 are all read-only, per spec 1.6 and Rule 23.

### G14 · Output Bypass — `gui_clk_op_byp` … `gui_clk_s5_byp`

A bypassed output carries the reference clock instead of the divided VCO (spec 1.5.2). An output may not be bypassed while it is the feedback source, and no output may be bypassed in fractional-N or spread-spectrum mode (Rules 13, 14) — so each test below routes the feedback around whichever output it bypasses.

#### TC-PLL-033 — Primary output bypassed to the reference clock `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1
- `gui_fbk_mode`=`INTCLKOS`, `gui_clk_os_en`=`True`, `gui_clk_os_div`=8 — feedback clock 100 MHz, VCO 800 MHz, `clkos_o` 100 MHz
- `gui_clk_op_byp`=`True`

**Procedure**

1. Confirm the primary bypass field is editable — it is, because the primary is not the feedback source here and neither fractional-N nor spread spectrum nor the user feedback clock is enabled (spec 1.6 Primary Clock Output).
2. Generate, compile, then simulate `clkop_o`, `clkos_o` and `lock_o`.

**Pass Criteria**

- `CLKOP_BYPASS` is 1 and the corresponding output-select attribute on the primitive is turned on, routing the reference clock to that output, per 1.5.2.
- The primary output's frequency and divider fields are read-only while it is bypassed, per spec 1.6.
- In simulation `clkop_o` measures 100 MHz — the **reference** frequency, per 1.5.2 — and `clkos_o` measures 100 MHz from the divided VCO. Both are 100 MHz here by construction; the distinguishing observation is that `clkop_o` remains present and at the reference frequency while `lock_o` is still deasserted early in the run, whereas `clkos_o` only becomes correct once the loop locks.
- `CLKOS_EN` is 1 and `CLKOS_BYPASS` is 0 — the feedback output is forced enabled and un-bypassed, per Rule 13.

#### TC-PLL-034 — All five secondary outputs bypassed `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz, `clkop_o` 100 MHz
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_os_byp`=`gui_clk_s2_byp`=`gui_clk_s3_byp`=`gui_clk_s4_byp`=`gui_clk_s5_byp`=`True`

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKOS_BYPASS` … `CLKOS5_BYPASS` are all 1 and `CLKOP_BYPASS` is 0, per 1.5.2.
- Each bypassed output's frequency, divider, tolerance, phase, trim-enable and clock-enable-port fields are read-only, per spec 1.6 and Rules 23, 24.
- The primary output remains enabled and un-bypassed as the feedback source, per Rule 13 — so this configuration does not reach the all-disabled-or-bypassed short circuit of Rule 27 (see Exclusions).

#### TC-PLL-035 — Mixed bypass: CLKOS2 and CLKOS4 bypassed, CLKOS3 and CLKOS5 divided `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz, `clkop_o` 100 MHz
- `gui_clk_s2_en`=`gui_clk_s3_en`=`gui_clk_s4_en`=`gui_clk_s5_en`=`True`
- `gui_clk_s2_byp`=`gui_clk_s4_byp`=`True`; `gui_clk_s3_div`=4 (200 MHz), `gui_clk_s5_div`=16 (50 MHz)

**Procedure**

1. Generate, compile, then simulate `clkop_o`, `clkos2_o`, `clkos3_o`, `clkos4_o`, `clkos5_o` and `lock_o`.

**Pass Criteria**

- `CLKOS2_BYPASS` and `CLKOS4_BYPASS` are 1; `CLKOS3_BYPASS` and `CLKOS5_BYPASS` are 0, per 1.5.2.
- `DIVOS3_ACTUAL_STR` is `3` (4 − 1) and `DIVOS5_ACTUAL_STR` is `15` (16 − 1), per 1.5.2.
- In simulation `clkos2_o` and `clkos4_o` each measure 100 MHz, the reference frequency, per 1.5.2.
- In simulation `clkos3_o` measures 200 MHz and `clkos5_o` measures 50 MHz — VCO ÷ divider — per 1.5.2, confirming bypass is a strictly per-output property.
- `lock_o` asserts and stays asserted.

### G15 · Output Frequency — `gui_clk_op_freq` … `gui_clk_s5_freq` — Frequency mode only

Legal range 6.25–800 MHz, widened to 10–800 MHz for whichever output is the feedback source (Rule 10). The median value tested is 100 MHz, which is also each field's default. Every requested frequency in this group is exactly achievable from an 800 MHz VCO, so the tolerance stays at 0.0 and Rule 1 is satisfied without relying on a search outcome.

#### TC-PLL-036 — Maximum primary output frequency with minimum secondary frequencies `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, `gui_fbk_mode`=`CLKOP`
- `gui_clk_op_freq`=800 — the top of the widened feedback-source range (Rule 10)
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_os_freq`=`gui_clk_s2_freq`=`gui_clk_s3_freq`=`gui_clk_s4_freq`=`gui_clk_s5_freq`=6.25 — the bottom of the ordinary range (Rule 10)
- All six tolerances 0.0. Achievable set: VCO 800 MHz, primary divider 1, secondary dividers 128

**Pass Criteria**

- Generation and compilation complete with no Rule 1 DRC error.
- `CLKOP_FREQ_ACTUAL` is 800 and `CLKOS_FREQ_ACTUAL` … `CLKOS5_FREQ_ACTUAL` are each 6.25, per 1.5.2.
- Every `gui_clk_*_ppm` display reads 0 — each request is met exactly, per Rule 1.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.
- The primary output is accepted at 800 MHz *as the feedback source*, confirming its range is the widened 10–800 MHz variant, per Rule 10.

#### TC-PLL-037 — Minimum primary output frequency with CLKOS at maximum as feedback source `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, `gui_fbk_mode`=`CLKOS`
- `gui_clk_op_freq`=6.25 — the bottom of the ordinary range; legal because the primary is *not* the feedback source here (Rule 10)
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_os_freq`=800, `gui_clk_s2_freq`=`gui_clk_s3_freq`=`gui_clk_s4_freq`=`gui_clk_s5_freq`=6.25
- All applicable tolerances 0.0. Achievable set: VCO 800 MHz, CLKOS divider 1, primary and remaining secondary dividers 128

**Pass Criteria**

- Generation and compilation complete with no Rule 1 DRC error.
- `CLKOP_FREQ_ACTUAL` is 6.25 and `CLKOS_FREQ_ACTUAL` is 800, per 1.5.2.
- Every `gui_clk_*_ppm` display reads 0, per Rule 1.
- `CLKOP_BYPASS` is 0 and the primary output's phase-shift and clock-enable-port fields are editable, while CLKOS's are read-only — CLKOS is the feedback source, per Rule 23.
- `CLKOS_EN` is 1 and `CLKOS_BYPASS` is 0, forced by Rule 13.

#### TC-PLL-038 — Median output frequency 100 MHz on all six outputs `Both`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, feedback via the default primary selection
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six frequency fields 100, all six tolerances 0.0
- Achievable set: VCO 800 MHz, all six dividers 8

**Procedure**

1. Generate, compile, then simulate all six output clocks and `lock_o`.

**Pass Criteria**

- Generation and compilation complete with no Rule 1 DRC error, and every `gui_clk_*_ppm` reads 0.
- All six `CLKO*_FREQ_ACTUAL` parameters are 100, per 1.5.2.
- In simulation all six output clocks measure 100 MHz and `lock_o` asserts.
- Each output port publishes its frequency to the tool through its `clock_param` extension naming that output's `*_FREQ_ACTUAL` parameter, per 1.3 — the IP's own constraints declare only the reference clock, per 1.5.13 *Constraints applied*.

#### TC-PLL-039 — Maximum output frequency 800 MHz on all six outputs `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, `gui_fbk_mode`=`CLKOP`
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six frequency fields 800, all six tolerances 0.0
- Achievable set: VCO 800 MHz, all six dividers 1

**Pass Criteria**

- Generation and compilation complete with no Rule 1 DRC error.
- All six `CLKO*_FREQ_ACTUAL` parameters are 800 — the ceiling of Rule 10 for both the feedback source and the other five outputs.
- Every `gui_clk_*_ppm` display reads 0, per Rule 1.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

### G16 · Output Divider — `gui_clk_op_div` … `gui_clk_s5_div` — Divider mode only

Declared 1–128 per output, narrowed so the resulting output frequency stays inside 6.25–800 MHz for the VCO in force, and for the feedback output narrowed instead by the 800–1600 MHz VCO window (Rule 6). All three tests hold the VCO at a value that makes the extreme divider legal on every output at once.

#### TC-PLL-040 — Primary divider 1 with all secondary dividers 128 `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8 — feedback via `INTCLKOP`, feedback clock 800 MHz, VCO 800 MHz
- `gui_clk_op_div`=1 (`clkop_o` 800 MHz); `gui_clk_os_en` … `gui_clk_s5_en`=`True`, all five secondary dividers 128 (each 6.25 MHz)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `DIVOP_ACTUAL_STR` is `0` — the divider 1 minus one — per 1.5.2. This is the encoding's floor and the clearest demonstration of the minus-one offset.
- `DIVOS_ACTUAL_STR` … `DIVOS5_ACTUAL_STR` are each `127` (128 − 1), per 1.5.2.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9; the resulting 6.25 MHz secondary outputs sit exactly at the floor of Rule 6's 6.25–800 MHz window.
- The primary output, as feedback source, is accepted at 800 MHz under the widened 10–800 MHz range of Rule 10.

#### TC-PLL-041 — Primary divider 128 with all secondary dividers 1 `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8, `gui_fbk_mode`=`INTCLKOS`
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_os_div`=1 — CLKOS is the feedback source, feedback clock 800 MHz, VCO 800 MHz
- `gui_clk_op_div`=128 (`clkop_o` 6.25 MHz); `gui_clk_s2_div`=`gui_clk_s3_div`=`gui_clk_s4_div`=`gui_clk_s5_div`=1 (each 800 MHz)
- The primary output can take the divider ceiling here precisely because it is not the feedback source: 6.25 MHz is legal on an ordinary output but below the 10 MHz feedback-source floor (Rule 10)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `DIVOP_ACTUAL_STR` is `127` (128 − 1) and `DIVOS_ACTUAL_STR` … `DIVOS5_ACTUAL_STR` are each `0` (1 − 1), per 1.5.2.
- `CLKOP_FREQ_ACTUAL` is 6.25, at the floor of Rule 6's window, and the four non-feedback secondary outputs report 800 — its ceiling.
- `gui_vco_freq` reads 800.0 MHz, per Rule 9.

#### TC-PLL-042 — All six output dividers at 64 (median) `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=4, `gui_n_div`=1, `gui_fbk_mode`=`INTCLKOS`
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 64
- Implied loop: phase-detector frequency 25 MHz, feedback clock 25 MHz — inside the widened 10–800 MHz range (Rule 10) — VCO 1600 MHz, all six outputs 25 MHz

**Procedure**

1. Generate, compile, then simulate all six output clocks and `lock_o`.

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- All six output-divider parameters are `63` (64 − 1), per 1.5.2.
- `gui_vco_freq` reads 1600.0 MHz, the ceiling of Rule 9.
- In simulation all six output clocks measure 25 MHz and `lock_o` asserts.

### G17 · Output Tolerance — `gui_clk_op_tol` … `gui_clk_s5_tol` — Frequency mode only

Eight options per output (spec 1.6). Both tests request 100 MHz on all six outputs, which is exactly achievable from an 800 MHz VCO with a divider of 8, so every tolerance option is legal and Rule 1 is satisfied at each of them without depending on a search outcome. Rule 1 also records that a tolerance of 0 is replaced internally by 1e-6 % before the comparison, so an exact request is still checkable at the 0.0 setting.

#### TC-PLL-043 — Tolerance sweep 0.0 / 0.1 / 0.2 / 0.5 on all six outputs `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=100.0, feedback via the default primary selection
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six frequency fields 100
- Iterate all six tolerance fields together over 0.0, 0.1, 0.2, 0.5

**Procedure**

1. For each tolerance in the list, set all six tolerance fields to it, press **Calculate**, generate and compile.

**Pass Criteria**

- All four iterations generate and compile with no Rule 1 DRC error.
- In every iteration each `gui_clk_*_ppm` display reads 0 and each `CLKO*_FREQ_ACTUAL` is 100 — the achieved frequency equals the request, so the difference is inside the tolerance at every setting, per Rule 1.
- In every iteration the tolerance fields are editable and the divider fields read-only, per Rule 15.
- The 0.0 iteration passes, confirming the internal 1e-6 % substitution Rule 1 describes: a zero tolerance does not make an exact request unachievable.

#### TC-PLL-044 — Tolerance sweep 1.0 / 2.0 / 5.0 / 10.0 on all six outputs `Radiant Compilation`

**Configuration**

- As TC-PLL-043, iterating all six tolerance fields together over 1.0, 2.0, 5.0, 10.0

**Procedure**

1. For each tolerance in the list, set all six tolerance fields to it, press **Calculate**, generate and compile.

**Pass Criteria**

- All four iterations generate and compile with no Rule 1 DRC error.
- In every iteration each `gui_clk_*_ppm` display reads 0 and each `CLKO*_FREQ_ACTUAL` is 100, per Rule 1.
- Taken with TC-PLL-043, all eight declared tolerance options have been exercised on all six outputs.
### G18 · Static Phase Shift — `gui_clk_op_phase` … `gui_clk_s5_phase`

Eight 45° steps per output (spec 1.6). The field is read-only on whichever output is the feedback source (Rule 23), so all three tests select the **external** feedback clock: with `USERFBCLK` no output is the feedback source, and all six phase fields are editable at once. Each test therefore covers its phase values on all six outputs in one pass.

The shared loop is reference frequency 100 MHz, reference divider 1, feedback divider 8 and every output divider **1**, giving an 800 MHz VCO and six 800 MHz outputs. The primary divider is 1 deliberately: it makes the VCO 800 MHz under either reading of the loop equation of 1.5.2, so these tests do not depend on the unresolved external-feedback arithmetic (`SPEC-GAP-03`). `usr_fbclk_i` is driven at 800 MHz (`SPEC-GAP-13`).

#### TC-PLL-045 — Static phase shift 90 and 270 degrees on all six outputs `Both`

**Configuration**

- `gui_en_usr_fbk`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 1 — all six outputs 800 MHz
- Iterate all six phase fields together over 90, 270
- Stimulus: `clki_i` at 100 MHz, `usr_fbclk_i` at 800 MHz

**Procedure**

1. For each phase value, set all six phase fields to it, press **Calculate**, generate and compile.
2. Simulate each iteration: wait for `lock_o`, then measure the edge offset of each of the six output clocks against `clkop_o` of the 0° reference run (TC-PLL-046 iteration 1), expressed as a fraction of the 1.25 ns output period.

| Iteration | All six phase fields | Expected shift |
|---|---|---|
| 1 | 90 | one quarter period |
| 2 | 270 | three quarters of a period |

**Pass Criteria**

- Both iterations generate and compile with no DRC error, and `lock_o` asserts in both.
- In each iteration every `CLKO*_PHASE_ACTUAL` parameter equals the requested shift, per spec 1.6.
- In each iteration the per-output delay and phase attributes (`DELA`/`PHIA` for the primary, `DELB`/`PHIB` … `DELF`/`PHIF` for CLKOS … CLKOS5) are populated with the code pair the plugin resolved from the requested shift and that output's divider value, and every delay code is below the delay limit of 128, per 1.5.7.
- In simulation the measured edge offset of each output matches the requested shift to within one simulation time step: a quarter period at 90°, three quarters at 270°, per 1.5.7.
- All six phase fields are editable throughout, because no output is the feedback source in an external-feedback configuration, per Rule 23.

#### TC-PLL-046 — Static phase shift 0, 45 and 135 degrees on all six outputs `Radiant Compilation`

**Configuration**

- As TC-PLL-045, iterating all six phase fields together over 0, 45, 135

**Procedure**

1. For each phase value, set all six phase fields to it, press **Calculate**, generate and compile.

**Pass Criteria**

- All three iterations generate and compile with no DRC error.
- Every `CLKO*_PHASE_ACTUAL` parameter equals the requested shift in each iteration, per spec 1.6.
- Every per-output delay and phase attribute pair is populated and every delay code is below 128, per 1.5.7.
- In the 0° iteration the phase codes are the unshifted pair, giving the reference run that TC-PLL-045's measurements are taken against.

#### TC-PLL-047 — Static phase shift 180, 225 and 315 degrees on all six outputs `Radiant Compilation`

**Configuration**

- As TC-PLL-045, iterating all six phase fields together over 180, 225, 315

**Procedure**

1. For each phase value, set all six phase fields to it, press **Calculate**, generate and compile.

**Pass Criteria**

- All three iterations generate and compile with no DRC error.
- Every `CLKO*_PHASE_ACTUAL` parameter equals the requested shift in each iteration, per spec 1.6.
- Every per-output delay and phase attribute pair is populated and every delay code is below the delay limit of 128 — including any shift the plugin had to resolve through the complementary direction, which 1.5.7 describes as the fallback when no code pair produces the shift directly.
- Taken with TC-PLL-045 and TC-PLL-046, all eight declared phase options have been exercised on all six outputs.

### G19 · Duty-Cycle Trim — `gui_clk_op_trim_en`, `gui_clk_op_trim_mode`, `gui_clk_op_trim_mult`, `gui_clk_os_trim_en`, `gui_clk_os_trim_mode`, `gui_clk_os_trim_mult` — Primary and first secondary outputs only

Trim exists only on CLKOP and CLKOS (Rule 24). The mode and multiplier fields are editable only while that output's trim enable is on and the output is not bypassed (Rule 24). Spec 1.5.7 describes the trim attribute as five bits built from a leading edge bit followed by the three-bit multiplier code, which accounts for four — see `SPEC-GAP-14` — so the criteria below assert the leading bit and the multiplier code, not the full five-bit word. The `False` value of both trim-enable fields is covered by TC-PLL-001.

#### TC-PLL-048 — Rising-edge duty trim with delay multipliers 0 and 2 `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz, `clkop_o` 100 MHz
- `gui_clk_os_en`=`True`, `gui_clk_os_div`=8 — `clkos_o` 100 MHz
- `gui_clk_op_trim_en`=`gui_clk_os_trim_en`=`True`; `gui_clk_op_trim_mode`=`gui_clk_os_trim_mode`=`Rising`
- Iterate `gui_clk_op_trim_mult` and `gui_clk_os_trim_mult` together over `0`, `2`

**Procedure**

1. Confirm the mode and multiplier fields become editable only once the trim-enable field is set (Rule 24), and that no trim field exists for CLKOS2 … CLKOS5.
2. For each multiplier, set both multiplier fields, press **Calculate**, generate and compile.
3. Simulate each iteration: wait for `lock_o`, then measure the high and low times of `clkop_o` and `clkos_o`.

| Iteration | Both multiplier fields | Expected multiplier code (1.5.7) |
|---|---|---|
| 1 | `0` | `000` |
| 2 | `2` | `010` |

**Pass Criteria**

- Both iterations generate and compile with no DRC error, and `lock_o` asserts in both.
- `TRIM_EN_P` and `TRIM_EN_S` are both 1, so the trim block is used rather than bypassed on each of the two outputs, per 1.5.7.
- `CLKOP_TRIM_MODE` and `CLKOS_TRIM_MODE` carry the rising-edge selection, and the leading bit of `CLKOP_TRIM` and `CLKOS_TRIM` is `1` for a rising-edge trim, per 1.5.7.
- The three multiplier bits of `CLKOP_TRIM` and `CLKOS_TRIM` are `000` in iteration 1 and `010` in iteration 2, per the mapping in spec 1.6 Primary Clock Output.
- No trim field is offered for CLKOS2 … CLKOS5, per Rule 24.
- In simulation the measured high and low times of `clkop_o` and `clkos_o` are identical between the two iterations only if the multiplier has no effect; the pass condition is that the two iterations differ in the measured duty of both trimmed outputs, since iteration 1 applies no delay and iteration 2 applies twice the unit delay, per 1.5.7. The absolute delay figure is not asserted — it is a property of the hard block (spec 1.5.13).

#### TC-PLL-049 — Falling-edge duty trim with delay multipliers 1 and 4 `Radiant Compilation`

**Configuration**

- As TC-PLL-048 but `gui_clk_op_trim_mode`=`gui_clk_os_trim_mode`=`Falling`
- Iterate `gui_clk_op_trim_mult` and `gui_clk_os_trim_mult` together over `1`, `4`

**Procedure**

1. For each multiplier, set both multiplier fields, press **Calculate**, generate and compile.

| Iteration | Both multiplier fields | Expected multiplier code (1.5.7) |
|---|---|---|
| 1 | `1` | `001` |
| 2 | `4` | `100` |

**Pass Criteria**

- Both iterations generate and compile with no DRC error.
- `CLKOP_TRIM_MODE` and `CLKOS_TRIM_MODE` carry the falling-edge selection, and the leading bit of `CLKOP_TRIM` and `CLKOS_TRIM` is `0` for a falling-edge trim, per 1.5.7.
- The three multiplier bits are `001` in iteration 1 and `100` in iteration 2, per the mapping in spec 1.6.
- Taken with TC-PLL-048, both trim modes and all four multiplier options have been exercised on both trim-capable outputs.

### G20 · Reference Clock I/O Pin and I/O Standard — `gui_en_refclk_pin`, `gui_refclk_io_type`

The I/O-standard field is editable only when the reference clock comes from a device pin (Rule 19); without the pin option it is read-only at its `LVDS` default and the constraint script emits no I/O-standard assignment (spec 1.5.5). The `False` value of the pin field is covered by TC-PLL-001.

#### TC-PLL-050 — Reference clock taken from a device pin with the default LVDS standard `Both`

**Configuration**

- `gui_en_refclk_pin`=`True`, `gui_refclk_io_type`=`LVDS`; all other fields at their defaults (as TC-PLL-001)

**Procedure**

1. Confirm the I/O-standard field becomes editable once the pin option is set (Rule 19).
2. Generate, compile, then simulate `clkop_o` and `lock_o`.

**Pass Criteria**

- `PLL_REFCLK_FROM_PIN` is 1 and the reference clock is routed through the bidirectional device-pin buffer configured as an input — its output enable held off and its data input tied low — per 1.5.5.
- `IO_TYPE` is `LVDS`, per spec 1.6 Optional Ports.
- The emitted constraints contain both the `create_clock` on `clki_i` **and** the I/O-standard assignment on `clki_i` setting the buffer to `LVDS`; the assignment is present only because the pin option is on, per 1.5.5 and 1.5.13 *Constraints applied*. Comparing against TC-PLL-001, whose constraint file carries the `create_clock` alone, is the check for the conditional emission.
- The rest of the loop is structurally unchanged from TC-PLL-001 — the pin buffer is the only structural difference, per 1.5.5.
- In simulation `clkop_o` measures 100 MHz and `lock_o` asserts.

#### TC-PLL-051 — All seventeen distinct reference-clock I/O standards `Radiant Compilation`

**Configuration**

- `gui_en_refclk_pin`=`True`; all other fields at their defaults (as TC-PLL-001)
- Iterate `gui_refclk_io_type` over the 17 distinct options of the declared list: `LVDS`, `SUBLVDS`, `SLVS`, `HSTL15_I`, `HSTL15D_I`, `LVTTL33`, `LVCMOS33`, `LVCMOS25`, `LVCMOS18`, `LVCMOS18H`, `LVCMOS15`, `LVCMOS15H`, `LVCMOS12`, `LVCMOS12H`, `LVCMOS10H`, `LVCMOS10`, `LVCMOS10R`
- The declared list holds 18 entries because `HSTL15D_I` appears twice (spec 1.6 Optional Ports); the duplicate is a repeat of the same value and is exercised once — see Exclusions

**Procedure**

1. For each standard in the list, set the field, press **Calculate**, generate and compile.
2. Record the emitted I/O-standard assignment for each iteration.

**Pass Criteria**

- All 17 iterations generate and compile with no DRC error.
- In each iteration `IO_TYPE` equals the selected standard, per spec 1.6.
- In each iteration the emitted constraint sets the `clki_i` buffer to that same standard, per 1.5.5 and 1.5.13.
- The dialog offers `HSTL15D_I` twice and both entries yield the identical `IO_TYPE` value and the identical constraint line, per the duplicate recorded in spec 1.6 Optional Ports.

### G21 · Dynamic Phase Control Ports — `gui_en_dyn_phase`

Editable unless the APB slave is selected together with the soft control register, in which case the phase controls come from that register instead (Rule 22, spec 1.5.7). The `False` value is covered by TC-PLL-001.

#### TC-PLL-052 — Dynamic phase control ports generated `Radiant Compilation`

**Configuration**

- `gui_en_dyn_phase`=`True`; all other fields at their defaults (as TC-PLL-001)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `DYN_PORTS_EN` is 1, and `phasedir_i`, `phasestep_i`, `phaseloadreg_i` and `phasesel_i` are connected rather than tied low, per 1.3 and spec 1.6 Optional Ports.
- The primitive's phase-control source attribute is set to its **dynamic** value rather than staying static, per 1.5.7.
- With no register interface selected, the phase controls come from the four ports rather than from a register, per 1.5.7.
- `phasesel_i` is 3 bits wide on the generated boundary, per 1.3.

#### TC-PLL-053 — Dynamic phase stepping on every output select code 000-101 `Both`

**Configuration**

- `gui_en_dyn_phase`=`True`, `gui_reg_interface`=`None`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 8 — all six outputs 100 MHz

**Procedure**

1. Generate, compile, then simulate. Release `rstn_i` and wait for `lock_o`.
2. For each output select code in the table, in order: drive `phasesel_i` with the code, set `phasedir_i`, pulse `phaseloadreg_i`, then apply a sequence of `phasestep_i` assertions — one step per assertion, per 1.5.7 — and after the sequence settles measure the edge offset of every one of the six output clocks against its pre-sequence position.
3. Repeat the sequence for each code with `phasedir_i` at its opposite value.

| Step | `phasesel_i` | Output the controls act on (1.5.7) |
|---|---|---|
| 1 | `000` | `clkop_o` |
| 2 | `001` | `clkos_o` |
| 3 | `010` | `clkos2_o` |
| 4 | `011` | `clkos3_o` |
| 5 | `100` | `clkos4_o` |
| 6 | `101` | `clkos5_o` |

**Pass Criteria**

- `lock_o` asserts and remains asserted throughout the whole stepping sequence.
- At each step only the output named in the table for that select code changes its edge position; the other five are unchanged, per the code mapping in 1.5.7.
- The direction of the shift reverses when `phasedir_i` is inverted, per spec 1.6 Optional Ports and 1.3.
- The accumulated shift grows with the number of `phasestep_i` assertions — one step per assertion, per 1.3.
- The shift takes effect only after `phaseloadreg_i` is pulsed, which loads the dynamic phase register, per 1.3.
- Neither the number of clock cycles between a `phasestep_i` assertion and the resulting edge movement nor the step size in degrees is asserted: both are properties of the hard block, which spec 1.5.13 leaves `[UNRESOLVED]`. Only steady-state edge positions either side of a settled sequence are measured, per the transient-behavior rule in section 1.

### G22 · Clock Enable Ports — `gui_en_clken_op` … `gui_en_clken_s5`

Each field is visible and editable only when its output is enabled, not bypassed, and not the feedback source (Rule 23). The `False` value of all six is covered by TC-PLL-001.

#### TC-PLL-054 — All six clock-enable ports requested `Radiant Compilation`

**Configuration**

- `gui_en_usr_fbk`=`True` — with the external feedback clock, no output is the feedback source, so all six clock-enable-port fields are editable at once (Rule 23)
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 1 — VCO 800 MHz, all six outputs 800 MHz
- `gui_en_clken_op`=`gui_en_clken_os`=`gui_en_clken_s2`=`gui_en_clken_s3`=`gui_en_clken_s4`=`gui_en_clken_s5`=`True`

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `ENCLKOP_EN` … `ENCLKOS5_EN` are all 1, and `enclkop_i` … `enclkos5_i` are connected rather than tied high, per 1.3.
- Each output's internal enable attribute on the primitive is **disarmed**, so the port controls that clock rather than the clock running continuously, per 1.5.7.
- All six fields are editable, because an external-feedback configuration makes none of the outputs the feedback source, per Rule 23.

#### TC-PLL-055 — Clock-enable port on CLKOS only `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz, `clkop_o` 100 MHz
- `gui_clk_os_en`=`True`, `gui_clk_os_div`=8 — `clkos_o` 100 MHz
- `gui_en_clken_os`=`True`; every other clock-enable-port field `False` or unavailable

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `ENCLKOS_EN` is 1 and `enclkos_i` is connected; `ENCLKOP_EN` and `ENCLKOS2_EN` … `ENCLKOS5_EN` are 0 and the corresponding ports are tied high, per 1.3.
- CLKOS's internal enable attribute is disarmed while the primary output's is armed, per 1.5.7.
- The primary output's clock-enable-port field is read-only, because the primary is the feedback source here, per Rule 23 — which is why this test puts the enable port on a secondary output.
- The five disabled secondary outputs' clock-enable-port fields are read-only, per Rule 23.

### G23 · PLL Reset — `gui_en_pll_reset`

Default `True`, covered by TC-PLL-001 and exercised behaviourally in TC-PLL-072.

#### TC-PLL-056 — PLL reset port not requested `Radiant Compilation`

**Configuration**

- `gui_en_pll_reset`=`False`; all other fields at their defaults (as TC-PLL-001)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `PLL_RST` is 0, `rstn_i` is tied high at generation so the primitive's reset is held inactive, and the attribute that arms reset handling is disarmed, per 1.3 and 1.5.8.
- `rstn_i` remains declared on the generated module boundary even though it is tied off — the boundary is fixed at 43 ports, per 1.1 and 1.3.

### G24 · PLL Lock — `gui_en_pll_lock`, `gui_pll_lock_sticky`

The sticky field is editable only while the lock output is provided (Rule 20).

#### TC-PLL-057 — Non-sticky lock detector `Both`

**Configuration**

- `gui_en_pll_lock`=`True`, `gui_pll_lock_sticky`=`False`; all other fields at their defaults (as TC-PLL-001)

**Procedure**

1. Generate, compile, then simulate: release `rstn_i`, wait for `lock_o` to assert, then assert `rstn_i` again and observe `lock_o` while reset is held, and again after release.

**Pass Criteria**

- `LOCK_EN` is 1 and `PLL_LOCK_STICKY` is 0, selecting the primitive's **non-sticky** lock detector, per 1.5.8.
- `lock_o` is a driven output, not dangling, per 1.3.
- In simulation `lock_o` asserts after the first reset release.
- With reset re-asserted, `lock_o` deasserts, and after the second release it asserts again — the non-sticky detector follows the loop's state rather than latching, per 1.5.8. Only the steady-state value while reset is held and after relock is checked, not the transition edge, per the transient-behavior rule in section 1.

#### TC-PLL-058 — Sticky lock detector `Both`

**Configuration**

- `gui_en_pll_lock`=`True`, `gui_pll_lock_sticky`=`True`; all other fields at their defaults

**Procedure**

1. Confirm the sticky field is editable because the lock output is provided (Rule 20).
2. Generate, compile, then run the same reset sequence as TC-PLL-057 and observe `lock_o`.

**Pass Criteria**

- `LOCK_EN` is 1 and `PLL_LOCK_STICKY` is 1, selecting the primitive's **sticky** lock detector, per 1.5.8.
- In simulation `lock_o` asserts after the first reset release and remains asserted for the rest of the run.
- The generated parameter list differs from TC-PLL-057's only in `PLL_LOCK_STICKY`, per 1.5.8 — this field selects between the two detectors and nothing else.

#### TC-PLL-059 — Lock output not requested `Radiant Compilation`

**Configuration**

- `gui_en_pll_lock`=`False`; all other fields at their defaults

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `LOCK_EN` is 0 and `lock_o` is left dangling, per 1.3 and 1.5.8.
- The sticky field is read-only and hidden at its `False` default, and `PLL_LOCK_STICKY` is 0, per Rule 20.
- `lock_o` remains declared on the generated module boundary, per 1.1 and 1.3.

### G25 · Register Interface and Soft Control Registers — `gui_reg_interface`, `gui_en_csr`

A three-way choice; the parameters that connect each interface are set from it so at most one is ever 1 (spec 1.5.11). The soft control register field is editable only under the APB slave (Rule 21). The `None` value is covered by TC-PLL-001.

The hard PLL block's own register space is reachable at DWORD offsets `0x00`–`0x7F` through either interface, but the number of cycles the block takes and the content of those registers are outside this IP tree (spec 1.5.13, Appendix A). Criteria for accesses into that space therefore assert completion and the wrapper's own contribution, never a cycle count or a data value — see `SPEC-GAP-05` and `SPEC-GAP-06`.

#### TC-PLL-060 — LMMI slave register interface `Both`

**Configuration**

- `gui_reg_interface`=`LMMI`; all other fields at their defaults (as TC-PLL-001)

**Procedure**

1. Generate, compile, then simulate: release `lmmi_resetn_i` and `rstn_i`, wait for `lock_o`, then drive one LMMI write followed by one LMMI read at the same offset — assert `lmmi_request_i` with `lmmi_wr_rdn_i` = 1 and an offset inside the hard block's 128-entry space, then repeat with `lmmi_wr_rdn_i` = 0.

**Pass Criteria**

- `LMMI_EN` is 1 and `APB_EN` is 0, so exactly one interface is connected, per 1.5.11.
- `lmmi_clk_i`, `lmmi_resetn_i`, `lmmi_request_i`, `lmmi_wr_rdn_i`, `lmmi_offset_i` and `lmmi_wdata_i` are connected rather than tied off, and `lmmi_ready_o`, `lmmi_rdata_valid_o` and `lmmi_rdata_o` are driven rather than dangling, per 1.3.
- `lmmi_offset_i` is 7 bits and `lmmi_wdata_i` and `lmmi_rdata_o` are 8 bits on the generated boundary, per 1.3.
- The LMMI ports feed the hard block's register bus directly, with no fabric logic in either direction, so the IP adds **zero** cycles of latency, per 1.5.13 *Register Read Timing — LMMI*. The check is that no fabric register stage appears between the LMMI boundary and the register bus in the generated netlist; the observed response time on `lmmi_ready_o`, `lmmi_rdata_valid_o` and `lmmi_rdata_o` is the block's and is not asserted (`SPEC-GAP-05`).
- In simulation both transactions complete: `lmmi_ready_o` asserts for each, and `lmmi_rdata_valid_o` asserts for the read.
- Asserting `lmmi_resetn_i` low clears the transaction state machine to idle along with all of its outputs, per 1.5.8.

#### TC-PLL-061 — APB3 slave without the soft control register `Both`

**Configuration**

- `gui_reg_interface`=`APB`, `gui_en_csr`=`False`; all other fields at their defaults

**Procedure**

1. Confirm the soft control register field is editable because the interface is APB (Rule 21), and leave it `False`.
2. Generate, compile, then simulate: release `apb_preset_n_i` and `rstn_i`, wait for `lock_o`, then drive one APB write and one APB read at DWORD offset `0x00` (byte address `0x000`) using the ordering the IP's own testbench drives — address and select on one rising edge, enable on the next, hold until `apb_pready_o` (spec 1.5.13).

**Pass Criteria**

- `APB_EN` is 1 and `LMMI_EN` and `APB_SOFT_REG_EN` are 0, per 1.5.11 and Rule 21.
- The seven APB inputs are connected and `apb_pready_o`, `apb_pslverr_o` and `apb_prdata_o` are driven rather than dangling, per 1.3.
- `apb_paddr_i` and `apb_pwdata_i` are 32 bits wide, but only `apb_paddr_i[9:2]` and `apb_pwdata_i[7:0]` reach the register bus — the space is DWORD-addressed with 8 bits of data — per 1.3 and 1.5.10.
- `apb_pslverr_o` stays low for both transactions: the bridge's error input is tied to 0 inside the IP, per 1.3 and 1.5.13.
- `apb_prdata_o[31:8]` reads as zero on the read, per 1.3 and 1.5.13.
- Both transactions complete — `apb_pready_o` asserts for each. No cycle count is asserted, because without the soft control register the access reaches the hard block and its latency is `[UNRESOLVED]` per 1.5.13; the check is that the wrapper adds no register stage to the request path, the bridge being instantiated without registered outputs, per 1.5.13.
- The three LMMI output ports are marked dangling at the boundary yet still carry the register response internally to the bridge, per 1.5.11 — the generated netlist shows that path present, not removed.

#### TC-PLL-062 — APB3 slave with the soft control register - read `Both`

**Configuration**

- `gui_reg_interface`=`APB`, `gui_en_csr`=`True`; all other fields at their defaults
- `gui_en_dyn_phase` is read-only at `False` in this configuration, per Rule 22

**Procedure**

1. Confirm the dynamic-phase-ports field has become read-only (Rule 22).
2. Generate, compile, then simulate: release `apb_preset_n_i` and `rstn_i`, wait for `lock_o`, then read DWORD offset `0x80` — byte address `0x200` — with the testbench ordering of spec 1.5.13: `apb_paddr_i` and `apb_psel_i` on one rising edge, `apb_penable_i` on the next, held until `apb_pready_o`.
3. Count `apb_pclk_i` cycles from the assertion of `apb_psel_i` to the assertion of `apb_pready_o`.

**Pass Criteria**

- `APB_SOFT_REG_EN` is 1 and `APB_EN` is 1 — the soft register can only exist under the APB slave, per Rule 21 and 1.5.10.
- `DYN_PORTS_EN` is 0 and the four dynamic phase ports are tied low: in this configuration the phase controls come from the register, not the ports, per Rule 22 and 1.5.7.
- The read completes **two `apb_pclk_i` cycles after `apb_psel_i` is asserted**, per 1.5.13 *Soft Control Register Read Timing*.
- Bit 7 of the returned byte equals the current value of `lock_o`, and bit 6 reads as zero, per 1.5.10.
- `apb_prdata_o[31:8]` is zero and `apb_pslverr_o` stays low, per 1.5.13.
- The read succeeds without `apb_penable_i` having any effect on it — `apb_psel_i` alone starts the transaction, per 1.5.13.

#### TC-PLL-063 — Soft control register write drives the dynamic phase controls `Both`

**Configuration**

- `gui_reg_interface`=`APB`, `gui_en_csr`=`True`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 8 — all six outputs 100 MHz

**Procedure**

1. Generate, compile, then simulate: release `apb_preset_n_i` and `rstn_i` and wait for `lock_o`.
2. Write DWORD offset `0x80` (byte address `0x200`) with a value that sets the direction bit, the step bit, the load bit and an output select of `000`, using the testbench ordering of spec 1.5.13. Count `apb_pclk_i` cycles from `apb_psel_i` to `apb_pready_o`.
3. Repeat for output selects `001` through `101`, measuring the edge position of all six output clocks after each settled sequence.
4. Write a value with bits 7:6 set and read the register back.
5. Assert `apb_preset_n_i` low, then read the register back again.

**Pass Criteria**

- The write completes **two `apb_pclk_i` cycles after `apb_psel_i` is asserted**, and the dynamic phase control values it carries take effect on the edge at the end of the second cycle — the same edge that raises `apb_pready_o` — per 1.5.13 *Soft Control Register Write Timing*.
- Bits 5, 4, 3 and 2:0 of the written byte act as the dynamic phase direction, step, register load and output select, replacing `phasedir_i`, `phasestep_i`, `phaseloadreg_i` and `phasesel_i` respectively, per 1.5.10.
- After each settled sequence only the output named by the written select code has moved, using the same `000`–`101` mapping as TC-PLL-053, per 1.5.7.
- Only bits 5:0 are writable: after step 4 the register still reads back bit 7 as `lock_o` and bit 6 as zero, per 1.5.10 and 1.5.13.
- Asserting `apb_preset_n_i` low clears the bridge's transaction state machine to idle along with all of its outputs, per 1.5.8; the subsequent read returns bits 5:0 at their reset values.
- `apb_pslverr_o` stays low throughout, per 1.5.13.
- `lock_o` remains asserted throughout.

### G26 · Power Mode Settings — `gui_en_legacy`, `gui_en_powerdown`

Both inputs are always connected to the primitive; the field arms or disarms the matching attribute (spec 1.5.8). The `False` value of both is covered by TC-PLL-001; the behavioural cases are TC-PLL-073 and TC-PLL-074.

#### TC-PLL-064 — Legacy-mode input requested `Radiant Compilation`

**Configuration**

- `gui_en_legacy`=`True`; all other fields at their defaults (as TC-PLL-001)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `LEGACY_EN` is 1 and `legacy_i` is connected rather than tied high, per 1.3.
- The hard block's legacy attribute is armed, per 1.5.8 and spec 1.6 Power Mode Settings.
- No other generated parameter differs from TC-PLL-001's list.

#### TC-PLL-065 — Power-down input requested `Radiant Compilation`

**Configuration**

- `gui_en_powerdown`=`True`; all other fields at their defaults (as TC-PLL-001)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `POWERDOWN_EN` is 1 and `pllpd_en_n_i` is connected rather than tied high, per 1.3.
- The hard block's power-down input is connected in **both** this configuration and TC-PLL-001's; only the attribute that arms it follows the field, per 1.3 and 1.5.8.
- The primitive's own power-down attribute is at its hard-coded used value regardless of configuration, per 1.5.8 — it is identical in this test and in TC-PLL-001.
### G27 · Cross-Parameter Legal Combinations

Six configurations that exercise interacting fields together. Every combination was checked against all 28 rules of spec 1.7 simultaneously; the Configuration bullets state the loop arithmetic so the legality of each is auditable.

#### TC-PLL-066 — Fractional-N at the feedback-divider ceiling with the monitor and APB soft registers `Radiant Compilation`

**Configuration**

- `gui_en_frac_n`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=18.0, `gui_m_div`=1, `gui_n_div`=88, `gui_frac_n_div`=0, `gui_clk_op_div`=2
- `gui_en_refclk_mon`=`True`, `gui_refclk_mon_freq`=`3P2`
- `gui_reg_interface`=`APB`, `gui_en_csr`=`True` — so `gui_en_dyn_phase` is read-only at `False` (Rule 22)
- Implied loop: phase-detector frequency 18 MHz (the floor of the narrowed 18–100 MHz fractional range, Rule 4), effective feedback divider 88.0, VCO 1584 MHz (Rule 9), `clkop_o` 792 MHz (Rule 10). Feedback is forced to the primary internal tap and every bypass to 0 (Rules 13, 14)
- Division ratio for the monitor: 1 ÷ 88 = 0.0114 taking the fractional path, or 1 ÷ (88 × 2) = 0.0057 counting the output divider — both fall in the `< 0.03` row of the `REF_COUNTS` table in 1.5.6, so the expected value is the same under either reading (`SPEC-GAP-03`)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `FRAC_N_EN` is 1, `FBCLK_DIVIDER_ACTUAL_STR` is `88`, `SSC_F_CODE_STR` is 0, per 1.5.4.
- `EN_REFCLK_MON` is 1, the monitor-capable primitive is instantiated, `refdetreset` and `refdetlos` are connected, and `REF_OSC_CTRL` selects 3.2 MHz, per 1.5.1 and 1.5.6.
- `REF_COUNTS` is `4`, per the `< 0.03` row of 1.5.6.
- `APB_EN` and `APB_SOFT_REG_EN` are both 1, `LMMI_EN` is 0, `DYN_PORTS_EN` is 0, per 1.5.11, Rules 21 and 22.
- `gui_vco_freq` reads 1584.0 MHz, per Rule 9.
- Every spread-spectrum-specific attribute is at its zero encoding — fractional-N alone is enabled — per 1.5.4.

#### TC-PLL-067 — Spread spectrum with a pin reference clock, six distinct output frequencies and sticky lock `Radiant Compilation`

**Configuration**

- `gui_en_ssc`=`True`, `gui_ssc_profile`=`CENTER`, `gui_ssc_mod_depth`=1.50, `gui_ssc_mod_freq`=150.0 kHz
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=16
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_op_div`=16, `gui_clk_os_div`=8, `gui_clk_s2_div`=4, `gui_clk_s3_div`=2, `gui_clk_s4_div`=32, `gui_clk_s5_div`=128
- `gui_en_refclk_pin`=`True`, `gui_refclk_io_type`=`SLVS`; `gui_en_pll_lock`=`True`, `gui_pll_lock_sticky`=`True`
- Implied loop: phase-detector frequency 100 MHz (the ceiling of the narrowed spread-spectrum range, Rule 4), VCO 1600 MHz (the ceiling of Rule 9), outputs 100 / 200 / 400 / 800 / 50 / 12.5 MHz — all inside 6.25–800 (Rule 6), with the primary at 100 MHz satisfying the widened 10 MHz floor as the forced feedback source (Rules 10, 13)

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `SS_EN` is 1, `SSC_PROFILE` is `CENTER`, and `SSC_TBASE_STR` is `667` — round(1000 × 100 ÷ 150) — per 1.5.4.
- `SSC_REG_WEIGHTING_SEL_STR` is `0` and `SSC_STEP_IN_STR` is at most 127, per 1.5.4.
- The six output-divider parameters are `15`, `7`, `3`, `1`, `31` and `127` — each entered divider minus one — per 1.5.2.
- `PLL_REFCLK_FROM_PIN` is 1, `IO_TYPE` is `SLVS`, and the emitted constraints carry both the `create_clock` on `clki_i` at a 10.0 ns period and the `SLVS` I/O-standard assignment, per 1.5.5 and 1.5.13.
- `PLL_LOCK_STICKY` is 1, per 1.5.8.
- Every bypass parameter is 0 and `FBK_MODE` is the primary internal tap, per Rules 13, 14 and 1.5.4.

#### TC-PLL-068 — External feedback with all six clock-enable ports and the dynamic phase ports `Both`

**Configuration**

- `gui_en_usr_fbk`=`True`, `gui_en_dyn_phase`=`True`, `gui_reg_interface`=`None`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; all six output dividers 1 — VCO 800 MHz, all six outputs 800 MHz
- `gui_en_clken_op` … `gui_en_clken_s5`=`True`
- Stimulus: `clki_i` at 100 MHz, `usr_fbclk_i` at 800 MHz (`SPEC-GAP-13`)

**Procedure**

1. Generate, compile, then simulate. Release `rstn_i`, hold all six enables high, and wait for `lock_o`.
2. Deassert `enclkos3_i` alone, confirm `clkos3_o` stops while the other five keep running, then reassert it.
3. Drive a dynamic phase sequence on select code `011` (`clkos3_o`) and confirm only that output moves.

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `FBK_MODE` is `USERFBCLK`; `ENCLKOP_EN` … `ENCLKOS5_EN` are all 1; `DYN_PORTS_EN` is 1, per 1.5.3, 1.5.7 and Rule 22 (the dynamic-phase field is editable because no register interface is selected).
- All six clock-enable-port fields and all six phase fields are editable, because no output is the feedback source, per Rule 23.
- Each output's internal enable attribute is disarmed so the port controls the clock, per 1.5.7.
- In simulation `lock_o` asserts with all enables high; with `enclkos3_i` deasserted `clkos3_o` is static while `clkop_o`, `clkos_o`, `clkos2_o`, `clkos4_o` and `clkos5_o` continue at 800 MHz; after reassertion `clkos3_o` runs at 800 MHz again. Only steady-state behaviour either side of each transition is checked, per section 1.
- The dynamic phase sequence on select code `011` moves `clkos3_o` alone, per the code mapping in 1.5.7.

#### TC-PLL-069 — Mixed bypass with duty trim on both trim-capable outputs, legacy and power-down `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — feedback via `INTCLKOP`, VCO 800 MHz, `clkop_o` 100 MHz
- `gui_clk_os_en`=`True`, `gui_clk_os_div`=8 — `clkos_o` 100 MHz
- `gui_clk_s2_en`=`gui_clk_s3_en`=`gui_clk_s4_en`=`gui_clk_s5_en`=`True`; `gui_clk_s2_byp`=`gui_clk_s3_byp`=`gui_clk_s4_byp`=`gui_clk_s5_byp`=`True`
- `gui_clk_op_trim_en`=`True`, `gui_clk_op_trim_mode`=`Falling`, `gui_clk_op_trim_mult`=`2`
- `gui_clk_os_trim_en`=`True`, `gui_clk_os_trim_mode`=`Rising`, `gui_clk_os_trim_mult`=`1`
- `gui_en_legacy`=`True`, `gui_en_powerdown`=`True`
- CLKOS is deliberately left un-bypassed: a bypassed output's trim fields are read-only (Rule 24), so trim can only be exercised on an output that still passes through the loop

**Pass Criteria**

- Generation and compilation complete with no DRC error.
- `CLKOS2_BYPASS` … `CLKOS5_BYPASS` are 1 while `CLKOP_BYPASS` and `CLKOS_BYPASS` are 0, per 1.5.2 and Rule 13.
- `TRIM_EN_P` and `TRIM_EN_S` are both 1; the leading bit of `CLKOP_TRIM` is `0` (falling) with multiplier bits `010`, and the leading bit of `CLKOS_TRIM` is `1` (rising) with multiplier bits `001`, per 1.5.7 and spec 1.6 — the two trim-capable outputs carry independent settings.
- `LEGACY_EN` and `POWERDOWN_EN` are both 1, and `legacy_i` and `pllpd_en_n_i` are connected, per 1.3 and 1.5.8.
- The trim fields of the four bypassed outputs do not exist at all — trim is offered only on CLKOP and CLKOS, per Rule 24.

#### TC-PLL-070 — Maximum reference frequency and divider chain with LMMI, no reset and no lock `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=800.0, `gui_m_div`=44, `gui_n_div`=44, `gui_clk_op_div`=1
- `gui_reg_interface`=`LMMI`; `gui_en_pll_reset`=`False`; `gui_en_pll_lock`=`False`
- Implied loop: phase-detector frequency 18.182 MHz (Rule 4 floor), feedback clock 800 MHz (Rule 10 ceiling for the feedback source), VCO 800 MHz (Rule 9 floor), `clkop_o` 800 MHz. This is the simultaneous-extreme corner of the divider chain: reference frequency, reference divider and feedback divider are all at their maxima at once
- Rule 20 makes `gui_pll_lock_sticky` read-only at `False` because the lock output is not provided

**Pass Criteria**

- Generation and compilation complete with no DRC error — the three maxima are legal together.
- `CLKI_FREQ` is 800.0, `CLKI_DIVIDER_ACTUAL_STR` is `44`, `FBCLK_DIVIDER_ACTUAL_STR` is `44`, `DIVOP_ACTUAL_STR` is `0`, per 1.5.2.
- `gui_phasedet_freq` reads 18.18 MHz and `gui_vco_freq` reads 800.0 MHz, per Rules 4 and 9.
- `LMMI_EN` is 1 and `APB_EN` is 0, per 1.5.11.
- `PLL_RST` is 0 with `rstn_i` tied high and the reset attribute disarmed; `LOCK_EN` is 0 with `lock_o` dangling; `PLL_LOCK_STICKY` is 0, per 1.3, 1.5.8 and Rule 20.
- All 43 ports remain declared on the boundary, per 1.1 and 1.3.

#### TC-PLL-071 — Minimum reference frequency with the 1.0 MHz monitor, internal path switching and per-output phase shifts `Radiant Compilation`

**Configuration**

- `gui_config_mode`=`FREQUENCY`, `gui_refclk_freq`=18.0, `gui_en_int_fbkdel_sel`=`True`
- `gui_en_refclk_mon`=`True`, `gui_refclk_mon_freq`=`1P0`
- `gui_fbk_mode`=`CLKOS` — CLKOS is the feedback source, which frees the primary output's phase field (Rule 23)
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; requested frequencies `gui_clk_op_freq`=396, `gui_clk_os_freq`=792, `gui_clk_s2_freq`=264, `gui_clk_s3_freq`=198, `gui_clk_s4_freq`=99, `gui_clk_s5_freq`=49.5; all six tolerances 0.0
- Phase shifts `gui_clk_op_phase`=45, `gui_clk_s2_phase`=90, `gui_clk_s3_phase`=135, `gui_clk_s4_phase`=180, `gui_clk_s5_phase`=225; CLKOS's phase field is read-only at 0 (Rule 23)
- Achievable set: phase-detector frequency 18 MHz, feedback divider 44, CLKOS divider 2, VCO 1584 MHz, output dividers 4 / 2 / 6 / 8 / 16 / 32 — every requested frequency is exact, so a 0.0 tolerance satisfies Rule 1
- Division ratio for the monitor: 1 ÷ (44 × 2) = 0.0114, in the `< 0.03` row of 1.5.6

**Pass Criteria**

- Generation and compilation complete with no Rule 1 DRC error, and every `gui_clk_*_ppm` reads 0.
- The six `CLKO*_FREQ_ACTUAL` parameters are 396, 792, 264, 198, 99 and 49.5, per 1.5.2 — five distinct non-integer-ratio outputs from one VCO.
- `gui_phasedet_freq` reads 18.0 MHz and `gui_vco_freq` reads 1584.0 MHz, per Rules 4 and 9.
- `INTFBKDEL_SEL` is `ENABLED`, per spec 1.6 General.
- `EN_REFCLK_MON` is 1, `REF_OSC_CTRL` selects 1.0 MHz, `REF_COUNTS` is `4`, and the monitor-capable primitive is instantiated with `refdetreset` and `refdetlos` connected, per 1.5.1 and 1.5.6.
- `CLKOP_PHASE_ACTUAL`, `CLKOS2_PHASE_ACTUAL`, `CLKOS3_PHASE_ACTUAL`, `CLKOS4_PHASE_ACTUAL` and `CLKOS5_PHASE_ACTUAL` are 45, 90, 135, 180 and 225, each with its delay and phase code pair populated below the 128 delay limit, per 1.5.7 — the codes differ per output because each is resolved against that output's own divider value.
- `CLKOS_PHASE_ACTUAL` is 0 and CLKOS's phase and clock-enable-port fields are read-only, because CLKOS is the feedback source, per Rule 23.
- `CLKOS_EN` is 1 and `CLKOS_BYPASS` is 0, forced by Rule 13.

### G28 · Port Behaviour

One test per behavioral input port, plus a test for every declared output port whose behavior is not already asserted elsewhere. Two groups of ports are accounted for here rather than given their own card:

- **`clki_i`** is the single reference clock and is driven in every test in this plan; its frequency is swept in TC-PLL-013 – TC-PLL-015 and TC-PLL-018, its pin-buffer path in TC-PLL-050 and TC-PLL-051, and its loss in TC-PLL-077.
- **`clkop_o` … `clkos5_o`** are observed as the measured result in every simulated test; TC-PLL-080 observes all six together at six distinct frequencies. `lock_o` is asserted on in TC-PLL-001, TC-PLL-057 – TC-PLL-059, TC-PLL-062, TC-PLL-072 and TC-PLL-073.

Per the transient-behavior rule in section 1, the reset, power-down, legacy, enable and monitor-reset paths reach the hard block with no synchronizer (spec 1.5.8, 1.5.13), so every criterion below is a steady-state observation either side of a transition. No card asserts an edge relationship or a cycle count on those paths.

#### TC-PLL-072 — `rstn_i` assertion and release `Both`

**Configuration**

- `gui_en_pll_reset`=`True`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — VCO 800 MHz, `clkop_o` 100 MHz

**Procedure**

1. Generate, compile, then simulate. Hold `rstn_i` low from time zero with `clki_i` running.
2. Release `rstn_i` and observe `clkop_o` and `lock_o` for at least 700 µs.
3. Assert `rstn_i` low again and hold it, then observe `lock_o`.
4. Release `rstn_i` a second time and observe `lock_o` for a further 700 µs.

**Pass Criteria**

- `PLL_RST` is 1 and `rstn_i` is connected rather than tied high, per 1.3.
- `rstn_i` reaches the primitive through a single combinational inversion producing an active-high reset, with no synchronizer and no release sequencing in the fabric, per 1.5.8 — the generated netlist shows one inverter and no register on that path.
- With `rstn_i` held low, `lock_o` is deasserted.
- After the first release `lock_o` asserts and stays asserted.
- With `rstn_i` re-asserted, `lock_o` is deasserted again; after the second release it asserts again — the relock behaviour itself is the hard block's, per 1.5.8, so only the steady-state values are checked and no lock time is asserted (`SPEC-GAP-11`).

#### TC-PLL-073 — `pllpd_en_n_i` power-down assertion and release `Both`

**Configuration**

- `gui_en_powerdown`=`True`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — VCO 800 MHz, `clkop_o` 100 MHz

**Procedure**

1. Generate, compile, then simulate. Release `rstn_i` with `pllpd_en_n_i` held high and wait for `lock_o`.
2. Assert `pllpd_en_n_i` low and hold it, then observe `lock_o` and `clkop_o`.
3. Release `pllpd_en_n_i` high and observe `lock_o` for a further 700 µs.

**Pass Criteria**

- `POWERDOWN_EN` is 1 and `pllpd_en_n_i` is connected rather than tied high, per 1.3.
- `pllpd_en_n_i` is a direct connection to the primitive with no fabric logic in the path, per 1.5.13.
- With `pllpd_en_n_i` held low — the active-low power-down asserted — `lock_o` is deasserted, per 1.3 and 1.5.13.
- After releasing `pllpd_en_n_i`, `lock_o` asserts again.
- No response time is asserted. The 500 ns figure in spec 1.5.13 is recorded there as the IP testbench's own check bound, not as a specification (`SPEC-GAP-11`).

#### TC-PLL-074 — `legacy_i` asserted for the whole run `Both`

**Configuration**

- `gui_en_legacy`=`True`
- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1, `gui_clk_op_div`=8 — VCO 800 MHz, `clkop_o` 100 MHz

**Procedure**

1. Generate, compile, then simulate twice with the same generated output: once with `legacy_i` held at its inactive level for the whole run, once held at its active level for the whole run.
2. In each run release `rstn_i` and observe `clkop_o` and `lock_o` for at least 700 µs.

**Pass Criteria**

- `LEGACY_EN` is 1 and `legacy_i` is connected rather than tied high, per 1.3.
- `legacy_i` is a legacy-mode *request* input to the primitive, per 1.3; the wrapper adds no logic to it, per 1.5.1.
- In both runs `lock_o` asserts and `clkop_o` measures 100 MHz — the IP remains functional with legacy mode requested and with it not requested.
- No behavioural difference internal to the hard block is asserted: the effect of legacy mode is the block's and is not described by this source (`SPEC-GAP-11`).

#### TC-PLL-075 — `enclkop_i` through `enclkos5_i` deassertion and reassertion `Sim Only`

**Configuration**

- Reuse the generated output of TC-PLL-054 — this card shares every generation-time input with it: `gui_en_usr_fbk`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8, all six outputs enabled with divider 1, and all six clock-enable-port fields `True`
- Stimulus: `clki_i` at 100 MHz, `usr_fbclk_i` at 800 MHz; all six outputs 800 MHz

**Procedure**

1. Elaborate TC-PLL-054's generated RTL with the testbench; no synthesis or map run is required.
2. Release `rstn_i` with all six enables high and wait for `lock_o`.
3. For each enable in turn — `enclkop_i`, `enclkos_i`, `enclkos2_i`, `enclkos3_i`, `enclkos4_i`, `enclkos5_i` — deassert it alone, hold it deasserted long enough to observe the steady state, measure all six output clocks, then reassert it and measure all six again.

**Pass Criteria**

- While one enable is deasserted, that output's clock is static and the other five continue at 800 MHz — each enable controls its own output only, per 1.5.7.
- After each reassertion the affected output runs at 800 MHz again.
- `lock_o` remains asserted throughout — the enables gate the outputs, not the loop, per 1.5.7.
- Each `enclko*_i` is a direct connection to the hard block with nothing inserted by the wrapper, per 1.5.13.
- No stop or restart latency is asserted: the response to an enable deassertion is the block's, per 1.5.13, and same-cycle enable transitions are outside this plan's scope per section 1 (`SPEC-GAP-11`).

#### TC-PLL-076 — `usr_fbclk_i` as the loop feedback source `Sim Only`

**Configuration**

- Reuse the generated output of TC-PLL-011 — this card shares every generation-time input with it: `gui_en_usr_fbk`=`True`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=8, `gui_clk_op_div`=1
- Stimulus: `clki_i` at 100 MHz; `usr_fbclk_i` at 800 MHz (`SPEC-GAP-13`)

**Procedure**

1. Elaborate TC-PLL-011's generated RTL with the testbench; no synthesis or map run is required.
2. Release `rstn_i` with `usr_fbclk_i` running at 800 MHz and wait for `lock_o`; measure `clkop_o`.
3. Stop `usr_fbclk_i` (hold it static) and observe `lock_o`.
4. Restart `usr_fbclk_i` at 800 MHz and observe `lock_o` for a further 700 µs.

**Pass Criteria**

- With `usr_fbclk_i` running, `lock_o` asserts and `clkop_o` measures 800 MHz — the loop closes through the external feedback port, per 1.5.3.
- With `usr_fbclk_i` static, `lock_o` is deasserted — the feedback path genuinely runs through the port rather than through an output clock, per 1.5.3. This is the observation that distinguishes `USERFBCLK` from every output-derived selection.
- After `usr_fbclk_i` restarts, `lock_o` asserts again.
- No lock or loss-of-lock timing is asserted (`SPEC-GAP-11`).

#### TC-PLL-077 — `refdetreset` and `refdetlos` reference-loss reporting `Sim Only`

**Configuration**

- Reuse the generated output of TC-PLL-019 — this card shares every generation-time input with it: `gui_en_refclk_mon`=`True`, `gui_refclk_mon_freq`=`3P2`, `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=3, `gui_clk_op_div`=3
- Stimulus: `clki_i` at 100 MHz; `clkop_o` 300 MHz

**Procedure**

1. Elaborate TC-PLL-019's generated RTL with the testbench; no synthesis or map run is required.
2. Release `rstn_i` and `refdetreset`, wait for `lock_o`, and record `refdetlos` with the reference running.
3. Stop `clki_i` (hold it static) and record `refdetlos` once it settles.
4. Restart `clki_i` at 100 MHz, pulse `refdetreset` to restart the detector, and record `refdetlos` once it settles.

**Pass Criteria**

- With the reference running, `refdetlos` is deasserted, per 1.3 and 1.5.6.
- With `clki_i` held static, `refdetlos` asserts — the monitor reports loss of the reference, per 1.3 and 1.5.6.
- After the reference returns and `refdetreset` is pulsed, `refdetlos` is deasserted again — `refdetreset` lets the design restart the detector, per 1.5.6.
- Both ports are genuinely connected in this configuration, which is only true in the generate branch that instantiates the monitor-capable primitive, per 1.3 and 1.5.1.
- No detection latency is asserted: the monitor's response time is the hard block's, which this source does not specify (`SPEC-GAP-11`).

#### TC-PLL-078 — LMMI transaction on the six LMMI input ports and three LMMI output ports `Sim Only`

**Configuration**

- Reuse the generated output of TC-PLL-060 — this card shares every generation-time input with it: `gui_reg_interface`=`LMMI`, all other fields at their defaults

**Procedure**

1. Elaborate TC-PLL-060's generated RTL with the testbench; no synthesis or map run is required.
2. Release `lmmi_resetn_i` and `rstn_i` and wait for `lock_o`.
3. Drive an LMMI write: assert `lmmi_request_i` with `lmmi_wr_rdn_i` = 1, an offset inside the 7-bit space and a byte on `lmmi_wdata_i`; hold until `lmmi_ready_o` asserts.
4. Drive an LMMI read at the same offset with `lmmi_wr_rdn_i` = 0; hold until `lmmi_ready_o` and `lmmi_rdata_valid_o` assert, and capture `lmmi_rdata_o`.
5. Assert `lmmi_resetn_i` low mid-idle, release it, and repeat step 3.

**Pass Criteria**

- The write transaction completes: `lmmi_ready_o` asserts, per 1.3.
- The read transaction completes: `lmmi_ready_o` and `lmmi_rdata_valid_o` both assert and `lmmi_rdata_o` presents 8 bits of data, per 1.3.
- `lmmi_wr_rdn_i` selects direction — 1 for write, 0 for read — and both directions are accepted, per 1.3.
- Asserting `lmmi_resetn_i` low clears the transaction state machine to idle along with all of its outputs, and a transaction driven after release completes normally, per 1.5.8.
- The IP contributes zero cycles of latency in either direction — the LMMI ports are wired straight to the hard block's register bus with no fabric logic — per 1.5.13. The value returned on `lmmi_rdata_o` is not asserted, because the hard block's register content is outside this source (`SPEC-GAP-06`), and no cycle count is asserted (`SPEC-GAP-05`).
- `lock_o` remains asserted throughout — register traffic does not disturb the loop.

#### TC-PLL-079 — APB transaction on the seven APB input ports and three APB output ports `Sim Only`

**Configuration**

- Reuse the generated output of TC-PLL-061 — this card shares every generation-time input with it: `gui_reg_interface`=`APB`, `gui_en_csr`=`False`, all other fields at their defaults

**Procedure**

1. Elaborate TC-PLL-061's generated RTL with the testbench; no synthesis or map run is required.
2. Release `apb_preset_n_i` and `rstn_i` and wait for `lock_o`.
3. Drive an APB write at DWORD offset `0x00` (byte address `0x000`) using the ordering of spec 1.5.13: `apb_paddr_i`, `apb_pwdata_i`, `apb_pwrite_i` and `apb_psel_i` on one rising edge of `apb_pclk_i`, `apb_penable_i` on the next, held until `apb_pready_o`.
4. Drive an APB read at the same offset and capture `apb_prdata_o` and `apb_pslverr_o`.
5. Assert `apb_preset_n_i` low mid-idle, release it, and repeat step 3.

**Pass Criteria**

- Both transactions complete: `apb_pready_o` asserts for each, extending the access phase until the register transaction completes, per 1.3.
- `apb_psel_i` alone starts the transaction — the bridge derives the register request combinationally from its idle-state exit, before `apb_penable_i` is seen — per 1.5.13.
- `apb_pslverr_o` stays low for both transactions, because the bridge's error input is tied to 0 inside the IP, per 1.3 and 1.5.13. This output can never report an error in any configuration.
- `apb_prdata_o[31:8]` reads as zero on the read, per 1.3 and 1.5.13.
- Only `apb_paddr_i[9:2]` participates in decoding, so the space is DWORD-addressed, per 1.3 and 1.5.10.
- Asserting `apb_preset_n_i` low clears the bridge's transaction state machine to idle along with all of its outputs, and a transaction driven after release completes normally, per 1.5.8.
- The data value returned is not asserted (`SPEC-GAP-06`), no cycle count is asserted for this hard-block access (`SPEC-GAP-05`), and address aliasing above DWORD offset `0x7F` is not exercised (see Exclusions).

#### TC-PLL-080 — All six output clocks and `lock_o` observed together at distinct frequencies `Both`

**Configuration**

- `gui_config_mode`=`DIVIDER`, `gui_refclk_freq`=100.0, `gui_m_div`=1, `gui_n_div`=1 — feedback via `INTCLKOP`, VCO 800 MHz
- `gui_clk_os_en` … `gui_clk_s5_en`=`True`; `gui_clk_op_div`=8, `gui_clk_os_div`=4, `gui_clk_s2_div`=2, `gui_clk_s3_div`=1, `gui_clk_s4_div`=16, `gui_clk_s5_div`=128
- Expected outputs: `clkop_o` 100 MHz, `clkos_o` 200 MHz, `clkos2_o` 400 MHz, `clkos3_o` 800 MHz, `clkos4_o` 50 MHz, `clkos5_o` 6.25 MHz — spanning the whole 6.25–800 MHz range of Rule 6 in one configuration

**Procedure**

1. Generate, compile, then simulate. Release `rstn_i`, wait for `lock_o`, and measure all six output clocks simultaneously over the same window.

**Pass Criteria**

- The six output-divider parameters are `7`, `3`, `1`, `0`, `15` and `127` — each entered divider minus one — per 1.5.2.
- All six output ports are driven, not dangling, because all five secondary enables are 1, per 1.3.
- In simulation the six clocks measure 100, 200, 400, 800, 50 and 6.25 MHz respectively — VCO ÷ that output's divider, per 1.5.2 — confirming the six output dividers are independent of one another.
- `lock_o` asserts and stays asserted while all six outputs run.
- Each output publishes its frequency to the tool through its own `clock_param` extension naming that output's `*_FREQ_ACTUAL` parameter, per 1.3.

### G29 · DRC and Radiant Compilation Checks

The rules below are exercised implicitly by the tests named against each. None is tested destructively: this plan uses legal configurations only, so a rule is confirmed by the configuration it *permits* and by the field states it produces, never by feeding it an illegal input to read back an error message (see Exclusions).

- **DRC-1** — Requested output frequency achievable within its tolerance (Rule 1). Exercised by every frequency-mode test: TC-PLL-002, TC-PLL-004, TC-PLL-036 – TC-PLL-039, TC-PLL-043, TC-PLL-044, TC-PLL-071. The 0.0-tolerance iteration of TC-PLL-043 also confirms the internal 1e-6 % substitution.
- **DRC-2** — Divider-field validation hook (Rule 2). Present on all six output-divider fields in every divider-mode test — TC-PLL-003, TC-PLL-005, TC-PLL-013 – TC-PLL-030, TC-PLL-040 – TC-PLL-042, TC-PLL-066 – TC-PLL-070 — and never observed to fail, which is consistent with Rule 2's finding that the hook's argument gates out both failure paths. Recorded as dead validation in the specification's Appendix A; see `SPEC-GAP-09`.
- **DRC-3** — Reference clock frequency range 18–800 MHz (Rule 3). Both bounds accepted in TC-PLL-013 and TC-PLL-015.
- **DRC-4** — Phase-detector frequency range by mode (Rule 4). Integer-N floor and interior in TC-PLL-013, TC-PLL-014, TC-PLL-018; fractional / spread-spectrum sub-range in TC-PLL-005 – TC-PLL-010, TC-PLL-027 – TC-PLL-030, TC-PLL-066, TC-PLL-067.
- **DRC-5** — Feedback divider range by mode (Rule 5). Integer-N 1–44 in TC-PLL-024 – TC-PLL-026; fractional-N floor 16 and reachable ceiling 88 in TC-PLL-027.
- **DRC-6** — Output divider range 1–128 narrowed by the frequency window (Rule 6). Both extremes on all six outputs in TC-PLL-040 and TC-PLL-041; the median in TC-PLL-042.
- **DRC-7** — Reference divider range 1–44 (Rule 7). All three values in TC-PLL-016 – TC-PLL-018, with the maximum at the 18 MHz phase-detector floor.
- **DRC-8** — Fractional word range 0–4095 (Rule 8). Both bounds and the median in TC-PLL-028 – TC-PLL-030.
- **DRC-9** — VCO frequency range 800–1600 MHz (Rule 9). Floor in TC-PLL-014 – TC-PLL-018, TC-PLL-026, TC-PLL-040, TC-PLL-041; ceiling in TC-PLL-027, TC-PLL-042, TC-PLL-067.
- **DRC-10** — Output frequency range widened for the feedback clock (Rule 10). The 6.25 MHz floor on a non-feedback output and the 10–800 MHz widened range on the feedback output in TC-PLL-036, TC-PLL-037, TC-PLL-041.
- **DRC-11** — Spread-spectrum modulation frequency range 24.42–200 kHz (Rule 11). Both bounds in TC-PLL-008 and TC-PLL-010.
- **DRC-12** — Feedback source must be an enabled, un-bypassed output (Rule 12). The offered option list checked against the enabled set in TC-PLL-022 and TC-PLL-023.
- **DRC-13** — The feedback clock is forced enabled and un-bypassed (Rule 13). Confirmed in TC-PLL-021 – TC-PLL-023, TC-PLL-033, TC-PLL-037, TC-PLL-071.
- **DRC-14** — Bypass unavailable in fractional-N and spread-spectrum modes (Rule 14). Confirmed in TC-PLL-004, TC-PLL-005, TC-PLL-006, TC-PLL-066, TC-PLL-067.
- **DRC-15** — Frequency and divider fields mutually exclusive (Rule 15). Checked in both directions in TC-PLL-002 and TC-PLL-003, and re-confirmed in TC-PLL-043.
- **DRC-16** — User feedback clock excludes fractional-N and spread spectrum (Rule 16). Confirmed by the field being read-only and hidden in TC-PLL-004, TC-PLL-005 and TC-PLL-066, and editable in TC-PLL-011.
- **DRC-17** — Spread-spectrum fields require spread spectrum (Rule 17). Confirmed read-only in TC-PLL-001 and editable in TC-PLL-006 – TC-PLL-010.
- **DRC-18** — Reference-clock monitor unavailable on a device whose name ends in `p` (Rule 18). The editable branch is exercised on `LIFCL-40` in TC-PLL-019, TC-PLL-020, TC-PLL-066 and TC-PLL-071; the read-only branch is excluded (see Exclusions, `SPEC-GAP-02`).
- **DRC-19** — I/O standard requires the pin option (Rule 19). Read-only at `LVDS` with no constraint emitted in TC-PLL-001; editable with the constraint emitted in TC-PLL-050 and TC-PLL-051.
- **DRC-20** — Sticky lock requires the lock output (Rule 20). Editable in TC-PLL-058; read-only at `False` in TC-PLL-059 and TC-PLL-070.
- **DRC-21** — Soft control registers require the APB slave (Rule 21). Read-only in TC-PLL-001 and TC-PLL-060; editable in TC-PLL-061 – TC-PLL-063.
- **DRC-22** — Dynamic phase ports and the soft control register mutually exclusive (Rule 22). Ports editable with no register interface in TC-PLL-052, TC-PLL-053 and TC-PLL-068; read-only under APB with soft registers in TC-PLL-062, TC-PLL-063 and TC-PLL-066.
- **DRC-23** — Phase shift and clock-enable ports unavailable on the feedback clock (Rule 23). Confirmed on the locked output in TC-PLL-021 – TC-PLL-023, TC-PLL-037, TC-PLL-055 and TC-PLL-071, and on all six outputs at once in the external-feedback configurations TC-PLL-045 – TC-PLL-047, TC-PLL-054 and TC-PLL-068.
- **DRC-24** — Duty trim fields require trim to be enabled (Rule 24). Confirmed in TC-PLL-048, TC-PLL-049 and TC-PLL-069, including the absence of trim fields on CLKOS2 – CLKOS5.
- **DRC-25** — Optimization target fixed (Rule 25). The field is read-only in every test; the unreachable `POWER` option is excluded (see Exclusions).
- **DRC-26** — PMU wait-for-lock field permanently hidden (Rule 26). The field is absent from the dialog in every test and `PMU_WAITFORLOCK` is `ENABLED` in every generated parameter list.
- **DRC-27** — All outputs disabled or bypassed short-circuits the search (Rule 27). Not reachable through the GUI on this IP — see Exclusions and `SPEC-GAP-10`. TC-PLL-034 and TC-PLL-069 come closest, bypassing every secondary output while the feedback output stays enabled and un-bypassed as Rule 13 requires.
- **DRC-28** — Reference divider preset by frequency threshold (Rule 28). Confirmed at 1 for reference frequencies at or below 500 MHz in TC-PLL-013, TC-PLL-014 and TC-PLL-016, and at 2 for 800 MHz in TC-PLL-015.

#### TC-PLL-081 — Default-parameter Radiant compilation smoke test `Radiant Compilation`

**Configuration**

- All fields at their spec 1.6 defaults — the same configuration as TC-PLL-001, taken through compilation alone

**Procedure**

1. Create a Radiant 2025.1 project for `LIFCL-40`, instantiate the IP, change nothing, generate.
2. Run synthesis and map to completion.
3. Record the tool version, the generated file set and the emitted constraint file.

**Pass Criteria**

- Generation completes with no DRC error and no warning attributable to the IP's own metadata or plugin.
- Synthesis and map complete on the default configuration.
- The tool accepts the IP on Radiant 2025.1 — the declared minimum, with no upper bound declared (spec header, spec 1.1).
- The generated file set is the tool's default for this IP, the IP declaring no `outFileConfigs`, per 1.5.12.
- The emitted constraint file contains exactly two lines' worth of constraint: a `create_clock` on `clki_i` and no I/O-standard assignment, with no `set_false_path` and no `set_max_delay` anywhere, per 1.5.13 *Constraints applied*.
- The `gpll_cfg_upd` component generator has run and left the instance configuration files in the state 1.5.12 describes.

## Exclusions and Rationale

| Excluded | Rationale |
|---|---|
| Performance and timing verification | Functional plan; VCO jitter, phase noise, lock time, duty accuracy, fmax, setup/hold and clock-frequency characterization are out of scope. Almost all of this IP's timing is a property of the hard PLL block, which is not part of the IP tree (spec 1.5.13). |
| Non-target device families | `LFD2NX`, `LFCPNX`, `jd5d00`, `LFMXO5`, `UT24C`, `UT24CP`. Spec 1.2 records that the plugin performs no family normalization and holds no family lookup table, so these six share the `LIFCL` implementation path and are covered implicitly; every test case is nevertheless written for `LIFCL`. |
| Non-target device paths — the `IS_JP_DEVICE` branch | The whole set of behaviours keyed on a device name ending in `p`: the widened 10–160 MHz phase-detector range with no separate fractional sub-range, the reference divider preset threshold of 160 MHz instead of 500 MHz, the read-only reference-clock-monitor field, and the unconditional selection of the monitor-capable primitive through the `IS_JP_DEVICE` macro (spec 1.2, 1.5.1, 1.5.6, Rules 4, 18, 28, *Device-dependent limits*). None of the `LIFCL` device names in the release-notes list ends in `p`, and spec 1.2 records the affected device set as `[UNRESOLVED]` — see `SPEC-GAP-02`. |
| Hidden, read-only, and derived parameters | All 94 auto-calculated `type="param"` settings, each fixed by `editable="False"` and `hidden="True"` with a `value_expr` reading the plugin's computed dictionary (spec 1.4); `SIM_FLOAT_PRECISION`, which has no matching setting (spec 1.4); the `IS_JP_DEVICE` `verilog_macro`, likewise hidden and non-editable (spec 1.4); the four never-displayed calculation hooks `set_attributes`, `gui_clkout`, `print_attributes` and `gui_sim_type`, whose `hidden` attribute is the literal `bool(1)` (spec 1.6 preamble); and the display-only fields listed in section 1, whose editability flag the plugin initialises false and never reassigns. The analog loop-filter set — charge-pump currents, loop and ripple capacitance, voltage-to-current resistance — is not user-visible anywhere and is chosen by the optimizer (spec 1.5.9), as are the hard-coded VCO gain code, voltage-to-current selection and 1 V enable. |
| Unreachable GUI options | `gui_optim_prio` = `Minimum Power (Lower VCO)` (`POWER`): the field is visible but its editability flag is never reassigned, so the optimizer always reads the calculated `JITTER` (Rule 25, spec Appendix A). `gui_en_pmu_wait_lock`: permanently hidden, its default `True` still yielding `PMU_WAITFORLOCK` = `ENABLED` (Rule 26). The second `HSTL15D_I` entry in the 18-item I/O-standard list: a duplicate of the same value, so TC-PLL-051 exercises the value once across 17 distinct options (spec 1.6 Optional Ports, spec Appendix A). `gui_n_div` values 89–128: declared but unreachable on this target because the narrowing of Rule 5 and the 800 MHz output ceiling of Rule 10 bind first — see `SPEC-GAP-07`. `REF_COUNTS` = 3: the table in spec 1.5.6 assigns 2 to two adjacent ratio rows and jumps from 2 to 4, so no division ratio produces 3 — see `SPEC-GAP-08`. Rule 27's all-disabled-or-bypassed short circuit: not reachable through the GUI on this IP — see `SPEC-GAP-10`. |
| DRC-negative testing | Legal configurations only. No test feeds an out-of-range value or an illegal combination to read back an error message, so the two Calculate-command errors of spec 1.5.9 (`[ERROR] No valid dividers found!` and `[ERROR] Unable to find valid Analog Parameter combination.`), the Rule 1 DRC message, and the informational `[INFO] All clocks are disabled/bypassed!` of Rule 27 are not verified here. |
| Unreachable RTL paths | The `` `ifdef IS_JP_DEVICE `` branch of the primitive selection (spec 1.5.1) — see the non-target device paths row and `SPEC-GAP-12`. The final defensive arm of the feedback multiplexer, which defaults to the primary output clock for any `FBK_MODE` value outside the declared set (spec 1.5.3): the plugin only ever writes one of the declared values, so no legal configuration reaches it. An asserted `apb_pslverr_o`: the bridge's error input is tied to 0 inside the IP, so the output can never report an error (spec 1.3, 1.5.13) — TC-PLL-079 asserts it stays low rather than trying to provoke it. |
| APB address aliasing above DWORD offset `0x7F` | Without the soft control register the wrapper truncates the decoded eight-bit DWORD address to the seven bits the hard block uses, so offsets `0x80`–`0xFF` alias onto `0x00`–`0x7F` (spec 1.5.10). Verifying the aliasing would require knowing the hard block's register content, which is outside this source, and spec Appendix A records the aliasing itself as an open question rather than intended behaviour — see `SPEC-GAP-06` and `SPEC-GAP-15`. |
| Hard-block register content and latency | Accesses to DWORD offsets `0x00`–`0x7F` reach the hard PLL block's own 128-entry register space through either interface. Neither the number of cycles the block takes nor the meaning of any register there is established anywhere in the IP tree (spec 1.5.13, spec Appendix A), so TC-PLL-060, TC-PLL-061, TC-PLL-078 and TC-PLL-079 verify completion and the wrapper's own contribution only — see `SPEC-GAP-05` and `SPEC-GAP-06`. |

## Spec Issues and Assumptions

| ID | Missing or Ambiguous | Assumption Used | Impact | Who Should Confirm |
|---|---|---|---|---|
| `SPEC-GAP-01` | The default feedback selection. Spec 1.6 Feedback and Appendix A record an open `[CONFLICT]`: the metadata declares `default = "CLKOP"` for `gui_fbk_mode` while the plugin's own default is `INTCLKOP`, and the RTL top-module default cannot settle it because the plugin-computed value always overwrites it. | The baseline records whichever default the dialog actually presents rather than asserting one, and its Pass Criteria make no claim about which of the two is in force. Tests that need a specific feedback source set the field explicitly. | TC-PLL-001, TC-PLL-081, and the "feedback via the default primary selection" wording in TC-PLL-038, TC-PLL-043, TC-PLL-044 | IP owner / metadata owner |
| `SPEC-GAP-02` | Which marketed device names satisfy `check_is_jp_device` — the predicate that a device name ends in `p`. Spec 1.2 records the affected device set as `[UNRESOLVED]`. | `LIFCL-40` is assumed **not** to end in `p`, so the non-`p` limits apply throughout: 18–500 MHz integer-N and 18–100 MHz fractional phase-detector ranges, an editable reference-clock-monitor field, the 500 MHz reference-divider preset threshold, and the base primitive unless the monitor is enabled. | Every test in the plan; explicitly TC-PLL-013 – TC-PLL-020, TC-PLL-027, TC-PLL-066, TC-PLL-071 and the Rule 4 / 18 / 28 rows of G29 | IP owner |
| `SPEC-GAP-03` | How the loop equation is formed when the feedback source is the external `usr_fbclk_i` port. Spec 1.5.2 includes the feedback output divider "when feedback is taken from an output rather than the fractional path", and Rule 5 says "in integer-N mode" — neither statement resolves the external-feedback case. | Every external-feedback test uses a primary output divider of 1, which makes the VCO identical under either reading. No test depends on the ambiguous term. | TC-PLL-011, TC-PLL-045 – TC-PLL-047, TC-PLL-054, TC-PLL-068, TC-PLL-076 | IP owner |
| `SPEC-GAP-04` | The rounding rule for the spread-spectrum depth code. Spec 1.5.4 gives depth code = amplitude × feedback divider × 262144 ÷ time base but does not say how a non-integer result is rounded. | Criteria assert the time base exactly, the weighting selector, and whether the code exceeds 127 — all of which the derivation fixes — but never an exact depth code. | TC-PLL-006 – TC-PLL-010, TC-PLL-067 | IP owner |
| `SPEC-GAP-05` | Register access latency through the hard block. Spec 1.5.13 marks both the hard-block APB path and the whole LMMI path `[UNRESOLVED]` because the primitive is not part of the IP tree. | Criteria for those accesses assert transaction completion and the wrapper's zero added latency (no fabric register stage in the generated netlist), never a cycle count. Only the soft-control-register path, which spec 1.5.13 does establish at two `apb_pclk_i` cycles, carries a cycle-count criterion. | TC-PLL-060, TC-PLL-061, TC-PLL-078, TC-PLL-079 | IP owner |
| `SPEC-GAP-06` | The content of the hard PLL block's 128-entry register space. The metadata declares one address block and no `register` or `field` elements at all (spec 1.5.10, Appendix A), and the block's registers are not described anywhere in the tree. | No test asserts a data value read back from DWORD offsets `0x00`–`0x7F`; those accesses are verified by completion only. Only the soft control register, whose layout spec 1.5.10 gives bit by bit, carries data-value criteria. | TC-PLL-060, TC-PLL-061, TC-PLL-078, TC-PLL-079 | Metadata owner / IP owner |
| `SPEC-GAP-07` | Whether the declared feedback-divider ceiling of 128 is reachable. Rule 5 declares 1–128 (16–128 fractional) and then narrows it to the VCO window; combined with the 800 MHz output ceiling of Rule 10 and the 18 MHz phase-detector floor of Rule 4, the effective ceiling on this target is 44 in integer-N and 88 in fractional-N. The specification does not state the effective ceiling. | The plan tests 44 as the integer-N maximum and 88 as the fractional-N maximum and records 89–128 as unreachable rather than writing an illegal test at 128. | TC-PLL-026, TC-PLL-027, TC-PLL-066, TC-PLL-070; the "Unreachable GUI options" row of Exclusions | IP owner |
| `SPEC-GAP-08` | The `REF_COUNTS` table in spec 1.5.6. Its rows are stated as `≥ 0.3`, `0.125 … 0.3`, `0.06 … 0.125`, `0.03 … 0.06` and `< 0.03`, so the boundary values 0.3, 0.125, 0.06 and 0.03 each belong to two rows; the 0.03 … 0.06 row yields 2, the same as the row above it, so no ratio produces 3. | Every monitor test uses a division ratio strictly inside a row (0.111, 0.222, 0.0114, 0.0057), so no criterion depends on a boundary. `REF_COUNTS` = 3 is recorded as unreachable rather than tested. | TC-PLL-019, TC-PLL-020, TC-PLL-066, TC-PLL-071 | IP owner |
| `SPEC-GAP-09` | Whether the six output-divider `drc` hooks are meant to validate anything. Rule 2 and spec Appendix A record that the hook's third argument gates out both failure paths, so it returns success unconditionally. | The plan treats the hooks as dead validation: divider entries are bounded by Rule 6 instead, and no test expects one of these hooks to fire. | DRC-2 in G29; every divider-mode test | IP owner |
| `SPEC-GAP-10` | Whether Rule 27's all-disabled-or-bypassed short circuit is reachable. The primary output is always enabled (spec 1.1), and bypassing it requires that it not be the feedback source — which requires another output to be the feedback source, and Rule 13 then forces *that* output enabled and un-bypassed. Selecting the external feedback clock instead forces the primary bypass off (Rule 14). Spec 1.6 also states the primary bypass field is hidden whenever the primary is the feedback source, which appears to conflict with Rule 13's carve-out that the primary bypass is forced "only when the non-internal tap is selected". | The condition is treated as unreachable through the GUI and is not tested. The apparent Rule 13 / spec 1.6 conflict is avoided: no test bypasses the primary output while it is the feedback source under either reading. | Rule 27 in G29; the "Unreachable GUI options" row of Exclusions; TC-PLL-033, TC-PLL-034, TC-PLL-069 | IP owner |
| `SPEC-GAP-11` | Absolute lock, enable-response, power-down-response, relock and reference-loss-detection times. Spec 1.5.13 marks all of them `[UNRESOLVED]` and records the 700 µs, 5 µs and 500 ns figures as the IP testbench's own check bounds rather than specifications. | Simulated cases use 700 µs as an *observation window*, never as a pass threshold, and assert steady-state values either side of a transition. No test asserts a response time on any of these paths. | TC-PLL-001, TC-PLL-057, TC-PLL-058, TC-PLL-072 – TC-PLL-077 | Hardware team / IP owner |
| `SPEC-GAP-12` | Whether the generator suppresses the `IS_JP_DEVICE` macro definition when its boolean `value_expr` evaluates false. Spec Appendix A records that the RTL branches on whether the macro is *defined*, not on its value, and that the generator's behaviour for a false-valued boolean macro is not stated. | The plan targets a device for which the predicate is assumed false and expects the macro-undefined branch to be taken; it does not assert how the macro appears in the generated output. If the generator defines the macro regardless of value, the primitive selection of spec 1.5.1 would change for every test in this plan. | Every test; explicitly the primitive-selection criteria of TC-PLL-001 and TC-PLL-019 | IP owner |
| `SPEC-GAP-13` | What frequency the external feedback clock must carry. The IP exposes no GUI field for the `usr_fbclk_i` frequency, and spec 1.5.3 says only that the port is selected as the loop's feedback source. | External-feedback tests drive `usr_fbclk_i` at the phase-detector frequency times the feedback divider — 800 MHz for the 100 MHz reference, reference divider 1 and feedback divider 8 these tests use — which is the frequency the loop's own comparison implies (spec 1.5.2). | TC-PLL-011, TC-PLL-045 – TC-PLL-047, TC-PLL-054, TC-PLL-068, TC-PLL-076 | IP owner |
| `SPEC-GAP-14` | The width of the duty-trim attribute. Spec 1.5.7 calls it a 5-bit attribute but describes only four bits of content — a leading edge bit followed by a three-bit multiplier code — and does not say what the fifth bit carries. | Trim criteria assert the leading edge bit and the three multiplier bits, and do not assert the full attribute word. | TC-PLL-048, TC-PLL-049, TC-PLL-069 | IP owner |
| `SPEC-GAP-15` | Whether the APB address aliasing above DWORD offset `0x7F` without the soft control register is intended. Spec 1.5.10 documents the truncation and spec Appendix A records it as an open question with the declared 1024-byte block only half distinct in that configuration. | The aliasing is not exercised. TC-PLL-061 and TC-PLL-079 access DWORD offset `0x00` only, so no criterion depends on how the upper half of the block behaves. | TC-PLL-061, TC-PLL-079; the APB-aliasing row of Exclusions | IP owner / metadata owner |
