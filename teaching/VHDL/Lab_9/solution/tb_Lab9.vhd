--------------------------------------------------------------------------------
-- EE 362 - Lab 9 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 19 checks. Reads all seven instructions of the real program out of the ROM,
-- exercises the full RAM bus discipline, and stores 0x400 at address 0 - the
-- value the CPU itself will store in Lab 12.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab9 is
end entity tb_Lab9;

architecture test of tb_Lab9 is

    constant PERIOD : time := 20 ns;

    -- ROM
    signal RomAddr : std_logic_vector(31 downto 0) := (others => '0');
    signal RomData : std_logic_vector(31 downto 0);

    -- RAM on a shared bus
    signal RamAddr : std_logic_vector(31 downto 0) := (others => '0');
    signal Strb, rw, en : std_logic := '0';
    signal clk : std_logic := '0';
    signal MemBus : std_logic_vector(31 downto 0);

    -- the testbench acts as the other driver (the register file's TriBuffer)
    signal tb_drive : std_logic_vector(31 downto 0) := (others => 'Z');

    signal running : boolean := true;

begin

    MemBus <= tb_drive;

    U_ROM : entity work.ROM
        port map (Addr => RomAddr, Data => RomData);

    U_RAM : entity work.RAM
        port map (Addr => RamAddr, Strb => Strb, rw => rw, en => en,
                  clk => clk, Data => MemBus);

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

        procedure rom_chk (a, want : in std_logic_vector(31 downto 0);
                           msg : in string) is
        begin
            RomAddr <= a;
            wait for 5 ns;
            if RomData /= want then
                report "FAIL (ROM): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure rom_chk;

        procedure bus_chk (want : in std_logic_vector(31 downto 0);
                           msg : in string) is
        begin
            if MemBus /= want then
                report "FAIL (bus): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure bus_chk;

        procedure wr (a, d : in std_logic_vector(31 downto 0)) is
        begin
            wait until rising_edge(clk);
            RamAddr <= a; en <= '1'; rw <= '0'; Strb <= '1';
            tb_drive <= d;
            wait until falling_edge(clk);
            wait for 1 ns;
            en <= '0'; Strb <= '0';
            tb_drive <= (others => 'Z');
            wait for 1 ns;
        end procedure wr;

    begin

        ----------------------------------------------------------------------
        -- The whole program, read out of the ROM
        ----------------------------------------------------------------------
        rom_chk(x"00000000", x"3C01000B", "1.  0x00 LUI  r1, 11");
        rom_chk(x"00000004", x"3C020001", "2.  0x04 LUI  r2, 1");
        rom_chk(x"00000008", x"2021FFFF", "3.  0x08 ADDI r1, r1, -1");
        rom_chk(x"0000000C", x"18200002", "4.  0x0C BLEZ r1, +2");
        rom_chk(x"00000010", x"00021040", "5.  0x10 SLL  r2, r2, 1");
        rom_chk(x"00000014", x"08000002", "6.  0x14 J    0x08");
        rom_chk(x"00000018", x"AC020000", "7.  0x18 SW   r2, 0(r0)");

        -- Past the program: zeros
        rom_chk(x"0000001C", x"00000000", "8.  past the program - zeros");

        -- The ROM is combinational: no clock has been involved at all so far.
        report "All eight ROM reads above happened with no clock edge." severity note;

        ----------------------------------------------------------------------
        -- RAM bus discipline
        ----------------------------------------------------------------------
        en <= '0'; wait for 5 ns;
        bus_chk((31 downto 0 => 'Z'), "9.  nothing enabled - bus floats");

        -- Store the value the CPU itself will store in Lab 12: 2^10 = 1024
        wr(x"00000000", x"00000400");
        RamAddr <= x"00000000"; en <= '1'; rw <= '1'; wait for 5 ns;
        bus_chk(x"00000400", "10. stored 0x400 at address 0 - the Lab 12 result");

        -- A second location
        en <= '0'; wait for 2 ns;
        wr(x"00000010", x"DEADBEEF");
        RamAddr <= x"00000010"; en <= '1'; rw <= '1'; wait for 5 ns;
        bus_chk(x"DEADBEEF", "11. second word stored");
        RamAddr <= x"00000000"; wait for 5 ns;
        bus_chk(x"00000400", "12. first word undisturbed");

        -- Release
        en <= '0'; wait for 5 ns;
        bus_chk((31 downto 0 => 'Z'), "13. en low - RAM releases the bus");

        -- Write mode with no strobe: the RAM must not drive either
        en <= '1'; rw <= '0'; Strb <= '0'; wait for 5 ns;
        bus_chk((31 downto 0 => 'Z'), "14. write mode - RAM does not drive");

        -- Falling edge with Strb low: nothing written
        RamAddr <= x"00000000"; tb_drive <= x"FFFFFFFF";
        wait until falling_edge(clk); wait for 1 ns;
        tb_drive <= (others => 'Z');
        en <= '1'; rw <= '1'; wait for 5 ns;
        bus_chk(x"00000400", "15. Strb low at the edge did not write");

        -- Write mode with en low: also nothing
        en <= '0'; wait for 2 ns;
        RamAddr <= x"00000000"; rw <= '0'; Strb <= '1'; tb_drive <= x"11111111";
        wait until falling_edge(clk); wait for 1 ns;
        tb_drive <= (others => 'Z');
        en <= '1'; rw <= '1'; Strb <= '0'; wait for 5 ns;
        bus_chk(x"00000400", "16. en low at the edge did not write");

        ----------------------------------------------------------------------
        -- Byte order: store a word, then confirm the bytes came back in the
        -- same order. A big-endian store followed by a big-endian load is
        -- self-consistent - which is the property that matters.
        ----------------------------------------------------------------------
        en <= '0'; wait for 2 ns;
        wr(x"00000020", x"12345678");
        RamAddr <= x"00000020"; en <= '1'; rw <= '1'; wait for 5 ns;
        bus_chk(x"12345678", "17. store then load is self-consistent");

        -- Adjacent addresses do not overlap: 0x20 and 0x24 are separate words
        en <= '0'; wait for 2 ns;
        wr(x"00000024", x"9ABCDEF0");
        RamAddr <= x"00000020"; en <= '1'; rw <= '1'; wait for 5 ns;
        bus_chk(x"12345678", "18. word at 0x20 undisturbed by writing 0x24");
        RamAddr <= x"00000024"; wait for 5 ns;
        bus_chk(x"9ABCDEF0", "19. word at 0x24 is its own");

        en <= '0';

        if errors = 0 then
            report "PASS - Lab 9: all 19 checks passed." severity note;
        else
            report "FAILED - Lab 9: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
