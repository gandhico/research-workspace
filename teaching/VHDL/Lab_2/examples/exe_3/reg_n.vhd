--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2, Example 3 - A register whose WIDTH is a parameter
--
-- A GENERIC is a compile-time parameter. It lets one entity serve every width
-- you will ever need, instead of writing reg4, reg5, reg8, reg32 by hand.
--
-- You need widths 5 and 32 for the CPU (register-select fields are 5 bits,
-- data paths are 32). By Lab 8 you will have instantiated this at four
-- different widths without editing it once.
--
-- SPECIFICATION (Table T)
--   #  Rst  Ld  Clk    ||  Q+     note
--   0   1   -   -      ||  0      asynchronous reset
--   1   0   -   not ^  ||  Q      hold between edges
--   2   0   0   ^      ||  Q      edge, but not loading
--   3   0   1   ^      ||  D      load
--
-- EQUATION, per bit i, evaluated at the rising edge:
--   Q_i+ = Rst' . ( Ld.D_i + Ld'.Q_i )
--
-- Compare that with Lab 1's latch:  Q+ = Clr'.( En.D + En'.Q )
-- It is the SAME equation. En became Ld, Clr became Rst, and the enable is now
-- sampled at an edge instead of continuously. New name, same circuit.
--------------------------------------------------------------------------------

-- N is the generic parameter that specifies the width of the register.
-- ++ positive is a VHDL keyword that specifies that the generic parameter must be a positive integer.
-- and finally, := 8 specifies the default width of the register.


library ieee;
use ieee.std_logic_1164.all;

entity reg_n is
    generic (
        N : positive := 8                   -- default width, overridden per use
    );
    port (
        D   : in  std_logic_vector(N - 1 downto 0);
        Clk : in  std_logic;
        Ld  : in  std_logic;                -- load enable
        Rst : in  std_logic;                -- asynchronous reset, active high
        Q   : out std_logic_vector(N - 1 downto 0)
    );
end entity reg_n;

architecture behavioral of reg_n is
begin

    -- Sensitivity list: Clk and Rst only.
    --   Rst is there because it is ASYNCHRONOUS - it must act immediately,
    --   without waiting for an edge.
    --   D and Ld are NOT there because they are only ever read at the edge,
    --   and the edge is caused by Clk.
    process (Clk, Rst)
    begin
        if Rst = '1' then
            Q <= (others => '0');           -- row 0
        elsif rising_edge(Clk) then
            if Ld = '1' then
                Q <= D;                     -- row 3
            end if;
            -- row 2 (edge, not loading) is the missing else, exactly as in Lab 1
        end if;
    end process;

end architecture behavioral;
