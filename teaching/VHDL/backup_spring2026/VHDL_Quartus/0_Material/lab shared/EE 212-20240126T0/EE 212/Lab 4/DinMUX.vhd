Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity DinMUX IS																--  Register file data input mux
		PORT(	ALUresult	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    ALU result value
				MemData		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Memory data value
				RetAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Function call return addrress
				Sel			:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);			--    Input selection bus
				Data			:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus

END Entity;

Architecture Behavioral of DinMUX is

begin

	Data <= ALUResult when Sel = RF_DSEL_ALU else
			  MemData   when Sel = RF_DSEL_MEM else
			  RetAdrs   when Sel = RF_DSEL_RET else
			  (Others => 'Z');


End Architecture;