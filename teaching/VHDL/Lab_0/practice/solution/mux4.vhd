--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P2 - REFERENCE SOLUTION  (TA only)
--
-- mux4 : 4-to-1 multiplexer, S1S0 selects one of D0..D3
--
--   Y = S1'S0'.D0 + S1'S0.D1 + S1S0'.D2 + S1S0.D3
--     = Sum over k of  m_k(S1,S0) . D_k
--
-- Read that second form: the coefficients ARE the four outputs of the
-- 2-to-4 decoder from Example 3. A multiplexer is a decoder AND-ed with
-- the data, then OR-ed together.
--
-- Two architectures:
--   behavioral - flat select, 2 gate levels (fast, wide)
--   structural - a TREE of three mux2 components, 2 mux levels
--                (slower here, but the form that scales - see Lab 3)
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux4 is
    port ( D0, D1, D2, D3 : in  std_logic;
           S1, S0         : in  std_logic;
           Y              : out std_logic );
end entity mux4;

architecture behavioral of mux4 is
    signal S : std_logic_vector(1 downto 0);
begin
    S <= S1 & S0;

    with S select
        Y <= D0   when "00",
             D1   when "01",
             D2   when "10",
             D3   when "11",
             'X'  when others;      -- metavalues on the select only
end architecture behavioral;

architecture structural of mux4 is
    signal L0, L1 : std_logic;
begin
    -- Level 1: S0 picks within each pair
    U0 : entity work.mux2 port map ( D0 => D0, D1 => D1, S => S0, Y => L0 );
    U1 : entity work.mux2 port map ( D0 => D2, D1 => D3, S => S0, Y => L1 );

    -- Level 2: S1 picks between the pairs
    U2 : entity work.mux2 port map ( D0 => L0, D1 => L1, S => S1, Y => Y  );
end architecture structural;
