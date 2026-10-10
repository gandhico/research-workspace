--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - REFERENCE SOLUTION testbench  (TA only - do not publish to Canvas)
--
-- 10 checked vectors across both DUTs. Covers every row of the table, both
-- clear paths, and the hold behaviour that is the actual point of the lab.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_TransLatch is
end entity tb_TransLatch;

architecture test of tb_TransLatch is

    signal D   : std_logic := '0';
    signal En  : std_logic := '0';
    signal Clr : std_logic := '0';
    signal Q   : std_logic;

    signal D8  : std_logic_vector(7 downto 0) := (others => '0');
    signal Q8  : std_logic_vector(7 downto 0);

begin

    DUT1 : entity work.TransLatch
        port map (D => D, En => En, Clr => Clr, Q => Q);

    DUT8 : entity work.TransLatch8
        port map (D => D8, En => En, Clr => Clr, Q => Q8);

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

        -- 1. Row 0 : asynchronous clear dominates, even with D = '1'
        Clr <= '1'; En <= '0'; D <= '1'; D8 <= x"FF";
        wait for 10 ns;
        check1('0',   "1. clear forces Q low");
        check8(x"00", "1. clear forces Q8 low");

        -- 2. Rows 2/3 : transparent, data passes through
        Clr <= '0'; En <= '1'; D <= '1'; D8 <= x"A5";
        wait for 10 ns;
        check1('1',   "2. transparent, Q follows D=1");
        check8(x"A5", "2. transparent, Q8 follows D8=A5");

        -- 3. Still transparent, new data must follow immediately
        D <= '0'; D8 <= x"5A";
        wait for 10 ns;
        check1('0',   "3. transparent, Q tracks a change of D");
        check8(x"5A", "3. transparent, Q8 tracks a change of D8");

        -- 4. Load a known value, then close the latch
        D <= '1'; D8 <= x"3C";
        wait for 10 ns;
        En <= '0';
        wait for 10 ns;
        check1('1',   "4. value captured before closing");
        check8(x"3C", "4. value captured before closing (8-bit)");

        -- 5. THE HOLD VECTOR : change D while closed, Q must not move
        D <= '0'; D8 <= x"00";
        wait for 10 ns;
        check1('1',   "5. HOLD: Q survives a change of D while En=0");
        check8(x"3C", "5. HOLD: Q8 survives a change of D8 while En=0");

        -- 6. Clear while HOLDING (En = '0'): must still clear, it is asynchronous
        Clr <= '1';
        wait for 10 ns;
        check1('0',   "6. clear works while holding");
        check8(x"00", "6. clear works while holding (8-bit)");

        -- 7. Release clear while still closed: Q stays cleared
        Clr <= '0';
        wait for 10 ns;
        check1('0',   "7. releasing clear does not restore the old value");
        check8(x"00", "7. releasing clear does not restore the old value (8-bit)");

        -- 8. Reopen: Q must catch up to the current D
        En <= '1'; D <= '1'; D8 <= x"F0";
        wait for 10 ns;
        check1('1',   "8. reopening makes Q follow D again");
        check8(x"F0", "8. reopening makes Q8 follow D8 again");

        -- 9. Clear while TRANSPARENT (En = '1'): clear must still win
        Clr <= '1';
        wait for 10 ns;
        check1('0',   "9. clear beats transparency");
        check8(x"00", "9. clear beats transparency (8-bit)");

        -- 10. Release clear while transparent: Q immediately follows D again
        Clr <= '0';
        wait for 10 ns;
        check1('1',   "10. after clear releases, transparency resumes");
        check8(x"F0", "10. after clear releases, transparency resumes (8-bit)");

        if errors = 0 then
            report "PASS - TransLatch: all 20 checks passed." severity note;
        else
            report "FAILED - TransLatch: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
