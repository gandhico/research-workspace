--------------------------------------------------------------------------------------
--  Component:	ALU_RDHI
--
--       File:	RdhiSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU read HI register operation
--
--     Inputs:  LoReg: Content of HI register;
--					 Func	: ALU function code
--
--    Outputs:  Rout: 32-bit result
--              Stat: ALU status codes
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY ALU_RDHI IS
	PORT(	HiReg	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_RDHI IS
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_RDHI) THEN						-- read HI function?
			Stat 	<= (others => 'Z');

			Rout	<= HiReg;								-- output content of LO register
			
			Stat.ALU_sign  <= HiReg(31);
			Stat.ALU_zero  <= NOT(OR_REDUCE(HiReg));
				
		ELSE
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
