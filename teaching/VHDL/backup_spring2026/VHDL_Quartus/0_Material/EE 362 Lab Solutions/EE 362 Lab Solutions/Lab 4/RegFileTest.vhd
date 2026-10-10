-------------------------------------------------------------------------------------
--Description:	RegFileTest
--
--       File:	RegFileTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Test stub for Register File
--
--     Inputs:    Asel: 5-bit  Aout select bus
--                Bsel: 5-bit  Bout select bus
--                Dsel: 5-bit  Bout select bus
--                 Din: 32-bit data input bus
--			      Strb: Data input save strobe
--
--    Outputs:    Aout:	32-bit output selected by Asel
--                Bout: 32-bit output selected by Bsel
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_RegFile;
use EE_362_RegFile.RegFile_Pkg.all;


ENTITY RegFileTest IS
	PORT(	Asel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Bsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Dsel	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			 Din	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Strb	:	IN		STD_LOGIC;
			Aout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF RegFileTest IS
BEGIN
	TestComponent : RegFile  PORT MAP(Asel, Bsel, Dsel, Din, Strb,  Aout, Bout);
END ARCHITECTURE;
