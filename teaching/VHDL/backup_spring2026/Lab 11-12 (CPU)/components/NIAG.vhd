library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.ALU_Pkg.all;

entity NIAG is
    Port (
        Target  : in  STD_LOGIC_VECTOR(25 downto 0);
        Immed   : in  STD_LOGIC_VECTOR(31 downto 0);
        Reg     : in  STD_LOGIC_VECTOR(31 downto 0);
        Xshft   : in  STD_LOGIC;
        PCin    : in  STD_LOGIC_VECTOR(31 downto 0);
        Cond    : in  STD_LOGIC_VECTOR(2 downto 0);
        Sel     : in  STD_LOGIC_VECTOR(1 downto 0);
        Stat    : in  STAT_SIGNL_REC;
        MemAdrs : out STD_LOGIC_VECTOR(31 downto 0);
        RtnAdrs : out STD_LOGIC_VECTOR(31 downto 0)
    );
end NIAG;

architecture structural of NIAG is
    signal nsa_s : STD_LOGIC_VECTOR(31 downto 0);
    signal abs_s : STD_LOGIC_VECTOR(31 downto 0);
    signal rel_s : STD_LOGIC_VECTOR(31 downto 0);
    signal reg_s : STD_LOGIC_VECTOR(31 downto 0);
begin
    U_NSA : entity work.NIAG_NSA port map(PC => PCin, NSA => nsa_s);
    U_ABS : entity work.NIAG_Abslt port map(Index => Target, NSA => nsa_s, AbsltAdrs => abs_s);
    U_REL : entity work.NIAG_Rel port map(Immed => Immed, Xshft => Xshft, NSA => nsa_s, RelAdrs => rel_s);
    U_REG : entity work.NIAG_Reg port map(Reg => Reg, RegAdrs => reg_s);
    U_RTN : entity work.NIAG_Rtn port map(PC => PCin, RtnAdrs => RtnAdrs);
    U_MUX : entity work.NIAG_MUX port map(NxtAdrs => nsa_s, AbsltAdrs => abs_s, RelAdrs => rel_s, RegAdrs => reg_s, Cond => Cond, Sel => Sel, Stat => Stat, InstrAdrs => MemAdrs);
end structural;
