library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.ALU_Pkg.ALL;

entity ALU is
    Port (
        Ain  : in  STD_LOGIC_VECTOR(31 downto 0);
        Bin  : in  STD_LOGIC_VECTOR(31 downto 0);
        Func : in  STD_LOGIC_VECTOR(4 downto 0);
        Shft : in  STD_LOGIC_VECTOR(4 downto 0);
        Rout : out STD_LOGIC_VECTOR(31 downto 0);
        Stat : out STAT_SIGNL_REC
    );
end ALU;

architecture Behavioral of ALU is

    signal hi_reg, lo_reg : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');

begin

process(Ain, Bin, Func, Shft, hi_reg, lo_reg)
    variable res_s   : signed(31 downto 0);
    variable res_u   : unsigned(31 downto 0);
    variable mul_s   : signed(63 downto 0);
    variable mul_u   : unsigned(63 downto 0);
    variable q_s, r_s: signed(31 downto 0);
    variable q_u, r_u: unsigned(31 downto 0);
    variable tmp     : STD_LOGIC_VECTOR(31 downto 0);
begin

    tmp := (others => '0');

    case Func is

    ----------------------------------------------------------------
    -- ADD
    ----------------------------------------------------------------
    when ALU_FUNC_ADD =>
        res_s := signed(Ain) + signed(Bin);
        tmp := std_logic_vector(res_s);

    ----------------------------------------------------------------
    -- SUB
    ----------------------------------------------------------------
    when ALU_FUNC_SUB =>
        res_s := signed(Ain) - signed(Bin);
        tmp := std_logic_vector(res_s);

    ----------------------------------------------------------------
    -- MUL SIGNED
    ----------------------------------------------------------------
    when ALU_FUNC_MULS =>
        mul_s := signed(Ain) * signed(Bin);
        lo_reg <= std_logic_vector(mul_s(31 downto 0));
        hi_reg <= std_logic_vector(mul_s(63 downto 32));
        tmp := std_logic_vector(mul_s(31 downto 0));

    ----------------------------------------------------------------
    -- MUL UNSIGNED
    ----------------------------------------------------------------
    when ALU_FUNC_MULU =>
        mul_u := unsigned(Ain) * unsigned(Bin);
        lo_reg <= std_logic_vector(mul_u(31 downto 0));
        hi_reg <= std_logic_vector(mul_u(63 downto 32));
        tmp := std_logic_vector(mul_u(31 downto 0));

    ----------------------------------------------------------------
    -- DIV SIGNED
    ----------------------------------------------------------------
    when ALU_FUNC_DIVS =>
        if Bin /= x"00000000" then
            q_s := signed(Ain) / signed(Bin);
            r_s := signed(Ain) rem signed(Bin);
        else
            q_s := (others => '0');
            r_s := (others => '0');
        end if;

        lo_reg <= std_logic_vector(q_s);
        hi_reg <= std_logic_vector(r_s);
        tmp := std_logic_vector(q_s);

    ----------------------------------------------------------------
    -- DIV UNSIGNED
    ----------------------------------------------------------------
    when ALU_FUNC_DIVU =>
        if Bin /= x"00000000" then
            q_u := unsigned(Ain) / unsigned(Bin);
            r_u := unsigned(Ain) mod unsigned(Bin);
        else
            q_u := (others => '0');
            r_u := (others => '0');
        end if;

        lo_reg <= std_logic_vector(q_u);
        hi_reg <= std_logic_vector(r_u);
        tmp := std_logic_vector(q_u);

    ----------------------------------------------------------------
    -- NEGATION
    ----------------------------------------------------------------
    when ALU_FUNC_NEG =>
        res_s := -signed(Bin);
        tmp := std_logic_vector(res_s);

    ----------------------------------------------------------------
    -- SHIFT LEFT ARITHMETIC
    ----------------------------------------------------------------
    when ALU_FUNC_SLA =>
        tmp := std_logic_vector(shift_left(signed(Ain), to_integer(unsigned(Shft))));

    ----------------------------------------------------------------
    -- SHIFT RIGHT ARITHMETIC
    ----------------------------------------------------------------
    when ALU_FUNC_SRA =>
        tmp := std_logic_vector(shift_right(signed(Ain), to_integer(unsigned(Shft))));

    ----------------------------------------------------------------
    -- SIGNED SET LESS
    ----------------------------------------------------------------
    when ALU_FUNC_SOLS =>
        if signed(Ain) < signed(Bin) then
            tmp := (0 => '1', others => '0');
        end if;

    ----------------------------------------------------------------
    -- UNSIGNED SET LESS
    ----------------------------------------------------------------
    when ALU_FUNC_SOLU =>
        if unsigned(Ain) < unsigned(Bin) then
            tmp := (0 => '1', others => '0');
        end if;

    ----------------------------------------------------------------
    -- LOGIC
    ----------------------------------------------------------------
    when ALU_FUNC_AND  => tmp := Ain and Bin;
    when ALU_FUNC_NAND => tmp := not (Ain and Bin);
    when ALU_FUNC_OR   => tmp := Ain or Bin;
    when ALU_FUNC_NOR  => tmp := not (Ain or Bin);
    when ALU_FUNC_XOR  => tmp := Ain xor Bin;
    when ALU_FUNC_XNOR => tmp := Ain xnor Bin;
    when ALU_FUNC_NOT  => tmp := not Bin;

    ----------------------------------------------------------------
    -- SHIFTS LOGICAL
    ----------------------------------------------------------------
    when ALU_FUNC_SLL =>
        tmp := std_logic_vector(shift_left(unsigned(Ain), to_integer(unsigned(Shft))));

    when ALU_FUNC_SRL =>
        tmp := std_logic_vector(shift_right(unsigned(Ain), to_integer(unsigned(Shft))));

    ----------------------------------------------------------------
    -- HI / LO ACCESS
    ----------------------------------------------------------------
    when ALU_FUNC_RDLO => tmp := lo_reg;
    when ALU_FUNC_RDHI => tmp := hi_reg;

    when ALU_FUNC_WRLO =>
        lo_reg <= Bin;

    when ALU_FUNC_WRHI =>
        hi_reg <= Bin;

    when others =>
        tmp := (others => '0');

    end case;

    ----------------------------------------------------------------
    -- OUTPUT
    ----------------------------------------------------------------
    Rout <= tmp;

    ----------------------------------------------------------------
    -- STATUS FLAGS
    ----------------------------------------------------------------
    if tmp = x"00000000" then
        Stat.ALU_zero <= ALU_STAT_ZERO;
    else
        Stat.ALU_zero <= ALU_STAT_N_ZERO;
    end if;

    Stat.ALU_sign <= tmp(31);

end process;

end Behavioral;