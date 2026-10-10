-------------------------------------------------------------------------------------
--    Library:	EE_212_CPU
--
--       File:	EE212CPU.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the Central Proccessing Unit
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

PACKAGE LabCPU_Pkg IS

	COMPONENT CPU IS
		PORT(	Clk		:	IN		STD_LOGIC);
	END COMPONENT CPU;
	
	CONSTANT	CPU_BYTE_SIZE	:	INTEGER	:= 4;
	CONSTANT	CPU_BIT_SIZE	:	INTEGER	:= 32;
	
END PACKAGE;	
