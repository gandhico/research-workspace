Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Entity PCMUX IS																--  Program counter selection bus
		PORT(	NxtAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Next sequential address
				RelAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Relative address
				RegAdrs		:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Register address
				AbsltAdrs	:	IN			STD_LOGIC_VECTOR(31 DOWNTO 0);			--    Absolute address
				Sel			:	IN			STD_LOGIC_VECTOR(1  DOWNTO 0);			--    Input selection bus
				Data			:	OUT		STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Data output bus

END Entity;

Architecture Behavioral of PCMUX is

begin

	Data <= NxtAdrs when Sel = NIAG_SEL_NSA else
			  RelAdrs   when Sel = NIAG_SEL_REL else
			  RegAdrs   when Sel = NIAG_SEL_REG else
			  AbsltAdrs   when Sel = NIAG_SEL_ABS else
			  (Others => 'Z');


End Architecture;