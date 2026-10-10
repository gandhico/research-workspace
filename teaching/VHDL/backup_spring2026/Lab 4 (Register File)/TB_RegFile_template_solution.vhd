library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- Import EE362Decoder package
use work.DecodeLogic_Pkg.all;

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

    -- Instantiate the register file being tested
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

    -- Main stimulus process
    stimulus : process

        -- Local expected-value storage
        type data_array_t is array (0 to 31) of STD_LOGIC_VECTOR(31 downto 0);
        variable expected : data_array_t := (others => (others => '0'));

        -- Function: pattern
        function pattern(i : integer) return STD_LOGIC_VECTOR is
        begin
            return STD_LOGIC_VECTOR(to_unsigned(i * 16#01010101#, 32));
        end function;

        -- Procedure: write_reg
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

        -- ================================================================
        -- EXAMPLE TEST 1: Initial state
        -- ================================================================
        Asel <= RF_REG_00;
        Bsel <= RF_REG_00;
        wait for 5 ns;

        assert (Aout = x"00000000")
            report "Example Test 1 failed: R0 on Aout is not zero at startup"
            severity error;

        assert (Bout = x"00000000")
            report "Example Test 1 failed: R0 on Bout is not zero at startup"
            severity error;

        -- ================================================================
        -- EXAMPLE TEST 2: Write one register and read it back on Aout
        -- ================================================================
        expected(1) := x"11111111";
        write_reg(1, expected(1));

        Asel <= STD_LOGIC_VECTOR(to_unsigned(1, 5));
        wait for 5 ns;

        assert (Aout = expected(1))
            report "Example Test 2 failed: R1 write/read failed on Aout"
            severity error;

        -- ================================================================
        -- STUDENT TEST 1:
        -- Attempt to write register 0 and prove it remains zero
        -- ================================================================
        write_reg(0, x"DEADBEEF");
        expected(0) := x"00000000";

        Asel <= RF_REG_00;
        Bsel <= RF_REG_00;
        wait for 5 ns;

        assert (Aout = x"00000000")
            report "Student Test 1 failed: R0 changed on Aout"
            severity error;

        assert (Bout = x"00000000")
            report "Student Test 1 failed: R0 changed on Bout"
            severity error;

        -- ================================================================
        -- STUDENT TEST 2:
        -- Verify that Bout can read a written register correctly
        -- ================================================================
        expected(2) := x"22222222";
        write_reg(2, expected(2));

        Bsel <= STD_LOGIC_VECTOR(to_unsigned(2, 5));
        wait for 5 ns;

        assert (Bout = expected(2))
            report "Student Test 2 failed: R2 readback failed on Bout"
            severity error;

        -- ================================================================
        -- STUDENT TEST 3:
        -- Verify simultaneous reads on Aout and Bout
        -- ================================================================
        expected(3) := x"33333333";
        expected(4) := x"44444444";
        write_reg(3, expected(3));
        write_reg(4, expected(4));

        Asel <= STD_LOGIC_VECTOR(to_unsigned(3, 5));
        Bsel <= STD_LOGIC_VECTOR(to_unsigned(4, 5));
        wait for 5 ns;

        assert (Aout = expected(3))
            report "Student Test 3 failed: simultaneous read failed on Aout"
            severity error;

        assert (Bout = expected(4))
            report "Student Test 3 failed: simultaneous read failed on Bout"
            severity error;

        -- ================================================================
        -- STUDENT TEST 4:
        -- Verify writing one register does not disturb another register
        -- ================================================================
        expected(5) := x"55555555";
        expected(6) := x"66666666";
        write_reg(5, expected(5));
        write_reg(6, expected(6));

        -- Update only R5
        expected(5) := x"12345678";
        write_reg(5, expected(5));

        Asel <= STD_LOGIC_VECTOR(to_unsigned(5, 5));
        Bsel <= STD_LOGIC_VECTOR(to_unsigned(6, 5));
        wait for 5 ns;

        assert (Aout = expected(5))
            report "Student Test 4 failed: updated R5 value incorrect"
            severity error;

        assert (Bout = expected(6))
            report "Student Test 4 failed: R6 changed unexpectedly"
            severity error;

        -- ================================================================
        -- STUDENT TEST 5:
        -- Extra test: overwrite a register and verify the new value replaced
        -- the old one
        -- ================================================================
        expected(7) := x"AAAAAAAA";
        write_reg(7, expected(7));

        expected(7) := x"BBBBBBBB";
        write_reg(7, expected(7));

        Asel <= STD_LOGIC_VECTOR(to_unsigned(7, 5));
        Bsel <= STD_LOGIC_VECTOR(to_unsigned(7, 5));
        wait for 5 ns;

        assert (Aout = expected(7))
            report "Student Test 5 failed: overwrite check failed on Aout"
            severity error;

        assert (Bout = expected(7))
            report "Student Test 5 failed: overwrite check failed on Bout"
            severity error;

        -- ================================================================
        -- Optional final check: R0 must still be zero
        -- ================================================================
        Asel <= RF_REG_00;
        Bsel <= RF_REG_00;
        wait for 5 ns;

        assert (Aout = x"00000000")
            report "Final check failed: R0 is not zero on Aout"
            severity error;

        assert (Bout = x"00000000")
            report "Final check failed: R0 is not zero on Bout"
            severity error;

        report "TB_RegFile solution completed successfully." severity note;
        wait;
    end process;

end architecture sim;