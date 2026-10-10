Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity DselMUX IS															--  Register file write select															--  
		PORT(	RD			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR RD field
				RT			:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    IR RT field
				RET		:	IN			STD_LOGIC_VECTOR(4 DOWNTO 0);			--    function call return register (1F) 
				Sel		:	IN			STD_LOGIC_VECTOR(1 DOWNTO 0);			--    Input selection bus
				Data		:	OUT			STD_LOGIC_VECTOR(4 DOWNTO 0));			--    Data output bus
END Entity;

Architecture Behavioral of DselMUX is

begin

	Data <= RD  when Sel = RF_WSEL_RD else
			  RT  when Sel = RF_WSEL_RT else
			  RET when Sel = RF_WSEL_RET else
			  (Others => 'Z');


End Architecture;