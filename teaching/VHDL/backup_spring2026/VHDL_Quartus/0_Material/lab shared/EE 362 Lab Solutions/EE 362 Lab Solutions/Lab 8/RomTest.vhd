-------------------------------------------------------------------------------------
--Description:	TestROM
--
--       File:	RomTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define a test stub for the instruction memory module
--
--     Inputs:    Addr	: address bus
--                  en	: memory enable
--
--     InOuts:    Data	: data bus
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

library EE_362_Memory;
use EE_362_Memory.Memory_Pkg.all;

ENTITY TestROM IS
	PORT(	Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
		    Data	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)
	    );
END ENTITY;


ARCHITECTURE Behavioral OF TestROM IS
BEGIN
		F01 : ROM  PORT MAP(Addr, Data);
END ARCHITECTURE;
