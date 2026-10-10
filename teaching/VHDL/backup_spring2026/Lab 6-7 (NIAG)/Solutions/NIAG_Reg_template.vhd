library IEEE;
use IEEE.STD_LOGIC_1164.all;

use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_Reg
-- Next Instruction Address Generation:
-- Register Address block
--
-- Purpose:
-- This component provides the next instruction address
-- directly from a register value.
--
-- Main idea:
-- Some instructions obtain the next address from a CPU
-- register instead of computing it from PC or instruction
-- fields.
--
-- In this case:
--
--     RegAdrs = Reg
--
-- So this block simply forwards the register value to the
-- output.
--
-- Example:
-- If:
--     Reg = x"00000080"
--
-- Then:
--     RegAdrs = x"00000080"
--
-- Binary example:
-- Reg      = 00000000 00000000 00000000 10000000
-- RegAdrs  = 00000000 00000000 00000000 10000000
--
-- No addition or concatenation is needed here.
-- =========================================================
	entity NIAG_Reg is
		port (	
		
			-- Register value that already contains the next address
			Reg : in STD_LOGIC_VECTOR(31 downto 0);
			
			-- Register-based next instruction address
			RegAdrs : out STD_LOGIC_VECTOR(31 downto 0)
			);
	end NIAG_Reg;
	

architecture rtl of NIAG_Reg is
begin
    -- =====================================================
    -- TODO:
    -- For register addressing, the output address is simply
    -- the same value stored in the register input.
    --
    -- Complete the assignment below.
    -- =====================================================

	 RegAdrs <= Reg;
	 
end rtl;








	 