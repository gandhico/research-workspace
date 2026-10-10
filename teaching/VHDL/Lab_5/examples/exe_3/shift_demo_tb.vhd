--------------------------------------------------------------------------------
-- EE 362 - Lab 5, Example 3 - Testbench for the three shifts
--
-- Vectors 1 and 2 use a POSITIVE value. SRL and SRA agree there, and prove
-- nothing about which one you implemented.
--
-- Vectors 3, 4 and 5 use NEGATIVE values, where the two disagree. Those are
-- the only vectors that can catch an SRA written as an SRL.
--
-- Same rule as Lab 4: test where the implementations disagree.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity shift_demo_tb is
end entity shift_demo_tb;

architecture test of shift_demo_tb is

    signal Ain  : std_logic_vector(31 downto 0) := (others => '0');
    signal Shft : std_logic_vector(4 downto 0)  := (others => '0');
    signal Rsll, Rsrl, Rsra : std_logic_vector(31 downto 0);

begin

    DUT : entity work.shift_demo
        port map (Ain => Ain, Shft => Shft,
                  Rsll => Rsll, Rsrl => Rsrl, Rsra => Rsra);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wl, wr, wa : in std_logic_vector(31 downto 0);
                         msg : in string) is
        begin
            if Rsll /= wl then
                report "FAIL (SLL): " & msg severity error;
                errors := errors + 1;
            end if;
            if Rsrl /= wr then
                report "FAIL (SRL): " & msg severity error;
                errors := errors + 1;
            end if;
            if Rsra /= wa then
                report "FAIL (SRA): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- 1. Shift by zero: everything is unchanged. A useful sanity check,
        --    and a real case - the CPU issues shifts of zero.
        Ain <= x"0000000F"; Shft <= "00000"; wait for 10 ns;
        check(x"0000000F", x"0000000F", x"0000000F", "1. shift by 0 changes nothing");

        -- 2. POSITIVE value: SRL and SRA agree. Proves nothing about SRA.
        Ain <= x"0000000F"; Shft <= "00010"; wait for 10 ns;   -- 15 >> 2
        check(x"0000003C", x"00000003", x"00000003",
              "2. positive value: SRL and SRA agree - proves nothing");

        -- 3. NEGATIVE value. THE VECTOR THAT CATCHES THE BUG.
        --    -8 >> 1 should be -4. SRL would give +2147483644.
        Ain <= x"FFFFFFF8"; Shft <= "00001"; wait for 10 ns;   -- -8 >> 1
        check(x"FFFFFFF0", x"7FFFFFFC", x"FFFFFFFC",
              "3. -8 >> 1: SRA gives -4, SRL gives +2147483644");

        -- 4. -1 shifted right stays -1 under SRA, no matter how far.
        Ain <= x"FFFFFFFF"; Shft <= "11111"; wait for 10 ns;   -- -1 >> 31
        check(x"80000000", x"00000001", x"FFFFFFFF",
              "4. -1 >> 31: SRA is still -1, SRL is 1");

        -- 5. The most negative number, shifted right by one.
        Ain <= x"80000000"; Shft <= "00001"; wait for 10 ns;
        check(x"00000000", x"40000000", x"C0000000",
              "5. most negative >> 1: sign preserved by SRA");

        -- Confirm the arithmetic claim numerically, not just the bit pattern
        Ain <= x"FFFFFFF8"; Shft <= "00001"; wait for 10 ns;
        assert to_integer(signed(Rsra)) = -4
            report "SRA of -8 by 1 should be -4" severity error;

        if errors = 0 then
            report "PASS - shift_demo: SRA preserves the sign, SRL does not."
                severity note;
        else
            report "FAILED - shift_demo: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
