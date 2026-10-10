--------------------------------------------------------------------------------------
--  Component:	NIAG_Abslt
--
--       File:	NIAG_Abslt.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the absolute instruction address
--
--     Inputs:	   Index: Index field from IR
--                   NSA: Next Sequential Address
--
--    Outputs: AbsltAdrs: absolute instruction's address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

ENTITY NIAG_Abslt IS
	PORT(	Index 		:	IN		STD_LOGIC_VECTOR(25 DOWNTO 0);
			NSA			:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			AbsltAdrs	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_Abslt IS
	BEGIN
		AbsltAdrs <= NSA(31 DOWNTO 28) & Index & "00";
END ARCHITECTURE;
