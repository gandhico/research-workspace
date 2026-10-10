library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity NIAG_Rel is
    port(
        Immed   : in  STD_LOGIC_VECTOR(31 downto 0);
        Xshft   : in  STD_LOGIC;
        NSA     : in  STD_LOGIC_VECTOR(31 downto 0);
        RelAdrs : out STD_LOGIC_VECTOR(31 downto 0)
    );
end NIAG_Rel;

architecture rtl of NIAG_Rel is
    signal disp_s : STD_LOGIC_VECTOR(31 downto 0);
begin
    disp_s <= Immed(29 downto 0) & "00" when Xshft = '1' else Immed;
    RelAdrs <= STD_LOGIC_VECTOR(signed(NSA) + signed(disp_s));
end rtl;
