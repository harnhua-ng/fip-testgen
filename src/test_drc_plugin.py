"""
TG-10 — DRC and Parameter Validation (TC-10-01 ... TC-10-09)

Drives the actual plugin/plugin.py DRC functions invoked by the Radiant IP
Generator, rather than maintaining a local reimplementation.

How it works
------------
plugin.py references two framework globals that are only available inside the
Radiant process:

  PluginUtil   -- emits error/warning messages
  runtime_info -- provides device and instance context

This module stubs PluginUtil so that post_error() messages can be inspected.
runtime_info is NOT needed by any lscc_rom DRC function and is left unset.

The plugin module is loaded from plugin/plugin.py relative to the repo root,
and PluginUtil is injected into its namespace before any test runs.

Run without a simulator:

    pytest src/test_drc_plugin.py -v

Pass/fail criteria (Section 8.2 of ROM_LIFCL_testplan.md):
    PASS -- the plugin function returns 0 and the expected error substring
            appears in the captured PluginUtil message.
    FAIL -- the function returns 1 (accepted), or the wrong error is emitted.

Known gaps (documented inline)
-------------------------------
TC-10-01: RADDR_DEPTH minimum of 2 is enforced by value_range in metadata.xml,
          not by the DRC function (which uses min_addr_depth=1).  The test is
          marked xfail so the discrepancy is visible rather than hidden.

TC-10-08: No ECC drc attribute exists in metadata.xml for lscc_rom and no
          corresponding check function exists in plugin.py.  The test is
          skipped pending the addition of both.
"""

import sys
import pathlib
import importlib
import pytest

# ---------------------------------------------------------------------------
# PluginUtil stub
# ---------------------------------------------------------------------------

class _PluginUtil:
    """Minimal stand-in for the Radiant IP Generator's PluginUtil global."""

    _last_error = None

    @classmethod
    def post_error(cls, msg):
        cls._last_error = str(msg)

    @classmethod
    def reset(cls):
        cls._last_error = None

    @classmethod
    def last_error(cls):
        return cls._last_error


# ---------------------------------------------------------------------------
# Load plugin module and inject the stub
# ---------------------------------------------------------------------------

_PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent / "plugin"

def _load_plugin():
    if str(_PLUGIN_DIR) not in sys.path:
        sys.path.insert(0, str(_PLUGIN_DIR))
    mod = importlib.import_module("plugin")
    mod.PluginUtil = _PluginUtil
    return mod

_plugin = _load_plugin()

# Family token delivered by T_FAMILY for a LIFCL device.
_LIFCL = "LIFCL"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _call(fn, *args):
    """Reset the stub, call fn(*args), return (result, error_message)."""
    _PluginUtil.reset()
    result = fn(*args)
    return result, _PluginUtil.last_error()


# ---------------------------------------------------------------------------
# TC-10-01 — depth below minimum
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=True,
    reason=(
        "check_addr_depth_data_width uses min_addr_depth=1, so RADDR_DEPTH=1 "
        "is accepted by the DRC function.  The testplan minimum of 2 is "
        "enforced by value_range=(2,65536) in metadata.xml, which the GUI "
        "validates before invoking the DRC expression.  Either lower the "
        "testplan minimum to 1 or add an explicit guard in the DRC function."
    ),
)
def test_tc_10_01_depth_below_minimum():
    """TC-10-01: RADDR_DEPTH=1 is below the testplan minimum of 2."""
    # DRC expression from metadata.xml:
    #   check_addr_depth_data_width(RADDR_DEPTH, RADDR_DEPTH, RDATA_WIDTH, RDATA_WIDTH, T_FAMILY)
    result, err = _call(_plugin.check_addr_depth_data_width, 1, 1, 36, 36, _LIFCL)
    assert result == 0, "Expected DRC function to reject RADDR_DEPTH=1"
    assert "Address depth is out of range!" in err


# ---------------------------------------------------------------------------
# TC-10-02 — depth above maximum
# ---------------------------------------------------------------------------

def test_tc_10_02_depth_above_maximum():
    """TC-10-02: RADDR_DEPTH=65537 exceeds the maximum of 65536."""
    result, err = _call(_plugin.check_addr_depth_data_width, 65537, 65537, 1, 1, _LIFCL)
    assert result == 0
    assert "Address depth is out of range!" in err


# ---------------------------------------------------------------------------
# TC-10-03 — width below minimum
# ---------------------------------------------------------------------------

def test_tc_10_03_width_below_minimum():
    """TC-10-03: RDATA_WIDTH=0 is below the minimum of 1."""
    # DRC expression: check_data_width(RADDR_DEPTH, RADDR_DEPTH, RDATA_WIDTH, RDATA_WIDTH)
    result, err = _call(_plugin.check_data_width, 512, 512, 0, 0)
    assert result == 0
    assert "Data width is out of range!" in err


# ---------------------------------------------------------------------------
# TC-10-04 — width above maximum
# ---------------------------------------------------------------------------

