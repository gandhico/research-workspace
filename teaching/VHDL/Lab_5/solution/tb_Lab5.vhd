--------------------------------------------------------------------------------
-- EE 362 - Lab 5 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 26 checks. Every implemented operation at least once, with boundary values
-- where they exist, and the three pairs that separate a correct ALU from a
-- plausible-looking wrong one:
--
--   SRA vs SRL on a negative number
--   SOLS vs SOLU on the same operand pair
--   flags computed on the selected result, not on the adder
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

        constant Z5 : std_logic_vector(4 downto 0) := "00000";

    begin

        ----------------------------------------------------------------------
        -- Arithmetic
        ----------------------------------------------------------------------
        op(ALU_FUNC_ADD, x"00000003", x"00000004", Z5, x"00000007", "1. ADD 3+4");
        op(ALU_FUNC_ADD, x"FFFFFFFF", x"00000001", Z5, x"00000000", "2. ADD -1+1 = 0");
        flags('1', '0', "2. ADD result zero sets Zero");

        op(ALU_FUNC_SUB, x"00000007", x"00000004", Z5, x"00000003", "3. SUB 7-4");
        op(ALU_FUNC_SUB, x"00000004", x"00000007", Z5, x"FFFFFFFD", "4. SUB 4-7 = -3");
        flags('0', '1', "4. negative result sets Neg");

        op(ALU_FUNC_NEG, x"00000000", x"00000005", Z5, x"FFFFFFFB", "5. NEG 5 = -5");
        op(ALU_FUNC_NEG, x"00000000", x"FFFFFFFB", Z5, x"00000005", "6. NEG -5 = 5");

        ----------------------------------------------------------------------
        -- Bitwise logic. Operands chosen so a wrong operator gives a visibly
        -- different answer, not an accidentally-equal one.
        ----------------------------------------------------------------------
        op(ALU_FUNC_AND,  x"F0F0FF00", x"FF00F0F0", Z5, x"F000F000", "7. AND");
        op(ALU_FUNC_NAND, x"F0F0FF00", x"FF00F0F0", Z5, x"0FFF0FFF", "8. NAND");
        op(ALU_FUNC_OR,   x"F0F0FF00", x"FF00F0F0", Z5, x"FFF0FFF0", "9. OR");
        op(ALU_FUNC_NOR,  x"F0F0FF00", x"FF00F0F0", Z5, x"000F000F", "10. NOR");
        op(ALU_FUNC_XOR,  x"F0F0FF00", x"FF00F0F0", Z5, x"0FF00FF0", "11. XOR");
        op(ALU_FUNC_XNOR, x"F0F0FF00", x"FF00F0F0", Z5, x"F00FF00F", "12. XNOR");
        op(ALU_FUNC_NOT,  x"00000000", x"F0F0FF00", Z5, x"0F0F00FF", "13. NOT operates on Bin");

        ----------------------------------------------------------------------
        -- Shifts
        ----------------------------------------------------------------------
        op(ALU_FUNC_SLL, x"0000000F", x"00000000", "00010", x"0000003C", "14. SLL by 2");
        op(ALU_FUNC_SLA, x"0000000F", x"00000000", "00010", x"0000003C", "15. SLA = SLL");
        op(ALU_FUNC_SRL, x"0000000F", x"00000000", "00010", x"00000003", "16. SRL by 2");

        -- Positive value: SRL and SRA agree. Proves nothing on its own.
        op(ALU_FUNC_SRA, x"0000000F", x"00000000", "00010", x"00000003",
           "17. SRA on a positive value agrees with SRL");

        -- THE VECTORS THAT CATCH SRA-WRITTEN-AS-SRL
        op(ALU_FUNC_SRA, x"FFFFFFF8", x"00000000", "00001", x"FFFFFFFC",
           "18. SRA: -8 >> 1 = -4 (SRL would give 0x7FFFFFFC)");
        op(ALU_FUNC_SRL, x"FFFFFFF8", x"00000000", "00001", x"7FFFFFFC",
           "19. SRL on the same value fills with zero");
        op(ALU_FUNC_SRA, x"FFFFFFFF", x"00000000", "11111", x"FFFFFFFF",
           "20. SRA: -1 >> 31 is still -1");

        -- Shift by zero is a real case the CPU issues
        op(ALU_FUNC_SLL, x"12345678", x"00000000", Z5, x"12345678",
           "21. shift by 0 changes nothing");

        ----------------------------------------------------------------------
        -- Set on less than. Same operands, different answers.
        ----------------------------------------------------------------------
        op(ALU_FUNC_SOLS, x"FFFFFFFF", x"00000001", Z5, x"00000001",
           "22. SOLS: -1 < 1 signed -> 1");
        op(ALU_FUNC_SOLU, x"FFFFFFFF", x"00000001", Z5, x"00000000",
           "23. SOLU: 4294967295 < 1 unsigned -> 0");

        op(ALU_FUNC_SOLS, x"00000001", x"00000002", Z5, x"00000001",
           "24. SOLS: 1 < 2 -> 1");
        op(ALU_FUNC_SOLS, x"00000002", x"00000002", Z5, x"00000000",
           "25. SOLS: equal is not less -> 0");
        flags('1', '0', "25. a zero result sets Zero, whatever produced it");

        ----------------------------------------------------------------------
        -- Unimplemented code must give a defined default, not a latch
        ----------------------------------------------------------------------
        op("11111", x"12345678", x"9ABCDEF0", Z5, x"00000000",
           "26. unimplemented function code gives the safe default");

        if errors = 0 then
            report "PASS - Lab 5: all 26 checks passed." severity note;
        else
            report "FAILED - Lab 5: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
