-------------------------------------------------------------------------------------
--Description:	TestRAM
--
--       File:	RamTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define a test stub for the data memory module
--
--     Inputs:    Addr	: address bus
--			      Strb	: clock
--			        rw	: read/write control signal
--                  en	: memory output enable
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

ENTITY TestRAM IS
	PORT(	Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Strb	:	IN		STD_LOGIC;
			  rw	:	IN		STD_LOGIC;
			  en	:	IN		STD_LOGIC;
		    Data	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)
	    );
END ENTITY;


ARCHITECTURE Behavioral OF TestRAM IS
BEGIN
		F00 : RAM  PORT MAP(Addr, Strb, rw, en,  Data);
END ARCHITECTURE;
