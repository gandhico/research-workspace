




-- =========================================================
-- RAM
-- ---------------------------------------------------------
-- Simple byte-addressable RAM for Lab 6.
--
-- Interface:
--   Addr : 32-bit address bus
--   Strb : write strobe, confirms the write operation
--   rw   : read/write control
--          '1' = read
--          '0' = write
--   en   : memory enable
--   clk  : clock for synchronous writes
--   Data : bidirectional 32-bit data bus
--
-- Behavior:
--   - Read is combinational:
--       when en='1' and rw='1', RAM places a 32-bit word on Data
--   - Write is synchronous:
--       on rising_edge(clk), if en='1', rw='0', and Strb='1',
--       the 32-bit word on Data is stored into memory
--
-- Note:
--   Only the first 128 bytes (addresses 0 to 127) are valid.
-- =========================================================



---  Architecture 

    -- Maximum valid address for this lab.
    -- Since addresses go from 0 to 127, the RAM effectively supports 128 bytes.


    -- Internal memory array.
    -- Each position stores 1 byte (8 bits).
    -- It is initialized to 00 in every location.
 

    -- =========================================================
    -- ReadWord
    -- ---------------------------------------------------------
    -- Builds a 32-bit word from 4 consecutive memory bytes:
    --   memory(base)     -> bits 31..24
    --   memory(base + 1) -> bits 23..16
    --   memory(base + 2) -> bits 15..8
    --   memory(base + 3) -> bits 7..0
    --
    -- If part of the requested word goes outside the valid range,
    -- the out-of-range bytes remain as 0.
    -- =========================================================

	 
	 
	 
	 
	 
        -- Only attempt the read if the starting address is valid


            -- Load each byte only if that byte address is still inside the valid range

				
				
	

    -- =========================================================
    -- Read path
    -- ---------------------------------------------------------
    -- The RAM drives the Data bus only during a valid read cycle:
    --   en = '1'  -> memory enabled
    --   rw = '1'  -> read operation
    --
    -- Otherwise, the RAM disconnects from the bus by driving 'Z'
    -- (high impedance), allowing other devices to use the bus.
    -- =========================================================

	 
	 
	 

    -- =========================================================
    -- Write path
    -- ---------------------------------------------------------
    -- Writes are synchronous, so they happen only on the rising
    -- edge of the clock.
    --
    -- A write occurs only if:
    --   en   = '1'  -> memory enabled
    --   rw   = '0'  -> write operation selected
    --   Strb = '1'  -> write strobe asserted
    --
    -- The 32-bit Data bus is split into 4 bytes and stored in
    -- 4 consecutive memory addresses.
    -- =========================================================

	 
	 

            -- Convert the 32-bit address into an integer index


            -- Perform write only under valid write conditions
				
 
                -- Check that the starting address is inside the valid memory range
 

                    -- Store the 32-bit word as 4 consecutive bytes
                    -- Data(31:24) goes to the lowest address
                    -- Data(7:0)   goes to the highest address

						  
