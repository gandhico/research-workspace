
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_RDHI IS
	PORT(	HiReg	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_RDHI IS
BEGIN
	Rout	<= HiReg when Func = ALU_FUNC_RDHI else(others => 'Z') ;											
			
			Stat.ALU_sign  <= HiReg(31) when Func = ALU_FUNC_RDHI else 'Z';
			Stat.ALU_zero  <= NOT(OR_REDUCE(HiReg))when Func = ALU_FUNC_RDHI else 'Z';
END ARCHITECTURE;
