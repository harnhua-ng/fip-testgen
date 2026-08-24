# PLL Foundation IP — Test Plan
## LIFCL Device Family | IP Version 1.9.1 | Radiant 2025.1+

| Field | Value |
|---|---|
| Document Status | Draft |
| IP Under Test | PLL FIP v1.9.1 (`lscc_pll`) |
| Device Scope | **LIFCL only** — LIFCL-40, LIFCL-33, LIFCL-33U, LIFCL-17 |
| Excluded Families | LFD2NX, LFCPNX, LFMXO5, UT24C, UT24CP |
| Radiant Version | 2025.1+ |
| Author | Karen Ng |
| Date | 2026-08-01 |
| Source Specification | PLL_FIP_Functional_Spec.md v1.9.1 |

---

## Requirements Source

This test plan is derived directly from `PLL_FIP_Functional_Spec.md` v1.9.1 (reverse-engineered from implementation, 2026-08-01). All section references below (e.g., §7.2) correspond to that document. The GPLL hardware primitive behavior is governed by Lattice GPLL/PLL User Guide (document ID 52468); hardware-level analog parameters are out of scope for this test plan and assumed correct by GPLL silicon verification.

---

## Assumptions

| ID | Assumption |
|---|---|
| A-01 | LIFCL devices use the `PLL` primitive (EN_REFCLK_MON=0) or `PLLA` primitive (EN_REFCLK_MON=1). The `PLLD` primitive is used exclusively on JP devices (UT24CP) and is not testable on LIFCL. |
| A-02 | Simulation tests execute the generated `tb_top.v` testbench against a behavioral model of the GPLL primitive. Output clock frequencies and phases are verified by the built-in `clock_checker` module using 255-sample averaging. |
| A-03 | Radiant Compilation tests verify IP generation + synthesis + MAP/PAR without simulation. Pass criteria are zero errors and zero critical warnings; timing is not the primary metric unless specified. |
| A-04 | The `gpll_cfg_upd.py` post-processor is assumed to run correctly after IP generation (§10.6). Testbench configuration file accuracy is out of scope here. |
| A-05 | APB DWORD address mapping (paddr[9:2]) was introduced in v1.9.0; all APB test cases assume this addressing scheme. |
| A-06 | Fractional-N and SSC can be combined. Test cases exercising both simultaneously are included at system level only. |
| A-07 | The analog loop filter is auto-optimized by the plugin. Analog parameter correctness is tested only through indirect evidence (PLL achieves lock within 700 ms simulation timeout). |

---

## Scope Notes — LIFCL-Specific Constraints

| Constraint | LIFCL Behavior |
|---|---|
| PLL primitives supported | `PLL` (standard), `PLLA` (with reference clock monitor) |
| `PLLD` (JP device primitive) | **Not applicable — excluded from this plan** |
| IS_JP_DEVICE macro | Always `0` on LIFCL |
| VCO range | 800–1600 MHz |
| M divider | 1–44 |
| N divider | 1–128 (integer-N), 16–128 (fractional-N) |
| O dividers | 1–128 each |
| Reference clock monitor | Available via PLLA primitive (TC-LIFCL-012, TC-LIFCL-023) |
| Phase detector frequency | 18–500 MHz (integer-N), 18–100 MHz (fractional-N) |

---

## Coverage Strategy

**Equivalence partitioning:** LIFCL device SKUs share the same silicon architecture (PLL/PLLA primitive). Compilation coverage runs on all four LIFCL devices (TC-LIFCL-020); remaining functional tests default to LIFCL-40 as the representative device.

**Pairwise / combinatorial reduction:** The 17 optional feature flags (reset, powerdown, lock, legacy, 6× clock enable, 4× interface options, CSR, refclk monitor) are not tested in full Cartesian product. Instead:
- Single-feature enable/disable tests cover individual ports.
- TC-LIFCL-030 (System test) exercises a high-density combination (Frac-N + SSC + APB + CSR + refclk mon + dynamic phase).
- TC-LIFCL-026 covers output frequency extremes rather than all intermediate values.

**Boundary value analysis:** VCO boundaries (800 / 1600 MHz), output frequency minima (10 MHz integer-N, 6.25 MHz fractional-N), and N divider minimum in fractional-N mode (N=16) are explicitly tested.

**Risk-based prioritization:** High — integer-N frequency accuracy, lock behavior, LMMI/APB interfaces, PLLA reference monitor. Medium — SSC, dynamic phase, duty trim, powerdown. Low — legacy mode, individual per-device compilation variants.

---

## Acceptance Criteria

### 1. Functional Criteria

| ID | Criterion |
|---|---|
| FUNC-1 | PLL asserts `lock_o` within 700 ms simulation time after reset release. |
| FUNC-2 | CLKOP output frequency matches configured value within ±0.1% (plugin-computed dividers). |
| FUNC-3 | All enabled secondary outputs (CLKOS–CLKOS5) meet configured frequencies within ±0.1%. |
| FUNC-4 | Fractional-N mode generates the target VCO using `N + FRAC/4096` with FRAC in [0, 4095] and N ≥ 16. |
| FUNC-5 | SSC down-spread modulates frequency only below nominal; center-spread modulates symmetrically. |
| FUNC-6 | Static phase shift is correct within ±10% for each of the eight 45° steps on each output clock. |
| FUNC-7 | `phasestep_i` rising edge advances or retards phase by one step according to `phasedir_i`. |
| FUNC-8 | APB write to `pll_csr` PHASESTEP bit produces a one-cycle pulse; bit self-clears. |
| FUNC-9 | `pll_csr` bit[7] (PLL_LOCK) reflects live `lock_o` state on each APB read. |
| FUNC-10 | Duty-cycle trim on CLKOP/CLKOS shifts the specified edge by the encoded multiplier. |
| FUNC-11 | `refdetlos` asserts within a bounded interval after reference clock removal (PLLA, EN_REFCLK_MON=1). |
| FUNC-12 | `refdetlos` deasserts and PLL re-locks after reference clock restoration and `refdetreset` pulse. |
| FUNC-13 | `lock_o` (UFREQ) deasserts immediately on PLL unlock event. |
| FUNC-14 | `lock_o` (SFREQ) remains asserted after unlock; deasserts only after `rstn_i` assertion. |
| FUNC-15 | Asserting `pllpd_en_n_i` (low) stops PLL output clocks; releasing it restores lock. |
| FUNC-16 | Each `enclkox_i` port (when enabled) gates the corresponding output clock only. |
| FUNC-17 | LMMI read returns valid data on `lmmi_rdata_o` with `lmmi_rdata_valid_o` asserted. |
| FUNC-18 | APB write/read completes with `apb_pready_o` asserted; `apb_pslverr_o` deasserted on success. |

