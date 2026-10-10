--------------------------------------------------------------------------------
-- EE 362 - Lab 12, Example 1 - A CPU with TWO deliberate wiring errors
--
-- This file is WRONG ON PURPOSE. Do not copy it into your assignment.
--
-- Both errors compile. Both run. Both produce a machine that looks almost
-- right: the PC advances correctly, the right instructions are fetched, and
-- every control signal matches the control table.
--
-- They are DATAPATH bugs - which is precisely what checks 1, 2 and 3 of the
-- bisection method are there to establish.
--
-- Work the method from bisect_method.md BEFORE reading the answers at the
-- bottom of this file. The point of the example is the method, not the bugs.
--
-- Both are marked with *** BUG n *** so you can find them afterwards. In real
-- life they are not marked, which is the whole difficulty.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.CPU_Pkg.all;

entity cpu_broken is
    port (
        SysClk : in  std_logic;
        Rst    : in  std_logic;

        -- Observation ports. Not part of the machine - they exist so the
        -- testbench can build an execution trace without reaching inside.
        PC_out    : out std_logic_vector(31 downto 0);   -- PC of the instruction in IR
        IR_out    : out std_logic_vector(31 downto 0);
        ALU_out   : out std_logic_vector(31 downto 0);
        RegWr     : out std_logic;
        RegWrAddr : out std_logic_vector(4 downto 0);
        RegWrData : out std_logic_vector(31 downto 0);
        MemBus_out : out std_logic_vector(31 downto 0);
        MemWr      : out std_logic
    );
end entity cpu_broken;

architecture broken of cpu_broken is

    -- fetch
    signal PCreg    : std_logic_vector(31 downto 0);
    signal IMemData : std_logic_vector(31 downto 0);
    signal IRreg    : std_logic_vector(31 downto 0) := (others => '0');
    -- The PC that the instruction currently in IRreg was fetched from. The PC
    -- itself has already moved on by the time you look, so a trace that printed
    -- PCreg would name the wrong instruction. Captured at the same edge as IR.
    signal IRPC     : std_logic_vector(31 downto 0) := (others => '0');

    -- instruction fields
    signal rs_f, rt_f, rd_f, sa_f : std_logic_vector(4 downto 0);
    signal immed_f : std_logic_vector(15 downto 0);
    signal index_f : std_logic_vector(25 downto 0);

    -- control
    signal Ctrl : CTRL_REC;

    -- datapath
    signal Xtnd32     : std_logic_vector(31 downto 0);
    signal Aout, Bout : std_logic_vector(31 downto 0);
    signal ALUinA     : std_logic_vector(31 downto 0);
    signal Shft       : std_logic_vector(4 downto 0);
    signal ALUresult  : std_logic_vector(31 downto 0);
    signal Zero, Neg  : std_logic;

    -- write-back
    signal DselOut : std_logic_vector(4 downto 0);
    signal DinOut  : std_logic_vector(31 downto 0);

    -- address generation
    signal NSA, Rtn : std_logic_vector(31 downto 0);

    -- the shared memory data bus
    signal MemBus : std_logic_vector(31 downto 0);

    -- the register file runs on the inverted clock so that it commits on the
    -- falling edge with everything else
    signal RegClk : std_logic;

