--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 10, Example 2 - ONE instruction decoded, end to end
--
-- This is the template every other row copies. Read it once properly and the
-- remaining seven instructions are bookkeeping.
--
-- ============================================================================
-- THE IDEA THAT CLOSES THE COURSE
-- ============================================================================
-- In Lab 1 you took a four-row truth table and wrote one Boolean equation from
-- it. Today you take an eight-row table and write sixteen.
--
-- That is the entire difference. Nothing new has been introduced since week one.
-- The control unit of a processor IS a truth table - that is not an analogy,
-- it is literally what you are about to write.
--
-- ============================================================================
-- ADD rd, rs, rt   -   what has to happen
-- ============================================================================
--   read two registers, add them, write the result to a third register,
--   and carry on to the next instruction.
--
-- Which of the sixteen control signals does that require?
--
--   ALU_func  = ADD          do an addition
--   ALU_Asel  = AOUT         the ALU's A input comes from the register file,
--                            not from an immediate
--   RF_Dsel   = ALU          the value written back comes from the ALU
--   RF_Wsel   = RD           the destination register is the rd field
--   RF_strb   = STROBE       actually perform the write
--
-- FIVE signals. The other eleven keep their default values, and that is the
-- whole point of having a default: you specify only what is different.
--
-- Everything not mentioned is already safe - no memory access, no bus driving,
-- PC advances sequentially.
--
-- ============================================================================
-- WHY THE DEFAULT MUST BE ASSIGNED FIRST
-- ============================================================================
-- If you write a case statement that assigns only SOME fields in SOME branches,
-- the synthesiser must keep the unassigned ones unchanged - which means it
-- builds a LATCH for each of them. Sixteen latches, and a CPU whose behaviour
-- depends on what it did last.
--
-- Assigning the complete default first makes every field defined on every path.
-- This is Lab 1's missing-else and Lab 3's missing-when-others, at scale.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity decode_add is
    port (
        Instr : in  std_logic_vector(31 downto 0);
        Ctrl  : out CTRL_REC
    );
end entity decode_add;

architecture rtl of decode_add is

    signal opcode : std_logic_vector(5 downto 0);
    signal func   : std_logic_vector(5 downto 0);

begin

    opcode <= Instr(31 downto 26);
    func   <= Instr( 5 downto  0);

    process (opcode, func)
        variable c : CTRL_REC;
    begin

        -- Step 1: START FROM THE DEFAULT. Every field defined, every path.
        c := CTRL_DEFAULT;

        -- Step 2: override only what this instruction changes.
        if opcode = OP_SPECIAL and func = FN_ADD then
            c.ALU_func := ALU_FUNC_ADD;
            c.ALU_Asel := ALU_ASEL_AOUT;
            c.RF_Dsel  := RF_DSEL_ALU;
            c.RF_Wsel  := RF_WSEL_RD;
            c.RF_strb  := RF_STRB_STROBE;
        end if;
        -- No else. An unrecognised instruction keeps the default, which is
        -- safe: no register write, no memory write, PC advances normally.

        Ctrl <= c;

    end process;

end architecture rtl;
