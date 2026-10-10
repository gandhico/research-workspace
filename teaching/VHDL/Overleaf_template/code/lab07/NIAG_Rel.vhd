-- PLACEHOLDER: replace with YOUR OWN NIAG_Rel.vhd
--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7 - Assignment, Part 2 of 3
--
-- NIAG_Rel : PC-relative branch target
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION
--   Rel = NSA + Xtnd32
--
--   where NSA is PC+4 (Part 1) and Xtnd32 is the sign-extended, shifted-by-two
--   immediate that your Lab 4 ImmedXtnd produces with Xsel='1' and Xlsft='1'.
--
-- YOU ARE NOT WRITING THE EXTENDER AGAIN.
--   ImmedXtnd already does SignExt-then-shift. In the real CPU it is a SHARED
--   block: its output feeds both the ALU (for ADDI, LW, SW) and this adder (for
--   branches). That is why the extension happens outside this entity rather
--   than inside it - one extender, two consumers.
--
--   Your testbench wires your Lab 4 ImmedXtnd to this component's Xtnd32 input,
--   exactly as the CPU does in Lab 12. Copy your ImmedXtnd.vhd into this folder.
--
-- WORKED EXAMPLE - a real instruction from the Lab 12 program
--
--   0x0C   0x18200002   BLEZ r1, +2
--
--     NSA    = 0x0C + 4                    = 0x10
--     Xtnd32 = SignExt(0x0002) << 2 = 2x4  = 0x00000008
--     Rel    = 0x10 + 0x08                 = 0x18    <- the SW, the loop exit
--
--   Verify that by hand before you simulate. If you cannot predict it, you
--   cannot debug it.
--
-- THE TWO WAYS THIS GOES WRONG (Example 3 shows both):
--   forgot the shift  -> off by a FACTOR; target not a multiple of 4
--   used PC not PC+4  -> off by a CONSTANT 4; still aligned, still nearly right
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity NIAG_Rel is
    port (
        NSA    : in  std_logic_vector(31 downto 0);  -- PC + 4, the BASE
        Xtnd32 : in  std_logic_vector(31 downto 0);  -- from ImmedXtnd, already x4
        Rel    : out std_logic_vector(31 downto 0)
    );
end entity NIAG_Rel;

architecture rtl of NIAG_Rel is
begin

    -- TODO: one line. Note that both operands are already 32 bits and the
    --       offset is already sign-extended, so a plain add is correct -
    --       two's complement addition handles the negative case by itself.

end architecture rtl;
