--------------------------------------------------------------------------------
-- EE 362 - Lab 3, Example 3 - Watching a latch appear
--
-- Both multiplexers get identical stimulus. They agree on rows 0, 1 and 2.
-- They disagree the moment Sel = "11", and the disagreement is the lesson:
--
--   Y_good goes to its defined default.
--   Y_bad  KEEPS WHATEVER IT HAD, because nothing assigned it.
--
-- The final assert is expected to FAIL. That failure is the point.
--
-- After running this, open the RTL Viewer on mux3_bad and find the latch.
-- Then remember what it looks like, because you will meet it again in Lab 10
-- when a decoder with sixteen outputs is missing its default assignments.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity latch_trap_tb is
end entity latch_trap_tb;

architecture test of latch_trap_tb is

    signal A, B, C : std_logic_vector(7 downto 0) := (others => '0');
    signal Sel     : std_logic_vector(1 downto 0) := "00";
    signal Y_good  : std_logic_vector(7 downto 0);
    signal Y_bad   : std_logic_vector(7 downto 0);

begin

    GOOD : entity work.mux3_good
        port map (A => A, B => B, C => C, Sel => Sel, Y => Y_good);

    BAD : entity work.mux3_bad
        port map (A => A, B => B, C => C, Sel => Sel, Y => Y_bad);

    stimulus : process
    begin

        A <= x"A1"; B <= x"B2"; C <= x"C3";

        -- Rows 0..2: the two agree, because every one of these rows assigns
        Sel <= "00"; wait for 10 ns;
        assert Y_good = Y_bad report "rows should agree at Sel=00" severity error;
        Sel <= "01"; wait for 10 ns;
        assert Y_good = Y_bad report "rows should agree at Sel=01" severity error;
        Sel <= "10"; wait for 10 ns;
        assert Y_good = Y_bad report "rows should agree at Sel=10" severity error;

        -- Row 3: nothing assigns Y_bad, so it holds the value from Sel="10"
        Sel <= "11"; wait for 10 ns;

        assert Y_good = x"00"
            report "the correct mux should take its defined default at Sel=11"
            severity error;

        assert Y_bad = x"00"
            report "EXPECTED FAILURE: mux3_bad held its previous value at " &
                   "Sel=11 instead of taking a default. Nothing assigned it, " &
                   "so it remembered - that is an inferred latch."
            severity error;

        report "Compare Y_good and Y_bad from t = 30 ns onward, then open the " &
               "RTL Viewer on mux3_bad and find the latch."
            severity note;

        wait;
    end process stimulus;

end architecture test;
