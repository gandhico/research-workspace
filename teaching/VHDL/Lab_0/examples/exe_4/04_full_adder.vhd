--------------------------------------------------------------------------------
-- EE362 - Introduction to Computer Organization Laboratory
-- Exercise 4 - Full Adder
--
-- PURPOSE
--   Add three one-bit values: A + B + CIN.
--
-- OUTPUTS
--   SUM  = one-bit sum
--   COUT = carry to the next bit
--
-- BOOLEAN EQUATIONS
--   SUM  = A XOR B XOR CIN
--   COUT = AB + A*CIN + B*CIN
--
-- TEACHING GOAL
--   Reinforce basic VHDL and introduce a fundamental arithmetic circuit.
--------------------------------------------------------------------------------

library ieee;
-- Makes the IEEE library visible.

use ieee.std_logic_1164.all;
-- Imports std_logic and XOR/AND/OR operators.

entity full_adder is
-- External interface of the one-bit full adder.

    port (
        a : in std_logic;
        -- First one-bit input.

        b : in std_logic;
        -- Second one-bit input.

        cin : in std_logic;
        -- Carry input.

        sum : out std_logic;
        -- Sum output.

        cout : out std_logic
        -- Carry output.
    );

end entity full_adder;
-- End of entity declaration.

architecture behavioral of full_adder is

begin

    sum <= a xor b xor cin;
    -- XOR produces the correct one-bit sum for the three inputs.
    -- This is a concurrent signal assignment.

    cout <= (a and b) or
            (a and cin) or
            (b and cin);
    -- Carry is '1' whenever at least two inputs are '1'.
    --
    -- Notice the connection with Exercise 1:
    -- COUT is exactly a MAJORITY-OF-THREE function of a, b, and cin.
    --
    -- The statement spans multiple text lines only for readability.
    -- The semicolon marks the end of the VHDL statement.

end architecture behavioral;
-- End of full-adder implementation.
