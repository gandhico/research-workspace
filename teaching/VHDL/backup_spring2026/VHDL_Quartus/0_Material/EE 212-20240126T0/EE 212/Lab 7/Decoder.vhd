Library IEEE;
use IEEE.std_logic_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

use IEEE.NUMERIC_STD.All;

ENTITY Decoder is

PORT(		Instruction		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			CtrlSgnls		:	OUT		CTRL_SIGNL_REC	
    );
		 
END ENTITY;

ARCHITECTURE behavioral of Decoder is

begin

	Decoder_ADD: Decode_ADD Port MAP(instruction, ctrlsgnls);
	Decoder_LW: Decode_LW Port MAP(instruction, ctrlsgnls);
	Decoder_MTLO: Decode_MTLO Port MAP(instruction, ctrlsgnls);
	Decoder_BGEZ: Decode_BGEZ Port MAP(instruction, ctrlsgnls);
	Decoder_ADDU: Decode_ADDU Port MAP(instruction, ctrlsgnls);
	Decoder_SLLV: Decode_SLLV Port MAP(instruction, ctrlsgnls);
	Decoder_ANDI: Decode_ANDI Port MAP(instruction, ctrlsgnls);
	

	
END Architecture;