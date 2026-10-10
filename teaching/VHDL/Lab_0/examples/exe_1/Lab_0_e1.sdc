create_clock -name FPGA_CLK_50 -period 20.000 [get_ports {FPGA_CLK_50}]
derive_clock_uncertainty
