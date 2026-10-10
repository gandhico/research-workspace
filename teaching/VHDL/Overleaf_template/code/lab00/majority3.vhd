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

-- Main Library
library ieee;

-- std_logic_1164 imports std_logic and standard logic operators such as AND and OR
use ieee.std_logic_1164.all;


-- ENTITY defines the external interface of the hardware block.
entity majority3 is
 port ( A : in std_logic; B : in std_logic; C : in std_logic;
       Y : out std_logic);
end majority3;

-- ARCHITECTURE defines how the entity is implemented.
 architecture behavioral of majority3 is 
 begin Y <= (A and B) or (A and C) or (B and C);
 end architecture behavioral;
 
 