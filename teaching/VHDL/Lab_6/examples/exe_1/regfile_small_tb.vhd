--------------------------------------------------------------------------------
-- EE 362 - Lab 6, Example 1 - Testbench for the small register file
--
-- Watch the 'regs' signal in the waveform. Four bytes, and you can see every
-- one of them change. That is the reason this example is 4 x 8 and not 32 x 32.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity regfile_small_tb is
end entity regfile_small_tb;

architecture test of regfile_small_tb is

    constant PERIOD : time := 20 ns;

    signal Asel, Dsel : std_logic_vector(1 downto 0) := "00";
    signal Din, Aout  : std_logic_vector(7 downto 0) := (others => '0');
    signal Strb       : std_logic := '0';
    signal clk        : std_logic := '0';
    signal running    : boolean := true;

begin

    DUT : entity work.regfile_small
        port map (Asel => Asel, Dsel => Dsel, Din => Din,
                  Strb => Strb, clk => clk, Aout => Aout);

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

        procedure check (want : in std_logic_vector(7 downto 0);
                         msg  : in string) is
        begin
            if Aout /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Write 0xAA into register 1
        wait until falling_edge(clk);
        Dsel <= "01"; Din <= x"AA"; Strb <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;

        -- Read it back. Note: no clock needed - just change the address.
        Asel <= "01"; wait for 1 ns;
        check(x"AA", "1. wrote reg 1, read it back");

        -- Write a different value into register 2
        wait until falling_edge(clk);
        Dsel <= "10"; Din <= x"55";
        wait until rising_edge(clk);
        wait for 1 ns;

        -- Register 1 must be untouched. Writing one register must not disturb
        -- the others - obvious, and worth testing exactly once.
        Asel <= "01"; wait for 1 ns;
        check(x"AA", "2. writing reg 2 did not disturb reg 1");

        Asel <= "10"; wait for 1 ns;
        check(x"55", "3. reg 2 holds its own value");

        -- Reads are COMBINATIONAL: change the address, output follows with no
        -- clock edge at all. This is the vector that proves it.
        Asel <= "01"; wait for 1 ns;
        check(x"AA", "4. read is combinational - address changed, no clock");
        Asel <= "10"; wait for 1 ns;
        check(x"55", "5. and again, still no clock edge");

        -- Strb low: the edge arrives but nothing is written
        wait until falling_edge(clk);
        Dsel <= "10"; Din <= x"FF"; Strb <= '0';
        wait until rising_edge(clk);
        wait for 1 ns;
        Asel <= "10"; wait for 1 ns;
        check(x"55", "6. edge with Strb low does not write");

        if errors = 0 then
            report "PASS - regfile_small: all checks passed." severity note;
        else
            report "FAILED - regfile_small: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
