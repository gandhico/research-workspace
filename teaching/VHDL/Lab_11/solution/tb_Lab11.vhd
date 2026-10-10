--------------------------------------------------------------------------------
-- EE 362 - Lab 11 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- TABLE-DRIVEN. Instead of hand-written blocks per instruction, the expected
-- control bundle for each instruction is stored in an array and the checks run
-- in a loop. That is how you verify a table-shaped design: the test data and
-- the specification become visibly the same object.
--
-- 8 instructions, every field checked, plus the safety and latch tests.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity tb_Lab11 is
end entity tb_Lab11;

architecture test of tb_Lab11 is

    signal Instr : std_logic_vector(31 downto 0) := (others => '0');
    signal Ctrl  : CTRL_REC;

    -- One entry per instruction: the encoding, a name, and the full expected
    -- control bundle. This array IS the control table.
    type vec_t is record
        code : std_logic_vector(31 downto 0);
        name : string(1 to 4);
        want : CTRL_REC;
    end record;

    type vec_array is array (natural range <>) of vec_t;

    -- Build each expectation from the default, overriding the same fields the
    -- decoder should. If the decoder and this table disagree, one is wrong.
    function E (base : CTRL_REC) return CTRL_REC is
    begin
        return base;
    end function;

    constant EXP_ADD : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_AOUT,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_ZERO,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RD,
        RF_strb => RF_STRB_STROBE, RF_oe => RF_OE_HIZ);

    constant EXP_SLL : CTRL_REC := (
        ALU_func => ALU_FUNC_SLL, ALU_Asel => ALU_ASEL_AOUT,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_ZERO,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RD,
        RF_strb => RF_STRB_STROBE, RF_oe => RF_OE_HIZ);

    constant EXP_ADDI : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_IMMED,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_SIGN,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RT,
        RF_strb => RF_STRB_STROBE, RF_oe => RF_OE_HIZ);

    constant EXP_LUI : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_IMMED,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_ZERO,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RT,
        RF_strb => RF_STRB_STROBE, RF_oe => RF_OE_HIZ);

    constant EXP_LW : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_IMMED,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_SIGN,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_ENABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_MEM, RF_Wsel => RF_WSEL_RT,
        RF_strb => RF_STRB_STROBE, RF_oe => RF_OE_HIZ);

    constant EXP_SW : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_IMMED,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_SIGN,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_ENABLE, DM_rw => DM_RW_WR, DM_strb => DM_STRB_STORE,
        NIAG_sel => NIAG_SEL_NSA, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RD,
        RF_strb => RF_STRB_HOLD, RF_oe => RF_OE_DRIVE);

    constant EXP_BLEZ : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_AOUT,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_SIGN,
        IR_Xlsft => IR_XLSFT_TWO, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_REL, NIAG_cond => NIAG_COND_LEZ,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RD,
        RF_strb => RF_STRB_HOLD, RF_oe => RF_OE_HIZ);

    constant EXP_J : CTRL_REC := (
        ALU_func => ALU_FUNC_ADD, ALU_Asel => ALU_ASEL_AOUT,
        ALU_Ssel => ALU_SSEL_SA,  IR_Xsel  => IR_XSEL_ZERO,
        IR_Xlsft => IR_XLSFT_NONE, IR_strb => IR_STRB_STROBE,
        DM_en => DM_EN_DISABLE, DM_rw => DM_RW_RD, DM_strb => DM_STRB_HOLD,
        NIAG_sel => NIAG_SEL_ABS, NIAG_cond => NIAG_COND_NONE,
        NIAG_strb => NIAG_STRB_STROBE,
        RF_Dsel => RF_DSEL_ALU, RF_Wsel => RF_WSEL_RD,
        RF_strb => RF_STRB_HOLD, RF_oe => RF_OE_HIZ);

    constant TABLE : vec_array := (
        (x"00221820", "ADD ", EXP_ADD),
        (x"00021040", "SLL ", EXP_SLL),
        (x"2021FFFF", "ADDI", EXP_ADDI),
        (x"3C01000B", "LUI ", EXP_LUI),
        (x"8C220004", "LW  ", EXP_LW),
        (x"AC020000", "SW  ", EXP_SW),
        (x"18200002", "BLEZ", EXP_BLEZ),
        (x"08000002", "J   ", EXP_J)
    );

