`timescale 1ns/1ps
// Simulation wrapper for lscc_rom CoCoTB testbench.
// Provides GSR_INST at the top level (required by LIFCL EBR primitives)
// and exposes all DUT ports for cocotb to drive.
module testgen_top #(
    parameter FAMILY           = "common",
    parameter RDATA_WIDTH      = 36,
    parameter RADDR_DEPTH      = 512,
    parameter REGMODE          = "noreg",
    parameter RESETMODE        = "sync",
    parameter OUTPUT_CLK_EN    = 0,
    parameter ECC_ENABLE       = 0,
    parameter INIT_MODE        = "all_one",
    parameter INIT_FILE        = "none",
    parameter INIT_FILE_FORMAT = "hex"
) (
    input  wire                            rd_clk_i,
    input  wire                            rst_i,
    input  wire                            rd_clk_en_i,
    input  wire                            rd_out_clk_en_i,
    input  wire                            rd_en_i,
    input  wire [$clog2(RADDR_DEPTH)-1:0]  rd_addr_i,
    output wire [RDATA_WIDTH-1:0]          rd_data_o,
    output wire                            one_err_det_o,
    output wire                            two_err_det_o
);

    // GSR_N=1 keeps global set/reset de-asserted; CLK=0 is unused on LIFCL.
    // Without this instance, LIFCL EBR primitives fail with vopt-7063.
    GSR GSR_INST (.GSR_N(1'b1), .CLK(1'b0));

    lscc_rom #(
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
        .rd_out_clk_en_i(OUTPUT_CLK_EN ? rd_out_clk_en_i : 1'b1),
        .rd_en_i        (rd_en_i),
        .rd_addr_i      (rd_addr_i),
        .rd_data_o      (rd_data_o),
        .one_err_det_o  (one_err_det_o),
        .two_err_det_o  (two_err_det_o)
    );

endmodule
