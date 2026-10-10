--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 7 reference component
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
