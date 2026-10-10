-------------------------------------------------------------------------------------
--Description:	TriBuffer
--
--       File:	TriBuffer.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the register file tri-state buffer
--
--     Inputs:  Sel	      selection bus
--              Aout      register file A output
--
--	   InOuts:  DataBus   bi-directional data memory data bus
--					 
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;


ENTITY TriBuffer IS
	PORT(	Sel		:	IN			STD_LOGIC;
			Aout	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);
			DataBus	:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF TriBuffer IS
BEGIN
	WITH Sel select
		 DataBus <=	Aout	 		WHEN RF_OE_DRIVE,
					VAL_32_FLOAT	WHEN others;
END ARCHITECTURE;
