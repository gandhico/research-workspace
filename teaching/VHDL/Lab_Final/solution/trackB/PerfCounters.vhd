--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track B REFERENCE  (TA only - also given to students)
--
-- PerfCounters : counts what the processor actually did
--
-- ============================================================================
-- WHY THIS IS INTERESTING ON A CPU WHERE CPI IS OBVIOUSLY 1
-- ============================================================================
-- Your CPU executes exactly one instruction per clock period, so measuring CPI
-- gives 1.000 and tells you nothing you did not already know.
--
-- The interesting measurement is the INSTRUCTION MIX: how many of each kind of
-- instruction the program actually executed. That number is a property of the
-- PROGRAM, not the hardware, and it is what lets you answer questions about
-- hardware you have not built:
--
--     "If loads took 3 cycles instead of 1, what would CPI become?"
--     "If every taken branch cost a 2-cycle penalty, what would CPI become?"
--
-- You cannot answer either without knowing the mix. That is why real
-- performance work starts with counting, not with modelling.
--
-- ============================================================================
-- HOW THE CLASSIFICATION WORKS
-- ============================================================================
-- Every instruction is classified from its CONTROL BUNDLE - which is to say,
-- from the control table you wrote in Labs 10 and 11. Nothing else is needed:
--
--     AluOps    RF_strb asserted and memory disabled
--     Loads     memory enabled, reading
--     Stores    memory enabled, writing
--     CtrlFlow  the next-PC source is not the sequential one
--
-- Those four are mutually exclusive and cover all eight instructions, so
--     AluOps + Loads + Stores + CtrlFlow = Cycles
-- and if that identity does not hold, your classification has a hole in it.
-- The testbench checks exactly that.
--
-- Counted on the FALLING edge - the commit point, so an instruction is counted
-- when it takes effect rather than when it is fetched.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.CPU_Pkg.all;

entity PerfCounters is
    port (
        clk    : in  std_logic;          -- the COMMIT clock (falling-edge domain)
        Rst    : in  std_logic;
        Enable : in  std_logic;          -- count only while the program runs
        Ctrl   : in  CTRL_REC;

        Cycles   : out unsigned(31 downto 0);
        AluOps   : out unsigned(31 downto 0);
        Loads    : out unsigned(31 downto 0);
        Stores   : out unsigned(31 downto 0);
        CtrlFlow : out unsigned(31 downto 0)
    );
end entity PerfCounters;

architecture rtl of PerfCounters is

    signal c_cyc, c_alu, c_ld, c_st, c_cf : unsigned(31 downto 0)
         := (others => '0');

begin

    process (clk, Rst)
    begin
        if Rst = '1' then
            c_cyc <= (others => '0');
            c_alu <= (others => '0');
            c_ld  <= (others => '0');
            c_st  <= (others => '0');
            c_cf  <= (others => '0');

        elsif rising_edge(clk) then         -- the commit edge
            if Enable = '1' then

                c_cyc <= c_cyc + 1;

                if Ctrl.NIAG_sel /= NIAG_SEL_NSA then
                    -- a branch or a jump: the next PC is not the sequential one
                    c_cf <= c_cf + 1;

                elsif Ctrl.DM_en = DM_EN_ENABLE then
                    if Ctrl.DM_rw = DM_RW_RD then
                        c_ld <= c_ld + 1;
                    else
                        c_st <= c_st + 1;
                    end if;

                elsif Ctrl.RF_strb = RF_STRB_STROBE then
                    c_alu <= c_alu + 1;
                end if;
                -- anything else is an instruction that does nothing observable

            end if;
        end if;
    end process;

    Cycles   <= c_cyc;
    AluOps   <= c_alu;
    Loads    <= c_ld;
    Stores   <= c_st;
    CtrlFlow <= c_cf;

end architecture rtl;
