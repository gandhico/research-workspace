-------------------------------------------------------------------------------------
--Description:	ALUsftMUX
--
--       File:	ALUsftMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the ALU's shift input MUX
--
--     Inputs:  RS 	      ALU result bus
--			    Bout	  data memory data
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


ENTITY ALUsftMUX IS
	PORT(	RS			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);
			Bout		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);
			Sel			:	IN			STD_LOGIC;
			Data		:	OUT			STD_LOGIC_VECTOR(4 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF ALUsftMUX IS
BEGIN
	WITH Sel select
		Data <=	RS		 	 WHEN ALU_SSEL_RS,
				Bout		 WHEN ALU_SSEL_BOUT,
				VAL_5_FLOAT  WHEN others;
END ARCHITECTURE;
