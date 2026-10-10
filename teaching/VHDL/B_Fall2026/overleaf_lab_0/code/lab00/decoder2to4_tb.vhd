--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 3 - self-checking testbench
-- 5 vectors, 10 ns each (ends at 50 ns): the disabled row first, then every
-- address with the decoder enabled.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4_tb is
end entity decoder2to4_tb;

architecture test of decoder2to4_tb is

    signal E, A1, A0 : std_logic := '0';
    signal D         : std_logic_vector(3 downto 0);

begin

    dut : entity work.decoder2to4
        port map ( E => E, A1 => A1, A0 => A0, D => D );

    stimulus : process
        variable errors : natural := 0;

        procedure check (expected : in std_logic_vector(3 downto 0);
                         msg      : in string) is
        begin
            if D /= expected then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;
    begin
        E <= '0';                          wait for 10 ns;
        check("0000", "row 0: E=0 must disable every output");

        E <= '1'; A1 <= '0'; A0 <= '0';    wait for 10 ns;
        check("0001", "row 1: A=00 selects D(0)");

        A1 <= '0'; A0 <= '1';              wait for 10 ns;
        check("0010", "row 2: A=01 selects D(1)");

        A1 <= '1'; A0 <= '0';              wait for 10 ns;
        check("0100", "row 3: A=10 selects D(2)");

        A1 <= '1'; A0 <= '1';              wait for 10 ns;
        check("1000", "row 4: A=11 selects D(3)");

        if errors = 0 then
            report "PASS - decoder2to4: all 5 rows correct" severity note;
        else
            report "FAILED - decoder2to4: " & integer'image(errors) &
                   " row(s) wrong" severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
