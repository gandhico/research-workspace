
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;


ENTITY Decode_BGEZ IS
	PORT(	Instruction	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			CtrlSgnls	:	OUT	CTRL_SIGNL_REC);
END ENTITY;


ARCHITECTURE Behavioral OF Decode_BGEZ IS
	SIGNAL IR : I_INSTRUCTION;
	
	BEGIN
		PROCESS(Instruction,IR)
			BEGIN
				IR <= IR_to_Itype(Instruction);
			
				IF((IR.I_OPCODE = CPU_BGEZ_OPCODE) AND   						
					(IR.I_RT = CPU_BGEZ_RT)) THEN
																				
					CtrlSgnls.ALU_func					<=	ALU_FUNC_SUB;		 
					CtrlSgnls.ALU_Asel					<= ALU_ASEL_AOUT;		 
					CtrlSgnls.ALU_Ssel					<= ALU_SSEL_FLOAT;	 
					CtrlSgnls.DM_strb					<= DM_STRB_HOLD;		 
					CtrlSgnls.DM_rw						<=	DM_RW_FLOAT;		                
					CtrlSgnls.DM_en						<=	DM_EN_DISABLE;		 		 
					CtrlSgnls.NIAG_sel					<=	NIAG_SEL_REL;		 
					CtrlSgnls.NIAG_strb					<=	NIAG_STRB_STROBE;	 
					CtrlSgnls.NIAG_cond					<= NIAG_COND_GEZ;		 
					CtrlSgnls.IR_Xsel					<=	IR_XSEL_SIGN;		 
					CtrlSgnls.IR_Xlsft					<=	IR_XLSFT_TWO;		 
					CtrlSgnls.IR_strb					<=	IR_STRB_STROBE;	 
					CtrlSgnls.RF_Dsel					<=	RF_DSEL_FLOAT;		 
					CtrlSgnls.RF_strb					<=	RF_STRB_HOLD;		 
					CtrlSgnls.RF_Wsel					<=	RF_WSEL_FLOAT;		 
					CtrlSgnls.RF_oe						<=	RF_OE_HiZ;			 
				ELSE
					CtrlSgnls <= CtrlSgnls_Float;									
				END IF;
			END PROCESS;
END ARCHITECTURE;
