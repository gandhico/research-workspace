library ieee;
use ieee.std_logic_1164.all;

entity full_adder_tb is
end entity;

architecture test of full_adder_tb is

    signal A   : std_logic := '0';
    signal B   : std_logic := '0';
    signal Cin : std_logic := '0';

    signal Sum_beh    : std_logic;
    signal Cout_beh   : std_logic;

    signal Sum_struct  : std_logic;
    signal Cout_struct : std_logic;

begin

    DUT_BEH : entity work.full_adder_beh
        port map (
            A    => A,
            B    => B,
            Cin  => Cin,
            Sum  => Sum_beh,
            Cout => Cout_beh
        );

    DUT_STRUCT : entity work.full_adder_struct
        port map (
            A    => A,
            B    => B,
            Cin  => Cin,
            Sum  => Sum_struct,
            Cout => Cout_struct
        );

    stimulus : process
    begin

        A<='0'; B<='0'; Cin<='0';
        wait for 10 ns;
        assert Sum_beh='0' and Cout_beh='0'
           and Sum_struct='0' and Cout_struct='0'
        severity error;

        A<='0'; B<='0'; Cin<='1';
        wait for 10 ns;
        assert Sum_beh='1' and Cout_beh='0'
           and Sum_struct='1' and Cout_struct='0'
        severity error;

        A<='0'; B<='1'; Cin<='0';
        wait for 10 ns;
        assert Sum_beh='1' and Cout_beh='0'
           and Sum_struct='1' and Cout_struct='0'
        severity error;

        A<='0'; B<='1'; Cin<='1';
        wait for 10 ns;
        assert Sum_beh='0' and Cout_beh='1'
           and Sum_struct='0' and Cout_struct='1'
        severity error;

        A<='1'; B<='0'; Cin<='0';
        wait for 10 ns;
        assert Sum_beh='1' and Cout_beh='0'
           and Sum_struct='1' and Cout_struct='0'
        severity error;

        A<='1'; B<='0'; Cin<='1';
        wait for 10 ns;
        assert Sum_beh='0' and Cout_beh='1'
           and Sum_struct='0' and Cout_struct='1'
        severity error;

        A<='1'; B<='1'; Cin<='0';
        wait for 10 ns;
        assert Sum_beh='0' and Cout_beh='1'
           and Sum_struct='0' and Cout_struct='1'
        severity error;

        A<='1'; B<='1'; Cin<='1';
        wait for 10 ns;
        assert Sum_beh='1' and Cout_beh='1'
           and Sum_struct='1' and Cout_struct='1'
        severity error;

        report "SUCCESS: Full Adder test completed."
            severity note;

        wait;

    end process;

end architecture;