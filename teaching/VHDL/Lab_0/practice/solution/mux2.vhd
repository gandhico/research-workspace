--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice - shared component (from class Example 2)
-- mux2 : Y = S'.D0 + S.D1
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux2 is
    port ( D0, D1 : in  std_logic;
           S      : in  std_logic;
           Y      : out std_logic );
end entity mux2;

architecture behavioral of mux2 is
begin
    Y <= D0 when S = '0' else D1;
end architecture behavioral;
