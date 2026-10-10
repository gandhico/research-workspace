--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 1 - REFERENCE SOLUTION  (TA only - do not publish to Canvas)
--
-- TransLatch8 : 8-bit transparent latch with asynchronous clear
--
--   Q_i+ = Clr' . ( En.D_i + En'.Q_i )      for i = 0 .. 7
--
-- Identical to the 1-bit version apart from the port types and the aggregate
-- used for the cleared value.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity TransLatch8 is
    port (
        D   : in  std_logic_vector(7 downto 0);
        En  : in  std_logic;
        Clr : in  std_logic;
        Q   : out std_logic_vector(7 downto 0)
    );
end entity TransLatch8;

architecture behavioral of TransLatch8 is
begin

    process (Clr, En, D)
    begin
        if Clr = '1' then
            Q <= (others => '0');           -- row 0
        elsif En = '1' then
            Q <= D;                         -- rows 2, 3
        end if;
        -- row 1 (hold): no else
    end process;

end architecture behavioral;
