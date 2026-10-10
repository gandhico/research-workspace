library ieee;
use ieee.std_logic_1164.all;

entity full_adder_struct is
    port (
        A    : in  std_logic;
        B    : in  std_logic;
        Cin  : in  std_logic;
        Sum  : out std_logic;
        Cout : out std_logic
    );
end entity;

architecture structural of full_adder_struct is

    signal S1 : std_logic;
    signal C1 : std_logic;
    signal C2 : std_logic;

begin

    HA1 : entity work.half_adder
        port map (
            A => A,
            B => B,
            S => S1,
            C => C1
        );

    HA2 : entity work.half_adder
        port map (
            A => S1,
            B => Cin,
            S => Sum,
            C => C2
        );

    Cout <= C1 or C2;

end architecture;