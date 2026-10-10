-------------------------------------------------------------------------------------
--    Library:	EE_212_RegFile
--
--       File:	EE212RegFile.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the Register File
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

PACKAGE RegFile_Pkg IS

	COMPONENT RegFile IS												--  register file
		PORT(	Asel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    A select bus
				Bsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    B select bus
				Dsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);		--    Data write select bus
				 Din	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);		--    Data input value
				Strb	:	IN		STD_LOGIC;							--    strobe
				Aout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);		--    A output value
				Bout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);		--    B output value
				clk:		IN		STD_LOGIC);		
	END COMPONENT RegFile;
	
END PACKAGE;