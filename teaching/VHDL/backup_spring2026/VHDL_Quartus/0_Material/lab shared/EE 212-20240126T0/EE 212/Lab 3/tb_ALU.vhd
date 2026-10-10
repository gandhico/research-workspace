
Library IEEE;
use IEEE.STD_LOGIC_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

ENTITy TB_ALU IS

END TB_ALU;

ARCHITECTURE TB OF TB_ALU IS

		  SIGNAL AIN:  STD_LOGIC_VECTOR(31 DOWNTO 0);
		  SIGNAL BIN:  STD_LOGIC_VECTOR(31 DOWNTO 0);
		  SIGNAL FUNC: STD_LOGIC_VECTOR(4 DOWNTO 0);
		  SIGNAL SHFT: STD_LOGIC_VECTOR(4 DOWNTO 0);
		  SIGNAL ROUT: STD_LOGIC_VECTOR(31 DOWNTO 0);
		  SIGNAL STAT: STAT_SIGNL_REC;
		  SIGNAL HiReg: STD_LOGIC_VECTOR(31 DOWNTO 0);
		  SIGNAL LoReg: STD_LOGIC_VECTOR(31 DOWNTO 0);
	
BEGIN

	DUT : ALU
	Port Map (AIN => AIN,
				 BIN => BIN,
				FUNC => FUNC,
				SHFT => SHFT,
				ROUT => ROUT,
				STAT => STAT);
				
	stimuli : process
	begin
	
		wait for 10 ns;
	
		AIN <= X"00000001";
		BIN <= X"00000001";
	   FUNC <= ALU_FUNC_ADD;
		
		
		wait for 10 ns;
		
		
		func <= ALU_FUNC_RDHI;
		HiReg <= X"00000002"; 
		
		wait for 10 ns;
		
		func <= ALU_FUNC_XOR;
		bin <= X"FFFFFFFF"; 
		ain <= X"F0F0F0F0";
		
		wait for 10 ns;
		
		func <= ALU_FUNC_MULS;
		ain  <= x"FFFFFFFF";
		bin  <= x"00000001";
		wait for 10 ns; 
		
		wait;
		
		
	end process;
	
end tb;
	
	