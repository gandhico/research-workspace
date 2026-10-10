--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4, Example 3 - The conversion chain
--
-- std_logic_vector is a BAG OF BITS. It has no numeric meaning at all - VHDL
-- will not let you add two of them, because it does not know whether you meant
-- signed or unsigned arithmetic. You have to say.
--
-- THE CHAIN, and you will type it a hundred times this semester:
--
--   std_logic_vector  --> unsigned / signed  --> integer
--        (bits)              (a number)          (an index or a count)
--
--     to_integer( unsigned( Slv ) )     -- treat the bits as unsigned, get an integer
--     to_integer(   signed( Slv ) )     -- treat the bits as two's complement
--     std_logic_vector( to_unsigned( N, W ) )   -- and back again, at width W
--
-- Read it inside out. unsigned(Slv) reinterprets; to_integer() then converts.
--
-- WHY YOU NEED IT: you cannot index a vector with a vector. Slv(Other_Slv) is
-- meaningless. Array indices are integers, so a shift amount, a register
-- number, or a memory address arriving as bits must be converted before use.
--
-- Requires:  use ieee.numeric_std.all;
-- NEVER use std_logic_arith or std_logic_unsigned. They are not IEEE standard,
-- they conflict with each other, and mixing them produces errors that read as
-- though the compiler has lost its mind.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity convert_demo is
    port (
        Data  : in  std_logic_vector(7 downto 0);
        Shamt : in  std_logic_vector(2 downto 0);   -- shift amount, AS BITS
        Bit0  : out std_logic;                      -- one selected bit of Data
        Shift : out std_logic_vector(7 downto 0)    -- Data shifted left by Shamt
    );
end entity convert_demo;

architecture rtl of convert_demo is

    -- Convert once, use twice. Naming the integer makes the intent obvious and
    -- keeps the conversion out of the middle of an expression.
    signal amount : natural range 0 to 7;

begin

    amount <= to_integer(unsigned(Shamt));

    -- Indexing a vector REQUIRES an integer. This is the whole reason for the
    -- conversion chain.
    Bit0 <= Data(amount);

    -- Shifting: shift_left works on unsigned/signed, not on std_logic_vector,
    -- so we convert in, shift, and convert back out.
    Shift <= std_logic_vector(shift_left(unsigned(Data), amount));

end architecture rtl;
