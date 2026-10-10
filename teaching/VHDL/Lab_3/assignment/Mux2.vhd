--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3 - Assignment, Part 1 of 3
--
-- Mux2 : 2-to-1 multiplexer, ANY width
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C (compressed)
--
--   #  Sel  ||  Y     note
--   0   0   ||  A
--   1   1   ||  B
--
-- Two rows. That is the complete specification of a function with 65 inputs
-- when W = 32. An exhaustive table would need 2^65 rows.
--
-- EQUATION, per bit i:
--   Y_i = Sel'.A_i + Sel.B_i
--
-- WHERE THIS ENDS UP: this becomes DselMUX (5 bits) and part of the ALU input
-- path (32 bits) in your CPU. Same entity, two widths, no duplicated code.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity Mux2 is
    generic (
        W : positive := 32                  -- data width
    );
    port (
        A   : in  std_logic_vector(W - 1 downto 0);   -- selected when Sel = '0'
        B   : in  std_logic_vector(W - 1 downto 0);   -- selected when Sel = '1'
        Sel : in  std_logic;
        Y   : out std_logic_vector(W - 1 downto 0)
    );
end entity Mux2;

architecture rtl of Mux2 is
begin

    -- TODO: implement the table above.
    --
    -- Any of the three styles from Example 1 is acceptable. Whichever you pick,
    -- say in your report WHY you picked it - that is the graded part, not the
    -- syntax.
    --
    -- Whatever you write, it must be COMBINATIONAL. If the Fitter reports any
    -- storage element for this entity, you have written a latch. Go back to
    -- Example 3.

end architecture rtl;
