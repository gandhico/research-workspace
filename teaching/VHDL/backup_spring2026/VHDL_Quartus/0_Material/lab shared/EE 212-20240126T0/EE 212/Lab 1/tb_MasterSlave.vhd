--Name: Zuriel Esparza
--Date: 7/06/2021

Library IEEE;
use IEEE.std_logic_1164.all;

entity tb_MasterSlave is 

end tb_MasterSlave;

Architecture tb of tb_MasterSlave is
		
		component MasterSlave
			port (Reset: in std_logic;
					Data : in std_logic;
					Clock : in std_logic;
					Out_H: out std_logic;
					Out_L: out std_logic);
		end component;
		
		signal Reset : std_logic;
		signal Data  : Std_logic;
		signal Clock  : std_logic;
		signal Out_H : std_logic;
		signal Out_L : std_logic;
		
		
begin

	dut : MasterSlave
	port map (Reset => Reset,
				 Data  => Data,
				 Clock  => Clock,
				 Out_H => Out_H,
				 Out_L => Out_L);
				 
	stimuli : process
	begin
	
	Reset <= '0';
	
	wait for 5ns;
	
	Reset <= '1';
	Clock <= '0';
	Data  <= '1';
	
	
	wait for 5ns;
	
	Clock <= '1';
	
	wait for 5 ns;
	
	Clock <= '0';
	
	wait for 5 ns;
	
	Data <= '0';
	
	
		wait;
	end process;
	
end;