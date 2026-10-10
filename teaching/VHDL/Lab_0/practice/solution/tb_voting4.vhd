--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P1 - testbench
-- Exhaustive: 16 vectors. Checks both architectures against a COMPUTED
-- expectation (count the ones), and checks the two architectures agree.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_voting4 is
end entity tb_voting4;

architecture test of tb_voting4 is
    signal A, B, C, D : std_logic := '0';
    signal Yb, Ys     : std_logic;
begin

    DUT_B : entity work.voting4(behavioral)
        port map ( A => A, B => B, C => C, D => D, Y => Yb );

    DUT_S : entity work.voting4(structural)
        port map ( A => A, B => B, C => C, D => D, Y => Ys );

    stimulus : process
        variable v      : std_logic_vector(3 downto 0);
        variable ones   : natural;
        variable want   : std_logic;
        variable errors : natural := 0;
    begin
        for i in 0 to 15 loop
            v := std_logic_vector(to_unsigned(i, 4));
            A <= v(3);  B <= v(2);  C <= v(1);  D <= v(0);
            wait for 10 ns;

            ones := 0;
            for k in 0 to 3 loop
                if v(k) = '1' then ones := ones + 1; end if;
            end loop;
            if ones >= 3 then want := '1'; else want := '0'; end if;

            if Yb /= want then
                report "FAIL beh row " & integer'image(i) &
                       ": expected " & std_logic'image(want) &
                       ", got " & std_logic'image(Yb) severity error;
                errors := errors + 1;
            end if;
            if Ys /= want then
                report "FAIL str row " & integer'image(i) &
                       ": expected " & std_logic'image(want) &
                       ", got " & std_logic'image(Ys) severity error;
                errors := errors + 1;
            end if;
            if Yb /= Ys then
                report "FAIL row " & integer'image(i) &
                       ": architectures disagree" severity error;
                errors := errors + 1;
            end if;
        end loop;

        if errors = 0 then
            report "PASS - voting4: 48 checks passed (16 vectors x 3)." severity note;
        else
            report "FAILED - voting4: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