begin

    RegClk <= not SysClk;

    ----------------------------------------------------------------------------
    -- Field extraction. Pure wiring.
    ----------------------------------------------------------------------------
    rs_f    <= IRreg(25 downto 21);
    rt_f    <= IRreg(20 downto 16);
    rd_f    <= IRreg(15 downto 11);
    sa_f    <= IRreg(10 downto  6);
    immed_f <= IRreg(15 downto  0);
    index_f <= IRreg(25 downto  0);

    ----------------------------------------------------------------------------
    -- Instruction memory. Addressed by the PC.
    ----------------------------------------------------------------------------
    U_ROM : entity work.ROM
        port map (Addr => PCreg, Data => IMemData);

    ----------------------------------------------------------------------------
    -- Control
    ----------------------------------------------------------------------------
    U_DEC : entity work.Decoder
        port map (Instr => IRreg, Ctrl => Ctrl);

    ----------------------------------------------------------------------------
    -- The shared immediate extender: feeds the ALU AND the branch adder.
    ----------------------------------------------------------------------------
    U_XTND : entity work.ImmedXtnd
        port map (Immed16 => immed_f,
                  Xsel    => Ctrl.IR_Xsel,
                  Xlsft   => Ctrl.IR_Xlsft,
                  Xtnd32  => Xtnd32);

    ----------------------------------------------------------------------------
    -- Register file.  Asel = rt, Bsel = rs.
    ----------------------------------------------------------------------------
    U_RF : entity work.RegFile
        port map (Asel => rs_f,          -- *** BUG 1 ***  should be rt_f
                  Bsel => rt_f,          -- *** BUG 1 ***  should be rs_f
                  Dsel => DselOut,
                  Din  => DinOut,
                  Strb => Ctrl.RF_strb,
                  clk  => RegClk,
                  Aout => Aout,
                  Bout => Bout);

    ----------------------------------------------------------------------------
    -- ALU input selection and the shift-amount source
    ----------------------------------------------------------------------------
    U_AINMUX : entity work.Mux2
        generic map (W => 32)
        port map (A => Aout, B => Xtnd32, Sel => Ctrl.ALU_Asel, Y => ALUinA);

    U_SFTMUX : entity work.ALUsftMUX
        port map (SA => sa_f, Bout => Bout(4 downto 0),
                  Ssel => Ctrl.ALU_Ssel, Shft => Shft);

    U_ALU : entity work.ALU
        port map (Ain  => ALUinA,
                  Bin  => Bout,
                  Func => Ctrl.ALU_func,
                  Shft => Shft,
                  Rout => ALUresult,
                  Zero => Zero,
                  Neg  => Neg);

    ----------------------------------------------------------------------------
    -- Write-back selection
    --   destination : rd / rt / $31
    --   data        : ALU result / memory / return address
    ----------------------------------------------------------------------------
    U_DSELMUX : entity work.Mux3
        generic map (W => 5)
        port map (A => rd_f, B => rt_f, C => "11111",
                  Sel => Ctrl.RF_Wsel, Y => DselOut);

    U_DINMUX : entity work.Mux3
        generic map (W => 32)
        port map (A => ALUresult, B => MemBus, C => Rtn,
                  Sel => Ctrl.RF_Dsel, Y => DinOut);

    ----------------------------------------------------------------------------
    -- The shared memory data bus.
    --   On a load  : the RAM drives it.
    --   On a store : the register file drives it, through the TriBuffer.
    -- Exactly one driver at a time - enforced by RF_oe and by (en AND rw).
    ----------------------------------------------------------------------------
    U_TRI : entity work.TriBuffer
        port map (Din => Bout,           -- *** BUG 2 ***  should be Aout
                  Sel => Ctrl.RF_oe, Dout => MemBus);

    U_RAM : entity work.RAM
        port map (Addr => ALUresult,
                  Strb => Ctrl.DM_strb,
                  rw   => Ctrl.DM_rw,
                  en   => Ctrl.DM_en,
                  clk  => SysClk,
                  Data => MemBus);

    ----------------------------------------------------------------------------
    -- Next instruction address generation
    ----------------------------------------------------------------------------
    U_NIAG : entity work.NIAG
        port map (Index   => index_f,
                  Xtnd32  => Xtnd32,
                  RegAddr => Bout,
                  Sel     => Ctrl.NIAG_sel,
                  Cond    => Ctrl.NIAG_cond,
                  Strb    => Ctrl.NIAG_strb,
                  Zero    => Zero,
                  Neg     => Neg,
                  Rst     => Rst,
                  clk     => RegClk,      -- PC commits on the falling edge
                  PC      => PCreg,
                  NSA     => NSA,
                  Rtn     => Rtn);

    ----------------------------------------------------------------------------
    -- FETCH: the instruction register loads on the RISING edge.
    ----------------------------------------------------------------------------
    fetch : process (SysClk, Rst)
    begin
        if Rst = '1' then
            IRreg <= (others => '0');
            IRPC  <= (others => '0');
        elsif rising_edge(SysClk) then
            if Ctrl.IR_strb = IR_STRB_STROBE then
                IRreg <= IMemData;
                IRPC  <= PCreg;         -- remember where it came from
            end if;
        end if;
    end process fetch;

    ----------------------------------------------------------------------------
    -- Observation ports
    ----------------------------------------------------------------------------
    PC_out    <= IRPC;      -- the PC of the instruction being executed
    IR_out    <= IRreg;
    ALU_out   <= ALUresult;
    RegWr     <= Ctrl.RF_strb;
    RegWrAddr <= DselOut;
    RegWrData <= DinOut;
    MemBus_out <= MemBus;
    MemWr      <= '1' when (Ctrl.DM_en = DM_EN_ENABLE and
                            Ctrl.DM_rw = DM_RW_WR and
                            Ctrl.DM_strb = DM_STRB_STORE) else '0';

end architecture broken;


--------------------------------------------------------------------------------
-- THE ANSWERS.  Do not read these until you have worked the method.
--------------------------------------------------------------------------------
--
-- BUG 1: Asel and Bsel are swapped on the register file.
--
--   Correct:  Asel => rt_f,  Bsel => rs_f
--
--   Why it is subtle: for LUI, ADDI and BLEZ it makes NO DIFFERENCE, because
--   in those instructions rs and rt happen to name the same register, or the
--   one that differs is r0. Three of the four instruction types keep working.
--
--   It breaks SLL. SLL shifts the value in rt, read through Aout. With the
--   swap, Aout carries R[rs] - and for SLL r2,r2,1 the rs field is 0, so the
--   ALU shifts ZERO. r2 is written 0 every pass and never doubles.
--
--   SYMPTOM: the loop runs the right number of times, the branch behaves,
--   and r2 ends at 0 instead of 0x400.
--
-- BUG 2: the store value is taken from Bout instead of Aout.
--
--   Correct:  Din => Aout
--
--   SW stores the value in rt, which arrives on Aout. With Bout the CPU
--   stores R[rs], and for SW r2,0(r0) that is r0 - so it stores zero.
--
--   SYMPTOM: everything runs perfectly, r2 reaches 0x400, and the word
--   written to memory is 0.
--
--------------------------------------------------------------------------------
-- WHAT THE EXAMPLE IS ACTUALLY TEACHING
--------------------------------------------------------------------------------
--
-- Both bugs give the SAME headline symptom - "the stored word is not 0x400".
-- The symptom does not identify the bug.
--
-- What separates them is where they fail under the method:
--   BUG 1 shows a wrong value in the r2 write-back column of the trace.
--   BUG 2 shows a correct r2 all the way through, and a wrong value only on
--         the memory bus during the single SW cycle.
--
-- One is visible on almost every line of the trace; the other on exactly one.
-- That is why you read the trace instruction by instruction rather than
-- looking only at the final answer.
--------------------------------------------------------------------------------
