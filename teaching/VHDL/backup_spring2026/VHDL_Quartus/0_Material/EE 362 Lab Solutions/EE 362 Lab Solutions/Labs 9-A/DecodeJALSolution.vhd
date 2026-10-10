-------------------------------------------------------------------------------------
--Description:	DecodeJAL
--
--       File:	DecodeJALSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose: Define the instruction Decode logic for the JAL instruction
--
--     Inputs:  Instruction : instruction to be decoded
--
--	  Outputs:	 CtrlSgnls  : control signals
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


ENTITY Decode_JAL IS
	PORT(	Instruction	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			CtrlSgnls	:	OUT		CTRL_SIGNL_REC);
END ENTITY;


ARCHITECTURE Behavioral OF Decode_JAL IS
	SIGNAL IR : J_INSTRUCTION;
	
	BEGIN
		PROCESS(Instruction)
			BEGIN
				IR <= IR_to_Jtype(Instruction);
			
				IF(IR.J_OPCODE = CPU_JAL_OPCODE) THEN    			--  JAL instruction ?
				
																	--  yes, an JAL instruction
					CtrlSgnls.ALU_func		<=	ALU_FUNC_ADD;		--  ALU function code
					CtrlSgnls.ALU_Asel		<=  ALU_ASEL_AOUT;		--	ALU A input source select
					CtrlSgnls.ALU_Ssel		<=  ALU_SSEL_FLOAT;		--	ALU shift input source select
					CtrlSgnls.DM_strb		<=  DM_STRB_HOLD;		--	Data memory strobe
					CtrlSgnls.DM_rw			<=	DM_RW_FLOAT;		--	Data memory read/write                
					CtrlSgnls.DM_en			<=	DM_EN_DISABLE;		--	Data memory enable
					CtrlSgnls.RN_size		<=	RN_SIZE_FLOAT;		--	Rat's nest transfer size
					CtrlSgnls.NIAG_sel		<=	NIAG_SEL_ABS;		--  next instruction select
					CtrlSgnls.NIAG_strb		<=	NIAG_STRB_STROBE;	--	next instruction strobe
					CtrlSgnls.NIAG_cond		<=  NIAG_COND_NONE;		--	next instruction condition code
					CtrlSgnls.IR_Xsel		<=	IR_XSEL_FLOAT;		--  IR immediate field extend method select
					CtrlSgnls.IR_Xlsft		<=	IR_XLSFT_FLOAT;		--  IR immediate field left shift method
					CtrlSgnls.IR_strb		<=	IR_STRB_STROBE;		--	Instruction Register strobe
					CtrlSgnls.RF_Dsel		<=	RF_DSEL_RET;		--	Register file data input select
					CtrlSgnls.RF_strb		<=	RF_STRB_strobe;		--	Register file strobe
					CtrlSgnls.RF_Wsel		<=	RF_DSEL_RET;		--	Register file write destination select
					CtrlSgnls.RF_oe			<=	RF_OE_HiZ;			--	Register file output enable
				ELSE
					CtrlSgnls <= CtrlSgnls_Float;					--  no, not JAL instruction
				END IF;
			END PROCESS;
END ARCHITECTURE;
