--------------------------------------------------------------------------------
-- EE 362 - Lab 8 REFERENCE SOLUTION  (TA only - do not publish)
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
