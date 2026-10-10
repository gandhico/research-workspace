--------------------------------------------------------------------------------------
--  Component:	ALU_NEG
--
--       File:	NegSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU negate operation
--
--     Inputs:   Bin:  32-bit operand
--               Func: ALU function code
--
--    Outputs:  Rout: 32-bit result
--              Stat: ALU status codes
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY ALU_NEG IS
	PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_NEG IS
	SIGNAL SignedRout	:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin	:	SIGNED(31 DOWNTO 0);
	
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_NEG) THEN								-- negate function?
			SignedBin	<= SIGNED(Bin);
			Stat <= (others => 'Z');

			SignedRout 	<= -SignedBin;								-- calculate negative
				
			Stat.ALU_sign  	<= SignedRout(31);
			Stat.ALU_zero  	<= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Rout 			<= STD_LOGIC_VECTOR(SignedRout);
		ELSE
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
