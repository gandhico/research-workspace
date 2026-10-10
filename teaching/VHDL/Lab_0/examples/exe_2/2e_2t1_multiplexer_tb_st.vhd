library ieee;
use ieee.std_logic_1164.all;

entity mux2_tb_st is
end entity;

architecture test of mux2_tb_st is

    signal D0 : std_logic := '0';
    signal D1 : std_logic := '0';
    signal S  : std_logic := '0';
    signal Y  : std_logic;

begin

    dut : entity work.mux2_st
        port map (
            D0 => D0,
            D1 => D1,
            S  => S,
            Y  => Y
        );

    stimulus : process
    begin

        D0 <= '0'; D1 <= '1'; S <= '0';
        wait for 10 ns;
        assert Y = '0' severity error;

        S <= '1';
        wait for 10 ns;
        assert Y = '1' severity error;

        D0 <= '1'; D1 <= '0'; S <= '0';
        wait for 10 ns;
        assert Y = '1' severity error;

        S <= '1';
        wait for 10 ns;
        assert Y = '0' severity error;

        report "MUX test completed successfully"
            severity note;

        wait;
    end process;

end architecture;