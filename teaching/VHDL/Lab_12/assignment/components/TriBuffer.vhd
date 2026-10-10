--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 4 reference component
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
