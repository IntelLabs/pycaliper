// Parent module with a miter with different inputs
module einter (
    input wire clk
);


    adder #(
        .WIDTH(8)
    ) adder_0 (
        .clk_i(clk)
    );

    default clocking cb @(posedge clk);
    endclocking // cb

    logic fvreset;

    `include "adder.pyc.sv"

endmodule
