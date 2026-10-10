library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.all;

use work.NIAG_Pkg.all;

-- =========================================================
-- NIAG_Rel
-- Next Instruction Address Generation:
-- Relative Address block
--
-- Purpose:
-- This component calculates the next instruction address
-- for relative branches.
--
-- Main idea:
-- The relative address is obtained by adding a signed
-- displacement to the Next Sequential Address (NSA).
--
--     RelAdrs = NSA + displacement
--
-- The displacement comes from the immediate field.
--
-- If Xshft = '1':
--     the immediate is shifted left by 2 bits
--     to word-align the displacement
--
-- If Xshft = '0':
--     the immediate is used directly
--
-- Why shift left by 2?
-- Because instruction addresses are word aligned, so
-- a displacement in words must be converted to bytes.
--
-- Example 1:
-- If:
--     NSA   = x"00000020"   = 32
--     Immed = x"00000003"   = 3
--     Xshft = '1'
--
-- Then:
--     displacement = 3 << 2 = 12
--     RelAdrs      = 32 + 12 = 44 = x"0000002C"
--
-- Binary:
-- NSA             = 00000000 00000000 00000000 00100000
-- Immed           = 00000000 00000000 00000000 00000011
-- shifted Immed   = 00000000 00000000 00000000 00001100
-- RelAdrs         = 00000000 00000000 00000000 00101100
--
-- Example 2:
-- If Immed is negative, the displacement can move backward.
-- This is why SIGNED type is used.
-- =========================================================

entity NIAG_Rel is
	port (	
		-- Sign-Extended immediate value
		Immed : in STD_LOGIC_VECTOR(31 downto 0);
		
		-- Shift Control
		-- '1' = shift immediate left by 2
		-- 'o' = use immediate directly
		Xshft : in STD_LOGIC;
		
		-- Next Sequential Address
		NSA : in STD_LOGIC_VECTOR(31 downto 0);
		
		-- Relative branch adress
		RelAdrs : out STD_LOGIC_VECTOR(31 downto 0)
		);
end NIAG_Rel;
		
		
architecture rtl of NIAG_Rel is

		--internal signed displacement
		signal disp : signed(31 downto 0);
		
begin

    -- =====================================================
    -- TODO:
    -- Build the displacement from the immediate field.
    --
    -- If Xshft = '1':
    --     shift the signed immediate left by 2 bits
    --
    -- If Xshft = '0':
    --     use the signed immediate directly
    --
    -- Complete the assignment below.
    -- =====================================================

	disp <= shift_left(signed(Immed),2) when Xshft = '1' else signed(Immed);
	 
	 
    -- =====================================================
    -- TODO:
    -- Compute the relative address.
    --
    -- Steps:
    -- 1. Convert NSA to SIGNED
    -- 2. Add the signed displacement
    -- 3. Convert the result back to STD_LOGIC_VECTOR
    --
    -- Complete the assignment below.
    -- =====================================================
	RelAdrs <= STD_LOGIC_VECTOR(signed(NSA) + disp);
	
end rtl;
	 
	 