Library IEEE;
use IEEE.std_logic_1164.all;

Library EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;

Library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

use IEEE.NUMERIC_STD.All;

ENTITY tb_Decoder is


		 
END ENTITY;

ARCHITECTURE behavioral of tb_Decoder is

	SIGNAL Instruction : IN STD_LOGIC_VECTOR(31 Downto 0);
	SIGNAL CtrlSgnls   : OUT CTRL_SIGNL_REC;

	begin

		dut: Decoder port map(Instruction, Ctrlsgnls);
		
		process
			begin
	
			wait for 10 ns;
		
			Instruction <= CPU_ADD_OPCODE & "00001" & "00010" & "00011"  & "00000" & cpu_add_func;
	
		end process;
	
END Architecture;

--ADDU ANDI BGEZ LW MTLO SLLV