### 2. Compilation Criteria

| ID | Criterion |
|---|---|
| COMP-1 | IP generates for all LIFCL devices (LIFCL-40, -33, -33U, -17) without error or critical warning in Radiant 2025.1. |
| COMP-2 | Generated RTL synthesizes and completes MAP/PAR without DRC violations or P&R failures. |
| COMP-3 | `constraint.ldc` contains a `create_clock` constraint on `clki_i` with period = round(1,000,000 / F_REF) ns. |
| COMP-4 | When `PLL_REFCLK_FROM_PIN=1`, `constraint.ldc` contains an `ldc_set_port -iobuf IO_TYPE=<std>` on `clki_i`. |
| COMP-5 | EN_REFCLK_MON=1 causes generated RTL to instantiate `PLLA` (not `PLL`) as the hardware primitive. |
| COMP-6 | APB_EN=1 instantiates `lscc_apb2lmmi` bridge; APB_EN=0 omits it. |
| COMP-7 | APB_SOFT_REG_EN=1 (with APB_EN=1) instantiates `pll_csr`; otherwise `pll_csr` is absent. |
| COMP-8 | Optional ports (`rstn_i`, `pllpd_en_n_i`, `legacy_i`, `enclkop_i`–`enclkos5_i`) appear only when their respective enable parameter is 1. |

### 3. Integration Criteria

| ID | Criterion |
|---|---|
| INTEG-1 | APB `paddr[9:2]` values 0x00–0x7F route to GPLL internal registers (LMMI offset bit[7]=0). |
| INTEG-2 | APB `paddr[9:2]` values 0x80–0xFF route to soft CSR (LMMI offset bit[7]=1) when APB_SOFT_REG_EN=1. |
| INTEG-3 | Only one of LMMI or APB interfaces may be active simultaneously; dual-enable is blocked by the plugin. |

### 4. Compatibility Criteria

| ID | Criterion |
|---|---|
| COMPAT-1 | All four LIFCL device variants compile without error using default PLL parameters. |
| COMPAT-2 | POWER optimization selects a lower VCO frequency than JITTER optimization for identical target frequencies. |
| COMPAT-3 | DIVIDER mode accepts user-specified M, N, O values that satisfy VCO range constraints. |

### 5. Entry / Exit Criteria

**Entry Criteria:**
- PLL FIP v1.9.1 IP package available in Radiant 2025.1 installation.
- LIFCL device database available.
- Simulation environment (ModelSim/Active-HDL) accessible.
- Functional Specification v1.9.1 reviewed and baselined.

**Exit Criteria:**
- All High priority test cases pass.
- No Critical or Blocker defects open.
- Medium priority pass rate ≥ 90%.
- All Compilation test cases pass on all four LIFCL device variants.

---

## Test Cases

> **Method Legend:**
> - `Compilation` — Radiant IP generation + synthesis + MAP/PAR only; no simulation runtime required.
> - `Simulation` — Runs the generated `tb_top.v` testbench in a Verilog/SV simulator; verifies functional behavior at RTL level.
> - `Both` — Requires compilation pass first (RTL must be valid), then simulation for functional checks.

### Summary Table

| TC ID | Title | Type | Priority | Method |
|---|---|---|---|---|
| TC-LIFCL-001 | Smoke: Basic IP generation and P&R (LIFCL-40, single CLKOP 100 MHz) | Smoke | High | **Compilation** |
| TC-LIFCL-002 | Functional: Integer-N — lock acquisition and CLKOP frequency accuracy | Functional | High | **Simulation** |
| TC-LIFCL-003 | Functional: Integer-N — all 6 output clocks enabled simultaneously | Functional | High | **Simulation** |
| TC-LIFCL-004 | Functional: Fractional-N — non-integer frequency synthesis | Functional | High | **Simulation** |
| TC-LIFCL-005 | Functional: SSC — down-spread profile (1.0% depth) | Functional | Medium | **Simulation** |
| TC-LIFCL-006 | Functional: SSC — center-spread profile (0.5% depth) | Functional | Medium | **Simulation** |
| TC-LIFCL-007 | Functional: Static phase adjustment — all eight 45° steps on CLKOP | Functional | High | **Simulation** |
| TC-LIFCL-008 | Functional: Dynamic phase control — port-driven (phasedir/phasestep) | Functional | High | **Simulation** |
| TC-LIFCL-009 | Functional: Dynamic phase control — APB soft CSR register write | Functional | High | **Simulation** |
| TC-LIFCL-010 | Functional: Duty-cycle trim on CLKOP — Rising edge, multiplier sweep | Functional | Medium | **Simulation** |
| TC-LIFCL-011 | Functional: Duty-cycle trim on CLKOS — Falling edge | Functional | Medium | **Simulation** |
| TC-LIFCL-012 | Functional: Reference clock monitor — refdetlos on loss of CLKI (PLLA) | Functional | High | **Simulation** |
| TC-LIFCL-013 | Functional: Lock output — UFREQ (non-sticky) deasserts on unlock | Functional | High | **Simulation** |
| TC-LIFCL-014 | Functional: Lock output — SFREQ (sticky) persists until reset | Functional | Medium | **Simulation** |
| TC-LIFCL-015 | Functional: Powerdown (pllpd_en_n_i) and recovery to lock | Functional | Medium | **Simulation** |
| TC-LIFCL-016 | Functional: Clock enable ports gate respective output clocks | Functional | Medium | **Simulation** |
| TC-LIFCL-017 | Integration: LMMI slave — read/write transaction protocol | Integration | High | **Simulation** |
| TC-LIFCL-018 | Integration: APB slave — DWORD address mapping (paddr[9:2] → LMMI offset) | Integration | High | **Simulation** |
| TC-LIFCL-019 | Integration: APB soft CSR — address space routing (bit[7] distinction) and PLL_LOCK readback | Integration | High | **Simulation** |
| TC-LIFCL-020 | Compatibility: All four LIFCL devices — IP generation and compilation | Compatibility | High | **Compilation** |
| TC-LIFCL-021 | Compilation: PLL_REFCLK_FROM_PIN=1 — IO standard and clock constraints in .ldc | Functional | High | **Compilation** |
| TC-LIFCL-022 | Compilation: Optional ports present/absent per enable parameters | Functional | High | **Compilation** |
| TC-LIFCL-023 | Compilation: PLLA selected when EN_REFCLK_MON=1; PLL when =0 | Functional | High | **Compilation** |
| TC-LIFCL-024 | Compilation: APB bridge and CSR module instantiation correctness | Functional | High | **Compilation** |
| TC-LIFCL-025 | Regression: VCO boundary frequencies — 800 MHz and 1600 MHz | Regression | High | **Both** |
| TC-LIFCL-026 | Regression: Minimum output frequency boundaries (10 MHz int-N, 6.25 MHz frac-N) | Regression | High | **Both** |
| TC-LIFCL-027 | Regression: VCO@800 MHz — O=1 disallowed constraint enforced by plugin | Regression | High | **Compilation** |
| TC-LIFCL-028 | Regression: Fractional-N minimum N divider = 16 enforced | Regression | High | **Compilation** |
| TC-LIFCL-029 | Regression: POWER vs JITTER optimization — correct VCO selection | Regression | Medium | **Compilation** |
| TC-LIFCL-030 | System: Full-feature configuration compile and simulate | System | High | **Both** |
| TC-LIFCL-031 | Acceptance: tb_top.v lock assertion within 700 ms simulation timeout | Acceptance | High | **Simulation** |
| TC-LIFCL-032 | Acceptance: tb_top.v output frequency within 10% tolerance (clock_checker) | Acceptance | High | **Simulation** |
| TC-LIFCL-033 | Acceptance: tb_top.v phase relationship within 10% tolerance (clock_checker) | Acceptance | Medium | **Simulation** |
| TC-LIFCL-034 | Sanity: Radiant FREQUENCY mode vs DIVIDER mode — parameter consistency | Sanity | Medium | **Compilation** |

