
module einter (
    input wire clk
    , input wire rst
);

    TopModule a (
        .clk(clk)
        , .rst_n(rst)
    );

    default clocking cb @(posedge clk);
    endclocking // cb

    logic fvreset;

    `include "hier.pyc.sv"

endmodule
