--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 4 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- NOTE THE BUS. Two TriBuffer instances drive ONE signal, MemBus. That is legal
-- only because std_logic is a resolved type. Enable neither and the bus reads
-- 'Z'; enable one and it reads that driver; enable both with different data and
-- it reads 'X'.
--
-- REQUIRED, at least 6 checked vectors, including all of:
--
--   [required] ImmedXtnd on x"8000" BOTH ways. That is the value where sign
--              and zero extension visibly differ: 0xFFFF8000 vs 0x00008000.
--              An input like x"0001" proves nothing - both give 0x00000001.
--              TEST WHERE THE TWO ANSWERS DISAGREE.
--   [required] ImmedXtnd row 2 (sign + shift x4) - the branch-offset case
--   [required] ImmedXtnd row 3 (zero + shift x4) - the "unused" row. If you
--              did not implement it you have a latch.
--   [required] the bus with NO driver enabled  -> all 'Z'
--   [required] the bus with BOTH drivers enabled and different data -> 'X'
--   [required] ALUsftMUX for both values of Ssel
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity tb_Lab4 is
end entity tb_Lab4;

architecture test of tb_Lab4 is

    -- ImmedXtnd
    signal Immed16 : std_logic_vector(15 downto 0) := (others => '0');
    signal Xsel    : std_logic := '0';
    signal Xlsft   : std_logic := '0';
    signal Xtnd32  : std_logic_vector(31 downto 0);

    -- Two tri-state drivers sharing ONE bus
    signal DinA, DinB : std_logic_vector(31 downto 0) := (others => '0');
    signal SelA, SelB : std_logic := '0';
    signal MemBus     : std_logic_vector(31 downto 0);   -- the shared wire

    -- ALUsftMUX
    signal SA, BoutLo : std_logic_vector(4 downto 0) := (others => '0');
    signal Ssel       : std_logic := '0';
    signal Shft       : std_logic_vector(4 downto 0);

begin

    DUT_X : entity work.ImmedXtnd
        port map (Immed16 => Immed16, Xsel => Xsel, Xlsft => Xlsft,
                  Xtnd32 => Xtnd32);

    -- BOTH of these drive MemBus. That is the point.
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

        ------------------------------------------------------------------------
        -- ImmedXtnd - use x"8000", the value where the two extensions differ
        ------------------------------------------------------------------------
        Immed16 <= x"8000";

        Xsel <= '0'; Xlsft <= '0'; wait for 10 ns;
        checkx(x"00008000", "row 0: zero-extend, no shift");

        Xsel <= '1'; Xlsft <= '0'; wait for 10 ns;
        -- TODO: check row 1 - sign-extend, no shift. What should this be?


        -- TODO: check row 2 - sign-extend AND shift left 2


        -- TODO: check row 3 - zero-extend AND shift left 2
        --       This is the "unused" row. Skip it and you have a latch.


        ------------------------------------------------------------------------
        -- The shared bus
        ------------------------------------------------------------------------
        DinA <= x"AAAAAAAA"; DinB <= x"BBBBBBBB";

        SelA <= '0'; SelB <= '0'; wait for 10 ns;
        checkbus((31 downto 0 => 'Z'), "no driver enabled: bus floats at Z");

        -- TODO: enable only A, check the bus reads A


        -- TODO: enable only B, check the bus reads B


        -- TODO: enable BOTH drivers with data that differs in EVERY bit
        --       (for example x"00000000" against x"FFFFFFFF"). The bus must
        --       then read all 'X'; write that as (31 downto 0 => 'X').
        --
        --       Careful: resolution happens PER BIT, not per bus. If you use
        --       x"AAAAAAAA" against x"BBBBBBBB" the two agree on three bits of
        --       every nibble and only the fourth goes 'X' - you would get
        --       "101X" repeated, not all 'X'. Worth trying both and seeing it.


        ------------------------------------------------------------------------
        -- ALUsftMUX
        ------------------------------------------------------------------------
        SA <= "00001"; BoutLo <= "11111";
        -- TODO: check both values of Ssel


        ------------------------------------------------------------------------
        -- Verdict - do not delete
        ------------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 4: all checks passed." severity note;
        else
            report "FAILED - Lab 4: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        wait;
    end process stimulus;

end architecture test;
