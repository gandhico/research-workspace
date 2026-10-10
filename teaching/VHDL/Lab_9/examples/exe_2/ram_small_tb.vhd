--------------------------------------------------------------------------------
-- EE 362 - Lab 9, Example 2 - Driving a shared bus
--
-- The testbench itself is the OTHER driver. It drives the bus during a write
-- and releases it to 'Z' at every other moment - which is exactly what the
-- register file's TriBuffer does in the real CPU.
--
-- Watch the Data bus in the waveform. It should be:
--     'Z' when nothing is enabled
--     driven by the RAM during a read
--     driven by the TESTBENCH during a write
-- and never driven by both at once.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity ram_small_tb is
end entity ram_small_tb;

architecture test of ram_small_tb is

    constant PERIOD : time := 20 ns;

    signal Addr : std_logic_vector(31 downto 0) := (others => '0');
    signal Strb, rw, en : std_logic := '0';
    signal clk : std_logic := '0';
    signal Data : std_logic_vector(31 downto 0);

    -- What the testbench puts on the bus when IT is the driver.
    signal tb_drive : std_logic_vector(31 downto 0) := (others => 'Z');

    signal running : boolean := true;

begin

    -- The testbench is the second driver on the shared bus.
    Data <= tb_drive;

    DUT : entity work.ram_small
        port map (Addr => Addr, Strb => Strb, rw => rw, en => en,
                  clk => clk, Data => Data);

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

        procedure chk (want : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if Data /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

        -- Write one word: the testbench drives the bus, the RAM stores it on
        -- the falling edge. Exactly what the CPU does with SW.
        procedure wr (a : in std_logic_vector(31 downto 0);
                      d : in std_logic_vector(31 downto 0)) is
        begin
            wait until rising_edge(clk);
            Addr <= a; en <= '1'; rw <= '0'; Strb <= '1';
            tb_drive <= d;                       -- we drive
            wait until falling_edge(clk);
            wait for 1 ns;
            en <= '0'; Strb <= '0';
            tb_drive <= (others => 'Z');         -- and release
            wait for 1 ns;
        end procedure wr;

    begin

        -- 1. Nothing enabled: the bus floats.
        en <= '0'; wait for 10 ns;
        chk((31 downto 0 => 'Z'), "1. nothing enabled - the bus floats at Z");

        -- 2. Write, then read back
        wr(x"00000000", x"DEADBEEF");
        Addr <= x"00000000"; en <= '1'; rw <= '1'; wait for 5 ns;
        chk(x"DEADBEEF", "2. wrote 0xDEADBEEF at 0, read it back");

        -- 3. A second address, and the first is undisturbed
        en <= '0'; wait for 2 ns;
        wr(x"00000004", x"12345678");
        Addr <= x"00000004"; en <= '1'; rw <= '1'; wait for 5 ns;
        chk(x"12345678", "3. second word stored");
        Addr <= x"00000000"; wait for 5 ns;
        chk(x"DEADBEEF", "4. the first word is undisturbed");

        -- 5. en low while reading: the RAM must RELEASE the bus, not drive 0
        en <= '0'; wait for 5 ns;
        chk((31 downto 0 => 'Z'), "5. en low - RAM releases the bus to Z");

        -- 6. Enabled but rw = '0' (write mode) with no strobe: the RAM must not
        --    drive either, because the other side owns the bus during a write.
        en <= '1'; rw <= '0'; Strb <= '0'; wait for 5 ns;
        chk((31 downto 0 => 'Z'), "6. write mode - RAM does not drive the bus");

        -- 7. Strb low at a falling edge: nothing is written
        en <= '1'; rw <= '0'; Strb <= '0'; Addr <= x"00000000";
        tb_drive <= x"00000000";
        wait until falling_edge(clk); wait for 1 ns;
        tb_drive <= (others => 'Z'); en <= '1'; rw <= '1'; wait for 5 ns;
        chk(x"DEADBEEF", "7. falling edge with Strb low did not write");

        if errors = 0 then
            report "PASS - ram_small: bus discipline and storage both correct."
                severity note;
        else
            report "FAILED - ram_small: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
