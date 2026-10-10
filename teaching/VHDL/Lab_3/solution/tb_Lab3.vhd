--------------------------------------------------------------------------------
-- EE 362 - Lab 3 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 14 checks. Exhaustive on every selector, distinct data patterns, no-latch
-- checks on both mux types, and the generic exercised at widths 5 and 32.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab3 is
end entity tb_Lab3;

architecture test of tb_Lab3 is

    signal A32, B32, C32 : std_logic_vector(31 downto 0) := (others => '0');
    signal Sel2          : std_logic_vector(1 downto 0)  := "00";
    signal Y32           : std_logic_vector(31 downto 0);

    signal Sel1          : std_logic := '0';
    signal Y32b          : std_logic_vector(31 downto 0);

    signal A5, B5        : std_logic_vector(4 downto 0) := (others => '0');
    signal Y5            : std_logic_vector(4 downto 0);

begin

    DUT_3x32 : entity work.MUX3x32
        port map (A => A32, B => B32, C => C32, Sel => Sel2, Y => Y32);

    DUT_2x32 : entity work.MUX2x32
        port map (A => A32, B => B32, Sel => Sel1, Y => Y32b);

    DUT_2x5 : entity work.MUX2x5
        port map (A => A5, B => B5, Sel => Sel1, Y => Y5);

    stimulus : process

        variable errors : natural := 0;

        procedure check32 (got  : in std_logic_vector(31 downto 0);
                           want : in std_logic_vector(31 downto 0);
                           msg  : in string) is
        begin
            if got /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check32;

        procedure check5 (got  : in std_logic_vector(4 downto 0);
                          want : in std_logic_vector(4 downto 0);
                          msg  : in string) is
        begin
            if got /= want then
                report "FAIL (5-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check5;

    begin

        A32 <= x"AAAAAAA1"; B32 <= x"BBBBBBB2"; C32 <= x"CCCCCCC3";
        A5  <= "10101";     B5  <= "01010";

        -- MUX3x32, exhaustive on the selector
        Sel2 <= "00"; wait for 10 ns;
        check32(Y32, x"AAAAAAA1", "1. row 0: Sel=00 selects A");

        Sel2 <= "01"; wait for 10 ns;
        check32(Y32, x"BBBBBBB2", "2. row 1: Sel=01 selects B");

        Sel2 <= "10"; wait for 10 ns;
        check32(Y32, x"CCCCCCC3", "3. row 2: Sel=10 selects C");

        Sel2 <= "11"; wait for 10 ns;
        check32(Y32, x"00000000", "4. row 3: Sel=11 gives the defined default");

        -- No-latch on the 3-to-1: hold the selector, move the selected input
        Sel2 <= "01"; wait for 10 ns;
        check32(Y32, x"BBBBBBB2", "5. re-selecting B");
        B32 <= x"5E5E5E5E"; wait for 10 ns;
        check32(Y32, x"5E5E5E5E", "6. NO LATCH: output follows B while Sel held");
        B32 <= x"BBBBBBB2"; wait for 10 ns;

        -- The latch check that matters most: leave the selector on row 3, then
        -- change every data input. A latched design would show an old value.
        Sel2 <= "11"; wait for 10 ns;
        A32 <= x"11111111"; B32 <= x"22222222"; C32 <= x"33333333";
        wait for 10 ns;
        check32(Y32, x"00000000", "7. row 3 stays at the default when data changes");
        A32 <= x"AAAAAAA1"; B32 <= x"BBBBBBB2"; C32 <= x"CCCCCCC3";
        wait for 10 ns;

        -- MUX2x32, both selector values
        Sel1 <= '0'; wait for 10 ns;
        check32(Y32b, x"AAAAAAA1", "8. 2-to-1 32-bit: Sel=0 selects A");
        Sel1 <= '1'; wait for 10 ns;
        check32(Y32b, x"BBBBBBB2", "9. 2-to-1 32-bit: Sel=1 selects B");

        -- No-latch on the 2-to-1
        A32 <= x"0F0F0F0F"; wait for 10 ns;
        check32(Y32b, x"BBBBBBB2", "10. 2-to-1 ignores the unselected input");
        Sel1 <= '0'; wait for 10 ns;
        check32(Y32b, x"0F0F0F0F", "11. 2-to-1 follows the new A once selected");

        -- The generic at a second width
        Sel1 <= '0'; wait for 10 ns;
        check5(Y5, "10101", "12. 5-bit: Sel=0 selects A");
        Sel1 <= '1'; wait for 10 ns;
        check5(Y5, "01010", "13. 5-bit: Sel=1 selects B");
        B5 <= "11100";  wait for 10 ns;
        check5(Y5, "11100", "14. 5-bit: NO LATCH, follows B while Sel held");

        if errors = 0 then
            report "PASS - Lab 3: all 14 checks passed." severity note;
        else
            report "FAILED - Lab 3: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
