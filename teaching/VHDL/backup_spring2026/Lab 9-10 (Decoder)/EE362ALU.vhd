--------------------------------------------------------------------------------------
--    Library:	EE_212_ALU
--
--       File:	EE212ALU.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: define constants and components for the CPU's ALU
--
--  Copyright 2020 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

PACKAGE ALU_Pkg IS
																					-- ALU function codes
	CONSTANT		ALU_FUNC_FLOAT	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "ZZZZZ";		--		float (not used)
	CONSTANT		ALU_FUNC_ADD	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00000";		--		addition
	CONSTANT		ALU_FUNC_SUB	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00001";		--		subtration
	CONSTANT		ALU_FUNC_MULS	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00010";		--		signed multiplication
	CONSTANT		ALU_FUNC_MULU	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00011";		--		unsigned multiplication
	CONSTANT		ALU_FUNC_DIVS	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00100";		--		signed division
	CONSTANT		ALU_FUNC_DIVU	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00101";		--		unsigned division
	CONSTANT		ALU_FUNC_NEG	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00110";		--		negation
	CONSTANT		ALU_FUNC_SLA	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "00111";		--		shift left arithmetic
	CONSTANT		ALU_FUNC_SRA	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01000";		--		shift right arithmetic
	CONSTANT		ALU_FUNC_SOLS	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01001";		--		signed set on less
	CONSTANT		ALU_FUNC_SOLU	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01010";		--		unsigned set on less
	CONSTANT		ALU_FUNC_AND	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01011";		--		bitwise AND
	CONSTANT		ALU_FUNC_NAND	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01100";		--		bitwise NAND
	CONSTANT		ALU_FUNC_OR		:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01101";		--		bitwise OR
	CONSTANT		ALU_FUNC_NOR	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01110";		--		bitwise NOR
	CONSTANT		ALU_FUNC_XOR	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "01111";		--		bitwise XOR
	CONSTANT		ALU_FUNC_XNOR	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "10000";		--		bitwise XNOR
	CONSTANT		ALU_FUNC_NOT	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "10001";		--		bitwise inversion
	CONSTANT		ALU_FUNC_SLL	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "10010";		--		shift left logical
	CONSTANT		ALU_FUNC_SRL	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "10011";		--		shift right logical

	CONSTANT		ALU_FUNC_RDLO	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "11100";		--		read LO register
	CONSTANT		ALU_FUNC_RDHI	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "11101";		--		read HI register
	CONSTANT		ALU_FUNC_WRLO	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "11110";		--		write LO register
	CONSTANT		ALU_FUNC_WRHI	:	STD_LOGIC_VECTOR(4 DOWNTO 0) := "11111";		--		write HI register

	CONSTANT		ALU_STAT_FLOAT	:	STD_LOGIC					 := 'Z';			--		status code float (don't use)
	CONSTANT		ALU_STAT_N_ZERO :	STD_LOGIC					 := '0';			--		status code reset
	CONSTANT		ALU_STAT_ZERO	:	STD_LOGIC					 := '1';			--		status code set
	CONSTANT		ALU_STAT_POS	:	STD_LOGIC					 := '0';			--		status code reset
	CONSTANT		ALU_STAT_NEG	:	STD_LOGIC					 := '1';			--		status code set
	
	TYPE STAT_SIGNL_REC is record													--  ALU status signal record										
					ALU_zero		:	std_logic;										--		zero status                
					ALU_sign		:	std_logic;										--		sign ststus                
	END RECORD;  
 

						
	COMPONENT ALU IS																--    ALU body (calls the functions)
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						--		A input value
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);						--		B input value
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);						--		Function code input
				Shft	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);						--		Shift input value
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);						--		Result output value
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

																					--	ALU function components
	COMPONENT ALU_ADD IS																--    addition function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_SUB IS																--    subtract function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_MULS IS																--    signed multiply function
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

						
	COMPONENT ALU_MULU IS																--    unsigned multiply function
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_DIVS IS																--    signed divide function
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_DIVU IS																--    unsigned divide function
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_NEG IS																--    negate function
		PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_SLA IS																--    shift left arithmetic function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_SRA IS																--    shift right arithmetic function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

																						--    signed set on less function
	COMPONENT ALU_SOLS IS
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_SOLU IS																--    unsigned set on less function
	PORT(		Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_RDLO IS																--    read LO function
		PORT(	LoReg	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_RDHI IS																--    read HI function
		PORT(	HiReg	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_WRHI IS																--    write HI function
		PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				HiReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
	END COMPONENT;
						
	COMPONENT ALU_WRLO IS																--    write LO function
		PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				LoReg	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));
	END COMPONENT;
						
	COMPONENT ALU_AND IS																--    AND function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_NAND IS																--    NAND function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
					
	COMPONENT ALU_OR IS																	--    OR function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_NOR IS																--    NOR function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_XOR IS																--    XOR function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
						
	COMPONENT ALU_XNOR IS																--    XNOR function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_NOT IS																--    negate function
		PORT(	Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;

	COMPONENT ALU_SLL IS																--    shift left logical function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
					
	COMPONENT ALU_SRL IS																--    shift right logical function
		PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4 DOWNTO 0);
				Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				Rout	:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT		STAT_SIGNL_REC);
	END COMPONENT;
END PACKAGE;
