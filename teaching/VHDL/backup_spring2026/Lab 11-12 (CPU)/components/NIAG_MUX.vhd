library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.ALU_Pkg.all;
use work.DecodeLogic_Pkg.all;

entity NIAG_MUX is
    port(
        NxtAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
        AbsltAdrs : in  STD_LOGIC_VECTOR(31 downto 0);
        RelAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
        RegAdrs   : in  STD_LOGIC_VECTOR(31 downto 0);
        Cond      : in  STD_LOGIC_VECTOR(2 downto 0);
        Sel       : in  STD_LOGIC_VECTOR(1 downto 0);
        Stat      : in  STAT_SIGNL_REC;
        InstrAdrs : out STD_LOGIC_VECTOR(31 downto 0)
    );
end NIAG_MUX;

architecture rtl of NIAG_MUX is
    function branch_taken(Cond_in : STD_LOGIC_VECTOR(2 downto 0); Stat_in : STAT_SIGNL_REC) return boolean is
    begin
        case Cond_in is
            when NIAG_COND_NONE => return true;
            when NIAG_COND_EQ   => return (Stat_in.ALU_zero = ALU_STAT_ZERO);
            when NIAG_COND_NEQ  => return (Stat_in.ALU_zero = ALU_STAT_N_ZERO);
            when NIAG_COND_GTZ  => return (Stat_in.ALU_sign = ALU_STAT_POS) and (Stat_in.ALU_zero = ALU_STAT_N_ZERO);
            when NIAG_COND_GEZ  => return (Stat_in.ALU_sign = ALU_STAT_POS);
            when NIAG_COND_LTZ  => return (Stat_in.ALU_sign = ALU_STAT_NEG);
            when NIAG_COND_LEZ  => return (Stat_in.ALU_sign = ALU_STAT_NEG) or (Stat_in.ALU_zero = ALU_STAT_ZERO);
            when others         => return false;
        end case;
    end function;
begin
    process(NxtAdrs, AbsltAdrs, RelAdrs, RegAdrs, Cond, Sel, Stat)
    begin
        case Sel is
            when NIAG_SEL_NSA => InstrAdrs <= NxtAdrs;
            when NIAG_SEL_REL =>
                if branch_taken(Cond, Stat) then InstrAdrs <= RelAdrs; else InstrAdrs <= NxtAdrs; end if;
            when NIAG_SEL_REG => InstrAdrs <= RegAdrs;
            when NIAG_SEL_ABS => InstrAdrs <= AbsltAdrs;
            when others       => InstrAdrs <= (others => '0');
        end case;
    end process;
end rtl;
