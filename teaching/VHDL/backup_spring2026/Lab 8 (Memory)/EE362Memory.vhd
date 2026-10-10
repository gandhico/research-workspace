-------------------------------------------------------------------------------------
--    Library:	EE_212_Memory
--
--       File:	EE212Memory.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the system memory
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;


PACKAGE Memory_Pkg IS
	TYPE	RAM_Memory IS ARRAY(0 to 511) OF STD_LOGIC_VECTOR(7 DOWNTO 0);			-- RAM storage
	TYPE	ROM_Memory IS ARRAY(0 to 511) OF STD_LOGIC_VECTOR(7 DOWNTO 0);			-- ROM storage
	
	COMPONENT RAM IS																-- Random Access Memory
		PORT(	Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);					--   Address
				Strb	:	IN		STD_LOGIC;										--   Strobe
				rw		:	IN		STD_LOGIC;										--   Read/Write
				en		:	IN		STD_LOGIC;										--   Enable
				clk : in std_logic;
				Data	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)					--   Data in and out
			 );
	END COMPONENT RAM;

	
	COMPONENT ROM IS																-- Read Only Memory
		PORT(	Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);					--   Address
				Data	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0)					--   Data in and out
			 );
	END COMPONENT ROM;
END PACKAGE;	
