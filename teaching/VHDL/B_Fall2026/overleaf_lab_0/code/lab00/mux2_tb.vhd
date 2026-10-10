--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 2 - self-checking testbench
-- 4 vectors, 10 ns each (ends at 40 ns). In every vector D0 /= D1, so the
-- output can only be right if the multiplexer picked the correct input.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity mux2_tb is
end entity mux2_tb;

architecture test of mux2_tb is

    signal D0, D1, S : std_logic := '0';
    signal Y         : std_logic;

begin

    dut : entity work.mux2
        port map ( D0 => D0, D1 => D1, S => S, Y => Y );

    stimulus : process
        variable errors : natural := 0;

        procedure check (expected : in std_logic; msg : in string) is
        begin
            if Y /= expected then
                report "FAIL: " & msg & " - expected " & std_logic'image(expected) &
                       ", got " & std_logic'image(Y) severity error;
                errors := errors + 1;
            end if;
        end procedure check;
    begin
        D0 <= '0'; D1 <= '1'; S <= '0';  wait for 10 ns;
        check('0', "vector 1: S=0 selects D0");

        S <= '1';                        wait for 10 ns;
        check('1', "vector 2: S=1 selects D1");

        D0 <= '1'; D1 <= '0'; S <= '0';  wait for 10 ns;
        check('1', "vector 3: S=0 selects D0");

        S <= '1';                        wait for 10 ns;
        check('0', "vector 4: S=1 selects D1");

        if errors = 0 then
            report "PASS - mux2: all 4 vectors correct" severity note;
        else
            report "FAILED - mux2: " & integer'image(errors) &
                   " vector(s) wrong" severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
