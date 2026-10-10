library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- Entity declaration:
-- This module implements a 3-to-1 multiplexer for 5-bit vectors.
-- According to the 2-bit select signal Sel, the output Y takes
-- the value of In0, In1, or In2.
entity DselMUX is
    Port (
        Sel  : in  STD_LOGIC_VECTOR(1 downto 0); -- 2-bit select signal
        In0  : in  STD_LOGIC_VECTOR(4 downto 0); -- Input selected when Sel = "00"
        In1  : in  STD_LOGIC_VECTOR(4 downto 0); -- Input selected when Sel = "01"
        In2  : in  STD_LOGIC_VECTOR(4 downto 0); -- Input selected when Sel = "10"
        Y    : out STD_LOGIC_VECTOR(4 downto 0)  -- Multiplexer output
    );
end DselMUX;

-- Behavioral architecture:
-- Describes the multiplexer behavior with a process and case statement.
architecture Behavioral of DselMUX is
begin

    -- Combinational process:
    -- Any change in Sel or the inputs is immediately reflected at output Y.
    process(Sel, In0, In1, In2)
    begin
        -- Select which input is routed to the output
        case Sel is
            when "00" => 
                Y <= In0;  -- Output In0

            when "01" => 
                Y <= In1;  -- Output In1

            when "10" => 
                Y <= In2;  -- Output In2

            when others => 
                -- Default case:
                -- If Sel = "11" or any undefined value, output zeros
                Y <= (others => '0');
        end case;
    end process;

end Behavioral;