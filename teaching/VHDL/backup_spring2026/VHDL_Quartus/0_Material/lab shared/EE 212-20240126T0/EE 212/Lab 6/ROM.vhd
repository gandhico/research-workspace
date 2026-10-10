
Library EE_212_Memory;
Use EE_212_Memory.Memory_pkg.all;

Library EE_212_Decoder;
Use EE_212_Decoder.DecodeLogic_pkg.all;

Library IEEE;
USE IEEE.STD_LOGIC_1164.all;
Use IEEE.NUMERIC_STD.all;

Entity ROM is

PORT( Addr : IN  STD_LOGIC_VECTOR(31 DOWNTO 0);
		Data : OUT STD_LOGIC_VECTOR(31 DOWNTO 0));

End Entity;

Architecture behavioral of ROM is 


signal ROM_Content: ROM_Memory := (			  0=>X"34",
											  1=>X"01",
											  2=>X"00",
											  3=>X"0F",
											  
											  4=>X"34",
											  5=>X"02",
											  6=>X"00",
											  7=>X"0A",
											  
											  8=>X"00",
											  9=>X"41",
											  10=>X"18",
											  11=>X"20",
											  
											  12=>X"AC",
											  13=>X"03",
											  14=>X"00",
											  15=>X"00",
											  
											  16=>X"8C",
											  17=>X"04",
											  18=>X"00",
											  19=>X"00",
											  others=>(others=>'0'));

BEGIN
	
				DATA(31 DOWNTO 24)<= ROM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+0));
				DATA(23 DOWNTO 16)<= ROM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+1));
				DATA(15 DOWNTO 8)<= ROM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+2));
				DATA(7 DOWNTO 0)<= ROM_CONTENT(TO_INTEGER(UNSIGNED(Addr)+3));
		
END Architecture;