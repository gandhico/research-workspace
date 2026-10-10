--------------------------------------------------------------------------------
-- EE 362 - Lab 9, Example 3 - What the wrong byte order actually costs
--
-- Every vector here takes real bytes from the Lab 12 program and shows what
-- instruction each convention produces. Read the transcript, not just the
-- pass/fail line.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity endian_demo_tb is
end entity endian_demo_tb;

architecture test of endian_demo_tb is

    signal B0, B1, B2, B3 : std_logic_vector(7 downto 0) := (others => '0');
    signal BigEndian, LittleEndian : std_logic_vector(31 downto 0);

begin

    DUT : entity work.endian_demo
        port map (B0 => B0, B1 => B1, B2 => B2, B3 => B3,
                  BigEndian => BigEndian, LittleEndian => LittleEndian);

    stimulus : process

        variable errors : natural := 0;

        procedure chk (wb, wl : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if BigEndian /= wb then
                report "FAIL (big-endian): " & msg severity error;
                errors := errors + 1;
            end if;
            if LittleEndian /= wl then
                report "FAIL (little-endian): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

    begin

        ----------------------------------------------------------------------
        -- The ADDI at 0x08 - the loop counter decrement
        ----------------------------------------------------------------------
        B0 <= x"20"; B1 <= x"21"; B2 <= x"FF"; B3 <= x"FF"; wait for 10 ns;
        chk(x"2021FFFF", x"FFFF2120", "1. bytes 20 21 FF FF");
        report "  big-endian    0x2021FFFF -> opcode 001000 = ADDI r1,r1,-1  (correct)"
            severity note;
        report "  little-endian 0xFFFF2120 -> opcode 111111 = not an instruction"
            severity note;
        report "  Consequence: the counter never decrements and the loop never ends."
            severity note;

        ----------------------------------------------------------------------
        -- The J at 0x14 - the jump that closes the loop
        ----------------------------------------------------------------------
        B0 <= x"08"; B1 <= x"00"; B2 <= x"00"; B3 <= x"02"; wait for 10 ns;
        chk(x"08000002", x"02000008", "2. bytes 08 00 00 02");
        report "  big-endian    0x08000002 -> opcode 000010 = J 0x08  (correct)"
            severity note;
        report "  little-endian 0x02000008 -> opcode 000000 = SPECIAL, func 001000"
            severity note;
        report "  ...which is JR - a jump to whatever happens to be in a register."
            severity note;

        ----------------------------------------------------------------------
        -- A symmetric value, where the two conventions AGREE.
        -- Worth seeing: a test that cannot detect the bug.
        ----------------------------------------------------------------------
        B0 <= x"AA"; B1 <= x"BB"; B2 <= x"BB"; B3 <= x"AA"; wait for 10 ns;
        chk(x"AABBBBAA", x"AABBBBAA",
            "3. a palindromic word - both conventions agree, proves nothing");

        report "Vector 3 is a warning about test data: a symmetric value cannot" &
               " detect a byte-order error. Same rule as Lab 4 - test where the" &
               " implementations disagree." severity note;

        if errors = 0 then
            report "PASS - endian_demo: the two conventions produce different programs."
                severity note;
        else
            report "FAILED - endian_demo: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
