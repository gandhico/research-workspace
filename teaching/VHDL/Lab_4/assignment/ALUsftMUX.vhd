--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4 - Assignment, Part 3 of 3
--
-- ALUsftMUX : choose where the ALU's shift amount comes from
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C
--
--   #  Ssel  ||  Shft     source                       instruction
--   0   0    ||  SA       the instruction's sa field   SLL r2, r2, 1
--   1   1    ||  Bout     low 5 bits of register B     SLLV r2, r2, r3
--
-- Five bits, because a 32-bit value can be shifted by 0..31 and that is exactly
-- what five bits hold. Nothing is wasted and nothing is out of range.
--
-- THIS IS A Mux2 WITH W = 5. You already wrote that in Lab 3, and you may
-- simply instantiate it:
--
--     U : entity work.Mux2
--         generic map (W => 5)
--         port map (A => SA, B => Bout, Sel => Ssel, Y => Shft);
--
-- Either write it directly or reuse Mux3/Mux2 - both are acceptable. But say
-- in your report WHICH you did and why. Reusing a tested component is usually
-- the better engineering answer, and recognising that a "new" block is one you
-- already own is a skill this course is trying to build.
--
-- (If you reuse Mux2, copy your Lab 3 Mux2.vhd into this folder and add it to
-- the project.)
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ALUsftMUX is
    port (
        SA   : in  std_logic_vector(4 downto 0);   -- IR sa field
        Bout : in  std_logic_vector(4 downto 0);   -- register file B, low 5 bits
        Ssel : in  std_logic;                      -- '0' = SA, '1' = Bout
        Shft : out std_logic_vector(4 downto 0)
    );
end entity ALUsftMUX;

architecture rtl of ALUsftMUX is
begin

    -- TODO: implement the table above, directly or by instantiating Mux2.

end architecture rtl;
