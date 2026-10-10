-------------------------------------------------------------------------------------
--Description:	DinMUX
--
--       File:	DinMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the Register File's Data input MUX
--
--     Inputs:  ALUresult  ALU result bus
--			    MemData	   data memory data
--				RrturnAdrs function return address
--		   		Sel	       select bus
--					 
--    Outputs:  Data 	   result
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY DinMUX IS
	PORT(	ALUresult	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			MemData		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			RetAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			Sel			:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);
			Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF DinMUX IS
BEGIN
	WITH Sel select
		 Data <=	ALUresult	 WHEN RF_DSEL_ALU,
					MemData		 WHEN RF_DSEL_MEM,
					RetAdrs		 WHEN RF_DSEL_RET,
					VAL_32_FLOAT WHEN others;
END ARCHITECTURE;
