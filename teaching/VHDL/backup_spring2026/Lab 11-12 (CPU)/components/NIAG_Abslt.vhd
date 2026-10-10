library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity NIAG_Abslt is
    port(
        Index     : in  STD_LOGIC_VECTOR(25 downto 0);
        NSA       : in  STD_LOGIC_VECTOR(31 downto 0);
        AbsltAdrs : out STD_LOGIC_VECTOR(31 downto 0)
    );
end NIAG_Abslt;

architecture rtl of NIAG_Abslt is
begin
    AbsltAdrs <= NSA(31 downto 28) & Index & "00";
end rtl;
