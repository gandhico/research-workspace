library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity NIAG_NSA is
    port(PC : in STD_LOGIC_VECTOR(31 downto 0); NSA : out STD_LOGIC_VECTOR(31 downto 0));
end NIAG_NSA;

architecture rtl of NIAG_NSA is
begin
    NSA <= STD_LOGIC_VECTOR(unsigned(PC) + 4);
end rtl;
