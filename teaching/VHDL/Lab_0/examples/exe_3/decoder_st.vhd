library ieee;
use ieee.std_logic_1164.all;

entity decoder2to4_st is
    port (
        E  : in  std_logic;
        A1 : in  std_logic;
        A0 : in  std_logic;
        D  : out std_logic_vector(3 downto 0)
    );
end entity;

architecture structural of decoder2to4_st is

    signal nA1 : std_logic;
    signal nA0 : std_logic;

begin

    nA1 <= not A1;
    nA0 <= not A0;

    D(0) <= E and nA1 and nA0;
    D(1) <= E and nA1 and A0;
    D(2) <= E and A1  and nA0;
    D(3) <= E and A1  and A0;

end architecture;
