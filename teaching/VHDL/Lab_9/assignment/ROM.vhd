--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9 - Assignment, Part 1 of 2
--
-- ROM : 512-byte instruction memory, preloaded with the program your CPU runs
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- ============================================================================
-- THE PROGRAM. This is what your processor executes in Lab 12.
-- ============================================================================
--
--   addr   bytes          instruction          meaning
--   ----   ------------   ------------------   -----------------------------
--   0x00   3C 01 00 0B    LUI  r1, 11          r1 <- 11   (the loop counter)
--   0x04   3C 02 00 01    LUI  r2, 1           r2 <- 1    (the accumulator)
--   0x08   20 21 FF FF    ADDI r1, r1, -1      loop top: count down
--   0x0C   18 20 00 02    BLEZ r1, +2          exit when r1 <= 0  -> 0x18
--   0x10   00 02 10 40    SLL  r2, r2, 1       r2 <- r2 * 2
--   0x14   08 00 00 02    J    0x08            back to the loop top
--   0x18   AC 02 00 00    SW   r2, 0(r0)       store the result at address 0
--
--   It doubles r2 once per pass and stops when the counter reaches zero.
--   Ten passes. 2^10 = 1024 = 0x400, stored at memory address 0.
--
--   *** YOUR CPU COMPUTES 2^10. *** That is the sentence at the end of Lab 12.
--
-- NOTE ON LUI: this CPU treats LUI as a plain ZERO-EXTENDED immediate load, not
-- a shifted upper load. That is a deliberate simplification of the real MIPS
-- instruction, and it is documented here so that you know the difference when
-- you read the actual ISA. LUI r1, 11 loads 11, not 11 << 16.
--
-- ============================================================================
-- WHAT YOU BUILD
-- ============================================================================
--
--   512 bytes, byte-addressed. Combinational read - no clock.
--   Word assembly is BIG-ENDIAN:
--
--     Data(31 downto 24) = M[A]      Data(23 downto 16) = M[A+1]
--     Data(15 downto  8) = M[A+2]    Data( 7 downto  0) = M[A+3]
--
--   A ROM is combinational and its contents are a 'constant', fixed at
--   synthesis time. That is what read-only means: the running program cannot
--   overwrite itself, which is exactly what you want of instruction memory.
--
-- WATCH THE ADDRESS RANGE. Addr is 32 bits; the memory has 512 bytes. You must
-- reduce the address to a valid index. Reading M[base+3] when base is 511 is an
-- out-of-range error that stops the simulation dead - guard it.
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

    -- The program, byte by byte. Given to you complete - do not change it.
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

begin

    -- TODO 1: reduce the 32-bit address to a valid byte index into MEM.
    --         Only the low bits matter. Which ones, for 512 bytes?

    -- TODO 2: assemble four consecutive bytes into one 32-bit word, BIG-ENDIAN.
    --         Guard the range: if the index is near the top of memory, reading
    --         base+3 would be out of bounds and the simulation would stop.
    --         Returning zeros for an out-of-range read is an acceptable answer -
    --         say in your report what you chose and why.

end architecture rtl;
