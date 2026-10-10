Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_ImmedXtnd IS

End Entity;

Architecture tb of tb_ImmedXtnd is

SIGNAL Immed16  : STD_LOGIC_VECTOR(15 Downto 0);
SIGNAL Sel		 : STD_LOGIC;
SIGNAL Immed32  : STD_LOGIC_VECTOR(31 Downto 0);

begin

	dut: ImmedXtnd PORT MAP
	(
	Immed16 => Immed16,
	Sel     => Sel,
	Immed32 => Immed32);
	
	Process
	
	Begin
	
	Immed16<=X"FF00";
	Sel<=IR_XSEL_SIGN;
	wait for 10 ns;

	Immed16<=X"FF00";
	Sel<=IR_XSEL_ZERO;
	wait for 10 ns;

	Immed16<=X"0FFF";
	Sel<=IR_XSEL_SIGN;
	wait for 10 ns;

	Immed16<=X"0FFF";
	Sel<=IR_XSEL_ZERO;
	wait for 10 ns;
	
	wait;
	
	End Process;
	

End Architecture;