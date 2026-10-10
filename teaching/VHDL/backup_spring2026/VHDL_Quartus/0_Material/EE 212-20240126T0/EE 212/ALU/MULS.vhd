
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_MULS IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			HiReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			LoReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_MULS IS
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedBin		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedRout		:	SIGNED(63 DOWNTO 0);
	
BEGIN
	PROCESS(Func,Ain,Bin,SignedRout,SignedAin,SignedBin) IS
	BEGIN
		IF(Func = ALU_FUNC_MULS) THEN										
			SignedAin	<= SIGNED(Ain);
			SignedBin	<= SIGNED(Bin);
			Stat  		<= (others => 'Z');
			
			SignedRout <= SignedAin * SignedBin;	
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  <= SignedRout(31);
			
			LoReg <= STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0));	
			HiReg <= STD_LOGIC_VECTOR(SignedRout(63 DOWNTO 32));	
			Rout  <= STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0));	
		ELSE
			SignedAin <= (others => 'Z');
			SignedBin <= (others => 'Z');
			SignedRout <= (others => 'Z');
			HiReg <= (others => 'Z');
			LoReg <= (others => 'Z');
			Rout  <= (others => 'Z');
			Stat  <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
