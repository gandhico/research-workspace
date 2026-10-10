--Name: Zuriel Esparza
--Date: 7/06/2021

Library IEEE;
use IEEE.std_logic_1164.all;

entity MasterSlave is 

port(Reset: in std_logic;
		Data: in std_logic;
		Clock: in std_logic;
		Out_H: out std_logic;
		Out_L: out std_logic);

end entity;

Architecture Behavioral of MasterSlave is

	signal Clock_not : std_logic;
	signal Q_1D      : std_logic;
	
component TransLatch

port(Reset: in std_logic;
		Data: in std_logic;
		Gate: in std_logic;
		Out_H: out std_logic;
		Out_L: out std_logic);

end component;

begin

	Clock_not <= not Clock;
	
	L0: TransLatch port map(Reset, Data, Clock_not, Q_1D,open);
	L1: TransLatch port map(Reset, Q_1D, Clock, Out_H, Out_L);
	
end Architecture;