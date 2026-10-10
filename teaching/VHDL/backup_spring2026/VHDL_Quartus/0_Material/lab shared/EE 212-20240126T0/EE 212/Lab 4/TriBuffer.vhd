Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity TriBuffer IS															--  Tri-state buffer 

		PORT(	Sel		:	IN			STD_LOGIC;								--    Enable
				Aout		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register file B output
				DataBus	:	INOUT		STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus

END Entity;

Architecture Behavioral of TriBuffer is

begin

	DataBus <= Aout when Sel = RF_OE_DRIVE Else
	(OTHERS => 'Z');
	


End Architecture;
