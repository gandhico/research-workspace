-------------------------------------------------------------------------------------
--Description:	TestALUshftMUX
--
--       File:	TestALUshftMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the ALU shift selection mux
--
--     Inputs:  IRrs            Instruction Register rs field
--			    RFbOut	        Register File B Output (bits 4-0)
--				ALUsftMuxCtrl	ALU Shift selection control signal
--					 
--    Outputs:  ALUsftMuxOut	ALU shift MUX Output to ALU
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


ENTITY TestALUshftMUX IS
	PORT(	
			IRrs			:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			RFbOut			:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			ALUsftMuxCtrl	:	IN		STD_LOGIC;
			ALUsftMuxOut	:	OUT		STD_LOGIC_VECTOR(4 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestALUshftMUX IS
BEGIN
		F01 : ALUsftMUX PORT MAP(IRrs, RFbOut, ALUsftMuxCtrl,  ALUsftMuxOut);
END ARCHITECTURE;
