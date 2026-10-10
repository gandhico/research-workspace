-------------------------------------------------------------------------------------
--Description:	TestImmedXtnd
--
--       File:	TestImmedXtnd.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the immediate 16-to-32-bit extender
--
--     Inputs:  Immed16Data    16-bit Instruction Register immediate field
--			    ImmedXtndCtrl  immediate field sign extender control signal
--					 
--    Outputs:  ImmedXtndOut   32-bit immediate field extender Output
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


ENTITY TestImmedXtnd IS
	PORT(	
			Immed16Data		:	IN			STD_LOGIC_VECTOR(15 DOWNTO 0);
			ImmedXtndCtrl	:	IN			STD_LOGIC;
			ImmedXtndOut	:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestImmedXtnd IS
BEGIN
		F04 : ImmedXtnd PORT MAP(Immed16Data, ImmedXtndCtrl, ImmedXtndOut);
END ARCHITECTURE;
