--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - Assignment, Part 2 of 2
--
-- TransLatch8 : 8-bit transparent latch with asynchronous clear
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION
--   Exactly the same table as TransLatch, applied to all 8 bits at once.
--   The equation is the same equation, subscripted:
--
--       Q_i+ = Clr' . ( En.D_i + En'.Q_i )      for i = 0 .. 7
--
--   The control signals Clr and En are still SINGLE BITS. They are shared by
--   all eight storage elements. This is the first time you will see the
--   pattern that dominates the rest of the course:
--
--       control signals are narrow, data paths are wide.
--
-- THINK BEFORE YOU TYPE: how much of your 1-bit code actually has to change?
-- (Answer: the port types, and how you write the cleared value. That is all.)
--
-- CLEARING A VECTOR: you cannot write  Q <= '0';  for a vector - '0' is one bit.
-- Use the aggregate:  Q <= (others => '0');  which means "every element gets '0'"
-- and works at any width without being rewritten. You will use it all semester.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity TransLatch8 is
    port (
        D   : in  std_logic_vector(7 downto 0);     -- data input
        En  : in  std_logic;                        -- enable  (1 bit, shared)
        Clr : in  std_logic;                        -- clear   (1 bit, shared)
        Q   : out std_logic_vector(7 downto 0)      -- data output
    );
end entity TransLatch8;

architecture behavioral of TransLatch8 is
begin

    -- TODO 1: this sensitivity list is INCOMPLETE ON PURPOSE. Fix it.
    process (En)

    begin

        -- TODO 2: same three cases as TransLatch, on vectors.
        --         Use (others => '0') for the cleared value.

    end process;

end architecture behavioral;
