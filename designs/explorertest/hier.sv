module BottomModule(
    input logic clk,
    input logic rst_n,
    output logic bottom_signal
);
    // Simple logic for demonstration purposes
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            bottom_signal <= 0;
        else
            bottom_signal <= ~bottom_signal;
    end
endmodule


module MiddleModule(
    input logic clk,
    input logic rst_n,
    output logic middle_signal
);
    // To connect MiddleModule to BottomModule
    logic bottom_signal;

    // Instantiate BottomModule
    BottomModule bottom_inst (
        .clk(clk),
        .rst_n(rst_n),
        .bottom_signal(bottom_signal)
    );

    // Simple logic for demonstration purposes
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            middle_signal <= 0;
        else
            middle_signal <= bottom_signal;
    end
endmodule


module TopModule(
    input logic clk,
    input logic rst_n,
    output logic top_signal
);
    // To connect TopModule to MiddleModule
    logic middle_signal;

    // Instantiate MiddleModule
    MiddleModule middle_inst (
        .clk(clk),
        .rst_n(rst_n),
        .middle_signal(middle_signal)
    );

    // Simple logic for demonstration purposes
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            top_signal <= 0;
        else
            top_signal <= middle_signal;
    end
endmodule