--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 7, Example 2 - Computing a branch target from a real instruction
--
-- This example takes an ACTUAL instruction out of the ROM program your CPU
-- runs in Lab 12, and computes where it branches to.
--
--   address  encoding     instruction
--   0x0C     0x18200002   BLEZ r1, +2
--
-- FIELD EXTRACTION
--   0x18200002 = 0001 1000 0010 0000 0000 0000 0000 0010
--                ^^^^^^ opcode = 000110 = BLEZ
--                       ^^^^^ rs = 00001 = r1
--                            ^^^^^ rt = 00000
--                                 ^^^^^^^^^^^^^^^^ immediate = 0x0002
--
-- THE COMPUTATION
--   NSA    = PC + 4          = 0x0C + 4          = 0x10
--   offset = SignExt(0x0002) << 2 = 2 x 4        = 0x08
--   target = NSA + offset    = 0x10 + 0x08       = 0x18   <- the SW instruction
--
-- TWO QUESTIONS WORTH ANSWERING PROPERLY
--
--   Why is the base PC+4 and not PC?
--     Because by the time the branch is being evaluated, the fetch has already
--     happened - the hardware has moved on. Using PC would mean every branch
--     target was one instruction earlier than the assembler wrote, so the
--     assembler would have to compensate. Basing on PC+4 keeps the encoding
--     honest: "+2" really means "skip 2 instructions".
--
--   Why shift left by two?
--     Instructions are 4 bytes and word-aligned, so the low two bits of every
--     instruction address are ALWAYS ZERO. Encoding them would waste two bits
--     of the immediate on information we already know. Instead we shift, and
--     get FOUR TIMES the branch range for free.
--
--     That is a genuine architectural trade-off, and it fits in one line of
--     concatenation. It is also why the offset counts INSTRUCTIONS, not bytes.
--
-- REUSE: the extender you built in Lab 4 already does SignExt-then-shift.
-- Set Xsel = '1' (sign) and Xlsft = '1' (x4) and its output is the offset.
-- You are not writing that logic again.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity branch_target is
    port (
        PC     : in  std_logic_vector(31 downto 0);
        Immed  : in  std_logic_vector(15 downto 0);   -- IR immediate field
        NSA    : out std_logic_vector(31 downto 0);   -- PC + 4
        Target : out std_logic_vector(31 downto 0)    -- NSA + (SignExt(imm) << 2)
    );
end entity branch_target;

architecture rtl of branch_target is

    signal nsa_i   : std_logic_vector(31 downto 0);
    signal offset  : std_logic_vector(31 downto 0);

begin

    -- Next sequential address
    nsa_i <= std_logic_vector(unsigned(PC) + 4);
    NSA   <= nsa_i;

    -- Sign-extend to 32 bits, then shift left 2. This is exactly what your
    -- Lab 4 ImmedXtnd does with Xsel='1', Xlsft='1' - written out here so the
    -- arithmetic is visible in one place.
    offset <= (31 downto 18 => Immed(15)) & Immed & "00";

    -- The target. One adder, reused from the same idea as the ALU's.
    Target <= std_logic_vector(unsigned(nsa_i) + unsigned(offset));

end architecture rtl;
