-------------------------------------------------------------------------------------
--Description:	CPU
--
--       File:	CpuSolution.vhd
--	
--    Project:	LabCPU
--
--     Author:	A.K. Petersen
--
--    Purpose:  Define a 32-bit Central Proccessing Unit
--
--     Inputs:  CLK: system master clock
--
--    Outputs:  None
--
--  Copyright 2021 by A.K. Petersen, New Mexico State University, all rights reserved
--
-------------------------------------------------------------------------------------
 
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;


library EE_362_ALU;
USE EE_362_ALU.ALU_Pkg.all;

library EE_362_Decoder;
use EE_362_Decoder.DecodeLogic_Pkg.all;

library EE_362_Memory;
use EE_362_Memory.Memory_Pkg.all;

library EE_362_MISC;
use EE_362_MISC.MISC_Pkg.all;

library EE_362_NIAG;
USE EE_362_NIAG.NIAG_Pkg.all;

library EE_362_RegFile;
use EE_362_RegFile.RegFile_Pkg.all;

library EE_362_CPU;
use EE_362_CPU.LabCPU_Pkg.all;

ENTITY CPU IS
	PORT(	Clk	:	IN		STD_LOGIC);
END ENTITY;

ARCHITECTURE Behavioral OF CPU IS
	SIGNAL	IRout		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- instruction register
	SIGNAL 	PCout		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Program counter
	SIGNAL 	CtrlSgnls	:	CTRL_SIGNL_REC;					-- control signals
	SIGNAL 	IMout		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Instruction memory output
	SIGNAL 	NIAGout		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Instruction address output
	SIGNAL 	XtndrOut	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Immediate extender output
	SIGNAL 	Rtype		:	R_INSTRUCTION;					-- R type instruction fields
	SIGNAL 	Jtype		:	J_INSTRUCTION;					-- J type instruction fields
	SIGNAL 	Itype		:	I_INSTRUCTION;					-- I type instruction fields
	SIGNAL 	RTNadrs		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Return address
	SIGNAL	DselMUXout	:	STD_LOGIC_VECTOR(4   DOWNTO 0);	-- Data destination select MUX output
	SIGNAL	ALUinMUXout	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- ALU input select MUX output
	SIGNAL	DinMUXout	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Data input select MUX output
	SIGNAL	RegFileAout	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Register file A output
	SIGNAL	RegFileBout	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Register file B output
	SIGNAL	ALUout		:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Arithmetic/Logical Unit output
	SIGNAL	ALUsftMUXout:	STD_LOGIC_VECTOR(4   DOWNTO 0);	-- ALU shift MUX output
	SIGNAL	ALUstatCodes:	STAT_SIGNL_REC;					-- ALU condition codes
	SIGNAL	RatsNestOut	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Rat's Nest output toward tri-state buffer
	SIGNAL	DataMemData	:	STD_LOGIC_VECTOR(31  DOWNTO 0);	-- Data memory data port
	
	BEGIN
		Rtype <= IR_to_Rtype(IRout);						-- cast instruction as all three types
		Itype <= IR_to_Itype(IRout);
		Jtype <= IR_to_Jtype(IRout);

		Component00 : Decoder	PORT MAP(IRout, CtrlSgnls);
		Component01 : RegFile	PORT MAP(Rtype.R_RT, Rtype.R_RS, DselMUXout, DinMUXout, clk, RegFileAout, RegFileBout);
		Component02 : RatsNest	PORT MAP(CtrlSgnls.DM_rw, CtrlSgnls.RN_Size, RatsNestOut, DataMemData);
		Component03	: NIAG		PORT MAP(Jtype.J_INDEX, XtndrOut, RegFileBout, CtrlSgnls.IR_Xlsft, PCout, CtrlSgnls.NIAG_cond,
										 CtrlSgnls.NIAG_sel, ALUstatCodes, NIAGout, RTNadrs);
		Component04 : ALU		PORT MAP(ALUinMUXout, RegFileBout, CtrlSgnls.ALU_func, ALUsftMUXout, ALUout, ALUstatCodes);
		Component05 : ROM		PORT MAP(PCout, IRout);
		Component06 : RAM		PORT MAP(ALUout, CtrlSgnls.DM_strb, CtrlSgnls.DM_rw, CtrlSgnls.DM_en, DataMemData);
		Component07	: ALUinMUX	PORT MAP(ALUout, XtndrOut, CtrlSgnls.ALU_Asel, ALUinMUXout);
		Component08 : ImmedXtnd	PORT MAP(Itype.I_IMMED, CtrlSgnls.IR_Xlsft, XtndrOut);
		Component09	: DselMUX	PORT MAP(Rtype.R_RD, Rtype.R_RT, RF_REG_1F, CtrlSgnls.RF_Wsel, DselMUXout);
		Component0A : DinMUX	PORT MAP(ALUout, RatsNestOut, RTNadrs, CtrlSgnls.RF_Dsel, DinMUXout);
		Component0B	: ALUsftMUX	PORT MAP(Rtype.R_RS, RegFileBout(4 DOWNTO 0), CtrlSgnls.ALU_Ssel, ALUsftMUXout);
		Component0C	: TriBuffer	PORT MAP(CtrlSgnls.RF_oe, RegFileBout, RatsNestOut);

		PROCESS (Clk) IS									-- stuff to do on a rising edge of Clk
		BEGIN
			IF rising_edge(Clk) THEN						-- load program counter
				IF CtrlSgnls.NIAG_strb = NIAG_STRB_STROBE THEN
					PCout <= NIAGout;
				END IF;
			END IF;
		END PROCESS;		
END ARCHITECTURE;
