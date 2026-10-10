--------------------------------------------------------------------------------
-- PLACEHOLDER: replace with YOUR OWN RegN.vhd (Overleaf: folder icon > Upload)
-- EE 362 - Computer Organization Laboratory
-- Lab 2 - Assignment, Part 2 of 2
--
-- RegN : N-bit register with load enable and asynchronous reset
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION (Table T)
--
--   #  Rst  Ld  Clk    ||  Q+     note
--   0   1   -   -      ||  0      asynchronous reset, dominates
--   1   0   -   not ^  ||  Q      hold between edges
--   2   0   0   ^      ||  Q      edge arrives, but not loading
--   3   0   1   ^      ||  D      load
--
-- EQUATION, per bit i, evaluated at the rising edge:
--
--   (1)  Q_i+ = Rst' . ( Ld.D_i + Ld'.Q_i )
--   (2)  This is Lab 1's latch equation with En -> Ld and Clr -> Rst.
--        Same circuit, new names, sampled at an edge instead of continuously.
--   (3)  <- that is what you are writing below
--
-- THIS IS THE MOST REUSED COMPONENT IN THE COURSE.
--   Lab 6  - 32 of these become the register file
--   Lab 7  - one of these becomes the program counter
--   Lab 12 - both of the above end up inside your CPU
-- Write it carefully and keep it.
--
-- WHY A GENERIC: the CPU needs registers of width 5 (register-select fields)
-- and width 32 (data). Writing Reg5 and Reg32 separately means fixing every
-- bug twice. One parameterised entity, instantiated twice, cannot drift apart.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity RegN is
    generic (
        N : positive := 32                  -- default width
    );
    port (
        D   : in  std_logic_vector(N - 1 downto 0);
        Clk : in  std_logic;
        Ld  : in  std_logic;                -- load enable
        Rst : in  std_logic;                -- asynchronous reset, active high
        Q   : out std_logic_vector(N - 1 downto 0)
    );
end entity RegN;

architecture behavioral of RegN is
begin

    -- TODO 1: complete the sensitivity list.
    --         Careful - this one is NOT the same rule as Lab 1.
    --         A clocked process needs the clock, and any ASYNCHRONOUS control.
    --         It does not need signals that are only read at the edge.
    --         Which of Clk, Rst, Ld, D belong here? Justify it in your report.
    --         As supplied this list is INCOMPLETE: the file compiles, and your
    --         asynchronous reset will only act when the clock happens to move.
    process (Clk)

    begin

        -- TODO 2: implement the table above.
        --         - Rst first, and OUTSIDE the rising_edge test (that is what
        --           makes it asynchronous)
        --         - then rising_edge(Clk)
        --         - then Ld, nested inside the edge test
        --
        --         Structure:
        --             if Rst = '1' then
        --                 ...
        --             elsif rising_edge(Clk) then
        --                 if Ld = '1' then
        --                     ...
        --                 end if;
        --             end if;

    end process;

end architecture behavioral;
