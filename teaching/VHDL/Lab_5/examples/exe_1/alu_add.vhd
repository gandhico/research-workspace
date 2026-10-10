--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5, Example 1 - One ALU function unit, complete, with status flags
--
-- This is the TEMPLATE every other operation copies. Read it once carefully and
-- the other fourteen become one line each.
--
-- THE ARITHMETIC
--   std_logic_vector is a bag of bits with no numeric meaning, so you cannot
--   write A + B on two of them. Convert, add, convert back:
--
--       unsigned(Ain) + unsigned(Bin)          -- now it is arithmetic
--       std_logic_vector( ... )                -- back to bits for the port
--
--   We add as UNSIGNED even though the values may be signed. That is correct:
--   two's complement addition is bit-identical whether you call the operands
--   signed or unsigned. Only the INTERPRETATION of the result differs, and that
--   is what the flags are for.
--
-- THE FLAGS
--   Zero  Z = 1 when every result bit is 0.
--         In VHDL:  if Result = 0 ... but Result is a vector, so compare it
--         against an all-zeros aggregate.
--
--   Neg   N = the top bit of the result, Result(31).
--         In two's complement the top bit IS the sign. Nothing to compute.
--
--   These two flags are what makes conditional branching possible. In Lab 8 you
--   will write six one-line Boolean equations over exactly these two signals and
--   get every conditional branch the machine has.
--
-- CARRY OUT, and why we bother
--   Adding two 32-bit numbers can produce 33 bits. To see the 33rd, widen the
--   operands to 33 bits BEFORE adding. If you add at 32 bits the extra bit is
--   simply lost - there is nowhere for it to go.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity alu_add is
    port (
        Ain   : in  std_logic_vector(31 downto 0);
        Bin   : in  std_logic_vector(31 downto 0);
        Rout  : out std_logic_vector(31 downto 0);
        Zero  : out std_logic;                      -- result is all zeros
        Neg   : out std_logic;                      -- result's top bit
        Cout  : out std_logic                       -- carry out of bit 31
    );
end entity alu_add;

architecture rtl of alu_add is

    -- 33 bits wide, so the carry out has somewhere to land.
    signal sum33 : unsigned(32 downto 0);
    signal res   : std_logic_vector(31 downto 0);

begin

    -- Widen both operands to 33 bits, then add. '0' & X prepends a zero bit.
    sum33 <= unsigned('0' & Ain) + unsigned('0' & Bin);

    res   <= std_logic_vector(sum33(31 downto 0));
    Rout  <= res;

    Cout  <= sum33(32);                             -- the 33rd bit

    -- Zero: true only if every bit of the result is '0'.
    Zero  <= '1' when res = (res'range => '0') else '0';

    -- Negative: in two's complement the top bit is the sign. No computation.
    Neg   <= res(31);

end architecture rtl;
