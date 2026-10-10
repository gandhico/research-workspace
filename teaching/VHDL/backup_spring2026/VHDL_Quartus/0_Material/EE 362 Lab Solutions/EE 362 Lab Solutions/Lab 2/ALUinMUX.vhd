-------------------------------------------------------------------------------------
--Description:	ALUinMUX
--
--       File:	ALUinMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the ALU's Data input MUX
--
--     Inputs:  Aout	  ALU result bus
--			    Immed	  data memory data
--		   		Sel	      select bus
--					 
--    Outputs:  Data  	   result
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY ALUinMUX IS
	PORT(	Aout		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			Immed		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			Sel			:	IN			STD_LOGIC;
			Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF ALUinMUX IS
BEGIN
	WITH Sel select
		Data <=	Aout	 		WHEN ALU_ASEL_AOUT,
				Immed		 	WHEN ALU_ASEL_IMMED,
				VAL_32_FLOAT 	WHEN others;
END ARCHITECTURE;
