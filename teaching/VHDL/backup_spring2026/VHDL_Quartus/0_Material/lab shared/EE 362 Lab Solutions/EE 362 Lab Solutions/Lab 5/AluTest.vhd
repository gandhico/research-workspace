-------------------------------------------------------------------------------------
--Description:	AluTest
--
--       File:	AluTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for ALU component
--
--     Inputs:    Ain: 32-bit operand
--                Bin: 32-bit operand
--               Func: ALU function code
--				 Shft: # places to shift (if a shifgt operation)
--
--    Outputs:    Rslt:	32-bit result
--                Stat: ALU status codes
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY AluTest IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Shft	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			Rout	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF AluTes IS
SIGNAL	Status	:	STD_LOGIC_VECTOR(4  DOWNTO 0);	     -- ALU status register

BEGIN
	TestComponent : ALU  PORT MAP(Ain, Bin, Func, Shft, Rout,  Stat);
END ARCHITECTURE;
