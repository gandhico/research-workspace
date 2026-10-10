--------------------------------------------------------------------------------
-- EE 362 - Lab 4 REFERENCE SOLUTION  (TA only - do not publish)
-- TriBuffer : 32-bit tri-state buffer.  Sel='1' drives Din, Sel='0' releases.
-- Not a Boolean function: its output range is {0,1,Z}.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity TriBuffer is
    port (
        Din  : in  std_logic_vector(31 downto 0);
        Sel  : in  std_logic;
        Dout : out std_logic_vector(31 downto 0)
    );
end entity TriBuffer;

architecture rtl of TriBuffer is
begin
    Dout <= Din when Sel = '1' else (others => 'Z');
end architecture rtl;
