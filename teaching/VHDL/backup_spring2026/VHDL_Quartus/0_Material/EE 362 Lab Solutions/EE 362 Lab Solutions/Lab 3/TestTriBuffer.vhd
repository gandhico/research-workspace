-------------------------------------------------------------------------------------
--Description:	TestTriBuffer
--
--       File:	TestTriBuffer.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the Register File A output tri-state buffer
--
--     Inputs:  TriBufferIn    Register File's A output
--			    TriBufferCtrl  tri-state buffer control signal
--					 
--    InOuts:   TriBufferOut   tri-state buffer output
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


ENTITY TestTriBuffer IS
	PORT(	
			TriBufferIn		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			TriBufferCtrl	:	IN			STD_LOGIC;
			TriBufferOut	:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestTriBuffer IS
BEGIN
		F05 : TriBuffer PORT MAP(TriBufferCtrl, TriBufferIn, TriBufferOut);
END ARCHITECTURE;
