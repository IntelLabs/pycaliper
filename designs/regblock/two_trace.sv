// Parent module with a miter with different inputs
module miter (
    input wire clk
    , input wire rst
    , output wire [31:0] qA
    , output wire [31:0] qB
);


    regblock a (
        .clk(clk)
        , .rst(rst)
        , .q(qA)
    );

    regblock b (
        .clk(clk)
        , .rst(rst)
        , .q(qB)
    );

    default clocking cb @(posedge clk);
    endclocking // cb

    logic fvreset;

    `include "regblock.pyc.sv"

endmodule
