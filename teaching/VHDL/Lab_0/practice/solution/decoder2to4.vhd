--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice - shared component (from class Example 3, CORRECTED)
-- decoder2to4 : D(k) = E . m_k(A1,A0)
--
-- NOTE: the behavioural file shown in class declared E and never used it.
-- This version gates on E, as the specification requires.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4 is
    port ( E, A1, A0 : in  std_logic;
           D         : out std_logic_vector(3 downto 0) );
end entity decoder2to4;

architecture behavioral of decoder2to4 is
begin
    D(0) <= E and (not A1) and (not A0);
    D(1) <= E and (not A1) and      A0;
    D(2) <= E and      A1  and (not A0);
    D(3) <= E and      A1  and      A0;
end architecture behavioral;
