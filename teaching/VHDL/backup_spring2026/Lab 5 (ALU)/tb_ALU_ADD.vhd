library IEEE;                          -- Import the IEEE library
use IEEE.STD_LOGIC_1164.ALL;          -- Import standard logic definitions
use IEEE.NUMERIC_STD.ALL;             -- Import numeric operations for signed/unsigned values

use work.ALU_Pkg.all;                 -- Import all definitions from the custom ALU package

entity tb_ALU_ADD is                  -- Define the testbench entity
end tb_ALU_ADD;                       -- A testbench has no ports, so the entity ends here

architecture sim of tb_ALU_ADD is     -- Begin simulation architecture
    signal A       : STD_LOGIC_VECTOR(31 downto 0); -- Signal to drive operand A
    signal B       : STD_LOGIC_VECTOR(31 downto 0); -- Signal to drive operand B
    signal FuncSel : STD_LOGIC_VECTOR(4 downto 0);  -- Signal to select the ALU function
    signal Shift   : STD_LOGIC_VECTOR(4 downto 0);  -- Signal for shift control input
    signal Result  : STD_LOGIC_VECTOR(31 downto 0); -- Signal to capture ALU result
    signal S       : STD_LOGIC;                     -- Signal to capture sign flag
    signal Z       : STD_LOGIC;                     -- Signal to capture zero flag
begin                                  -- Begin architecture body

    UUT: entity work.ALU_ADD           -- Instantiate the Unit Under Test (UUT)
        port map(                      -- Map testbench signals to the ALU ports
            A       => A,              -- Connect testbench signal A to ALU input A
            B       => B,              -- Connect testbench signal B to ALU input B
            FuncSel => FuncSel,        -- Connect function select signal
            Shift   => Shift,          -- Connect shift signal
            Result  => Result,         -- Connect ALU result output
            S       => S,              -- Connect sign flag output
            Z       => Z               -- Connect zero flag output
        );                             -- End port mapping

    process                            -- Begin stimulus process
    begin                              -- Begin process body
        Shift <= (others => '0');      -- Set Shift input to all zeros
        FuncSel <= ALU_FUNC_ADD;       -- Select the ADD operation in the ALU

        -- Test 1: 1 + 2 = 3
        A <= x"00000001";              -- Apply value 1 to input A
        B <= x"00000002";              -- Apply value 2 to input B
        wait for 10 ns;                -- Wait 10 ns for the result to propagate
        assert (Result = x"00000003" and S = '0' and Z = '0') -- Check expected result and flags
            report "FAIL: ADD test 1"  -- Error message if assertion fails
            severity error;            -- Mark failure as an error

        -- Test 2: -1 + 1 = 0
        A <= x"FFFFFFFF";              -- Apply -1 to input A in two's complement
        B <= x"00000001";              -- Apply 1 to input B
        wait for 10 ns;                -- Wait for the ALU to compute
        assert (Result = x"00000000" and S = '0' and Z = '1') -- Check result is zero and Z flag is set
            report "FAIL: ADD test 2"  -- Error message if assertion fails
            severity error;            -- Mark failure as an error

        -- Test 3: -1 + -2 = -3
        A <= x"FFFFFFFF";              -- Apply -1 to input A
        B <= x"FFFFFFFE";              -- Apply -2 to input B
        wait for 10 ns;                -- Wait for the result
        assert (Result = x"FFFFFFFD" and S = '1' and Z = '0') -- Check result is -3 and sign flag is set
            report "FAIL: ADD test 3"  -- Error message if assertion fails
            severity error;            -- Mark failure as an error

        -- Test 4: 7FFFFFFF + 1 = 80000000
        A <= x"7FFFFFFF";              -- Apply the largest positive 32-bit signed value
        B <= x"00000001";              -- Apply 1 to input B
        wait for 10 ns;                -- Wait for the ALU to compute
        assert (Result = x"80000000" and S = '1' and Z = '0') -- Check result and sign flag
            report "FAIL: ADD test 4"  -- Error message if assertion fails
            severity error;            -- Mark failure as an error

        report "ALU_ADD testbench completed successfully." severity note; -- Report success if all tests pass
        wait;                           -- Stop the process and wait forever
    end process;                       -- End stimulus process

end sim;                               -- End simulation architecture