library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library ee_212_ALU;
use EE_212_alu.ALU_pkg.all;

library EE_212_Decoder;
use EE_212_Decoder.DecodeLogic_pkg.all;

entity NIAG_MUX is

PORT(	NxtAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Next sequential address
		AbsltAdrs	:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Absolute address
		RelAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Relative address
		RegAdrs		:	IN	STD_LOGIC_VECTOR(31 DOWNTO 0);				--    Register address
		Cond		   :	IN	STD_LOGIC_VECTOR(2  DOWNTO 0);				--    Logical condition to be tested
		Sel			:	IN	STD_LOGIC_VECTOR(1  DOWNTO 0);				--    Input selection bus
		Stat		   :	IN	STAT_SIGNL_REC;								--    ALU status signals
		InstrAdrs	:	OUT	STD_LOGIC_VECTOR(31 DOWNTO 0));
end entity;

architecture synth of NIAG_MUX is

signal mux_sel: std_logic_vector(1 downto 0);

begin
	process (cond, sel, stat, mux_sel, absltadrs, reladrs, regadrs, nxtadrs)
	begin
		if sel /= niag_sel_float then
			if sel/= niag_sel_rel then --If it is not a branch instruction
				mux_sel <= sel;
			else    --If it is a branch instruction
			case cond is
			when niag_cond_eq =>  if stat.alu_zero = alu_stat_zero then --Check to see that two values are equal
											mux_sel <= niag_sel_rel;
										 else 
											mux_sel <= niag_sel_NSA;
										 end if;
			
			when niag_cond_neq => if stat.alu_zero = alu_stat_n_zero then  --Check to see that two values are not equal
											 mux_sel <= niag_sel_rel;
										 else 
											 mux_sel <= niag_sel_nsa;
										 end if;
			
			when niag_cond_gtz => if (stat.alu_zero = alu_stat_n_zero) and (stat.alu_sign = alu_stat_pos) then --Check that a value is greater than zero.
											 mux_sel <= niag_sel_rel;
										 else 
											 mux_sel <= niag_sel_nsa;
										 end if;
			
			when niag_cond_ltz => if (stat.alu_zero = alu_stat_n_zero) and (stat.alu_sign = alu_stat_neg) then --Check that a value is less than zero.
											mux_sel <= niag_sel_rel;
										 else 
											mux_sel <= niag_sel_nsa;
										 end if;
			
			when niag_cond_gez => if (stat.alu_zero = alu_stat_zero) or (stat.alu_sign = alu_stat_pos) then --Check that a value is greater than or equal to zero.
											mux_sel <= niag_sel_rel;
										 else 
											mux_sel <= niag_sel_nsa;
										 end if;
			
			when niag_cond_lez => if (stat.alu_zero = alu_stat_zero) or (stat.alu_sign = alu_stat_neg) then --Check that a value is less than or equal to zero.
											mux_sel <= niag_sel_rel;
										 else 
											mux_sel <= niag_sel_nsa;
										 end if;
			when others => Mux_sel <= NIAG_SEL_NSA;
			end case;
		end if;
		end if;
		
		
		
		
	end process; 
	
	with mux_sel select --Select which addressing mode will be used depending on the MUX_sel signal. 
	 Instradrs <= absltadrs when niag_sel_abs,
					  reladrs   when niag_sel_rel,
					  regadrs   when niag_sel_reg,
					  nxtadrs   when others;

end architecture;