---

### Detailed Test Cases

---

#### TC-LIFCL-001 — Smoke: Basic IP generation and P&R

| Field | Value |
|---|---|
| **Test Type** | Smoke |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-1, COMP-2 |
| **Spec Reference** | §3, §10.7 |

**Prerequisites:** Radiant 2025.1 installed with LIFCL-40 device database.

**Test Steps:**
1. Open Radiant IP Wizard, select PLL v1.9.1 for LIFCL-40.
2. Set `gui_refclk_freq = 100 MHz`, `gui_clkop_freq = 100 MHz`, all other options at defaults.
3. Click **Calculate**, then **Generate**.
4. Compile the generated project through MAP and PAR.

**Expected Results:**
- IP generation completes with zero errors and zero critical warnings.
- Synthesis, MAP, and PAR complete without errors.
- No DRC violations.

---

#### TC-LIFCL-002 — Functional: Integer-N lock and CLKOP frequency accuracy

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-1, FUNC-2 |
| **Spec Reference** | §7.2, §7.3, §10.8 |

**Prerequisites:** IP generated with: `refclk=100 MHz`, `CLKOP=125 MHz`, `LOCK_EN=1`, `PLL_RST=1`. Simulation environment available.

**Test Steps:**
1. Run simulation of generated `tb_top.v`.
2. Assert `rstn_i` low for 10 ns, then deassert.
3. Monitor `lock_o` signal.
4. After `lock_o` asserts, measure CLKOP period using `clock_checker`.

**Expected Results:**
- `lock_o` asserts within 700 ms simulation time (FUNC-1).
- Measured CLKOP frequency is within ±0.1% of 125 MHz (FUNC-2).

---

#### TC-LIFCL-003 — Functional: Integer-N, all 6 output clocks

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-1, FUNC-3 |
| **Spec Reference** | §7.6 |

**Prerequisites:** IP generated with: `refclk=100 MHz`, CLKOP=200 MHz, CLKOS=100 MHz, CLKOS2=50 MHz, CLKOS3=25 MHz, CLKOS4=10 MHz, CLKOS5=40 MHz. All `CLKOSx_EN=1`.

**Test Steps:**
1. Run simulation of `tb_top.v`.
2. After lock asserts, verify frequency of each of the six output clocks via `clock_checker`.

**Expected Results:**
- `lock_o` asserts within 700 ms.
- All six output clocks are within ±0.1% of their configured frequencies.
- No output clock is unexpectedly absent or always-high/always-low.

---

#### TC-LIFCL-004 — Functional: Fractional-N frequency synthesis

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-1, FUNC-4 |
| **Spec Reference** | §7.4 |

**Prerequisites:** IP generated with: `gui_en_frac_n=True`, `refclk=100 MHz`, `CLKOP=133.333 MHz` (not achievable in integer-N with ≤ 0.1% tolerance).

**Test Steps:**
1. Confirm plugin computes `N ≥ 16` and `FRAC ∈ [0, 4095]`.
2. Run simulation of `tb_top.v`.
3. Measure CLKOP frequency after lock.

**Expected Results:**
- `lock_o` asserts within 700 ms.
- CLKOP frequency is within ±0.1% of 133.333 MHz.
- `SSC_N_CODE_STR` and `SSC_F_CODE_STR` in generated RTL encode the correct fractional divider.

---

#### TC-LIFCL-005 — Functional: SSC down-spread (1.0% depth)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-5 |
| **Spec Reference** | §7.5 |

**Prerequisites:** IP generated with: `gui_en_ssc=True`, `gui_ssc_profile=DOWN`, `gui_ssc_mod_depth=1.0`, `refclk=100 MHz`, `CLKOP=200 MHz`.

**Test Steps:**
1. Run simulation.
2. Monitor CLKOP period over time during lock.
3. Verify that the measured frequency varies only below the nominal 200 MHz.
4. Verify that the peak-to-peak variation corresponds to the 1.0% programmed depth.

**Expected Results:**
- CLKOP frequency modulates between approximately 198 MHz and 200 MHz (down-spread only).
- No frequency excursion above nominal.
- PLL remains locked throughout.

---

#### TC-LIFCL-006 — Functional: SSC center-spread (0.5% depth)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-5 |
| **Spec Reference** | §7.5 |

