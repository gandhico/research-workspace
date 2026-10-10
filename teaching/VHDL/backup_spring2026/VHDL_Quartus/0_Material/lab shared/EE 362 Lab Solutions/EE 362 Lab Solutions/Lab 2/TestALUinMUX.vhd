-------------------------------------------------------------------------------------
--Description:	TestALUinMUX
--
--       File:	TestALUinMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the ALU data input mux
--
--     Inputs:  RFaOut        Register File A output
--			    Immed32Data	  32-bit Immediate value
--				ALUinMuxCtrl  ALU MUX selection control signal
--					 
--    Outputs:  ALUinMuxOut   ALU MUX Output to ALU A input
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_MISC;
use EE_362_MISC.MISC_Pkg.all;


ENTITY TestALUinMUX IS
	PORT(	
			RFaOut			:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Immed32Data		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			ALUinMuxCtrl	:	IN		STD_LOGIC;
			ALUinMuxOut		:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestALUinMUX IS
BEGIN
		F00 : ALUinMUX  PORT MAP(RFaOut, Immed32Data, ALUinMuxCtrl,  ALUinMuxOut);
END ARCHITECTURE;
