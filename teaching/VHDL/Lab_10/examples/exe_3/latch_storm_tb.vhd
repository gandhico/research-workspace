--------------------------------------------------------------------------------
-- EE 362 - Lab 10, Example 3 - Order-dependent control signals
--
-- Watch this carefully. LUI is fed to both decoders twice:
--
--   once AFTER a reset-ish unknown instruction  -> both agree
--   once AFTER an ADDI                          -> bad_decode is wrong
--
-- The instruction is IDENTICAL both times. Only the history differs.
--
-- That is what a latch in a control unit does, and it is why "it works when I
-- test it alone" tells you nothing about a decoder.
--
-- The assert on bad_decode is EXPECTED TO FAIL. That failure is the example.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity latch_storm_tb is
end entity latch_storm_tb;

architecture test of latch_storm_tb is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal CtrlGood, CtrlBad : CTRL_REC;

    -- LUI r1, 11   and   ADDI r1, r1, -1   from the Lab 12 program
    constant I_LUI  : std_logic_vector(31 downto 0) := x"3C01000B";
    constant I_ADDI : std_logic_vector(31 downto 0) := x"2021FFFF";
    constant I_NONE : std_logic_vector(31 downto 0) := x"FC000000";

begin

    DUT_GOOD : entity work.good_decode
        port map (Instr => Instr, Ctrl => CtrlGood);

    DUT_BAD : entity work.bad_decode
        port map (Instr => Instr, Ctrl => CtrlBad);

    stimulus : process
    begin

        ----------------------------------------------------------------------
        -- LUI arriving after an unrecognised instruction
        ----------------------------------------------------------------------
        Instr <= I_NONE; wait for 10 ns;
        Instr <= I_LUI;  wait for 10 ns;

        report "--- LUI, arriving after an unknown instruction ---" severity note;
        report "  good_decode IR_Xsel = " & std_logic'image(CtrlGood.IR_Xsel)
            severity note;
        report "  bad_decode  IR_Xsel = " & std_logic'image(CtrlBad.IR_Xsel)
            severity note;

        assert CtrlGood.IR_Xsel = IR_XSEL_ZERO
            report "good_decode should zero-extend for LUI" severity error;

        ----------------------------------------------------------------------
        -- THE SAME LUI, arriving after an ADDI
        ----------------------------------------------------------------------
        Instr <= I_ADDI; wait for 10 ns;
        Instr <= I_LUI;  wait for 10 ns;

        report "--- the SAME LUI, arriving after an ADDI ---" severity note;
        report "  good_decode IR_Xsel = " & std_logic'image(CtrlGood.IR_Xsel)
            severity note;
        report "  bad_decode  IR_Xsel = " & std_logic'image(CtrlBad.IR_Xsel)
            severity note;

        assert CtrlGood.IR_Xsel = IR_XSEL_ZERO
            report "good_decode is order-independent, as it must be"
            severity error;

        assert CtrlBad.IR_Xsel = IR_XSEL_ZERO
            report "EXPECTED FAILURE (bad_decode): LUI inherited ADDI's " &
                   "sign-extension setting. Identical instruction, different " &
                   "answer, because the previous instruction was different. " &
                   "That is a latch in the control unit."
            severity error;

        report "In Lab 12 this shows up as: every instruction works when tested" &
               " alone, the program still fails, and it fails differently" &
               " depending on instruction order. Assign the default FIRST."
            severity note;

        wait;
    end process stimulus;

end architecture test;
