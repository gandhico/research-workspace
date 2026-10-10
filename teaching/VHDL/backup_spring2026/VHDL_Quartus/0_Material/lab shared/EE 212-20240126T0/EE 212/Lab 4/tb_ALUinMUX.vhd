Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_ALUinMUX IS

End Entity;

Architecture tb of tb_ALUinMUX is

SIGNAL Aout		: 	STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL Immed   :  STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL Sel		:  STD_LOGIC;
SIGNAL Data		:  STD_LOGIC_VECTOR(31 Downto 0);

begin

	dut: ALUinMUX PORT MAP
	(
	Aout   => Aout,
	Immed  => Immed,
	Sel    => Sel,
	Data   => Data);
	
	Process
	
	Begin
	
	wait for 10 ns;
	
	Aout    <= x"AAAAAAAA";
	Immed   <= x"BBBBBBBB";
	
	Sel <= '0';
	
	wait for 10 ns;
	
	Sel <= '1';
	
	wait;
	
	End Process;
	

End Architecture;