--Alvaro Esparza
--February 16, 2021

Library IEEE;
use IEEE.STD_LOGIC_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Use IEEE.NUMERIC_STD.all;
Use IEEE.STD_LOGIC_MISC.all;


entity ALU_MULS is

port(			Ain	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Bin	:	IN		STD_LOGIC_VECTOR(31 DOWNTO 0);
				Func	:	IN		STD_LOGIC_VECTOR(4  DOWNTO 0);
				HiReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
				LoReg	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
				Rout	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0);
				Stat	:	OUT	STAT_SIGNL_REC);

end ALU_MULS;

ARCHITECTURE BEHAVIORAL of ALU_MULS is 

SIGNAL SAIN: SIGNED(31 DOWNTO 0);
SIGNAL SBIN: SIGNED(31 DOWNTO 0);
SIGNAL SROUT: SIGNED(63 DOWNTO 0);
SIGNAL SLR: SIGNED(31 DOWNTO 0);
SIGNAL SHR: SIGNED(31 DOWNTO 0);



begin 

process(Ain, Bin, FUNC, SAIN, SBIN, SROUT, SLR, SHR)
begin 

IF (Func=ALU_FUNC_MULS) THEN

Stat <= (others =>'Z');

	SAIN <= SIGNED(Ain);
	SBIN <= SIGNED(Bin);
	SROUT <= SAIN * SBIN;
	SLR <= SROUT(31 DOWNTO 0);
	SHR <= SROUT(63 DOWNTO 32);
	Stat.ALU_SIGN <= SROUT(31);
	Stat.ALU_ZERO <= NOT(OR_REDUCE(STD_LOGIC_VECTOR(SLR)));

	LoReg<= std_logic_vector(SLR);
	HiReg<= std_logic_vector(SHR);
	Rout<= std_logic_vector(SLR);

else

	HiReg <=(others => 'Z');
	LoReg <=(others =>'Z');
	Rout  <=(others => 'Z');
	Stat  <=(others =>'Z');

end if;
end process;
end architecture;