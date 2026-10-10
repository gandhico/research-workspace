Library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

Entity ALU_arithmetic is

port(Ain : in std_logic_vector(7 downto 0);
	  Bin : in std_logic_vector(7 downto 0);
	  Result : out std_logic_vector(7 downto 0);
	  pin : out std_logic);
	  
end entity;

architecture behavioral of ALU_arithmetic is

signal Ain_u : signed(7 downto 0);
signal Bin_u : signed(7 downto 0);
signal result_u : signed(7 downto 0);

signal remainder : signed(7 downto 0);

begin

Ain_u <= signed(Ain);
Bin_u <= signed(Bin);

Result_u <= Ain_u / Bin_u;
Remainder <= Ain_u MOD Bin_u;


Result <= std_logic_vector(Result_u);

pin <= '1' when Result_u = -1 else '0';

end architecture;

