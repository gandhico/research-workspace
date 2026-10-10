--------------------------------------------------------------------------------
-- EE 362 - Final Lab, Track A - reference test program for ORI
--                                       (TA only - also given to students)
--
-- A four-instruction program that exercises the new instruction and nothing
-- else. Small on purpose: an extension is verified by a test you can hand-check
-- in thirty seconds, not by re-running the big loop.
--
--   addr   bytes          instruction            effect
--   ----   ------------   --------------------   ------------------------
--   0x00   3C 01 00 00    LUI  r1, 0             r1 <- 0x00000000
--   0x04   34 21 00 F0    ORI  r1, r1, 0x00F0    r1 <- 0x000000F0
--   0x08   34 21 00 0F    ORI  r1, r1, 0x000F    r1 <- 0x000000FF
--   0x0C   AC 01 00 00    SW   r1, 0(r0)         store 0xFF at address 0
--
-- Expected: r1 = 0x000000FF, and 0x000000FF stored at address 0.
--
-- WHY TWO ORIs: the second one proves the instruction ORs into an existing
-- value rather than simply loading the immediate. One ORI would pass even if
-- you had implemented it as "copy the immediate", which is a real thing people
-- do by accident when they clone the LUI row.
--
-- WHY ORI ZERO-EXTENDS: its immediate is a bit pattern, not a number - the same
-- argument as LUI in Lab 4. Sign-extending it would set the top 16 bits for any
-- immediate with bit 15 high, which is not what "or in these bits" means.
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
        16#00# => x"3C", 16#01# => x"01", 16#02# => x"00", 16#03# => x"00",
        16#04# => x"34", 16#05# => x"21", 16#06# => x"00", 16#07# => x"F0",
        16#08# => x"34", 16#09# => x"21", 16#0A# => x"00", 16#0B# => x"0F",
        16#0C# => x"AC", 16#0D# => x"01", 16#0E# => x"00", 16#0F# => x"00",
        others => x"00"
    );

    signal base : natural range 0 to 511;

begin

    base <= to_integer(unsigned(Addr(8 downto 0)));

    Data <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3)
            when base <= 508
            else (others => '0');

end architecture rtl;
