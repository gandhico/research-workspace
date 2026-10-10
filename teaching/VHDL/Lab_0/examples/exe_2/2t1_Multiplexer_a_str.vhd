library ieee; use ieee.std_logic_1164.all;

entity mux_2t1_str is 
port (
	D0 : in std_logic;
	D1 : in std_logic;
	S : in std_logic;
	Y : out std_logic);
end entity mux_2t1_str;

architecture structural of mux_2t1_str is

	signal not_S : std_logic;
	signal w0 : std_logic;
	signal w1 : std_logic;
	
 begin

	not_S <= not S;
	
	w0 <= D0 and not_S;
	
	w1 <= D1 and S;
	
	Y <= w0 or w1;
	
end architecture structural;