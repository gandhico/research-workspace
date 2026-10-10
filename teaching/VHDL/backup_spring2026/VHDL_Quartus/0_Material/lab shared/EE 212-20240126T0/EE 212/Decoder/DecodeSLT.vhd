library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;


ENTITY Decode_SLT IS
	PORT(	Instruction	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			CtrlSgnls	:	OUT	CTRL_SIGNL_REC);
END ENTITY;


ARCHITECTURE Behavioral OF Decode_SLT IS
	SIGNAL IR : R_INSTRUCTION;
	
	BEGIN
		PROCESS(Instruction,IR)
			BEGIN
				IR <= IR_to_Rtype(Instruction);
				
				IF((IR.R_OPCODE = CPU_SLT_OPCODE) AND   						
				   (IR.R_FUNC   = CPU_SLT_FUNC)) THEN
																				
					CtrlSgnls.ALU_func					<=	ALU_FUNC_SOLS;		 
					CtrlSgnls.ALU_Asel					<= ALU_ASEL_AOUT;		 
					CtrlSgnls.ALU_Ssel					<= ALU_SSEL_FLOAT;	 
					CtrlSgnls.DM_strb					<= DM_STRB_HOLD;		 
					CtrlSgnls.DM_rw						<=	DM_RW_FLOAT;		                
					CtrlSgnls.DM_en						<=	DM_EN_DISABLE;		 	 
					CtrlSgnls.NIAG_sel					<=	NIAG_SEL_NSA;		 
					CtrlSgnls.NIAG_strb					<=	NIAG_STRB_STROBE;	 
					CtrlSgnls.NIAG_cond					<= NIAG_COND_NONE;	 
					CtrlSgnls.IR_Xsel					<=	IR_XSEL_FLOAT;		 
					CtrlSgnls.IR_Xlsft					<=	IR_XLSFT_FLOAT;	 
					CtrlSgnls.IR_strb					<=	IR_STRB_STROBE;	 
					CtrlSgnls.RF_Dsel					<=	RF_DSEL_ALU;		 
					CtrlSgnls.RF_strb					<=	RF_STRB_STROBE;	 
					CtrlSgnls.RF_Wsel					<=	RF_WSEL_RD;			 
					CtrlSgnls.RF_oe						<=	RF_OE_FLOAT;		 
				ELSE
					CtrlSgnls <= CtrlSgnls_Float;									
				END IF;
			END PROCESS;
END ARCHITECTURE;
