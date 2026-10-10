--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- This testbench drives THREE devices from one clock:
--   MSFlipFlop, RegN at width 5, and RegN at width 32.
-- Instantiating RegN twice at different widths is itself part of the proof
-- that your generic works.
--
-- REQUIRED, at least 6 checked vectors, and they must include:
--
--   [required] the EDGE vector: toggle D several times BETWEEN two rising
--              edges and prove Q moves only once. Without this you have not
--              shown the design is edge-triggered rather than transparent.
--   [required] asynchronous reset asserted BETWEEN edges (not on one). If your
--              reset only works when the clock moves, it is not asynchronous.
--   [required] an edge with Ld = '0', proving the register holds.
--   [required] a 32-bit pattern that is neither all-zeros nor all-ones.
--
-- NEW THIS WEEK - the clock process. It must contain a 'wait', or the
-- simulation hangs at time zero. Change stimulus AFTER falling edges, never
-- on a rising edge: real flip-flops need the data stable before the edge
-- (setup time), and simulating a setup violation gives meaningless results.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab2 is
end entity tb_Lab2;

architecture test of tb_Lab2 is

    constant PERIOD : time := 20 ns;

    signal Clk : std_logic := '0';
    signal Clr : std_logic := '0';          -- for the flip-flop
    signal Rst : std_logic := '0';          -- for the registers
    signal Ld  : std_logic := '0';

    -- flip-flop
    signal Dff  : std_logic := '0';
    signal Qff  : std_logic;

    -- 5-bit register
    signal D5  : std_logic_vector(4 downto 0)  := (others => '0');
    signal Q5  : std_logic_vector(4 downto 0);

    -- 32-bit register
    signal D32 : std_logic_vector(31 downto 0) := (others => '0');
    signal Q32 : std_logic_vector(31 downto 0);

    signal running : boolean := true;

begin

    ----------------------------------------------------------------------------
    -- Devices under test
    ----------------------------------------------------------------------------
    DUT_FF : entity work.MSFlipFlop
        port map (D => Dff, Clk => Clk, Clr => Clr, Q => Qff);

    DUT_R5 : entity work.RegN
        generic map (N => 5)                -- no semicolon before port map
        port map (D => D5, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q5);

    DUT_R32 : entity work.RegN
        generic map (N => 32)
        port map (D => D32, Clk => Clk, Ld => Ld, Rst => Rst, Q => Q32);

    ----------------------------------------------------------------------------
    -- Clock generator
    ----------------------------------------------------------------------------
    clock_gen : process
    begin
        while running loop
            Clk <= '0'; wait for PERIOD / 2;
            Clk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    ----------------------------------------------------------------------------
    -- Stimulus and checking
    ----------------------------------------------------------------------------
    stimulus : process

        variable errors : natural := 0;

        procedure checkff (expected : in std_logic; msg : in string) is
        begin
            if Qff /= expected then
                report "FAIL (FF): " & msg &
                       " - expected " & std_logic'image(expected) &
                       ", got "       & std_logic'image(Qff)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure checkff;

        procedure check5 (expected : in std_logic_vector(4 downto 0);
                          msg      : in string) is
        begin
            if Q5 /= expected then
                report "FAIL (5-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check5;

        procedure check32 (expected : in std_logic_vector(31 downto 0);
                           msg      : in string) is
        begin
            if Q32 /= expected then
                report "FAIL (32-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check32;

    begin

        ------------------------------------------------------------------------
        -- Reset everything, mid-period, to prove the reset is asynchronous
        ------------------------------------------------------------------------
        Clr <= '1'; Rst <= '1'; Ld <= '1';
        Dff <= '1'; D5 <= "11111"; D32 <= (others => '1');
        wait for 3 ns;
        checkff('0', "async clear acts immediately");
        -- TODO: add the matching 5-bit and 32-bit checks


        Clr <= '0'; Rst <= '0';

        ------------------------------------------------------------------------
        -- Load at a rising edge
        ------------------------------------------------------------------------
        wait until falling_edge(Clk);
        Dff <= '1'; D5 <= "10101"; D32 <= x"DEADBEEF";
        wait until rising_edge(Clk);
        wait for 1 ns;
        -- TODO: check all three loaded


        ------------------------------------------------------------------------
        -- THE EDGE VECTOR: toggle between edges, prove Q moves only once
        ------------------------------------------------------------------------
        wait until falling_edge(Clk);
        Dff <= '0'; wait for 2 ns;
        Dff <= '1'; wait for 2 ns;
        Dff <= '0'; wait for 2 ns;
        -- TODO: check Qff is STILL '1' - it ignored all of that


        wait until rising_edge(Clk);
        wait for 1 ns;
        -- TODO: check Qff is now '0' - it took the LAST value before the edge


        ------------------------------------------------------------------------
        -- An edge with Ld = '0': the registers must hold
        ------------------------------------------------------------------------
        -- TODO


        ------------------------------------------------------------------------
        -- Verdict - do not delete, this is what the TA reads
        ------------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 2: all checks passed." severity note;
        else
            report "FAILED - Lab 2: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
