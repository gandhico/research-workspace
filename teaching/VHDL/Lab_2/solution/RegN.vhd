--------------------------------------------------------------------------------
-- EE 362 - Lab 2 REFERENCE SOLUTION  (TA only - do not publish)
--
-- RegN : N-bit register, load enable, asynchronous reset
--
--   Q_i+ = Rst' . ( Ld.D_i + Ld'.Q_i )    at the rising edge
--
-- Sensitivity list is (Clk, Rst): the clock, plus the asynchronous control.
-- D and Ld are absent because they are only ever read at the edge.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity RegN is
    generic (
        N : positive := 32
    );
    port (
        D   : in  std_logic_vector(N - 1 downto 0);
        Clk : in  std_logic;
        Ld  : in  std_logic;
        Rst : in  std_logic;
        Q   : out std_logic_vector(N - 1 downto 0)
    );
end entity RegN;

architecture behavioral of RegN is
begin

    process (Clk, Rst)
    begin
        if Rst = '1' then
            Q <= (others => '0');           -- row 0, asynchronous
        elsif rising_edge(Clk) then
            if Ld = '1' then
                Q <= D;                     -- row 3
            end if;
            -- row 2 (edge, Ld low) is the missing else
        end if;
    end process;

end architecture behavioral;