begin

    DUT : entity work.Decoder
        port map (Instr => Instr, Ctrl => Ctrl);

    stimulus : process
        variable errors : natural := 0;

        procedure one (got, want : in std_logic; nm, instr : in string) is
        begin
            if got /= want then
                report "FAIL: " & instr & " field " & nm severity error;
                errors := errors + 1;
            end if;
        end procedure one;

        procedure onev (got, want : in std_logic_vector; nm, instr : in string) is
        begin
            if got /= want then
                report "FAIL: " & instr & " field " & nm severity error;
                errors := errors + 1;
            end if;
        end procedure onev;

    begin

        for i in TABLE'range loop
            Instr <= TABLE(i).code;
            wait for 10 ns;

            onev(Ctrl.ALU_func,  TABLE(i).want.ALU_func,  "ALU_func",  TABLE(i).name);
            one (Ctrl.ALU_Asel,  TABLE(i).want.ALU_Asel,  "ALU_Asel",  TABLE(i).name);
            one (Ctrl.ALU_Ssel,  TABLE(i).want.ALU_Ssel,  "ALU_Ssel",  TABLE(i).name);
            one (Ctrl.IR_Xsel,   TABLE(i).want.IR_Xsel,   "IR_Xsel",   TABLE(i).name);
            one (Ctrl.IR_Xlsft,  TABLE(i).want.IR_Xlsft,  "IR_Xlsft",  TABLE(i).name);
            one (Ctrl.DM_en,     TABLE(i).want.DM_en,     "DM_en",     TABLE(i).name);
            one (Ctrl.DM_rw,     TABLE(i).want.DM_rw,     "DM_rw",     TABLE(i).name);
            one (Ctrl.DM_strb,   TABLE(i).want.DM_strb,   "DM_strb",   TABLE(i).name);
            onev(Ctrl.NIAG_sel,  TABLE(i).want.NIAG_sel,  "NIAG_sel",  TABLE(i).name);
            onev(Ctrl.NIAG_cond, TABLE(i).want.NIAG_cond, "NIAG_cond", TABLE(i).name);
            onev(Ctrl.RF_Dsel,   TABLE(i).want.RF_Dsel,   "RF_Dsel",   TABLE(i).name);
            onev(Ctrl.RF_Wsel,   TABLE(i).want.RF_Wsel,   "RF_Wsel",   TABLE(i).name);
            one (Ctrl.RF_strb,   TABLE(i).want.RF_strb,   "RF_strb",   TABLE(i).name);
            one (Ctrl.RF_oe,     TABLE(i).want.RF_oe,     "RF_oe",     TABLE(i).name);
        end loop;

        report "8 instructions, 14 control fields each, all checked."
            severity note;

        ----------------------------------------------------------------------
        -- Safety: unimplemented opcode, and unimplemented func within SPECIAL
        ----------------------------------------------------------------------
        Instr <= x"FC000000"; wait for 10 ns;
        one(Ctrl.RF_strb, RF_STRB_HOLD,  "RF_strb",  "unknown opcode");
        one(Ctrl.DM_strb, DM_STRB_HOLD,  "DM_strb",  "unknown opcode");
        one(Ctrl.DM_en,   DM_EN_DISABLE, "DM_en",    "unknown opcode");
        one(Ctrl.RF_oe,   RF_OE_HIZ,     "RF_oe",    "unknown opcode");

        Instr <= x"00221825"; wait for 10 ns;      -- SPECIAL, func 100101
        one(Ctrl.RF_strb, RF_STRB_HOLD, "RF_strb", "SPECIAL with unknown func");

        ----------------------------------------------------------------------
        -- Latch test: the same instruction after two different predecessors
        ----------------------------------------------------------------------
        Instr <= x"2021FFFF"; wait for 10 ns;      -- ADDI
        Instr <= x"3C01000B"; wait for 10 ns;      -- LUI
        one(Ctrl.IR_Xsel, IR_XSEL_ZERO, "IR_Xsel", "LUI after ADDI");

        Instr <= x"18200002"; wait for 10 ns;      -- BLEZ (sets IR_Xlsft = TWO)
        Instr <= x"AC020000"; wait for 10 ns;      -- SW   (must be NONE)
        one(Ctrl.IR_Xlsft, IR_XLSFT_NONE, "IR_Xlsft", "SW after BLEZ");

        Instr <= x"AC020000"; wait for 10 ns;      -- SW   (sets RF_oe = DRIVE)
        Instr <= x"00221820"; wait for 10 ns;      -- ADD  (must be HiZ)
        one(Ctrl.RF_oe, RF_OE_HIZ, "RF_oe", "ADD after SW");

        if errors = 0 then
            report "PASS - Lab 11: complete decoder, all 8 instructions verified."
                severity note;
        else
            report "FAILED - Lab 11: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
