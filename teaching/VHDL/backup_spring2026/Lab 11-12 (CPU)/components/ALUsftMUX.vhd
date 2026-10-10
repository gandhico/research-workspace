library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity ALUsftMUX is
    port(
        Sel : in  STD_LOGIC;
        In0 : in  STD_LOGIC_VECTOR(4 downto 0);
        In1 : in  STD_LOGIC_VECTOR(4 downto 0);
        Y   : out STD_LOGIC_VECTOR(4 downto 0)
    );
end ALUsftMUX;

architecture Behavioral of ALUsftMUX is
begin
    Y <= In0 when Sel = '0' else In1;
end Behavioral;
