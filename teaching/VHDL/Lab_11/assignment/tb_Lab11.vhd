--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 11 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- THIS ONE IS TABLE-DRIVEN, and that is the point.
--
-- Instead of writing a block of checks per instruction, the expected control
-- bundle for each instruction is stored in an array and a loop checks every
-- field of every row. The test data and the specification become visibly the
-- same object - which is exactly what you want when the design under test IS
-- a table.
--
-- Eight instructions x fourteen fields = 112 checks, from one loop.
--
-- REQUIRED:
--   [required] complete the TABLE below - one entry per instruction, with the
--              FULL expected control bundle for each. Build each expectation
--              from CTRL_DEFAULT and override the same fields your decoder
--              should. If your table and your decoder disagree, one of them is
--              wrong, and finding out which is the exercise.
--   [required] an unimplemented opcode - must be inert
--   [required] SPECIAL with an unimplemented func - also inert
--   [required] THREE latch tests, each feeding one instruction after another
--              that sets the signal differently:
--                  LUI after ADDI   -> IR_Xsel must be ZERO
--                  SW  after BLEZ   -> IR_Xlsft must be NONE
--                  ADD after SW     -> RF_oe must be HiZ
--
-- The three latch tests matter more this week than last: with eight rows there
-- are far more signals that some instructions set and others do not.
--
-- Two expectation constants (EXP_ADD, EXP_SLL) are filled in as templates.
-- Complete the remaining six.
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

    -- TODO: complete EXP_ADDI from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_ADDI : CTRL_REC := CTRL_DEFAULT;


    -- TODO: complete EXP_LUI from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_LUI : CTRL_REC := CTRL_DEFAULT;


    -- TODO: complete EXP_LW from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_LW : CTRL_REC := CTRL_DEFAULT;


    -- TODO: complete EXP_SW from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_SW : CTRL_REC := CTRL_DEFAULT;


    -- TODO: complete EXP_BLEZ from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_BLEZ : CTRL_REC := CTRL_DEFAULT;


    -- TODO: complete EXP_J from the control table.
    --       Copy the shape of EXP_ADD above and change what differs.
    constant EXP_J : CTRL_REC := CTRL_DEFAULT;


    -- NOTE the "0 =>" below. A one-element array aggregate is ambiguous in
    -- VHDL - without the index it parses as the RECORD, not an array of one.
    -- Once you have two or more rows you can drop it and use a plain list.
    constant TABLE : vec_array := (
        0 => (x"00221820", "ADD ", EXP_ADD)

        -- TODO: add the other seven rows, in this order:
        --     (x"00021040", "SLL ", EXP_SLL),
        --     (x"2021FFFF", "ADDI", EXP_ADDI),
        --     (x"3C01000B", "LUI ", EXP_LUI),
        --     (x"8C220004", "LW  ", EXP_LW),
        --     (x"AC020000", "SW  ", EXP_SW),
        --     (x"18200002", "BLEZ", EXP_BLEZ),
        --     (x"08000002", "J   ", EXP_J)
        --
        -- Remember to add a comma after the ADD entry when you uncomment these.
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

        report "Instructions checked: " & integer'image(TABLE'length) &
               " (should be 8 when your table is complete)."
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
        -- *** REQUIRED *** Three latch tests. Each feeds one instruction after
        -- another that sets the same signal differently.
        --
        --   LUI  after ADDI  -> IR_Xsel  must be ZERO
        --   SW   after BLEZ  -> IR_Xlsft must be NONE
        --   ADD  after SW    -> RF_oe    must be HiZ
        ----------------------------------------------------------------------
        -- TODO


        if errors = 0 then
            report "PASS - Lab 11: complete decoder verified."
                severity note;
        else
            report "FAILED - Lab 11: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
