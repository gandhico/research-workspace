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
-- NIAG_Rel : Rel = NSA + Xtnd32.
-- Xtnd32 arrives already sign-extended and already shifted left by 2, from the
-- shared ImmedXtnd. Two's complement addition handles negative offsets with no
-- special case.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity NIAG_Rel is
    port (
        NSA    : in  std_logic_vector(31 downto 0);
        Xtnd32 : in  std_logic_vector(31 downto 0);
        Rel    : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Rel;

architecture rtl of NIAG_Rel is
begin
    Rel <= std_logic_vector(unsigned(NSA) + unsigned(Xtnd32));
end architecture rtl;
