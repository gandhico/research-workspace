Library IEEE;
use IEEE.STD_LOGIC_1164.all;

LIBRARY EE_212_DECODER;

use EE_212_DECODER.DecodeLogic_pkg.all;

Library EE_212_MISC;
use EE_212_MISC.MISC_pkg.all;

Entity tb_DinMUX IS

End Entity;

Architecture tb of tb_DinMUx is

SIGNAL ALUresult: STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL MEmData:   STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL RetADRS:   STD_LOGIC_VECTOR(31 Downto 0);
SIGNAL Sel:       STD_LOGIC_VECTOR(1  Downto 0);
SIGNAL Data:      STD_LOGIC_VECTOR(31 Downto 0);

begin

	dut: DinMUX PORT MAP
	(
	ALUresult => ALUresult,
	MemData   => MemData,
	RetAdrs   => RetAdrs,
	Sel       => Sel,
	Data      => Data);
	
	Process
	
	Begin
	
	wait for 10 ns;
	
	ALUresult <= x"AAAAAAAA";
	MemData   <= x"BBBBBBBB";
	RetAdrs   <= x"CCCCCCCC";
	
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