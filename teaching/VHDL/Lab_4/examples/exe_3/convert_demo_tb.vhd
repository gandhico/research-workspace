--------------------------------------------------------------------------------
-- EE 362 - Lab 4, Example 3 - Testbench for the conversion chain
--
-- Nothing subtle here. The value is in seeing the chain work, and in seeing
-- that an out-of-range index would be a runtime error rather than a wrong
-- answer - which is why 'amount' is declared as a constrained natural.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity convert_demo_tb is
end entity convert_demo_tb;

architecture test of convert_demo_tb is

    signal Data  : std_logic_vector(7 downto 0) := (others => '0');
    signal Shamt : std_logic_vector(2 downto 0) := (others => '0');
    signal Bit0  : std_logic;
    signal Shift : std_logic_vector(7 downto 0);

begin

    DUT : entity work.convert_demo
        port map (Data => Data, Shamt => Shamt, Bit0 => Bit0, Shift => Shift);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wb : in std_logic;
                         ws : in std_logic_vector(7 downto 0);
                         msg : in string) is
        begin
            if Bit0 /= wb then
                report "FAIL (indexed bit): " & msg severity error;
                errors := errors + 1;
            end if;
            if Shift /= ws then
                report "FAIL (shift): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Data = 1000_0001. Bit 0 is '1', bit 7 is '1', everything else '0'.
        Data <= "10000001";

        Shamt <= "000"; wait for 10 ns;
        check('1', "10000001", "1. shift 0: bit 0 selected, no shift");

        Shamt <= "001"; wait for 10 ns;
        check('0', "00000010", "2. shift 1: bit 1 selected, shifted left once");

        Shamt <= "111"; wait for 10 ns;
        check('1', "10000000", "3. shift 7: bit 7 selected, shifted left seven");

        -- A pattern where the shifted-out bits obviously vanish
        Data <= "11110000"; Shamt <= "100"; wait for 10 ns;
        check('1', "00000000", "4. shifting left discards the high bits");

        if errors = 0 then
            report "PASS - conversion chain works: bits -> number -> index."
                severity note;
        else
            report "FAILED - " & integer'image(errors) & " check(s) failed."
                severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
