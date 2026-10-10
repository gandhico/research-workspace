--------------------------------------------------------------------------------------
--  Component:	ALU_MULS
--
--       File:	MulsSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define a 32-bit ALU signed multiply operation
--
--     Inputs:   Ain:  	32-bit operand
--               Bin:  	32-bit operand
--               Func: 	ALU function code
--
--    Outputs:   HiReg:	high order 32-bit word
--               LoReg:	low order  32-bit word
--               Rout : low order  32-bit word
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

ENTITY ALU_MULS IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT		STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_MULS IS
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedRout		:	SIGNED(63 DOWNTO 0);
	
BEGIN
	PROCESS(Func) IS
	BEGIN
		IF(Func = ALU_FUNC_MULS) THEN								-- signed multiply function?
			SignedAin	<= SIGNED(Ain);
			SignedBin	<= SIGNED(Bin);
			Stat  		<= (others => 'Z');
			
			SignedRout <= SignedAin * SignedBin;		      		-- calculate product
			
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  <= SignedRout(31);
			
			LoReg <= STD_LOGIC_VECTOR(SignedRout)(31 DOWNTO 0);	--	save low word in LO
			HiReg <= STD_LOGIC_VECTOR(SignedRout)(63 DOWNTO 32);	--	save high word in HI
			Rout  <= STD_LOGIC_VECTOR(SignedRout)(31 DOWNTO 0);	--	return low word
		ELSE
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat  <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
