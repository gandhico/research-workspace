


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





    -- =====================================================
    -- TODO:
    -- For register addressing, the output address is simply
    -- the same value stored in the register input.
    --
    -- Complete the assignment below.
    -- =====================================================

	 
	 