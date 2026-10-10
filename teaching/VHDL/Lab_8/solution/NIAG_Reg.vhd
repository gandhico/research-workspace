--------------------------------------------------------------------------------
-- EE 362 - Lab 7 REFERENCE SOLUTION  (TA only - do not publish)
-- NIAG_Reg : the program counter. Lab 2's RegN with a non-zero reset value.
--   PC+ = Rst' . ( Strb.NextPC + Strb'.PC )
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity NIAG_Reg is
    generic (
        RESET_VEC : natural := 0
    );
    port (
        NextPC : in  std_logic_vector(31 downto 0);
        Strb   : in  std_logic;
        Rst    : in  std_logic;
        clk    : in  std_logic;
        PC     : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Reg;

architecture rtl of NIAG_Reg is
    signal pc_reg : std_logic_vector(31 downto 0)
                  := std_logic_vector(to_unsigned(RESET_VEC, 32));
begin
    process (clk, Rst)
    begin
        if Rst = '1' then
            pc_reg <= std_logic_vector(to_unsigned(RESET_VEC, 32));
        elsif rising_edge(clk) then
            if Strb = '1' then
                pc_reg <= NextPC;
            end if;
        end if;
    end process;

    PC <= pc_reg;
end architecture rtl;
