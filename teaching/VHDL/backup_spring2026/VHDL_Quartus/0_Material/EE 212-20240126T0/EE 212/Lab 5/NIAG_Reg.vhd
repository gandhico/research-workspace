Library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_212_NIAG;
use EE_212_NIAG.NIAG_Pkg.all;

LIBRARY EE_212_DECODER;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;


ENTITY NIAG_Reg is

PORT(		Reg	 		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Register file B output
			RegAdrs		:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));				--    Register address output
	

END ENTITY;

ARCHITECTURE Behavioral of NIAG_Reg is

BEGIN

	RegAdrs <= Reg;

END ARCHITECTURE;