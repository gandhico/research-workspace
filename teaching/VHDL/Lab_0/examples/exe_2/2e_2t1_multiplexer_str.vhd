library ieee;
use ieee.std_logic_1164.all;

entity mux2_st is
    port (
        D0 : in  std_logic;
        D1 : in  std_logic;
        S  : in  std_logic;
        Y  : out std_logic
    );
end entity;

architecture structural of mux2_st is

    signal not_s : std_logic;
    signal w0    : std_logic;
    signal w1    : std_logic;

begin

    not_s <= not S;

    w0 <= D0 and not_s;
    w1 <= D1 and S;

    Y <= w0 or w1;

end architecture;

