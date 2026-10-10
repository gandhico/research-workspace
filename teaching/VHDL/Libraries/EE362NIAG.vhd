-------------------------------------------------------------------------------------
--    Library:	EE_212_PC
--
--       File:	EE212NIAG.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the Next Instruction Address Generator
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_ALU;
use EE_362_ALU.ALU_Pkg.all;

PACKAGE NIAG_Pkg IS

	COMPONENT NIAG IS															--  Next Instruction Address Generator
		PORT(	Target		:	IN	STD_LOGIC_VECTOR(25 DOWNTO 0);				--    Absolute address
				Immed		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    IR immediate field extended
				Reg			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Register file B output 
				Xshft		:	IN	STD_LOGIC;									--    IR immediate field extender selection
				PCin		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Program counter input
				Cond		:	IN	STD_LOGIC_VECTOR(2 DOWNTO 0);				--    ALU status codes
				Sel			:	IN	STD_LOGIC_VECTOR(1 DOWNTO 0);				--    PC mux input selection bus
				Stat		:	IN	STAT_SIGNL_REC;								--    ALU status signals
				MemAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Memory address bus
				RtnAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Function return address
	END COMPONENT NIAG;

	COMPONENT NIAG_NSA IS														--  Next sequential instruction address generation
		PORT(	PC			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Program counter output
				NSA			:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Next sequential address output    
	END COMPONENT NIAG_NSA;
	
	COMPONENT NIAG_Abslt IS														--  Absolute address generation
		PORT(	Index 		:	IN	STD_LOGIC_VECTOR(25 DOWNTO 0);				--    IR index field
				NSA			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
				AbsltAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Absolute address output
	END COMPONENT NIAG_Abslt;
	
	COMPONENT NIAG_Rel IS														--  Relative address generation
		PORT(	Immed 		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    IR immediate field
				Xshft		:	IN	STD_LOGIC;									--    16 to 32 extender selection
				NSA			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
				RelAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Relative address output
	END COMPONENT NIAG_Rel;
	
	COMPONENT NIAG_Reg IS														--  Register address generation
		PORT(	Reg	 		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Register file B output
				RegAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Register address output
	END COMPONENT NIAG_Reg;

	COMPONENT NIAG_MUX IS														--  Program counter MUX
		PORT(	NxtAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
				AbsltAdrs	:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Absolute address
				RelAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Relative address
				RegAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Register address
				Cond		:	IN	STD_LOGIC_VECTOR(2  DOWNTO 0);				--    Logical condition to be tested
				Sel			:	IN	STD_LOGIC_VECTOR(1  DOWNTO 0);				--    Input selection bus
				Stat		:	IN	STAT_SIGNL_REC;								--    ALU status signals
				InstrAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Program counter input bus
	END COMPONENT NIAG_MUX;

	COMPONENT NIAG_Rtn IS														--  Function call return address
		PORT(	PC			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Program counter output
				RtnAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Return address output
	END COMPONENT NIAG_Rtn;

END PACKAGE;	