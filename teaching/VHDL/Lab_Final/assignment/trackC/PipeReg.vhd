--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track C
--
-- PipeReg : the pipeline register between fetch and execute
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- ============================================================================
-- READ THE GRADING RULE BEFORE YOU START
-- ============================================================================
--   A WORKING PIPELINED CPU IS NOT REQUIRED.
--   Breaking it correctly and explaining precisely why is FULL CREDIT.
--
-- This track is graded on the HAZARD ANALYSIS, not on whether the machine runs
-- the loop. If you make arithmetic work and then document exactly how and why
-- branches are now wrong, that is the whole assignment.
--
-- ============================================================================
-- WHAT YOU ARE BUILDING
-- ============================================================================
--
--   stage 1 (IF)    PC -> ROM -> IR
--                                 |
--                          [ PipeReg ]   <- this file
--                                 |
--   stage 2 (EX)    decode, register read, ALU, write-back, PC update
--
-- The register carries the fetched instruction, and the PC it came from, from
-- one stage to the next. That is all it does.
--
-- ============================================================================
-- WHAT WILL BREAK, AND WHY THAT IS THE POINT
-- ============================================================================
-- Once the register is in, stage 2 is running one instruction BEHIND stage 1.
-- The PC is updated in stage 2, so by the time a branch decides where to go,
-- stage 1 has already fetched the instruction after it.
--
-- That is a CONTROL HAZARD, and it is why real MIPS has a branch delay slot -
-- the instruction after a jump executes anyway, because flushing it was more
-- expensive than telling the assembler to fill it.
--
-- There is also a DATA HAZARD waiting for you: in the Lab 12 program,
--     ADDI r1, r1, -1
--     BLEZ r1, +2
-- are adjacent, so the BLEZ reads r1 while the ADDI is still writing it.
--
-- Find both. Name them. Give the exact instruction pair that triggers each.
-- Then say what a real machine does about it, and what that costs.
--
-- ============================================================================
-- A STRAIGHT-LINE PROGRAM TO TEST STAGE 2 WITH
-- ============================================================================
-- Use ROM_pipeline.vhd. Four instructions, no branches, and the ADD's operands
-- are written three instructions earlier - far enough apart that no forwarding
-- is needed. If THAT does not execute correctly, the pipeline register itself
-- is wrong and the hazards are not your problem yet.
--
--   0x00  LUI  r1, 5
--   0x04  LUI  r2, 3
--   0x08  LUI  r3, 7
--   0x0C  ADD  r4, r1, r2      -> r4 = 8
--
-- Then, as an experiment: move the ADD up so it immediately follows the LUI of
-- r2. Predict what happens before you run it. That is the data hazard, made by
-- hand, and it belongs in your report.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity PipeReg is
    port (
        clk    : in  std_logic;
        Rst    : in  std_logic;
        Enable : in  std_logic;                        -- '0' stalls the stage

        -- from stage 1 (fetch)
        IR_in  : in  std_logic_vector(31 downto 0);
        PC_in  : in  std_logic_vector(31 downto 0);

        -- to stage 2 (execute)
        IR_out : out std_logic_vector(31 downto 0);
        PC_out : out std_logic_vector(31 downto 0)
    );
end entity PipeReg;

architecture rtl of PipeReg is
begin

    -- TODO: a two-field register.
    --
    --   asynchronous reset  -> both fields all-zeros
    --   rising edge         -> if Enable, capture IR_in and PC_in
    --   Enable low          -> hold (that is a stall, and you will want it)
    --
    -- WHY ALL-ZEROS ON RESET: the zero instruction decodes as SLL r0, r0, 0 -
    -- a NOP that writes r0, which the register file blocks. So an empty
    -- pipeline stage is harmless. That is not luck; it is why the all-zeros
    -- encoding was chosen for NOP in the first place.

end architecture rtl;
