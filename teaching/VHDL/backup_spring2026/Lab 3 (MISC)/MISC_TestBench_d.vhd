library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.EE362Decoder.ALL;

-- Testbench entity:
-- A testbench has no ports because it is only used for simulation.
entity MISC_tb is
end MISC_tb;

architecture Behavioral of MISC_tb is

    -- Component declaration for the device under test
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
    signal SelExt : STD_LOGIC := IR_XSEL_ZERO;
    signal SelOE  : STD_LOGIC := RF_OE_HiZ;
    signal In16   : STD_LOGIC_VECTOR(15 downto 0) := (others => '0');
    signal TriIn  : STD_LOGIC := '0';
    signal Out32  : STD_LOGIC_VECTOR(31 downto 0);
    signal TriOut : STD_LOGIC;

begin

    -- Instantiate the DUT
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
    -- Verifies both extension modes and both tri-state modes.
    process
    begin

        --------------------------------------
        -- Test 1: Zero extension
        --------------------------------------
        In16   <= "1000000000000001";
        SelExt <= IR_XSEL_ZERO;
        wait for 20 ns;

        --------------------------------------
        -- Test 2: Sign extension
        --------------------------------------
        SelExt <= IR_XSEL_SIGN;
        wait for 20 ns;

        --------------------------------------
        -- Test 3: TriBuffer drives output
        --------------------------------------
        SelOE <= RF_OE_DRIVE;
        TriIn <= '1';
        wait for 20 ns;

        TriIn <= '0';
        wait for 20 ns;

        --------------------------------------
        -- Test 4: TriBuffer goes Hi-Z
        --------------------------------------
        SelOE <= RF_OE_HiZ;
        wait for 20 ns;

        wait;
    end process;

end Behavioral;