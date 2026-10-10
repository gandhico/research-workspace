--------------------------------------------------------------------------------
-- EE 362 - Lab 8, Example 3 - Testbench for the PC selection
--
-- The vectors that matter are 3 and 4: the SAME select code (REL) with Taken
-- high and low, giving two different next addresses. That pair is what makes
-- conditional execution exist.
--
-- Vectors 5 and 6 show the other side of it: Taken has NO effect when the
-- select code is not REL. A jump is unconditional by construction, and the
-- flags cannot change that.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity pc_select_tb is
end entity pc_select_tb;

architecture test of pc_select_tb is

    signal Sel   : std_logic_vector(1 downto 0) := NIAG_SEL_NSA;
    signal Taken : std_logic := '0';
    signal NSA     : std_logic_vector(31 downto 0) := x"00000010";
    signal Rel     : std_logic_vector(31 downto 0) := x"00000018";
    signal RegAddr : std_logic_vector(31 downto 0) := x"DEADBEE0";
    signal Abslt   : std_logic_vector(31 downto 0) := x"00000008";
    signal NextPC  : std_logic_vector(31 downto 0);

begin

    DUT : entity work.pc_select
        port map (Sel => Sel, Taken => Taken, NSA => NSA, Rel => Rel,
                  RegAddr => RegAddr, Abslt => Abslt, NextPC => NextPC);

    stimulus : process

        variable errors : natural := 0;

        procedure chk (want : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if NextPC /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

    begin

        -- 1 & 2: sequential. Taken is irrelevant.
        Sel <= NIAG_SEL_NSA; Taken <= '0'; wait for 10 ns;
        chk(x"00000010", "1. NSA selected, not taken");
        Taken <= '1'; wait for 10 ns;
        chk(x"00000010", "2. NSA selected, Taken has no effect here");

        -- 3 & 4: THE PAIR THAT MATTERS. Same select code, different Taken.
        Sel <= NIAG_SEL_REL; Taken <= '1'; wait for 10 ns;
        chk(x"00000018", "3. REL selected and TAKEN -> the branch target");
        Taken <= '0'; wait for 10 ns;
        chk(x"00000010", "4. REL selected, NOT taken -> falls back to NSA");

        -- 5 & 6: jumps are unconditional by construction.
        Sel <= NIAG_SEL_ABS; Taken <= '0'; wait for 10 ns;
        chk(x"00000008", "5. ABS selected while not taken - still jumps");
        Taken <= '1'; wait for 10 ns;
        chk(x"00000008", "6. ABS selected while taken - same answer");

        -- 7 & 8: register jump, also unconditional. Note it is a FULL 32-bit
        -- address, which is how JR reaches outside the 256 MB jump region.
        Sel <= NIAG_SEL_REG; Taken <= '0'; wait for 10 ns;
        chk(x"DEADBEE0", "7. REG selected -> full 32-bit address from a register");
        Taken <= '1'; wait for 10 ns;
        chk(x"DEADBEE0", "8. REG selected, Taken irrelevant");

        if errors = 0 then
            report "PASS - pc_select: only the relative path is conditional."
                severity note;
        else
            report "FAILED - pc_select: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
