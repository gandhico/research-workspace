--------------------------------------------------------------------------------
-- EE 362 - Computer Organization Laboratory
-- Lab 8 - Testbench TEMPLATE
--
-- YOUR NAME  :
-- SECTION    :  Monday / Tuesday
-- DATE       :
--
-- The 'step' procedure advances the PC by one instruction using whatever
-- control settings are currently applied. Set Sel / Cond / Xtnd32 / Index /
-- flags, then call step, then check where the PC went.
--
-- REQUIRED: a SCRIPTED SEQUENCE walking the PC through all of these, in one
-- continuous run. That waveform is the centrepiece figure of your report.
--
--   [required] sequential execution, two or three instructions
--   [required] a NOT-TAKEN conditional branch - the PC falls back to NSA
--   [required] a TAKEN conditional branch, with the SAME Sel code as above.
--              That pair is what makes conditional execution exist.
--   [required] the real J from the Lab 12 program: at 0x14, index 2, to 0x08
--   [required] a register jump to a FULL 32-bit address, then a J from there,
--              showing the jump stays in ITS region
--   [required] Strb = '0' at an edge: the PC holds (a stall)
--   [required] a BACKWARD relative branch
--   [required] at least three NIAG_COND_* codes through the whole NIAG,
--              including GTZ with Zero='1', which must NOT be taken
--
-- HAND-COMPUTE EVERY TARGET BEFORE YOU SIMULATE, as in Lab 7.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

use work.NIAG_Pkg.all;

entity tb_Lab8 is
end entity tb_Lab8;

architecture test of tb_Lab8 is

    constant PERIOD : time := 20 ns;

    signal Index   : std_logic_vector(25 downto 0) := (others => '0');
    signal Xtnd32  : std_logic_vector(31 downto 0) := (others => '0');
    signal RegAddr : std_logic_vector(31 downto 0) := (others => '0');
    signal Sel     : std_logic_vector(1 downto 0)  := NIAG_SEL_NSA;
    signal Cond    : std_logic_vector(2 downto 0)  := NIAG_COND_NONE;
    signal Strb    : std_logic := '1';
    signal Zero, Neg, Rst : std_logic := '0';
    signal clk : std_logic := '0';
    signal PC, NSA, Rtn : std_logic_vector(31 downto 0);
    signal running : boolean := true;

begin

    DUT : entity work.NIAG
        port map (Index => Index, Xtnd32 => Xtnd32, RegAddr => RegAddr,
                  Sel => Sel, Cond => Cond, Strb => Strb,
                  Zero => Zero, Neg => Neg, Rst => Rst, clk => clk,
                  PC => PC, NSA => NSA, Rtn => Rtn);

    clock_gen : process
    begin
        while running loop
            clk <= '0'; wait for PERIOD / 2;
            clk <= '1'; wait for PERIOD / 2;
        end loop;
        wait;
    end process clock_gen;

    stimulus : process

        variable errors : natural := 0;

        procedure chk (got, want : in std_logic_vector(31 downto 0);
                       msg : in string) is
        begin
            if got /= want then
                report "FAIL: " & msg severity error;
                errors := errors + 1;
            end if;
        end procedure chk;

        -- Advance one instruction with the current control settings.
        procedure step is
        begin
            wait until rising_edge(clk);
            wait for 1 ns;
        end procedure step;

    begin

        ----------------------------------------------------------------------
        -- Reset. This one fails until your NIAG is built.
        ----------------------------------------------------------------------
        Rst <= '1'; wait for 3 ns;
        chk(PC,  x"00000000", "reset vector");
        -- TODO: also check NSA is 0x04 and Rtn is 0x04 here
        Rst <= '0';

        ----------------------------------------------------------------------
        -- *** REQUIRED *** Sequential execution, two or three instructions
        ----------------------------------------------------------------------
        Sel <= NIAG_SEL_NSA; Cond <= NIAG_COND_NONE;
        -- TODO: step and check 0x04, 0x08, 0x0C


        ----------------------------------------------------------------------
        -- *** REQUIRED *** A NOT-TAKEN branch, then a TAKEN one
        --   Use NIAG_COND_LEZ (= N + Z) and Xtnd32 = 0x00000008 (offset +2).
        --   Zero='0', Neg='0' -> result positive -> NOT taken -> falls to NSA
        --   Zero='1'          -> result zero     -> TAKEN     -> the target
        --   Same Sel code both times. That pair IS conditional execution.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** The real J: at 0x14 with index 2, target is 0x08
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** A register jump to a full 32-bit address (try
        --   0xA0000040), then a J from there - it must stay in region 0xA.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** Strb = '0' at an edge: the PC holds
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** At least three NIAG_COND_* codes through the NIAG.
        --   Include GTZ with Zero='1': it must NOT be taken, because zero is
        --   not greater than zero. That is the condition students get wrong.
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- *** REQUIRED *** A BACKWARD relative branch (Xtnd32 = 0xFFFFFFF0)
        ----------------------------------------------------------------------
        -- TODO


        ----------------------------------------------------------------------
        -- Verdict - do not delete
        ----------------------------------------------------------------------
        if errors = 0 then
            report "PASS - Lab 8: all checks passed." severity note;
        else
            report "FAILED - Lab 8: " & integer'image(errors) &
                   " check(s) failed." severity error;
        end if;

        running <= false;
        wait;
    end process stimulus;

end architecture test;
