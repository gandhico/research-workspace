--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P2 - testbench
-- Exhaustive: 4 select values x 16 data patterns = 64 vectors.
-- Sweeping ALL data patterns for every select is what proves the mux
-- IGNORES the three unselected inputs.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_mux4 is
end entity tb_mux4;

architecture test of tb_mux4 is
    signal D0, D1, D2, D3 : std_logic := '0';
    signal S1, S0         : std_logic := '0';
    signal Yb, Ys         : std_logic;
begin

    DUT_B : entity work.mux4(behavioral)
        port map ( D0 => D0, D1 => D1, D2 => D2, D3 => D3,
                   S1 => S1, S0 => S0, Y => Yb );

    DUT_S : entity work.mux4(structural)
        port map ( D0 => D0, D1 => D1, D2 => D2, D3 => D3,
                   S1 => S1, S0 => S0, Y => Ys );

    stimulus : process
        variable dv     : std_logic_vector(3 downto 0);
        variable sv     : std_logic_vector(1 downto 0);
        variable want   : std_logic;
        variable errors : natural := 0;
    begin
        for s in 0 to 3 loop
            sv := std_logic_vector(to_unsigned(s, 2));
            for d in 0 to 15 loop
                dv := std_logic_vector(to_unsigned(d, 4));
                D0 <= dv(0);  D1 <= dv(1);  D2 <= dv(2);  D3 <= dv(3);
                S1 <= sv(1);  S0 <= sv(0);
                wait for 5 ns;

                want := dv(s);          -- the selected input, whatever it is

                if Yb /= want then
                    report "FAIL beh: S=" & integer'image(s) &
                           " D=" & integer'image(d) &
                           " expected " & std_logic'image(want) &
                           ", got " & std_logic'image(Yb) severity error;
                    errors := errors + 1;
                end if;
                if Ys /= want then
                    report "FAIL str: S=" & integer'image(s) &
                           " D=" & integer'image(d) &
                           " expected " & std_logic'image(want) &
                           ", got " & std_logic'image(Ys) severity error;
                    errors := errors + 1;
                end if;
                if Yb /= Ys then
                    report "FAIL S=" & integer'image(s) & " D=" & integer'image(d) &
                           ": architectures disagree" severity error;
                    errors := errors + 1;
                end if;
            end loop;
        end loop;

        if errors = 0 then
            report "PASS - mux4: 192 checks passed (64 vectors x 3)." severity note;
        else
            report "FAILED - mux4: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
