library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_NEG IS
	PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_NEG IS
	SIGNAL SignedRout		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin		:	SIGNED(31 DOWNTO 0);
	
BEGIN
	PROCESS(Func,Bin,SignedRout,SignedBin) IS
	BEGIN
		IF(Func = ALU_FUNC_NEG) THEN							
			SignedBin	<= SIGNED(Bin);
			Stat <= (others => 'Z');

			SignedRout 	<= -SignedBin;							
				
			Stat.ALU_sign  	<= SignedRout(31);
			Stat.ALU_zero  	<= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Rout 					<= STD_LOGIC_VECTOR(SignedRout);
		ELSE
			SignedRout <= (others => 'Z');
			SignedBin <= (others => 'Z');
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
