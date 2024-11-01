

module adder #(
    parameter int unsigned WIDTH = 8
) (
    input logic clk_i,
    input logic rst_ni,
    input logic [WIDTH-1:0] a_i,
    input logic [WIDTH-1:0] b_i,
    output logic [WIDTH-1:0] sum_o
);

    logic [WIDTH:0] sum;

    always_ff @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            sum <= '0;
        end else begin
            sum <= a_i + b_i;
        end
    end

    assign sum_o = sum[WIDTH-1:0];

endmodule