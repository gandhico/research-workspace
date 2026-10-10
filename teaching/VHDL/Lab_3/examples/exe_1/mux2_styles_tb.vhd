--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 3, Example 1 - One testbench, three multiplexers
--
-- Every check asserts that all three styles agree. If they are really the same
-- circuit described three ways, no check can fail.
--
-- Then open the RTL Viewer on all three. The pictures are the same too - unlike
-- Lab 2, where structural and behavioural gave different pictures. Here the
-- difference is purely how the source reads to a human.
--
-- 'when others' is not optional padding. std_logic has NINE values, not two:
-- 'U','X','0','1','Z','W','L','H','-'. Any case or selected assignment must
-- cover all of them, and the compiler will refuse the file if it does not.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity mux2_styles_tb is
end entity mux2_styles_tb;

architecture test of mux2_styles_tb is

    signal A, B, Sel : std_logic := '0';
    signal Y1, Y2, Y3 : std_logic;

begin

    D1 : entity work.mux2_whenelse    port map (A => A, B => B, Sel => Sel, Y => Y1);
    D2 : entity work.mux2_withselect  port map (A => A, B => B, Sel => Sel, Y => Y2);
    D3 : entity work.mux2_case        port map (A => A, B => B, Sel => Sel, Y => Y3);

    stimulus : process

        variable errors : natural := 0;

        procedure check (expected : in std_logic; msg : in string) is
        begin
            if Y1 /= expected or Y2 /= expected or Y3 /= expected then
                report "FAIL: " & msg &
                       " - expected " & std_logic'image(expected) &
                       "; when/else=" & std_logic'image(Y1) &
                       " with/select=" & std_logic'image(Y2) &
                       " case=" & std_logic'image(Y3)
                    severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Exhaustive on Sel, and two distinct data patterns for each value,
        -- so that "always returns A" and "always returns B" both get caught.
        A <= '0'; B <= '1'; Sel <= '0'; wait for 10 ns;
        check('0', "Sel=0 selects A (A=0,B=1)");

        A <= '1'; B <= '0'; Sel <= '0'; wait for 10 ns;
        check('1', "Sel=0 selects A (A=1,B=0)");

        A <= '0'; B <= '1'; Sel <= '1'; wait for 10 ns;
        check('1', "Sel=1 selects B (A=0,B=1)");

        A <= '1'; B <= '0'; Sel <= '1'; wait for 10 ns;
        check('0', "Sel=1 selects B (A=1,B=0)");

        -- No-latch check: hold Sel, change the selected input, output must move
        -- immediately. A latched output would keep the old value.
        A <= '1'; B <= '1'; Sel <= '0'; wait for 10 ns;
        check('1', "no latch: output follows A while Sel is held");
        A <= '0';                        wait for 10 ns;
        check('0', "no latch: output follows a change of A");

        if errors = 0 then
            report "PASS - all three styles agree on every vector." severity note;
        else
            report "FAILED - " & integer'image(errors) & " disagreement(s)."
                severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
