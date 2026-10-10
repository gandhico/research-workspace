--------------------------------------------------------------------------------------
--  Component:	ALU_MULU
--
--       File:	MuluSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU unsigned multiply operation
--
--     Inputs:   Ain:  	32-bit operand
--               Bin:  	32-bit operand
--               Func: 	ALU function code
--
--    Outputs:   HiReg:	High-order 32-bit word
--               LoReg:	Low-order 32-bit word
--               Rout : low order 32-bit word
--                Stat: ALU status codes
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

ENTITY ALU_MULU IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_MULU IS
	SIGNAL UnsignedAin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedBin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedRout		:	UNSIGNED(63 DOWNTO 0);
	
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_MULU) THEN							-- unsigned multiply function?
			UnsignedAin	<= UNSIGNED(Ain);
			UnsignedBin	<= UNSIGNED(Bin);
			Stat 	    <= (others => 'Z');
			
			UnsignedRout <= UnsignedAin * UnsignedBin;		    -- calculate product
			
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(UnsignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  <= UnsignedRout(31);
			
			LoReg <= STD_LOGIC_VECTOR(UnsignedRout)(31 DOWNTO 0);	--	save low word in LO
			HiReg <= STD_LOGIC_VECTOR(UnsignedRout)(63 DOWNTO 32);--	save high word in HI
			Rout  <= STD_LOGIC_VECTOR(UnsignedRout)(31 DOWNTO 0);	--	return low word
		ELSE
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat  <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
