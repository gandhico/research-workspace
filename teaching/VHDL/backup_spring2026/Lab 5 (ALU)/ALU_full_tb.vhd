library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.ALU_Pkg.ALL;

entity ALU_tb is
--  Testbench has no ports
end ALU_tb;

architecture Behavioral of ALU_tb is

    -- Signals for ALU
    signal Ain, Bin : STD_LOGIC_VECTOR(31 downto 0) := (others => '0');
    signal Func     : STD_LOGIC_VECTOR(4 downto 0) := (others => '0');
    signal Shft     : STD_LOGIC_VECTOR(4 downto 0) := (others => '0');
    signal Rout     : STD_LOGIC_VECTOR(31 downto 0);
    signal Stat     : STAT_SIGNL_REC;

begin

    -- Instantiate the ALU
    uut: entity work.ALU
        port map(
            Ain  => Ain,
            Bin  => Bin,
            Func => Func,
            Shft => Shft,
            Rout => Rout,
            Stat => Stat
        );

    -- Stimulus process
    stim_proc: process
    begin

        report "---- Starting ALU Testbench ----";

        -- Test ADD
        Ain <= x"00000005"; Bin <= x"00000003"; Func <= ALU_FUNC_ADD;
        wait for 20 ns;
        report "ADD result: " & integer'image(to_integer(signed(Rout))) & 
               " Zero: " & std_logic'image(Stat.ALU_zero) & 
               " Sign: " & std_logic'image(Stat.ALU_sign);

        -- Test SUB
        Ain <= x"00000005"; Bin <= x"00000007"; Func <= ALU_FUNC_SUB;
        wait for 20 ns;
        report "SUB result: " & integer'image(to_integer(signed(Rout))) &
               " Zero: " & std_logic'image(Stat.ALU_zero) &
               " Sign: " & std_logic'image(Stat.ALU_sign);

        -- Test MULS
        Ain <= x"00000004"; Bin <= x"FFFFFFFE"; Func <= ALU_FUNC_MULS;
        wait for 20 ns;
        report "MULS result: " & integer'image(to_integer(signed(Rout)));

        -- Test MULU
        Ain <= x"00000004"; Bin <= x"00000003"; Func <= ALU_FUNC_MULU;
        wait for 20 ns;
        report "MULU result: " & integer'image(to_integer(unsigned(Rout)));

        -- Test DIVS
        Ain <= x"0000000A"; Bin <= x"00000003"; Func <= ALU_FUNC_DIVS;
        wait for 20 ns;
        report "DIVS quotient: " & integer'image(to_integer(signed(Rout)));

        -- Test DIVU
        Ain <= x"0000000A"; Bin <= x"00000003"; Func <= ALU_FUNC_DIVU;
        wait for 20 ns;
        report "DIVU quotient: " & integer'image(to_integer(unsigned(Rout)));

        -- Test NEG
        Bin <= x"00000007"; Func <= ALU_FUNC_NEG;
        wait for 20 ns;
        report "NEG result: " & integer'image(to_integer(signed(Rout)));

        -- Test SLA
        Ain <= x"00000003"; Shft <= "00010"; Func <= ALU_FUNC_SLA;
        wait for 20 ns;
        report "SLA result: " & integer'image(to_integer(signed(Rout)));

        -- Test SRA
        Ain <= x"FFFFFFF8"; Shft <= "00001"; Func <= ALU_FUNC_SRA;
        wait for 20 ns;
        report "SRA result: " & integer'image(to_integer(signed(Rout)));

        -- Test SOLS
        Ain <= x"00000005"; Bin <= x"00000007"; Func <= ALU_FUNC_SOLS;
        wait for 20 ns;
        report "SOLS result: " & integer'image(to_integer(unsigned(Rout)));

        -- Test SOLU
        Ain <= x"00000005"; Bin <= x"00000007"; Func <= ALU_FUNC_SOLU;
        wait for 20 ns;
        report "SOLU result: " & integer'image(to_integer(unsigned(Rout)));

        -- Test AND
        Ain <= x"F0F0F0F0"; Bin <= x"0F0F0F0F"; Func <= ALU_FUNC_AND;
        wait for 20 ns;
        report "AND test completed. Check waveform for result.";

        -- Test NAND
        Func <= ALU_FUNC_NAND;
        wait for 20 ns;
        report "NAND test completed. Check waveform for result.";

        -- Test OR
        Func <= ALU_FUNC_OR;
        wait for 20 ns;
        report "OR test completed. Check waveform for result.";

        -- Test NOR
        Func <= ALU_FUNC_NOR;
        wait for 20 ns;
        report "NOR test completed. Check waveform for result.";

        -- Test XOR
        Func <= ALU_FUNC_XOR;
        wait for 20 ns;
        report "XOR test completed. Check waveform for result.";

        -- Test XNOR
        Func <= ALU_FUNC_XNOR;
        wait for 20 ns;
        report "XNOR test completed. Check waveform for result.";

        -- Test NOT
        Bin <= x"0F0F0F0F"; Func <= ALU_FUNC_NOT;
        wait for 20 ns;
        report "NOT test completed. Check waveform for result.";

        -- Test SLL
        Ain <= x"00000001"; Shft <= "00011"; Func <= ALU_FUNC_SLL;
        wait for 20 ns;
        report "SLL result: " & integer'image(to_integer(unsigned(Rout)));

        -- Test SRL
        Func <= ALU_FUNC_SRL;
        wait for 20 ns;
        report "SRL result: " & integer'image(to_integer(unsigned(Rout)));

        -- Test HI/LO write & read
        Bin <= x"12345678"; Func <= ALU_FUNC_WRHI; wait for 20 ns;
        Func <= ALU_FUNC_RDHI; wait for 20 ns;
        report "HI read completed.";

        Bin <= x"87654321"; Func <= ALU_FUNC_WRLO; wait for 20 ns;
        Func <= ALU_FUNC_RDLO; wait for 20 ns;
        report "LO read completed.";

        report "---- ALU Testbench Completed ----";
        wait;
    end process;

end Behavioral;