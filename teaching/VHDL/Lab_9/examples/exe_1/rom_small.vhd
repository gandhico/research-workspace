--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9, Example 1 - A ROM, and how four bytes become one instruction
--
-- Memory is BYTE-ADDRESSED: every address names one 8-bit byte. Instructions
-- are 32 bits. So fetching one instruction means reading FOUR consecutive
-- bytes and assembling them into a word.
--
--   Data(31 downto 24) = M[A]
--   Data(23 downto 16) = M[A+1]
--   Data(15 downto  8) = M[A+2]
--   Data( 7 downto  0) = M[A+3]
--
-- That ordering - most significant byte at the LOWEST address - is called
-- BIG-ENDIAN. The other choice, least significant byte first, is little-endian.
--
-- ENDIANNESS IS A DECISION, NOT A FACT.
--   Neither is more correct. But the two are not compatible: the SAME bytes
--   decode to DIFFERENT instructions under the two conventions, which is
--   exactly why a program compiled for one crashes on the other.
--   Example 3 shows this happening.
--
--   This CPU is big-endian. Write that down in your report - a memory whose
--   byte order is undocumented is a memory nobody else can use.
--
-- A ROM IS COMBINATIONAL
--   No clock. Present an address, the data appears. The contents are fixed at
--   synthesis time by the 'constant' below, which is what makes it read-only.
--   The instruction memory in your CPU is a ROM precisely because a running
--   program must not be able to overwrite itself by accident.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity rom_small is
    port (
        Addr : in  std_logic_vector(31 downto 0);
        Data : out std_logic_vector(31 downto 0)
    );
end entity rom_small;

architecture rtl of rom_small is

    type rom_array is array (0 to 15) of std_logic_vector(7 downto 0);

    -- Sixteen bytes = four instructions. Laid out one instruction per line so
    -- the byte order is visible.
    constant MEM : rom_array := (
        16#00# => x"3C", 16#01# => x"01", 16#02# => x"00", 16#03# => x"0B",
        16#04# => x"3C", 16#05# => x"02", 16#06# => x"00", 16#07# => x"01",
        16#08# => x"20", 16#09# => x"21", 16#0A# => x"FF", 16#0B# => x"FF",
        16#0C# => x"18", 16#0D# => x"20", 16#0E# => x"00", 16#0F# => x"02"
    );

    signal base : natural range 0 to 15;

begin

    base <= to_integer(unsigned(Addr(3 downto 0)));

    -- Assemble four bytes into one 32-bit word, big-endian.
    -- Note this only works for an ALIGNED address (a multiple of 4). Reading a
    -- word from address 1 would straddle two instructions - see Example 3.
    Data <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3);

end architecture rtl;
