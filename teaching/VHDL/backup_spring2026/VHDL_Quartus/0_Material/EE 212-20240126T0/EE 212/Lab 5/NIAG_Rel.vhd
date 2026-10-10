Library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_212_NIAG;
use EE_212_NIAG.NIAG_Pkg.all;

LIBRARY EE_212_DECODER;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;


ENTITY NIAG_Rel is

PORT(		Immed 	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);				--    IR immediate field
			Xshft		:	IN		STD_LOGIC;											--    16 to 32 extender selection
			NSA		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
			RelAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Relative address output
	
END ENTITY;

ARCHITECTURE Behavioral of NIAG_Rel is

SIGNAL Intrm : STD_LOGIC_VECTOR(31 downto 0);

BEGIN

	Process(Immed, Xshft, Intrm, NSA) is
		begin

		IF(Xshft = '1') then
		
		Intrm <= Immed(29 Downto 0) & "00";
			
		else
		
		Intrm <= Immed;

		end if;

		RelAdrs <= std_logic_vector(unsigned(Intrm) + unsigned(NSA));
		
		end process;
		
END ARCHITECTURE;