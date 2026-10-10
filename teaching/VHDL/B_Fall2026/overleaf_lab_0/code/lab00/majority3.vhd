--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 1
-- majority3 : Y = '1' when at least two of A, B, C are '1'
--
--   Y = AB + AC + BC
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity majority3 is
    port ( A : in  std_logic;
           B : in  std_logic;
           C : in  std_logic;
           Y : out std_logic );
end entity majority3;

architecture behavioral of majority3 is
begin
    Y <= (A and B) or (A and C) or (B and C);
end architecture behavioral;
