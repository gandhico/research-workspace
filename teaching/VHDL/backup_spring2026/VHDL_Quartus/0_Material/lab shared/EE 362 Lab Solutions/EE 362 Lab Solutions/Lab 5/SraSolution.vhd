--------------------------------------------------------------------------------------
--  Component:	ALU_SRA
--
--       File:	SraSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU shift right arithmetic operation
--
--     Inputs:    Ain: 32-bit operand
--               Func: ALU function code
--					  Shft: number of places to shift
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

ENTITY ALU_SRA IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SRA IS
	SIGNAL SignedRout		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL NaturalShift  	:	NATURAL;

	BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_SRA) THEN
			Stat			<= (others => 'Z');
			SignedAin		<= SIGNED(Ain);
			NaturalShift	<= to_integer(unsigned(Shft));
			
			SignedRout 		<= shift_right(SignedAin, NaturalShift);
			
			Stat.ALU_zero  	<= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  	<= SignedRout(31);
			
			Rout		 	<= STD_LOGIC_VECTOR(SignedRout);
		ELSE
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
