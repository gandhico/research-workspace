--------------------------------------------------------------------------------------
--  Component:	ALU_DIVU
--
--       File:	DivuSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU unsigned divide operation
--
--     Inputs:   Ain:  32-bit operand
--               Bin:  32-bit operand
--               Func: ALU function code
--
--    Outputs:   HiReg:	32-bit remainder
--               LoReg:	32-bit quotient
--                Rout:	quotient
--                Stat: ALU status codes
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

LIBRARY EE_362_ALU_Pkg;
USE EE_362_ALU.ALU_Pkg.all;

ENTITY ALU_DIVU IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_DIVU IS
	SIGNAL unSignedAin	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedBin	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedInt	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedRem	:	UNSIGNED(31 DOWNTO 0);
	
BEGIN
	unSignedAin	<= UNSIGNED(Ain);									-- convert inputs to unsigned
	unSignedBin	<= UNSIGNED(Bin);
	
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_DIVU) THEN								-- unsigned divide function?
			Stat <= (others => 'Z');
			
			IF(unSignedBin /= 0) THEN								-- 	divide by zero?
																			--	no-
				unSignedInt	<= unSignedAin / unSignedBin;			-- 			calculate quotient
				unSignedRem	<= unSignedAin MOD unSignedBin;			--    		calculate remainder
				
				HiReg			<= STD_LOGIC_VECTOR(unSignedRem);	--				output remainder
				LoReg			<= STD_LOGIC_VECTOR(unSignedInt);	--				output quotient
				Rout  			<= STD_LOGIC_VECTOR(UnsignedInt);	--          return quotient
				Stat.ALU_zero	<= '0';
			ELSE													--			yes-
				HiReg 			<= (others => 'Z');					--				output nothing but a
				LoReg 			<= (others => 'Z');
				Rout  			<= (others => 'Z');
				Stat.ALU_zero	<= '1';								-- 			division by zero warning
			END IF;	
		ELSE
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
