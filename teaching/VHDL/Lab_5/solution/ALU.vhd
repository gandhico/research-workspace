--------------------------------------------------------------------------------
-- EE 362 - Lab 5 REFERENCE SOLUTION  (TA only - do not publish)
--
-- ALU: sixteen operations selected by a 5-bit code. The case statement IS the
-- multiplexer; the RTL Viewer draws one.
--
-- Points to check when marking:
--   * SRA uses signed(), SRL uses unsigned(). Same operator, different fill.
--   * SOLS/SOLU use the numeric_std comparison, which is overflow-correct.
--     Equivalent hardware equation: SOLS = R(31) xor V, R = Ain - Bin.
--   * Flags are computed on 'result', AFTER the case - not inside a branch.
--   * 'when others' assigns, so no latch.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.ALU_Pkg.all;

entity ALU is
    port (
        Ain  : in  std_logic_vector(31 downto 0);
        Bin  : in  std_logic_vector(31 downto 0);
        Func : in  std_logic_vector(4 downto 0);
        Shft : in  std_logic_vector(4 downto 0);
        Rout : out std_logic_vector(31 downto 0);
        Zero : out std_logic;
        Neg  : out std_logic
    );
end entity ALU;

architecture rtl of ALU is

    signal result : std_logic_vector(31 downto 0);
    signal amount : natural range 0 to 31;

begin

    amount <= to_integer(unsigned(Shft));

    process (Ain, Bin, Func, amount)
    begin

        case Func is

            -- Arithmetic
            when ALU_FUNC_ADD =>
                result <= std_logic_vector(unsigned(Ain) + unsigned(Bin));

            when ALU_FUNC_SUB =>
                result <= std_logic_vector(unsigned(Ain) - unsigned(Bin));

            when ALU_FUNC_NEG =>
                result <= std_logic_vector(0 - signed(Bin));

            -- Bitwise logic
            when ALU_FUNC_AND  => result <= Ain and Bin;
            when ALU_FUNC_NAND => result <= not (Ain and Bin);
            when ALU_FUNC_OR   => result <= Ain or Bin;
            when ALU_FUNC_NOR  => result <= not (Ain or Bin);
            when ALU_FUNC_XOR  => result <= Ain xor Bin;
            when ALU_FUNC_XNOR => result <= not (Ain xor Bin);
            when ALU_FUNC_NOT  => result <= not Bin;

            -- Shifts. Left shifts have only one sensible answer, so SLL = SLA.
            when ALU_FUNC_SLL | ALU_FUNC_SLA =>
                result <= std_logic_vector(shift_left(unsigned(Ain), amount));

            -- SRL fills with '0'  -> unsigned
            when ALU_FUNC_SRL =>
                result <= std_logic_vector(shift_right(unsigned(Ain), amount));

            -- SRA fills with the sign bit -> signed. The TYPE decides.
            when ALU_FUNC_SRA =>
                result <= std_logic_vector(shift_right(signed(Ain), amount));

            -- Set on less than. numeric_std's comparisons are overflow-correct,
            -- which is the whole difficulty of doing this in raw gates.
            when ALU_FUNC_SOLS =>
                if signed(Ain) < signed(Bin) then
                    result <= x"00000001";
                else
                    result <= x"00000000";
                end if;

            when ALU_FUNC_SOLU =>
                if unsigned(Ain) < unsigned(Bin) then
                    result <= x"00000001";
                else
                    result <= x"00000000";
                end if;

            -- Defined, harmless default. No latch.
            when others =>
                result <= (others => '0');

        end case;

    end process;

    Rout <= result;

    -- Flags describe the SELECTED result, computed after the multiplexer.
    Zero <= '1' when result = (result'range => '0') else '0';
    Neg  <= result(31);

end architecture rtl;
