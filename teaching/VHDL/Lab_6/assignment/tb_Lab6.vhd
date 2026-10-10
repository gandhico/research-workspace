--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 6 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- The 'wr' procedure writes one register on the next rising edge, so a write
-- is one line. Use it.
--
-- REQUIRED, at least six checked vectors, and they must include all of:
--
--   [required] write a register, read it back on BOTH ports
--   [required] *** try to write register 0, then prove it still reads zero ***
--              This is the whole point of the lab. A register file without it
--              is just memory.
--   [required] a READ-DURING-WRITE case: address a register on a read port
--              while writing it on the same edge. Check the value BEFORE the
--              edge and AFTER it, and state in your report which behaviour
--              your design has (READ-OLD or READ-NEW).
--   [required] an edge with Strb = '0', proving nothing is written
--   [required] a read that changes with NO clock edge, proving reads are
--              combinational
--   [required] register 31, the boundary of the address range
--
-- The first vector below already fails, and it is meant to: nothing is written
-- yet. A testbench should be red until the design is right.
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

        -- Write one register on the next rising edge. One line per write.
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
        -- Write and read back. This one fails until you build the design.
        ----------------------------------------------------------------------
        wr("00101", x"DEADBEEF");                       -- write R5
        Asel <= "00101"; wait for 1 ns;
        checkA(x"DEADBEEF", "R5 written and read back on port A");

        -- TODO: read the same register on port B at the same time


        -- TODO: write a second register, then prove the first is undisturbed


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Register zero
        ----------------------------------------------------------------------
        -- TODO: try to write R0 with a non-zero value, then read it on both
        --       ports and prove it is still zero.
        --       Then re-read a normal register to prove nothing else broke.


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Read-during-write
        ----------------------------------------------------------------------
        -- TODO: set Asel to a register, and on the SAME falling edge set up a
        --       write to that same register. Check Aout BEFORE the rising edge
        --       and AFTER it.
        --       Then say in your report which behaviour you built.
        --
        --       Structure:
        --           wait until falling_edge(clk);
        --           Asel <= ...;  Dsel <= same;  Din <= new value; Strb <= '1';
        --           wait for 1 ns;
        --           checkA( <old or new?> , "before the edge");
        --           wait until rising_edge(clk); wait for 1 ns;
        --           checkA( ... , "after the edge");
        --           Strb <= '0';


        ----------------------------------------------------------------------
        -- TODO: an edge with Strb = '0' - nothing must be written
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: reads are combinational - change Asel with no clock edge
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- TODO: register 31, the top of the address range
        ----------------------------------------------------------------------


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 6: all checks passed." severity note;
        else
            report "FAILED - Lab 6: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
