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
-- EE 362 - Lab 8 reference component
-- NIAG_Abslt : Abslt = NSA(31..28) & Index & "00".  Pure wiring, no arithmetic.
-- The inherited top 4 bits are why a jump cannot leave its 256 MB region.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity NIAG_Abslt is
    port (
        NSA   : in  std_logic_vector(31 downto 0);
        Index : in  std_logic_vector(25 downto 0);
        Abslt : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Abslt;

architecture rtl of NIAG_Abslt is
begin
    Abslt <= NSA(31 downto 28) & Index & "00";
end architecture rtl;
