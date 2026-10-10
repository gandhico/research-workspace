--------------------------------------------------------------------------------
-- EE 362 - Lab 4 REFERENCE SOLUTION testbench  (TA only - do not publish)
--
-- 16 checks: all four extension rows on the value where the two extensions
-- disagree, full bus resolution (Z / A / B / X / agreeing drivers), and both
-- shift-amount sources.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab4 is
end entity tb_Lab4;

architecture test of tb_Lab4 is

    signal Immed16 : std_logic_vector(15 downto 0) := (others => '0');
    signal Xsel    : std_logic := '0';
    signal Xlsft   : std_logic := '0';
    signal Xtnd32  : std_logic_vector(31 downto 0);

    signal DinA, DinB : std_logic_vector(31 downto 0) := (others => '0');
    signal SelA, SelB : std_logic := '0';
    signal MemBus     : std_logic_vector(31 downto 0);

    signal SA, BoutLo : std_logic_vector(4 downto 0) := (others => '0');
    signal Ssel       : std_logic := '0';
    signal Shft       : std_logic_vector(4 downto 0);

begin

    DUT_X : entity work.ImmedXtnd
        port map (Immed16 => Immed16, Xsel => Xsel, Xlsft => Xlsft,
                  Xtnd32 => Xtnd32);

    DRV_A : entity work.TriBuffer
        port map (Din => DinA, Sel => SelA, Dout => MemBus);

    DRV_B : entity work.TriBuffer
        port map (Din => DinB, Sel => SelB, Dout => MemBus);

    DUT_S : entity work.ALUsftMUX
        port map (SA => SA, Bout => BoutLo, Ssel => Ssel, Shft => Shft);

    stimulus : process

        variable errors : natural := 0;

        procedure checkx (want : in std_logic_vector(31 downto 0);
                          msg  : in string) is
        begin
            if Xtnd32 /= want then
                report "FAIL (extend): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure checkx;

        procedure checkbus (want : in std_logic_vector(31 downto 0);
                            msg  : in string) is
        begin
            if MemBus /= want then
                report "FAIL (bus): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure checkbus;

        procedure checks (want : in std_logic_vector(4 downto 0);
                          msg  : in string) is
        begin
            if Shft /= want then
                report "FAIL (shift sel): " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure checks;

    begin

        ----------------------------------------------------------------------
        -- ImmedXtnd, on x"8000": sign and zero extension visibly disagree
        ----------------------------------------------------------------------
        Immed16 <= x"8000";

        Xsel <= '0'; Xlsft <= '0'; wait for 10 ns;
        checkx(x"00008000", "1. row 0: zero-extend, no shift");

        Xsel <= '1'; Xlsft <= '0'; wait for 10 ns;
        checkx(x"FFFF8000", "2. row 1: sign-extend, no shift");

        Xsel <= '1'; Xlsft <= '1'; wait for 10 ns;
        checkx(x"FFFE0000", "3. row 2: sign-extend then shift left 2");

        Xsel <= '0'; Xlsft <= '1'; wait for 10 ns;
        checkx(x"00020000", "4. row 3: zero-extend then shift left 2");

        -- A value where the two extensions AGREE, to prove the low bits pass
        Immed16 <= x"0001";
        Xsel <= '0'; Xlsft <= '0'; wait for 10 ns;
        checkx(x"00000001", "5. small positive, zero-extend");
        Xsel <= '1';             wait for 10 ns;
        checkx(x"00000001", "6. small positive, sign-extend: same answer");

        -- The branch-offset case from Lab 7: offset +2 becomes +8 bytes
        Immed16 <= x"0002";
        Xsel <= '1'; Xlsft <= '1'; wait for 10 ns;
        checkx(x"00000008", "7. offset +2 scaled by 4 = +8 bytes");

        -- A negative offset, scaled
        Immed16 <= x"FFFF";                       -- -1
        Xsel <= '1'; Xlsft <= '1'; wait for 10 ns;
        checkx(x"FFFFFFFC", "8. offset -1 scaled by 4 = -4 bytes");

        ----------------------------------------------------------------------
        -- The shared bus
        ----------------------------------------------------------------------
        DinA <= x"AAAAAAAA"; DinB <= x"BBBBBBBB";

        SelA <= '0'; SelB <= '0'; wait for 10 ns;
        checkbus((31 downto 0 => 'Z'), "9. no driver: bus floats at Z");

        SelA <= '1'; SelB <= '0'; wait for 10 ns;
        checkbus(x"AAAAAAAA", "10. only A drives");

        SelA <= '0'; SelB <= '1'; wait for 10 ns;
        checkbus(x"BBBBBBBB", "11. only B drives");

        -- Total contention: every bit differs, so every bit resolves to 'X'.
        DinA <= x"00000000"; DinB <= x"FFFFFFFF";
        SelA <= '1'; SelB <= '1'; wait for 10 ns;
        checkbus((31 downto 0 => 'X'), "12. CONTENTION: every bit differs -> all X");

        -- PARTIAL contention. Resolution happens PER BIT, not per bus.
        --   0xA = 1010, 0xB = 1011 - they differ only in the low bit of each
        --   nibble, so only those bits go 'X'. The rest resolve normally.
        --   Each nibble becomes "101X".
        DinA <= x"AAAAAAAA"; DinB <= x"BBBBBBBB"; wait for 10 ns;
        checkbus("101X101X101X101X101X101X101X101X",
                 "13. PARTIAL contention: only the differing bits go X");

        -- Two drivers that agree resolve cleanly: 'X' comes from disagreement,
        -- not from the mere presence of two drivers.
        DinB <= x"AAAAAAAA"; wait for 10 ns;
        checkbus(x"AAAAAAAA", "14. two drivers that AGREE resolve cleanly");

        SelA <= '0'; SelB <= '0';

        ----------------------------------------------------------------------
        -- ALUsftMUX
        ----------------------------------------------------------------------
        SA <= "00001"; BoutLo <= "11111";

        Ssel <= '0'; wait for 10 ns;
        checks("00001", "15. Ssel=0 takes the IR sa field");

        Ssel <= '1'; wait for 10 ns;
        checks("11111", "16. Ssel=1 takes register B");

        if errors = 0 then
            report "PASS - Lab 4: all 16 checks passed." severity note;
        else
            report "FAILED - Lab 4: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
