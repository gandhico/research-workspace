--------------------------------------------------------------------------------
-- EE 362 - Lab 4 REFERENCE SOLUTION  (TA only - do not publish)
-- ALUsftMUX : shift amount from the IR sa field (Ssel='0') or register B
-- (Ssel='1'). Written directly; instantiating Lab 3's Mux2 with W=>5 is
-- equally acceptable and is the better engineering answer.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity ALUsftMUX is
    port (
        SA   : in  std_logic_vector(4 downto 0);
        Bout : in  std_logic_vector(4 downto 0);
        Ssel : in  std_logic;
        Shft : out std_logic_vector(4 downto 0)
    );
end entity ALUsftMUX;

architecture rtl of ALUsftMUX is
begin
    with Ssel select
        Shft <= SA   when '0',
                Bout when '1',
                (others => 'X') when others;
end architecture rtl;
