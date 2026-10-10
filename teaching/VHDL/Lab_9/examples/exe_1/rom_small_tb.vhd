--------------------------------------------------------------------------------
-- EE 362 - Lab 9, Example 1 - Reading instructions out of a ROM
--
-- These are the first four instructions of the program your CPU runs in Lab 12.
-- Read them, then disassemble them by hand against the instruction formats -
-- that is the exercise, not the VHDL.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity rom_small_tb is
end entity rom_small_tb;

architecture test of rom_small_tb is

    signal Addr : std_logic_vector(31 downto 0) := (others => '0');
    signal Data : std_logic_vector(31 downto 0);

begin

    DUT : entity work.rom_small
        port map (Addr => Addr, Data => Data);

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

    begin

        Addr <= x"00000000"; wait for 10 ns;
        chk(x"3C01000B", "1. word at 0x00 = 3C01000B  (LUI r1, 0x000B)");

        Addr <= x"00000004"; wait for 10 ns;
        chk(x"3C020001", "2. word at 0x04 = 3C020001  (LUI r2, 0x0001)");

        Addr <= x"00000008"; wait for 10 ns;
        chk(x"2021FFFF", "3. word at 0x08 = 2021FFFF  (ADDI r1, r1, -1)");

        Addr <= x"0000000C"; wait for 10 ns;
        chk(x"18200002", "4. word at 0x0C = 18200002  (BLEZ r1, +2)");

        report "Notice: the byte at 0x00 is 0x3C and it lands in bits 31..24." &
               " Most significant byte at the lowest address - big-endian."
            severity note;

        report "Disassemble 0x2021FFFF by hand: opcode 001000 = ADDI," &
               " rs = 00001, rt = 00001, immediate = 0xFFFF = -1." severity note;

        if errors = 0 then
            report "PASS - rom_small: all four instructions read correctly."
                severity note;
        else
            report "FAILED - rom_small: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
