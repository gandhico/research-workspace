library ieee;
use ieee.std_logic_1164.all;

entity half_adder is
    port (
        A : in  std_logic;
        B : in  std_logic;
        S : out std_logic;
        C : out std_logic
    );
end entity;

architecture rtl of half_adder is
begin

    S <= A xor B;
    C <= A and B;

end architecture;