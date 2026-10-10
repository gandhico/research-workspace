library ieee;
use ieee.std_logic_1164.all;

entity majority3_tb is
end entity;

architecture test of majority3_tb is

    signal A : std_logic := '0';
    signal B : std_logic := '0';
    signal C : std_logic := '0';
    signal Y : std_logic;

begin

    dut : entity work.majority3
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
        assert Y = '0' report "Error 000" severity error;

        A <= '0'; B <= '0'; C <= '1';
        wait for 10 ns;
        assert Y = '0' report "Error 001" severity error;

        A <= '0'; B <= '1'; C <= '0';
        wait for 10 ns;
        assert Y = '0' report "Error 010" severity error;

        A <= '0'; B <= '1'; C <= '1';
        wait for 10 ns;
        assert Y = '1' report "Error 011" severity error;

        A <= '1'; B <= '0'; C <= '0';
        wait for 10 ns;
        assert Y = '0' report "Error 100" severity error;

        A <= '1'; B <= '0'; C <= '1';
        wait for 10 ns;
        assert Y = '1' report "Error 101" severity error;

        A <= '1'; B <= '1'; C <= '0';
        wait for 10 ns;
        assert Y = '1' report "Error 110" severity error;

        A <= '1'; B <= '1'; C <= '1';
        wait for 10 ns;
        assert Y = '1' report "Error 111" severity error;

        report "Majority test completed successfully"
            severity note;

        wait;
    end process;

end architecture;