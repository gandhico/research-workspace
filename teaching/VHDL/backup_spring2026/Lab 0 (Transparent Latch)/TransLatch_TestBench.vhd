library ieee;
use ieee.std_logic_1164.all;

-- Testbench entity:
-- A testbench has no input or output ports because it is only used
-- to simulate and verify the design.
entity Transparent_Latch_tb is
end;

-- Simulation architecture for the testbench
architecture sim of Transparent_Latch_tb is

    -- Test signals connected to the latch inputs and outputs
    signal Reset_n : std_logic := '1';  -- Active-low reset, initially inactive
    signal Gate    : std_logic := '0';  -- Gate control, initially closed
    signal Data    : std_logic := '0';  -- Data input, initially 0
    signal Q       : std_logic;         -- Normal output
    signal Qn      : std_logic;         -- Complemented output

begin

    -- Unit Under Test (UUT):
    -- Instantiates the Transparent_Latch design and connects the
    -- testbench signals to its ports.
    uut: entity work.Transparent_Latch
        port map(
            Reset_n => Reset_n,
            Gate    => Gate,
            Data    => Data,
            Q       => Q,
            Qn      => Qn
        );

    -- Stimulus process:
    -- Applies a sequence of input changes to verify reset,
    -- transparent behavior, and hold behavior.
    process
    begin
        -- Apply reset:
        -- Since Reset_n is active low, setting it to '0' forces Q to 0.
        Reset_n <= '0'; 
        wait for 10 ns;

        -- Release reset
        Reset_n <= '1';

        -- Transparent mode:
        -- When Gate = '1', the latch output should follow Data.
        Gate <= '1'; 
        wait for 10 ns;

        Data <= '1'; 
        wait for 15 ns;

        Data <= '0'; 
        wait for 13 ns;

        -- Hold mode:
        -- When Gate = '0', the latch should keep its previous value
        -- even if Data changes.
        Gate <= '0'; 
        wait for 17 ns;

        Data <= '1'; 
        wait for 15 ns;

        -- Apply reset again:
        -- This should force Q back to 0 immediately.
        Reset_n <= '0';

        -- Transparent mode again:
        -- Gate is opened again to let Q follow Data.
        Gate <= '1'; 
        wait for 10 ns;

        Data <= '1'; 
        wait for 15 ns;

        Data <= '0'; 
        wait for 13 ns;

        Data <= '1'; 
        wait for 13 ns;

        -- Hold mode again:
        -- Closing the gate makes the latch store the last value.
        Gate <= '0'; 
        wait for 17 ns;

        Data <= '0'; 
        wait for 15 ns;

        Data <= '1'; 
        wait for 13 ns;

        -- End simulation
        wait;
    end process;

end architecture;