--Alvaro Esparza
--February 16, 2021

Library IEEE;
use IEEE.STD_LOGIC_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Use IEEE.NUMERIC_STD.all;
Use IEEE.STD_LOGIC_MISC.all;


ENTITY ALU_XOR IS

	PORT( Ain : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
		   Bin : IN STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Func : IN STD_LOGIC_VECTOR(4 DOWNTO 0);
		  Rout : OUT STD_LOGIC_VECTOR(31 DOWNTO 0);
		  Stat : OUT STAT_SIGNL_REC);
			
END ENTITY;

Architecture Behavioral of ALU_XOR is

	SIGNAL ANSWER : STD_LOGIC_VECTOR(31 DOWNTO 0);

	Begin
		Process(Func,Answer,Ain,Bin) IS
		
		Begin
		
			IF (Func=ALU_FUNC_XOR) Then
			
				
				Answer <= Ain XOR Bin;
				Rout   <= Answer;
				
				STAT.ALU_ZERO <= NOT (OR_REDUCE(Answer));
				STAT.ALU_SIGN <= Answer(31);
				
			ELSE
				
				ROUT <= (OTHERS => 'Z');
				STAT <= (OTHERS => 'Z');
			
			End If;
		
		End Process;
	

End Architecture;