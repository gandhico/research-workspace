--------------------------------------------------------------------------------------
--  Component:   ALU
--	
--       File:   AluSolution.vhd
--	
--    Project:   LabCPU
--
--     Author:   A.K. Petersen
--
--    Purpose:   define a 32-bit ALU
--
--     Inputs:   Ain:  32-bit input
--               Bin:  32-bit input
--               Func: function selection
--
--    Outputs:   Rout: 32-bit result
--               Stat: ALU status codes
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
--------------------------------------------------------------------------------------- 

LIBRARY IEEE;
USE IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_362_ALU;
USE EE_362_ALU.ALU.all;

ENTITY ALU IS
PORT(	Ain		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);
		Bin		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);
		Func	:	IN	STD_LOGIC_VECTOR(4 DOWNTO 0);
		Shft	:	IN	STD_LOGIC_VECTOR(4 DOWNTO 0);
		Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
		Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;
 
ARCHITECTURE Behavioral OF ALU IS
	SIGNAL HiReg : std_logic_vector(31 downto 0);               -- Hi and Lo registers
	SIGNAL LoReg : std_logic_vector(31 downto 0);
 
BEGIN
	F00 : ALU_ADD PORT MAP(Ain, Bin, Func, Rout, Stat);
	F01 : ALU_AND PORT MAP(Ain, Bin, Func, Rout, Stat);
	F02 : ALU_DIVS PORT MAP(Ain, Bin, Func, HiReg, LoReg, Rout, Stat);
	F03 : ALU_DIVU PORT MAP(Ain, Bin, Func, HiReg, LoReg, Rout, Stat);
	F04 : ALU_MULS PORT MAP(Ain, Bin, Func, HiReg, LoReg, Rout, Stat);
	F05 : ALU_MULU PORT MAP(Ain, Bin, Func, HiReg, LoReg, Rout, Stat);
	F06 : ALU_NAND PORT MAP(Ain, Bin, Func, Rout, Stat);
	F07 : ALU_NEG PORT MAP(Bin, Func, Rout, Stat);
	F08 : ALU_NOR PORT MAP(Ain, Bin, Func, Rout, Stat);
	F09 : ALU_NOT PORT MAP(Bin, Func, Rout, Stat);
	F0A : ALU_OR PORT MAP(Ain, Bin, Func, Rout, Stat);
	F0B : ALU_RDHI PORT MAP(HiReg, Func, Rout, Stat);
	F0C : ALU_RDLO PORT MAP(LoReg, Func, Rout, Stat);
	F0D : ALU_SLA PORT MAP(Ain, Func, Shft, Rout, Stat);
	F0E : ALU_SLL PORT MAP(Ain, Func, Shft, Rout, Stat);
	F0F : ALU_SOLS PORT MAP(Ain, Bin, Func, Rout, Stat);
	F10 : ALU_SOLU PORT MAP(Ain, Bin, Func, Rout, Stat);
	F11 : ALU_SRA PORT MAP(Ain, Func, Shft, Rout, Stat);
	F12 : ALU_SRL PORT MAP(Ain, Func, Shft, Rout, Stat);
	F13 : ALU_SUB PORT MAP(Ain, Bin, Func, Rout, Stat);
	F14 : ALU_WRHI PORT MAP(Bin, Func, HiReg);
	F15 : ALU_WRLO PORT MAP(Bin, Func, LoReg);
	F16 : ALU_XNOR PORT MAP(Ain, Bin, Func, Rout, Stat);
	F17 : ALU_XOR PORT MAP(Ain, Bin, Func, Rout, Stat);
END ARCHITECTURE;
