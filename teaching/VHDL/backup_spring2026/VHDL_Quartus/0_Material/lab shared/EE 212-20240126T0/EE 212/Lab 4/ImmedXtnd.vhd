Library IEEE;
Library EE_212_MISC;
Library EE_212_Decoder;

use EE_212_MISC.MISC_Pkg.all;
use IEEE.STD_LOGIC_1164.all;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;

Entity ImmedXtnd is
	Port( Immed16   :  IN STD_LOGIC_VECTOR(15 Downto 0);
			Sel		 :  IN STD_LOGIC;
			Immed32   : OUT STD_LOGIC_VECTOR(31 downto 0 ));
			
End Entity;

Architecture synth of ImmedXtnd is

begin

	with Sel select Immed32 <= Std_Logic_Vector(resize(signed(immed16), Immed32'length)) when IR_XSEL_SIGN,
										Std_Logic_Vector(resize(unsigned(immed16), Immed32'length))	when IR_XSEL_ZERO,
										(others => 'Z') when others;
		
end architecture; 