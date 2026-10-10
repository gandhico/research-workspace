--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P3 - REFERENCE SOLUTION  (TA only)
--
-- decoder3to8 : D(k) = E . m_k(A2,A1,A0),  k = 0..7
--
-- Two architectures:
--   behavioral - eight explicit minterms
--   structural - TWO decoder2to4 components, with A2 splitting the enable.
--                This is how every large decoder is actually built: a
--                5-to-32 decoder is two 4-to-16 decoders, which is what the
--                register file in Lab 6 needs.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity decoder3to8 is
    port ( E, A2, A1, A0 : in  std_logic;
           D             : out std_logic_vector(7 downto 0) );
end entity decoder3to8;

architecture behavioral of decoder3to8 is
begin
    D(0) <= E and (not A2) and (not A1) and (not A0);
    D(1) <= E and (not A2) and (not A1) and      A0;
    D(2) <= E and (not A2) and      A1  and (not A0);
    D(3) <= E and (not A2) and      A1  and      A0;
    D(4) <= E and      A2  and (not A1) and (not A0);
    D(5) <= E and      A2  and (not A1) and      A0;
    D(6) <= E and      A2  and      A1  and (not A0);
    D(7) <= E and      A2  and      A1  and      A0;
end architecture behavioral;

architecture structural of decoder3to8 is
    signal Elo, Ehi : std_logic;
begin
    -- A2 does not go into the sub-decoders. It splits the ENABLE.
    Elo <= E and (not A2);      -- lower half active when A2 = '0'
    Ehi <= E and      A2;       -- upper half active when A2 = '1'

    ULO : entity work.decoder2to4
        port map ( E => Elo, A1 => A1, A0 => A0, D => D(3 downto 0) );

    UHI : entity work.decoder2to4
        port map ( E => Ehi, A1 => A1, A0 => A0, D => D(7 downto 4) );
end architecture structural;
