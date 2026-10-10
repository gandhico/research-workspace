Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity ALUinMUX IS															--  ALU A-input select													--  
		PORT(	Aout		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register file A output value
				Immed		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    IR immediate field
				Sel		:	IN			STD_LOGIC;								--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus
END Entity;

Architecture Behavioral of ALUinMUX is

begin

	Data <= Aout  when Sel = ALU_ASEL_AOUT else
			  Immed when Sel = ALU_ASEL_IMMED else
			  (Others => 'Z');


End Architecture;