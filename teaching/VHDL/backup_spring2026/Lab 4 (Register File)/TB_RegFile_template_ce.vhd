library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Import EE362Decoder package
use work.DecodeLogic_Pkg.all;

-- ============================================================================
--  TB_RegFile_template
-- ----------------------------------------------------------------------------
--  Student template for the 32 x 32 tri-ported register file.
--
--  Provided:
--      1. Signal declarations
--      2. UUT instantiation
--      3. Helper function pattern()
--      4. Helper procedure write_reg()
--      5. Two example tests
--
--  Student work:
--      Complete the stimulus process by adding the required tests.
--
--  Required tests to implement:
--      1. Prove register 0 cannot be modified
--      2. Verify Bout can read a written register
--      3. Verify simultaneous reads on Aout and Bout
--      4. Verify writing one register does not disturb another
--      5. Add one extra test of your own
-- ============================================================================

entity TB_RegFile is
end entity TB_RegFile;

architecture sim of TB_RegFile is

    -- Signals connected to the Unit Under Test (UUT)
    signal Asel : STD_LOGIC_VECTOR(4 downto 0) := RF_REG_00;
    signal Bsel : STD_LOGIC_VECTOR(4 downto 0) := RF_REG_00;
    signal Dsel : STD_LOGIC_VECTOR(4 downto 0) := RF_REG_00;
    signal Din  : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Strb : STD_LOGIC := '0';
    signal Aout : STD_LOGIC_VECTOR(31 downto 0);
    signal Bout : STD_LOGIC_VECTOR(31 downto 0);

begin

    -- ------------------------------------------------------------------------
    -- Instantiate the register file being tested
    -- ------------------------------------------------------------------------
    UUT : entity work.RegFile
        port map(
            Asel => Asel,
            Bsel => Bsel,
            Dsel => Dsel,
            Din  => Din,
            Strb => Strb,
            Aout => Aout,
            Bout => Bout
        );

    -- ------------------------------------------------------------------------
    -- Main stimulus process
    -- ------------------------------------------------------------------------
    stimulus : process

        -- Local expected-value storage
        type data_array_t is array (0 to 31) of STD_LOGIC_VECTOR(31 downto 0);
        variable expected : data_array_t := (others => (others => '0'));

        -- --------------------------------------------------------------------
        -- Function: pattern
        -- Purpose :
        --      Generate a distinct 32-bit test value for each register number.
        -- --------------------------------------------------------------------
        function pattern(i : integer) return STD_LOGIC_VECTOR is
        begin
            return STD_LOGIC_VECTOR(to_unsigned(i * 16#01010101#, 32));
        end function;

        -- --------------------------------------------------------------------
        -- Procedure: write_reg
        -- Purpose  :
        --      Performs one register write transaction in the testbench.
        -- --------------------------------------------------------------------
        procedure write_reg(
            constant reg_num : in integer;
            constant value   : in STD_LOGIC_VECTOR(31 downto 0)
        ) is
        begin
            Dsel <= STD_LOGIC_VECTOR(to_unsigned(reg_num, 5));
            Din  <= value;
            wait for 5 ns;

            Strb <= '1';
            wait for 5 ns;

            Strb <= '0';
            wait for 5 ns;
        end procedure;

    begin
        -- Small startup delay
        wait for 10 ns;

        -- ====================================================================
        -- EXAMPLE TEST 1: Initial state
        -- Verify that register 0 starts at zero on both outputs.
        -- ====================================================================
        Asel <= RF_REG_00;
        Bsel <= RF_REG_00;
        wait for 5 ns;

        assert (Aout = x"00000000")
            report "Example Test 1 failed: R0 on Aout is not zero at startup"
            severity error;

        assert (Bout = x"00000000")
            report "Example Test 1 failed: R0 on Bout is not zero at startup"
            severity error;

        -- ====================================================================
        -- EXAMPLE TEST 2: Write one register and read it back on Aout
        -- ====================================================================
        expected(1) := x"11111111";
        write_reg(1, expected(1));

        Asel <= STD_LOGIC_VECTOR(to_unsigned(1, 5));
        wait for 5 ns;

        assert (Aout = expected(1))
            report "Example Test 2 failed: R1 write/read failed on Aout"
            severity error;

        -- ====================================================================
        -- STUDENT TEST 1:
        -- Attempt to write register 0 and prove it remains zero.
        --
        -- Suggested steps:
        --   1. Call write_reg(0, x\"DEADBEEF\")
        --   2. Select R0 on Aout and/or Bout
        --   3. Assert that the output is still x\"00000000\"
        -- ====================================================================

        -- TODO: write your code here



        -- ====================================================================
        -- STUDENT TEST 2:
        -- Verify that Bout can read a written register correctly.
        --
        -- Suggested steps:
        --   1. Write a value into some register, for example R2
        --   2. Select that register using Bsel
        --   3. Assert that Bout matches the expected value
        -- ====================================================================

        -- TODO: write your code here



        -- ====================================================================
        -- STUDENT TEST 3:
        -- Verify simultaneous reads:
        --   Aout reads one register while Bout reads another register.
        --
        -- Suggested steps:
        --   1. Write two different registers with two different values
        --   2. Put one register on Asel and the other on Bsel
        --   3. Assert Aout and Bout independently
        -- ====================================================================

        -- TODO: write your code here



        -- ====================================================================
        -- STUDENT TEST 4:
        -- Verify that writing one register does not disturb another register.
        --
        -- Suggested steps:
        --   1. Write a known value into R5
        --   2. Write a different value into R6
        --   3. Update only one of them
        --   4. Read both and prove the other one did not change
        -- ====================================================================

        -- TODO: write your code here



        -- ====================================================================
        -- STUDENT TEST 5:
        -- Add one extra test of your own.
        --
        -- Possible ideas:
        --   - Read the same register on both Aout and Bout
        --   - Overwrite a register and verify the new value replaced the old one
        --   - Change Din and Dsel without pulsing Strb and verify nothing changes
        --   - Explicitly test boundary registers like R1 and R31
        -- ====================================================================

        -- TODO: write your code here



        -- ====================================================================
        -- Final note
        -- If simulation reaches here without an error, the testbench passed.
        -- ====================================================================
        report "TB_RegFile_template completed successfully." severity note;
        wait;
    end process;

end architecture sim;