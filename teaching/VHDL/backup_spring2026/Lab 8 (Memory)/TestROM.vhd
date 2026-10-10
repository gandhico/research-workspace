library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.Memory_Pkg.ALL;   -- Shared memory type definitions

-- =========================================================
-- TestROM
-- ---------------------------------------------------------
-- Testbench for the ROM module.
--
-- Purpose:
--   This testbench verifies that the ROM returns the expected
--   32-bit words for several addresses.
--
-- What is being tested:
--   1. Read from address 0x00
--   2. Read from address 0x04
--   3. Read from address 0x0C
--   4. Read from address 0x0E (partial read near programmed end)
--   5. Read from an out-of-range address (0x80)
--
-- Notes:
--   - ROM is combinational, so no clock is needed.
--   - Each read returns 4 consecutive bytes combined into one
--     32-bit word.
-- =========================================================
entity TestROM is
end TestROM;

architecture sim of TestROM is

    -- Address input applied to the ROM
    signal Addr : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');

    -- Data output produced by the ROM
    signal Data : STD_LOGIC_VECTOR(31 downto 0);

begin

    -- =========================================================
    -- Unit Under Test (UUT)
    -- ---------------------------------------------------------
    -- Instantiates the ROM and connects the address and data
    -- signals from the testbench.
    -- =========================================================
    UUT : ROM
        port map(
            Addr => Addr,
            Data => Data
        );

    -- =========================================================
    -- Stimulus process
    -- ---------------------------------------------------------
    -- Applies several addresses to the ROM and checks whether
    -- the returned 32-bit word matches the expected contents.
    -- =========================================================
    stim_proc : process
    begin

        -- -----------------------------------------------------
        -- Test 1: Read from address 0x00000000
        --
        -- ROM contents:
        --   Mem(0) = 0x45
        --   Mem(1) = 0x10
        --   Mem(2) = 0x87
        --   Mem(3) = 0x10
        --
        -- Expected 32-bit output:
        --   x"45108710"
        -- -----------------------------------------------------
        Addr <= x"00000000";
        wait for 10 ns;
        assert Data = x"45108710"
            report "FAIL: ROM[0x00] should return 0x45108710"
            severity error;

        -- -----------------------------------------------------
        -- Test 2: Read from address 0x00000004
        --
        -- ROM contents:
        --   Mem(4) = 0x98
        --   Mem(5) = 0x22
        --   Mem(6) = 0x47
        --   Mem(7) = 0x84
        --
        -- Expected 32-bit output:
        --   x"98224784"
        -- -----------------------------------------------------
        Addr <= x"00000004";
        wait for 10 ns;
        assert Data = x"98224784"
            report "FAIL: ROM[0x04] should return 0x98224784"
            severity error;

        -- -----------------------------------------------------
        -- Test 3: Read from address 0x0000000C
        --
        -- ROM contents:
        --   Mem(12) = 0x00
        --   Mem(13) = 0x00
        --   Mem(14) = 0xC5
        --   Mem(15) = 0x46
        --
        -- Expected 32-bit output:
        --   x"0000C546"
        -- -----------------------------------------------------
        Addr <= x"0000000C";
        wait for 10 ns;
        assert Data = x"0000C546"
            report "FAIL: ROM[0x0C] should return 0x0000C546"
            severity error;

        -- -----------------------------------------------------
        -- Test 4: Read from address 0x0000000E
        --
        -- ROM contents:
        --   Mem(14) = 0xC5
        --   Mem(15) = 0x46
        --   Mem(16) = 0x00   (default value)
        --   Mem(17) = 0x00   (default value)
        --
        -- Expected 32-bit output:
        --   x"C5460000"
        --
        -- This test is useful because it shows that the ROM still
        -- forms a 32-bit word from 4 consecutive bytes, even when
        -- some of the last bytes come from default-initialized
        -- memory locations.
        -- -----------------------------------------------------
        Addr <= x"0000000E";
        wait for 10 ns;
        assert Data = x"C5460000"
            report "FAIL: ROM[0x0E] should return 0xC5460000"
            severity error;

        -- -----------------------------------------------------
        -- Test 5: Read from address 0x00000080
        --
        -- Address 0x80 = 128 decimal, which is outside the valid
        -- ROM range (0 to 127).
        --
        -- Expected output:
        --   x"00000000"
        -- because addresses above 0x7F must be ignored.
        -- -----------------------------------------------------
        Addr <= x"00000080";
        wait for 10 ns;
        assert Data = x"00000000"
            report "FAIL: ROM addresses above 0x7F must be ignored"
            severity error;

        -- End of simulation
        wait;
    end process;

end sim;
