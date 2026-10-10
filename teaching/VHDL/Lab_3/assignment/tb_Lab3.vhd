--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- COVERAGE ARGUMENT FOR A TYPE C TABLE - read this before you write vectors.
--
-- You cannot test 2^65 input combinations, and you do not need to. The
-- specification has four rows, so the argument is:
--
--     exhaustive on the SELECTOR, distinct patterns on the DATA
--
-- "Distinct patterns" matters. If A, B and C all carry the same value, then a
-- multiplexer that ignores its selector entirely and always returns A passes
-- every check. Give each input a value only it has (x"A1", x"B2", x"C3"), and
-- a wrong selection is impossible to miss.
--
-- REQUIRED, at least 6 checked vectors, including all of:
--   [required] every selector value on MUX3x32, INCLUDING Sel = "11"
--   [required] a NO-LATCH check: hold the selector, change the selected input,
--              and prove the output moves immediately. A latched output would
--              keep the old value - and a latch is exactly what you get if you
--              forget row 3.
--   [required] at least one check on a 5-bit mux, to prove the generic works at
--              a width other than 32
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab3 is
end entity tb_Lab3;

architecture test of tb_Lab3 is

    -- 32-bit, 3-to-1  (DinMUX)
    signal A32, B32, C32 : std_logic_vector(31 downto 0) := (others => '0');
    signal Sel2          : std_logic_vector(1 downto 0)  := "00";
    signal Y32           : std_logic_vector(31 downto 0);

    -- 32-bit, 2-to-1  (ALUinMUX)
    signal Sel1          : std_logic := '0';
    signal Y32b          : std_logic_vector(31 downto 0);

    -- 5-bit, 2-to-1   (DselMUX)
    signal A5, B5        : std_logic_vector(4 downto 0)  := (others => '0');
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

        procedure check32 (got, expected : in std_logic_vector(31 downto 0);
                           msg : in string) is
        begin
            if got /= expected then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check32;

        procedure check5 (got, expected : in std_logic_vector(4 downto 0);
                          msg : in string) is
        begin
            if got /= expected then
                report "FAIL (5-bit): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check5;

    begin

        -- Distinct patterns, so a wrong selection cannot pass
        A32 <= x"AAAAAAA1"; B32 <= x"BBBBBBB2"; C32 <= x"CCCCCCC3";
        A5  <= "10101";     B5  <= "01010";

        ------------------------------------------------------------------------
        -- MUX3x32: exhaustive on the selector
        ------------------------------------------------------------------------
        Sel2 <= "00"; wait for 10 ns;
        check32(Y32, x"AAAAAAA1", "row 0: Sel=00 selects A");

        Sel2 <= "01"; wait for 10 ns;
        -- TODO: check row 1

        -- TODO: check row 2

        -- TODO: check row 3 - Sel = "11" must give the DEFINED DEFAULT.
        --       This is the check that catches a missing row 3, i.e. a latch.


        ------------------------------------------------------------------------
        -- NO-LATCH check: hold the selector, change the selected input
        ------------------------------------------------------------------------
        Sel2 <= "01"; wait for 10 ns;
        B32  <= x"5E5E5E5E"; wait for 10 ns;
        -- TODO: check the output followed B32 immediately


        ------------------------------------------------------------------------
        -- The generic at a second width
        ------------------------------------------------------------------------
        -- TODO: check MUX2x5 for both values of Sel1


        ------------------------------------------------------------------------
        -- Verdict - do not delete
        ------------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 3: all checks passed." severity note;
        else
            report "FAILED - Lab 3: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
