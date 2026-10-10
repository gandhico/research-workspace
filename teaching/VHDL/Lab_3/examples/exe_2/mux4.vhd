--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3, Example 2 - 4-to-1 multiplexer, 8 bits wide, generic
--
-- SPECIFICATION - Table C (compressed)
--
--   #  Sel  ||  Y      note
--   0  00   ||  A
--   1  01   ||  B
--   2  10   ||  C
--   3  11   ||  D
--
-- Four rows completely specify a function of 34 inputs (four 8-bit buses plus
-- a 2-bit selector). An EXHAUSTIVE table would need 2^34 rows - about 17
-- billion. The rows are symbolic: "Y = B" names a SOURCE, not a value.
--
-- That is what a compressed table buys you, and it is the only reason datapath
-- design is possible at all. You will use Type C tables for the rest of the
-- course; Type E (exhaustive) only survives while you have four inputs or fewer.
--
-- EQUATION, per bit i:
--   Y_i = S1'S0'.A_i + S1'S0.B_i + S1S0'.C_i + S1S0.D_i
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity mux4 is
    generic (
        W : positive := 32                   -- data width
    );
    port (
        A, B, C, D : in  std_logic_vector(W - 1 downto 0);
        Sel        : in  std_logic_vector(1 downto 0);
        Y          : out std_logic_vector(W - 1 downto 0)
    );
end entity mux4;

architecture rtl of mux4 is
begin

    -- Selected signal assignment: reads exactly like the table above.
    with Sel select
        Y <= A when "00",
             B when "01",
             C when "10",
             D when "11",
             (others => 'X') when others;   -- 'U','X','Z'... on the selector
    -- Driving 'X' for an impossible selector value is a deliberate choice: if a
    -- selector ever goes undefined in a later lab, the 'X' propagates and shows
    -- you immediately, instead of silently picking one of the inputs.

end architecture rtl;
