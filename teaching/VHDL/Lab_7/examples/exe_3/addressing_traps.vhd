--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7, Example 3 - Three ways to compute a branch target, two of them wrong
--
-- All three of these compile. All three produce plausible-looking 32-bit
-- addresses. Two of them are wrong, and the symptoms are worth recognising
-- BEFORE you meet them in Lab 12, where they look like "my CPU jumps to
-- nonsense".
--
--   GOOD    target = (PC + 4) + (SignExt(imm) << 2)
--   NOSHIFT target = (PC + 4) +  SignExt(imm)          <- forgot the x4
--   BASEPC  target =  PC      + (SignExt(imm) << 2)    <- used PC, not PC+4
--
-- THE SYMPTOMS, and how to tell them apart in a waveform:
--
--   NOSHIFT is off by a FACTOR. A branch of +2 instructions lands 2 bytes
--           along instead of 8 - in the MIDDLE of an instruction. The CPU then
--           fetches a word straddling two instructions and executes garbage.
--           Tell-tale: the target is not a multiple of 4.
--
--   BASEPC  is off by a CONSTANT 4, always, in the same direction. Every
--           branch lands exactly one instruction early. Tell-tale: the target
--           is still word-aligned and still "nearly right", which makes this
--           the harder of the two to spot. Loops run one instruction too many
--           or too few.
--
-- "Off by a factor" and "off by a constant" are worth naming, because they are
-- the two shapes almost every addressing bug takes.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity addressing_traps is
    port (
        PC      : in  std_logic_vector(31 downto 0);
        Immed   : in  std_logic_vector(15 downto 0);
        Good    : out std_logic_vector(31 downto 0);
        NoShift : out std_logic_vector(31 downto 0);
        BasePC  : out std_logic_vector(31 downto 0)
    );
end entity addressing_traps;

architecture rtl of addressing_traps is

    signal nsa       : std_logic_vector(31 downto 0);
    signal ext       : std_logic_vector(31 downto 0);   -- sign-extended, no shift
    signal ext_shift : std_logic_vector(31 downto 0);   -- sign-extended, x4

begin

    nsa       <= std_logic_vector(unsigned(PC) + 4);
    ext       <= (31 downto 16 => Immed(15)) & Immed;
    ext_shift <= (31 downto 18 => Immed(15)) & Immed & "00";

    Good    <= std_logic_vector(unsigned(nsa) + unsigned(ext_shift));
    NoShift <= std_logic_vector(unsigned(nsa) + unsigned(ext));
    BasePC  <= std_logic_vector(unsigned(PC)  + unsigned(ext_shift));

end architecture rtl;
