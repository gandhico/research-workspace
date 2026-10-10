--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1, Example 2 - Testbench for the transparent latch
--
-- This is the testbench pattern used for the REST OF THE SEMESTER. Learn it here.
--
--   1. The testbench entity has NO PORTS. It is a closed world.
--   2. It instantiates the design under test (DUT).
--   3. One stimulus process applies inputs and CHECKS outputs with assert.
--   4. It counts failures and reports a verdict, then stops with 'wait'.
--
-- A waveform is EVIDENCE. The asserts are the PROOF. Never rely on looking at
-- a waveform and deciding it looks about right.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity trans_latch_tb is
end entity trans_latch_tb;

architecture test of trans_latch_tb is

    signal D  : std_logic := '0';
    signal En : std_logic := '0';
    signal Q  : std_logic;

begin

    DUT : entity work.trans_latch
        port map (
            D  => D,
            En => En,
            Q  => Q
        );

    stimulus : process

        variable errors : natural := 0;

        -- One place that knows how to check and complain. Reused every lab.
        procedure check (expected : in std_logic; msg : in string) is
        begin
            if Q /= expected then
                report "FAIL: " & msg &
                       " - expected " & std_logic'image(expected) &
                       ", got "       & std_logic'image(Q)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Row 1: transparent, D = '0'
        En <= '1'; D <= '0';  wait for 10 ns;
        check('0', "row 1: transparent with D=0");

        -- Row 2: transparent, D = '1'
        D <= '1';             wait for 10 ns;
        check('1', "row 2: transparent with D=1");

        -- Row 0: HOLD. This is the vector that proves it is memory.
        -- Close the latch, then change D. Q must NOT follow.
        En <= '0';            wait for 9 ns;
        D  <= '0';            wait for 12 ns;
        check('1', "row 0: held value survives a change of D");
		  
		  -- New Test
        En <= '1';   wait for 9 ns;
		  D <= '0';  wait for 15 ns;
		  D <= '1';  wait for 5 ns;
		  En <= '0';   wait for 3 ns;
		  D <= '0';  wait for 6 ns;
		  D <= '1';  wait for 9 ns;
        check('0', "row 1: transparent with D=0");

        -- Re-open: Q must now catch up to the new D
        En <= '1';            wait for 10 ns;
        check('0', "reopening makes Q follow D again");

        -- Verdict
        if errors = 0 then
            report "PASS - trans_latch: all checks passed." severity note;
        else
            report "FAILED - trans_latch: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;                               -- stop here, or the process restarts forever
    end process stimulus;

end architecture test;
