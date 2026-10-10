--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 11, Example 3 - Control flow: BLEZ and J
--
-- These two are where your Lab 8 work gets driven. Everything the NIAG can do
-- is selected from here, by exactly two control fields.
--
-- ============================================================================
-- BLEZ rs, offset      "branch if rs <= 0"
-- ============================================================================
--   NIAG_sel  = REL       use the relative target...
--   NIAG_cond = LEZ       ...if the condition holds
--   IR_Xsel   = SIGN      the offset is signed
--   IR_Xlsft  = TWO       *** and it is scaled by 4 ***
--   ALU_func  = ADD       the ALU computes rs + 0 so the FLAGS describe rs
--   RF_strb   = HOLD      a branch writes no register
--
--   IR_Xlsft = TWO is the ONLY instruction in this CPU that scales the
--   immediate. Every other one uses a byte offset. Miss it and every branch
--   lands a quarter of the way to its target - Lab 7's "off by a factor".
--
--   WHY THE ALU IS INVOLVED AT ALL: the branch condition is evaluated from the
--   ALU's Zero and Neg flags. So the instruction must push rs through the ALU
--   just to produce flags that describe it. The result itself is discarded -
--   RF_strb is HOLD.
--
-- ============================================================================
-- J index              "jump"
-- ============================================================================
--   NIAG_sel  = ABS       use the absolute target
--   NIAG_cond = NONE      unconditionally
--   ...and nothing else. J is the sparsest row in the whole table:
--   two signals changed, fourteen defaults.
--
--   It does not use the ALU, does not touch memory, does not write a register,
--   and does not read the extender. Almost every control signal is a DON'T
--   CARE for J - which is exactly the freedom Example 2 exploits.
--
-- ============================================================================
-- THE SHAPE OF A CONTROL TABLE
-- ============================================================================
-- Notice how sparse this all is. Most of the table is default. A control unit
-- is mostly "do nothing" with a few exceptions per row - which is why the
-- default-first structure is not a convenience but the natural shape of the
-- problem.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_flow is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity decode_flow;

architecture rtl of decode_flow is
    signal opcode : std_logic_vector(5 downto 0);
begin

    opcode <= Instr(31 downto 26);

    process (opcode)
        variable c : CTRL_REC;
    begin
        c := CTRL_DEFAULT;

        case opcode is

            when OP_BLEZ =>
                c.ALU_func  := ALU_FUNC_ADD;     -- push rs through, for the flags
                c.ALU_Asel  := ALU_ASEL_AOUT;
                c.IR_Xsel   := IR_XSEL_SIGN;
                c.IR_Xlsft  := IR_XLSFT_TWO;     -- the ONLY scaled immediate
                c.NIAG_sel  := NIAG_SEL_REL;
                c.NIAG_cond := NIAG_COND_LEZ;
                -- RF_strb stays HOLD: a branch writes no register.

            when OP_J =>
                c.NIAG_sel  := NIAG_SEL_ABS;
                c.NIAG_cond := NIAG_COND_NONE;
                -- and nothing else. Fourteen defaults.

            when others =>
                null;

        end case;

        Ctrl <= c;
    end process;

end architecture rtl;
