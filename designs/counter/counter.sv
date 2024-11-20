

module counter (
    input clk,
    input rst,
    output [7:0] counter
);

    // Counter that increments by 1
    logic [7:0] counter_internal;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            counter_internal <= 8'h00;
        end else begin
            counter_internal <= counter_internal + 1;
        end
    end

    assign counter = counter_internal;

endmodule


module parity (
    input clk,
    input rst,
    input [7:0] counter
);

    // OddEven parity
    logic parity;

    // toggle parity bit
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            parity <= 1'b0;
        end else begin
            parity <= ~parity;
        end
    end

endmodule
