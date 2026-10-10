Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_ALUsftMUX IS

End Entity;

Architecture tb of tb_ALUsftMUX is

SIGNAL RS		: 	STD_LOGIC_VECTOR(4 Downto 0);
SIGNAL Bout    :  STD_LOGIC_VECTOR(4 Downto 0);
SIGNAL Sel		:  STD_LOGIC;
SIGNAL Data		:  STD_LOGIC_VECTOR(4 Downto 0);

begin
 
	dut: ALUsftMUX PORT MAP
	(
	RS    => RS,
	Bout  => Bout,
	Sel   => Sel,
	Data  => Data);
	
	Process
	
	Begin
	
	wait for 10 ns;
	
	RS     <= "01010";
	Bout   <= "01011";
	
	Sel <= '0';
	
	wait for 10 ns;
	
	Sel <= '1';
	
	wait;
	
	End Process;
	

End Architecture;