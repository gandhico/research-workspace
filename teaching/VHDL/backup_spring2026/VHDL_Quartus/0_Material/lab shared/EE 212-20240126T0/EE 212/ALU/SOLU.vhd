
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_SOLU IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SOLU IS
	SIGNAL UnsignedAin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedBin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedRout		:	UNSIGNED(31 DOWNTO 0);
	
BEGIN
	UnsignedAin	<= UNSIGNED(Ain);
	UnsignedBin	<= UNSIGNED(Bin);
	
	PROCESS(Func,Ain,Bin,UnsignedAin,UnsignedBin,UnsignedRout) IS
	BEGIN
		IF(Func = ALU_FUNC_SOLU) THEN					
			Stat <= (others => 'Z');

			IF(UnsignedAin < UnsignedBin) THEN				
				UnsignedRout	<= to_unsigned(1, 32);
				Stat.ALU_zero  <= '0';
			ELSE
				UnsignedRout	<= to_unsigned(0, 32);
				Stat.ALU_zero  <= '1';
			END IF;
			
			Rout <= STD_LOGIC_VECTOR(UnsignedRout);			
		ELSE
			UnsignedAin<= (others => 'Z');
			UnsignedBin<=(others => 'Z');
		   UnsignedRout<=(others => 'Z');
			Rout	<= (others => 'Z');
			Stat	<= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
