library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

use work.LabCPU_Pkg.all;
use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_Rtn
-- Next Instruction Address Generation:
-- Return Address block
--
-- Purpose:
-- This component generates the return address used by
-- call-type instructions.
--
-- Main idea:
-- When the CPU executes a function call, it must save the
-- address of the instruction that should run after the
-- function finishes.
--
-- That return address is:
--
--     RtnAdrs = PC + instruction size
--
-- In this CPU, the instruction size is given by:
--     CPU_BYTE_SIZE
--
-- Example:
-- If:
--     PC = x"00000020"
-- and:
--     CPU_BYTE_SIZE = 4
--
-- Then:
--     RtnAdrs = 32 + 4 = 36 = x"00000024"
--
-- Binary example:
-- PC              = 00000000 00000000 00000000 00100000
-- CPU_BYTE_SIZE   = 00000000 00000000 00000000 00000100
-- RtnAdrs         = 00000000 00000000 00000000 00100100
--
-- So this block saves the address of the next instruction,
-- which is where execution should return after the call.
-- =========================================================

entity NIAG_Rtn is 
	port (
		-- Current Program Counter Value
		PC : in STD_LOGIC_VECTOR(31 downto 0);
		
		-- Return address for a call instruction
		RtnAdrs : out STD_LOGIC_VECTOR(31 downto 0)
		);
end NIAG_Rtn;


architecture rtl of NIAG_Rtn is
begin

    -- =====================================================
    -- TODO:
    -- Compute the return address.
    --
    -- Steps:
    -- 1. Convert PC to UNSIGNED so arithmetic can be used.
    -- 2. Add the instruction size in bytes:
    --        CPU_BYTE_SIZE
    -- 3. Convert the result back to STD_LOGIC_VECTOR.
    --
    -- Complete the expression below.
    -- =====================================================
	RtnAdrs <= STD_LOGIC_VECTOR(unsigned(PC) + to_unsigned(CPU_BYTE_SIZE, CPU_BIT_SIZE));
	
end rtl;

	 
	 