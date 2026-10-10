library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.DecodeLogic_Pkg.all;

entity DselMUX is
    port(
        Sel : in  STD_LOGIC_VECTOR(1 downto 0);
        Rd  : in  STD_LOGIC_VECTOR(4 downto 0);
        Rt  : in  STD_LOGIC_VECTOR(4 downto 0);
        Y   : out STD_LOGIC_VECTOR(4 downto 0)
    );
end DselMUX;

architecture Behavioral of DselMUX is
begin
    process(Sel, Rd, Rt)
    begin
        case Sel is
            when RF_WSEL_RD  => Y <= Rd;
            when RF_WSEL_RT  => Y <= Rt;
            when RF_WSEL_RET => Y <= RF_REG_1F;
            when others      => Y <= (others => '0');
        end case;
    end process;
end Behavioral;
