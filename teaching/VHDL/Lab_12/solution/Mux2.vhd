--------------------------------------------------------------------------------
-- EE 362 - Lab 3 REFERENCE SOLUTION  (TA only - do not publish)
--
-- Mux2 : generic-width 2-to-1 multiplexer
--   Y_i = Sel'.A_i + Sel.B_i
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity Mux2 is
    generic (W : positive := 32);
    port (
        A   : in  std_logic_vector(W - 1 downto 0);
        B   : in  std_logic_vector(W - 1 downto 0);
        Sel : in  std_logic;
        Y   : out std_logic_vector(W - 1 downto 0)
    );
end entity Mux2;

architecture rtl of Mux2 is
begin
    with Sel select
        Y <= A when '0',
             B when '1',
             (others => 'X') when others;   -- undefined selector propagates
end architecture rtl;
