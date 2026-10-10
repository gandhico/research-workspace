library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This module implements a 3-to-1 multiplexer for 32-bit vectors.
-- The 2-bit select signal chooses which input is sent to the output.
entity DinMUX is
    Port (
        Sel  : in  STD_LOGIC_VECTOR(1 downto 0);  -- 2-bit select signal
        In0  : in  STD_LOGIC_VECTOR(31 downto 0); -- Input selected when Sel = "00"
        In1  : in  STD_LOGIC_VECTOR(31 downto 0); -- Input selected when Sel = "01"
        In2  : in  STD_LOGIC_VECTOR(31 downto 0); -- Input selected when Sel = "10"
        Y    : out STD_LOGIC_VECTOR(31 downto 0)  -- Multiplexer output
    );
end DinMUX;

-- Behavioral architecture:
-- Describes the multiplexer using a combinational process.
architecture Behavioral of DinMUX is
begin

    -- Combinational process:
    -- Any change in the select signal or inputs updates the output immediately.
    process(Sel, In0, In1, In2)
    begin
        -- Select one of the three 32-bit inputs
        case Sel is
            when "00" => 
                Y <= In0;  -- Route In0 to the output

            when "01" => 
                Y <= In1;  -- Route In1 to the output

            when "10" => 
                Y <= In2;  -- Route In2 to the output

            when others => 
                -- Default case:
                -- If Sel = "11" or has an undefined value,
                -- drive the output with all zeros
                Y <= (others => '0');
        end case;
    end process;

end Behavioral;