--------------------------------------------------------------------------------
-- EE 362 - Lab 6, Example 2 - Two read ports
--
-- The check that matters is the last one: both ports reading the SAME register
-- at the same time. Reading is not destructive and not exclusive, so it simply
-- works - but it is worth proving, because students who imagine registers as
-- something you "take" from expect a conflict.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity regfile_two_ports_tb is
end entity regfile_two_ports_tb;

architecture test of regfile_two_ports_tb is

    constant PERIOD : time := 20 ns;

    signal Asel, Bsel, Dsel : std_logic_vector(1 downto 0) := "00";
    signal Din, Aout, Bout  : std_logic_vector(7 downto 0) := (others => '0');
    signal Strb : std_logic := '0';
    signal clk  : std_logic := '0';
    signal running : boolean := true;

begin

    DUT : entity work.regfile_two_ports
        port map (Asel => Asel, Bsel => Bsel, Dsel => Dsel, Din => Din,
                  Strb => Strb, clk => clk, Aout => Aout, Bout => Bout);

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

        procedure check (wa, wb : in std_logic_vector(7 downto 0);
                         msg : in string) is
        begin
            if Aout /= wa then
                report "FAIL (port A): " & msg severity error;
                errors := errors + 1;
            end if;
            if Bout /= wb then
                report "FAIL (port B): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Load three registers with distinct values
        wait until falling_edge(clk);
        Dsel <= "01"; Din <= x"11"; Strb <= '1';
        wait until rising_edge(clk); wait for 1 ns;

        wait until falling_edge(clk);
        Dsel <= "10"; Din <= x"22";
        wait until rising_edge(clk); wait for 1 ns;

        wait until falling_edge(clk);
        Dsel <= "11"; Din <= x"33";
        wait until rising_edge(clk); wait for 1 ns;
        Strb <= '0';

        -- Two ports, two different registers, simultaneously
        Asel <= "01"; Bsel <= "10"; wait for 1 ns;
        check(x"11", x"22", "1. two ports read two different registers at once");

        Asel <= "11"; Bsel <= "01"; wait for 1 ns;
        check(x"33", x"11", "2. and again with different addresses");

        -- THE INTERESTING ONE: both ports on the SAME register.
        -- Reading is neither destructive nor exclusive.
        Asel <= "10"; Bsel <= "10"; wait for 1 ns;
        check(x"22", x"22", "3. both ports read the SAME register - no conflict");

        if errors = 0 then
            report "PASS - regfile_two_ports: reads are independent." severity note;
        else
            report "FAILED - regfile_two_ports: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
