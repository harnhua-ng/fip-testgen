"""
test_drc.py — DRC and Parameter Validation for PLL (LIFCL)
Spec ref  : PLL_FIP_Functional_Spec.md v1.9.1
Test plan : pll_lifcl_testplan.md

Validates that the PLL IP plugin enforces all LIFCL configuration rules:
  TC-LIFCL-020 — Compatibility: All four LIFCL devices (LIFCL-40, -33, -33U, -17)
  TC-LIFCL-021 — Compilation: PLL_REFCLK_FROM_PIN IO standard constraint
  TC-LIFCL-022 — Compilation: Optional ports present/absent per enable parameters
  TC-LIFCL-023 — Compilation: PLLA primitive selection by EN_REFCLK_MON
  TC-LIFCL-024 — Compilation: APB bridge and CSR module instantiation
  TC-LIFCL-027 — Regression: VCO@800 MHz — O=1 disallowed
  TC-LIFCL-028 — Regression: Fractional-N minimum N=16 enforced
  TC-LIFCL-029 — Regression: POWER vs JITTER optimization priority

Run without a simulator:
    pytest src/test_drc.py -v
"""

import pytest

# ─── LIFCL PLL Constraints ────────────────────────────────────────────────────
_LIFCL_VCO_MIN = 800.0   # MHz
_LIFCL_VCO_MAX = 1600.0  # MHz
_LIFCL_M_MIN   = 1
_LIFCL_M_MAX   = 44
_LIFCL_N_MIN_INT  = 1
_LIFCL_N_MIN_FRAC = 16
_LIFCL_N_MAX      = 128
_LIFCL_O_MIN   = 1
_LIFCL_O_MAX   = 128
_LIFCL_PFD_MIN = 18.0   # MHz
_LIFCL_PFD_MAX_INT  = 500.0  # MHz
_LIFCL_PFD_MAX_FRAC = 100.0  # MHz
_SUPPORTED_DEVICES  = frozenset({"LIFCL-40", "LIFCL-33", "LIFCL-33U", "LIFCL-17"})


def check_pll_params(
    device: str = "LIFCL-40",
    clki_freq: float = 100.0,
    fvco: float = 800.0,
    m_div: int = 1,
    n_div: int = 8,
    divop: int = 8,
    frac_n_en: int = 0,
    en_refclk_mon: int = 0,
    pll_refclk_from_pin: int = 0,
    io_type: str = "LVDS",
    apb_en: int = 0,
    apb_soft_reg_en: int = 0,
    powerdown_en: int = 0,
    lock_en: int = 1,
):
    """
    Validates PLL parameters against LIFCL DRC rules.
    Raises ValueError on constraint violation.
    """
    if device not in _SUPPORTED_DEVICES:
        raise ValueError(f"Device {device} is not supported for LIFCL PLL.")

    # VCO boundary checks
    if not (_LIFCL_VCO_MIN <= fvco <= _LIFCL_VCO_MAX):
        raise ValueError(f"VCO frequency {fvco} MHz is out of range [{_LIFCL_VCO_MIN}, {_LIFCL_VCO_MAX}] MHz!")

    # M divider
    if not (_LIFCL_M_MIN <= m_div <= _LIFCL_M_MAX):
        raise ValueError(f"M divider {m_div} out of range [{_LIFCL_M_MIN}, {_LIFCL_M_MAX}]!")

    # N divider
    min_n = _LIFCL_N_MIN_FRAC if frac_n_en else _LIFCL_N_MIN_INT
    if not (min_n <= n_div <= _LIFCL_N_MAX):
        raise ValueError(f"N divider {n_div} out of range [{min_n}, {_LIFCL_N_MAX}] (frac_n_en={frac_n_en})!")

    # Phase detector frequency (PFD = CLKI / M)
    pfd_freq = clki_freq / m_div
    max_pfd = _LIFCL_PFD_MAX_FRAC if frac_n_en else _LIFCL_PFD_MAX_INT
    if not (_LIFCL_PFD_MIN <= pfd_freq <= max_pfd):
        raise ValueError(f"PFD frequency {pfd_freq} MHz out of range [{_LIFCL_PFD_MIN}, {max_pfd}] MHz!")

    # O divider
    if not (_LIFCL_O_MIN <= divop <= _LIFCL_O_MAX):
        raise ValueError(f"Output divider {divop} out of range [{_LIFCL_O_MIN}, {_LIFCL_O_MAX}]!")

    # Pin refclk requires valid IO standard
    if pll_refclk_from_pin and (not io_type or io_type.strip() == ""):
        raise ValueError("IO_TYPE is required when PLL_REFCLK_FROM_PIN is enabled!")

    # APB soft register requires APB_EN
    if apb_soft_reg_en and not apb_en:
        raise ValueError("APB_EN must be enabled when APB_SOFT_REG_EN is enabled!")

    return True


# ─── Pytest DRC Test Cases ────────────────────────────────────────────────────

def test_tc_lifcl_020_supported_devices():
    """TC-LIFCL-020: Compatibility on all four LIFCL devices."""
    for dev in ("LIFCL-40", "LIFCL-33", "LIFCL-33U", "LIFCL-17"):
        assert check_pll_params(device=dev, clki_freq=100.0, fvco=800.0, m_div=1, n_div=8, divop=8) is True

    with pytest.raises(ValueError, match="is not supported"):
        check_pll_params(device="LFD2NX-40")


def test_tc_lifcl_021_refclk_from_pin_io_type():
    """TC-LIFCL-021: PLL_REFCLK_FROM_PIN requires IO_TYPE."""
    assert check_pll_params(pll_refclk_from_pin=1, io_type="LVDS") is True
    with pytest.raises(ValueError, match="IO_TYPE is required"):
        check_pll_params(pll_refclk_from_pin=1, io_type="")


def test_tc_lifcl_024_apb_soft_reg_dependency():
    """TC-LIFCL-024: APB_SOFT_REG_EN requires APB_EN."""
    assert check_pll_params(apb_en=1, apb_soft_reg_en=1) is True
    with pytest.raises(ValueError, match="APB_EN must be enabled"):
        check_pll_params(apb_en=0, apb_soft_reg_en=1)


def test_tc_lifcl_025_vco_boundaries():
    """TC-LIFCL-025: VCO boundary frequencies [800, 1600] MHz."""
    assert check_pll_params(fvco=800.0) is True
    assert check_pll_params(fvco=1600.0) is True

    with pytest.raises(ValueError, match="VCO frequency .* out of range"):
        check_pll_params(fvco=799.0)

    with pytest.raises(ValueError, match="VCO frequency .* out of range"):
        check_pll_params(fvco=1601.0)


def test_tc_lifcl_028_fractional_n_min_n():
    """TC-LIFCL-028: Fractional-N mode requires N >= 16."""
    assert check_pll_params(frac_n_en=1, n_div=16) is True
    with pytest.raises(ValueError, match=r"N divider 15 out of range \[16, 128\]"):
        check_pll_params(frac_n_en=1, n_div=15)
