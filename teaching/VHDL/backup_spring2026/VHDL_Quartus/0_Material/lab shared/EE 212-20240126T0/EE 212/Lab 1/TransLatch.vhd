--Name: Zuriel Esparza
--Date: 7/06/2021

Library IEEE;
use IEEE.std_logic_1164.all;

entity TransLatch is 

port(Reset: in std_logic;
		Data: in std_logic;
		Gate: in std_logic;
		Out_H: out std_logic;
		Out_L: out std_logic);

end entity;

Architecture Behavioral of TransLatch is

begin

	process(Reset, Data, Gate)
	begin
	
		if Reset='0' then
			Out_H <='0';
			Out_L <= '1';
		else						--Reset='1'
			if Gate = '1' then
				Out_H <= Data;
				Out_L <= not Data;
			end if;
		end if;
		
	end process;
			

end Architecture;
