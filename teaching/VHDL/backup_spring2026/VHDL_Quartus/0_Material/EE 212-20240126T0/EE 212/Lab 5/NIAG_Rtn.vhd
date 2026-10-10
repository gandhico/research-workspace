Library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_212_NIAG;
use EE_212_NIAG.NIAG_Pkg.all;

LIBRARY EE_212_DECODER;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;


ENTITY NIAG_Rtn is

	PORT(		PC			:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Program counter output
				RtnAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Return address output
	
END ENTITY;

ARCHITECTURE Behavioral of NIAG_Rtn is

BEGIN


		RtnAdrs <= STD_LOGIC_VECTOR(UNSIGNED(PC) + 8);



END ARCHITECTURE;