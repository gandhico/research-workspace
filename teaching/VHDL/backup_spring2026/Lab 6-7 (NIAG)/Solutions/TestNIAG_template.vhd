library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.ALU_Pkg.all;
use work.LabCPU_Pkg.all;
use work.DecodeLogic_Pkg.all;
use work.NIAG_Pkg.all;

-- =========================================================
-- TestNIAG
-- Testbench for the complete NIAG unit
--
-- Purpose:
-- This testbench applies different input combinations to the
-- NIAG block and checks whether the generated addresses are
-- correct.
--
-- Main idea:
-- We test the main NIAG cases:
--
--   1. Next Sequential Address (NSA)
--   2. Absolute Address (ABS)
--   3. Relative Address taken
--   4. Relative Address not taken
--   5. Register Address (REG)
--   6. Negative relative displacement
--   7. GTZ branch not taken
--   8. LEZ branch taken
--
-- Example:
-- If:
--   PCin = x"00400020"
--
-- Then the next sequential address should be:
--   x"00400024"
--
-- Since the instruction size is 4 bytes.
-- =========================================================

entity TestNIAG is
end TestNIAG;

architecture tb of TestNIAG is

    -- =====================================================
    -- Test signals connected to the NIAG inputs and outputs
    -- =====================================================
    signal Target  : STD_LOGIC_VECTOR(25 downto 0) := (others => '0');
    signal Immed   : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Reg     : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Xshft   : STD_LOGIC := '0';
    signal PCin    : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Cond    : STD_LOGIC_VECTOR(2 downto 0) := NIAG_COND_NONE;
    signal Sel     : STD_LOGIC_VECTOR(1 downto 0) := NIAG_SEL_NSA;

    -- ALU status flags used by branch decisions
    signal Stat    : STAT_SIGNL_REC := (ALU_zero => '0', ALU_sign => '0');

    -- Outputs from NIAG
    signal MemAdrs : STD_LOGIC_VECTOR(31 downto 0);
    signal RtnAdrs : STD_LOGIC_VECTOR(31 downto 0);

begin

    -- =====================================================
    -- DUT = Device Under Test
    -- Instantiate the complete NIAG block
    -- =====================================================
    DUT : entity work.NIAG
        port map (
            Target  => Target,
            Immed   => Immed,
            Reg     => Reg,
            Xshft   => Xshft,
            PCin    => PCin,
            Cond    => Cond,
            Sel     => Sel,
            Stat    => Stat,
            MemAdrs => MemAdrs,
            RtnAdrs => RtnAdrs
        );

    -- =====================================================
    -- Stimulus process:
    -- Applies test cases one after another
    -- =====================================================
    stim : process
    begin

        -- -------------------------------------------------
        -- Common initial values
        -- -------------------------------------------------
        PCin   <= x"00400020";
        Target <= "00000000010010001101000101"; -- 26-bit target field
        Reg    <= x"10010080";
        Immed  <= x"00000003";
        Xshft  <= '1';
        Stat   <= (ALU_zero => '0', ALU_sign => '0');

        -- -------------------------------------------------
        -- 1) Next Sequential Address
        --
        -- Expected:
        --   MemAdrs = PCin + 4 = x"00400024"
        --   RtnAdrs = PCin + 4 = x"00400024"
        -- -------------------------------------------------
        Sel  <= NIAG_SEL_NSA;
        Cond <= NIAG_COND_NONE;
        wait for 10 ns;

        assert MemAdrs = x"00400024"
            report "NSA case failed"
            severity error;

        assert RtnAdrs = x"00400024"
            report "Return address case failed"
            severity error;

        -- -------------------------------------------------
        -- 2) Absolute Address
        --
        -- Expected absolute jump address:
        --   {NSA(31:28), Target, "00"}
        -- -------------------------------------------------
        Sel <= NIAG_SEL_ABS;
        wait for 10 ns;

        assert MemAdrs = x"00448D14"
            report "ABS case failed"
            severity error;

        -- -------------------------------------------------
        -- 3) Relative Address taken
        --
        -- Condition: EQ
        -- Branch taken when ALU_zero = '1'
        -- Immed = 3, Xshft = '1' => displacement = 12
        -- Expected:
        --   RelAdrs = NSA + 12 = x"00400030"
        -- -------------------------------------------------
        Sel  <= NIAG_SEL_REL;
        Cond <= NIAG_COND_EQ;
        Stat <= (ALU_zero => '1', ALU_sign => '0');
        wait for 10 ns;

        assert MemAdrs = x"00400030"
            report "REL taken EQ case failed"
            severity error;

        -- -------------------------------------------------
        -- 4) Relative Address not taken
        --
        -- Condition: EQ
        -- Branch not taken when ALU_zero = '0'
        -- Expected fallback:
        --   MemAdrs = NSA = x"00400024"
        -- -------------------------------------------------
        Stat <= (ALU_zero => '0', ALU_sign => '0');
        wait for 10 ns;

        assert MemAdrs = x"00400024"
            report "REL not-taken EQ case failed"
            severity error;

        -- -------------------------------------------------
        -- 5) Register Address
        --
        -- Expected:
        --   MemAdrs = Reg
        -- -------------------------------------------------
        Sel <= NIAG_SEL_REG;
        wait for 10 ns;

        assert MemAdrs = x"10010080"
            report "REG case failed"
            severity error;

        -- -------------------------------------------------
        -- 6) Negative relative displacement without shift
        --
        -- Immed = x"FFFFFFFC" = -4
        -- Xshft = '0' => use displacement directly
        -- Unconditional relative branch
        --
        -- Expected:
        --   RelAdrs = NSA + (-4) = x"00400020"
        -- -------------------------------------------------
        Immed <= x"FFFFFFFC";
        Xshft <= '0';
        Sel   <= NIAG_SEL_REL;
        Cond  <= NIAG_COND_NONE;
        wait for 10 ns;

        assert MemAdrs = x"00400020"
            report "REL negative displacement case failed"
            severity error;

        -- -------------------------------------------------
        -- 7) GTZ not taken
        --
        -- GTZ means greater than zero
        -- If sign = '1', result is negative, so branch is not taken
        --
        -- Expected fallback:
        --   MemAdrs = NSA = x"00400024"
        -- -------------------------------------------------
        Immed <= x"00000002";
        Xshft <= '1';
        Cond  <= NIAG_COND_GTZ;
        Stat  <= (ALU_zero => '0', ALU_sign => '1');
        wait for 10 ns;

        assert MemAdrs = x"00400024"
            report "GTZ not-taken case failed"
            severity error;

        -- -------------------------------------------------
        -- 8) LEZ taken
        --
        -- LEZ means less than or equal to zero
        -- If zero = '1', branch is taken
        --
        -- Immed = 2, Xshft = '1' => displacement = 8
        -- Expected:
        --   RelAdrs = NSA + 8 = x"0040002C"
        -- -------------------------------------------------
        Cond  <= NIAG_COND_LEZ;
        Stat  <= (ALU_zero => '1', ALU_sign => '0');
        wait for 10 ns;

        assert MemAdrs = x"0040002C"
            report "LEZ taken case failed"
            severity error;

        -- -------------------------------------------------
        -- Final message if all tests pass
        -- -------------------------------------------------
        report "All NIAG tests with official packages passed."
            severity note;

        wait;
    end process;

end tb;