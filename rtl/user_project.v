`timescale 1ns / 1ps
`default_nettype none

module user_project (
`ifdef USE_POWER_PINS
    inout vccd1,
    inout vssd1,
`endif
    input wire wb_clk_i,
    input wire wb_rst_i,
    input wire wbs_stb_i,
    input wire wbs_cyc_i,
    input wire wbs_we_i,
    input wire [3:0] wbs_sel_i,
    input wire [31:0] wbs_dat_i,
    input wire [31:0] wbs_adr_i,
    output wire wbs_ack_o,
    output wire [31:0] wbs_dat_o,
    output wire [2:0] user_irq,
    input wire uart0_rx,
    output wire uart0_tx,
    input wire uart1_rx,
    output wire uart1_tx
);

  wire uart0_sel;
  wire uart1_sel;
  wire valid_sel;

  wire uart0_stb;
  wire uart1_stb;

  wire uart0_ack;
  wire uart1_ack;

  wire [31:0] uart0_dat_o;
  wire [31:0] uart1_dat_o;

  wire uart0_irq;
  wire uart1_irq;

  reg invalid_ack;
  reg [31:0] mux_dat_o;

  assign uart0_sel = (wbs_adr_i[19:16] == 4'b0000);
  assign uart1_sel = (wbs_adr_i[19:16] == 4'b0001);
  assign valid_sel = uart0_sel | uart1_sel;

  assign uart0_stb = wbs_stb_i & uart0_sel;
  assign uart1_stb = wbs_stb_i & uart1_sel;

  always @(posedge wb_clk_i) begin
    if (wb_rst_i) begin
      invalid_ack <= 1'b0;
    end else begin
      if (wbs_stb_i & wbs_cyc_i & ~valid_sel & ~invalid_ack) begin
        invalid_ack <= 1'b1;
      end else begin
        invalid_ack <= 1'b0;
      end
    end
  end

  always @(*) begin
    case (wbs_adr_i[19:16])
      4'b0000: mux_dat_o = uart0_dat_o;
      4'b0001: mux_dat_o = uart1_dat_o;
      default: mux_dat_o = 32'hDEADBEEF;
    endcase
  end

  assign wbs_ack_o = uart0_ack | uart1_ack | invalid_ack;
  assign wbs_dat_o = mux_dat_o;

  assign user_irq[0] = uart0_irq;
  assign user_irq[1] = uart1_irq;
  assign user_irq[2] = 1'b0;

  CF_UART_WB #(
      .SC(8),
      .MDW(9),
      .GFLEN(8),
      .FAW(4)
  ) uart0_inst (
      .clk_i(wb_clk_i),
      .rst_i(wb_rst_i),
      .adr_i(wbs_adr_i),
      .dat_i(wbs_dat_i),
      .dat_o(uart0_dat_o),
      .sel_i(wbs_sel_i),
      .cyc_i(wbs_cyc_i),
      .stb_i(uart0_stb),
      .ack_o(uart0_ack),
      .we_i (wbs_we_i),
      .IRQ  (uart0_irq),
      .rx   (uart0_rx),
      .tx   (uart0_tx)
  );

  CF_UART_WB #(
      .SC(8),
      .MDW(9),
      .GFLEN(8),
      .FAW(4)
  ) uart1_inst (
      .clk_i(wb_clk_i),
      .rst_i(wb_rst_i),
      .adr_i(wbs_adr_i),
      .dat_i(wbs_dat_i),
      .dat_o(uart1_dat_o),
      .sel_i(wbs_sel_i),
      .cyc_i(wbs_cyc_i),
      .stb_i(uart1_stb),
      .ack_o(uart1_ack),
      .we_i (wbs_we_i),
      .IRQ  (uart1_irq),
      .rx   (uart1_rx),
      .tx   (uart1_tx)
  );

endmodule

`default_nettype wire
