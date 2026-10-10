--------------------------------------------------------------------------------
-- EE 362 - Lab 8 REFERENCE SOLUTION  (TA only - do not publish)
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
