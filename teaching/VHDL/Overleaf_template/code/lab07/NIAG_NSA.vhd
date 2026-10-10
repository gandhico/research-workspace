-- PLACEHOLDER: replace with YOUR OWN NIAG_NSA.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7 - Assignment, Part 1 of 3
--
-- NIAG_NSA : Next Sequential Address = PC + 4
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- The smallest component in the whole CPU, and one of the most used. Every
-- instruction needs it: sequential execution takes it directly, branches use
-- it as their BASE, and JAL saves it as the return address.
--
-- SPECIFICATION
--   NSA = PC + 4
--
-- WHY 4 AND NOT 1
--   Addresses count BYTES. Instructions are 32 bits = 4 bytes. So the next
--   instruction lives 4 addresses along, not 1.
--
--   This is also why instruction addresses are always multiples of 4, which is
--   the fact that makes the branch offset shift work (Part 3).
--
-- COMBINATIONAL, not clocked. NSA must be available DURING the cycle - the
-- branch logic needs it as a base, and the PC needs it as a candidate next
-- value, both before the clock edge that ends the cycle.
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

    -- TODO: one line. Remember to convert, add, and convert back.

end architecture rtl;