**Prerequisites:** IP generated with: `gui_en_ssc=True`, `gui_ssc_profile=CENTER`, `gui_ssc_mod_depth=0.5`, `refclk=100 MHz`, `CLKOP=200 MHz`.

**Test Steps:**
1. Run simulation.
2. Monitor CLKOP period over several SSC modulation cycles.
3. Verify frequency spreads symmetrically above and below 200 MHz.

**Expected Results:**
- CLKOP modulates approximately ±0.25% around 200 MHz (199.5 MHz to 200.5 MHz).
- Symmetric spread confirmed; PLL remains locked.

---

#### TC-LIFCL-007 — Functional: Static phase adjustment — all eight 45° steps

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-6 |
| **Spec Reference** | §7.7 |

**Prerequisites:** Generate eight IP instances for CLKOP with `gui_clkop_phase` = 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315° (CLKOS as reference at 0° in each). `refclk=100 MHz`, `CLKOP=CLKOS=100 MHz`.

**Test Steps:**
1. For each phase configuration, run simulation.
2. After lock, measure time offset between CLKOP rising edge and CLKOS rising edge.
3. Convert to degrees using the 100 MHz period (10 ns → 360°).

**Expected Results:**
- For each configuration, measured phase offset is within ±10% of the specified step (e.g., 90° ± 9°).
- No configuration fails to lock.

---

#### TC-LIFCL-008 — Functional: Dynamic phase control — port-driven

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-7 |
| **Spec Reference** | §7.8 |

**Prerequisites:** IP with `gui_en_dyn_phase=True`, `DYN_PORTS_EN=1`, `APB_SOFT_REG_EN=0`. `refclk=100 MHz`, `CLKOP=100 MHz`.

**Test Steps:**
1. After lock, set `phasesel_i=3'b000` (CLKOP), `phasedir_i=1` (advance).
2. Toggle `phasestep_i` with 3 rising edges.
3. Measure CLKOP phase shift from reference.
4. Repeat with `phasedir_i=0` (retard) and 3 rising edges.

**Expected Results:**
- Each rising edge on `phasestep_i` produces a measurable phase advance (dir=1) or retard (dir=0).
- `phasesel_i` correctly targets only the selected output clock; other outputs are unaffected.

---

#### TC-LIFCL-009 — Functional: Dynamic phase control — APB soft CSR

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-7, FUNC-8, FUNC-9 |
| **Spec Reference** | §7.8, §7.15 |

**Prerequisites:** IP with `APB_EN=1`, `APB_SOFT_REG_EN=1`, `DYN_PORTS_EN=1`. APB master available in testbench.

**Test Steps:**
1. After PLL lock, issue APB write to `pll_csr` (paddr[9]=1) with PHASEDIR=1, PHASESTEP=1, PHASESEL=3'b000.
2. On the next clock, verify PHASESTEP bit reads back as 0 (self-cleared).
3. Read `pll_csr`; verify PLL_LOCK bit (bit[7]) is 1.
4. Assert `rstn_i` briefly; verify PLL_LOCK bit goes to 0 during relock.

**Expected Results:**
- PHASESTEP self-clears after one cycle (FUNC-8).
- PLL_LOCK bit accurately reflects `lock_o` state (FUNC-9).
- Phase advances one step per write (FUNC-7).

---

#### TC-LIFCL-010 — Functional: Duty-cycle trim on CLKOP (Rising, multiplier sweep)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-10 |
| **Spec Reference** | §7.9 |

**Prerequisites:** Generate three IP instances with `TRIM_EN_P=1`, `CLKOP_TRIM_MODE=Rising`, and `CLKOP_TRIM_MULT` = 001, 010, 100.

**Test Steps:**
1. For each trim multiplier, run simulation and measure CLKOP duty cycle (high time / period).
2. Compare duty cycles across multiplier values.

**Expected Results:**
- Duty cycle shifts with increasing multiplier (monotonically increasing or decreasing rising-edge delay).
- Trim with multiplier 000 (no delay) matches untrimmed configuration baseline.
- All configurations lock successfully.

---

#### TC-LIFCL-011 — Functional: Duty-cycle trim on CLKOS (Falling)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-10 |
| **Spec Reference** | §7.9 |

**Prerequisites:** IP with `CLKOS_EN=1`, `TRIM_EN_S=1`, `CLKOS_TRIM_MODE=Falling`, `CLKOS_TRIM_MULT=010`.

**Test Steps:**
1. Run simulation, measure CLKOS duty cycle (low time = falling-edge delay target).
2. Compare to baseline with trim disabled.

**Expected Results:**
- CLKOS falling-edge delay shifts by the encoded multiplier.
- CLKOP (untrimmed) remains unchanged.

---

#### TC-LIFCL-012 — Functional: Reference clock monitor (PLLA) — refdetlos assertion

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-11, FUNC-12 |
| **Spec Reference** | §7.10 |

**Prerequisites:** IP with `EN_REFCLK_MON=1` (instantiates PLLA), `REF_OSC_CTRL=3P2`, `LOCK_EN=1`.

**Test Steps:**
1. Run simulation to lock.
2. Stop driving `clki_i` (remove reference clock) at time T1.
3. Monitor `refdetlos` output.
4. Restart `clki_i` at time T2; pulse `refdetreset` high.
5. Monitor `lock_o` and `refdetlos`.

**Expected Results:**
- `refdetlos` asserts within a bounded interval after T1 (FUNC-11).
- After T2 + `refdetreset`, `refdetlos` deasserts and `lock_o` re-asserts (FUNC-12).
- Generated RTL instantiates `PLLA`, not `PLL` (confirmed by waveform or RTL inspection).

---

#### TC-LIFCL-013 — Functional: Lock output — UFREQ (non-sticky)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-13 |
| **Spec Reference** | §7.11 |

**Prerequisites:** IP with `LOCK_EN=1`, `PLL_LOCK_STICKY=UFREQ`. Testbench can perturb `clki_i` frequency.

**Test Steps:**
1. Run simulation to lock.
2. Abruptly change `clki_i` frequency to induce an unlock event.
3. Observe `lock_o`.

**Expected Results:**
- `lock_o` deasserts immediately (within a few clock cycles) on the unlock event.
- `lock_o` re-asserts after PLL re-locks to the new frequency (or original, once restored).

---

#### TC-LIFCL-014 — Functional: Lock output — SFREQ (sticky)

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-14 |
| **Spec Reference** | §7.11 |

