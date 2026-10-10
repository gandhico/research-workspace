library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This module implements a 2-to-1 multiplexer for 32-bit vectors.
-- The output Y selects either In0 or In1 according to Sel.
entity ALUinMUX is
    Port (
        Sel  : in  STD_LOGIC;                      -- Select signal
        In0  : in  STD_LOGIC_VECTOR(31 downto 0); -- First 32-bit input
        In1  : in  STD_LOGIC_VECTOR(31 downto 0); -- Second 32-bit input
        Y    : out STD_LOGIC_VECTOR(31 downto 0)  -- Selected 32-bit output
    );
end ALUinMUX;

-- Behavioral architecture:
-- Uses a conditional signal assignment to describe the MUX behavior.
architecture Behavioral of ALUinMUX is
begin

    -- If Sel = '0', the output is In0.
    -- If Sel = '1', the output is In1.
    Y <= In0 when Sel = '0' else
         In1;

end Behavioral;