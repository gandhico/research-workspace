--------------------------------------------------------------------------------
-- EE 362 - Lab 0 Practice P3 - testbench
-- 8 addresses x E in {0,1} = 16 vectors.
--
-- The expectation is COMPUTED, not typed as a table of literals:
--     E = '0'  ->  D = all zeros, for EVERY address
--     E = '1'  ->  D = 1 shifted left by the address
--
-- Driving all eight addresses with E = '0' is the check that the class
-- example failed: that version ignored E entirely and still asserted an
-- output. A testbench that only exercises E = '1' passes it.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_decoder3to8 is
end entity tb_decoder3to8;

architecture test of tb_decoder3to8 is
    signal E, A2, A1, A0 : std_logic := '0';
    signal Db, Ds        : std_logic_vector(7 downto 0);
begin

    DUT_B : entity work.decoder3to8(behavioral)
        port map ( E => E, A2 => A2, A1 => A1, A0 => A0, D => Db );

    DUT_S : entity work.decoder3to8(structural)
        port map ( E => E, A2 => A2, A1 => A1, A0 => A0, D => Ds );

    stimulus : process
        variable av     : std_logic_vector(2 downto 0);
        variable want   : std_logic_vector(7 downto 0);
        variable hot    : natural;
        variable errors : natural := 0;
    begin
        for ev in 0 to 1 loop
            for a in 0 to 7 loop
                av := std_logic_vector(to_unsigned(a, 3));
                if ev = 1 then E <= '1'; else E <= '0'; end if;
                A2 <= av(2);  A1 <= av(1);  A0 <= av(0);
                wait for 10 ns;

                if ev = 0 then
                    want := (others => '0');
                else
                    want := std_logic_vector(shift_left(to_unsigned(1, 8), a));
                end if;

                if Db /= want then
                    report "FAIL beh: E=" & integer'image(ev) &
                           " A=" & integer'image(a) severity error;
                    errors := errors + 1;
                end if;
                if Ds /= want then
                    report "FAIL str: E=" & integer'image(ev) &
                           " A=" & integer'image(a) severity error;
                    errors := errors + 1;
                end if;

                -- one-hot invariant: exactly one bit set when enabled
                hot := 0;
                for k in 0 to 7 loop
                    if Db(k) = '1' then hot := hot + 1; end if;
                end loop;
                if (ev = 1 and hot /= 1) or (ev = 0 and hot /= 0) then
                    report "FAIL one-hot: E=" & integer'image(ev) &
                           " A=" & integer'image(a) &
                           " bits set = " & integer'image(hot) severity error;
                    errors := errors + 1;
                end if;
            end loop;
        end loop;

        if errors = 0 then
            report "PASS - decoder3to8: 48 checks passed (16 vectors x 3)." severity note;
        else
            report "FAILED - decoder3to8: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;
        wait;
    end process stimulus;

end architecture test;
