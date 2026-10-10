--------------------------------------------------------------------------------
-- EE 362 - Lab 4, Example 1 - Watching a bus resolve
--
-- Four cases, and all four matter:
--
--   nobody driving     -> 'Z'   the bus floats
--   A driving only     -> A     normal operation
--   B driving only     -> B     normal operation
--   BOTH driving       -> 'X'   contention
--
-- The last one is the point. Watch the waveform go red, and remember what
-- caused it: two drivers, one wire, disagreeing.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tristate_demo_tb is
end entity tristate_demo_tb;

architecture test of tristate_demo_tb is

    signal A, B       : std_logic := '0';
    signal SelA, SelB : std_logic := '0';
    signal BusWire    : std_logic;

begin

    DUT : entity work.bus_demo
        port map (A => A, B => B, SelA => SelA, SelB => SelB, BusWire => BusWire);

    stimulus : process

        variable errors : natural := 0;

        procedure check (want : in std_logic; msg : in string) is
        begin
            if BusWire /= want then
                report "FAIL: " & msg &
                       " - expected " & std_logic'image(want) &
                       ", got "       & std_logic'image(BusWire)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        A <= '1'; B <= '0';

        -- 1. Nobody driving: the bus floats.
        SelA <= '0'; SelB <= '0'; wait for 10 ns;
        check('Z', "1. no driver enabled -> bus floats at Z");

        -- 2. Only A drives.
        SelA <= '1'; SelB <= '0'; wait for 10 ns;
        check('1', "2. only A enabled -> bus reads A");

        -- 3. Only B drives.
        SelA <= '0'; SelB <= '1'; wait for 10 ns;
        check('0', "3. only B enabled -> bus reads B");

        -- 4. Both drive, and they disagree. Resolution gives 'X'.
        SelA <= '1'; SelB <= '1'; wait for 10 ns;
        check('X', "4. CONTENTION: two drivers disagreeing -> X");

        -- 5. Both drive, but they AGREE. No contention: the bus is fine.
        --    Worth seeing - 'X' comes from disagreement, not from two drivers.
        B <= '1'; wait for 10 ns;
        check('1', "5. two drivers that AGREE resolve cleanly");

        if errors = 0 then
            report "PASS - bus resolution behaves as the table says." severity note;
        else
            report "FAILED - " & integer'image(errors) & " check(s) failed."
                severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
