library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.ALU_Pkg.all;

entity ALU_SLL is
    port(
        A       : in  STD_LOGIC_VECTOR(31 downto 0);
        B       : in  STD_LOGIC_VECTOR(31 downto 0);
        FuncSel : in  STD_LOGIC_VECTOR(4 downto 0);
        Shift   : in  STD_LOGIC_VECTOR(4 downto 0);
        Result  : out STD_LOGIC_VECTOR(31 downto 0);
        S       : out STD_LOGIC;
        Z       : out STD_LOGIC
    );
end ALU_SLL;

architecture rtl of ALU_SLL is
    signal temp_result : STD_LOGIC_VECTOR(31 downto 0);
begin

    process(A, B, FuncSel, Shift)
        variable sh : integer range 0 to 31;
    begin
        temp_result <= (others => '0');

        if FuncSel = ALU_FUNC_SLL then
            sh := to_integer(unsigned(Shift));
            temp_result <= std_logic_vector(shift_left(unsigned(A), sh));
        end if;
    end process;

    Result <= temp_result;
    S <= temp_result(31);
    Z <= '1' when temp_result = x"00000000" else '0';

end rtl;