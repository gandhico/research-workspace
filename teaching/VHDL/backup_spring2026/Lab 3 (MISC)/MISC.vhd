library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Testbench entity:
-- A testbench has no ports because it is only used for simulation.
entity MISC_tb is
end MISC_tb;

architecture Behavioral of MISC_tb is

    -- Component declaration for the DUT
    component MISC
        Port (
            SelExt : in  STD_LOGIC;
            SelOE  : in  STD_LOGIC;
            In16   : in  STD_LOGIC_VECTOR(15 downto 0);
            TriIn  : in  STD_LOGIC;
            Out32  : out STD_LOGIC_VECTOR(31 downto 0);
            TriOut : out STD_LOGIC
        );
    end component;

    -- Test signals
    -- No decoder constants are used in this testbench.
    -- Control meanings:
    --   SelExt = '0' -> zero extend
    --   SelExt = '1' -> sign extend
    --   SelOE  = '1' -> drive TriOut
    --   SelOE  = '0' -> TriOut = Hi-Z
    signal SelExt : STD_LOGIC := '0';
    signal SelOE  : STD_LOGIC := '0';
    signal In16   : STD_LOGIC_VECTOR(15 downto 0);
    signal TriIn  : STD_LOGIC := '0';
    signal Out32  : STD_LOGIC_VECTOR(31 downto 0);
    signal TriOut : STD_LOGIC;

begin

    -- Instantiate DUT (Device Under Test)
    DUT: MISC
        port map (
            SelExt => SelExt,
            SelOE  => SelOE,
            In16   => In16,
            TriIn  => TriIn,
            Out32  => Out32,
            TriOut => TriOut
        );

    -- Stimulus process:
    -- Applies test values to verify both the extender and tri-state buffer.
    process
    begin

        --------------------------------------
        -- Test 1: Zero extension
        -- SelExt = '0' means upper 16 bits should become zeros
        --------------------------------------
        In16   <= "1000000000000001";
        SelExt <= '0';
        wait for 20 ns;

        --------------------------------------
        -- Test 2: Sign extension
        -- SelExt = '1' means upper 16 bits copy In16(15)
        --------------------------------------
        SelExt <= '1';
        wait for 20 ns;

        --------------------------------------
        -- Test 3: TriBuffer enabled
        -- SelOE = '1' means TriOut follows TriIn
        --------------------------------------
        SelOE <= '1';
        TriIn <= '1';
        wait for 20 ns;

        TriIn <= '0';
        wait for 20 ns;

        --------------------------------------
        -- Test 4: TriBuffer disabled
        -- SelOE = '0' means TriOut goes to Hi-Z
        --------------------------------------
        SelOE <= '0';
        wait for 20 ns;

        -- End simulation
        wait;
    end process;

end Behavioral;