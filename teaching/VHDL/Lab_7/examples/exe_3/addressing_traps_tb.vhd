--------------------------------------------------------------------------------
-- EE 362 - Lab 7, Example 3 - Watching the two wrong answers
--
-- The asserts on NoShift and BasePC are expected to FAIL. That is the example.
-- Read the failure messages, then look at the three outputs side by side in the
-- waveform and note how DIFFERENT the two kinds of wrongness look.
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity addressing_traps_tb is
end entity addressing_traps_tb;

architecture test of addressing_traps_tb is

    signal PC    : std_logic_vector(31 downto 0) := (others => '0');
    signal Immed : std_logic_vector(15 downto 0) := (others => '0');
    signal Good, NoShift, BasePC : std_logic_vector(31 downto 0);

begin

    DUT : entity work.addressing_traps
        port map (PC => PC, Immed => Immed,
                  Good => Good, NoShift => NoShift, BasePC => BasePC);

    stimulus : process
    begin

        -- The real BLEZ from the Lab 12 program: at 0x0C, offset +2.
        -- Correct target is 0x18.
        PC <= x"0000000C"; Immed <= x"0002"; wait for 10 ns;

        assert Good = x"00000018"
            report "The correct version is broken - check Example 2."
            severity error;

        report "PC = 0x0000000C, offset = +2 instructions" severity note;
        report "  Good    = 0x00000018   (correct: the SW instruction)" severity note;
        report "  NoShift = 0x00000012   (not word-aligned - mid-instruction!)"
            severity note;
        report "  BasePC  = 0x00000014   (word-aligned, but one instruction early)"
            severity note;

        assert NoShift = x"00000018"
            report "EXPECTED FAILURE (NoShift): got 0x12. Off by a FACTOR - " &
                   "the target is not even a multiple of 4, so the CPU would " &
                   "fetch a word straddling two instructions."
            severity error;

        assert BasePC = x"00000018"
            report "EXPECTED FAILURE (BasePC): got 0x14. Off by a CONSTANT 4 - " &
                   "still word-aligned, still nearly right. This is the harder " &
                   "one to spot: loops just run one instruction too many."
            severity error;

        -- A backward branch, where the same two errors show up mirrored
        PC <= x"00000030"; Immed <= x"FFFC"; wait for 10 ns;   -- -4 instructions

        assert Good = x"00000024"
            report "The correct version is broken on backward branches."
            severity error;

        report "PC = 0x00000030, offset = -4 instructions" severity note;
        report "  Good    = 0x00000024   (correct)" severity note;
        report "  NoShift = 0x00000030   (only 4 bytes back instead of 16)"
            severity note;
        report "  BasePC  = 0x00000020   (16 bytes back from the wrong base)"
            severity note;

        report "Compare the three outputs in the waveform. 'Off by a factor' " &
               "and 'off by a constant' are the two shapes almost every " &
               "addressing bug takes." severity note;

        wait;
    end process stimulus;

end architecture test;
