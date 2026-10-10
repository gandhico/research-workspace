--------------------------------------------------------------------------------
-- EE362 - Introduction to Computer Organization Laboratory
-- Exercise 2 - 2-to-1 Multiplexer
--
-- PURPOSE
--   A multiplexer selects one of two data inputs.
--
-- FUNCTION
--   s='0' -> y=d0
--   s='1' -> y=d1
--
-- TEACHING GOAL
--   Introduce conditional signal assignment with WHEN / ELSE.
--------------------------------------------------------------------------------

library ieee;
-- Makes the IEEE library visible.

use ieee.std_logic_1164.all;
-- Imports std_logic definitions.

entity mux_2to1 is
-- External interface of the multiplexer.

    port (
        d0 : in std_logic;
        -- First data input.

        d1 : in std_logic;
        -- Second data input.

        s : in std_logic;
        -- Selection input.

        y : out std_logic
        -- Selected output.
    );

end entity mux_2to1;
-- End of entity declaration.

architecture behavioral of mux_2to1 is begin

 y <= d0 when s = '0' else d1;

end architecture behavioral;
-- End of MUX implementation.
