--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 5 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- The 'op' procedure below applies one operation and checks the result in a
-- single line. Use it - sixteen operations tested by hand would be 200 lines
-- of near-identical code, and you would get bored and stop checking properly.
--
--     op(ALU_FUNC_ADD, x"00000003", x"00000004", "00000", x"00000007", "ADD 3+4");
--         function       Ain          Bin        Shft     expected     message
--
-- REQUIRED: at least THREE checked vectors per implemented operation, and your
-- vector set MUST include all of these, because each one catches a specific
-- wrong implementation that would otherwise pass:
--
--   [required] SRA on a NEGATIVE number, e.g. 0xFFFFFFF8 >> 1 = 0xFFFFFFFC.
--              An SRA written as an SRL passes every positive-value test.
--   [required] SOLS and SOLU on the SAME pair, 0xFFFFFFFF and 0x00000001.
--              Signed says 1 (-1 < 1). Unsigned says 0 (4294967295 > 1).
--              If your two answers match, one of them is wrong.
--   [required] a result of zero produced by something OTHER than the adder,
--              proving your Zero flag follows the selected result (Example 2).
--   [required] SUB producing a negative result, to exercise the Neg flag.
--   [required] one unimplemented function code, proving 'when others' gives a
--              defined value rather than a latch.
--
-- COVERAGE ARGUMENT FOR ARITHMETIC
--   You cannot test 2^64 operand pairs. Test BOUNDARIES instead: zero, one,
--   the largest positive (0x7FFFFFFF), the most negative (0x80000000), and -1
--   (0xFFFFFFFF). Arithmetic bugs live at boundaries, not in the middle.
--   Write that argument in your report - it is Section 5.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.ALU_Pkg.all;

entity tb_Lab5 is
end entity tb_Lab5;

architecture test of tb_Lab5 is

    signal Ain, Bin : std_logic_vector(31 downto 0) := (others => '0');
    signal Func     : std_logic_vector(4 downto 0)  := ALU_FUNC_ADD;
    signal Shft     : std_logic_vector(4 downto 0)  := (others => '0');
    signal Rout     : std_logic_vector(31 downto 0);
    signal Zero, Neg : std_logic;

begin

    DUT : entity work.ALU
        port map (Ain => Ain, Bin => Bin, Func => Func, Shft => Shft,
                  Rout => Rout, Zero => Zero, Neg => Neg);

    stimulus : process

        variable errors : natural := 0;

        -- Apply one operation and check the result. One line per vector.
        procedure op (f : in std_logic_vector(4 downto 0);
                      a, b : in std_logic_vector(31 downto 0);
                      s : in std_logic_vector(4 downto 0);
                      want : in std_logic_vector(31 downto 0);
                      msg : in string) is
        begin
            Func <= f; Ain <= a; Bin <= b; Shft <= s;
            wait for 10 ns;
            if Rout /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure op;

        -- Check the flags produced by the operation you just applied.
        procedure flags (wz, wn : in std_logic; msg : in string) is
        begin
            if Zero /= wz then
                report "FAIL (Zero): " & msg severity error;
                errors := errors + 1;
            end if;
            if Neg /= wn then
                report "FAIL (Neg): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure flags;

        constant Z5 : std_logic_vector(4 downto 0) := "00000";   -- no shift

    begin

        ----------------------------------------------------------------------
        -- Arithmetic
        ----------------------------------------------------------------------
        op(ALU_FUNC_ADD, x"00000003", x"00000004", Z5, x"00000007", "ADD 3+4");

        -- This one FAILS when you first run the project, and it is meant to.
        -- ADD is given to you, so the vector above passes immediately and tells
        -- you nothing. SUB is not written yet, so this vector reports a failure
        -- until you implement it. That is what a testbench is for: it should be
        -- red until the design is right, not green until you look closely.
        op(ALU_FUNC_SUB, x"00000007", x"00000004", Z5, x"00000003", "SUB 7-4");

        -- TODO: ADD at a boundary - try -1 + 1, and check the Zero flag


        -- TODO: SUB, including one that produces a NEGATIVE result,
        --       then check the Neg flag


        -- TODO: NEG


        ----------------------------------------------------------------------
        -- Bitwise logic - three vectors each.
        -- Choose operands where a wrong operator gives a DIFFERENT answer.
        -- x"F0F0FF00" against x"FF00F0F0" works well; x"FFFFFFFF" against
        -- x"FFFFFFFF" does not, because AND, OR and XNOR all agree on it.
        ----------------------------------------------------------------------
        -- TODO: AND, NAND, OR, NOR, XOR, XNOR, NOT
        --       (remember NOT operates on Bin, not Ain)


        ----------------------------------------------------------------------
        -- Shifts
        ----------------------------------------------------------------------
        -- TODO: SLL, SLA, SRL on a positive value

        -- TODO: *** REQUIRED *** SRA on a NEGATIVE value.
        --       0xFFFFFFF8 >> 1 must give 0xFFFFFFFC, not 0x7FFFFFFC.
        --       Also run SRL on the same value so the two answers sit side by
        --       side in your waveform - that pair is a report figure.


        -- TODO: shift by zero


        ----------------------------------------------------------------------
        -- Set on less than
        ----------------------------------------------------------------------
        -- TODO: *** REQUIRED *** SOLS and SOLU on Ain=0xFFFFFFFF, Bin=0x00000001.
        --       They must give DIFFERENT answers.


        -- TODO: a case where the operands are equal - equal is not less


        ----------------------------------------------------------------------
        -- The default
        ----------------------------------------------------------------------
        -- TODO: an unimplemented code, e.g. "11111"


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 5: all checks passed." severity note;
        else
            report "FAILED - Lab 5: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
