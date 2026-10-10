--------------------------------------------------------------------------------
-- EE 362 - Lab 7 - STEP 1: REPLACE THIS FILE
--
-- This is the empty Lab 4 skeleton, included only so the Lab 7 project compiles
-- the moment you open it.
--
--   >>> Overwrite it with YOUR OWN completed ImmedXtnd.vhd from Lab 4. <<<
--
-- In the real CPU this extender is a SHARED block: its output feeds both the
-- ALU (for ADDI, LW, SW) and the branch adder you are building today. That is
-- why NIAG_Rel takes an already-extended value rather than doing the extension
-- itself - one extender, two consumers.
--
-- If your Lab 4 extender never worked, ask for the reference version rather
-- than being stuck. Using it costs you nothing on this lab.
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4 - Assignment, Part 1 of 3
--
-- ImmedXtnd : widen a 16-bit instruction immediate to the 32-bit datapath
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C
--
--   #  Xsel  Xlsft  ||  Xtnd32                    used by
--   0    0     0    ||  0^16 & I                  LUI       (zero, no shift)
--   1    1     0    ||  I(15)^16 & I              ADDI, LW, SW  (sign, no shift)
--   2    1     1    ||  I(15)^14 & I & "00"       BLEZ      (sign, x4)
--   3    0     1    ||  0^14 & I & "00"           (unused, but DEFINED)
--
--   x^n  means "bit x repeated n times".
--
-- Row 3 is not "impossible" and it is not "don't care". Leave it out and you
-- get an inferred latch - Lab 3, Example 3. Implement all four.
--
-- EQUATIONS
--   No shift:
--     Xtnd32_i = I_i                for i = 0..15
--     Xtnd32_i = Xsel . I_15        for i = 16..31      <- sign bit replicated
--
--   With x4 shift, where E is the extended value above:
--     Xtnd32_i = E_(i-2)            for i = 2..31
--     Xtnd32_1 = Xtnd32_0 = 0
--
-- WHY TWO KINDS OF EXTENSION EXIST
--   Widening a number is two different operations, and which one is right
--   depends on what the bits MEAN.
--     ADDI sign-extends: the immediate is a signed offset, so ADDI r1,r1,-1
--     must actually subtract one. Zero-extend it and -1 becomes +65535.
--     LUI zero-extends: its immediate is a bit pattern, not a number.
--   Your report must answer: why does ADDI sign-extend but LUI zero-extend?
--
-- WHY THE x4 SHIFT EXISTS
--   Branch offsets are counted in INSTRUCTIONS, not bytes. Instructions are
--   four bytes and word-aligned, so the low two bits of every instruction
--   address are always zero. Encoding them would waste two bits; instead we
--   shift, and get four times the branch range for free. You will use this
--   again, deliberately, in Lab 7.
--
-- VHDL YOU NEED
--   (31 downto 16 => I(15))       replicate a bit across a range
--   A & B                          concatenation
--   Build the extension first, then shift it. Two steps, one internal signal,
--   much easier to read than one enormous expression.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ImmedXtnd is
    port (
        Immed16 : in  std_logic_vector(15 downto 0);  -- IR immediate field
        Xsel    : in  std_logic;                      -- '0' zero, '1' sign
        Xlsft   : in  std_logic;                      -- '0' none, '1' shift x4
        Xtnd32  : out std_logic_vector(31 downto 0)
    );
end entity ImmedXtnd;

architecture rtl of ImmedXtnd is

    -- TODO 1: declare an internal signal to hold the extended-but-not-yet-
    --         shifted 32-bit value. Doing it in two steps is much clearer than
    --         one expression, and the RTL Viewer will show you why.


begin

    -- TODO 2: build the extension (rows 0/1 behaviour).
    --         The top 16 bits are either all '0' or all copies of Immed16(15).


    -- TODO 3: apply the shift, or not, according to Xlsft.
    --         Shifting left by 2 means: take bits 29..0 of the extended value
    --         and put "00" underneath them.
    --         Make sure BOTH values of Xlsft assign something.


end architecture rtl;
