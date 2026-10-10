--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 11 reference component
--
-- The COMPLETE decoder: all eight instructions.
-- This is the version the CPU instantiates in Lab 12.
--
-- Marking points:
--   * CTRL_DEFAULT assigned first - no latches
--   * SPECIAL checked on opcode AND func
--   * SW:   RF_strb = HOLD  and  RF_oe = DRIVE     (the two that matter)
--   * BLEZ: IR_Xlsft = TWO  and  RF_strb = HOLD
--   * LW:   RF_Dsel = MEM
--   * ADDI sign-extends, LUI zero-extends
--   * 'when others => null' keeps the safe default
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity Decoder is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity Decoder;

architecture rtl of Decoder is

    signal opcode : std_logic_vector(5 downto 0);
    signal func   : std_logic_vector(5 downto 0);

begin

    opcode <= Instr(31 downto 26);
    func   <= Instr( 5 downto  0);

    process (opcode, func)
        variable c : CTRL_REC;
    begin

        c := CTRL_DEFAULT;

        case opcode is

            ------------------------------------------------------------------
            -- R-type family. SPECIAL is not one instruction.
            ------------------------------------------------------------------
            when OP_SPECIAL =>
                if func = FN_ADD then
                    c.ALU_func := ALU_FUNC_ADD;
                    c.ALU_Asel := ALU_ASEL_AOUT;
                    c.RF_Dsel  := RF_DSEL_ALU;
                    c.RF_Wsel  := RF_WSEL_RD;
                    c.RF_strb  := RF_STRB_STROBE;

                elsif func = FN_SLL then
                    c.ALU_func := ALU_FUNC_SLL;
                    c.ALU_Asel := ALU_ASEL_AOUT;
                    c.ALU_Ssel := ALU_SSEL_SA;
                    c.RF_Dsel  := RF_DSEL_ALU;
                    c.RF_Wsel  := RF_WSEL_RD;
                    c.RF_strb  := RF_STRB_STROBE;
                end if;

            ------------------------------------------------------------------
            -- I-type arithmetic
            ------------------------------------------------------------------
            when OP_ADDI =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.RF_Dsel  := RF_DSEL_ALU;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_ORI =>
                -- TRACK A REFERENCE ROW.
                -- Mirrors ADDI exactly except for the operation and the
                -- extension: ORI's immediate is a bit pattern, so it is
                -- ZERO-extended, the same argument as LUI.
                c.ALU_func := ALU_FUNC_OR;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_ZERO;
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.RF_Dsel  := RF_DSEL_ALU;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_LUI =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_ZERO;
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.RF_Dsel  := RF_DSEL_ALU;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            ------------------------------------------------------------------
            -- Memory. Same address arithmetic as ADDI; opposite afterwards.
            ------------------------------------------------------------------
            when OP_LW =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.DM_en    := DM_EN_ENABLE;
                c.DM_rw    := DM_RW_RD;
                c.RF_Dsel  := RF_DSEL_MEM;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_SW =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.DM_en    := DM_EN_ENABLE;
                c.DM_rw    := DM_RW_WR;
                c.DM_strb  := DM_STRB_STORE;
                c.RF_oe    := RF_OE_DRIVE;      -- register file drives the bus
                -- RF_strb stays HOLD: a store writes MEMORY.

            ------------------------------------------------------------------
            -- Control flow
            ------------------------------------------------------------------
            when OP_BLEZ =>
                c.ALU_func  := ALU_FUNC_ADD;    -- runs only to produce flags
                c.ALU_Asel  := ALU_ASEL_AOUT;
                c.IR_Xsel   := IR_XSEL_SIGN;
                c.IR_Xlsft  := IR_XLSFT_TWO;    -- the only scaled immediate
                c.NIAG_sel  := NIAG_SEL_REL;
                c.NIAG_cond := NIAG_COND_LEZ;
                -- RF_strb stays HOLD.

            when OP_J =>
                c.NIAG_sel  := NIAG_SEL_ABS;
                c.NIAG_cond := NIAG_COND_NONE;
                -- and nothing else.

            when others =>
                null;                           -- safe default

        end case;

        Ctrl <= c;

    end process;

end architecture rtl;