def test_tc_10_04_width_above_maximum():
    """TC-10-04: RDATA_WIDTH=513 exceeds the maximum of 512."""
    result, err = _call(_plugin.check_data_width, 2, 2, 513, 513)
    assert result == 0
    assert "Data width is out of range!" in err


# ---------------------------------------------------------------------------
# TC-10-05 — total bits exceed LIFCL limit
# ---------------------------------------------------------------------------

def test_tc_10_05_total_bits_exceed_limit():
    """TC-10-05: RDATA_WIDTH=512, RADDR_DEPTH=4096 → 2,097,152 bits > 1,548,288."""
    result, err = _call(_plugin.check_addr_depth_data_width, 4096, 4096, 512, 512, _LIFCL)
    assert result == 0
    assert "Total memory size exceeds the resource limitation!" in err


# ---------------------------------------------------------------------------
# TC-10-06 — OUTPUT_CLK_EN without REGMODE
# ---------------------------------------------------------------------------

def test_tc_10_06_output_clk_en_without_reg():
    """TC-10-06: OUTPUT_CLK_EN=True with REGMODE=False is rejected.

    REGMODE is a Python bool in the DRC expression (metadata.xml declares
    value_type="bool").  Passing the string "noreg" instead of False would
    make not("noreg") evaluate to False and silently accept the bad config.
    """
    # DRC expression: check_output_clk_en(OUTPUT_CLK_EN, REGMODE)
    result, err = _call(_plugin.check_output_clk_en, True, False)
    assert result == 0
    assert (
        "Enable Output ClockEn is turned on, while Enable Output Register is turned off"
        in err
    )


# ---------------------------------------------------------------------------
# TC-10-07 — async reset without REGMODE
# ---------------------------------------------------------------------------

def test_tc_10_07_async_reset_without_reg():
    """TC-10-07: RESETMODE=async with REGMODE=False is rejected.

    Same bool-vs-string note as TC-10-06 applies to REGMODE here.
    """
    # DRC expression: check_resetmode(RESETMODE, REGMODE)
    result, err = _call(_plugin.check_resetmode, "async", False)
    assert result == 0
    assert (
        "Reset assertion is set to async, while Enable Output Register is turned off"
        in err
    )


# ---------------------------------------------------------------------------
# TC-10-08 — ECC with unsupported width
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason=(
        "TC-10-08: metadata.xml has no drc attribute for ECC on lscc_rom, "
        "and plugin.py has no corresponding check function.  Add both before "
        "enabling this test."
    )
)
def test_tc_10_08_ecc_unsupported_width():
    """TC-10-08: ECC_ENABLE=True with RDATA_WIDTH=65 should be rejected."""
    pass


# ---------------------------------------------------------------------------
# TC-10-09 — mem_file mode without an init file path
# ---------------------------------------------------------------------------

def test_tc_10_09_mem_file_without_path():
    """TC-10-09: user_init_file='-' (default sentinel) with INIT_MODE=mem_file is rejected."""
    # DRC expression: chk_file(user_init_file)
    result, err = _call(_plugin.chk_file, "-")
    assert result == 0
    assert "Initialization file is mandatory" in err


# ---------------------------------------------------------------------------
# Valid edge-case sanity checks (not in testplan — confirm plugin accepts these)
# ---------------------------------------------------------------------------

class TestBoundaryValid:
    """Verify that valid edge-case configurations are accepted without error."""

    def test_depth_at_plugin_minimum(self):
        # Plugin allows depth=1 even though metadata.xml value_range starts at 2.
        result, _ = _call(_plugin.check_addr_depth_data_width, 1, 1, 1, 1, _LIFCL)
        assert result == 1

    def test_depth_maximum_boundary(self):
        result, _ = _call(_plugin.check_addr_depth_data_width, 65536, 65536, 1, 1, _LIFCL)
        assert result == 1

    def test_width_maximum_within_bit_limit(self):
        # 512 bits × 2 depth = 1024 bits, well within the LIFCL limit.
        result, _ = _call(_plugin.check_addr_depth_data_width, 2, 2, 512, 512, _LIFCL)
        assert result == 1

    def test_total_bits_at_limit(self):
        # 36 × 43008 = 1,548,288 exactly — should be accepted.
        result, _ = _call(_plugin.check_addr_depth_data_width, 43008, 43008, 36, 36, _LIFCL)
        assert result == 1

    def test_output_clk_en_with_reg(self):
        result, _ = _call(_plugin.check_output_clk_en, True, True)
        assert result == 1

    def test_async_reset_with_reg(self):
        result, _ = _call(_plugin.check_resetmode, "async", True)
        assert result == 1

    def test_mem_file_with_valid_path(self):
        result, _ = _call(_plugin.chk_file, "testbench/rom_init.hex")
        assert result == 1

    def test_sync_reset_without_reg(self):
        # sync reset is allowed regardless of REGMODE.
        result, _ = _call(_plugin.check_resetmode, "sync", False)
        assert result == 1

    def test_clk_en_false_without_reg(self):
        # OUTPUT_CLK_EN=False is allowed regardless of REGMODE.
        result, _ = _call(_plugin.check_output_clk_en, False, False)
        assert result == 1
