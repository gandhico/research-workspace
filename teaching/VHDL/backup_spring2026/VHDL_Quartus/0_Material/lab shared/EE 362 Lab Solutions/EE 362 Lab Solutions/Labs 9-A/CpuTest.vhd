Library IEEE;
USE IEEE.STD_LOGIC_1164.all;
Use IEEE.NUMERIC_STD.all;

library EE_212_CPU;
use EE_212_CPU.LabCPU_pkg.all;


entity tb_CPU is

end entity;


architecture behavioral of tb_CPU is
signal clk: std_logic;
begin

	L0: CPU port map(clk);

	clock_procss: process

	begin
		clk<='0';
		wait for 10 ns;
		clk<='1';
		wait for 10 ns;		
	end process;


end architecture;