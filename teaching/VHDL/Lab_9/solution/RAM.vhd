--------------------------------------------------------------------------------
-- EE 362 - Lab 9 REFERENCE SOLUTION  (TA only - do not publish)
--
-- RAM : 512-byte data memory on a shared bus.
--   DataDrive = en . rw           (rw = '1' is READ)
--   Write     = en . rw' . Strb   at the FALLING edge
--
-- Marking points:
--   * releases the bus to 'Z' whenever not reading - never drives '0'
--   * writes on the FALLING edge, matching the CPU's two-phase timing
--   * big-endian, agreeing with the ROM
--   * range-guarded
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity RAM is
    port (
        Addr : in    std_logic_vector(31 downto 0);
        Strb : in    std_logic;
        rw   : in    std_logic;
        en   : in    std_logic;
        clk  : in    std_logic;
        Data : inout std_logic_vector(31 downto 0)
    );
end entity RAM;

architecture rtl of RAM is

    type ram_array is array (0 to 511) of std_logic_vector(7 downto 0);

    signal MEM  : ram_array := (others => x"00");
    signal base : natural range 0 to 511;
    signal word : std_logic_vector(31 downto 0);

begin

    base <= to_integer(unsigned(Addr(8 downto 0)));

    word <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3)
            when base <= 508
            else (others => '0');

    -- Drive the shared bus only when reading. Otherwise release it.
    Data <= word when (en = '1' and rw = '1') else (others => 'Z');

    -- Write on the FALLING edge - the CPU's two-phase timing.
    process (clk)
    begin
        if falling_edge(clk) then
            if en = '1' and rw = '0' and Strb = '1' and base <= 508 then
                MEM(base)     <= Data(31 downto 24);
                MEM(base + 1) <= Data(23 downto 16);
                MEM(base + 2) <= Data(15 downto  8);
                MEM(base + 3) <= Data( 7 downto  0);
            end if;
        end if;
    end process;

end architecture rtl;