**Prerequisites:** IP with `LOCK_EN=1`, `PLL_LOCK_STICKY=SFREQ`, `PLL_RST=1`.

**Test Steps:**
1. Run simulation to lock; verify `lock_o` asserts.
2. Perturb `clki_i` to induce unlock.
3. Observe `lock_o` — it must remain asserted (sticky).
4. Assert `rstn_i` low.
5. Observe `lock_o` — it must deassert.
6. Release `rstn_i`; verify PLL re-locks.

**Expected Results:**
- `lock_o` stays asserted after step 2 (FUNC-14).
- `lock_o` deasserts only after `rstn_i` assertion in step 4.
- PLL re-locks after reset release.

---

#### TC-LIFCL-015 — Functional: Powerdown and recovery

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-15 |
| **Spec Reference** | §7.12 |

**Prerequisites:** IP with `POWERDOWN_EN=1`, `LOCK_EN=1`.

**Test Steps:**
1. Run simulation to lock.
2. Assert `pllpd_en_n_i` low (powerdown).
3. Verify `lock_o` deasserts and output clocks stop.
4. Deassert `pllpd_en_n_i` high (power restored).
5. Verify `lock_o` re-asserts and output clocks resume.

**Expected Results:**
- `lock_o` deasserts within bounded time after powerdown assertion.
- Output clocks gate off during powerdown.
- After powerdown release, PLL goes through normal lock sequence (FUNC-15).

---

#### TC-LIFCL-016 — Functional: Clock enable ports

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-16 |
| **Spec Reference** | §7.6 |

**Prerequisites:** IP with all six `ENCLKOx_EN=1`, all six outputs enabled at distinct frequencies.

**Test Steps:**
1. After lock, assert `enclkop_i=0`; verify CLKOP stops toggling while CLKOS–CLKOS5 continue.
2. Deassert `enclkop_i=1`; verify CLKOP resumes.
3. Repeat steps 1–2 for each of `enclkos_i` through `enclkos5_i` independently.

**Expected Results:**
- Each `enclkox_i=0` gates only that specific output clock.
- All other output clocks are unaffected by the gated clock's enable state (FUNC-16).

---

#### TC-LIFCL-017 — Integration: LMMI slave read/write

| Field | Value |
|---|---|
| **Test Type** | Integration |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-17, INTEG-3 |
| **Spec Reference** | §7.14.1 |

**Prerequisites:** IP with `LMMI_EN=1`. LMMI master driver in testbench.

**Test Steps:**
1. Issue LMMI write: `lmmi_request_i=1`, `lmmi_wr_rdn_i=1`, `lmmi_offset_i=7'h00`, `lmmi_wdata_i=8'hAA`.
2. Wait for `lmmi_ready_o`.
3. Issue LMMI read at the same offset: `lmmi_wr_rdn_i=0`.
4. Capture `lmmi_rdata_o` when `lmmi_rdata_valid_o=1`.

**Expected Results:**
- Write completes with `lmmi_ready_o` asserted (FUNC-17).
- Read returns expected data with `lmmi_rdata_valid_o=1`.
- `lmmi_ready_o` deasserts when no transaction is pending.

---

#### TC-LIFCL-018 — Integration: APB slave DWORD address mapping

| Field | Value |
|---|---|
| **Test Type** | Integration |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-18, INTEG-1 |
| **Spec Reference** | §7.14.2 |

**Prerequisites:** IP with `APB_EN=1`. APB master in testbench.

**Test Steps:**
1. Issue APB write to `apb_paddr_i = 32'h00000008` (DWORD 2, paddr[9:2]=0x02).
2. Wait for `apb_pready_o`.
3. Issue APB read to the same address.
4. Verify `apb_prdata_o` lower byte returns expected data.
5. Verify `apb_pslverr_o` is deasserted.
6. Verify `lmmi_offset_i = 7'h02` was presented to the GPLL (DWORD → LMMI offset mapping).

**Expected Results:**
- APB transactions complete with `apb_pready_o` asserted (FUNC-18).
- `paddr[9:2]` correctly translates to LMMI offset (INTEG-1).
- `apb_pslverr_o` is 0 on successful transactions.

---

#### TC-LIFCL-019 — Integration: APB soft CSR address routing and PLL_LOCK readback

| Field | Value |
|---|---|
| **Test Type** | Integration |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-8, FUNC-9, INTEG-1, INTEG-2 |
| **Spec Reference** | §7.15, §8.1 |

**Prerequisites:** IP with `APB_EN=1`, `APB_SOFT_REG_EN=1`.

**Test Steps:**
1. After lock, issue APB read to `paddr[9:2]=0x00` (bit[7]=0 → GPLL register space).
2. Issue APB read to `paddr[9:2]=0x80` (bit[7]=1 → soft CSR space).
3. Verify bit[7] of CSR read result = 1 (lock asserted).
4. Assert `rstn_i` briefly; re-read CSR; verify bit[7] = 0 (lock deasserted).

**Expected Results:**
- Address 0x00–0x7F (bit[7]=0) routes to GPLL internal registers (INTEG-1).
- Address 0x80–0xFF (bit[7]=1) routes to `pll_csr` (INTEG-2).
- PLL_LOCK bit accurately reflects live lock status (FUNC-9).

---

#### TC-LIFCL-020 — Compatibility: All four LIFCL devices

| Field | Value |
|---|---|
| **Test Type** | Compatibility |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40, LIFCL-33, LIFCL-33U, LIFCL-17 |
| **Acceptance Criteria** | COMP-1, COMPAT-1 |
| **Spec Reference** | §3 |

**Prerequisites:** Radiant 2025.1 with all four LIFCL device databases installed.

**Test Steps:**
1. For each device (LIFCL-40, LIFCL-33, LIFCL-33U, LIFCL-17):
   a. Generate PLL IP with defaults: `refclk=100 MHz`, `CLKOP=100 MHz`.
   b. Compile through MAP and PAR.
2. Record pass/fail per device.

**Expected Results:**
- All four devices generate and compile without errors or critical warnings (COMP-1, COMPAT-1).

---

#### TC-LIFCL-021 — Compilation: PLL_REFCLK_FROM_PIN IO standard constraint

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-3, COMP-4 |
| **Spec Reference** | §9, §6.6 |

