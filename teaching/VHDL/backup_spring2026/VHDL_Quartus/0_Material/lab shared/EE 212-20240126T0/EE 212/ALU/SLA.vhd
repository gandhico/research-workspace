library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_MISC.ALL;

LIBRARY EE_212_ALU;
USE EE_212_ALU.ALU_pkg.all;

ENTITY ALU_SLA IS
	PORT(	Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
			Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Shft	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
			Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
			Stat	:	OUT	STAT_SIGNL_REC);
END ENTITY;

ARCHITECTURE Behavioral OF ALU_SLA IS
	SIGNAL SignedRout		:	SIGNED(31 DOWNTO 0);
	SIGNAL SignedAin		:	SIGNED(31 DOWNTO 0);
	SIGNAL NaturalShift	:	NATURAL;

	BEGIN
	PROCESS(Func,Ain,Shft,SignedRout,SignedAin,NaturalShift) IS
	BEGIN
		IF(Func = ALU_FUNC_SLA) THEN
			Stat				<= (others => 'Z');
			SignedAin		<= SIGNED(Ain);
			NaturalShift	<= to_integer(unsigned(Shft));
			
			SignedRout 		<= shift_left(SignedAin, NaturalShift);
			
			Stat.ALU_zero  	<= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SignedRout(31 DOWNTO 0))));
			Stat.ALU_sign  	<= SignedRout(31);
			
			Rout	<= STD_LOGIC_VECTOR(SignedRout);
		ELSE
			SignedRout	<= (others => 'Z');
			SignedAin	<= (others => 'Z');
			NaturalShift	<= 0;
			Rout <= (others => 'Z');
			Stat <= (others => 'Z');
		END IF;
	END PROCESS;
END ARCHITECTURE;
