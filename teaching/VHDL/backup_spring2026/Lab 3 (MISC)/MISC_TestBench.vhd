library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity MISC_tb is
end MISC_tb;

architecture Behavioral of MISC_tb is

    -- Component declaration
    component MISC
        Port (
            SelExt  : in  STD_LOGIC;
            SelOE   : in  STD_LOGIC;
            In16    : in  STD_LOGIC_VECTOR(15 downto 0);
            TriIn   : in  STD_LOGIC;
            Out32   : out STD_LOGIC_VECTOR(31 downto 0);
            TriOut  : out STD_LOGIC
        );
    end component;

    -- Test signals
    signal SelExt  : STD_LOGIC := '0';
    signal SelOE   : STD_LOGIC := '0';
    signal In16    : STD_LOGIC_VECTOR(15 downto 0);
    signal TriIn   : STD_LOGIC := '0';
    signal Out32   : STD_LOGIC_VECTOR(31 downto 0);
    signal TriOut  : STD_LOGIC;

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

    -- Stimulus process
    process
    begin

        --------------------------------------
        -- Test 1: Zero Extension
        --------------------------------------
        In16   <= "1000000000000001";
        SelExt <= '0';  -- Zero extend
        wait for 20 ns;

        --------------------------------------
        -- Test 2: Sign Extension
        --------------------------------------
        SelExt <= '1';  -- Sign extend
        wait for 20 ns;

        --------------------------------------
        -- Test 3: TriBuffer Enabled
        --------------------------------------
        SelOE <= '1';
        TriIn <= '1';
        wait for 20 ns;

        TriIn <= '0';
        wait for 20 ns;

        --------------------------------------
        -- Test 4: TriBuffer Disabled (Hi-Z)
        --------------------------------------
        SelOE <= '0';
        wait for 20 ns;

        wait;
    end process;

end Behavioral;