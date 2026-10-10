library ieee; use ieee.std_logic_1164.all;

entity mux_2t1 is port (
	D0, D1, S : in std_logic;
	y : out std_logic);
end entity mux_2t1;

architecture behavioral of mux_2t1 is begin

	y <= D0 when s = '0' else D1;
	
end architecture behavioral;