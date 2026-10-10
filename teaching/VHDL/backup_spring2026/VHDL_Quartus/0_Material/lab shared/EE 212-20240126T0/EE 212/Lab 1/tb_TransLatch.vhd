--Name: Zuriel Esparza
--Date: 7/06/2021

Library IEEE;
use IEEE.std_logic_1164.all;

entity tb_TransLatch is 

end tb_TransLatch;

Architecture tb of tb_TransLatch is
		
		component TransLatch
			port (Reset: in std_logic;
					Data : in std_logic;
					Gate : in std_logic;
					Out_H: out std_logic;
					Out_L: out std_logic);
		end component;
		
		signal Reset : std_logic;
		signal Data  : Std_logic;
		signal Gate  : std_logic;
		signal Out_H : std_logic;
		signal Out_L : std_logic;
		
		
begin

	dut : TransLatch
	port map (Reset => Reset,
				 Data  => Data,
				 Gate  => Gate,
				 Out_H => Out_H,
				 Out_L => Out_L);
				 
	stimuli : process
	begin
	
	Reset <= '0';
	
	wait for 5ns;
	
	Reset <= '1';
	Gate  <= '1';
	Data  <= '0';
	
	wait for 5ns;
	
	
	Reset <= '1';
	Gate  <= '1';
	Data  <= '1';
	
	wait for 5ns; 
	
	
	Reset <= '1';
	Gate  <= '0';
	
	
		wait;
	end process;
	
end;