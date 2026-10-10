Library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

LIBRARY EE_212_NIAG;
use EE_212_NIAG.NIAG_Pkg.all;

LIBRARY EE_212_DECODER;
use EE_212_Decoder.DecodeLogic_Pkg.all;
use IEEE.NUMERIC_STD.all;

LIBRARY EE_212_ALU;
use EE_212_ALU.ALU_pkg.all;



Entity tb_NIAG is

END tb_NIAG;

Architecture tb of tb_NIAG is


		signal TARGET :  STD_LOGIC_VECTOR(25 Downto 0);
		signal Immed  :  STD_LOGIC_VECTOR(31 Downto 0);
		signal Reg    :  STD_LOGIC_VECTOR(31 Downto 0);
		signal Xshft  :  STD_LOGIC;
		signal PCin   :  STD_LOGIC_VECTOR(31 Downto 0);
		signal Cond   :  STD_LOGIC_VECTOR(2  Downto 0);
		signal Sel    :  STD_LOGIC_VECTOR(1  Downto 0);
		signal Stat   : STAT_SIGNL_REC;
		signal MemAdrs:  STD_LOGIC_VECTOR(31 Downto 0);
		signal RtnAdrs:  STD_LOGIC_VECTOR(31 Downto 0);

BEGIN

		dut : NIAG
		port map (Target  => Target,
					 Immed   => Immed,
					 Reg     => Reg,
					 Xshft   => Xshft,
					 PCin    => PCin,
					 Cond    => Cond,
					 Sel     => Sel,
					 Stat    => Stat,
					 MemAdrs => MemAdrs,
					 RtnAdrs => RtnAdrs);
					 
		
	stimuli: process
    begin
	 
		 wait for 10 ns;
		 
		 pcin <= X"00000000";  -- make sure PC is updated here
		 
		 wait for 10 ns;
		 
		 target <= X"000001" & "11"; --test for our absolute address NIAG. 
		 sel <= niag_sel_abs;
		 
		 wait for 10 ns;
		 
		 xshft <= '1';
		 immed <= X"00000001";
		 sel <= niag_sel_rel;  --Test for our relative addressing. Uses condition code "Branch equal"
		 cond <= niag_cond_eq;
		 stat.alu_zero <= alu_stat_zero; --Manually set the alu_zero flag to one to simulate a true condition for branch equal.
		 
		 wait for 10 ns;
		 
		 cond <= niag_cond_neq; --Change the condition code so the branch conditioning fails and defaults.
		 
		 wait for 10 ns;
		 
		 reg <= X"0000000C"; --Test for our register address NIAG
		 sel <= niag_sel_reg;    
    
    wait;
    
    end process;
	

END ARCHITECTURE;