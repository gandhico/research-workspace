library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.ALU_Pkg.all;

entity tb_ALU_SLL is
end tb_ALU_SLL;

architecture sim of tb_ALU_SLL is
    signal A       : STD_LOGIC_VECTOR(31 downto 0);
    signal B       : STD_LOGIC_VECTOR(31 downto 0);
    signal FuncSel : STD_LOGIC_VECTOR(4 downto 0);
    signal Shift   : STD_LOGIC_VECTOR(4 downto 0);
    signal Result  : STD_LOGIC_VECTOR(31 downto 0);
    signal S       : STD_LOGIC;
    signal Z       : STD_LOGIC;
begin

    UUT: entity work.ALU_SLL
        port map(
            A       => A,
            B       => B,
            FuncSel => FuncSel,
            Shift   => Shift,
            Result  => Result,
            S       => S,
            Z       => Z
        );

    process
    begin
        B <= (others => '0');
        FuncSel <= ALU_FUNC_SLL;

        A <= x"00000001";
        Shift <= "00001";
        wait for 10 ns;
        assert (Result = x"00000002" and S = '0' and Z = '0')
            report "FAIL: SLL test 1"
            severity error;

        A <= x"00000001";
        Shift <= "00100";
        wait for 10 ns;
        assert (Result = x"00000010" and S = '0' and Z = '0')
            report "FAIL: SLL test 2"
            severity error;

        A <= x"40000000";
        Shift <= "00001";
        wait for 10 ns;
        assert (Result = x"80000000" and S = '1' and Z = '0')
            report "FAIL: SLL test 3"
            severity error;

        A <= x"00000000";
        Shift <= "00101";
        wait for 10 ns;
        assert (Result = x"00000000" and S = '0' and Z = '1')
            report "FAIL: SLL test 4"
            severity error;

        wait;
    end process;

end sim;