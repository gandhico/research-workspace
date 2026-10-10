--------------------------------------------------------------------------------
-- EE 362 - Lab 3, Example 2 - Testbench for the 4-to-1 multiplexer
--
-- Coverage argument for a Type C table: exhaustive on the SELECTOR, symbolic
-- on the data. Four selector values, each checked with a data pattern that is
-- unique to one input, so "always returns A" cannot pass.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity mux4_tb is
end entity mux4_tb;

architecture test of mux4_tb is

    signal A, B, C, D : std_logic_vector(7 downto 0) := (others => '0');
    signal Sel        : std_logic_vector(1 downto 0) := "00";
    signal Y          : std_logic_vector(7 downto 0);

begin

    DUT : entity work.mux4
        generic map (W => 8)
        port map (A => A, B => B, C => C, D => D, Sel => Sel, Y => Y);

    stimulus : process

        variable errors : natural := 0;

        procedure check (expected : in std_logic_vector(7 downto 0);
                         msg      : in string) is
        begin
            if Y /= expected then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Four distinct patterns, so each row can only pass for the right input
        A <= x"A1"; B <= x"B2"; C <= x"C3"; D <= x"D4";

        Sel <= "00"; wait for 10 ns; check(x"A1", "row 0: Sel=00 selects A");
        Sel <= "01"; wait for 10 ns; check(x"B2", "row 1: Sel=01 selects B");
        Sel <= "10"; wait for 10 ns; check(x"C3", "row 2: Sel=10 selects C");
        Sel <= "11"; wait for 10 ns; check(x"D4", "row 3: Sel=11 selects D");

        -- No-latch check: hold the selector, change the selected input.
        Sel <= "01"; wait for 10 ns;
        B   <= x"5E"; wait for 10 ns;
        check(x"5E", "no latch: output follows B while Sel is held");

        if errors = 0 then
            report "PASS - mux4: all rows correct." severity note;
        else
            report "FAILED - mux4: " & integer'image(errors) & " row(s) wrong."
                severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
