--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8, Example 1 - Absolute jump target formation
--
-- A jump instruction carries a 26-bit index. The PC is 32 bits. Six bits have
-- to come from somewhere, and where they come from is an architectural
-- decision with a visible consequence.
--
--   Abslt = NSA(31 downto 28) & index(25 downto 0) & "00"
--           \______________/   \_________________/   \__/
--            4 bits INHERITED   26 bits ENCODED      2 bits ALWAYS ZERO
--                from PC+4        in the instruction   (word alignment)
--
-- 4 + 26 + 2 = 32.
--
-- THE REAL INSTRUCTION, from the Lab 12 program:
--
--   address  encoding     instruction
--   0x14     0x08000002   J 0x08
--
--     opcode  = 000010 = J
--     index   = 0x0000002
--     NSA     = 0x14 + 4 = 0x18
--     top 4   = 0x18(31..28) = 0x0
--     Abslt   = 0x0 & 0x0000002 & "00" = 0x00000008
--
--   0x08 is the ADDI at the top of the loop. This jump is what makes it a loop.
--
-- WHY THE LOW TWO BITS ARE "00"
--   Same reason as the branch offset shift in Lab 7: instructions are
--   word-aligned, so their low two bits are always zero. Not encoding them buys
--   four times the reach for free.
--
-- WHY THE TOP FOUR BITS ARE INHERITED
--   There is no room for them. 26 bits of index plus 2 implied zeros reaches
--   2^28 bytes = 256 MB. Anything beyond that has to come from where you
--   already are.
--
--   CONSEQUENCE: a jump cannot leave its 256 MB region. That is not a bug and
--   not an oversight - it is what you get for spending 26 bits instead of 32.
--   To go further you need JR, which takes a full 32-bit address from a
--   register. This is a real trade-off, visible in one line of concatenation.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity absolute_target is
    port (
        NSA   : in  std_logic_vector(31 downto 0);   -- PC + 4
        Index : in  std_logic_vector(25 downto 0);   -- IR index field
        Abslt : out std_logic_vector(31 downto 0)
    );
end entity absolute_target;

architecture rtl of absolute_target is
begin

    -- Three pieces, concatenated. No arithmetic at all - this is pure wiring.
    Abslt <= NSA(31 downto 28) & Index & "00";

end architecture rtl;
