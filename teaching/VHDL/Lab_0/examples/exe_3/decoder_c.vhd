library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4_c is
    port (
        E  : in  std_logic;
        A1 : in  std_logic;
        A0 : in  std_logic;
        D  : out std_logic_vector(3 downto 0)
    );
end entity decoder2to4_c;

architecture behavioral of decoder2to4_c is

    signal SEL : std_logic_vector(1 downto 0);

begin

    -- Explicitly create a 2-bit vector
    SEL <= A1 & A0;

    process(E, SEL)
    begin

        -- Default condition: decoder disabled
        D <= "0000";

        if E = '1' then

            case SEL is

                when "00" =>
                    D <= "0001";

                when "01" =>
                    D <= "0010";

                when "10" =>
                    D <= "0100";

                when "11" =>
                    D <= "1000";

                when others =>
                    D <= "0000";

            end case;

        end if;

    end process;

end architecture behavioral;