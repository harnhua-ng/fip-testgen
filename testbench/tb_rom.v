// =============================================================================
// tb_rom.v — Verilog testbench for lscc_rom (LIFCL)
// Test plan: docs/ROM_LIFCL_testplan.md
//
// Run a single test:
//   make tc-01-01               (via run_tc.py → vsim +TC=01_01 tb_rom)
//   make tg-01                  (all 7 TG-01 tests via run_tc.py)
//
// Run directly:
//   vsim -GREGMODE=noreg ... +TC=01_01 tb_rom
//
// +TC values: 01_01 01_02 01_03 01_04 01_05 01_06 01_07
// =============================================================================

`timescale 1ns/1ps

module tb_rom;

// ── Parameters (overridden per-TC via vsim -G<name>=<value>) ─────────────────
parameter string FAMILY          = "common";
parameter int    RDATA_WIDTH      = 36;
parameter int    RADDR_DEPTH      = 512;
parameter string REGMODE          = "noreg";
parameter string RESETMODE        = "sync";
parameter int    OUTPUT_CLK_EN    = 0;
parameter int    ECC_ENABLE       = 0;
parameter string INIT_MODE        = "all_one";
parameter string INIT_FILE        = "none";
parameter string INIT_FILE_FORMAT = "hex";

// ── Derived constants ─────────────────────────────────────────────────────────
localparam int RADDR_WIDTH = $clog2(RADDR_DEPTH);
// Pipeline latency: noreg = 1 clock (addr register only)
//                   reg   = 2 clocks (addr register + output register)
localparam int LAT      = (REGMODE == "reg") ? 2 : 1;
localparam int CLK_HALF = 5;    // 10 ns period → 100 MHz
localparam int RST_NS   = 100;  // 10 cycles at 100 MHz

// ── DUT signals ───────────────────────────────────────────────────────────────
logic                   rd_clk_i        = 1'b0;
logic                   rst_i           = 1'b0;
logic                   rd_clk_en_i     = 1'b0;
logic                   rd_out_clk_en_i = 1'b0;
logic                   rd_en_i         = 1'b0;
logic [RADDR_WIDTH-1:0] rd_addr_i       = '0;
wire  [RDATA_WIDTH-1:0] rd_data_o;
wire                    one_err_det_o;
wire                    two_err_det_o;

// ── Reference memory ──────────────────────────────────────────────────────────
logic [RDATA_WIDTH-1:0] REF [0:RADDR_DEPTH-1];

// ── Test bookkeeping ──────────────────────────────────────────────────────────
int    errors;
string tc_arg;    // value from +TC=XX_YY plusarg

// ── Clock ─────────────────────────────────────────────────────────────────────
always #CLK_HALF rd_clk_i = ~rd_clk_i;

// ── DUT instantiation (reuse existing GSR wrapper) ────────────────────────────
testgen_top #(
    .FAMILY           (FAMILY),
    .RDATA_WIDTH      (RDATA_WIDTH),
    .RADDR_DEPTH      (RADDR_DEPTH),
    .REGMODE          (REGMODE),
    .RESETMODE        (RESETMODE),
    .OUTPUT_CLK_EN    (OUTPUT_CLK_EN),
    .ECC_ENABLE       (ECC_ENABLE),
    .INIT_MODE        (INIT_MODE),
    .INIT_FILE        (INIT_FILE),
    .INIT_FILE_FORMAT (INIT_FILE_FORMAT)
) dut (
    .rd_clk_i       (rd_clk_i),
    .rst_i          (rst_i),
    .rd_clk_en_i    (rd_clk_en_i),
    .rd_out_clk_en_i(rd_out_clk_en_i),
    .rd_en_i        (rd_en_i),
    .rd_addr_i      (rd_addr_i),
    .rd_data_o      (rd_data_o),
    .one_err_det_o  (one_err_det_o),
    .two_err_det_o  (two_err_det_o)
);

// ── Reference model initialisation ───────────────────────────────────────────
initial begin
    if (INIT_MODE == "all_one") begin
        for (int i = 0; i < RADDR_DEPTH; i++) REF[i] = '1;
    end else if (INIT_MODE == "all_zero") begin
        for (int i = 0; i < RADDR_DEPTH; i++) REF[i] = '0;
    end else begin  // mem_file
        if (INIT_FILE_FORMAT == "hex")
            $readmemh(INIT_FILE, REF, 0, RADDR_DEPTH-1);
        else
            $readmemb(INIT_FILE, REF, 0, RADDR_DEPTH-1);
    end
end

// =============================================================================
// Shared tasks
// =============================================================================

// Apply reset for RST_NS then sync to first post-reset posedge.
task automatic do_reset();
    rst_i = 1'b1; rd_en_i = 1'b0; rd_clk_en_i = 1'b0;
    rd_out_clk_en_i = 1'b0; rd_addr_i = '0;
    #RST_NS;
    rst_i = 1'b0;
    @(posedge rd_clk_i);
endtask

// Assert all read-enable signals.
task automatic enable_reads();
    rd_en_i = 1'b1; rd_clk_en_i = 1'b1; rd_out_clk_en_i = 1'b1;
endtask

// Drive addr, wait LAT posedges, then sample rd_data_o 1 ps after the edge.
// Uses the module-level LAT localparam so the same task works for LAT=1 and LAT=2.
task automatic single_read(input int addr, output logic [RDATA_WIDTH-1:0] data);
    @(posedge rd_clk_i); rd_addr_i = addr;  // drive after posedge (delta cycle)
    repeat(LAT) @(posedge rd_clk_i);        // wait for pipeline to drain
    #1; data = rd_data_o;                   // sample 1 ps after last edge
endtask

// Pipeline read pattern: prime LAT stages, then steady-state drive+sample,
// then drain the last LAT addresses.
// → Verilog equivalent of CoCoTB latency_check()
// → $error format matches Python dut._log.error() in tb_rom.py field-for-field.
task automatic seq_read_check(input string tc_name, input int n_addrs);
    logic [RDATA_WIDTH-1:0] got;
    // Prime: fill LAT pipeline stages (no output sampled yet)
    for (int i = 0; i < LAT; i++) begin
        @(posedge rd_clk_i); rd_addr_i = i;
    end
    // Steady: at each rising edge drive addr[i] and sample addr[i-LAT]
    for (int i = LAT; i < n_addrs; i++) begin
        @(posedge rd_clk_i); rd_addr_i = i;
        #1; got = rd_data_o;
        if (got !== REF[i-LAT]) begin
            $display("[%s] cycle %0d: addr_in_pipeline=%0d got=0x%0X exp=0x%0X",
                     tc_name, i, i-LAT, got, REF[i-LAT]);
            errors++;
        end
    end
    // Drain: stop driving new addresses; flush last LAT through the pipeline
    for (int j = n_addrs-LAT; j < n_addrs; j++) begin
        @(posedge rd_clk_i); #1; got = rd_data_o;
        if (got !== REF[j]) begin
            $display("[%s] drain: addr_in_pipeline=%0d got=0x%0X exp=0x%0X",
                     tc_name, j, got, REF[j]);
            errors++;
        end
    end
endtask

// Print SIMULATION PASSED or SIMULATION FAILED (detected by run_tc.py log parser).
task automatic report(input string tc_name);
    if (errors == 0) begin
        $display("-----------------------------------------------------");
        $display("  %s: SIMULATION PASSED", tc_name);
        $display("-----------------------------------------------------");
    end else begin
        $display("-----------------------------------------------------");
        $display("  %s: SIMULATION FAILED (%0d error(s))", tc_name, errors);
        $display("-----------------------------------------------------");
    end
endtask

// =============================================================================
// TG-01  Basic Read Functionality
// =============================================================================

// TC-01-01: Sequential pipelined read, noreg (LAT=1), 36b×512, mem_file init.
// Expected parameters: REGMODE=noreg RDATA_WIDTH=36 RADDR_DEPTH=512 INIT_MODE=mem_file
task automatic tc_01_01;
    errors = 0;
    do_reset();
    enable_reads();
    seq_read_check("TC-01-01", 16);
endtask

// TC-01-02: Sequential pipelined read, reg (LAT=2), 36b×512, all_one init.
// Expected parameters: REGMODE=reg RDATA_WIDTH=36 RADDR_DEPTH=512
task automatic tc_01_02;
    errors = 0;
    do_reset();
    enable_reads();
    seq_read_check("TC-01-02", 16);
endtask

// TC-01-03: Full address sweep, noreg, 36b×512.
// Expected parameters: REGMODE=noreg RDATA_WIDTH=36 RADDR_DEPTH=512
task automatic tc_01_03;
    logic [RDATA_WIDTH-1:0] got;
    errors = 0;
    do_reset();
    enable_reads();
    for (int addr = 0; addr < RADDR_DEPTH; addr++) begin
        single_read(addr, got);
        if (got !== REF[addr]) begin
            $display("[TC-01-03] addr=%0d: got=0x%0X exp=0x%0X", addr, got, REF[addr]);
            errors++;
        end
    end
endtask

// TC-01-04: Full address sweep, reg (LAT=2), 36b×512.
// Expected parameters: REGMODE=reg RDATA_WIDTH=36 RADDR_DEPTH=512
task automatic tc_01_04;
    logic [RDATA_WIDTH-1:0] got;
    errors = 0;
    do_reset();
    enable_reads();
    for (int addr = 0; addr < RADDR_DEPTH; addr++) begin
        single_read(addr, got);
        if (got !== REF[addr]) begin
            $display("[TC-01-04] addr=%0d: got=0x%0X exp=0x%0X", addr, got, REF[addr]);
            errors++;
        end
    end
endtask

// TC-01-05: Boundary addresses (addr=0 and addr=RADDR_DEPTH-1), reg, 18b×1024.
// Expected parameters: REGMODE=reg RDATA_WIDTH=18 RADDR_DEPTH=1024
task automatic tc_01_05;
    logic [RDATA_WIDTH-1:0] got;
    errors = 0;
    do_reset();
    enable_reads();
    // First address
    single_read(0, got);
    if (got !== REF[0]) begin
        $display("[TC-01-05] boundary addr=0: got=0x%0X exp=0x%0X", got, REF[0]);
        errors++;
    end
    // Last address
    single_read(RADDR_DEPTH-1, got);
    if (got !== REF[RADDR_DEPTH-1]) begin
        $display("[TC-01-05] boundary addr=%0d: got=0x%0X exp=0x%0X",
                 RADDR_DEPTH-1, got, REF[RADDR_DEPTH-1]);
        errors++;
    end
endtask

// TC-01-06: 100 random addresses, reg, 36b×512.
// Fixed-seed 32-bit LCG (Knuth) → deterministic, repeatable.
// Expected parameters: REGMODE=reg RDATA_WIDTH=36 RADDR_DEPTH=512
task automatic tc_01_06;
    logic [RDATA_WIDTH-1:0] got;
    logic [31:0] rng;
    int          addr;
    errors = 0;
    rng = 32'h1ECC_CAFE;  // fixed seed
    do_reset();
    enable_reads();
    for (int i = 0; i < 100; i++) begin
        rng  = rng * 32'h6C07_8965 + 32'h1;  // LCG step (Knuth vol.2)
        addr = rng[30:0] % RADDR_DEPTH;        // bit 31 cleared; stays non-negative
        single_read(addr, got);
        if (got !== REF[addr]) begin
            $display("[TC-01-06] iter=%0d addr=%0d: got=0x%0X exp=0x%0X",
                     i, addr, got, REF[addr]);
            errors++;
        end
    end
endtask

// TC-01-07: Same address (RADDR_DEPTH/2) read 20 times consecutively, noreg, 9b×2048.
// Expected parameters: REGMODE=noreg RDATA_WIDTH=9 RADDR_DEPTH=2048
task automatic tc_01_07;
    logic [RDATA_WIDTH-1:0] got;
    int addr;
    errors = 0;
    addr = RADDR_DEPTH / 2;
    do_reset();
    enable_reads();
    for (int rep = 0; rep < 20; rep++) begin
        single_read(addr, got);
        if (got !== REF[addr]) begin
            $display("[TC-01-07] rep=%0d addr=%0d: got=0x%0X exp=0x%0X",
                     rep, addr, got, REF[addr]);
            errors++;
        end
    end
endtask

// =============================================================================
// Main test dispatcher
// =============================================================================

initial begin
    if (!$value$plusargs("TC=%s", tc_arg))
        tc_arg = "";

    case (tc_arg)
        "01_01": begin tc_01_01(); report("TC-01-01"); end
        "01_02": begin tc_01_02(); report("TC-01-02"); end
        "01_03": begin tc_01_03(); report("TC-01-03"); end
        "01_04": begin tc_01_04(); report("TC-01-04"); end
        "01_05": begin tc_01_05(); report("TC-01-05"); end
        "01_06": begin tc_01_06(); report("TC-01-06"); end
        "01_07": begin tc_01_07(); report("TC-01-07"); end
        "": begin
            $display("INFO: No +TC specified. Use +TC=01_01 ... +TC=01_07 to run a TG-01 test.");
            $display("INFO: e.g.  vsim -GREGMODE=noreg ... +TC=01_01 tb_rom");
        end
        default: begin
            $display("ERROR: unknown +TC=%s (valid: 01_01 ... 01_07)", tc_arg);
            $finish(1);
        end
    endcase

    $finish;
end

endmodule
