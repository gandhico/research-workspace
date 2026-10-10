--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4 - Assignment, Part 2 of 3
--
-- TriBuffer : 32-bit tri-state buffer - the register file's gateway onto the
--             shared memory data bus
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- SPECIFICATION - Table C
--
--   #  Sel  ||  Dout
--   0   0   ||  Z...Z    (all 32 bits high-impedance - not driving)
--   1   1   ||  Din
--
-- THIS IS NOT A BOOLEAN FUNCTION. Its output range is {0, 1, Z} and Boolean
-- algebra only has {0, 1}. You cannot write it as AND/OR/NOT, and you should
-- say so in your report - it is the first component in this course that lives
-- outside Boolean algebra.
--
-- WHERE IT GOES: in Lab 9 the RAM drives the memory data bus when reading, and
-- the register file drives it through this buffer when writing. Exactly one of
-- them may drive at a time. Enable both and you get 'X' across all 32 bits.
--
-- VHDL: releasing a whole vector needs an aggregate, not a single 'Z':
--       Dout <= (others => 'Z');
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity TriBuffer is
    port (
        Din  : in  std_logic_vector(31 downto 0);
        Sel  : in  std_logic;                       -- '1' drive, '0' release
        Dout : out std_logic_vector(31 downto 0)
    );
end entity TriBuffer;

architecture rtl of TriBuffer is
begin

    -- TODO: implement the table above.
    --       Both rows must assign something. Row 0 assigns 'Z', which is an
    --       assignment - "not driving" is a deliberate output, not a gap.

end architecture rtl;
