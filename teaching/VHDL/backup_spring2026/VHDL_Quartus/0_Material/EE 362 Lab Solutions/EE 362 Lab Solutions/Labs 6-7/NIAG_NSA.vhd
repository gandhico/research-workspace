--------------------------------------------------------------------------------------
--  Component:	NIAG_NSA
--
--       File:	NIAG_NSA.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the next sequential instruction address
--
--     Inputs:	     PC: Current Intruction's address
--
--    Outputs:      NSA: next sequential instruction's address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_CPU;
USE EE_362_CPU.LabCPU_Pkg.all;

ENTITY NIAG_NSA IS
	PORT(	PC		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			NSA		:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_NSA IS
	BEGIN
		NSA <= std_logic_vector(unsigned(PC) + CPU_BYTE_SIZE);
END ARCHITECTURE;
