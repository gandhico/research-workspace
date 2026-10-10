library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_ADD IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_ADD IS
	SIGNAL Result	:	STD_LOGIC_VECTOR(31 DOWNTO 0);
	

	BEGIN
											
			Result <= STD_LOGIC_VECTOR(UNSIGNED(Ain) + UNSIGNED(Bin)) when Func = ALU_FUNC_ADD
			else (others => 'Z') ;		

			Rout <= Result when Func = ALU_FUNC_ADD else (others => 'Z');
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(Result))) when Func = ALU_FUNC_ADD else  'Z';		
			Stat.ALU_sign  <= STD_LOGIC(Result(31)) when Func = ALU_FUNC_ADD else'Z';					

--			Rout <= (others => 'Z') when Func/=ALU_FUNC_ADD ;
--			Stat <= (others => 'Z')when Func/=ALU_FUNC_ADD ;

END ARCHITECTURE;