**Prerequisites:** IP generated with `PLL_REFCLK_FROM_PIN=1`, `gui_refclk_io_type=LVCMOS25`.

**Test Steps:**
1. Generate IP.
2. Inspect generated `constraint.ldc`.
3. Verify presence of `create_clock -name {clki_i} -period <value> [get_ports clki_i]`.
4. Verify presence of `ldc_set_port -iobuf IO_TYPE=LVCMOS25 [get_ports clki_i]`.
5. Compile through PAR.

**Expected Results:**
- `create_clock` constraint on `clki_i` with correct period = round(1,000,000 / 100) ns = 10.000 ns (COMP-3).
- `ldc_set_port` with `IO_TYPE=LVCMOS25` present only when `PLL_REFCLK_FROM_PIN=1` (COMP-4).
- Compilation succeeds.

---

#### TC-LIFCL-022 — Compilation: Optional ports present/absent per enable parameters

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-8 |
| **Spec Reference** | §5.1, §5.4, §6.6 |

**Test Steps:**

Generate and inspect the RTL (`lscc_pll.v`) for each of the following configurations:

| Parameter | Expected port present | Expected when disabled |
|---|---|---|
| `PLL_RST=1` | `rstn_i` | Tied HIGH |
| `POWERDOWN_EN=1` | `pllpd_en_n_i` | Tied HIGH |
| `LEGACY_EN=1` | `legacy_i` | Tied HIGH |
| `ENCLKOP_EN=1` | `enclkop_i` | Tied HIGH |
| `CLKOS_EN=1` + `ENCLKOS_EN=1` | `enclkos_i` | Tied HIGH |

**Expected Results:**
- Each optional port appears in the port list when its enable=1 and is absent (or tied) when enable=0 (COMP-8).
- Compilation succeeds for both enabled and disabled configurations.

---

#### TC-LIFCL-023 — Compilation: PLLA primitive selection by EN_REFCLK_MON

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-5 |
| **Spec Reference** | §7.1 |

**Test Steps:**
1. Generate IP with `gui_en_refclk_mon=False`. Inspect generated RTL for primitive instantiation keyword.
2. Generate IP with `gui_en_refclk_mon=True`. Inspect generated RTL.
3. Compile both configurations.

**Expected Results:**
- `gui_en_refclk_mon=False` → RTL contains `PLL` primitive instantiation (COMP-5).
- `gui_en_refclk_mon=True` → RTL contains `PLLA` primitive instantiation; `refdetlos` and `refdetreset` ports wired (COMP-5).
- Both configurations compile without errors.

---

#### TC-LIFCL-024 — Compilation: APB bridge and CSR module instantiation

| Field | Value |
|---|---|
| **Test Type** | Functional |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-6, COMP-7 |
| **Spec Reference** | §7.16, §7.15 |

**Test Steps:**
Generate and inspect RTL for the following 4 configurations:

| APB_EN | APB_SOFT_REG_EN | Expected |
|---|---|---|
| 0 | 0 | No bridge, no CSR |
| 1 | 0 | `lscc_apb2lmmi` present; no `pll_csr` |
| 1 | 1 | Both `lscc_apb2lmmi` and `pll_csr` present |
| 0 | 1 (invalid) | Plugin should error / reject |

**Expected Results:**
- Configurations 1–3 match expected instantiation (COMP-6, COMP-7).
- Configuration 4 is rejected by the plugin with an error message.
- All valid configurations compile through PAR without errors.

---

#### TC-LIFCL-025 — Regression: VCO boundary frequencies

| Field | Value |
|---|---|
| **Test Type** | Regression |
| **Priority** | High |
| **Method** | **Both** (Compilation first, then Simulation) |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-2, FUNC-1, FUNC-2 |
| **Spec Reference** | §7.2 |

**Test Steps:**
1. Configure: `refclk=100 MHz`, target VCO ≈ 800 MHz (e.g., CLKOP=800 MHz, O=1 if allowed; or CLKOP=400 MHz, O=2).
   - **Note:** When VCO=800 MHz and feedback uses an output divider, O=1 is disallowed (§7.3). Use O=2 with N adjusted accordingly.
2. Compile → verify no errors. (Compilation phase.)
3. Simulate → verify lock, CLKOP frequency. (Simulation phase.)
4. Repeat for VCO ≈ 1600 MHz (e.g., CLKOP=800 MHz, O=2, N×M to give VCO=1600 MHz).

**Expected Results:**
- Both VCO extremes compile and simulate without errors.
- Lock achieved within 700 ms in both cases.
- Output clock frequency within ±0.1%.

---

#### TC-LIFCL-026 — Regression: Minimum output frequency boundaries

| Field | Value |
|---|---|
| **Test Type** | Regression |
| **Priority** | High |
| **Method** | **Both** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-1, FUNC-1, FUNC-2 |
| **Spec Reference** | §7.3, §10.5 |

**Test Steps:**
1. **Integer-N case:** Configure `CLKOP = 10 MHz` (minimum). Compile and simulate.
2. **Fractional-N case:** Configure `gui_en_frac_n=True`, `CLKOP = 6.25 MHz` (minimum). Compile and simulate.
3. **Below minimum (negative test):** Request `CLKOP = 9 MHz` in integer-N mode; verify the plugin reports an error and refuses to generate.

**Expected Results:**
- 10 MHz (integer-N): generation succeeds, compiles, simulates to lock with correct frequency.
- 6.25 MHz (fractional-N): generation succeeds, compiles, simulates to lock with correct frequency.
- 9 MHz (integer-N): plugin rejects with a clear error message (§10.5).

---

#### TC-LIFCL-027 — Regression: VCO@800 MHz — O=1 disallowed

| Field | Value |
|---|---|
| **Test Type** | Regression |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-1 |
| **Spec Reference** | §7.3 |

**Test Steps:**
1. Request a configuration where F_VCO=800 MHz and the feedback divider uses an output clock (e.g., `gui_fbk_mode=CLKOP`).
2. Inspect the plugin-computed O divider for the feedback output.
3. Verify O ≠ 1.

**Expected Results:**
- Plugin selects O ≥ 2 (e.g., O=2 with N adjusted) to avoid the known PLL instability at VCO=800 MHz with O=1.
- No error or PLL instability in the generated configuration.
- Compilation succeeds.

---

#### TC-LIFCL-028 — Regression: Fractional-N minimum N=16 enforced

