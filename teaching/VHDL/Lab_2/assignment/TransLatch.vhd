--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 2 - STEP 1: REPLACE THIS FILE
--
-- This is the empty Lab 1 skeleton, included only so that the Lab 2 project
-- compiles the moment you open it.
--
--   >>> Overwrite it with YOUR OWN completed TransLatch.vhd from Lab 1. <<<
--
-- This is the first time your work accumulates. From now on every lab uses
-- components you built in earlier labs, and by Lab 12 you will instantiate
-- eleven of them at once. Keep your files, every week.
--
-- If your Lab 1 latch never worked, ask for the reference version rather than
-- being stuck. Using it costs you nothing on this lab.
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

    process (En)
    begin
        -- empty: replace this whole file with your Lab 1 solution
    end process;

end architecture behavioral;
