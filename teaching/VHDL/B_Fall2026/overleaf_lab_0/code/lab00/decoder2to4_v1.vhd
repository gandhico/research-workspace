--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 3 - FIRST VERSION (contains the bug discussed)
-- E is declared in the entity but never read by the architecture.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4 is
    port ( E  : in  std_logic;
           A1 : in  std_logic;
           A0 : in  std_logic;
           D  : out std_logic_vector(3 downto 0) );
end entity decoder2to4;

architecture behavioral of decoder2to4 is
    signal A : std_logic_vector(1 downto 0);
begin
    A <= A1 & A0;

    with A select
        D <= "0001" when "00",
             "0010" when "01",
             "0100" when "10",
             "1000" when "11",
             "0000" when others;
end architecture behavioral;
