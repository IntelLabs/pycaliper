
    logic counter;
    always @(posedge clk) begin
        if (fvreset) begin
            counter <= 0;
        end else begin
            if (counter < 1'd1) begin
                counter <= (counter + 1'b1);
            end
        end
    end
    logic step = (counter == 1'd1);

logic eq_reg1_rst ;
logic eq_reg1_en ;
logic condeq_reg1_d ;
logic eq_reg1_q ;
logic eq_reg2_rst ;
logic eq_reg2_en ;
logic condeq_reg2_d ;
logic eq_reg2_q ;
logic eq_rst ;
logic eq_en ;
logic condeq_d ;
logic condeq_wr_index ;
logic eq_rd_index ;
logic eq_q ;
assign eq_reg1_rst = (a.reg1.rst == b.reg1.rst);
assign eq_reg1_en = (a.reg1.en == b.reg1.en);
assign condeq_reg1_d = (!(a.reg1.en && b.reg1.en) | (a.reg1.d == b.reg1.d));
assign eq_reg1_q = (a.reg1.q == b.reg1.q);
assign eq_reg2_rst = (a.reg2.rst == b.reg2.rst);
assign eq_reg2_en = (a.reg2.en == b.reg2.en);
assign condeq_reg2_d = (!(a.reg2.en && b.reg2.en) | (a.reg2.d == b.reg2.d));
assign eq_reg2_q = (a.reg2.q == b.reg2.q);
assign eq_rst = (a.rst == b.rst);
assign eq_en = (a.en == b.en);
assign condeq_d = (!(a.en && b.en) | (a.d == b.d));
assign condeq_wr_index = (!(a.en && b.en) | (a.wr_index == b.wr_index));
assign eq_rd_index = (a.rd_index == b.rd_index);
assign eq_q = (a.q == b.q);

/////////////////////////////////////
// Module reg1

wire reg1_input = (
	eq_reg1_rst &&
	eq_reg1_en &&
	condeq_reg1_d &&
	1'b1);
wire reg1_state = (
	eq_reg1_q &&
	1'b1);
wire reg1_output = (
	eq_reg1_q &&
	1'b1);
wire reg1_input_inv = (
	1'b1);
wire reg1_state_inv = (
	1'b1);
wire reg1_output_inv = (
	1'b1);
wire reg1_input_inv = (
	1'b1);
wire reg1_state_inv = (
	1'b1);
wire reg1_output_inv = (
	1'b1);

/////////////////////////////////////
// Module reg2

wire reg2_input = (
	eq_reg2_rst &&
	eq_reg2_en &&
	condeq_reg2_d &&
	1'b1);
wire reg2_state = (
	eq_reg2_q &&
	1'b1);
wire reg2_output = (
	eq_reg2_q &&
	1'b1);
wire reg2_input_inv = (
	1'b1);
wire reg2_state_inv = (
	1'b1);
wire reg2_output_inv = (
	1'b1);
wire reg2_input_inv = (
	1'b1);
wire reg2_state_inv = (
	1'b1);
wire reg2_output_inv = (
	1'b1);

/////////////////////////////////////
// Module

wire _input = (
	eq_rst &&
	eq_en &&
	condeq_d &&
	condeq_wr_index &&
	eq_rd_index &&
	1'b1);
wire _state = (
	eq_reg1_q &&
	eq_reg2_q &&
	1'b1);
wire _output = (
	eq_q &&
	1'b1);
wire _input_inv = (
	1'b1);
wire _state_inv = (
	1'b1);
wire _output_inv = (
	1'b1);
wire _input_inv = (
	1'b1);
wire _state_inv = (
	1'b1);
wire _output_inv = (
	1'b1);

/////////////////////////////////////
// Assumptions and Assertions for top module
A_input_inv : assume property
	(_input_inv);

A_state_inv : assume property
	(!(step) |-> (_state_inv));

P_output_inv : assert property
	(step |-> (_state_inv && _output_inv));

A_input : assume property
	(_input && _input_inv);

A_state : assume property
	(!(step) |-> (_state && _state_inv));

P_output : assert property
	(step |-> (_state && _state_inv && _output && _output_inv));