| Field | Value |
|---|---|
| **Test Type** | Regression |
| **Priority** | High |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMP-1 |
| **Spec Reference** | §7.4, §10.4 |

**Test Steps:**
1. Enable fractional-N mode.
2. In DIVIDER mode, attempt to set `gui_n_div = 10` (below minimum of 16).
3. Verify that the plugin either auto-corrects to N ≥ 16 or raises a validation error.

**Expected Results:**
- Plugin enforces N ≥ 16 in fractional-N mode.
- Generated RTL (if any) has `FBCLK_DIVIDER_ACTUAL_STR ≥ 16`.
- No configuration with N < 16 is accepted silently.

---

#### TC-LIFCL-029 — Regression: POWER vs JITTER optimization priority

| Field | Value |
|---|---|
| **Test Type** | Regression |
| **Priority** | Medium |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMPAT-2 |
| **Spec Reference** | §7.3, §6.1 |

**Test Steps:**
1. Generate IP A: `gui_optim_prio=POWER`, `refclk=50 MHz`, `CLKOP=200 MHz`.
2. Record computed M, N, O values and derived VCO frequency from generated RTL.
3. Generate IP B: same frequencies, `gui_optim_prio=JITTER`.
4. Record M, N, O, VCO.
5. Compare VCO of A vs B.

**Expected Results:**
- POWER mode selects a lower VCO frequency than JITTER mode for the same target output (COMPAT-2).
- Both configurations are valid (VCO ∈ [800, 1600] MHz) and compile cleanly.

---

#### TC-LIFCL-030 — System: Full-feature configuration

| Field | Value |
|---|---|
| **Test Type** | System |
| **Priority** | High |
| **Method** | **Both** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-1 through FUNC-18, COMP-2, INTEG-3 |
| **Spec Reference** | All |

**Prerequisites:** Single IP with: `gui_en_frac_n=True`, `gui_en_ssc=True` (down-spread, 0.5%), `EN_REFCLK_MON=1` (PLLA), all 6 outputs enabled, `APB_EN=1`, `APB_SOFT_REG_EN=1`, `DYN_PORTS_EN=1`, `POWERDOWN_EN=1`, `LOCK_EN=1`, `PLL_RST=1`, CLKOP duty-cycle trim enabled.

**Test Steps:**
1. Generate and compile through PAR. (Compilation phase.)
2. Run full simulation:
   a. Reset and wait for lock.
   b. Verify all 6 output frequencies.
   c. Issue APB write to CSR to advance phase on CLKOP.
   d. Assert powerdown, then release; verify relock.
   e. Stop `clki_i`; verify `refdetlos` asserts.
   f. Resume `clki_i`; verify `refdetlos` deasserts and PLL relocks.

**Expected Results:**
- Compilation: zero errors.
- Simulation: all sub-checks from steps 2a–2f pass.
- No interaction defects between concurrently enabled features.

---

#### TC-LIFCL-031 — Acceptance: tb_top.v lock assertion within 700 ms

| Field | Value |
|---|---|
| **Test Type** | Acceptance |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-1 |
| **Spec Reference** | §10.8 |

**Test Steps:**
1. Generate IP with default parameters (`refclk=100 MHz`, `CLKOP=100 MHz`).
2. Run the generated `tb_top.v` with a 700 ms simulation timeout.
3. Check if the `lock_check` assertion in the testbench passes before timeout.

**Expected Results:**
- `lock_o` asserts within 700 ms.
- Testbench does not time out.
- No simulation errors related to lock failure.

---

#### TC-LIFCL-032 — Acceptance: tb_top.v output frequency within 10% tolerance

| Field | Value |
|---|---|
| **Test Type** | Acceptance |
| **Priority** | High |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-2, FUNC-3 |
| **Spec Reference** | §10.8 |

**Test Steps:**
1. Run `tb_top.v` (from TC-LIFCL-003 configuration with 6 outputs).
2. Allow `clock_checker` module to accumulate 255 samples on each output.
3. Observe `freq_check_done` signals; check `freq_error` flags.

**Expected Results:**
- All `clock_checker` instances report frequencies within ±10% of configured values.
- No `freq_error` asserted.
- Test completion signals assert before simulation timeout.

---

#### TC-LIFCL-033 — Acceptance: tb_top.v phase relationship within 10% tolerance

| Field | Value |
|---|---|
| **Test Type** | Acceptance |
| **Priority** | Medium |
| **Method** | **Simulation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | FUNC-6 |
| **Spec Reference** | §10.8 |

**Test Steps:**
1. Use IP from TC-LIFCL-007 (CLKOP at 90°, CLKOS at 0°, both 100 MHz).
2. Run `tb_top.v`; observe `clock_checker` phase measurement.
3. Verify measured CLKOP–CLKOS phase offset is within ±10% of 90° (81°–99°).

**Expected Results:**
- Phase check in testbench passes within ±10% tolerance.
- `phase_error` flag not asserted.

---

#### TC-LIFCL-034 — Sanity: FREQUENCY mode vs DIVIDER mode parameter consistency

| Field | Value |
|---|---|
| **Test Type** | Sanity |
| **Priority** | Medium |
| **Method** | **Compilation** |
| **Device** | LIFCL-40 |
| **Acceptance Criteria** | COMPAT-3 |
| **Spec Reference** | §6.1 |

**Test Steps:**
1. Generate IP A in FREQUENCY mode: `refclk=100 MHz`, `CLKOP=200 MHz`.
   Record plugin-computed M, N, O values from generated RTL parameters.
2. Generate IP B in DIVIDER mode using the exact M, N, O values from step 1.
3. Compare generated RTL parameters of A and B.
4. Compile both.

**Expected Results:**
- Both configurations produce identical RTL parameters (same M, N, O, analog filter values).
- Both compile without errors (COMPAT-3).
- DIVIDER mode accepts valid M, N, O values without error.

---

## Simulation vs. Radiant Compilation — Classification Summary

> This section directly answers the user's request: which test cases require simulation vs. Radiant Compilation.

### Simulation-Based Tests (21 test cases)

These tests require running the generated `tb_top.v` (or a custom testbench) in a Verilog/SystemVerilog simulator. They verify **runtime functional behavior** — timing, frequency, phase, protocol transactions, and dynamic state changes — that cannot be confirmed by static RTL inspection or compilation alone.

