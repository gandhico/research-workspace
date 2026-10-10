

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_OR IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_OR IS
	SIGNAL	Answer	:	STD_LOGIC_VECTOR(31 DOWNTO 0);
	
BEGIN
	
		
			Answer	<= Ain OR Bin when Func = ALU_FUNC_OR ELSE (others=>'Z');
			Rout 		<= Answer when Func = ALU_FUNC_OR ELSE (others => 'Z');
			
			Stat.ALU_zero  <= NOT(OR_REDUCE(Answer)) when Func = ALU_FUNC_OR ELSE 'Z';
			Stat.ALU_sign  <= Answer(31) when Func = ALU_FUNC_OR ELSE 'Z';
		
			
END ARCHITECTURE;
