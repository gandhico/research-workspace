--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1, Example 3 - The SAME latch, with a BROKEN sensitivity list
--
-- This file is WRONG ON PURPOSE. Do not copy it into your assignment.
--
-- The process reads both En and D, but only En is in the sensitivity list.
--
-- WHAT HAPPENS
--   In SIMULATION : the process only wakes up when En changes. If D changes
--                   while En is already '1', the simulator never re-evaluates,
--                   so Q does not follow D. The latch appears broken.
--                   Q only changes at the instant En goes 0 -> 1: that is a
--                   FLIP-FLOP clocked by En, not a latch.
--   In SYNTHESIS  : (measured, Quartus Prime Lite 25.1std) Quartus recognises
--                   "process (En) ... if En = '1'" as a flip-flop template and
--                   builds exactly that: Total registers = 1, 0 latches, and
--                   NO WARNING. Simulation and hardware agree - both are wrong.
--
-- Contrast: put a Clr branch in front (your assignment starter) and the same
-- missing names give Warning 10492 plus a correct latch in hardware - a
-- simulation/synthesis MISMATCH. One missing name, two different failures.
-- The correct latch prints a warning (10631); this broken one prints nothing.
--
-- Compare the waveforms of trans_latch (Example 2) and trans_latch_bad here.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity trans_latch_bad is
    port (
        D  : in  std_logic;
        En : in  std_logic;
        Q  : out std_logic
    );
end entity trans_latch_bad;

architecture broken of trans_latch_bad is
begin

    process (En)                            -- BUG: D is missing from this list
    begin
        if En = '1' then
            Q <= D;
        end if;
    end process;

end architecture broken;
