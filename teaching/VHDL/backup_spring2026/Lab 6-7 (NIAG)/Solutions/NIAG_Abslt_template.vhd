library IEEE;
use IEEE.STD_LOGIC_1164.all;

use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_Abslt
-- Next Instruction Address Generation:
-- Absolute Address block
--
-- Purpose:
-- This component builds the absolute jump address used by
-- jump-type instructions.
--
-- Main idea:
-- The absolute address is formed by concatenating:
--
--     { NSA(31 downto 28), Index(25 downto 0), "00" }
--
-- This means:
-- 1. Take the upper 4 bits from NSA
-- 2. Append the 26-bit Index field from the instruction
-- 3. Append "00" to word-align the address
--
-- Why add "00"?
-- Because instructions are word aligned, so instruction
-- addresses must end in two zeros.
--
-- Example:
-- Suppose:
--     NSA   = 0001 0010 0011 0100 0101 0110 0111 1000
--     Index = 10101010110011001100110011
--
-- Then:
--     NSA(31 downto 28) = 0001
--
-- Absolute address becomes:
--     0001 & 10101010110011001100110011 & 00
--
-- Final result:
--     00011010101011001100110011001100
--
-- So this block assembles the 32-bit absolute jump address.
-- =========================================================

entity NIAG_Abslt is

	port (
		Index : in STD_LOGIC_VECTOR(25 downto 0);
		
		NSA : in STD_LOGIC_VECTOR(31 downto 0);
		
		AbsltAdrs : out STD_LOGIC_VECTOR(31 downto 0)
		);
		
end NIAG_Abslt;

architecture rtl of NIAG_Abslt is
begin

    -- =====================================================
    -- TODO:
    -- Build the absolute address using concatenation.
    --
    -- Steps:
    -- 1. Take the upper 4 bits of NSA:
    --        NSA(31 downto 28)
    -- 2. Concatenate the 26-bit Index field
    -- 3. Append "00" at the end for word alignment
    --
    -- Complete the expression below.
    -- =====================================================
	AbsltAdrs <= NSA(31 downto 28) & Index & "00";
	
end rtl;

	 
	 
	 
	 