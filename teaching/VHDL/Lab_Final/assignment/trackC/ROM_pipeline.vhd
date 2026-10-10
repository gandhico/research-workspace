--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track C - straight-line test program
--
-- Four instructions, NO branches, and the ADD's operands are written three
-- instructions before they are read - far enough apart that no forwarding is
-- needed.
--
--   0x00   3C 01 00 05    LUI  r1, 5        r1 <- 5
--   0x04   3C 02 00 03    LUI  r2, 3        r2 <- 3
--   0x08   3C 03 00 07    LUI  r3, 7        r3 <- 7
--   0x0C   00 22 20 20    ADD  r4, r1, r2   r4 <- 8
--
-- Expected: r4 = 8.
--
-- If this does not execute correctly through your pipeline, the PIPELINE
-- REGISTER is wrong - the hazards are not your problem yet. Fix this first.
--
-- THEN, as an experiment: move the ADD up to 0x08, immediately after the LUI
-- of r2. Predict the result BEFORE running it. That is a data hazard, made by
-- hand, and it belongs in your report.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity ROM is
    port (
        Addr : in  std_logic_vector(31 downto 0);
        Data : out std_logic_vector(31 downto 0)
    );
end entity ROM;

architecture rtl of ROM is

    type rom_array is array (0 to 511) of std_logic_vector(7 downto 0);

    constant MEM : rom_array := (
        16#00# => x"3C", 16#01# => x"01", 16#02# => x"00", 16#03# => x"05",
        16#04# => x"3C", 16#05# => x"02", 16#06# => x"00", 16#07# => x"03",
        16#08# => x"3C", 16#09# => x"03", 16#0A# => x"00", 16#0B# => x"07",
        16#0C# => x"00", 16#0D# => x"22", 16#0E# => x"20", 16#0F# => x"20",
        others => x"00"
    );

    signal base : natural range 0 to 511;

begin

    base <= to_integer(unsigned(Addr(8 downto 0)));

    Data <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3)
            when base <= 508
            else (others => '0');

end architecture rtl;
