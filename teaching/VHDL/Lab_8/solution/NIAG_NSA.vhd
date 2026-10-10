--------------------------------------------------------------------------------
-- EE 362 - Lab 7 REFERENCE SOLUTION  (TA only - do not publish)
-- NIAG_NSA : NSA = PC + 4.  Combinational: needed during the cycle.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity NIAG_NSA is
    port (
        PC  : in  std_logic_vector(31 downto 0);
        NSA : out std_logic_vector(31 downto 0)
    );
end entity NIAG_NSA;

architecture rtl of NIAG_NSA is
begin
    NSA <= std_logic_vector(unsigned(PC) + 4);
end architecture rtl;
