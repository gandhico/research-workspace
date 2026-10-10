--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4, Example 2 - Sign extension vs zero extension, side by side
--
-- Widening a number is not one operation. It is two, and which one you want
-- depends on what the bits MEAN.
--
--   ZERO extension : pad the top with '0'. The value is unsigned.
--                    0x8 (4 bits) -> 0x08 = 8
--
--   SIGN extension : pad the top with a COPY OF THE TOP BIT. The value is
--                    two's complement, and its sign must survive.
--                    0x8 (4 bits) = -8 -> 0xF8 = -8   (still -8)
--
-- Both take the same input and produce different answers. Neither is "more
-- correct" - the instruction decides which one is wanted.
--
-- WHY THIS MATTERS IN THE CPU (Labs 10-11)
--   ADDI sign-extends: its immediate is a signed offset, and ADDI r1,r1,-1
--   must actually subtract one.
--   LUI zero-extends in this CPU: its immediate is a bit pattern, not a number.
--   Get this wrong and your CPU's loop counter counts the wrong way.
--
-- THE VHDL: bit replication with an aggregate
--   (others => I(3))  means "every remaining element gets a copy of bit 3".
--   It works at any width without being rewritten, which is why we use it
--   instead of writing I(3) & I(3) & I(3) & I(3) by hand.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity extend_demo is
    port (
        I     : in  std_logic_vector(3 downto 0);   -- 4-bit input
        Yzero : out std_logic_vector(7 downto 0);   -- zero-extended to 8
        Ysign : out std_logic_vector(7 downto 0)    -- sign-extended to 8
    );
end entity extend_demo;

architecture rtl of extend_demo is
begin

    -- Zero extension: the top four bits are always '0'.
    --   Y_i = 0            for i = 4..7
    --   Y_i = I_i          for i = 0..3
    Yzero <= (7 downto 4 => '0') & I;

    -- Sign extension: the top four bits are copies of I(3), the sign bit.
    --   Y_i = I_3          for i = 4..7
    --   Y_i = I_i          for i = 0..3
    Ysign <= (7 downto 4 => I(3)) & I;

end architecture rtl;
