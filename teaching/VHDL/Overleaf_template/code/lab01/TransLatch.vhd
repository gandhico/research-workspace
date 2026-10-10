--------------------------------------------------------------------------------
-- PLACEHOLDER
--
-- Replace this file with YOUR OWN TransLatch.vhd from Lab 1.
-- In Overleaf: click the folder icon > Upload, and overwrite this file.
--
-- Do not paste your code into lab01.tex. Upload the real .vhd file here and
-- let \vhdlfile include it, so the listing can never drift out of date with
-- the design you actually simulated.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity TransLatch is
    port (
        D   : in  std_logic;
        En  : in  std_logic;
        Clr : in  std_logic;
        Q   : out std_logic
    );
end entity TransLatch;

architecture behavioral of TransLatch is
begin
    -- your implementation goes here
end architecture behavioral;
