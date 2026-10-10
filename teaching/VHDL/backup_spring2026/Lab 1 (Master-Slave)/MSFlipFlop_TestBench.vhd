library ieee;
use ieee.std_logic_1164.all;

-- Testbench entity:
-- A testbench has no external ports because it is only used
-- to simulate and verify the design behavior.
entity MS_FF_tb is
end entity;

-- Simulation architecture for the Master-Slave Flip-Flop testbench
architecture sim of MS_FF_tb is

    -- Test signals connected to the inputs and outputs of the UUT
    signal Reset_n : std_logic := '1';  -- Active-low reset, initially inactive
    signal Strobe  : std_logic := '0';  -- Clock-like control signal
    signal Data    : std_logic := '0';  -- Data input
    signal Q       : std_logic;         -- Normal output
    signal Qn      : std_logic;         -- Complemented output

begin

    -- Unit Under Test (UUT):
    -- Instantiates the Master-Slave Flip-Flop and connects
    -- the testbench signals to its ports.
    uut: entity work.MS_FF
        port map(
            Reset_n => Reset_n,
            Strobe  => Strobe,
            Data    => Data,
            Q       => Q,
            Qn      => Qn
        );

    -------------------------------------------------
    -- Clock generation process
    -- Creates a periodic strobe signal with a 10 ns period:
    -- 5 ns low and 5 ns high.
    -------------------------------------------------
    clock_process : process
    begin
        -- Generate clock pulses until simulation time reaches 100 ns
        while now < 100 ns loop
            Strobe <= '0';
            wait for 5 ns;

            Strobe <= '1';
            wait for 5 ns;
        end loop;

        -- Stop this process after the clock sequence is complete
        wait;
    end process;

    -------------------------------------------------
    -- Stimulus process
    -- Applies reset and data changes to verify the
    -- master-slave flip-flop behavior.
    -------------------------------------------------
    stimulus : process
    begin
        -- 1) Apply reset:
        -- Since Reset_n is active low, this forces the output to reset.
        Reset_n <= '0';
        wait for 8 ns;

        -- Release reset
        Reset_n <= '1';

        -- 2) Change Data before a rising edge:
        -- This value should be captured on the next effective transfer
        -- through the master-slave structure.
        wait for 4 ns;
        Data <= '1';

        -- 3) Change Data while Strobe = '1':
        -- In a master-slave flip-flop, a change here should not
        -- immediately affect the final output Q.
        wait for 10 ns;
        Data <= '0';

        -- 4) Change Data before the next rising edge:
        -- This prepares another value to be stored.
        wait for 8 ns;
        Data <= '1';

        -- 5) Hold Data constant for a while
        wait for 20 ns;

        -- 6) Apply reset again:
        -- This should clear the output regardless of the strobe state.
        wait for 8 ns;
        Reset_n <= '0';

        -- 7) Change Data while reset is active:
        -- Since reset is asserted, the output should remain reset.
        wait for 3 ns;
        Data <= '0';

        -- End simulation
        wait;
    end process;

end architecture;