--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 10, Example 1 - Pulling an instruction apart
--
-- A 32-bit instruction is not one number. It is several fields packed together,
-- and WHICH fields exist depends on the format.
--
--   R-type   | opcode |  rs   |  rt   |  rd   |  sa   | func  |
--            |   6    |   5   |   5   |   5   |   5   |   6   |
--            31....26 25...21 20...16 15...11 10....6 5.....0
--
--   I-type   | opcode |  rs   |  rt   |     immediate         |
--            |   6    |   5   |   5   |          16           |
--            31....26 25...21 20...16 15..................... 0
--
--   J-type   | opcode |              index                    |
--            |   6    |               26                      |
--            31....26 25..................................... 0
--
-- NOTICE: the opcode is ALWAYS in the same place, bits 31..26. It has to be -
-- until you have decoded it you do not know which format you are looking at,
-- so the one field you need first must be in a fixed position.
--
-- Notice too that rs and rt are always in the same place across R and I types.
-- That is not luck: it means the register file can start reading BEFORE the
-- instruction is decoded. Field placement in an ISA is a hardware decision.
--
-- Extracting the fields is pure wiring - slices of a vector, no logic at all.
-- All three formats are extracted simultaneously and unconditionally; the
-- decoder then decides which set means anything.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity fields is
    port (
        Instr  : in  std_logic_vector(31 downto 0);
        Opcode : out std_logic_vector(5 downto 0);
        RS     : out std_logic_vector(4 downto 0);
        RT     : out std_logic_vector(4 downto 0);
        RD     : out std_logic_vector(4 downto 0);
        SA     : out std_logic_vector(4 downto 0);
        Func   : out std_logic_vector(5 downto 0);
        Immed  : out std_logic_vector(15 downto 0);
        Index  : out std_logic_vector(25 downto 0)
    );
end entity fields;

architecture rtl of fields is
begin

    -- Every field, extracted at once. No conditions, no logic - just slices.
    Opcode <= Instr(31 downto 26);
    RS     <= Instr(25 downto 21);
    RT     <= Instr(20 downto 16);
    RD     <= Instr(15 downto 11);
    SA     <= Instr(10 downto  6);
    Func   <= Instr( 5 downto  0);
    Immed  <= Instr(15 downto  0);
    Index  <= Instr(25 downto  0);

end architecture rtl;
