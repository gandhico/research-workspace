Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity ALUsftMUX IS															--  ALU shift selection mux
		PORT(	RS			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR rs field
				Bout		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    Register file B output
				Sel		:	IN			STD_LOGIC;								--    Input selection bus
				Data		:	OUT		STD_LOGIC_VECTOR(4 DOWNTO 0));			--    Data output bus

END Entity;

Architecture Behavioral of ALUsftMUX is

begin

	Data <= RS when Sel = ALU_SSEL_RS else
			  Bout when Sel = ALU_SSEL_BOUT else
			  (Others => 'Z');

End Architecture;