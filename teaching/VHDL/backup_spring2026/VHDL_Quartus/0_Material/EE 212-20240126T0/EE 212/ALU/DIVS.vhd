
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_DIVS IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_DIVS IS
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedInt		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedRem		:	SIGNED(31 DOWNTO 0);
	
BEGIN
	SignedAin	<= SIGNED(Ain);									
	SignedBin	<= SIGNED(Bin);
	
	PROCESS(Func,Ain,Bin,SignedAin,SignedBin,SignedInt,SignedRem) IS
	BEGIN
		IF(Func = ALU_FUNC_DIVS) THEN								
			Stat <= (others => 'Z');
			
			IF(SignedBin /= 0) THEN									
																	
				SignedInt	<= SignedAin / SignedBin;			
				SignedRem	<= SignedAin MOD SignedBin;		
				
				HiReg			<= STD_LOGIC_VECTOR(SignedRem);	
				LoReg			<= STD_LOGIC_VECTOR(SignedInt);	
				Rout  		<= STD_LOGIC_VECTOR(SignedInt);	      
				Stat.ALU_zero	<= '0';
			ELSE
				SignedInt <= (others => 'Z');
				SignedRem <= (others => 'Z');
 				HiReg	<= (others => 'Z');							
				LoReg	<= (others => 'Z');
				Rout  <= (others => 'Z');
				Stat.ALU_zero	<= '1';								
			END IF;	
		ELSE
			SignedInt <= (others => 'Z');
			SignedRem <= (others => 'Z');
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat  <= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
