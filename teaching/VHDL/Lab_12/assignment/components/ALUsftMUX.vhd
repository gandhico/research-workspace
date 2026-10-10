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
