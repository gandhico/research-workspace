--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track B REFERENCE testbench  (TA only)
--
-- Runs the Lab 12 program on the instrumented CPU, reports the instruction mix,
-- and then uses that mix to compute CPI for THREE machines - one of which you
-- built, and two of which you did not.
--
-- That last part is the point of the track. A measured instruction mix lets you
-- answer performance questions about hardware that does not exist yet, which is
-- what performance analysis is actually for.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_trackB is
end entity tb_trackB;

architecture test of tb_trackB is

    constant PERIOD : time := 20 ns;

    signal SysClk : std_logic := '0';
    signal Rst    : std_logic := '1';

    signal PC_out, IR_out, ALU_out, RegWrData, MemBus_out
         : std_logic_vector(31 downto 0);
    signal RegWr, MemWr : std_logic;
    signal RegWrAddr : std_logic_vector(4 downto 0);

    signal Cycles, AluOps, Loads, Stores, CtrlFlow : unsigned(31 downto 0);

    signal running : boolean := true;

    -- Integer CPI, reported in thousandths so no floating point is needed.
    function cpi_milli (cyc, instr : natural) return natural is
    begin
        return (cyc * 1000) / instr;
    end function;

begin

    DUT : entity work.CPU_perf
        port map (SysClk => SysClk, Rst => Rst,
                  PC_out => PC_out, IR_out => IR_out, ALU_out => ALU_out,
                  RegWr => RegWr, RegWrAddr => RegWrAddr,
                  RegWrData => RegWrData,
                  MemBus_out => MemBus_out, MemWr => MemWr,
                  Cycles => Cycles, AluOps => AluOps, Loads => Loads,
                  Stores => Stores, CtrlFlow => CtrlFlow);

    clock_gen : process
    begin
        while running loop
            SysClk <= '0'; wait for PERIOD / 2;
            SysClk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    stimulus : process
        variable errors : natural := 0;
        variable n_cyc, n_alu, n_ld, n_st, n_cf, n_tot : natural;
        variable hyp : natural;
    begin

        Rst <= '1';
        wait for PERIOD * 2;
        wait for PERIOD / 4;
        Rst <= '0';

        -- Run exactly the 45 instructions of the program and stop counting.
        wait for PERIOD * 45;

        n_cyc := to_integer(Cycles);
        n_alu := to_integer(AluOps);
        n_ld  := to_integer(Loads);
        n_st  := to_integer(Stores);
        n_cf  := to_integer(CtrlFlow);
        n_tot := n_alu + n_ld + n_st + n_cf;

        report "======== INSTRUCTION MIX ========" severity note;
        report "  cycles          " & integer'image(n_cyc) severity note;
        report "  ALU operations  " & integer'image(n_alu) severity note;
        report "  loads           " & integer'image(n_ld)  severity note;
        report "  stores          " & integer'image(n_st)  severity note;
        report "  control flow    " & integer'image(n_cf)  severity note;
        report "  classified      " & integer'image(n_tot) severity note;

        ------------------------------------------------------------------
        -- The classification must be complete. If these four classes do not
        -- add up to the cycle count, the classification has a hole in it.
        ------------------------------------------------------------------
        if n_tot /= n_cyc then
            report "FAIL: the four classes sum to " & integer'image(n_tot) &
                   " but " & integer'image(n_cyc) & " cycles elapsed - the " &
                   "classification is not exhaustive" severity error;
            errors := errors + 1;
        end if;

        if n_cyc /= 45 then
            report "FAIL: expected 45 instructions, counted " &
                   integer'image(n_cyc) severity error;
            errors := errors + 1;
        end if;

        -- The expected mix for this program:
        --   2 LUI + 11 ADDI + 10 SLL = 23 ALU ops
        --   11 BLEZ + 10 J           = 21 control flow
        --   1 SW                     =  1 store
        if n_alu /= 23 then
            report "FAIL: expected 23 ALU operations, got " &
                   integer'image(n_alu) severity error;
            errors := errors + 1;
        end if;
        if n_cf /= 21 then
            report "FAIL: expected 21 control-flow instructions, got " &
                   integer'image(n_cf) severity error;
            errors := errors + 1;
        end if;
        if n_st /= 1 then
            report "FAIL: expected 1 store, got " & integer'image(n_st)
                severity error;
            errors := errors + 1;
        end if;

        ------------------------------------------------------------------
        -- Now use the mix to reason about machines you did NOT build.
        ------------------------------------------------------------------
        report "======== CPI ========" severity note;

        report "  as built (every instruction 1 cycle):  CPI = " &
               integer'image(cpi_milli(n_cyc, n_cyc)) & " / 1000"
            severity note;

        -- Hypothetical 1: memory takes 3 cycles instead of 1.
        hyp := n_alu + n_cf + (n_ld + n_st) * 3;
        report "  if memory took 3 cycles:               CPI = " &
               integer'image(cpi_milli(hyp, n_cyc)) & " / 1000"
            severity note;

        -- Hypothetical 2: every control-flow instruction costs 2 extra cycles.
        hyp := n_alu + n_ld + n_st + n_cf * 3;
        report "  if control flow cost 2 extra cycles:   CPI = " &
               integer'image(cpi_milli(hyp, n_cyc)) & " / 1000"
            severity note;

        report "Note which hypothetical hurts more, and why: this program is " &
               "47% control flow and 2% memory. Speeding up the wrong thing " &
               "buys almost nothing - which is Amdahl's law, measured rather " &
               "than quoted." severity note;

        if errors = 0 then
            report "PASS - Track B: instruction mix measured and classification complete."
                severity note;
        else
            report "FAILED - Track B: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
