--------------------------------------------------------------------------------
-- EE 362 - Lab 0, Example 3 - CORRECTED VERSION
-- decoder2to4 : 2-to-4 decoder with enable
--
--   D(k) = E . m_k(A1, A0)
--
--   D(0) = E.A1'.A0'     D(1) = E.A1'.A0
--   D(2) = E.A1 .A0'     D(3) = E.A1 .A0
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4 is
    port ( E  : in  std_logic;
           A1 : in  std_logic;
           A0 : in  std_logic;
           D  : out std_logic_vector(3 downto 0) );
end entity decoder2to4;

architecture behavioral of decoder2to4 is
    signal A : std_logic_vector(1 downto 0);
begin
    A <= A1 & A0;

    process (E, A)
    begin
        if E = '0' then
            D <= "0000";                    -- row 0: disabled
        else
            case A is
                when "00"   => D <= "0001"; -- row 1
                when "01"   => D <= "0010"; -- row 2
                when "10"   => D <= "0100"; -- row 3
                when "11"   => D <= "1000"; -- row 4
                when others => D <= "0000"; -- metavalues on A (simulation only)
            end case;
        end if;
    end process;
end architecture behavioral;
