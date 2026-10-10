--------------------------------------------------------------------------------
-- EE 362 - Lab 4 REFERENCE SOLUTION  (TA only - do not publish)
--
-- ImmedXtnd : 16 -> 32 immediate extension, with optional left shift by 2
--
--   #  Xsel  Xlsft  ||  Xtnd32
--   0    0     0    ||  0^16 & I
--   1    1     0    ||  I(15)^16 & I
--   2    1     1    ||  I(15)^14 & I & "00"
--   3    0     1    ||  0^14 & I & "00"
--
-- Built in two steps - extend, then shift - because that is far easier to read
-- than one expression, and the RTL Viewer shows the two stages separately.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ImmedXtnd is
    port (
        Immed16 : in  std_logic_vector(15 downto 0);
        Xsel    : in  std_logic;
        Xlsft   : in  std_logic;
        Xtnd32  : out std_logic_vector(31 downto 0)
    );
end entity ImmedXtnd;

architecture rtl of ImmedXtnd is

    signal extended : std_logic_vector(31 downto 0);

begin

    -- Step 1: widen. The top 16 bits are '0' (zero-extend) or copies of the
    -- sign bit (sign-extend). One control bit chooses which.
    extended <= (31 downto 16 => Immed16(15)) & Immed16 when Xsel = '1'
           else (31 downto 16 => '0')         & Immed16;

    -- Step 2: shift by two, or not. Both cases assign, so no latch.
    Xtnd32 <= extended(29 downto 0) & "00" when Xlsft = '1'
         else extended;

end architecture rtl;
