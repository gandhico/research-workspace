
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_RDLO IS
	PORT(	LoReg	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_RDLO IS
BEGIN

			Rout	<= LoReg when Func = ALU_FUNC_RDLO else(others => 'Z') ;											
			
			Stat.ALU_sign  <= LoReg(31) when Func = ALU_FUNC_RDLO else 'Z';
			Stat.ALU_zero  <= NOT(OR_REDUCE(LoReg))when Func = ALU_FUNC_RDLO else 'Z';

END ARCHITECTURE;
