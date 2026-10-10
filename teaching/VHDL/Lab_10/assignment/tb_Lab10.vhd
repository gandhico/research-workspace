--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 10 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- Testing a decoder is not like testing a datapath component. There is no
-- waveform to squint at: you feed in an encoded instruction and ASSERT THE
-- EXACT VALUE of every control signal that matters.
--
-- REQUIRED: at least one vector per implemented instruction, plus all of:
--
--   [required] ADD  - check ALU_func, ALU_Asel, RF_Dsel, RF_Wsel, RF_strb
--   [required] SLL  - and specifically ALU_Ssel (the shift amount source)
--   [required] ADDI - and specifically IR_Xsel = SIGN
--   [required] LUI  - and specifically IR_Xsel = ZERO
--              (ADDI and LUI differ on exactly that one signal - if your two
--               checks agree, one of them is wrong)
--   [required] an UNIMPLEMENTED opcode: no register write, no memory write,
--              memory disabled, bus not driven, PC still advances
--   [required] SPECIAL with an unimplemented func - also inert. This is why
--              R-type must check BOTH fields.
--   [required] *** ORDER DEPENDENCE *** feed ADDI, then LUI, and check that
--              LUI still zero-extends. Then the reverse. If either fails you
--              have a latch - see Example 3.
--
-- The last one is the check that a single-instruction-at-a-time testbench can
-- never make, and it is the one that catches the worst bug in this lab.
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
        -- ADD r3, r1, r2. This one fails until your decoder is built.
        ----------------------------------------------------------------------
        Instr <= I_ADD; wait for 10 ns;
        chk(Ctrl.RF_strb = RF_STRB_STROBE, "ADD: register write happens");

        -- TODO: also check ALU_func, ALU_Asel, RF_Dsel, RF_Wsel for ADD


        ----------------------------------------------------------------------
        -- TODO: SLL - and specifically ALU_Ssel
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: ADDI - and specifically IR_Xsel = IR_XSEL_SIGN, RF_Wsel = RT
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: LUI - and specifically IR_Xsel = IR_XSEL_ZERO
        --       ADDI and LUI differ on exactly that one signal. If your two
        --       checks agree, one of them is wrong.
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: *** REQUIRED *** an unimplemented opcode (I_BAD).
        --       Use chk_inert, then also check the PC still advances.
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: *** REQUIRED *** SPECIAL with an unimplemented func
        --       (try x"00221825" - SPECIAL, func 100101). Must be inert.
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: *** REQUIRED *** ORDER DEPENDENCE, the latch test.
        --       Feed I_ADDI, then I_LUI, and check LUI still zero-extends.
        --       Then feed I_LUI, then I_ADDI, and check ADDI still
        --       sign-extends.
        --
        --       A testbench that only ever applies one instruction at a time
        --       CANNOT detect a latch. This is that test.
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 10: all checks passed." severity note;
        else
            report "FAILED - Lab 10: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
