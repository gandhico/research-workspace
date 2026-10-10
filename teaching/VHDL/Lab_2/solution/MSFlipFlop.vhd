--------------------------------------------------------------------------------
-- EE 362 - Lab 2 REFERENCE SOLUTION  (TA only - do not publish)
--
-- MSFlipFlop : positive-edge D flip-flop with async clear, from two TransLatch
--
--   master   Qm+ = Clr' . ( Clk'.D + Clk.Qm )
--   slave    Q+  = Clr' . ( Clk.Qm + Clk'.Q )
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity MSFlipFlop is
    port (
        D   : in  std_logic;
        Clk : in  std_logic;
        Clr : in  std_logic;
        Q   : out std_logic
    );
end entity MSFlipFlop;

architecture structural of MSFlipFlop is

    signal Qm   : std_logic;
    signal ClkN : std_logic;

begin

    ClkN <= not Clk;

    MASTER : entity work.TransLatch
        port map (D => D,  En => ClkN, Clr => Clr, Q => Qm);

    SLAVE : entity work.TransLatch
        port map (D => Qm, En => Clk,  Clr => Clr, Q => Q);

end architecture structural;
