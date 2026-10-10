--------------------------------------------------------------------------------
-- EE 362 - Lab 6, Example 3 - Register zero, and read-during-write
--
-- Vector 3 is the read-during-write case. It is the one to watch in the
-- waveform: the read port is addressing the register being written, on the
-- same edge, and it produces the OLD value.
--
-- That is not a bug. It is a documented design decision, and this testbench
-- ASSERTS it - which is the difference between a decision and an accident.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity read_during_write_tb is
end entity read_during_write_tb;

architecture test of read_during_write_tb is

    constant PERIOD : time := 20 ns;

    signal Asel, Dsel : std_logic_vector(1 downto 0) := "00";
    signal Din, Aout  : std_logic_vector(7 downto 0) := (others => '0');
    signal Strb : std_logic := '0';
    signal clk  : std_logic := '0';
    signal running : boolean := true;

begin

    DUT : entity work.read_during_write
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

        ------------------------------------------------------------------
        -- 1. Try to write register 0. The hardware must refuse.
        ------------------------------------------------------------------
        wait until falling_edge(clk);
        Dsel <= "00"; Din <= x"FF"; Strb <= '1';
        wait until rising_edge(clk); wait for 1 ns;
        Asel <= "00"; wait for 1 ns;
        check(x"00", "1. register 0 refuses to be written, still reads zero");

        ------------------------------------------------------------------
        -- 2. A normal register accepts the same data fine
        ------------------------------------------------------------------
        wait until falling_edge(clk);
        Dsel <= "01"; Din <= x"FF";
        wait until rising_edge(clk); wait for 1 ns;
        Asel <= "01"; wait for 1 ns;
        check(x"FF", "2. register 1 accepts the write");

        ------------------------------------------------------------------
        -- 3. READ-DURING-WRITE. Port A is addressing register 1 while
        --    register 1 is being written on this very edge.
        --    This design is READ-OLD: the port shows the value from before.
        ------------------------------------------------------------------
        wait until falling_edge(clk);
        Asel <= "01";                       -- reading reg 1
        Dsel <= "01"; Din <= x"42";         -- writing reg 1, same edge
        wait for 1 ns;

        -- THE CHECK THAT DEFINES THE BEHAVIOUR. The write data (0x42) is
        -- already sitting on Din, the write address already points at reg 1,
        -- and the edge has not happened yet. A READ-NEW (write-first) design
        -- would already be showing 0x42 here through a bypass path.
        -- This design shows the OLD value, because the read multiplexer looks
        -- at the register's stored output and nothing has been stored yet.
        check(x"FF", "3a. READ-OLD: before the edge, the port shows the old value");

        wait until rising_edge(clk);
        wait for 1 ns;
        check(x"42", "3b. after the edge the new value is visible");

        ------------------------------------------------------------------
        -- 4. Register 0 still reads zero even after other traffic
        ------------------------------------------------------------------
        Asel <= "00"; wait for 1 ns;
        check(x"00", "4. register 0 is still zero");

        ------------------------------------------------------------------
        -- 5. Writing register 0 with Strb high, again, mid-stream
        ------------------------------------------------------------------
        wait until falling_edge(clk);
        Dsel <= "00"; Din <= x"AB";
        wait until rising_edge(clk); wait for 1 ns;
        Asel <= "00"; wait for 1 ns;
        check(x"00", "5. register 0 refuses a second time");

        if errors = 0 then
            report "PASS - read_during_write: register 0 is hardwired, reads are READ-OLD."
                severity note;
        else
            report "FAILED - read_during_write: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
