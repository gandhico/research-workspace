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
-- EE 362 - Lab 8 reference component
-- NIAG_MUX : two stages. A Taken gate (2-to-1) feeding the selection (4-to-1).
-- Only the relative path is conditional; not-taken falls back to NSA.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use work.NIAG_Pkg.all;

entity NIAG_MUX is
    port (
        Sel     : in  std_logic_vector(1 downto 0);
        Taken   : in  std_logic;
        NSA     : in  std_logic_vector(31 downto 0);
        Rel     : in  std_logic_vector(31 downto 0);
        RegAddr : in  std_logic_vector(31 downto 0);
        Abslt   : in  std_logic_vector(31 downto 0);
        NextPC  : out std_logic_vector(31 downto 0)
    );
end entity NIAG_MUX;

architecture rtl of NIAG_MUX is
    signal rel_or_nsa : std_logic_vector(31 downto 0);
begin
    rel_or_nsa <= Rel when Taken = '1' else NSA;

    with Sel select
        NextPC <= NSA        when NIAG_SEL_NSA,
                  rel_or_nsa when NIAG_SEL_REL,
                  RegAddr    when NIAG_SEL_REG,
                  Abslt      when NIAG_SEL_ABS,
                  NSA        when others;
end architecture rtl;
