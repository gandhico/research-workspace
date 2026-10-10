--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 11, Example 2 - Two different correct answers
--
-- ============================================================================
-- A DON'T CARE IS A DEGREE OF FREEDOM, NOT A GAP
-- ============================================================================
-- Look at IR_Xsel across all eight instructions. Which of them actually READ
-- the extender output?
--
--     ADDI  yes - the immediate goes to the ALU
--     LUI   yes - same
--     LW    yes - the offset goes to the ALU
--     SW    yes - same
--     BLEZ  yes - the offset goes to the branch adder
--
--     ADD   NO  - ALU_Asel = AOUT, the extender output is ignored
--     SLL   NO  - same
--     J     NO  - nothing reads it
--
-- For those last three the value of IR_Xsel CANNOT AFFECT ANYTHING. It is a
-- DON'T CARE, and that gives you freedom.
--
-- TWO IMPLEMENTATIONS, both correct:
--
--   as_written    IR_Xsel = SIGN for ADDI, LW, SW, BLEZ; ZERO otherwise
--                 (a four-term OR - a direct transcription of the table)
--
--   minimised     IR_Xsel = SIGN for everything EXCEPT LUI
--                 (one term: NOT LUI)
--
-- These DISAGREE on ADD, SLL and J - and agree everywhere it matters.
-- The minimised version is smaller. The transcribed version reads more directly
-- as the table. Both ship.
--
-- ============================================================================
-- WHY THIS MATTERS BEYOND THIS LAB
-- ============================================================================
-- This is what "minimisation" actually means in a real control unit, and it is
-- the same operation you did with a K-map in Lab 3 - except the don't cares now
-- come from the ARCHITECTURE (which instructions read which signals) rather
-- than from an incomplete table.
--
-- It is also a warning about testing. A testbench that only checks the five
-- instructions which use the extender cannot tell these two apart - and does
-- not need to. But a testbench that pins down IR_Xsel for ADD would be testing
-- an accident of your implementation rather than a requirement.
--
-- OVER-SPECIFYING A TEST IS ITS OWN KIND OF BUG.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity dontcare is
    port (
        Instr      : in  std_logic_vector(31 downto 0);
        Xsel_table : out std_logic;    -- direct transcription of the table
        Xsel_min   : out std_logic;    -- minimised over the don't cares
        Reads_Ext  : out std_logic     -- does this instruction read the extender?
    );
end entity dontcare;

architecture rtl of dontcare is

    signal opcode : std_logic_vector(5 downto 0);

    -- Instruction recognisers, exactly as in your decoder.
    signal is_addi, is_lui, is_lw, is_sw, is_blez : std_logic;

begin

    opcode <= Instr(31 downto 26);

    is_addi <= '1' when opcode = OP_ADDI else '0';
    is_lui  <= '1' when opcode = OP_LUI  else '0';
    is_lw   <= '1' when opcode = OP_LW   else '0';
    is_sw   <= '1' when opcode = OP_SW   else '0';
    is_blez <= '1' when opcode = OP_BLEZ else '0';

    -- Which instructions actually read the extender output. This is the
    -- CARE SET - the rows where the two implementations must agree.
    Reads_Ext <= is_addi or is_lui or is_lw or is_sw or is_blez;

    -- (a) Direct transcription: SIGN for the four that need it.
    Xsel_table <= IR_XSEL_SIGN when (is_addi or is_lw or is_sw or is_blez) = '1'
             else IR_XSEL_ZERO;

    -- (b) Minimised: SIGN for everything except LUI.
    --     Cheaper. Differs from (a) on ADD, SLL and J - all don't cares.
    Xsel_min <= IR_XSEL_ZERO when is_lui = '1' else IR_XSEL_SIGN;

end architecture rtl;
