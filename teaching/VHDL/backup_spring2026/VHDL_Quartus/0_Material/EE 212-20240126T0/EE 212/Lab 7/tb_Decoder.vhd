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

	SIGNAL Instruction : STD_LOGIC_VECTOR(31 Downto 0);
	SIGNAL CtrlSgnls   : CTRL_SIGNL_REC;

	begin

		dut: Decoder port map(Instruction, Ctrlsgnls);
		
		process
			begin
	
			wait for 10 ns;
		
			Instruction <= CPU_ADD_OPCODE & "00001" & "00010" & "00011"  & "00000" & cpu_add_func;
			
			wait for 10 ns;
			
			Instruction <= CPU_ADDU_OPCODE & "00011" & "00001" & "00001" & "00000" & cpu_addu_func;
			
			wait for 10 ns;
			
			Instruction <= CPU_ANDI_OPCODE & "00001" & "00010" & "1111111111111111";

			wait for 10 ns;
			
			Instruction <= CPU_SLLV_OPCODE & "00010" & "11111" & "00100" & "00000" & cpu_sllv_func;
	
			wait for 10 ns;
			
			Instruction <= CPU_MTLO_OPCODE & "11111" & "00000" & "00000" & "00000" & cpu_mtlo_func;
			
			wait for 10 ns;
			
			Instruction <= CPU_LW_OPCODE & "00001" & "00101" & "0000000000000011";
			
			wait for 10 ns;
			
			Instruction <= CPU_BGEZ_OPCODE & "00001" & "00001" & "0000000000000011";
			
			wait;
			
		end process;
	
END Architecture;

--ADDU ANDI BGEZ LW MTLO SLLV
