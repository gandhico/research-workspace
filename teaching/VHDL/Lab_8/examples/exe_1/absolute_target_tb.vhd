--------------------------------------------------------------------------------
-- EE 362 - Lab 8, Example 1 - Testbench for absolute target formation
--
-- The last two vectors are the interesting ones. They show a jump being UNABLE
-- to leave its 256 MB region: the same index gives different targets depending
-- on where you jumped FROM, because the top four bits are inherited.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity absolute_target_tb is
end entity absolute_target_tb;

architecture test of absolute_target_tb is

    signal NSA   : std_logic_vector(31 downto 0) := (others => '0');
    signal Index : std_logic_vector(25 downto 0) := (others => '0');
    signal Abslt : std_logic_vector(31 downto 0);

begin

    DUT : entity work.absolute_target
        port map (NSA => NSA, Index => Index, Abslt => Abslt);

    stimulus : process

        variable errors : natural := 0;

        procedure chk (want : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if Abslt /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

    begin

        -- THE REAL ONE. J 0x08000002 at address 0x14, so NSA = 0x18.
        --   top 4 bits of 0x18 are 0x0
        --   index 0x0000002, shifted left 2 -> 0x00000008
        NSA <= x"00000018"; Index <= "00" & x"000002"; wait for 10 ns;
        chk(x"00000008", "1. the real J: targets 0x08, the top of the loop");

        -- Index zero: jump to the base of the current region
        Index <= (others => '0'); wait for 10 ns;
        chk(x"00000000", "2. index 0 targets the region base");

        -- Index 1: one instruction along from the base
        Index <= "00" & x"000001"; wait for 10 ns;
        chk(x"00000004", "3. index 1 targets address 4 - the shift is x4");

        -- All-ones index: the top of the current 256 MB region
        Index <= (others => '1'); wait for 10 ns;
        chk(x"0FFFFFFC", "4. largest index reaches the top of the region");

        ----------------------------------------------------------------------
        -- THE POINT OF THE EXAMPLE: the same index, two different regions.
        -- The top four bits are inherited from NSA, so the jump lands in
        -- whichever 256 MB region it started in. It CANNOT leave.
        ----------------------------------------------------------------------
        Index <= "00" & x"000002";
        NSA <= x"00000018"; wait for 10 ns;
        chk(x"00000008", "5. index 2 from region 0x0 -> 0x00000008");

        NSA <= x"A0000018"; wait for 10 ns;
        chk(x"A0000008", "6. SAME index from region 0xA -> 0xA0000008");

        -- Confirm the boundary: jumping from just below a region edge
        NSA <= x"0FFFFFFC"; Index <= (others => '0'); wait for 10 ns;
        chk(x"00000000", "7. still inside region 0x0, cannot cross into 0x1");

        if errors = 0 then
            report "PASS - absolute_target: a jump stays inside its 256 MB region."
                severity note;
        else
            report "FAILED - absolute_target: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
