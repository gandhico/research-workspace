--Alvaro Esparza
--February 16, 2021

Library IEEE;
use IEEE.STD_LOGIC_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Use IEEE.NUMERIC_STD.all;
Use IEEE.STD_LOGIC_MISC.all;


ENTITY ALU_RDLO IS

 PORT(  LoReg : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Func : IN STD_LOGIC_VECTOR(4 DOWNTO 0);
		  Rout : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Stat : OUT STAT_SIGNL_REC);
			
END ENTITY;

Architecture Behavioral of ALU_RDLO is

	Begin
		Process(Func,LoReg) IS
		
		Begin
		
			IF (Func=ALU_FUNC_RDLO) Then
				
				Rout <= LoReg;
				
				STAT.ALU_SIGN <= LoReg(31);
				STAT.ALU_SIGN <= NOT(OR_REDUCE(LoReg));
				
			ELSE
				
				ROUT <= (OTHERS => 'Z');
				STAT <= (OTHERS => 'Z');
			
			End If;
		
		End Process;
	

End Architecture;