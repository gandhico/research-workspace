library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_SOLS IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SOLS IS
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedRout		:	SIGNED(31 DOWNTO 0);
	
BEGIN
	SignedAin	<= SIGNED(Ain);
	SignedBin	<= SIGNED(Bin);
	
	PROCESS(Func,SignedAin,SignedBin,SignedRout,Ain,Bin) IS
	BEGIN
		IF(Func = ALU_FUNC_SOLS) THEN						
			

			IF(SignedAin < SignedBin) THEN					
				SignedRout		<= to_signed(1, 32);
				Stat.ALU_zero  <= '0';
				Stat.ALU_sign  <= 'Z';
			ELSE
				SignedRout		<= to_signed(0, 32);
				Stat.ALU_zero  <= '1';
				Stat.ALU_sign  <= 'Z';
			END IF;
			
			Rout <= STD_LOGIC_VECTOR(SignedRout);				
			
		ELSE
			SignedAin<= (others => 'Z');	
		   SignedBin<= (others => 'Z');
		   SignedRout<= (others => 'Z');
			Rout	<= (others => 'Z');
			Stat	<= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
