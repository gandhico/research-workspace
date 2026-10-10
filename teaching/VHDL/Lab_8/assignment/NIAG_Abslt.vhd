--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - Assignment, Part 1 of 4
--
-- NIAG_Abslt : absolute jump target formation
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION
--
--   Abslt = NSA(31 downto 28) & Index(25 downto 0) & "00"
--           \______________/   \_________________/   \__/
--            4 bits INHERITED   26 bits ENCODED      2 bits ALWAYS ZERO
--
--   4 + 26 + 2 = 32.
--
-- PURE WIRING. No arithmetic, no adder, no logic. One concatenation.
--
-- WORKED EXAMPLE - the real J from the Lab 12 program
--
--   0x14   0x08000002   J 0x08
--
--     index = 0x0000002
--     NSA   = 0x14 + 4 = 0x18,  top 4 bits = 0x0
--     Abslt = 0x0 & 0x0000002 & "00" = 0x00000008
--
--   0x08 is the ADDI at the top of the loop. This jump is what makes the loop
--   a loop.
--
-- THE CONSEQUENCE WORTH UNDERSTANDING
--   The top four bits are INHERITED, not encoded. So a jump cannot leave its
--   2^28 byte = 256 MB region. That is not a bug - it is what you get for
--   spending 26 bits instead of 32. To reach further you need JR, which takes
--   a full 32-bit address out of a register.
--
--   Your report must state this trade-off in your own words.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity NIAG_Abslt is
    port (
        NSA   : in  std_logic_vector(31 downto 0);   -- PC + 4
        Index : in  std_logic_vector(25 downto 0);   -- IR index field
        Abslt : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Abslt;

architecture rtl of NIAG_Abslt is
begin

    -- TODO: one line. Three pieces, concatenated with '&'.
    --       Get the slice right: which four bits of NSA, and in what order?

end architecture rtl;
