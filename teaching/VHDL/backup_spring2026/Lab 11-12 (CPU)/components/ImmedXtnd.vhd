library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity ImmedXtnd is
    port(
        Sel   : in  STD_LOGIC;
        In16  : in  STD_LOGIC_VECTOR(15 downto 0);
        Out32 : out STD_LOGIC_VECTOR(31 downto 0)
    );
end ImmedXtnd;

architecture Behavioral of ImmedXtnd is
begin
    Out32 <= (31 downto 16 => '0') & In16 when Sel = '0' else
             (31 downto 16 => In16(15)) & In16;
end Behavioral;