| TC ID | Title | Why Simulation is Required |
|---|---|---|
| TC-LIFCL-002 | Integer-N lock and CLKOP frequency | Lock and frequency are dynamic; require simulation time |
| TC-LIFCL-003 | All 6 output clocks | Multi-clock frequency measurement requires simulation |
| TC-LIFCL-004 | Fractional-N synthesis | Fractional frequency accuracy measurable only in simulation |
| TC-LIFCL-005 | SSC down-spread | Frequency modulation profile verifiable only in simulation |
| TC-LIFCL-006 | SSC center-spread | Same as above |
| TC-LIFCL-007 | Static phase adjustment | Edge-to-edge timing measurement requires simulation |
| TC-LIFCL-008 | Dynamic phase — port-driven | Protocol sequencing (phasestep toggle, effect measurement) |
| TC-LIFCL-009 | Dynamic phase — APB CSR | APB transaction sequences; self-clearing bit behavior |
| TC-LIFCL-010 | Duty-cycle trim CLKOP | Duty cycle measurement is a simulation-time measurement |
| TC-LIFCL-011 | Duty-cycle trim CLKOS | Same as above |
| TC-LIFCL-012 | Reference clock monitor | Loss-of-signal detection is a dynamic event |
| TC-LIFCL-013 | Lock UFREQ (non-sticky) | Lock deassertion timing after perturbation |
| TC-LIFCL-014 | Lock SFREQ (sticky) | Sticky behavior persists after unlock — requires stimulus |
| TC-LIFCL-015 | Powerdown and recovery | Power-gating and relock sequence is dynamic |
| TC-LIFCL-016 | Clock enable ports | Clock gating verification requires observing toggling/stopping |
| TC-LIFCL-017 | LMMI read/write protocol | Bus handshake (request/ready/rdata_valid) is dynamic |
| TC-LIFCL-018 | APB DWORD address mapping | APB transaction protocol (penable/pready timing) |
| TC-LIFCL-019 | APB CSR routing and PLL_LOCK | Requires live lock state + APB transaction to read it |
| TC-LIFCL-031 | Testbench lock assertion 700 ms | Acceptance gate: testbench's built-in lock check |
| TC-LIFCL-032 | Testbench frequency 10% tolerance | clock_checker requires 255 simulation cycles to conclude |
| TC-LIFCL-033 | Testbench phase 10% tolerance | Phase offset is measured in simulation time |

### Radiant Compilation Tests (10 test cases)

These tests verify **static correctness** — that the IP generates valid RTL, that the RTL compiles and places-and-routes cleanly, that constraints are correct, and that the plugin enforces its own rules. No simulation runtime is required.

| TC ID | Title | Why Compilation is Sufficient |
|---|---|---|
| TC-LIFCL-001 | Smoke: basic IP generation and P&R | Basic sanity — IP files correct, PAR clean |
| TC-LIFCL-020 | All four LIFCL devices compile | Cross-device database validation |
| TC-LIFCL-021 | PLL_REFCLK_FROM_PIN constraint | Constraint file content is inspected statically |
| TC-LIFCL-022 | Optional ports present/absent | Port presence is verifiable in generated RTL text |
| TC-LIFCL-023 | PLLA vs PLL primitive selection | Primitive instantiation keyword in generated RTL |
| TC-LIFCL-024 | APB bridge and CSR instantiation | Module hierarchy is verifiable in generated RTL |
| TC-LIFCL-027 | VCO@800 MHz O=1 disallowed | Plugin constraint → RTL parameter inspection only |
| TC-LIFCL-028 | Fractional-N N≥16 enforced | Plugin validation; RTL parameter value check |
| TC-LIFCL-029 | POWER vs JITTER VCO comparison | M/N/O parameters in generated RTL compared statically |
| TC-LIFCL-034 | FREQUENCY vs DIVIDER mode parity | RTL parameters compared between two generated files |

### Tests Requiring Both (3 test cases)

These tests require a **compilation pass first** (to confirm the RTL is valid and the configuration is legal), followed by **simulation** to verify functional behavior at the boundary condition.

| TC ID | Title | Compilation Phase | Simulation Phase |
|---|---|---|---|
| TC-LIFCL-025 | VCO boundary frequencies (800 / 1600 MHz) | Confirm legal config, no PAR errors | Lock and frequency accuracy at VCO extremes |
| TC-LIFCL-026 | Min output frequency (10 / 6.25 MHz) | Plugin accepts boundary; negative case rejected | Simulation confirms lock at 10 MHz / 6.25 MHz |
| TC-LIFCL-030 | Full-feature system configuration | PAR clean with all features enabled simultaneously | End-to-end functional scenario (lock, phase, powerdown, monitor) |

---

## Requirements Coverage

| Requirement | Status |
|---|---|
| Traceability | All TCs reference spec section and acceptance criteria ID. |
| Test Coverage | 34 TCs; all 18 FUNC, 8 COMP, 3 INTEG, 3 COMPAT acceptance criteria covered. |
| Risk Assessment | High-risk areas (frequency accuracy, lock, LMMI/APB) are High priority; boundary cases covered by regression TCs. |
| Resource Allocation | Requires Radiant 2025.1, LIFCL-40/33/33U/17 device databases, Verilog simulator (ModelSim/Active-HDL), LMMI/APB testbench drivers. |
| Timeline | Compilation TCs: low effort (~1 hour each). Simulation TCs: medium effort (~2–4 hours each). Full suite estimated at ~80 hours. |
| Dependencies | GPLL primitive behavioral model must be available for simulation. Plugin (plugin.py) must be accessible within Radiant IP Wizard. |
| Environment Setup | Radiant 2025.1 with LIFCL device support. Simulator must support Verilog-2005 or SystemVerilog 2012. |
| Entry/Exit Criteria | See Acceptance Criteria section above. |
| Defect Management | File defects in Jira; severity: Critical = lock failure, High = frequency/phase error >10%, Medium = optional port mismatch, Low = compile warning. |
| Test Data Requirements | Reference clock: 12 MHz, 25 MHz, 50 MHz, 100 MHz, 200 MHz sweep. Output targets chosen to exercise distinct M/N/O combinations. |

---

*End of Test Plan*

*Source: PLL_FIP_Functional_Spec.md v1.9.1 | Radiant Software Foundation IP | 2026-08-01*
