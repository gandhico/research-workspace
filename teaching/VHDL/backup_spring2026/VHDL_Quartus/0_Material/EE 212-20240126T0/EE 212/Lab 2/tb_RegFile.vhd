--Zuriel Esparza
--7/07/2021

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

library EE_212_RegFile;
use EE_212_RegFile.RegFile_pkg.all;

Entity tb_RegFile is
	end entity;
	
architecture tb of tb_RegFile is

	signal	Asel	:	STD_LOGIC_VECTOR(4  DOWNTO 0);
	signal	Bsel	:	STD_LOGIC_VECTOR(4  DOWNTO 0);		
	signal	Dsel	:	STD_LOGIC_VECTOR(4  DOWNTO 0);	
	signal   Din	:	STD_LOGIC_VECTOR(31 DOWNTO 0);		
	signal	Strb	:	STD_LOGIC;								
	signal	Aout	:	STD_LOGIC_VECTOR(31 DOWNTO 0);		
	signal	Bout	:	STD_LOGIC_VECTOR(31 DOWNTO 0);	
	signal	clk   :  STD_LOGIC;
	signal  TbClock :  STD_LOGIC:='0';

	 
	constant TbPeriod : time := 10 ns;
	
begin
	dut : RegFile
	
	port map( Asel => Asel,
				 Bsel => Bsel,
				 Dsel => Dsel,
				 Din  => Din,
				 Strb => Strb,
				 Aout => Aout,
				 Bout => Bout,
				 clk  => clk);
				 
			TbClock <= not TbClock after TbPeriod/2;
			clk<=TbClock;
			
			
			stimuli : process
			begin
			
			wait for 10 ns;
				
				Asel <= "00000";
				Bsel <= "00000";

				
			wait for 10 ns;
				
				Dsel <= "00001";
				Din <= X"0000000F";
				Strb <='1';
				
			wait for 10 ns;
				
				Dsel <= "00010";
				Din <= X"0000000A";
				Strb <='1';
				
			wait for 10 ns;
			
				Asel <= "00001";
				Bsel <= "00010";
				Strb <='0';
				
			wait for 10 ns;
			
			
			
			
			wait;
		end process;
	end tb;
				