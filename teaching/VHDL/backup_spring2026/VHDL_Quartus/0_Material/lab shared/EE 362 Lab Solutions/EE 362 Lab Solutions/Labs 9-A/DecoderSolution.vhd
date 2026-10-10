-------------------------------------------------------------------------------------
--Description:	Decoder
--
--       File:	DecoderSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the instruction Decode logic
--
--     Inputs:  Instruction : instruction to be decoded
--
--		Outputs:  CtrlSgnls : control signals
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_ALU;
USE EE_362_ALU.ALU_Pkg.all;


ENTITY Decoder IS
	PORT(	Instruction	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			CtrlSgnls	:	OUT		CTRL_SIGNL_REC);
END ENTITY;


ARCHITECTURE Behavioral OF Decoder IS
	BEGIN
		I00 : Decode_ADD    PORT MAP(Instruction, CtrlSgnls);
		I01 : Decode_ADDI   PORT MAP(Instruction, CtrlSgnls);
		I02 : Decode_ADDIU  PORT MAP(Instruction, CtrlSgnls);
		I03 : Decode_ADDU   PORT MAP(Instruction, CtrlSgnls);
		I04 : Decode_AND    PORT MAP(Instruction, CtrlSgnls);
		I05 : Decode_ANDI   PORT MAP(Instruction, CtrlSgnls);
		I06 : Decode_BEQ    PORT MAP(Instruction, CtrlSgnls);
		I07 : Decode_BGEZ   PORT MAP(Instruction, CtrlSgnls);
		I08 : Decode_BGEZAL PORT MAP(Instruction, CtrlSgnls);
		I09 : Decode_BGTZ   PORT MAP(Instruction, CtrlSgnls);
		I0A : Decode_BLEZ   PORT MAP(Instruction, CtrlSgnls);
		I0B : Decode_BLTZAL PORT MAP(Instruction, CtrlSgnls);
		I0C : Decode_BNE    PORT MAP(Instruction, CtrlSgnls);
		I0D : Decode_DIV    PORT MAP(Instruction, CtrlSgnls);
		I0E : Decode_DIVU   PORT MAP(Instruction, CtrlSgnls);
		I0F : Decode_J		PORT MAP(Instruction, CtrlSgnls);
		I10 : Decode_JAL    PORT MAP(Instruction, CtrlSgnls);
		I11 : Decode_JALR   PORT MAP(Instruction, CtrlSgnls);
		I12 : Decode_JR	    PORT MAP(Instruction, CtrlSgnls);
		I13 : Decode_LB	    PORT MAP(Instruction, CtrlSgnls);
		I14 : Decode_LBU    PORT MAP(Instruction, CtrlSgnls);
		I15 : Decode_LH	    PORT MAP(Instruction, CtrlSgnls);
		I16 : Decode_LHU    PORT MAP(Instruction, CtrlSgnls);
		I17 : Decode_LUI    PORT MAP(Instruction, CtrlSgnls);
		I18 : Decode_LW	    PORT MAP(Instruction, CtrlSgnls);
		I19 : Decode_MFHI   PORT MAP(Instruction, CtrlSgnls);
		I1A : Decode_MFLO   PORT MAP(Instruction, CtrlSgnls);
		I1B : Decode_MTHI   PORT MAP(Instruction, CtrlSgnls);
		I1C : Decode_MTLO	PORT MAP(Instruction, CtrlSgnls);
		I1D : Decode_MUL	PORT MAP(Instruction, CtrlSgnls);
		I1E : Decode_MULT   PORT MAP(Instruction, CtrlSgnls);
		I1F : Decode_MULTU  PORT MAP(Instruction, CtrlSgnls);
		I20 : Decode_NOR    PORT MAP(Instruction, CtrlSgnls);
		I21 : Decode_OR     PORT MAP(Instruction, CtrlSgnls);
		I22 : Decode_ORI	PORT MAP(Instruction, CtrlSgnls);
		I23 : Decode_SB     PORT MAP(Instruction, CtrlSgnls);
		I24 : Decode_SH     PORT MAP(Instruction, CtrlSgnls);
		I25 : Decode_SLA    PORT MAP(Instruction, CtrlSgnls);
		I26 : Decode_SLAV   PORT MAP(Instruction, CtrlSgnls);
		I27 : Decode_SLL    PORT MAP(Instruction, CtrlSgnls);
		I28 : Decode_SLLV   PORT MAP(Instruction, CtrlSgnls);
		I29 : Decode_SLT	PORT MAP(Instruction, CtrlSgnls);
		I2A : Decode_SLTI	PORT MAP(Instruction, CtrlSgnls);
		I2B : Decode_SLTIU  PORT MAP(Instruction, CtrlSgnls);
		I2C : Decode_SLTU	PORT MAP(Instruction, CtrlSgnls);
		I2D : Decode_SRA	PORT MAP(Instruction, CtrlSgnls);
		I2E : Decode_SRAV   PORT MAP(Instruction, CtrlSgnls);
		I2F : Decode_SRL    PORT MAP(Instruction, CtrlSgnls);
		I30 : Decode_SRLV   PORT MAP(Instruction, CtrlSgnls);
		I31 : Decode_SUB    PORT MAP(Instruction, CtrlSgnls);
		I32 : Decode_SUBU   PORT MAP(Instruction, CtrlSgnls);
		I33 : Decode_SW     PORT MAP(Instruction, CtrlSgnls);
		I34 : Decode_XOR    PORT MAP(Instruction, CtrlSgnls);
		I35 : Decode_XORI   PORT MAP(Instruction, CtrlSgnls);
END ARCHITECTURE;
