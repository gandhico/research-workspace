--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- You must supply AT LEAST 6 checked vectors, and they must include:
--
--   [required] the HOLD vector: with En = '0', change D and prove Q does NOT
--              follow. Without this vector you have not tested that your
--              design is memory at all - a plain wire passes every other test.
--   [required] clear asserted while the latch is transparent
--   [required] clear asserted while the latch is holding
--   [required] at least one vector on TransLatch8 with a pattern that is not
--              all-zeros and not all-ones (e.g. x"A5"), so a stuck bit shows up
--
-- Fill in the marked sections. The structure is already correct - do not
-- rearrange it. Every testbench this semester looks like this.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_TransLatch is
end entity tb_TransLatch;

architecture test of tb_TransLatch is

    -- 1-bit DUT signals
    signal D   : std_logic := '0';
    signal En  : std_logic := '0';
    signal Clr : std_logic := '0';
    signal Q   : std_logic;

    -- 8-bit DUT signals
    signal D8  : std_logic_vector(7 downto 0) := (others => '0');
    signal Q8  : std_logic_vector(7 downto 0);

begin

    ----------------------------------------------------------------------------
    -- Devices under test. Named association ( formal => actual ) - always.
    ----------------------------------------------------------------------------
    DUT1 : entity work.TransLatch
        port map (
            D   => D,
            En  => En,
            Clr => Clr,
            Q   => Q
        );

    DUT8 : entity work.TransLatch8
        port map (
            D   => D8,
            En  => En,                      -- both latches share the controls
            Clr => Clr,
            Q   => Q8
        );

    ----------------------------------------------------------------------------
    -- Stimulus and checking
    ----------------------------------------------------------------------------
    stimulus : process

        variable errors : natural := 0;

        procedure check1 (expected : in std_logic; msg : in string) is
        begin
            if Q /= expected then
                report "FAIL: " & msg &
                       " - expected " & std_logic'image(expected) &
                       ", got "       & std_logic'image(Q)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure check1;

        procedure check8 (expected : in std_logic_vector(7 downto 0);
                          msg      : in string) is
        begin
            if Q8 /= expected then
                report "FAIL (8-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check8;

    begin

        ------------------------------------------------------------------------
        -- Row 0 : asynchronous clear
        ------------------------------------------------------------------------
        Clr <= '1'; En <= '0'; D <= '1'; D8 <= x"FF";
        wait for 10 ns;
        check1('0', "row 0: clear forces Q low");
        -- TODO: add the matching 8-bit check


        ------------------------------------------------------------------------
        -- Rows 2 and 3 : transparent
        ------------------------------------------------------------------------
        Clr <= '0'; En <= '1'; D <= '1'; D8 <= x"A5";
        wait for 10 ns;
        -- TODO: check that Q is '1' and Q8 is x"A5"


        ------------------------------------------------------------------------
        -- Row 1 : HOLD  <-- the vector that proves this is memory
        ------------------------------------------------------------------------
        En <= '0';
        wait for 10 ns;
        D  <= '0'; D8 <= x"00";             -- change the data while holding
        wait for 10 ns;
        -- TODO: check that Q is STILL '1' and Q8 is STILL x"A5"


        ------------------------------------------------------------------------
        -- Clear while holding
        ------------------------------------------------------------------------
        -- TODO


        ------------------------------------------------------------------------
        -- Clear while transparent
        ------------------------------------------------------------------------
        -- TODO


        ------------------------------------------------------------------------
        -- Verdict - do not delete this block, it is what the TA reads
        ------------------------------------------------------------------------
        if errors = 0 then
            report "PASS - TransLatch: all checks passed." severity note;
        else
            report "FAILED - TransLatch: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
