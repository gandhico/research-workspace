Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_DselMUX IS

End Entity;

Architecture tb of tb_DselMUx is

SIGNAL RD   :   STD_LOGIC_VECTOR(4 Downto 0);
SIGNAL RT   :   STD_LOGIC_VECTOR(4 Downto 0);
SIGNAL RET  :   STD_LOGIC_VECTOR(4 Downto 0);
SIGNAL Sel  :   STD_LOGIC_VECTOR(1 Downto 0);
SIGNAL Data :   STD_LOGIC_VECTOR(4 Downto 0);

begin

	dut: DselMUX PORT MAP
	(
	RD   => RD,
	RT   => RT,
	RET  => RET,
	Sel  => Sel,
	Data => Data);
	
	Process
	
	Begin
	
	wait for 10 ns;
	
	RD   <= "01010";
	RT   <= "01011";
	RET  <= "01100";
	
	Sel <= "00";
	
	wait for 10 ns;
	
	Sel <= "01";
	
	wait for 10 ns;
	
	Sel <= "10";
	
	wait for 10 ns;
	
	Sel <= "11";
	
	wait;
	
	End Process;
	

End Architecture;