-------------------------------------------------------------------------------------
--Description:	TestCPU
--
--       File:	CpuTest.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose:  Test stub for the Central Processor
--
--     Inputs:  Clk: system master clock
--
--    Outputs:  None
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_CPU;
use EE_362_CPU.LabCPU_Pkg.all;


ENTITY TestCPU IS
	PORT(	Clk	:	IN		STD_LOGIC);
END ENTITY;

ARCHITECTURE Behavioral OF TestCPU IS
BEGIN
	TestComponent : CPU  PORT MAP(Clk);
END ARCHITECTURE;
