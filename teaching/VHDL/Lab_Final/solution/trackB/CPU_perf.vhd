--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track B REFERENCE  (TA only)
--
-- The Lab 12 CPU with PerfCounters instantiated. The ONLY changes are:
--   * five extra output ports
--   * one extra instantiation
--   * numeric_std added, because the counters are unsigned
--
-- Everything else is byte-identical to the Lab 12 CPU. That is the point of
-- the track: measurement should not require redesigning the thing measured.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.CPU_Pkg.all;

entity CPU_perf is
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
        MemWr      : out std_logic;

        -- Track B: performance counters
        Cycles     : out unsigned(31 downto 0);
        AluOps     : out unsigned(31 downto 0);
        Loads      : out unsigned(31 downto 0);
        Stores     : out unsigned(31 downto 0);
        CtrlFlow   : out unsigned(31 downto 0)
    );
end entity CPU_perf;

architecture structural of CPU_perf is

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
        port map (Asel => rt_f,
                  Bsel => rs_f,
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
        port map (Din => Aout, Sel => Ctrl.RF_oe, Dout => MemBus);

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
    -- Track B: the performance counters.
    -- Clocked on RegClk - the COMMIT edge - so an instruction is counted when
    -- it takes effect, not when it is fetched.
    ----------------------------------------------------------------------------
    U_PERF : entity work.PerfCounters
        port map (clk => RegClk, Rst => Rst, Enable => '1', Ctrl => Ctrl,
                  Cycles => Cycles, AluOps => AluOps, Loads => Loads,
                  Stores => Stores, CtrlFlow => CtrlFlow);

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

end architecture structural;
