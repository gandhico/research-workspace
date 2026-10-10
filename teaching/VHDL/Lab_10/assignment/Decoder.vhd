--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 10 - Assignment: the Instruction Decoder, part 1 of 2
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- ============================================================================
-- READ THIS FIRST. THE SCOPE IS SMALL.
-- ============================================================================
-- This CPU implements EIGHT instructions - the ones its program actually uses.
-- Not forty. You do four this week and four next week.
--
-- The instruction set manual is not your specification. THE CONTROL TABLE IS,
-- and it is given to you below, filled in. You implement it; you do not have
-- to derive it. Deriving it is Dr Tang's lecture, not fifty-five minutes at a
-- bench.
--
-- ============================================================================
-- THE IDEA
-- ============================================================================
-- In Lab 1 you took a four-row truth table and wrote one Boolean equation.
-- Today you take an eight-row table and write sixteen.
--
-- That is the whole difference. Nothing new has been introduced since week one.
-- The control unit of a processor IS a truth table.
--
-- ============================================================================
-- THE DEFAULTS - every instruction starts here
-- ============================================================================
-- CTRL_DEFAULT in CPU_Pkg.vhd. The safe values:
--
--     RF_strb   = HOLD        do not write a register
--     DM_en     = DISABLE     do not touch memory
--     DM_strb   = HOLD        do not store
--     RF_oe     = HiZ         do not drive the memory bus
--     NIAG_sel  = NSA         advance the PC sequentially
--     NIAG_cond = NONE        unconditionally
--     ALU_Asel  = AOUT        ALU A input from the register file
--     IR_Xsel   = ZERO        zero-extend
--     IR_Xlsft  = NONE        do not scale
--
-- ASSIGN THE DEFAULT FIRST, then override. Example 3 shows what happens if you
-- do not: sixteen latches, and control signals that depend on which instruction
-- ran before. Every instruction then works alone and the program still fails.
--
-- ============================================================================
-- THIS WEEK'S FOUR ROWS. Only the DIFFERENCES from the default are shown.
-- ============================================================================
--
--  instr  opcode/func      ALU_func ALU_Asel ALU_Ssel IR_Xsel IR_Xlsft RF_Dsel RF_strb RF_Wsel
--  -----  ---------------  -------- -------- -------- ------- -------- ------- ------- -------
--  ADD    000000 / 100000  ADD      AOUT     -        -       -        ALU     STROBE  RD
--  SLL    000000 / 000000  SLL      AOUT     SA       -       -        ALU     STROBE  RD
--  ADDI   001000           ADD      IMMED    -        SIGN    NONE     ALU     STROBE  RT
--  LUI    001111           ADD      IMMED    -        ZERO    NONE     ALU     STROBE  RT
--
--  "-" means: leave the default.
--
-- ============================================================================
-- THINGS WORTH NOTICING IN THAT TABLE
-- ============================================================================
--  * ADD and SLL both write RD; ADDI and LUI both write RT. R-type and I-type
--    put the destination register in DIFFERENT FIELDS. That is what RF_Wsel is
--    for, and getting it backwards writes the wrong register silently.
--
--  * ADDI sign-extends and LUI zero-extends. Same field, same width, different
--    meaning - decided by the instruction. This is the Lab 4 question, arriving
--    for real: get it wrong and ADDI r1,r1,-1 adds 65535 instead of subtracting
--    one, and the Lab 12 loop counts the wrong way forever.
--
--  * ADD and SLL do not set IR_Xsel or IR_Xlsft at all. They never read the
--    extender output, so those values are DON'T CARES. Leaving them at the
--    default is correct - and next week you will see why that matters.
--
-- ============================================================================
-- STRUCTURE
-- ============================================================================
-- The opcode is at a fixed position (31 downto 26) because until you have
-- decoded it you do not know the format. For opcode = SPECIAL you must ALSO
-- check the func field: SPECIAL is not one instruction, it is a family.
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

    -- TODO 1: extract the opcode and func fields. Two slices.


    process (opcode, func)
        variable c : CTRL_REC;
    begin

        -- TODO 2: assign the default FIRST. One line.
        --         Skip this and you get sixteen latches. See Example 3.


        -- TODO 3: the four rows above.
        --
        --         Structure - a case on the opcode, with a nested test on func
        --         for the SPECIAL family:
        --
        --           case opcode is
        --               when OP_SPECIAL =>
        --                   if func = FN_ADD then
        --                       ...
        --                   elsif func = FN_SLL then
        --                       ...
        --                   end if;
        --
        --               when OP_ADDI => ...
        --               when OP_LUI  => ...
        --
        --               when others => null;   -- keep the safe default
        --           end case;


        Ctrl <= c;

    end process;

end architecture rtl;
