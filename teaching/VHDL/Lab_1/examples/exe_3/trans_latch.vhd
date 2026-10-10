--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1, Example 2 - Transparent Latch (1 bit)
--
-- SPECIFICATION (Table T)
--   #  En  D  ||  Q+     note
--   0   0  -  ||  Q      hold        <-- the memory row
--   1   1  0  ||  0      transparent
--   2   1  1  ||  1      transparent
--
-- EQUATIONS
--   (1) canonical   Q+ = En.D + En'.Q
--   (2) VHDL        the 'if' below, with NO else - the missing else IS the hold row
--
-- The Q on the right-hand side of equation (1) is the whole difference between
-- combinational logic and memory. Lab 0 had no Q on the right. This one does.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity trans_latch is
    port (
        D  : in  std_logic;                 -- data in
        En : in  std_logic;                 -- enable: '1' = transparent, '0' = hold
        Q  : out std_logic                  -- data out
    );
end entity trans_latch;

architecture behavioral of trans_latch is
begin

    -- The sensitivity list must contain EVERY signal the process reads.
    -- Here that is En and D. Example 3 shows what happens when it does not.
    process (En, D)
    begin
        if En = '1' then
            Q <= D;                         -- transparent: Q follows D
        end if;
        -- No 'else'. When En = '0' nothing is assigned, so Q keeps its old
        -- value. That is a latch, and here it is exactly what we want.
    end process;

end architecture behavioral;
