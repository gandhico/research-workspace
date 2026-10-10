--------------------------------------------------------------------------------------
--  Component:	NIAG
--
--       File:	NiagSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the next instruction address generation logic
--
--     Inputs:	 Target: Target field of IR
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

ENTITY NIAG IS
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

ARCHITECTURE Behavioral OF NIAG IS
	SIGNAL	NSA			:	STD_LOGIC_VECTOR(31  DOWNTO 0);							-- Next Sequential Address
	SIGNAL	AbsltAdrs	:	STD_LOGIC_VECTOR(31  DOWNTO 0);							-- Absolute Address
	SIGNAL	RelAdrs		:	STD_LOGIC_VECTOR(31  DOWNTO 0);							-- Relative Address
	SIGNAL	RegAdrs		:	STD_LOGIC_VECTOR(31  DOWNTO 0);							-- Register Address
	SIGNAL	RetAdrs		:	STD_LOGIC_VECTOR(31  DOWNTO 0);							-- function return Address

	BEGIN
		F00 : NIAG_NSA		PORT MAP(PCin, NSA);
		F01 : NIAG_Abslt	PORT MAP(Target, NSA, AbsltAdrs);
		F02 : NIAG_Rel		PORT MAP(Immed, Xshft, NSA, RelAdrs);
		F03 : NIAG_Reg		PORT MAP(Reg, RegAdrs);
		F04 : NIAG_Rtn		PORT MAP(PCin, RetAdrs);
		F05 : NIAG_MUX		PORT MAP(NSA, AbsltAdrs, RelAdrs, RegAdrs, Cond, Sel, Stat, MemAdrs);

END ARCHITECTURE;
