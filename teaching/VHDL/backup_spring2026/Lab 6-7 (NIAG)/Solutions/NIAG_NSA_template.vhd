library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

use work.LabCPU_Pkg.all;
use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_NSA
-- Next Instruction Address Generation:
-- Next Sequential Address block
--
-- Purpose:
-- This component calculates the address of the next instruction
-- when the CPU continues executing normally in sequence.
--
-- Main idea:
-- If the current instruction is at address PC,
-- the next sequential instruction is located at:
--
--     NSA = PC + instruction size
--
-- In this CPU, the instruction size is given by:
--     CPU_BYTE_SIZE
--
-- Example:
-- If PC = x"00000020"
-- then PC = 32 decimal
--
-- If CPU_BYTE_SIZE = 4
-- then:
--     NSA = 32 + 4 = 36
--
-- Binary example:
-- PC              = 00000000 00000000 00000000 00100000
-- CPU_BYTE_SIZE   = 00000000 00000000 00000000 00000100
-- NSA             = 00000000 00000000 00000000 00100100
--
    -- TODO:
    -- Compute the next sequential address.
    --
    -- Steps:
    -- 1. Convert PC to UNSIGNED so arithmetic can be used.
    -- 2. Add the instruction size in bytes:
-- So the next instruction address becomes x"00000024".
-- =========================================================
entity NIAG_NSA is
	port (
		-- Current Program Conter Value 
		PC : in STD_LOGIC_VECTOR(31 downto 0);
		
		-- Next Sequential Address
		NSA : out STD_LOGIC_VECTOR(31 downto 0)
		);
end NIAG_NSA;

architecture rtl of NIAG_NSA is
begin
    -- =====================================================
    --        CPU_BYTE_SIZE
    -- 3. Convert the result back to STD_LOGIC_VECTOR.
    --
    -- Complete the expression below.
    -- =====================================================
	NSA <= std_logic_vector( unsigned(PC) + to_unsigned(CPU_BYTE_SIZE, CPU_BIT_SIZE)
			);
end rtl;



	 
	 