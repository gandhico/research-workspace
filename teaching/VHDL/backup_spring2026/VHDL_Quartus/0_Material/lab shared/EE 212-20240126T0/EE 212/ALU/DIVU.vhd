
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_DIVU IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_DIVU IS
	SIGNAL unSignedAin	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedBin	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedInt	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL unSignedRem	:	UNSIGNED(31 DOWNTO 0);
	
BEGIN
	unSignedAin	<= UNSIGNED(Ain);									
	unSignedBin	<= UNSIGNED(Bin);
	
	PROCESS(Func,unSignedAin,unSignedBin,unSignedInt,unSignedRem, Ain,Bin) IS
	BEGIN
		IF(Func = ALU_FUNC_DIVU) THEN							
			Stat <= (others => 'Z');
			
			IF(unSignedBin /= 0) THEN							
																
				unSignedInt	<= unSignedAin / unSignedBin;		
				unSignedRem	<= unSignedAin MOD unSignedBin;	   
				
				HiReg			<= STD_LOGIC_VECTOR(unSignedRem);
				LoReg			<= STD_LOGIC_VECTOR(unSignedInt);
				Rout  		<= STD_LOGIC_VECTOR(UnsignedInt);  
				Stat.ALU_zero	<= '0';
			ELSE								
				unSignedInt <= (others => 'Z');
				unSignedRem <= (others => 'Z');
				HiReg <= (others => 'Z');						
				LoReg <= (others => 'Z');
				Rout  <= (others => 'Z');
				Stat.ALU_zero	<= '1';							
			END IF;	
		ELSE
			unSignedInt <= (others => 'Z');
			unSignedRem <= (others => 'Z');
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;	
	END PROCESS;
END ARCHITECTURE;
