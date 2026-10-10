library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity NIAG_Rtn is
    port(PC : in STD_LOGIC_VECTOR(31 downto 0); RtnAdrs : out STD_LOGIC_VECTOR(31 downto 0));
end NIAG_Rtn;

architecture rtl of NIAG_Rtn is
begin
    -- CPU block diagram shows return address = PC + 8.
    RtnAdrs <= STD_LOGIC_VECTOR(unsigned(PC) + 8);
end rtl;
