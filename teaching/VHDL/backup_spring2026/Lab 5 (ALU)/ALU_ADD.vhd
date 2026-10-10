library IEEE;                          -- Import the IEEE library
use IEEE.STD_LOGIC_1164.ALL;          -- Import standard logic definitions
use IEEE.NUMERIC_STD.ALL;             -- Import numeric operations for signed/unsigned types

use work.ALU_Pkg.all;                 -- Import all definitions from the custom ALU package

entity ALU_ADD is                     -- Define the ALU_ADD entity
    port(                             -- Begin port declaration
        A       : in  STD_LOGIC_VECTOR(31 downto 0);  -- 32-bit input operand A
        B       : in  STD_LOGIC_VECTOR(31 downto 0);  -- 32-bit input operand B
        FuncSel : in  STD_LOGIC_VECTOR(4 downto 0);   -- 5-bit function select input
        Shift   : in  STD_LOGIC_VECTOR(4 downto 0);   -- 5-bit shift input (unused here)
        Result  : out STD_LOGIC_VECTOR(31 downto 0);  -- 32-bit output result
        S       : out STD_LOGIC;                      -- Sign flag output
        Z       : out STD_LOGIC                       -- Zero flag output
    );                               -- End port declaration
end ALU_ADD;                         -- End entity definition

architecture rtl of ALU_ADD is       -- Begin RTL architecture
    signal sum_val : signed(31 downto 0); -- Internal signed signal to hold the sum
begin                                 -- Begin architecture body
    sum_val <= signed(A) + signed(B); -- Continuously add A and B as signed values

    process(A, B, FuncSel, Shift, sum_val) -- Combinational process sensitive to inputs and sum
    begin                             -- Begin process
        Result <= (others => '0');    -- Default Result to all zeros
        S <= '0';                     -- Default Sign flag to 0
        Z <= '0';                     -- Default Zero flag to 0

        if FuncSel = ALU_fUNC_ADD then -- Check if the selected ALU function is ADD
            Result <= std_logic_vector(sum_val); -- Assign the computed sum to the output

            if sum_val(31) = '1' then -- Check if the most significant bit is 1 (negative result)
                S <= '1';             -- Set Sign flag
            end if;                   -- End sign check

            if sum_val = to_signed(0, 32) then -- Check if the sum is zero
                Z <= '1';             -- Set Zero flag
            end if;                   -- End zero check
        end if;                       -- End function select check
    end process;                      -- End process

end rtl;                              -- End architecture