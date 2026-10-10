--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P1 - REFERENCE SOLUTION  (TA only)
--
-- voting4 : Y = 1 when at least THREE of A, B, C, D are '1'
--           (with four voters, "at least three" is a strict majority)
--
--   Y = Sum m(7,11,13,14,15)
--     = ABC + ABD + ACD + BCD          <- all C(4,3) = 4 triples
--
-- Two architectures:
--   behavioral - the four-triple sum of products, straight from the equation
--   structural - Y = D.Maj3(A,B,C) + D'.(A.B.C), built by REUSING the
--                majority3 and mux2 components from class Examples 1 and 2
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity voting4 is
    port ( A, B, C, D : in  std_logic;
           Y          : out std_logic );
end entity voting4;

architecture behavioral of voting4 is
begin
    Y <= (A and B and C) or (A and B and D) or
         (A and C and D) or (B and C and D);
end architecture behavioral;

architecture structural of voting4 is
    signal maj3    : std_logic;     -- at least 2 of A,B,C
    signal allABC  : std_logic;     -- all 3 of A,B,C
begin
    -- If D votes yes, we only need 2 more from A,B,C.
    -- If D votes no,  we need all 3 of A,B,C.
    U_MAJ : entity work.majority3
        port map ( A => A, B => B, C => C, Y => maj3 );

    allABC <= A and B and C;

    U_MUX : entity work.mux2
        port map ( D0 => allABC, D1 => maj3, S => D, Y => Y );
end architecture structural;
