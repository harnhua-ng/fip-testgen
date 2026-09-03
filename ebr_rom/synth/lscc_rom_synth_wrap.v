`timescale 1ns/1ps
// Synthesis-only wrapper for lscc_rom.
//
// The IP RTL defaults to INIT_MODE="none", which produces an all-zero
// initialization image.  Synplify's constant-propagation folds the EBR
// output to constant 0 and Map removes the block entirely.
// Setting INIT_MODE="all_one" here gives the EBR a non-constant image so
// the block is preserved through synthesis and mapping.
//
// This file is NOT used by the CoCoTB simulation flow; the Makefile
// simulation targets drive lscc_rom directly with explicit parameter
// overrides via SIM_ARGS.
module lscc_rom_synth_wrap #(
    parameter FAMILY        = "LIFCL",
    parameter RDATA_WIDTH   = 18,
    parameter RADDR_DEPTH   = 1024,
    parameter REGMODE       = "reg",
    parameter RESETMODE     = "sync",
    parameter OUTPUT_CLK_EN = 0,
    parameter ECC_ENABLE    = 0
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

    lscc_rom #(
        .FAMILY        (FAMILY),
        .RDATA_WIDTH   (RDATA_WIDTH),
        .RADDR_DEPTH   (RADDR_DEPTH),
        .REGMODE       (REGMODE),
        .RESETMODE     (RESETMODE),
        .OUTPUT_CLK_EN (OUTPUT_CLK_EN),
        .ECC_ENABLE    (ECC_ENABLE),
        .INIT_MODE     ("all_one")
    ) u_rom (
        .rd_clk_i        (rd_clk_i),
        .rst_i           (rst_i),
        .rd_clk_en_i     (rd_clk_en_i),
        .rd_out_clk_en_i (rd_out_clk_en_i),
        .rd_en_i         (rd_en_i),
        .rd_addr_i       (rd_addr_i),
        .rd_data_o       (rd_data_o),
        .one_err_det_o   (one_err_det_o),
        .two_err_det_o   (two_err_det_o)
    );

endmodule
