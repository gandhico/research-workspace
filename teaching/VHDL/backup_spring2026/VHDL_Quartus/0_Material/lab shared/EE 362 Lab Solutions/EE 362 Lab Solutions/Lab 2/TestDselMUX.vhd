-------------------------------------------------------------------------------------
--Description:	TestDselMUX
--
--       File:	TestDselMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the Reg File data input selection mux
--
--     Inputs:  IRrd         Instruction Register rd field
--			    IRrt	     Instruction Register rt field
--				RetAddrsReg  Function return address register (1F)
--				DselMuxCtrl  Reg File data input mux selection control signal
--					 
--    Outputs:  DselMUXout   Reg File data input selection mux Output
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


ENTITY TestDselMUX IS
	PORT(	
			IRrd			:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			IRrt			:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			RetAddrsReg		:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
			DselMuxCtrl		:	IN		STD_LOGIC_VECTOR(1 DOWNTO 0);
			DselMuxOut		:	OUT		STD_LOGIC_VECTOR(4 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestDselMUX IS
BEGIN
		F03 : DselMUX	PORT MAP(IRrd, IRrt, RetAddrsReg, DselMuxCtrl, DselMuxOut);
END ARCHITECTURE;
