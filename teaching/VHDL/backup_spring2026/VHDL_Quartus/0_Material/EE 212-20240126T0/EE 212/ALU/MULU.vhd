-------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_MULU IS
	PORT(	Ain		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin		:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_MULU IS
	SIGNAL UnsignedAin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedBin		:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedRout		:	UNSIGNED(63 DOWNTO 0);
	
BEGIN
	PROCESS(Func,Ain,Bin,UnsignedAin,UnsignedBin,UnsignedRout) IS
	BEGIN
		IF(Func = ALU_FUNC_MULU) THEN										
			UnsignedAin	<= UNSIGNED(Ain);
			UnsignedBin	<= UNSIGNED(Bin);
			Stat  <= (others => 'Z');
			
			UnsignedRout <= UnsignedAin * UnsignedBin;		     
			
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(UnsignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  <= UnsignedRout(31);
			
			LoReg <= STD_LOGIC_VECTOR(UnsignedRout(31 DOWNTO 0));
			HiReg <= STD_LOGIC_VECTOR(UnsignedRout(63 DOWNTO 32));
			Rout  <= STD_LOGIC_VECTOR(UnsignedRout(31 DOWNTO 0));	
		ELSE
			UnsignedAin <= (others => 'Z');
			UnsignedBin <= (others => 'Z');
			UnsignedRout <= (others => 'Z');
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat  <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
