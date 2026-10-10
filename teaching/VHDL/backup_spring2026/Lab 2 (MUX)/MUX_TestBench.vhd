libralibrary IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Testbench entity:
-- This module has no ports because it is only used for simulation.
entity MUXtest is
end MUXtest;

-- Behavioral architecture for the testbench
architecture Behavioral of MUXtest is

    -------------------------------------------------
    -- Component declarations
    -- These describe the modules that will be tested
    -------------------------------------------------

    -- 2-to-1 multiplexer for 32-bit inputs
    component ALUinMUX
        Port (
            Sel : in STD_LOGIC;
            In0, In1 : in STD_LOGIC_VECTOR(31 downto 0);
            Y : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    -- 3-to-1 multiplexer for 32-bit inputs
    component DinMUX
        Port (
            Sel : in STD_LOGIC_VECTOR(1 downto 0);
            In0, In1, In2 : in STD_LOGIC_VECTOR(31 downto 0);
            Y : out STD_LOGIC_VECTOR(31 downto 0)
        );
    end component;

    -- 2-to-1 multiplexer for 5-bit inputs
    component ALUshftMUX
        Port (
            Sel : in STD_LOGIC;
            In0, In1 : in STD_LOGIC_VECTOR(4 downto 0);
            Y : out STD_LOGIC_VECTOR(4 downto 0)
        );
    end component;

    -- 3-to-1 multiplexer for 5-bit inputs
    component DselMUX
        Port (
            Sel : in STD_LOGIC_VECTOR(1 downto 0);
            In0, In1, In2 : in STD_LOGIC_VECTOR(4 downto 0);
            Y : out STD_LOGIC_VECTOR(4 downto 0)
        );
    end component;

    -------------------------------------------------
    -- Internal signals
    -------------------------------------------------

    -- Select signal for 2-to-1 multiplexers
    signal Sel1 : STD_LOGIC := '0';

    -- Select signal for 3-to-1 multiplexers
    signal Sel2 : STD_LOGIC_VECTOR(1 downto 0) := "00";

    -- 32-bit test inputs and outputs
    signal A0_32, A1_32, A2_32 : STD_LOGIC_VECTOR(31 downto 0);
    signal Y32a, Y32b          : STD_LOGIC_VECTOR(31 downto 0);

    -- 5-bit test inputs and outputs
    signal A0_5, A1_5, A2_5 : STD_LOGIC_VECTOR(4 downto 0);
    signal Y5a, Y5b         : STD_LOGIC_VECTOR(4 downto 0);

begin

    -------------------------------------------------
    -- Component instantiations
    -- Each unit is connected to the corresponding
    -- test signals
    -------------------------------------------------

    -- Test 2-to-1 mux for 32-bit inputs
    U1: ALUinMUX 
        port map (Sel1, A0_32, A1_32, Y32a);

    -- Test 3-to-1 mux for 32-bit inputs
    U2: DinMUX 
        port map (Sel2, A0_32, A1_32, A2_32, Y32b);

    -- Test 2-to-1 mux for 5-bit inputs
    U3: ALUshftMUX 
        port map (Sel1, A0_5, A1_5, Y5a);

    -- Test 3-to-1 mux for 5-bit inputs
    U4: DselMUX 
        port map (Sel2, A0_5, A1_5, A2_5, Y5b);

    -------------------------------------------------
    -- Stimulus process
    -- Applies test values to the multiplexers and
    -- changes the select signals over time
    -------------------------------------------------
    process
    begin
        -- Assign fixed values to 32-bit inputs
        A0_32 <= x"AAAAAAAA";  -- Alternating 1010...
        A1_32 <= x"55555555";  -- Alternating 0101...
        A2_32 <= x"FFFFFFFF";  -- All ones

        -- Assign fixed values to 5-bit inputs
        A0_5 <= "00001";
        A1_5 <= "10101";
        A2_5 <= "11111";

        -- First test:
        -- Sel1 = 0 selects In0 in 2-to-1 muxes
        -- Sel2 = 00 selects In0 in 3-to-1 muxes
        Sel1 <= '0';
        Sel2 <= "00";
        wait for 20 ns;

        -- Second test:
        -- Sel1 = 1 selects In1 in 2-to-1 muxes
        -- Sel2 = 01 selects In1 in 3-to-1 muxes
        Sel1 <= '1';
        Sel2 <= "01";
        wait for 20 ns;

        -- Third test:
        -- Sel2 = 10 selects In2 in 3-to-1 muxes
        -- Sel1 remains unchanged
        Sel2 <= "10";
        wait for 20 ns;

        -- End simulation
        wait;
    end process;

end Behavioral;