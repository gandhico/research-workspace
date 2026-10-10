library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4_tb is
end entity;

architecture test of decoder2to4_tb is

    signal E  : std_logic := '0';
    signal A1 : std_logic := '0';
    signal A0 : std_logic := '0';
    signal D  : std_logic_vector(3 downto 0);

begin

    dut : entity work.decoder2to4_st
        port map (
            E  => E,
            A1 => A1,
            A0 => A0,
            D  => D
        );

    stimulus : process
    begin

        E <= '0';
        wait for 10 ns;
        assert D = "0000" severity error;

        E <= '1'; A1 <= '0'; A0 <= '0';
        wait for 10 ns;
        assert D = "0001" severity error;

        A1 <= '0'; A0 <= '1';
        wait for 10 ns;
        assert D = "0010" severity error;

        A1 <= '1'; A0 <= '0';
        wait for 10 ns;
        assert D = "0100" severity error;

        A1 <= '1'; A0 <= '1';
        wait for 10 ns;
        assert D = "1000" severity error;

        report "Decoder test completed successfully"
            severity note;

        wait;

    end process;

end architecture;