--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1, Example 1 - Testbench for majority-of-three (from Lab 0)
--
-- The circuit is one you already trust. That is the point: today you are
-- learning the TOOL FLOW, not the circuit. Never learn a tool and a circuit
-- at the same time - when something breaks you will not know which one is wrong.
--
-- Exhaustive: 3 inputs, so 8 rows, so 8 vectors. Whenever a table is small
-- enough to enumerate completely, enumerate it completely.
--
--   #  A B C || Y     minterm
--   0  0 0 0 || 0
--   1  0 0 1 || 0
--   2  0 1 0 || 0
--   3  0 1 1 || 1     m3
--   4  1 0 0 || 0
--   5  1 0 1 || 1     m5
--   6  1 1 0 || 1     m6
--   7  1 1 1 || 1     m7
--
--   (1) canonical   Y = Sm(3,5,6,7) = A'BC + AB'C + ABC' + ABC
--   (2) simplified  Y = AB + AC + BC        [each pair absorbs ABC]
--   (3) VHDL        Y <= (A and B) or (A and C) or (B and C);
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity majority3_tb is
end entity majority3_tb;

architecture test of majority3_tb is

    signal A, B, C : std_logic := '0';
    signal Y       : std_logic;

    -- The truth table, as data. Driving a testbench from a table instead of
    -- hand-written blocks is a habit that pays off enormously by Lab 11.
    type vector_t is record
        a, b, c : std_logic;
        y       : std_logic;
    end record;

    type vector_array is array (natural range <>) of vector_t;

    constant VECTORS : vector_array := (
        ('0','0','0','0'),      -- row 0
        ('0','0','1','0'),      -- row 1
        ('0','1','0','0'),      -- row 2
        ('0','1','1','1'),      -- row 3
        ('1','0','0','0'),      -- row 4
        ('1','0','1','1'),      -- row 5
        ('1','1','0','1'),      -- row 6
        ('1','1','1','1')       -- row 7
    );

begin

    DUT : entity work.majority3
        port map (A => A, B => B, C => C, Y => Y);

    stimulus : process
        variable errors : natural := 0;
    begin

        for i in VECTORS'range loop
            A <= VECTORS(i).a;
            B <= VECTORS(i).b;
            C <= VECTORS(i).c;
            wait for 10 ns;

            if Y /= VECTORS(i).y then
                report "FAIL: row " & integer'image(i) &
                       " - expected " & std_logic'image(VECTORS(i).y) &
                       ", got "       & std_logic'image(Y)
                    severity error;
                errors := errors + 1;
            end if;
        end loop;

        if errors = 0 then
            report "PASS - majority3: all 8 rows correct." severity note;
        else
            report "FAILED - majority3: " & integer'image(errors) &
                   " of 8 rows wrong." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
