library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This block implements a tri-state buffer.
-- No decoder constants are used here.
-- Instead, OE directly controls the output behavior:
--   OE = '1' -> drive OUTP with INP
--   OE = '0' -> place OUTP in high-impedance ('Z')
entity TriBuffer is
    Port (
        OE   : in  STD_LOGIC;   -- Direct output enable
        INP  : in  STD_LOGIC;   -- Data input
        OUTP : out STD_LOGIC    -- Tri-state output
    );
end TriBuffer;

architecture Behavioral of TriBuffer is
begin

    -- Tri-state assignment:
    -- When enabled, the output follows the input.
    -- When disabled, the output is disconnected (Hi-Z).
    OUTP <= INP when OE = '1' else
            'Z';

end Behavioral;