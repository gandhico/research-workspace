library ieee;
use ieee.std_logic_1164.all;

entity schematic1_tb is
end entity schematic1_tb;

architecture test of schematic1_tb is

    -- Declare the BDF design as a component
    component schematic1
        port (
            A : in  std_logic;
            B : in  std_logic;
            C : in  std_logic;
            Y : out std_logic
        );
    end component;

    signal A : std_logic := '0';
    signal B : std_logic := '0';
    signal C : std_logic := '0';
    signal Y : std_logic;

begin

    -- Instantiate schematic1.bdf
    DUT : schematic1
        port map (
            A => A,
            B => B,
            C => C,
            Y => Y
        );

    stimulus : process
    begin

        A <= '0'; B <= '0'; C <= '0';
        wait for 10 ns;
        assert Y = '0'
            report "ERROR: ABC = 000"
            severity error;

        A <= '0'; B <= '0'; C <= '1';
        wait for 10 ns;
        assert Y = '0'
            report "ERROR: ABC = 001"
            severity error;

        A <= '0'; B <= '1'; C <= '0';
        wait for 10 ns;
        assert Y = '0'
            report "ERROR: ABC = 010"
            severity error;

        A <= '0'; B <= '1'; C <= '1';
        wait for 10 ns;
        assert Y = '1'
            report "ERROR: ABC = 011"
            severity error;

        A <= '1'; B <= '0'; C <= '0';
        wait for 10 ns;
        assert Y = '0'
            report "ERROR: ABC = 100"
            severity error;

        A <= '1'; B <= '0'; C <= '1';
        wait for 10 ns;
        assert Y = '1'
            report "ERROR: ABC = 101"
            severity error;

        A <= '1'; B <= '1'; C <= '0';
        wait for 10 ns;
        assert Y = '1'
            report "ERROR: ABC = 110"
            severity error;

        A <= '1'; B <= '1'; C <= '1';
        wait for 10 ns;
        assert Y = '1'
            report "ERROR: ABC = 111"
            severity error;

        report "SUCCESS: all Majority-3 cases passed."
            severity note;

        wait;

    end process;

end architecture test;