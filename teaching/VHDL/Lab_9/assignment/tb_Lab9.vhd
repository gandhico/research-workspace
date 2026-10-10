--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 9 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- NOTE WHO DRIVES THE BUS. This testbench acts as the SECOND driver on MemBus -
-- exactly the role the register file's TriBuffer plays in the real CPU. It
-- drives during a write and releases to 'Z' at every other moment.
--
-- The 'wr' procedure performs one complete store: drive the bus, assert the
-- controls, let the falling edge commit it, then release.
--
-- REQUIRED, at least six checked vectors, including all of:
--
--   [required] read ALL SEVEN instructions of the program out of your ROM and
--              check them against the table in ROM.vhd, word by word
--   [required] a write then a read-back at the same address
--   [required] the bus at 'Z' with nothing enabled
--   [required] the bus at 'Z' while en='1' and rw='0' (write mode) - the RAM
--              must NOT drive during a write; the other side owns the bus
--   [required] a falling edge with Strb='0' - nothing may be written
--   [required] two adjacent word addresses that do not overlap
--
-- IN YOUR REPORT: disassemble all seven ROM words by hand against the
-- instruction formats, and state the endianness convention explicitly.
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
        -- *** REQUIRED *** The whole program, read out of the ROM.
        -- The first one fails until your ROM is built.
        ----------------------------------------------------------------------
        rom_chk(x"00000000", x"3C01000B", "0x00 LUI r1, 11");

        -- TODO: the remaining six instructions, at 0x04 through 0x18.
        --       Check each against the table in ROM.vhd.


        -- TODO: read past the end of the program - it should be zeros


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Bus discipline: nothing enabled -> 'Z'
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Write then read back.
        --   Store 0x00000400 at address 0 - that is 2^10, the value your CPU
        --   itself will store in Lab 12.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** The RAM must NOT drive the bus in write mode
        --   (en='1', rw='0'). During a store, the register file owns the bus.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** A falling edge with Strb='0' writes nothing
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Two adjacent word addresses do not overlap
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 9: all checks passed." severity note;
        else
            report "FAILED - Lab 9: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
