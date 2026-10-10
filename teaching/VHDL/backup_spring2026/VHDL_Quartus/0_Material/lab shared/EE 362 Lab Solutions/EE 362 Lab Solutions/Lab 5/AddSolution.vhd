--------------------------------------------------------------------------------------
--  Component:	ALU_ADD
--
--       File:	AddSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU addition operation
--
--     Inputs:   Ain:  32-bit operand
--               Bin:  32-bit operand
--              Func:  ALU function code
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

ENTITY ALU_ADD IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_ADD IS
	SIGNAL Result	:	STD_LOGIC_VECTOR(31 DOWNTO 0);
	
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_ADD) THEN										-- addition function?
			Result <= STD_LOGIC_VECTOR(UNSIGNED(Ain) + UNSIGNED(Ain));		--   Yes: find sum as unsigned int
			Rout 		   <= Result;
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(Result)));		--       calculate zero status
			Stat.ALU_sign  <= STD_LOGIC_VECTOR(Result)(31);					--		 calculate sign status
		ELSE
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;



