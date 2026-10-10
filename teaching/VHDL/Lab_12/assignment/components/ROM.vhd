--------------------------------------------------------------------------------
-- EE 362 - Lab 12 - REFERENCE COMPONENT
--
-- This is the TA reference implementation, provided so that nobody is blocked
-- from building the CPU by an earlier lab that did not finish.
--
--   >>> REPLACE THIS FILE WITH YOUR OWN VERSION IF YOU HAVE ONE. <<<
--
-- Using a reference component costs you nothing on this lab. Your grade for
-- the earlier lab simply stands as it was. Integration is never gated on an
-- earlier miss - that is a deliberate rule of this course, not a favour.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Lab 9 reference component
--
-- ROM : 512-byte instruction memory holding the Lab 12 program.
-- Combinational, big-endian, range-guarded.
--
-- Marking points:
--   * address reduced with Addr(8 downto 0) - 512 bytes needs 9 bits
--   * big-endian assembly: M[A] lands in bits 31..24
--   * the top-of-memory guard: base+3 must not exceed 511
--   * no clock anywhere
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
        16#00# => x"3C", 16#01# => x"01", 16#02# => x"00", 16#03# => x"0B",
        16#04# => x"3C", 16#05# => x"02", 16#06# => x"00", 16#07# => x"01",
        16#08# => x"20", 16#09# => x"21", 16#0A# => x"FF", 16#0B# => x"FF",
        16#0C# => x"18", 16#0D# => x"20", 16#0E# => x"00", 16#0F# => x"02",
        16#10# => x"00", 16#11# => x"02", 16#12# => x"10", 16#13# => x"40",
        16#14# => x"08", 16#15# => x"00", 16#16# => x"00", 16#17# => x"02",
        16#18# => x"AC", 16#19# => x"02", 16#1A# => x"00", 16#1B# => x"00",
        others => x"00"
    );

    signal base : natural range 0 to 511;

begin

    -- 512 bytes needs 9 address bits.
    base <= to_integer(unsigned(Addr(8 downto 0)));

    -- Big-endian word assembly, guarded against running off the top.
    Data <= MEM(base) & MEM(base + 1) & MEM(base + 2) & MEM(base + 3)
            when base <= 508
            else (others => '0');

end architecture rtl;
