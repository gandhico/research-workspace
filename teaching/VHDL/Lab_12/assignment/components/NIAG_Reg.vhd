--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 7 reference component
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
