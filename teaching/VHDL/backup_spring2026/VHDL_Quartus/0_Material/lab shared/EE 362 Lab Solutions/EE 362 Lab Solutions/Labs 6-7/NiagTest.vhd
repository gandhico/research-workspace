-------------------------------------------------------------------------------------
--Description:	NiagTest
--
--       File:	NiagTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for the Next Instruction Address Generation logic
--
--     Inputs:	  Target: Target field of IR
--                Immed: Sign-extended Immediate value 
--                  Reg: ALU register  
--                Xshft: sign-extend select
--                 PCin: current Program Counter value
--                 Cond: logical condition being tested
--                  Sel: PC next address source
--                 Stat: ALU status codes
--
--    Outputs:  MemAdrs: address to instruction memory
--              RtnAdrs: return address for function calls
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

LIBRARY EE_362_NIAG;
USE EE_362_NIAG.NIAG_Pkg.all;

ENTITY NiagTest IS
	PORT(	Target	:	IN		STD_LOGIC_VECTOR(25 DOWNTO 0);
			Immed	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Reg		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Xshft	:	IN		STD_LOGIC;
			PCin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Cond	:	IN		STD_LOGIC_VECTOR(2 DOWNTO 0);
			Sel		:	IN		STD_LOGIC_VECTOR(1 DOWNTO 0);
			Stat	:	IN		STAT_SIGNL_REC;
			MemAdrs	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			RtnAdrs	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NiagTest IS
	TestComponent : NAIG  PORT MAP(Target, Immed, Reg, Xshift, PCin, Cond, Sel, Stat, MemAdrs, RtnAdrs);
BEGIN
END ARCHITECTURE;