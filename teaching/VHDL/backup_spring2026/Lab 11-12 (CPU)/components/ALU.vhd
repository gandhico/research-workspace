library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.ALU_Pkg.all;

entity ALU is
    port(
        Ain  : in  STD_LOGIC_VECTOR(31 downto 0);
        Bin  : in  STD_LOGIC_VECTOR(31 downto 0);
        Func : in  STD_LOGIC_VECTOR(4 downto 0);
        Shft : in  STD_LOGIC_VECTOR(4 downto 0);
        Rout : out STD_LOGIC_VECTOR(31 downto 0);
        Stat : out STAT_SIGNL_REC
    );
end ALU;

architecture Behavioral of ALU is
    signal result_s : STD_LOGIC_VECTOR(31 downto 0);

    function set_flags(v : STD_LOGIC_VECTOR(31 downto 0)) return STAT_SIGNL_REC is
        variable r : STAT_SIGNL_REC;
    begin
        if v = x"00000000" then
            r.ALU_zero := ALU_STAT_ZERO;
        else
            r.ALU_zero := ALU_STAT_N_ZERO;
        end if;

        if v(31) = '1' then
            r.ALU_sign := ALU_STAT_NEG;
        else
            r.ALU_sign := ALU_STAT_POS;
        end if;
        return r;
    end function;
begin
    process(Ain, Bin, Func, Shft)
        variable sh : integer;
        variable tmp : STD_LOGIC_VECTOR(31 downto 0);
    begin
        sh := to_integer(unsigned(Shft));
        tmp := (others => '0');

        case Func is
            when ALU_FUNC_ADD  => tmp := STD_LOGIC_VECTOR(signed(Ain) + signed(Bin));
            when ALU_FUNC_SUB  => tmp := STD_LOGIC_VECTOR(signed(Bin) - signed(Ain));
            when ALU_FUNC_AND  => tmp := Ain and Bin;
            when ALU_FUNC_OR   => tmp := Ain or Bin;
            when ALU_FUNC_XOR  => tmp := Ain xor Bin;
            when ALU_FUNC_NOR  => tmp := not (Ain or Bin);
            when ALU_FUNC_NAND => tmp := not (Ain and Bin);
            when ALU_FUNC_NOT  => tmp := not Bin;
            when ALU_FUNC_SLL  => tmp := STD_LOGIC_VECTOR(shift_left(unsigned(Ain), sh));
            when ALU_FUNC_SRL  => tmp := STD_LOGIC_VECTOR(shift_right(unsigned(Ain), sh));
            when ALU_FUNC_SRA  => tmp := STD_LOGIC_VECTOR(shift_right(signed(Ain), sh));
            when ALU_FUNC_SLA  => tmp := STD_LOGIC_VECTOR(shift_left(signed(Ain), sh));
            when ALU_FUNC_SOLS =>
                if signed(Bin) < signed(Ain) then tmp := x"00000001"; else tmp := (others => '0'); end if;
            when ALU_FUNC_SOLU =>
                if unsigned(Bin) < unsigned(Ain) then tmp := x"00000001"; else tmp := (others => '0'); end if;
            when others        => tmp := (others => '0');
        end case;

        result_s <= tmp;
        Rout <= tmp;
        Stat <= set_flags(tmp);
    end process;
end Behavioral;
