--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 11, Example 1 - LW and SW, and the adder they share with arithmetic
--
-- ============================================================================
-- THE ADDER IS SHARED. That is the lesson of this example.
-- ============================================================================
--   LW  rt, offset(rs)     address = rs + offset
--   SW  rt, offset(rs)     address = rs + offset
--   ADDI rt, rs, imm       result  = rs + imm
--
-- Look at those three. Computing "a + b" and computing "base + offset" are the
-- SAME OPERATION. So loads and stores use the same ALU, the same extender, and
-- the same control values for ALU_func and ALU_Asel as ADDI does.
--
-- That is why a load costs no more hardware than an add. It is also why
-- ALU_Asel = IMMED for four unrelated-looking instructions - ADDI, LUI, LW and
-- SW. When you see one control signal high for a strange-looking set of
-- instructions, look for the shared resource.
--
-- ============================================================================
-- WHERE LW AND SW DIFFER
-- ============================================================================
-- They compute the same address. Everything after that is opposite:
--
--                        LW                      SW
--   DM_rw                RD                      WR
--   DM_strb              HOLD                    STORE
--   RF_Dsel              MEM   (data comes in)   -       (nothing written)
--   RF_strb              STROBE                  HOLD    <-- CRITICAL
--   RF_Wsel              RT                      -
--   RF_oe                HiZ                     DRIVE   <-- CRITICAL
--
-- THE TWO CRITICAL ONES
--
--   RF_strb = HOLD for SW. A store writes MEMORY, not a register. Leave this
--   at STROBE and every store silently corrupts a register - and because the
--   store itself still works, the program fails somewhere else entirely.
--
--   RF_oe = DRIVE for SW. The register file must drive the memory data bus
--   through the Lab 4 TriBuffer, because the RAM is not driving it during a
--   write. Leave this at HiZ and the store writes 'Z' - which the RAM happily
--   stores, and your data is gone.
--
-- Those two signals are the entire difference between "store" and "corrupt".
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_lw_sw is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity decode_lw_sw;

architecture rtl of decode_lw_sw is
    signal opcode : std_logic_vector(5 downto 0);
begin

    opcode <= Instr(31 downto 26);

    process (opcode)
        variable c : CTRL_REC;
    begin
        c := CTRL_DEFAULT;

        case opcode is

            when OP_LW =>
                -- address arithmetic: identical to ADDI
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;      -- offsets can be negative
                c.IR_Xlsft := IR_XLSFT_NONE;     -- a byte offset, not scaled
                -- ...then the load-specific part
                c.DM_en    := DM_EN_ENABLE;
                c.DM_rw    := DM_RW_RD;
                c.RF_Dsel  := RF_DSEL_MEM;       -- write-back comes from memory
                c.RF_Wsel  := RF_WSEL_RT;
                c.RF_strb  := RF_STRB_STROBE;

            when OP_SW =>
                -- the SAME address arithmetic
                c.ALU_func := ALU_FUNC_ADD;
                c.ALU_Asel := ALU_ASEL_IMMED;
                c.IR_Xsel  := IR_XSEL_SIGN;
                c.IR_Xlsft := IR_XLSFT_NONE;
                -- ...then the store-specific part
                c.DM_en    := DM_EN_ENABLE;
                c.DM_rw    := DM_RW_WR;
                c.DM_strb  := DM_STRB_STORE;
                c.RF_oe    := RF_OE_DRIVE;       -- register file drives the bus
                -- RF_strb stays HOLD: a store writes MEMORY, not a register.

            when others =>
                null;

        end case;

        Ctrl <= c;
    end process;

end architecture rtl;
