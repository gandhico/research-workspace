library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.DecodeLogic_Pkg.all;

entity DinMUX is
    port(
        Sel : in  STD_LOGIC_VECTOR(1 downto 0);
        In0 : in  STD_LOGIC_VECTOR(31 downto 0);
        In1 : in  STD_LOGIC_VECTOR(31 downto 0);
        In2 : in  STD_LOGIC_VECTOR(31 downto 0);
        Y   : out STD_LOGIC_VECTOR(31 downto 0)
    );
end DinMUX;

architecture Behavioral of DinMUX is
begin
    process(Sel, In0, In1, In2)
    begin
        case Sel is
            when RF_DSEL_ALU => Y <= In0;
            when RF_DSEL_MEM => Y <= In1;
            when RF_DSEL_RET => Y <= In2;
            when others      => Y <= (others => '0');
        end case;
    end process;
end Behavioral;
