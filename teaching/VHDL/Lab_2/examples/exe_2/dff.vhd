--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 2 - The SAME flip-flop, written BEHAVIOURALLY
--
-- Example 1 built an edge out of two latches, structurally, so you could see
-- where edge behaviour comes from. In practice nobody writes it that way.
-- This is what you write instead:
--
--       if rising_edge(Clk) then Q <= D; end if;
--
-- Two descriptions, one piece of hardware. Compare their RTL Viewer output:
-- the structural version shows two latches and an inverter, the behavioural
-- version shows one flip-flop primitive. The synthesiser recognises the
-- IDIOM 'rising_edge(Clk)' and maps it straight onto a real flip-flop in the
-- FPGA fabric, which is smaller and faster than two latches.
--
-- WHEN TO USE WHICH
--   structural  - when the STRUCTURE is the lesson, or when you must control
--                 exactly what gets built
--   behavioural - everywhere else. Say what you want, let the tool build it.
--
-- From this point on, every clocked design in this course is behavioural.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity dff is
    port (
        D   : in  std_logic;
        Clk : in  std_logic;
        Q   : out std_logic
    );
end entity dff;

architecture behavioral of dff is
begin

    -- Only Clk is in the sensitivity list, and that is CORRECT here.
    -- A clocked process reacts to the clock, not to the data: D is only ever
    -- read at the edge. This is the one case where a short sensitivity list
    -- is right, and it is worth understanding why before you rely on it.
    process (Clk)
    begin
        if rising_edge(Clk) then
            Q <= D;
        end if;
    end process;

end architecture behavioral;
