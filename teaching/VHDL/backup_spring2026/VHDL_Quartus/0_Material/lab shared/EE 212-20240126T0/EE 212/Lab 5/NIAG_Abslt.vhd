Library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_212_NIAG;
use EE_212_NIAG.NIAG_Pkg.all;

LIBRARY EE_212_DECODER;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;


ENTITY NIAG_Abslt is

PORT(	Index		 	:	IN	STD_LOGIC_VECTOR(25 DOWNTO 0);				--    IR index field
		NSA			:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
		AbsltAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));			--    Absolute address output
	
END ENTITY;

ARCHITECTURE Behavioral of NIAG_Abslt is

BEGIN

		AbsltAdrs <= NSA (31 Downto 28) & Index & "00";



END ARCHITECTURE;