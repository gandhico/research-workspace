library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity NIAG_Reg is
    port(Reg : in STD_LOGIC_VECTOR(31 downto 0); RegAdrs : out STD_LOGIC_VECTOR(31 downto 0));
end NIAG_Reg;

architecture rtl of NIAG_Reg is
begin
    RegAdrs <= Reg;
end rtl;
