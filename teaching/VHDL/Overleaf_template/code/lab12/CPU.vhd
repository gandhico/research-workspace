-- PLACEHOLDER: replace with YOUR OWN CPU.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 12 - Assignment: the CPU
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- ============================================================================
-- ALMOST NO NEW VHDL. This lab is WIRING, TIMING and DEBUGGING.
-- ============================================================================
-- Twelve components, all of which you have already built. Expect it to be
-- emotionally hard and technically shallow: nothing here is difficult to write,
-- and finding out why it does not work is the entire exercise.
--
-- STEP 1: replace anything in components/ with your own version. The reference
-- copies are there so that nobody is blocked by an earlier lab. Using one costs
-- you nothing on this lab.
--
-- ============================================================================
-- THE TIMING CONTRACT.  Write this on paper before you wire anything.
-- ============================================================================
--
--   RISING edge    FETCH.   IRreg <= ROM[PC]
--   FALLING edge   COMMIT.  register file writes, RAM writes, PC updates
--
--   One instruction per clock period. The instruction is captured at the start
--   of the period; every piece of state changes in the middle of it, by which
--   time the combinational logic has settled.
--
--   THE REGISTER FILE NEEDS AN INVERTED CLOCK. Its own architecture uses
--   rising_edge, and you want it to commit on the falling edge with everything
--   else. Inverting the clock at the instantiation is how you retime a
--   component you do not want to modify. Same for the NIAG.
--
--   EVERY BUG IN THIS LAB THAT IS NOT A MIS-WIRE IS AN EDGE MISTAKE.
--
-- ============================================================================
-- THE THREE WIRING DECISIONS THAT ARE EASY TO GET WRONG
-- ============================================================================
--
--   1. Asel = rt   and   Bsel = rs.   Not the other way round.
--
--      Work it out rather than trusting this comment:
--        ADDI/LW/SW  the base register is rs, and it must arrive on Bout,
--                    because the ALU's A input is the immediate.
--        SLL         shifts rt, which must arrive on Aout.
--        SW          stores rt, driven onto the bus from Aout.
--        BLEZ        has rt = 0, so Aout + Bout = 0 + rs and the flags
--                    describe rs.
--      One assignment satisfies all eight instructions. Swap them and THREE of
--      the four instruction types still work - which is what makes it nasty.
--
--   2. The store value comes from Aout, through the TriBuffer.
--
--   3. The ROM is addressed by PCreg, NOT by NSA. Address it with NSA and every
--      instruction executes one too early.
--
-- ============================================================================
-- WIRING RULES
-- ============================================================================
--   * NAMED ASSOCIATION in every port map. Twelve components is where
--     positional association stops being survivable.
--   * One internal signal per wire between components.
--   * You cannot read an 'out' port - drive it from an internal signal.
--   * Wire in the order of the block diagram, then read it back against the
--     diagram ONCE before you simulate.
--
-- ============================================================================
-- WHAT SUCCESS LOOKS LIKE
-- ============================================================================
--   45 instructions, one per clock period, CPI = 1
--   final r1 = 0x00000000        the loop counter ran out
--   final r2 = 0x00000400        1024 = 2^10
--   the word stored at address 0 = 0x00000400
--
--   *** YOUR CPU COMPUTES 2^10. ***
--
-- ============================================================================
-- ON THE 'metavalue detected' WARNINGS
-- ============================================================================
-- You will see several NUMERIC_STD.TO_INTEGER metavalue warnings in the first
-- few cycles. They are normal: before the first instruction is fetched, some
-- addresses are still 'U', and converting 'U' to an integer warns and returns
-- 0. They stop once the machine is running.
--
-- They are ALSO the first thing to look at if your CPU is dead, because a
-- metavalue warning that never stops means a signal is never being driven.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity CPU is
    port (
        SysClk : in  std_logic;
        Rst    : in  std_logic;

        -- Observation ports. Not part of the machine - they exist so your
        -- testbench can build the execution trace without reaching inside.
        -- Drive them at the bottom; do not let them change the design.
        PC_out     : out std_logic_vector(31 downto 0);  -- PC of the instruction in IR
        IR_out     : out std_logic_vector(31 downto 0);
        ALU_out    : out std_logic_vector(31 downto 0);
        RegWr      : out std_logic;
        RegWrAddr  : out std_logic_vector(4 downto 0);
        RegWrData  : out std_logic_vector(31 downto 0);
        MemBus_out : out std_logic_vector(31 downto 0);
        MemWr      : out std_logic
    );
end entity CPU;

architecture structural of CPU is

    -- TODO 1: declare one internal signal per wire between components.
    --
    --   fetch        PCreg, IMemData, IRreg, IRPC
    --   fields       rs_f, rt_f, rd_f, sa_f, immed_f, index_f
    --   control      Ctrl : CTRL_REC
    --   datapath     Xtnd32, Aout, Bout, ALUinA, Shft, ALUresult, Zero, Neg
    --   write-back   DselOut, DinOut
    --   addressing   NSA, Rtn
    --   memory       MemBus
    --   clocking     RegClk
    --
    -- IRPC is worth explaining: it is the PC that the instruction currently in
    -- IRreg was fetched FROM. By the time you look, PCreg has already moved on,
    -- so a trace that printed PCreg would name the wrong instruction. Capture
    -- it at the same edge as IRreg.


begin

    -- TODO 2: the inverted clock for the register file and the NIAG.


    -- TODO 3: field extraction from IRreg. Six slices, pure wiring.


    -- TODO 4: instantiate the twelve components, in diagram order:
    --
    --   U_ROM     ROM         addressed by PCreg
    --   U_DEC     Decoder     driven by IRreg
    --   U_XTND    ImmedXtnd   the SHARED extender - feeds the ALU and the NIAG
    --   U_RF      RegFile     Asel = rt, Bsel = rs, clk = RegClk
    --   U_AINMUX  Mux2 (W=32) Aout or Xtnd32, selected by Ctrl.ALU_Asel
    --   U_SFTMUX  ALUsftMUX   sa field or Bout(4 downto 0)
    --   U_ALU     ALU         Ain from the mux, Bin from Bout
    --   U_DSELMUX Mux3 (W=5)  rd / rt / "11111", selected by Ctrl.RF_Wsel
    --   U_DINMUX  Mux3 (W=32) ALU result / MemBus / Rtn, by Ctrl.RF_Dsel
    --   U_TRI     TriBuffer   Aout onto MemBus, enabled by Ctrl.RF_oe
    --   U_RAM     RAM         addressed by the ALU result, on MemBus
    --   U_NIAG    NIAG        clk = RegClk, so the PC commits on the falling edge
    --
    -- Named association only.


    -- TODO 5: the FETCH process.
    --         Rising edge of SysClk, gated by Ctrl.IR_strb:
    --             IRreg <= IMemData;
    --             IRPC  <= PCreg;
    --         Asynchronous reset clears both.


    -- TODO 6: drive the observation ports.
    --         PC_out is IRPC, not PCreg. MemWr is high when the RAM is
    --         actually storing: DM_en enabled AND DM_rw write AND DM_strb.


end architecture structural;
