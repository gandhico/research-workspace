--------------------------------------------------------------------------------------
--  Component:	NIAG_Reg
--
--       File:	NIAG_Reg.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the register instruction address
--
--     Inputs:	   Reg: ALU's B output
--
--    Outputs: RegAdrs: register instruction address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

ENTITY NIAG_ReG IS
	PORT(	Reg	 	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			RegAdrs	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_Reg IS
	BEGIN
		RegAdrs <= Reg;
END ARCHITECTURE;
