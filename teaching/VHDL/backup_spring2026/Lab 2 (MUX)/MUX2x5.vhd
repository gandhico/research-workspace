library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This module implements a 2-to-1 multiplexer for 5-bit vectors.
-- Depending on the value of Sel, the output Y takes either In0 or In1.
entity ALUshftMUX is
    Port (
        Sel  : in  STD_LOGIC;                    -- Select signal
        In0  : in  STD_LOGIC_VECTOR(4 downto 0); -- Input 0
        In1  : in  STD_LOGIC_VECTOR(4 downto 0); -- Input 1
        Y    : out STD_LOGIC_VECTOR(4 downto 0)  -- Multiplexer output
    );
end ALUshftMUX;

-- Behavioral architecture:
-- Describes the multiplexer using a conditional signal assignment.
architecture Behavioral of ALUshftMUX is
begin

    -- If Sel = '0', pass In0 to the output.
    -- Otherwise, pass In1 to the output.
    Y <= In0 when Sel = '0' else
         In1;

end Behavioral;

