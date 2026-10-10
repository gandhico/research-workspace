--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1, Example 3 - Sensitivity list: correct vs broken, side by side
--
-- Both latches are driven by exactly the same stimulus. The only difference
-- between them is one signal name in a sensitivity list.
--
-- WHAT TO WATCH IN THE WAVEFORM
--   At t = 10 ns, D changes while En is already '1' (checked at t = 20 ns).
--     Q_good follows D immediately.  <-- correct
--     Q_bad  does not move.          <-- the process never woke up
--
-- Q_bad only updates when En rises, because En is the only signal that can
-- wake its process - it behaves as a flip-flop clocked by En. Quartus 25.1
-- synthesises it as exactly that (1 register, no warning), so here the
-- hardware matches the broken simulation. Check "Total registers" in the
-- Flow Summary: 1 for this design, 0 for the correct latch.
--
-- The assert below is expected to FAIL for the broken latch. That failure is
-- the point of this example.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity sensitivity_compare_tb is
end entity sensitivity_compare_tb;

architecture test of sensitivity_compare_tb is

    signal D      : std_logic := '0';
    signal En     : std_logic := '0';
    signal Q_good : std_logic;
    signal Q_bad  : std_logic;

begin

    DUT_GOOD : entity work.trans_latch
        port map (D => D, En => En, Q => Q_good);

    DUT_BAD : entity work.trans_latch_bad
        port map (D => D, En => En, Q => Q_bad);

    stimulus : process
    begin

        -- Open both latches with D = '0'
        En <= '1'; D <= '0';  wait for 10 ns;

        -- Now change D while En is ALREADY high.
        -- The good latch reacts. The broken one cannot: its process is only
        -- sensitive to En, and En did not change.
        D <= '1';             wait for 10 ns;

        assert Q_good = '1'
            report "Correct latch failed to follow D - check Example 2."
            severity error;

        assert Q_bad = '1'
            report "EXPECTED FAILURE: the broken latch did not follow D. " &
                   "One missing name in a sensitivity list caused this."
            severity error;

        report "Compare Q_good and Q_bad in the waveform at t = 10 ns to 20 ns."
            severity note;

        wait;
    end process stimulus;

end architecture test;
