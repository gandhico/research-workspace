library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity TriBuffer is
    port(
        En   : in  STD_LOGIC;
        Din  : in  STD_LOGIC_VECTOR(31 downto 0);
        Dout : out STD_LOGIC_VECTOR(31 downto 0)
    );
end TriBuffer;

architecture Behavioral of TriBuffer is
begin
    Dout <= Din when En = '1' else (others => 'Z');
end Behavioral;
