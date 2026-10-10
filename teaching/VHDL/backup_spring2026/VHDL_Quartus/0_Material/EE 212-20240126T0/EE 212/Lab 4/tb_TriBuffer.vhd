Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_TriBuffer IS

End Entity;

Architecture tb of tb_TriBuffer is

SIGNAL Sel       :  STD_LOGIC;
SIGNAL Aout		  :  STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL DataBus	  :  STD_LOGIC_VECTOR(31 Downto 0);

begin

	dut: TriBuffer PORT MAP
	(
	Sel       => Sel,
	Aout      => Aout,
	DataBus   => DataBus);
	
	Process
	
	Begin
	

		Aout<= X"FFFFFFFF";

		Sel <= DM_EN_ENABLE;

		wait for 10 ns;

		Sel <= DM_EN_DISABLE;
	
	wait;
	
	End Process;
	

End Architecture;