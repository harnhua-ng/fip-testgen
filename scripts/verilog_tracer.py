"""
verilog_tracer.py — Shared VerilogTracer class for all FIP testbenches.

Used by tb_rom.py, tb_fifo_dc.py, tb_pll.py (and future IP testbenches) to
generate a standalone Verilog task file that captures the stimulus and
expected-output checks executed during each testcase. RTL engineers can
use these trace files as golden references for waveform debugging.

Usage in a CoCoTB testcase:

    tracer = VerilogTracer("TC-ROM-001", enabled=True)
    # ... drive and check the DUT ...
    tracer.save()   # writes results/tc-rom-001_trace.v
"""

import os
import re
import cocotb
from cocotb.utils import get_sim_time


class VerilogTracer:
    """Logs Verilog-equivalent statements to the transcript and generates standalone _trace.v files."""

    def __init__(self, tc_name: str, out_dir: str = "results", enabled: bool = True):
        clean_name = re.sub(r'(_trace)?\.v$', '', tc_name, flags=re.IGNORECASE)
        self.tc_name = clean_name.upper().replace("_", "-")
        self.out_dir = out_dir
        self.enabled = enabled
        self.trace_lines = [
            "// ============================================================================",
            f"// Verilog Stimulus & Check Trace: {self.tc_name}",
            "// Auto-generated at runtime by VerilogTracer (scripts/verilog_tracer.py)",
            "// ============================================================================",
            f"task automatic run_{self.tc_name.lower().replace('-', '_')}_trace;",
        ]

    def log_stmt(self, stmt: str):
        """Print Verilog statement to transcript and record into trace buffer."""
        if not self.enabled:
            return
        try:
            t_ns = get_sim_time(unit="ns")
            cocotb.log.info(f"[VERILOG @ {t_ns:7.2f} ns] {stmt}")
        except Exception:
            cocotb.log.info(f"[VERILOG] {stmt}")
        self.trace_lines.append(f"    {stmt}")

    def comment(self, text: str):
        if self.enabled:
            self.trace_lines.append(f"\n    // {text}")
            cocotb.log.info(f"// --- {text} ---")

    def assign(self, signal: str, value: int, width: int = 0):
        if width > 0:
            stmt = f"{signal} = {width}'h{value:X};"
        else:
            stmt = f"{signal} = 1'b{value};"
        self.log_stmt(stmt)

    def clock_edge(self, clk_name: str = "clk_i"):
        self.log_stmt(f"@(posedge {clk_name});")

    def neg_clock_edge(self, clk_name: str = "clk_i"):
        self.log_stmt(f"@(negedge {clk_name});")

    def delay_ns(self, ns: int):
        self.log_stmt(f"#{ns};")

    def delay_ps(self, ps: int):
        self.log_stmt(f"#{ps}ps;")

    def wait_condition(self, condition: str):
        self.log_stmt(f"wait({condition});")

    def check(self, cycle: int, addr_pipe: int, got_sig: str, exp_val: int, hex_w: int):
        stmt = (
            f"if ({got_sig} !== {hex_w * 4}'h{exp_val:0{hex_w}X}) begin\n"
            f'        $display("[{self.tc_name}] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x{exp_val:0{hex_w}X}", {cycle}, {addr_pipe}, {got_sig});\n'
            f"        errors++;\n"
            f"    end"
        )
        self.log_stmt(stmt)

    def check_equal(self, got_sig: str, exp_val: int, width: int = 0):
        if width > 0:
            exp_str = f"{width}'h{exp_val:X}"
        else:
            exp_str = f"1'b{exp_val}"
        stmt = (
            f"if ({got_sig} !== {exp_str}) begin\n"
            f'        $display("[{self.tc_name}] ERROR: {got_sig} got=0x%0X exp={exp_str}", {got_sig});\n'
            f"        errors++;\n"
            f"    end"
        )
        self.log_stmt(stmt)

    def save(self):
        if not self.enabled:
            return
        os.makedirs(self.out_dir, exist_ok=True)
        path = os.path.join(self.out_dir, f"{self.tc_name.lower()}_trace.v")
        self.trace_lines.append("endtask\n")
        with open(path, "w") as f:
            f.write("\n".join(self.trace_lines))
        cocotb.log.info(f"[{self.tc_name}] Verilog trace written to: {path}")
