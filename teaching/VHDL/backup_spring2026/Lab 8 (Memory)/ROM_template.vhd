



-- =========================================================
-- ROM
-- ---------------------------------------------------------
-- Simple byte-addressable ROM for Lab 6.
--
-- Interface:
--   Addr : 32-bit address bus
--   Data : 32-bit output data bus
--
-- Behavior:
--   - ROM is read-only, so there is no clock, enable, or write control.
--   - For each address, the ROM returns a 32-bit word built from
--     4 consecutive bytes stored in memory.
--
-- Note:
--   Only the first 128 bytes (addresses 0 to 127) are valid.
--   Any undefined locations are initialized to x"00".
-- =========================================================




    -- Maximum valid address for this lab.
    -- ROM supports addresses from 0 to 127 only.

	 

    -- =========================================================
    -- ROM memory contents
    -- ---------------------------------------------------------
    -- Each location stores 1 byte.
    -- Only the listed addresses contain explicit instruction/data
    -- values; all remaining addresses default to x"00".
    -- =========================================================

	 
	 

    -- =========================================================
    -- ReadWord
    -- ---------------------------------------------------------
    -- Builds a 32-bit word from 4 consecutive ROM bytes:
    --   memory(base)     -> bits 31..24
    --   memory(base + 1) -> bits 23..16
    --   memory(base + 2) -> bits 15..8
    --   memory(base + 3) -> bits 7..0
    --
    -- If part of the requested word goes outside the valid range,
    -- the out-of-range bytes remain as 0.
    -- =========================================================

	 
	 

    -- =========================================================
    -- Read path
    -- ---------------------------------------------------------
    -- ROM output is purely combinational:
    -- whenever Addr changes, Data updates with the 32-bit word
    -- starting at that byte address.
    --
    -- Addr is converted from STD_LOGIC_VECTOR to integer so it
    -- can index the memory array.
    -- =========================================================

	 
