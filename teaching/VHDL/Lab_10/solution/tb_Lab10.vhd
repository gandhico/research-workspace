--------------------------------------------------------------------------------
-- EE 362 - Lab 10 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- Testing a decoder is table-driven: feed an encoded instruction, assert the
-- exact value of every control signal that matters.
--
-- 26 checks, including the order-dependence test that catches latches.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity tb_Lab10 is
end entity tb_Lab10;

architecture test of tb_Lab10 is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

    -- Real instructions from the Lab 12 program, plus one constructed ADD.
    constant I_ADD  : std_logic_vector(31 downto 0) := x"00221820"; -- ADD r3,r1,r2
    constant I_SLL  : std_logic_vector(31 downto 0) := x"00021040"; -- SLL r2,r2,1
    constant I_ADDI : std_logic_vector(31 downto 0) := x"2021FFFF"; -- ADDI r1,r1,-1
    constant I_LUI  : std_logic_vector(31 downto 0) := x"3C01000B"; -- LUI r1,11
    constant I_BAD  : std_logic_vector(31 downto 0) := x"FC000000"; -- opcode 111111

begin

    DUT : entity work.Decoder
        port map (Instr => Instr, Ctrl => Ctrl);

    stimulus : process

        variable errors : natural := 0;

        procedure chk (cond : in boolean; msg : in string) is
        begin
            if not cond then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

        -- The five signals that must be safe for any instruction that does not
        -- write anything. Used to check the default and the unknown opcode.
        procedure chk_inert (msg : in string) is
        begin
            chk(Ctrl.RF_strb = RF_STRB_HOLD,  msg & " - no register write");
            chk(Ctrl.DM_strb = DM_STRB_HOLD,  msg & " - no memory store");
            chk(Ctrl.DM_en   = DM_EN_DISABLE, msg & " - memory disabled");
            chk(Ctrl.RF_oe   = RF_OE_HIZ,     msg & " - bus not driven");
        end procedure chk_inert;

    begin

        ----------------------------------------------------------------------
        -- ADD r3, r1, r2
        ----------------------------------------------------------------------
        Instr <= I_ADD; wait for 10 ns;
        chk(Ctrl.ALU_func = ALU_FUNC_ADD,   "1.  ADD: ALU adds");
        chk(Ctrl.ALU_Asel = ALU_ASEL_AOUT,  "2.  ADD: A input from register file");
        chk(Ctrl.RF_Dsel  = RF_DSEL_ALU,    "3.  ADD: write-back from the ALU");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RD,     "4.  ADD: destination is rd");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE, "5.  ADD: register write happens");
        chk(Ctrl.DM_en    = DM_EN_DISABLE,  "6.  ADD: memory untouched");
        chk(Ctrl.NIAG_sel = NIAG_SEL_NSA,   "7.  ADD: PC advances sequentially");

        ----------------------------------------------------------------------
        -- SLL r2, r2, 1
        ----------------------------------------------------------------------
        Instr <= I_SLL; wait for 10 ns;
        chk(Ctrl.ALU_func = ALU_FUNC_SLL,   "8.  SLL: ALU shifts");
        chk(Ctrl.ALU_Ssel = ALU_SSEL_SA,    "9.  SLL: shift amount from the sa field");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RD,     "10. SLL: destination is rd");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE, "11. SLL: register write happens");

        ----------------------------------------------------------------------
        -- ADDI r1, r1, -1     <- the loop counter decrement
        ----------------------------------------------------------------------
        Instr <= I_ADDI; wait for 10 ns;
        chk(Ctrl.ALU_func = ALU_FUNC_ADD,    "12. ADDI: ALU adds");
        chk(Ctrl.ALU_Asel = ALU_ASEL_IMMED,  "13. ADDI: A input is the immediate");
        chk(Ctrl.IR_Xsel  = IR_XSEL_SIGN,    "14. ADDI: SIGN-extends - it is an offset");
        chk(Ctrl.IR_Xlsft = IR_XLSFT_NONE,   "15. ADDI: not scaled");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RT,      "16. ADDI: destination is rt, not rd");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE,  "17. ADDI: register write happens");

        ----------------------------------------------------------------------
        -- LUI r1, 11
        ----------------------------------------------------------------------
        Instr <= I_LUI; wait for 10 ns;
        chk(Ctrl.ALU_Asel = ALU_ASEL_IMMED,  "18. LUI: A input is the immediate");
        chk(Ctrl.IR_Xsel  = IR_XSEL_ZERO,    "19. LUI: ZERO-extends - it is a pattern");
        chk(Ctrl.RF_Wsel  = RF_WSEL_RT,      "20. LUI: destination is rt");
        chk(Ctrl.RF_strb  = RF_STRB_STROBE,  "21. LUI: register write happens");

        ----------------------------------------------------------------------
        -- An unimplemented opcode: the safe default
        ----------------------------------------------------------------------
        Instr <= I_BAD; wait for 10 ns;
        chk_inert("22. unknown opcode");
        chk(Ctrl.NIAG_sel = NIAG_SEL_NSA, "23. unknown opcode: PC still advances");

        ----------------------------------------------------------------------
        -- SPECIAL with an unimplemented func: also inert.
        -- This is why R-type must check BOTH fields.
        ----------------------------------------------------------------------
        Instr <= x"00221825"; wait for 10 ns;      -- SPECIAL, func 100101
        chk(Ctrl.RF_strb = RF_STRB_HOLD,
            "24. SPECIAL with an unknown func writes nothing");

        ----------------------------------------------------------------------
        -- ORDER DEPENDENCE - the latch test.
        -- Feed ADDI, then LUI. LUI must zero-extend regardless of history.
        ----------------------------------------------------------------------
        Instr <= I_ADDI; wait for 10 ns;
        Instr <= I_LUI;  wait for 10 ns;
        chk(Ctrl.IR_Xsel = IR_XSEL_ZERO,
            "25. LUI after ADDI still zero-extends - no latch");

        -- And the reverse order, for the same reason.
        Instr <= I_LUI;  wait for 10 ns;
        Instr <= I_ADDI; wait for 10 ns;
        chk(Ctrl.IR_Xsel = IR_XSEL_SIGN,
            "26. ADDI after LUI still sign-extends - no latch");

        if errors = 0 then
            report "PASS - Lab 10: all 26 checks passed." severity note;
        else
            report "FAILED - Lab 10: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
