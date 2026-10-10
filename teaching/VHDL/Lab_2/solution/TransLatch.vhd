--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - REFERENCE SOLUTION  (TA only - do not publish to Canvas)
--
-- TransLatch : 1-bit transparent latch with asynchronous clear
--
--   #  Clr  En  D  ||  Q+
--   0   1   -   -  ||  0
--   1   0   0   -  ||  Q
--   2   0   1   0  ||  0
--   3   0   1   1  ||  1
--
--   Q+ = Clr' . ( En.D + En'.Q )
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

    process (Clr, En, D)
    begin
        if Clr = '1' then
            Q <= '0';                       -- row 0: asynchronous clear wins
        elsif En = '1' then
            Q <= D;                         -- rows 2, 3: transparent
        end if;
        -- row 1 (hold) is the deliberately missing else
    end process;

end architecture behavioral;
