
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_SLL IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SLL IS
	SIGNAL UnsignedRout	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL UnsignedAin	:	UNSIGNED(31 DOWNTO 0);
	SIGNAL NaturalShift	:	Integer;

	BEGIN
	PROCESS(Func,Ain,Shft,UnsignedRout,UnsignedAin,NaturalShift) IS
	BEGIN
		IF(Func = ALU_FUNC_SLL) THEN
			Stat				<= (others => 'Z');
			
			UnsignedAin		<= UNSIGNED(Ain);
			NaturalShift	<= to_integer(unsigned(Shft));
			
			UnsignedRout 	<= shift_left(UnsignedAin, NaturalShift);
			
			Stat.ALU_zero  <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(UnsignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  <= UnsignedRout(31);
			
			Rout	<= STD_LOGIC_VECTOR(UnsignedRout);
		ELSE
			UnsignedRout<= (others => 'Z');
		   UnsignedAin<= (others => 'Z');
		   NaturalShift<= 0;
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
