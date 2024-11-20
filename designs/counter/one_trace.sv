// Parent module with a miter with different inputs
module einter (
    input wire clk
);

    counter a (
        .clk(clk)
    );

    default clocking cb @(posedge clk);
    endclocking // cb

    logic fvreset;

    `include "counter.pyc.sv"

endmodule
