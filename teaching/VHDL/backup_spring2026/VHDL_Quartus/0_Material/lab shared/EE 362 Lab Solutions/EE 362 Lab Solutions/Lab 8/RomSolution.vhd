-------------------------------------------------------------------------------------
--Description:	ROM
--
--       File:	RomSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the instruction memory module
--
--     Inputs:    Addr: address bus
--
--    Outputs:    Data: data bus
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_Memory;
use EE_362_Memory.Memory_Pkg.all;

ENTITY ROM IS
	PORT( Addr	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Data	:	INOUT	STD_LOGIC_VECTOR(31 DOWNTO 0)
	    );
END ENTITY;


ARCHITECTURE Behavioral OF ROM IS
	SIGNAL	ROM_Content	: ROM_Memory := (3=>X"01", 5=>X"02", 7=>X"03", 9=>X"04", 11=>X"05", 
										13=>X"06", 15=>X"07", others=>X"00");
BEGIN
	ROM_Content(to_integer(UNSIGNED(Addr))+0) <= Data(31 DOWNTO 24);		--     read: MSB
	ROM_Content(to_integer(UNSIGNED(Addr))+1) <= Data(23 DOWNTO 16);		--	         next-to-MSB
	ROM_Content(to_integer(UNSIGNED(Addr))+2) <= Data(15 DOWNTO  8);		--           next-to-LSB
	ROM_Content(to_integer(UNSIGNED(Addr))+3) <= Data(7  DOWNTO  0);		--	         LSB
END ARCHITECTURE;
