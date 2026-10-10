-------------------------------------------------------------------------------------
--    Library:	EE_212_MISC
--
--       File:	EE212MISC.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the Miscellaneous components
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;


PACKAGE MISC_Pkg IS

	COMPONENT DinMUX IS																--  Register file data input mux
		PORT(	ALUresult	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    ALU result value
				MemData		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Memory data value
				RetAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Function call return addrress
				Sel			:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);			--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
	END COMPONENT DinMUX;

	COMPONENT DselMUX IS															--  Register file write select															--  
		PORT(	RD			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR RD field
				RT			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR RT field
				RET			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    function call return register (1F) 
				Sel			:	IN			STD_LOGIC_VECTOR(1 DOWNTO 0);			--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(4 DOWNTO 0));			--    Data output bus
	END COMPONENT DselMUX;

	COMPONENT ALUinMUX IS															--  ALU A-input select													--  
		PORT(	Aout		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register file A output value
				Immed		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    IR immediate field
				Sel			:	IN			STD_LOGIC;								--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
	END COMPONENT ALUinMUX;

	COMPONENT ALUsftMUX IS															--  ALU shift selection mux
		PORT(	RS			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR rs field
				Bout		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    Register file B output
				Sel			:	IN			STD_LOGIC;								--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(4 DOWNTO 0));			--    Data output bus
	END COMPONENT ALUsftMUX;
	
	COMPONENT PCMUX IS																--  Program counter selection bus
		PORT(	NxtAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Next sequential address
				RelAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Relative address
				RegAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register address
				AbsltAdrs	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Absolute address
				Sel			:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);			--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
	END COMPONENT PCMUX;
	
	COMPONENT ImmedXtnd IS															--  Immediate 16 to 32 extender
		PORT(	Immed16		:	IN			STD_LOGIC_VECTOR(15 DOWNTO 0);			--    IR immediate field
				Sel			:	IN			STD_LOGIC;								--    Sign or unsigned selection
				Immed32		:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
	END COMPONENT ImmedXtnd;

	COMPONENT TriBuffer IS															--  Tri-state buffer 
		PORT(	Sel			:	IN			STD_LOGIC;								--    Enable
				Aout		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register file B output
				DataBus		:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
	END COMPONENT TriBuffer;

	COMPONENT RatsNest IS															--  Rat's nest
		PORT(	MEMrw		:	IN			STD_LOGIC;								--    Memory read/write
				RNsize		:	IN			STD_LOGIC_VECTOR(3  DOWNTO 0);			--    Extraction data size
				RFdb		:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register file data input
				MEMdb		:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0)			--    Memory data bus
			);
	END COMPONENT RatsNest;

END PACKAGE;	