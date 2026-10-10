-- PLACEHOLDER: replace with YOUR OWN Decoder.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 11 - Assignment: the Instruction Decoder, part 2 of 2
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- ============================================================================
-- STEP 1: PASTE IN YOUR LAB 10 DECODER
-- ============================================================================
-- This file is the Lab 10 skeleton again. Start by pasting in the four rows you
-- wrote last week - ADD, SLL, ADDI, LUI - then add the four below.
--
-- If your Lab 10 decoder had inferred latches, FIX THAT FIRST. Merging four
-- more rows into a design with sixteen latches makes it strictly worse, and
-- Lab 12 is next week.
--
-- ============================================================================
-- THIS WEEK'S FOUR ROWS. Differences from CTRL_DEFAULT only.
-- ============================================================================
--
--  instr  opcode    ALU_Asel IR_Xsel IR_Xlsft DM_en  DM_rw DM_strb RF_Dsel RF_strb RF_Wsel RF_oe  NIAG_sel NIAG_cond
--  -----  --------  -------- ------- -------- ------ ----- ------- ------- ------- ------- -----  -------- ---------
--  LW     100011    IMMED    SIGN    NONE     ENABLE RD    -       MEM     STROBE  RT      -      -        -
--  SW     101011    IMMED    SIGN    NONE     ENABLE WR    STORE   -       -       -       DRIVE  -        -
--  BLEZ   000110    AOUT     SIGN    TWO      -      -     -       -       -       -       -      REL      LEZ
--  J      000010    -        -       -        -      -     -       -       -       -       -      ABS      NONE
--
--  All four also set ALU_func = ADD, except J which does not use the ALU.
--  "-" means: leave the default.
--
-- ============================================================================
-- FOUR THINGS IN THAT TABLE THAT ARE EASY TO GET WRONG
-- ============================================================================
--
--  1. SW has RF_strb = HOLD.  A store writes MEMORY, not a register. Leave it
--     at STROBE and every store silently corrupts a register - and because the
--     store itself still works, your program fails somewhere else entirely.
--
--  2. SW has RF_oe = DRIVE.  During a store the RAM is not driving the data
--     bus, so the register file must, through your Lab 4 TriBuffer. Leave it at
--     HiZ and the store writes 'Z', which the RAM happily stores.
--
--  3. BLEZ has IR_Xlsft = TWO.  It is the ONLY instruction in this CPU that
--     scales its immediate. Miss it and every branch lands a quarter of the way
--     to its target - Lab 7's "off by a factor", arriving through the decoder.
--
--  4. BLEZ and J both have RF_strb = HOLD.  Control flow writes no register.
--
-- Signals 1, 2 and 4 are all the same idea: RF_strb must be STROBE for EXACTLY
-- the five instructions that produce a value worth keeping - ADD, SLL, ADDI,
-- LUI, LW - and HOLD for the other three.
--
-- ============================================================================
-- WORTH NOTICING WHEN THE TABLE IS COMPLETE
-- ============================================================================
--  * ALU_Asel = IMMED for ADDI, LUI, LW and SW - four instructions with nothing
--    obvious in common. Why? BECAUSE THE ADDER IS SHARED. Computing a + b and
--    computing base + offset are the same operation, so a load costs no more
--    hardware than an add.
--
--  * DM_rw is determined by exactly ONE instruction out of eight. Real control
--    tables are this sparse: mostly default, a few exceptions per row.
--
--  * Most of J's row is default. It changes two signals out of sixteen.
--
-- Your report must state these three observations in your own words.
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

    -- TODO 1: field extraction (from your Lab 10 decoder)


    process (opcode, func)
        variable c : CTRL_REC;
    begin

        -- TODO 2: the default, FIRST. Still true, and now more important.


        -- TODO 3: your four Lab 10 rows - ADD, SLL, ADDI, LUI


        -- TODO 4: the four new rows - LW, SW, BLEZ, J
        --         Use the table above. Watch the four traps.


        Ctrl <= c;

    end process;

end architecture rtl;
