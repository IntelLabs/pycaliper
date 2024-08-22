    logic step;
    always @(posedge clk ) begin
        if (fvreset) begin
            step <= 0;
        end else begin
            step <= 1;
        end
    end



//////////////////////////////////////////////////////////////////////
// regblock module

wire _input =
    a.rst == b.rst &&
    a.rd_index == b.rd_index &&
    a.wr_index == b.wr_index &&
    a.en == b.en &&
    a.d == b.d &&
    1'b1;

wire eq_q = (a.q == b.q);
wire eq_reg1_q = (a.reg1.q == b.reg1.q);
wire eq_reg2_q = (a.reg2.q == b.reg2.q);

wire _output =
    eq_q && eq_reg1_q && eq_reg2_q;

A_input : assume property
    (_input);

A_eq_q : assume property
    (!step |-> eq_q);

A_eq_reg1_q : assume property
    (!step |-> eq_reg1_q);

A_eq_reg2_q : assume property
    (!step |-> eq_reg2_q);

P_eq_q : assert property
    (step |-> eq_q);

P_eq_reg1_q : assert property
    (step |-> eq_reg1_q);

P_eq_reg2_q : assert property
    (step |-> eq_reg2_q);

P_output : assert property
    (step |-> _output);
