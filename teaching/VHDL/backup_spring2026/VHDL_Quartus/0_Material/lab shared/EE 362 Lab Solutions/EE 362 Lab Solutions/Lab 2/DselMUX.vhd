-------------------------------------------------------------------------------------
--Description:	DselMUX
--
--       File:	DselMUX.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the Register File's Data input select MUX
--
--     Inputs:  RD      instruction register RD field
--			    RT      instruction register RT field
--				RET     function return register (1F)
--		   		Sel     select bus
--					 
--    Outputs:  Data 	result
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY DselMUX IS
	PORT(	RD		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);
			RT		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);
			RET		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);
			Sel		:	IN			STD_LOGIC_VECTOR(1 DOWNTO 0);
			Data	:	OUT			STD_LOGIC_VECTOR(4 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF DselMUX IS
BEGIN
	WITH Sel select
		Data <=	RD			WHEN RF_WSEL_RD,
				RT			WHEN RF_WSEL_RT,
				RET			WHEN RF_WSEL_RET,
				VAL_5_FLOAT	WHEN others;
END ARCHITECTURE;
