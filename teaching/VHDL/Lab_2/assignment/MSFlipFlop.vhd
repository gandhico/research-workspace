--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2 - Assignment, Part 1 of 2
--
-- MSFlipFlop : positive-edge-triggered D flip-flop with asynchronous clear,
--              built STRUCTURALLY from two of your Lab 1 transparent latches
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION
--   Clk = '0'  ->  master transparent, slave holding
--   Clk = '1'  ->  master holding,     slave transparent
--   Clr = '1'  ->  both latches cleared, immediately, at any time
--
--   Result: Q can only change on the RISING edge of Clk.
--
-- EQUATIONS - each latch is Lab 1's equation with a different enable:
--   master   Qm+ = Clr' . ( Clk'.D  + Clk.Qm  )
--   slave    Q+  = Clr' . ( Clk.Qm  + Clk'.Q  )
--
-- Nothing new is being invented. You are wiring two things you already own.
--
-- WHY THE CLEAR GOES TO BOTH LATCHES: if you cleared only the slave, the master
-- would still hold the old value and would push it into the slave at the very
-- next rising edge - the clear would appear to "un-clear" itself one cycle
-- later. Try it in simulation once you have it working; it is a good bug to
-- have seen deliberately.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity MSFlipFlop is
    port (
        D   : in  std_logic;
        Clk : in  std_logic;
        Clr : in  std_logic;                -- asynchronous clear, active high
        Q   : out std_logic
    );
end entity MSFlipFlop;

architecture structural of MSFlipFlop is

    -- TODO 1: declare the internal signals you need.
    --         You need the master's output, and the opposite of Clk.
    --         (Internal wires are 'signal', declared here, before 'begin'.)


begin

    -- TODO 2: generate the opposite enable.


    -- TODO 3: instantiate TWO TransLatch components.
    --         Use named association - formal => actual - for every port.
    --         Give each instance a label (MASTER : ... and SLAVE : ...).
    --
    --         The master is open while Clk = '0'.
    --         The slave  is open while Clk = '1'.
    --         Both see the same Clr.
    --
    --         Syntax reminder:
    --             LABEL : entity work.TransLatch
    --                 port map (D => ..., En => ..., Clr => ..., Q => ...);


end architecture structural;
