--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3 - Assignment, Part 2 of 3
--
-- Mux3 : 3-to-1 multiplexer, ANY width
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C
--
--   #  Sel1 Sel0  ||  Y     note
--   0    0    0   ||  A
--   1    0    1   ||  B
--   2    1    0   ||  C
--   3    1    1   ||  0     DEFINED DEFAULT - all zeros
--
-- Row 3 is not "don't care" and it is not "impossible". It is a DECISION, and
-- you must implement it deliberately. Leave it unassigned and you get a latch
-- (Example 3). State the decision in your report.
--
-- EQUATIONS, per bit i:
--
--   (1) canonical   Y_i = S1'S0'.A_i + S1'S0.B_i + S1S0'.C_i + S1S0.0
--                                                              ^-- row 3 outputs
--                                                                  zero, so it
--                                                                  needs no term
--
--   (2) factored    Y_i = S1'.( S0'.A_i + S0.B_i ) + S1.S0'.C_i
--                                    [distributive law, factoring S1']
--
--   (3) VHDL        <- what you write below
--
-- LOOK AT WHAT (2) IS. The bracket is a 2-to-1 multiplexer choosing A or B.
-- The whole expression is a second 2-to-1 multiplexer choosing between that
-- result and C. You factored an equation and a CIRCUIT STRUCTURE came out.
--
-- Factoring algebra and splitting a design into sub-blocks are the same
-- operation. This is the first place in the course you can see that, and it
-- stays true all the way to the CPU.
--
-- WHERE THIS ENDS UP: DinMUX and ALUinMUX (32 bits), and the PC source select
-- in Lab 8.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity Mux3 is
    generic (
        W : positive := 32
    );
    port (
        A   : in  std_logic_vector(W - 1 downto 0);   -- Sel = "00"
        B   : in  std_logic_vector(W - 1 downto 0);   -- Sel = "01"
        C   : in  std_logic_vector(W - 1 downto 0);   -- Sel = "10"
        Sel : in  std_logic_vector(1 downto 0);
        Y   : out std_logic_vector(W - 1 downto 0)
    );
end entity Mux3;

architecture rtl of Mux3 is
begin

    -- TODO: implement the table above, INCLUDING row 3.
    --
    -- Strong advice: use a 'case' with 'when others', not an if/elsif chain.
    -- VHDL forces a case to cover every possible selector value, so the
    -- language itself will stop you making the Example 3 mistake. An if/elsif
    -- chain will happily let you forget.

end architecture rtl;
