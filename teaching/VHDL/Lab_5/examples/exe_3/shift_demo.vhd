--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5, Example 3 - The three shifts, and the one everybody gets wrong
--
-- SHIFT LEFT (SLL) - vacated bits on the RIGHT are filled with '0'.
--   There is only one sensible answer, so "logical" and "arithmetic" left
--   shifts are the same operation. SLA and SLL are identical.
--
-- SHIFT RIGHT LOGICAL (SRL) - vacated bits on the LEFT are filled with '0'.
--   Correct when the value is UNSIGNED.
--
-- SHIFT RIGHT ARITHMETIC (SRA) - vacated bits on the left are filled with
--   COPIES OF THE SIGN BIT. Correct when the value is SIGNED.
--
-- WHY SRA EXISTS
--   Shifting right by one should divide by two. Take -8 = 0xFFFFFFF8:
--
--     SRL by 1 -> 0x7FFFFFFC = +2147483644     ... -8 / 2 is not two billion
--     SRA by 1 -> 0xFFFFFFFC = -4              ... correct
--
--   Filling with '0' destroys the sign. Filling with the sign bit preserves it.
--   This is the same idea as sign extension in Lab 4, applied while shifting.
--
-- THE BUG THIS EXAMPLE EXISTS TO PREVENT
--   In VHDL, shift_right on an UNSIGNED value fills with '0' and shift_right on
--   a SIGNED value fills with the sign bit. The operator name is the same. The
--   TYPE decides the behaviour.
--
--       shift_right( unsigned(X), n )   -- this is SRL
--       shift_right(   signed(X), n )   -- this is SRA
--
--   So writing SRA with unsigned() silently gives you SRL. It compiles, it
--   runs, and it is wrong only for negative numbers - which most casual test
--   vectors do not include. Test with a negative number or you will not find it.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity shift_demo is
    port (
        Ain   : in  std_logic_vector(31 downto 0);
        Shft  : in  std_logic_vector(4 downto 0);   -- amount, 0..31, AS BITS
        Rsll  : out std_logic_vector(31 downto 0);
        Rsrl  : out std_logic_vector(31 downto 0);
        Rsra  : out std_logic_vector(31 downto 0)
    );
end entity shift_demo;

architecture rtl of shift_demo is

    -- Five bits hold 0..31, which is exactly the useful range for a 32-bit
    -- shift. Nothing is wasted and nothing can be out of range.
    signal amount : natural range 0 to 31;

begin

    amount <= to_integer(unsigned(Shft));

    Rsll <= std_logic_vector(shift_left (unsigned(Ain), amount));
    Rsrl <= std_logic_vector(shift_right(unsigned(Ain), amount));   -- fills '0'
    Rsra <= std_logic_vector(shift_right(  signed(Ain), amount));   -- fills sign

end architecture rtl;
