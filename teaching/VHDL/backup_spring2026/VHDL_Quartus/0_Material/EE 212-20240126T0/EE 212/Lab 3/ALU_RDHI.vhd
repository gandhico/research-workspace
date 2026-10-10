--Alvaro Esparza
--February 16, 2021

Library IEEE;
use IEEE.STD_LOGIC_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Use IEEE.NUMERIC_STD.all;
Use IEEE.STD_LOGIC_MISC.all;


ENTITY ALU_RDHI IS

 PORT(  HiReg : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Func : IN STD_LOGIC_VECTOR(4 DOWNTO 0);
		  Rout : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Stat : OUT STAT_SIGNL_REC);
			
END ENTITY;

Architecture Behavioral of ALU_RDHI is

	Begin
		Process(Func,HiReg) IS
		
		Begin
		
			IF (Func=ALU_FUNC_RDHI) Then
				
				Rout <= HiReg;
				
				STAT.ALU_SIGN <= HiReg(31);
				STAT.ALU_SIGN <= NOT(OR_REDUCE(HiReg));
				
			ELSE
				
				ROUT <= (OTHERS => 'Z');
				STAT <= (OTHERS => 'Z');
			
			End If;
		
		End Process;
	

End Architecture;