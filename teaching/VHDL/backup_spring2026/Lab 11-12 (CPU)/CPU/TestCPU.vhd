library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity TestCPU is
end TestCPU;

architecture sim of TestCPU is
    signal SysClk : STD_LOGIC := '0';
    constant Tclk : time := 20 ns;
begin
    DUT : entity work.CPU
        port map(SysClk => SysClk);

    -- TODO: extend or modify this testbench as needed.
    -- A simple starting point is to run the CPU long enough to execute the
    -- whole ROM program, then inspect internal signals in the waveform viewer.
	 
    clk_process : process
    begin
        while now < 2200 ns loop
            SysClk <= '0';
            wait for Tclk/2;
            SysClk <= '1';
            wait for Tclk/2;
        end loop;
        wait;
    end process;
	 
end sim;
