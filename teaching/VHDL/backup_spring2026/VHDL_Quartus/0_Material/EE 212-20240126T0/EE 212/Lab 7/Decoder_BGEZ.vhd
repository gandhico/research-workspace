Library IEEE;
use IEEE.std_logic_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;							

use IEEE.NUMERIC_STD.All;

ENTITY Decoder_BGEZ is

PORT(		Instruction				:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				CtrlSgnls			:	OUT		CTRL_SIGNL_REC
    );
		 
END ENTITY;

ARCHITECTURE behavioral of Decoder_BGEZ is

SIGNAL IR : I_instruction;

begin

	process(IR, Instruction)
		begin
			IR <= IR_to_Itype(Instruction);
				
			if(IR.I_OPCODE = CPU_bgez_OPCODE) then
		
			CTRlsgnls.ALU_func	  	<= alu_func_float;
			CTRlsgnls.ALU_Asel	  	<= alu_asel_aout;
			CTRlsgnls.ALU_Ssel	  	<= alu_ssel_float;
			CTRlsgnls.DM_strb	  		<= dm_strb_float;
			CTRlsgnls.DM_rw		  	<= dm_rw_float;
			CTRlsgnls.DM_en		  	<= dm_en_disable;
			CTRlsgnls.NIAG_sel	  	<= niag_sel_rel;
			CTRlsgnls.NIAG_strb  	<= niag_strb_strobe;
			CTRlsgnls.NIAG_cond  	<= niag_cond_gez;
			CTRlsgnls.IR_Xsel	  		<= ir_xsel_sign;
			CTRlsgnls.IR_Xlsft	  	<= ir_xlsft_two;
			CTRlsgnls.IR_strb	  		<= ir_strb_strobe;
			CTRlsgnls.RF_Dsel	  		<= rf_dsel_float;
			CTRlsgnls.RF_strb	  		<= rf_strb_strobe;
			CTRlsgnls.RF_Wsel	  		<= rf_wsel_float;
			CTRlsgnls.RF_oe		  	<= rf_oe_hiz;
		else
			ctrlsgnls <= ctrlsgnls_float;
			
		end if;
		
		
		end process;
	
	
END Architecture;