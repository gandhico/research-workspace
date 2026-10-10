--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - Assignment, Part 1 of 2
--
-- TransLatch : 1-bit transparent latch with asynchronous clear
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION (Table T)
--
--   #  Clr  En  D  ||  Q+     note
--   0   1   -   -  ||  0      asynchronous clear - dominates everything
--   1   0   0   -  ||  Q      hold
--   2   0   1   0  ||  0      transparent
--   3   0   1   1  ||  1      transparent
--
-- EQUATIONS  (copy these into your report, Section 2)
--
--   (1) canonical    Q+ = Clr'.En.D + Clr'.En'.Q
--   (2) factored     Q+ = Clr' . ( En.D + En'.Q )        [distributive law]
--   (3) VHDL         <- that is what you are writing below
--
-- NOTE ON "ASYNCHRONOUS": Clr takes effect the instant it is asserted. It does
-- not wait for En, and it does not wait for a clock (there is no clock here).
-- That is why Clr is tested FIRST in the if-statement: first test wins.
--
-- REMEMBER: this latch is the storage primitive for the whole semester.
-- Lab 2 builds a flip-flop from two of these. Lab 6 builds 1024 of them.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity TransLatch is
    port (
        D   : in  std_logic;                -- data input
        En  : in  std_logic;                -- enable: '1' transparent, '0' hold
        Clr : in  std_logic;                -- asynchronous clear, active high
        Q   : out std_logic                 -- data output
    );
end entity TransLatch;

architecture behavioral of TransLatch is
begin

    -- TODO 1: this sensitivity list is INCOMPLETE ON PURPOSE.
    --         It must name EVERY signal the process reads. As written, the
    --         file compiles - and simulates wrong, exactly like Example 3.
    --         Add what is missing.
    process (En)

    begin

        -- TODO 2: implement the table above.
        --   - test Clr first (row 0)
        --   - then En       (rows 2 and 3)
        --   - write NO else: the missing else is row 1, the hold row

    end process;

end architecture behavioral;
