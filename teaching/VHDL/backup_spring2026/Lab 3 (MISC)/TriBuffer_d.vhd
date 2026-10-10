library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.EE362Decoder.ALL;

-- Entity declaration:
-- Implements a tri-state buffer.
-- Output behavior is controlled by symbolic constants from EE362Decoder:
--   RF_OE_DRIVE -> output drives the input value
--   RF_OE_HiZ   -> output goes to high impedance
entity TriBuffer is
    Port (
        OE   : in  STD_LOGIC;  -- Output-enable control from decoder constants
        INP  : in  STD_LOGIC;  -- Data input
        OUTP : out STD_LOGIC   -- Tri-state output
    );
end TriBuffer;

architecture Behavioral of TriBuffer is
begin

    -- Tri-state behavior:
    -- when OE requests DRIVE, output follows input
    -- when OE requests Hi-Z, output floats
    OUTP <= INP when OE = RF_OE_DRIVE else
            'Z';

end Behavioral;