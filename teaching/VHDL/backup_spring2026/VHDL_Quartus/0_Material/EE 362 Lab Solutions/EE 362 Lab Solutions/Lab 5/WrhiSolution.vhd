--------------------------------------------------------------------------------------
--  Component:	ALU_WRHI
--
--       File:	WrhiSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU write HI register operation
--
--     Inputs:  Bin	: Value to write to HI register
--					 Func	: ALU function code
--
--    Outputs:  HiReg: HI register
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY ALU_WRHI IS
	PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
END ENTITY;

ARCHITECTURE Behavioral OF ALU_WRHI IS
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_WRHI) THEN			-- write HI function?
			HiReg <= Bin;						-- output Ain back to the HI register
		ELSE
			HiReg <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
