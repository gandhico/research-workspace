--------------------------------------------------------------------------------
-- EE 362 - Lab 7, Example 1 - Testbench for the program counter
--
-- Watch PC and NSA together in the waveform. NSA is always PC+4, available
-- immediately, with no clock delay. That simultaneity is the point: the CPU
-- must know where it is AND where it would go next, within one cycle.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity pc_counter_tb is
end entity pc_counter_tb;

architecture test of pc_counter_tb is

    constant PERIOD : time := 20 ns;

    signal NextPC : std_logic_vector(7 downto 0) := (others => '0');
    signal Ld, Rst, clk : std_logic := '0';
    signal PC, NSA : std_logic_vector(7 downto 0);
    signal running : boolean := true;

begin

    DUT : entity work.pc_counter
        port map (NextPC => NextPC, Ld => Ld, Rst => Rst, clk => clk,
                  PC => PC, NSA => NSA);

    clock_gen : process
    begin
        while running loop
            clk <= '0'; wait for PERIOD / 2;
            clk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    stimulus : process

        variable errors : natural := 0;

        procedure check (wpc, wnsa : in std_logic_vector(7 downto 0);
                         msg : in string) is
        begin
            if PC /= wpc then
                report "FAIL (PC): " & msg severity error;
                errors := errors + 1;
            end if;
            if NSA /= wnsa then
                report "FAIL (NSA): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Reset: the PC must go somewhere DEFINED
        Rst <= '1'; wait for 3 ns;
        check(x"00", x"04", "1. reset vector is 0, NSA already shows 4");
        Rst <= '0';

        -- Sequential execution: feed NSA back into NextPC. Three instructions.
        Ld <= '1';
        wait until falling_edge(clk); NextPC <= NSA;
        wait until rising_edge(clk); wait for 1 ns;
        check(x"04", x"08", "2. advanced to 0x04");

        wait until falling_edge(clk); NextPC <= NSA;
        wait until rising_edge(clk); wait for 1 ns;
        check(x"08", x"0C", "3. advanced to 0x08");

        wait until falling_edge(clk); NextPC <= NSA;
        wait until rising_edge(clk); wait for 1 ns;
        check(x"0C", x"10", "4. advanced to 0x0C");

        -- A JUMP: load something that is not NSA. This is why the PC is a
        -- loadable register rather than a counter.
        wait until falling_edge(clk); NextPC <= x"40";
        wait until rising_edge(clk); wait for 1 ns;
        check(x"40", x"44", "5. jumped to 0x40 - not a count");

        -- Ld low: the edge arrives and the PC holds. A stalled processor.
        wait until falling_edge(clk); Ld <= '0'; NextPC <= x"FF";
        wait until rising_edge(clk); wait for 1 ns;
        check(x"40", x"44", "6. Ld low: PC holds, ignoring NextPC");

        -- Reset again, mid-stream and between edges, to prove it is async
        wait for 3 ns;
        Rst <= '1'; wait for 1 ns;
        check(x"00", x"04", "7. async reset returns to the reset vector");
        Rst <= '0';

        if errors = 0 then
            report "PASS - pc_counter: all checks passed." severity note;
        else
            report "FAILED - pc_counter: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
