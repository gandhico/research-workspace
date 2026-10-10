--------------------------------------------------------------------------------
-- EE 362 - Lab 10 REFERENCE SOLUTION  (TA only - do not publish)
--
-- Decoder, part 1: ADD, SLL, ADDI, LUI.
--
-- Marking points:
--   * CTRL_DEFAULT assigned FIRST, before the case - no latches
--   * SPECIAL checked on BOTH opcode and func
--   * RF_Wsel = RD for R-type, RT for I-type
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

        c := CTRL_DEFAULT;              -- every field defined on every path

        case opcode is

            when OP_SPECIAL =>
                -- SPECIAL is a family, not an instruction: check func too.
                if func = FN_ADD then
                    c.ALU_func := ALU_FUNC_ADD;
                    c.ALU_Asel := ALU_ASEL_AOUT;
                    c.RF_Dsel  := RF_DSEL_ALU;
                    c.RF_Wsel  := RF_WSEL_RD;
                    c.RF_strb  := RF_STRB_STROBE;

                elsif func = FN_SLL then
                    c.ALU_func := ALU_FUNC_SLL;
                    c.ALU_Asel := ALU_ASEL_AOUT;
                    c.ALU_Ssel := ALU_SSEL_SA;      -- shift amount from the sa field
                    c.RF_Dsel  := RF_DSEL_ALU;
                    c.RF_Wsel  := RF_WSEL_RD;
                    c.RF_strb  := RF_STRB_STROBE;
                end if;

            when OP_ADDI =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;         -- a signed offset
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.RF_Dsel  := RF_DSEL_ALU;
                c.RF_Wsel  := RF_WSEL_RT;           -- I-type writes rt
                c.RF_strb  := RF_STRB_STROBE;

            when OP_LUI =>
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_ZERO;         -- a bit pattern, not a number
                c.IR_Xlsft := IR_XLSFT_NONE;
                c.RF_Dsel  := RF_DSEL_ALU;
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when others =>
                null;                               -- keep the safe default

        end case;

        Ctrl <= c;

    end process;

end architecture rtl;
