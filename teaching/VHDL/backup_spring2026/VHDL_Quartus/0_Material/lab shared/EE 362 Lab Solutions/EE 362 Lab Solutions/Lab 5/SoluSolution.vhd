--------------------------------------------------------------------------------------
--  Component:	ALU_SOLU
--
--       File:	SoluSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU unsigned set-on-less operation
--
--     Inputs:   Ain:  32-bit operand
--               Bin:  32-bit operand
--               Func: ALU function code
--
--    Outputs:   Rout: result
--               Stat: status signal bus: bit 1 = Zero
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY ALU_SOLU IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SOLU IS
	SIGNAL UnsignedAin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedBin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedRout		:	UNSIGNED(31 DOWNTO 0);
	
BEGIN
	UnsignedAin	<= UNSIGNED(Ain);
	UnsignedBin	<= UNSIGNED(Bin);
	
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_SOLU) THEN							-- unsigned set-on-less function?
			Stat <= (others => 'Z');

			IF(UnsignedAin < UnsignedBin) THEN					--     calculate result
				UnsignedRout	<= to_unsigned(1, 32);
				Stat.ALU_zero  	<= '0';
			ELSE
				UnsignedRout	<= to_unsigned(0, 32);
				Stat.ALU_zero  	<= '1';
			END IF;
			
			Rout <= STD_LOGIC_VECTOR(UnsignedRout);			     -- output result
			
		ELSE
			Rout	<= (others => 'Z');
			Stat	<= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
