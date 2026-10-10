-------------------------------------------------------------------------------------
--Description:	TestDinMUX
--
--       File:	TestDinMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define test stub for the Reg File data input mux
--
--     Inputs:  ALUresult   ALU output
--			    MemData	    Memory or Reg File A
--				RetAddrs    Function return address
--				DinMUXCtrl  Reg File data input mux selection control signal
--					 
--    Outputs:  DinMUXout   Reg File data input mux Output
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


ENTITY TestDinMUX IS
	PORT(	
			ALUresult		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			MemData			:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			RetAddrs			:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			DinMUXCtrl		:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);
			DinMUXout		:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0)
		 );
END ENTITY;

ARCHITECTURE Behavioral OF TestDinMUX IS
BEGIN
		F02 : DinMUX	PORT MAP(ALUresult, MemData, RetAddrs, DinMUXCtrl,  DinMUXout);
END ARCHITECTURE;
