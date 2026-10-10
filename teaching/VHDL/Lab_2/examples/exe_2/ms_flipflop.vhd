--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 1 - Master-slave flip-flop, STRUCTURAL
--
-- Built from two Lab 1 transparent latches with OPPOSITE enables.
-- Nothing new is invented here. An edge falls out of two level-sensitive parts.
--
--   Clk = '0' : master transparent (En = not Clk = '1'), slave holding
--   Clk = '1' : master holding,                          slave transparent
--
-- So while the clock is low the master tracks D. The instant the clock rises,
-- the master freezes on whatever D was, and the slave opens and copies it.
-- The output can therefore only ever change at the RISING EDGE.
--
-- EQUATIONS - each is just Lab 1's latch with a different enable:
--   master   Qm+ = Clk'.D  + Clk.Qm
--   slave    Q+  = Clk.Qm  + Clk'.Q
--
-- "Edge-triggered" is not a primitive. It is a consequence.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ms_flipflop is
    port (
        D   : in  std_logic;
        Clk : in  std_logic;
        Q   : out std_logic
    );
end entity ms_flipflop;

architecture structural of ms_flipflop is

    signal Qm   : std_logic;                -- master output, internal only
    signal ClkN : std_logic;                -- the opposite enable

begin

    ClkN <= not Clk;

    -- Component instantiation. Named association ( formal => actual ), always.
    MASTER : entity work.trans_latch
        port map (
            D  => D,
            En => ClkN,                     -- open while Clk = '0'
            Q  => Qm
        );

    SLAVE : entity work.trans_latch
        port map (
            D  => Qm,
            En => Clk,                      -- open while Clk = '1'
            Q  => Q
        );

end architecture structural;
