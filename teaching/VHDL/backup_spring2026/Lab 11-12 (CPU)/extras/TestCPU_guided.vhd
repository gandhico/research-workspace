library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity TestCPU is
end TestCPU;

architecture sim of TestCPU is
    signal SysClk : STD_LOGIC := '0';
    constant Tclk : time := 20 ns;

    signal CycleCount : natural := 0;
begin
    --------------------------------------------------------------------------
    -- Device Under Test
    --------------------------------------------------------------------------
    DUT : entity work.CPU
        port map(
            SysClk => SysClk
        );

    --------------------------------------------------------------------------
    -- 50% duty-cycle system clock
    --
    -- One CPU instruction is intended to complete in one full SysClk cycle.
    -- With Tclk = 20 ns, this testbench runs for 110 cycles:
    --
    --     2200 ns / 20 ns = 110 cycles
    --
    -- That is long enough for the official ROM loop program to finish.
    --------------------------------------------------------------------------
    clk_process : process
    begin
        while now < 2200 ns loop
            SysClk <= '0';
            wait for Tclk/2;
            SysClk <= '1';
            wait for Tclk/2;
        end loop;

        report "Simulation clock stopped at 2200 ns." severity note;
        wait;
    end process;

    --------------------------------------------------------------------------
    -- Cycle counter
    --
    -- The CPU loads IR on the rising edge of SysClk. Counting rising edges
    -- gives students an easy way to match waveform activity to instruction
    -- execution.
    --------------------------------------------------------------------------
    cycle_counter : process(SysClk)
    begin
        if rising_edge(SysClk) then
            CycleCount <= CycleCount + 1;
        end if;
    end process;

    --------------------------------------------------------------------------
    -- Guided simulation checkpoints
    --
    -- This process does not directly read internal DUT signals, so it remains
    -- portable across most VHDL simulators. Instead, it tells students exactly
    -- what to inspect in the waveform viewer at meaningful moments.
    --------------------------------------------------------------------------
    guide_process : process
    begin
        report "Starting CPU simulation." severity note;
        report "Add these DUT internal signals to the waveform viewer:" severity note;
        report "  DUT.PCreg, DUT.IRreg, DUT.Ctrl" severity note;
        report "  DUT.Dbg_Reg1, DUT.Dbg_Reg2, DUT.Dbg_Reg3, DUT.Dbg_RAMWord0" severity note;
        report "  DUT.ALUout, DUT.NIAGout, DUT.MemDataBus" severity note;

        wait for 5 ns;
        report "Initial check: PCreg should begin at x""00000000""." severity note;

        wait until rising_edge(SysClk);
        wait for 1 ns;
        report "Cycle 1 rising edge: IRreg should load the first ROM instruction, LUI r1, 0x0B." severity note;

        wait until falling_edge(SysClk);
        wait for 1 ns;
        report "Cycle 1 falling edge: PCreg should update to the next instruction address." severity note;

        wait until rising_edge(SysClk);
        wait for 1 ns;
        report "Cycle 2: IRreg should show LUI r2, 1." severity note;

        wait until rising_edge(SysClk);
        wait for 1 ns;
        report "Cycle 3: loop begins with ADDI r1, r1, -1." severity note;

        wait for 400 ns;
        report "Mid-simulation check: r1 should be counting down and r2 should be doubling through the loop." severity note;
        report "Inspect DUT.Dbg_Reg1, DUT.Dbg_Reg2, DUT.ALUout, and DUT.NIAGout." severity note;

        wait for 800 ns;
        report "Branch/jump check: BLEZ should eventually exit the loop when r1 reaches zero." severity note;
        report "Inspect DUT.Ctrl.NIAG_sel, DUT.Ctrl.NIAG_cond, DUT.ALUout, and DUT.NIAGout." severity note;

        wait for 800 ns;
        report "Final check: after the SW instruction, DUT.Dbg_RAMWord0 should be x""00000400""." severity note;
        report "If DUT.Dbg_RAMWord0 = x""00000400"", the official program stored decimal 1024 into RAM word 0." severity note;

        wait;
    end process;
end sim;
