--------------------------------------------------------------------------------
-- EE362 - Introduction to Computer Organization Laboratory
-- Exercise 1 - Majority-of-Three Circuit
-- Specification: Design a combinational circuit three inputs:
-- Three inputs: A, B, C
-- One Output: Y 
-- Y=1 whenever two or more inputs are 1
-- PURPOSE
-- The output Y is '1' when at least two of the three inputs are '1'
--------------------------------------------------------------------------------

library ieee;
-- Makes the IEEE library visible.

use ieee.std_logic_1164.all;
-- Imports std_logic and standard logic operators such as AND and OR.

entity majority_of_three is
-- ENTITY defines the external interface of the hardware block.

    port (
        a : in std_logic;
        -- First one-bit input.

        b : in std_logic;
        -- Second one-bit input.

        c : in std_logic;
        -- Third one-bit input.

        y : out std_logic
        -- One-bit output.
        -- y='1' when at least two inputs are '1'.
    );

end entity majority_of_three;
-- End of the interface declaration.

architecture behavioral of majority_of_three is
-- ARCHITECTURE defines how the entity is implemented.
-- "behavioral" is the architecture name chosen for this implementation.

begin
-- BEGIN marks the start of the concurrent hardware description.

    y <= (a and b) or (a and c) or (b and c);
    -- <= is SIGNAL ASSIGNMENT.
    --
    -- This implements the majority Boolean function:
    --   y = AB + AC + BC
    --
    -- Each AND term detects one pair of inputs equal to '1'.
    -- OR combines the three possible majority conditions.
    --
    -- This is a CONCURRENT statement, so this hardware is continuously active.
    -- Whenever a, b, or c changes, y responds to the new input combination.

end architecture behavioral;
-- End of the hardware description.
