--------------------------------------------------------------------------------
-- EE 362 - Lab 4, Example 2 - Testbench for the two extensions
--
-- The interesting inputs are the ones where the two answers DIFFER, which is
-- exactly the inputs whose top bit is '1'. An input like 0x3 proves nothing:
-- both extensions give 0x03.
--
-- That is a general rule for choosing test vectors, and it is worth stating
-- because it is the whole coverage argument here:
--
--     test where the implementations disagree, not where they agree
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity extend_demo_tb is
end entity extend_demo_tb;

architecture test of extend_demo_tb is

    signal I     : std_logic_vector(3 downto 0) := (others => '0');
    signal Yzero : std_logic_vector(7 downto 0);
    signal Ysign : std_logic_vector(7 downto 0);

begin

    DUT : entity work.extend_demo
        port map (I => I, Yzero => Yzero, Ysign => Ysign);

    stimulus : process

        variable errors : natural := 0;

        procedure check (wz, ws : in std_logic_vector(7 downto 0);
                         msg    : in string) is
        begin
            if Yzero /= wz then
                report "FAIL (zero-ext): " & msg severity error;
                errors := errors + 1;
            end if;
            if Ysign /= ws then
                report "FAIL (sign-ext): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure check;

    begin

        -- Top bit '0': the two agree. Proves the low bits pass through.
        I <= "0011"; wait for 10 ns;                    -- 3, and +3
        check(x"03", x"03", "1. I=0x3: both give 0x03, they agree");

        I <= "0111"; wait for 10 ns;                    -- 7, and +7
        check(x"07", x"07", "2. I=0x7: largest value where they still agree");

        -- Top bit '1': the two DISAGREE. These are the vectors that matter.
        I <= "1000"; wait for 10 ns;                    -- 8 unsigned, -8 signed
        check(x"08", x"F8", "3. I=0x8: 8 unsigned vs -8 signed");

        I <= "1111"; wait for 10 ns;                    -- 15 unsigned, -1 signed
        check(x"0F", x"FF", "4. I=0xF: 15 unsigned vs -1 signed");

        -- Confirm the numeric claim, not just the bit pattern.
        assert to_integer(unsigned(Yzero)) = 15
            report "0xF zero-extended should be 15 unsigned" severity error;
        assert to_integer(signed(Ysign)) = -1
            report "0xF sign-extended should be -1 signed" severity error;

        if errors = 0 then
            report "PASS - both extensions correct, and they differ where they should."
                severity note;
        else
            report "FAILED - " & integer'image(errors) & " check(s) failed."
                severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
