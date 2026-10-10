library ieee;

use ieee.std_logic_1164.all;

entity majority3_tb is
end entity;

architecture test of majority3_tb is

	signal A : std_logic := '0';
	signal B : std_logic := '0';
	signal C : std_logic := '0';
	signal Y : std_logic;
	
begin

	dut: entity work.majority3
		port map ( a => A, b => B, c => C, Y => Y);
	
	stimulus : process
	begin
	
	-- Test 1
	A <= '0'; B <= '0' ; C <= '0'; wait for 10 ns;
	
	-- Test 2
	A <= '0'; B <= '0' ; C <= '1'; wait for 10 ns;
	
	-- Test 3
	A <= '0'; B <= '1' ; C <= '0'; wait for 10 ns; 
	
	-- Test 4
	A <= '0'; B <= '1' ; C <= '1'; wait for 10 ns;
	
	-- Test 5
	A <= '1'; B <= '0' ; C <= '0'; wait for 10 ns;
	
	-- Test 6
	A <= '1'; B <= '0' ; C <= '1'; wait for 10 ns;
	
	-- Test 7
	A <= '1'; B <= '1' ; C <= '0'; wait for 10 ns;
	
	-- Test 8
	A <= '1'; B <= '1' ; C <= '1'; wait for 10 ns;
		
	wait;
	end process;
end architecture;
	