--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 1 - Testbench for the master-slave flip-flop
--
-- NEW THIS WEEK: a clock. Two things change in every testbench from now on.
--
--   1. A separate CLOCK PROCESS generates the clock forever. It needs a 'wait'
--      or the simulation hangs at time zero in an infinite loop.
--   2. The stimulus process changes D BETWEEN edges, never on one.
--
-- Point 2 is not a stylistic preference. Real flip-flops require the data to be
-- stable for a short time before the clock edge - the SETUP TIME. Changing D
-- exactly on an edge in simulation is the same mistake as violating setup time
-- in hardware, and it produces the same kind of unpredictable result.
--
-- WHAT TO WATCH: D toggles several times inside one clock period, and Q moves
-- exactly once, at the rising edge. That is the whole point of the lab.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ms_flipflop_tb is
end entity ms_flipflop_tb;

architecture test of ms_flipflop_tb is

    constant PERIOD : time := 20 ns;

    signal Clk : std_logic := '0';
    signal D   : std_logic := '0';
    signal Q   : std_logic;

    signal running : boolean := true;       -- lets us stop the clock at the end

begin

    DUT : entity work.ms_flipflop
        port map (D => D, Clk => Clk, Q => Q);

    ----------------------------------------------------------------------------
    -- Clock generator. Note the 'wait for' - without it this loops forever at
    -- time zero and the simulator appears to freeze.
    ----------------------------------------------------------------------------
    clock_gen : process
    begin
        while running loop
            Clk <= '0';
            wait for PERIOD / 2;
            Clk <= '1';
            wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    ----------------------------------------------------------------------------
    -- Stimulus. Every change of D happens just after a FALLING edge, which is
    -- as far from the next rising edge as we can get.
    ----------------------------------------------------------------------------
    stimulus : process

        variable errors : natural := 0;

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

        -- Settle: two clock periods with D low
        D <= '0';
        wait until falling_edge(Clk);
        wait until falling_edge(Clk);
        check('0', "starts low");

        -- Raise D between edges; Q must not move until the next rising edge
        D <= '1';
        wait for 1 ns;
        check('0', "Q does not follow D between edges");

        wait until rising_edge(Clk);
        wait for 1 ns;
        check('1', "Q captured D at the rising edge");

        -- THE KEY VECTOR: toggle D three times inside one clock period.
        -- Q must move only once, and only at the edge.
        wait until falling_edge(Clk);
        D <= '0'; wait for 2 ns;
        D <= '1'; wait for 2 ns;
        D <= '0'; wait for 2 ns;
        check('1', "Q ignores all toggling between edges");

        wait until rising_edge(Clk);
        wait for 1 ns;
        check('0', "Q captured the LAST value of D before the edge");

        if errors = 0 then
            report "PASS - ms_flipflop: all checks passed." severity note;
        else
            report "FAILED - ms_flipflop: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;                   -- stop the clock so the run ends
        wait;
    end process stimulus;

end architecture test;
