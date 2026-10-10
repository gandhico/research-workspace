--------------------------------------------------------------------------------------
--  Component:	NIAG_Rtn
--
--       File:	NIAG_Rtn.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define the procedure return address
--
--     Inputs:	     PC: Current Intruction's address
--
--    Outputs:  RtnAdrs: return address
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;
USE IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_CPU;
USE EE_362_CPU.LabCPU_Pkg.all;

ENTITY NIAG_Rtn IS
	PORT(	PC			:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			RtnAdrs		:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF NIAG_Rtn IS
	BEGIN
		RtnAdrs <= std_logic_vector(unsigned(PC) + (CPU_BYTE_SIZE * 2));
END ARCHITECTURE;
