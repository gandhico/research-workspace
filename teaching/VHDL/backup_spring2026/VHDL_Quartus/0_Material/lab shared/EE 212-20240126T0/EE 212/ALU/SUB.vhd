

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_SUB IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SUB IS
	SIGNAL Result	:	STD_LOGIC_VECTOR(31 DOWNTO 0);
	
BEGIN
	PROCESS(Func,Result,Ain,Bin) IS
	BEGIN
		IF(Func = ALU_FUNC_SUB) THEN
			Result <= STD_LOGIC_VECTOR(UNSIGNED(Ain) - UNSIGNED(Bin));	

			Rout	<= Result;
			Stat.ALU_zero  <= NOT(OR_REDUCE(Result));
			Stat.ALU_sign  <= Result(31);

		ELSE
			Result<=(others => 'Z');
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
