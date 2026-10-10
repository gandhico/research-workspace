-------------------------------------------------------------------------------------
--Description:	ImmedXtnd
--
--       File:	ImmedXtnd.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the immediate field 16-to-32 extender
--
--     Inputs:  Immed16    16-bit IR Immed field
--		   		Sel	       select bus
--					 
--    Outputs:  Immed32	   32-bit version of IR Immediate field
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY ImmedXtnd IS
	PORT(	Immed16	:	IN			STD_LOGIC_VECTOR(15 DOWNTO 0);
			Sel		:	IN			STD_LOGIC;
			Immed32	:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF ImmedXtnd IS
BEGIN
	WITH Sel select
		 Immed32 <=	std_logic_vector(resize(unsigned(Immed16), Immed32'length))	 WHEN IR_XSEL_ZERO,
					std_logic_vector(resize(  signed(Immed16), Immed32'length))	 WHEN others;
END ARCHITECTURE;
