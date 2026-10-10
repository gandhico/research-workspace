
library ieee;
use ieee.std_logic_1164.all;

entity majority3_structural is port 
( A : in std_logic ; B:in std_logic; C : in std_logic;
Y : out std_logic);
end entity;

architecture structural of majority3_structural is 

	signal AB_s : std_logic;
	signal AC_s : std_logic;
	signal BC_s : std_logic;
	
	begin
	
	AB_s <= A and B;
	AC_s <= A and C;
	BC_s <= B and C;
	
	Y <= AB_s or AC_s or BC_s;
	
end architecture;