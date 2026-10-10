--------------------------------------------------------------------------------
-- EE 362 - Lab 6 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 18 checks. Both read ports, register 0 on both the write and read sides,
-- read-during-write in both directions, and the boundary register (31).
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab6 is
end entity tb_Lab6;

architecture test of tb_Lab6 is

    constant PERIOD : time := 20 ns;

    signal Asel, Bsel, Dsel : std_logic_vector(4 downto 0)  := (others => '0');
    signal Din, Aout, Bout  : std_logic_vector(31 downto 0) := (others => '0');
    signal Strb : std_logic := '0';
    signal clk  : std_logic := '0';
    signal running : boolean := true;

begin

    DUT : entity work.RegFile
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

        procedure checkA (want : in std_logic_vector(31 downto 0);
                          msg : in string) is
        begin
            if Aout /= want then
                report "FAIL (port A): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure checkA;

        procedure checkB (want : in std_logic_vector(31 downto 0);
                          msg : in string) is
        begin
            if Bout /= want then
                report "FAIL (port B): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure checkB;

        -- Write one register on the next rising edge.
        procedure wr (addr : in std_logic_vector(4 downto 0);
                      data : in std_logic_vector(31 downto 0)) is
        begin
            wait until falling_edge(clk);
            Dsel <= addr; Din <= data; Strb <= '1';
            wait until rising_edge(clk);
            wait for 1 ns;
            Strb <= '0';
        end procedure wr;

    begin

        ----------------------------------------------------------------------
        -- Basic write and read back, on both ports
        ----------------------------------------------------------------------
        wr("00101", x"DEADBEEF");                       -- R5
        Asel <= "00101"; Bsel <= "00101"; wait for 1 ns;
        checkA(x"DEADBEEF", "1. R5 read on port A");
        checkB(x"DEADBEEF", "2. R5 read on port B simultaneously");

        wr("01010", x"12345678");                       -- R10
        Asel <= "00101"; Bsel <= "01010"; wait for 1 ns;
        checkA(x"DEADBEEF", "3. R5 undisturbed by writing R10");
        checkB(x"12345678", "4. R10 holds its own value");

        ----------------------------------------------------------------------
        -- The boundary register
        ----------------------------------------------------------------------
        wr("11111", x"CAFEBABE");                       -- R31
        Asel <= "11111"; wait for 1 ns;
        checkA(x"CAFEBABE", "5. R31, the top register, works");

        ----------------------------------------------------------------------
        -- REGISTER ZERO - the point of the lab
        ----------------------------------------------------------------------
        wr("00000", x"FFFFFFFF");                       -- try to write R0
        Asel <= "00000"; Bsel <= "00000"; wait for 1 ns;
        checkA(x"00000000", "6. R0 refuses the write, port A reads zero");
        checkB(x"00000000", "7. R0 refuses the write, port B reads zero");

        -- ...and everything else is still intact
        Asel <= "00101"; Bsel <= "11111"; wait for 1 ns;
        checkA(x"DEADBEEF", "8. R5 survived the attempted R0 write");
        checkB(x"CAFEBABE", "9. R31 survived too");

        -- A second attempt, with different data
        wr("00000", x"00000001");
        Asel <= "00000"; wait for 1 ns;
        checkA(x"00000000", "10. R0 refuses again");

        ----------------------------------------------------------------------
        -- Strb low: the edge arrives, nothing is written
        ----------------------------------------------------------------------
        wait until falling_edge(clk);
        Dsel <= "00101"; Din <= x"00000000"; Strb <= '0';
        wait until rising_edge(clk); wait for 1 ns;
        Asel <= "00101"; wait for 1 ns;
        checkA(x"DEADBEEF", "11. edge with Strb low does not write");

        ----------------------------------------------------------------------
        -- Reads are COMBINATIONAL: change the address, no clock involved
        ----------------------------------------------------------------------
        Asel <= "01010"; wait for 1 ns;
        checkA(x"12345678", "12. read is combinational - address changed only");
        Asel <= "11111"; wait for 1 ns;
        checkA(x"CAFEBABE", "13. and again, still no clock edge");

        ----------------------------------------------------------------------
        -- READ-DURING-WRITE, documented behaviour: READ-OLD
        ----------------------------------------------------------------------
        wait until falling_edge(clk);
        Asel <= "00101";                    -- reading R5
        Dsel <= "00101"; Din <= x"AAAAAAAA"; Strb <= '1';   -- writing R5
        wait for 1 ns;
        checkA(x"DEADBEEF", "14. READ-OLD: before the edge, the old value");

        wait until rising_edge(clk); wait for 1 ns;
        Strb <= '0';
        checkA(x"AAAAAAAA", "15. after the edge, the new value");

        ----------------------------------------------------------------------
        -- Both ports on different registers, one of which is R0
        ----------------------------------------------------------------------
        Asel <= "00000"; Bsel <= "01010"; wait for 1 ns;
        checkA(x"00000000", "16. port A on R0 reads zero");
        checkB(x"12345678", "17. port B on R10 reads normally at the same time");

        ----------------------------------------------------------------------
        -- Writing R0's neighbour must not leak into R0
        ----------------------------------------------------------------------
        wr("00001", x"BADF00D5");
        Asel <= "00000"; wait for 1 ns;
        checkA(x"00000000", "18. writing R1 did not disturb R0");

        if errors = 0 then
            report "PASS - Lab 6: all 18 checks passed." severity note;
        else
            report "FAILED - Lab 6: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
