library ieee;
use ieee.std_logic_1164.all;

entity mux2 is
    port (
        D0 : in  std_logic;
        D1 : in  std_logic;
        S  : in  std_logic;
        Y  : out std_logic
    );
end entity;

architecture structural of mux2 is begin 

 Y <= D0 when S = '0' else D1;

end architecture;