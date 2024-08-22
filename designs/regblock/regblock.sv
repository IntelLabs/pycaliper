



module reg_en (
    input wire clk,
    input wire rst,
    input wire en,
    input wire [31:0] d,
    output wire [31:0] q
);

    logic [31:0] q;

    always @(posedge clk) begin
        if (rst) begin
            q <= 32'h0;
        end else if (en) begin
            q <= d;
        end
    end

endmodule


module regblock (
    input wire clk,
    input wire rst,
    input wire rd_index,
    input wire wr_index,
    input wire en,
    input wire [31:0] d,
    output wire [31:0] q
);

    wire logic en1;
    wire logic en2;
    wire logic [31:0] q1;
    wire logic [31:0] q2;

    logic rd_index1;
    assign q = (rd_index1) ? q1 : q2;

    always @(posedge clk ) begin
        rd_index1 <= rd_index;
    end

    assign en1 = (wr_index) ? en : 1'b0;
    assign en2 = (wr_index) ? 1'b0 : en;

    reg_en reg1 (
        .clk(clk)
        , .rst(rst)
        , .en(en1)
        , .d(d)
        , .q(q1)
    );

    reg_en reg2 (
        .clk(clk)
        , .rst(rst)
        , .en(en1)
        , .d(d)
        , .q(q2)
    );


endmodule
