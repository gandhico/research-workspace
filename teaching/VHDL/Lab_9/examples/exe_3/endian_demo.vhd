--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9, Example 3 - The same bytes, two conventions, two different programs
--
-- Endianness is a DECISION. This example shows what it costs to get it wrong.
--
-- Take four bytes out of the Lab 12 program, at address 0x08:
--
--     20  21  FF  FF
--
--   BIG-endian    (MSB at the lowest address):  0x2021FFFF
--       opcode = 001000 = ADDI, rs = 00001, rt = 00001, imm = 0xFFFF = -1
--       -> ADDI r1, r1, -1     ... the loop counter decrement. Correct.
--
--   LITTLE-endian (LSB at the lowest address):  0xFFFF2120
--       opcode = 111111 = 63   ... not an instruction in this ISA at all
--       -> the decoder falls through to its safe default and does nothing,
--          the loop never decrements, and the program runs forever.
--
-- SAME BYTES. SAME MEMORY. Different machine.
--
-- This is why a binary compiled for one convention cannot run on the other,
-- and why every processor manual states its byte order on about page three.
--
-- THIS CPU IS BIG-ENDIAN. Say so in your report. A memory whose byte order is
-- undocumented is a memory nobody else can use - including you, in six weeks,
-- when you are debugging Lab 12 at midnight.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity endian_demo is
    port (
        B0, B1, B2, B3 : in  std_logic_vector(7 downto 0);  -- bytes at A..A+3
        BigEndian    : out std_logic_vector(31 downto 0);
        LittleEndian : out std_logic_vector(31 downto 0)
    );
end entity endian_demo;

architecture rtl of endian_demo is
begin

    -- Most significant byte at the LOWEST address.
    BigEndian    <= B0 & B1 & B2 & B3;

    -- Least significant byte at the lowest address.
    LittleEndian <= B3 & B2 & B1 & B0;

end architecture rtl;
