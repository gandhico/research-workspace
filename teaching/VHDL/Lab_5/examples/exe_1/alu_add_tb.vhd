--------------------------------------------------------------------------------
-- EE 362 - Lab 5, Example 1 - Testbench for one function unit
--
-- COVERAGE FOR ARITHMETIC. You cannot test 2^64 input pairs. The argument is
-- not "exhaustive on the selector" as it was in Lab 3 - there is no selector
-- here. For arithmetic the argument is BOUNDARIES:
--
--     zero, one, the largest positive, the most negative, and the crossings
--     between them
--
-- Bugs in arithmetic hardware live at boundaries, not in the middle. An adder
-- that works for 3 + 4 and fails at 0x7FFFFFFF + 1 is the normal kind of broken.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity alu_add_tb is
end entity alu_add_tb;

architecture test of alu_add_tb is

    signal Ain, Bin, Rout : std_logic_vector(31 downto 0) := (others => '0');
    signal Zero, Neg, Cout : std_logic;

begin

    DUT : entity work.alu_add
        port map (Ain => Ain, Bin => Bin, Rout => Rout,
                  Zero => Zero, Neg => Neg, Cout => Cout);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wr : in std_logic_vector(31 downto 0);
                         wz, wn, wc : in std_logic;
                         msg : in string) is
        begin
            if Rout /= wr then
                report "FAIL (result): " & msg severity error;
                errors := errors + 1;
            end if;
            if Zero /= wz then
                report "FAIL (Zero flag): " & msg severity error;
                errors := errors + 1;
            end if;
            if Neg /= wn then
                report "FAIL (Neg flag): " & msg severity error;
                errors := errors + 1;
            end if;
            if Cout /= wc then
                report "FAIL (Cout): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Boundary: zero plus zero. The only case where Zero should be '1'.
        Ain <= x"00000000"; Bin <= x"00000000"; wait for 10 ns;
        check(x"00000000", '1', '0', '0', "1. 0 + 0 = 0, Zero set");

        -- Ordinary small case
        Ain <= x"00000003"; Bin <= x"00000004"; wait for 10 ns;
        check(x"00000007", '0', '0', '0', "2. 3 + 4 = 7");

        -- Adding to the most negative number
        Ain <= x"80000000"; Bin <= x"00000001"; wait for 10 ns;
        check(x"80000001", '0', '1', '0', "3. most negative + 1, Neg stays set");

        -- Boundary: largest positive plus one. In SIGNED terms this overflows
        -- into the negative range - the result reads as the most negative
        -- number. The adder is not wrong; the interpretation changed.
        Ain <= x"7FFFFFFF"; Bin <= x"00000001"; wait for 10 ns;
        check(x"80000000", '0', '1', '0', "4. 0x7FFFFFFF + 1 wraps, Neg set");

        -- Boundary: the carry out. -1 + 1 in two's complement is
        -- 0xFFFFFFFF + 1 = 0x00000000 with a carry out of the top bit.
        Ain <= x"FFFFFFFF"; Bin <= x"00000001"; wait for 10 ns;
        check(x"00000000", '1', '0', '1', "5. -1 + 1 = 0 with carry out");

        -- Two negatives
        Ain <= x"FFFFFFFF"; Bin <= x"FFFFFFFF"; wait for 10 ns;
        check(x"FFFFFFFE", '0', '1', '1', "6. -1 + -1 = -2, carry out set");

        if errors = 0 then
            report "PASS - alu_add: all boundary cases correct." severity note;
        else
            report "FAILED - alu_add: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
